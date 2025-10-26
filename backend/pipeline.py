"""
Pipeline Orchestrator - Coordinates all phases of the parametric curve generation system.
This is the main workflow controller that ties together all components.
"""

import os
import json
import logging
import math
import time
import uuid
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from . import claude_client
from . import renderer_agent
from . import evaluator_agent
from . import memory_manager
from . import utils_relative
from .schemas import CurveDef, AbsoluteCurves, RelativeProgram, DrawResult

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

            # Phase 4: Build relative program
            logger.info("=" * 60)
            logger.info("PHASE 4: Building relative program")
            logger.info("=" * 60)

            relative_program = self._build_relative_program(final_curves)

            # Phase 5: Prepare final output
            logger.info("=" * 60)
            logger.info("PHASE 5: Preparing final output")
            logger.info("=" * 60)

            self.end_time = time.time()
            processing_time = self.end_time - self.start_time

            # Convert image to base64
            image_base64 = renderer_agent.get_image_as_base64(final_image)

            # Convert final_curves dict to AbsoluteCurves model
            absolute_curves = AbsoluteCurves(
                curves=[
                    CurveDef(**c) for c in final_curves.get('curves', [])
                ]
            )

            result = {
                "success": True,
                "prompt": prompt_text,
                "description": description,
                "curves": absolute_curves.dict(),  # Legacy format
                "relative_program": relative_program.dict(),  # New preferred format
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
            logger.info(f"Relative program segments: {len(relative_program.segments)}")

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

    def _build_relative_program(self, curves_dict: Dict[str, Any]) -> RelativeProgram:
        """
        Build a relative program from absolute curves.

        Each curve is transformed into the local frame of the previous curve's end pose.
        If curves are not connected (end of curve i != start of curve i+1), a pen-up
        travel segment is inserted.

        Args:
            curves_dict: Dictionary containing a 'curves' list with absolute CurveDef objects

        Returns:
            RelativeProgram with transformed segments (including travel segments)
        """
        logger.info("Building relative program from absolute curves...")

        curves = curves_dict.get('curves', [])
        if not curves:
            logger.warning("No curves to convert to relative program")
            return RelativeProgram(segments=[])

        # Convert dict curves to CurveDef objects
        curve_defs = []
        for c in curves:
            curve_def = CurveDef(
                name=c['name'],
                x=c['x'],
                y=c['y'],
                t_min=c['t_min'],
                t_max=c['t_max'],
                color=c.get('color', None)
            )
            curve_defs.append(curve_def)

        relative_segments = []
        current_pose = (0.0, 0.0, 0.0)  # Start pose P_0 = (0, 0, 0)

        for i, curve in enumerate(curve_defs):
            try:
                # Compute where this curve starts in absolute coordinates
                from .renderer_agent import safe_eval_expression
                curve_start_x = safe_eval_expression(curve.x, curve.t_min)
                curve_start_y = safe_eval_expression(curve.y, curve.t_min)

                # Check if we need a travel segment (pen up)
                # If this is not the first curve and it doesn't start where we ended
                if i > 0:
                    current_x, current_y, _ = current_pose
                    distance = math.sqrt((curve_start_x - current_x)**2 + (curve_start_y - current_y)**2)

                    if distance > 1e-3:  # Not connected (threshold: 1mm)
                        logger.info(
                            f"Curves not connected: inserting travel segment "
                            f"from ({current_x:.4f}, {current_y:.4f}) to "
                            f"({curve_start_x:.4f}, {curve_start_y:.4f}) "
                            f"[distance: {distance:.4f}]"
                        )

                        # Create a travel segment (straight line with pen up)
                        travel_curve = CurveDef(
                            name=f"travel_to_{curve.name}",
                            x=f"{current_x} + t * ({curve_start_x} - {current_x})",
                            y=f"{current_y} + t * ({curve_start_y} - {current_y})",
                            t_min=0.0,
                            t_max=1.0,
                            color=None  # Will be set to "none" for pen up
                        )

                        # Transform travel segment to relative frame
                        travel_segment = utils_relative.wrap_to_relative(
                            prev_pose=current_pose,
                            curve=travel_curve,
                            default_color="none"  # Pen up!
                        )

                        if utils_relative.validate_relative_segment(travel_segment):
                            relative_segments.append(travel_segment)

                        # Update current pose after travel
                        travel_end_pose = utils_relative.compute_end_pose(travel_curve)
                        current_pose = travel_end_pose

                # Transform the actual drawing curve to relative frame
                # Note: PenSpec validator will normalize the color to black/blue/none
                default_color = curve.color if curve.color else "#000000"
                relative_segment = utils_relative.wrap_to_relative(
                    prev_pose=current_pose,
                    curve=curve,
                    default_color=default_color
                )

                # Validate the segment
                if utils_relative.validate_relative_segment(relative_segment):
                    relative_segments.append(relative_segment)
                else:
                    logger.warning(f"Skipping invalid relative segment: {curve.name}")
                    continue

                # Compute end pose for next iteration
                end_pose = utils_relative.compute_end_pose(curve)
                current_pose = end_pose

                logger.info(
                    f"Added relative segment {i+1}/{len(curve_defs)}: {curve.name}"
                )

            except Exception as e:
                logger.error(f"Error processing curve '{curve.name}': {e}")
                # Continue with remaining curves

        logger.info(f"Built relative program with {len(relative_segments)} segments "
                   f"(including travel segments)")
        return RelativeProgram(segments=relative_segments)

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
        Result dictionary with durable export metadata in stats
    """
    pipeline = Pipeline(use_letta=use_letta)
    result = pipeline.run_pipeline(prompt_text)

    # --- Durable export of relative_program for robot ---
    exports_dir = Path("exports")
    exports_dir.mkdir(parents=True, exist_ok=True)

    run_id = uuid.uuid4().hex  # stable and unique

    # Normalize relative_program for both Pydantic v1/v2 or dict
    rel_prog = result.get("relative_program")
    if rel_prog is None:
        logger.warning("relative_program missing from pipeline result - skipping export")
        return result

    # Support Pydantic v2 (model_dump), v1 (dict), or plain dict
    if hasattr(rel_prog, "model_dump"):  # Pydantic v2
        rel_prog_dict = rel_prog.model_dump()
    elif hasattr(rel_prog, "dict"):  # Pydantic v1
        rel_prog_dict = rel_prog.dict()
    elif isinstance(rel_prog, dict):
        rel_prog_dict = rel_prog
    else:
        logger.error(f"Unsupported relative_program type: {type(rel_prog)}")
        return result

    payload = {
        "run_id": run_id,
        "prompt": prompt_text,
        "relative_program": rel_prog_dict
    }

    export_path = exports_dir / f"relative_program_{run_id}.json"

    # Atomic write to avoid partial files
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, dir=exports_dir, encoding="utf-8") as tf:
            json.dump(payload, tf, indent=2)
            tmp_name = tf.name
        os.replace(tmp_name, export_path)
        logger.info(f"Exported relative program to {export_path}")
    except Exception as e:
        logger.error(f"Failed to export relative program: {e}")
        # Continue without crashing - export is supplemental
        return result

    # Attach run info back to result (preserve existing stats)
    stats = result.get("stats") or {}
    stats.update({
        "run_id": run_id,
        "export_path": str(export_path)
    })
    result["stats"] = stats

    return result


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
