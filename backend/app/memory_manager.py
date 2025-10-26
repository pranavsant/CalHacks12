"""
Memory Manager - Handles state persistence and memory across pipeline iterations.
Can be extended to integrate with Letta Cloud for persistent memory across sessions.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Letta Cloud configuration (if available)
LETTA_API_KEY = os.getenv("LETTA_API_KEY")


class MemoryManager:
    """
    Manages state and history for the parametric curve generation pipeline.
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize the memory manager.

        Args:
            session_id: Optional session identifier for tracking across requests
        """
        self.session_id = session_id or self._generate_session_id()
        self.history: List[Dict[str, Any]] = []
        self.current_state: Dict[str, Any] = {}
        logger.info(f"Initialized MemoryManager for session: {self.session_id}")

    @staticmethod
    def _generate_session_id() -> str:
        """Generate a unique session ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{timestamp}"

    def store_initial_prompt(self, prompt: str, description: Dict[str, Any]) -> None:
        """
        Store the initial user prompt and its interpretation.

        Args:
            prompt: Original user prompt
            description: Structured description from interpret_prompt
        """
        entry = {
            "type": "initial_prompt",
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "description": description
        }
        self.history.append(entry)
        self.current_state["prompt"] = prompt
        self.current_state["description"] = description
        logger.info("Stored initial prompt in memory")

    def store_equations(self, equations: Dict[str, Any], iteration: int) -> None:
        """
        Store parametric equations for a given iteration.

        Args:
            equations: The curves dictionary
            iteration: Iteration number
        """
        entry = {
            "type": "equations",
            "timestamp": datetime.now().isoformat(),
            "iteration": iteration,
            "equations": equations
        }
        self.history.append(entry)
        self.current_state["equations"] = equations
        self.current_state["iteration"] = iteration
        logger.info(f"Stored equations for iteration {iteration}")

    def store_evaluation(self, score: float, feedback: str, iteration: int) -> None:
        """
        Store evaluation results for a given iteration.

        Args:
            score: Overall evaluation score
            feedback: Feedback text
            iteration: Iteration number
        """
        entry = {
            "type": "evaluation",
            "timestamp": datetime.now().isoformat(),
            "iteration": iteration,
            "score": score,
            "feedback": feedback
        }
        self.history.append(entry)
        self.current_state[f"evaluation_{iteration}"] = {
            "score": score,
            "feedback": feedback
        }
        logger.info(f"Stored evaluation for iteration {iteration}: score={score}")

    def store_image(self, image_path: str, iteration: int) -> None:
        """
        Store the path to a rendered image.

        Args:
            image_path: Path to the image file
            iteration: Iteration number
        """
        entry = {
            "type": "image",
            "timestamp": datetime.now().isoformat(),
            "iteration": iteration,
            "path": image_path
        }
        self.history.append(entry)
        self.current_state[f"image_{iteration}"] = image_path
        logger.info(f"Stored image path for iteration {iteration}")

    def get_current_equations(self) -> Optional[Dict[str, Any]]:
        """Get the most recent equations."""
        return self.current_state.get("equations")

    def get_latest_evaluation(self) -> Optional[Dict[str, float]]:
        """Get the most recent evaluation results."""
        iteration = self.current_state.get("iteration", 0)
        return self.current_state.get(f"evaluation_{iteration}")

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the full history of operations."""
        return self.history.copy()

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current state.

        Returns:
            Dictionary with key information about the session
        """
        iteration = self.current_state.get("iteration", 0)
        latest_eval = self.get_latest_evaluation()

        summary = {
            "session_id": self.session_id,
            "prompt": self.current_state.get("prompt"),
            "total_iterations": iteration,
            "latest_score": latest_eval.get("score") if latest_eval else None,
            "history_length": len(self.history)
        }
        return summary

    def export_to_json(self, filepath: Optional[str] = None) -> str:
        """
        Export the memory to a JSON file.

        Args:
            filepath: Optional path to save the JSON file

        Returns:
            Path to the saved file
        """
        if filepath is None:
            filepath = f"memory_{self.session_id}.json"

        data = {
            "session_id": self.session_id,
            "current_state": self.current_state,
            "history": self.history
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported memory to {filepath}")
        return filepath

    def load_from_json(self, filepath: str) -> None:
        """
        Load memory from a JSON file.

        Args:
            filepath: Path to the JSON file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.session_id = data.get("session_id", self.session_id)
        self.current_state = data.get("current_state", {})
        self.history = data.get("history", [])

        logger.info(f"Loaded memory from {filepath}")


class LettaMemoryManager(MemoryManager):
    """
    Extended memory manager that integrates with Letta Cloud.
    Provides persistent, long-term memory across sessions.
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize with Letta Cloud integration.

        Args:
            session_id: Optional session identifier
        """
        super().__init__(session_id)
        self.letta_client = None

        if LETTA_API_KEY:
            self._init_letta_client()
        else:
            logger.warning("LETTA_API_KEY not found - using local memory only")

    def _init_letta_client(self):
        """
        Initialize the Letta Cloud client.

        NOTE: This is a placeholder for actual Letta integration.
        Refer to Letta documentation for the correct implementation.
        """
        try:
            # Placeholder for Letta client initialization
            # Actual implementation would be:
            #
            # from letta_client import Letta
            # self.letta_client = Letta(token=LETTA_API_KEY)
            #
            # # Create or retrieve an agent
            # self.agent = self.letta_client.create_agent(
            #     name=f"curve_drawer_{self.session_id}",
            #     memory_blocks=[
            #         {"name": "prompt", "value": ""},
            #         {"name": "equations", "value": ""},
            #         {"name": "feedback", "value": ""}
            #     ]
            # )

            logger.info("Letta client initialization skipped (not implemented)")

        except Exception as e:
            logger.error(f"Failed to initialize Letta client: {e}")
            self.letta_client = None

    def store_to_letta(self, key: str, value: Any) -> None:
        """
        Store a value in Letta Cloud memory.

        Args:
            key: Memory block key
            value: Value to store
        """
        if not self.letta_client:
            logger.debug("Letta client not available, using local memory only")
            return

        try:
            # Placeholder for Letta memory storage
            # self.letta_client.update_memory_block(
            #     agent_id=self.agent.id,
            #     block_name=key,
            #     value=json.dumps(value)
            # )
            logger.info(f"Stored {key} to Letta Cloud")

        except Exception as e:
            logger.error(f"Failed to store to Letta: {e}")

    def retrieve_from_letta(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from Letta Cloud memory.

        Args:
            key: Memory block key

        Returns:
            Retrieved value or None
        """
        if not self.letta_client:
            return None

        try:
            # Placeholder for Letta memory retrieval
            # value = self.letta_client.get_memory_block(
            #     agent_id=self.agent.id,
            #     block_name=key
            # )
            # return json.loads(value)
            logger.info(f"Retrieved {key} from Letta Cloud")
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve from Letta: {e}")
            return None


def create_memory_manager(use_letta: bool = False) -> MemoryManager:
    """
    Factory function to create the appropriate memory manager.

    Args:
        use_letta: Whether to use Letta Cloud integration

    Returns:
        MemoryManager instance
    """
    if use_letta and LETTA_API_KEY:
        return LettaMemoryManager()
    else:
        return MemoryManager()


if __name__ == "__main__":
    # Test the memory manager
    print("Memory Manager Test")
    print("-" * 40)

    manager = create_memory_manager()
    print(f"Session ID: {manager.session_id}")

    # Store some test data
    manager.store_initial_prompt("Draw a circle", {"complexity": 1})
    manager.store_equations({"curves": []}, iteration=1)
    manager.store_evaluation(7.5, "Good start", iteration=1)

    # Get summary
    summary = manager.get_summary()
    print("\nSummary:")
    print(json.dumps(summary, indent=2))
