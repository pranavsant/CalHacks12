"""
Pipeline Orchestrator - Coordinates all phases of the parametric curve generation system.
This is the main workflow controller that ties together all components.
"""

import os
import logging
import time
from typing import Dict, Any, Optional, Tuple

from . import claude_client
from . import renderer_agent
from . import evaluator_agent
from . import memory_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MAX_ITERATIONS = 3
TARGET_SCORE = 9.0


class Pipeline:
    """
    Main pipeline orchestrator for the parametric curve drawing system.
    """

    def __init__(self, use_letta: bool = False):
        """
        Initialize the pipeline.

        Args:
            use_letta: Whether to use Letta Cloud for memory management
        """
        self.memory = memory_manager.create_memory_manager(use_letta=use_letta)
        self.start_time = None
        self.end_time = None

    def run_pipeline(self, prompt_text: str) -> Dict[str, Any]:
        """
        Execute the complete pipeline from prompt to final drawing.

        Args:
            prompt_text: Natural language description of what to draw

        Returns:
            Dictionary containing:
            - prompt: original prompt
            - description: structured interpretation
            - curves: final parametric equations
            - iterations: number of refinement iterations
            - evaluation_score: final score
            - evaluation_feedback: final feedback
            - image_path: path to final image
            - image_base64: base64-encoded image data URL
            - processing_time: total time in seconds
            - history: detailed history of all operations
        """
        self.start_time = time.time()
        logger.info(f"Starting pipeline for prompt: '{prompt_text}'")

        try:
            # Phase 1: Interpret the prompt
            logger.info("=" * 60)
            logger.info("PHASE 1: Interpreting user prompt")
            logger.info("=" * 60)

            description = claude_client.interpret_prompt(prompt_text)
            self.memory.store_initial_prompt(prompt_text, description)

            logger.info(f"Interpreted as: {description['description']}")
            logger.info(f"Components: {description['components']}")
            logger.info(f"Symmetry: {description['symmetry']}")
            logger.info(f"Complexity: {description['complexity']}/5")

            # Phase 2: Generate initial parametric equations
            logger.info("=" * 60)
            logger.info("PHASE 2: Generating parametric equations")
            logger.info("=" * 60)

            curves = claude_client.generate_parametric_equations(description)
            self.memory.store_equations(curves, iteration=0)

            logger.info(f"Generated {len(curves['curves'])} curves:")
            for curve in curves['curves']:
                logger.info(f"  - {curve['name']}: x={curve['x']}, y={curve['y']}")

            # Phase 3: Multi-agent refinement loop
            logger.info("=" * 60)
            logger.info("PHASE 3: Multi-agent refinement loop")
            logger.info("=" * 60)

            final_curves, final_score, final_feedback, final_image = self._refinement_loop(
                curves, prompt_text, description
            )

            # Phase 4: Prepare final output
            logger.info("=" * 60)
            logger.info("PHASE 4: Preparing final output")
            logger.info("=" * 60)

            self.end_time = time.time()
            processing_time = self.end_time - self.start_time

            # Convert image to base64
            image_base64 = renderer_agent.get_image_as_base64(final_image)

            result = {
                "success": True,
                "prompt": prompt_text,
                "description": description,
                "curves": final_curves,
                "iterations": self.memory.current_state.get("iteration", 0),
                "evaluation_score": final_score,
                "evaluation_feedback": final_feedback,
                "image_path": final_image,
                "image_base64": image_base64,
                "processing_time": round(processing_time, 2),
                "session_id": self.memory.session_id,
                "history": self.memory.get_history()
            }

            logger.info(f"Pipeline completed successfully in {processing_time:.2f} seconds")
            logger.info(f"Final score: {final_score}/10")
            logger.info(f"Total iterations: {result['iterations']}")

            return result

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            self.end_time = time.time()
            processing_time = self.end_time - self.start_time if self.start_time else 0

            return {
                "success": False,
                "error": str(e),
                "prompt": prompt_text,
                "processing_time": round(processing_time, 2),
                "session_id": self.memory.session_id
            }

    def _refinement_loop(
        self,
        initial_curves: Dict[str, Any],
        prompt_text: str,
        description: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], float, str, str]:
        """
        Execute the refinement loop: render → evaluate → refine.

        Args:
            initial_curves: Initial parametric equations
            prompt_text: Original prompt
            description: Structured description

        Returns:
            Tuple of (final_curves, final_score, final_feedback, final_image_path)
        """
        current_curves = initial_curves
        iteration = 0

        while iteration < MAX_ITERATIONS:
            iteration += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"Iteration {iteration}/{MAX_ITERATIONS}")
            logger.info(f"{'='*60}")

            # Render the current curves
            logger.info("Rendering curves...")
            image_path = renderer_agent.render_curves(
                current_curves,
                output_filename=f"iteration_{iteration}_{self.memory.session_id}"
            )
            self.memory.store_image(image_path, iteration)
            logger.info(f"Image saved: {image_path}")

            # Evaluate the rendered image
            logger.info("Evaluating image...")
            score, feedback = evaluator_agent.evaluate_image(
                image_path,
                prompt_text,
                description=description,
                iteration_number=iteration
            )
            self.memory.store_evaluation(score, feedback, iteration)

            logger.info(f"Evaluation Score: {score}/10")
            logger.info(f"Feedback: {feedback}")

            # Check if we've reached the target score or max iterations
            if score >= TARGET_SCORE or iteration >= MAX_ITERATIONS:
                logger.info(f"Stopping refinement: " +
                          (f"Target score reached" if score >= TARGET_SCORE
                           else f"Max iterations reached"))
                return current_curves, score, feedback, image_path

            # Refine the equations based on feedback
            logger.info("Refining equations based on feedback...")
            refined_curves = claude_client.refine_equations(current_curves, feedback)
            self.memory.store_equations(refined_curves, iteration)

            # Check if refinement actually changed the equations
            if refined_curves == current_curves:
                logger.info("No changes made in refinement, stopping loop")
                return current_curves, score, feedback, image_path

            current_curves = refined_curves
            logger.info("Equations refined, proceeding to next iteration")

        # Should not reach here, but return current state if we do
        return current_curves, score, feedback, image_path


def run_pipeline(prompt_text: str, use_letta: bool = False) -> Dict[str, Any]:
    """
    Convenience function to run the pipeline.

    Args:
        prompt_text: Natural language description of what to draw
        use_letta: Whether to use Letta Cloud for memory

    Returns:
        Result dictionary
    """
    pipeline = Pipeline(use_letta=use_letta)
    return pipeline.run_pipeline(prompt_text)


def run_pipeline_from_audio(audio_path: str, use_letta: bool = False) -> Dict[str, Any]:
    """
    Run the pipeline starting from an audio file.

    Args:
        audio_path: Path to audio file
        use_letta: Whether to use Letta Cloud for memory

    Returns:
        Result dictionary
    """
    logger.info(f"Processing audio file: {audio_path}")

    try:
        # Import here to avoid circular imports
        from . import vapi_client

        # Transcribe audio to text
        prompt_text = vapi_client.transcribe_audio(audio_path)
        logger.info(f"Transcribed text: {prompt_text}")

        # Run the normal pipeline with the transcribed text
        return run_pipeline(prompt_text, use_letta=use_letta)

    except NotImplementedError as e:
        logger.error(f"Audio transcription not available: {e}")
        return {
            "success": False,
            "error": "Audio transcription not implemented. Please use text input or configure Vapi API.",
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Error processing audio: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Test the pipeline
    import sys

    if len(sys.argv) > 1:
        test_prompt = " ".join(sys.argv[1:])
    else:
        test_prompt = "Draw a butterfly with symmetric wings"

    print("\nParametric Curve Drawing Pipeline")
    print("=" * 60)
    print(f"Test prompt: {test_prompt}")
    print("=" * 60 + "\n")

    result = run_pipeline(test_prompt)

    if result.get("success"):
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"Final Score: {result['evaluation_score']}/10")
        print(f"Iterations: {result['iterations']}")
        print(f"Processing Time: {result['processing_time']}s")
        print(f"Image: {result['image_path']}")
    else:
        print("\n" + "=" * 60)
        print("PIPELINE FAILED")
        print("=" * 60)
        print(f"Error: {result.get('error')}")
