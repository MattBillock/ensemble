"""State management for agent execution persistence and resume capability."""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class StateManager:
    """Manages agent execution state for checkpointing and resume functionality."""

    def __init__(self, state_file: Optional[Path] = None):
        """
        Initialize state manager.

        Args:
            state_file: Path to state file for persistence. If None, state is not persisted.
        """
        self.state_file = state_file
        self.state: Dict[str, Any] = {
            "agent_name": None,
            "iteration": 0,
            "conversation_history": [],
            "spawned_agents": [],
            "tool_results": [],
            "start_time": None,
            "last_checkpoint": None,
            "input_data": {},
            "status": "running"
        }

        # Load existing state if file exists
        if state_file and state_file.exists():
            self.load()

    def init_execution(self, agent_name: str, input_data: Dict[str, Any]) -> None:
        """
        Initialize a new agent execution.

        Args:
            agent_name: Name of the agent being executed
            input_data: Input data provided to the agent
        """
        self.state.update({
            "agent_name": agent_name,
            "iteration": 0,
            "conversation_history": [],
            "spawned_agents": [],
            "tool_results": [],
            "start_time": datetime.now().isoformat(),
            "last_checkpoint": None,
            "input_data": input_data,
            "status": "running"
        })

        logger.info(f"Initialized execution state for agent: {agent_name}")
        self.checkpoint()

    def record_iteration(self, iteration: int, message: Dict[str, Any]) -> None:
        """
        Record an iteration in the conversation history.

        Args:
            iteration: Current iteration number
            message: Message content (user or assistant)
        """
        self.state["iteration"] = iteration

        # Convert content to serializable format
        content = message.get("content", [])
        serializable_content = self._make_serializable(content)

        self.state["conversation_history"].append({
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "role": message.get("role"),
            "content": serializable_content
        })

    def _make_serializable(self, obj: Any) -> Any:
        """
        Convert Anthropic objects to JSON-serializable format.

        Args:
            obj: Object to convert (can be dict, list, or Anthropic object)

        Returns:
            JSON-serializable version of the object
        """
        if isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif hasattr(obj, 'model_dump'):
            # Anthropic objects have model_dump() method
            return obj.model_dump()
        elif hasattr(obj, '__dict__'):
            # Fallback for objects with __dict__
            return {k: self._make_serializable(v) for k, v in obj.__dict__.items()}
        else:
            # Primitive types (str, int, bool, None)
            return obj

    def record_tool_result(self, tool_name: str, inputs: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Record a tool execution result.

        Args:
            tool_name: Name of the tool executed
            inputs: Tool inputs
            result: Tool execution result
        """
        self.state["tool_results"].append({
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "inputs": inputs,
            "result": result
        })

        # Record spawned agents separately for easy tracking
        if tool_name == "spawn_agent":
            self.state["spawned_agents"].append({
                "timestamp": datetime.now().isoformat(),
                "agent_type": inputs.get("agent_type"),
                "success": result.get("success", False),
                "result": result.get("result", {})
            })

    def checkpoint(self) -> None:
        """Save current state to disk if state_file is configured."""
        if not self.state_file:
            return

        self.state["last_checkpoint"] = datetime.now().isoformat()

        try:
            # Ensure parent directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            # Write state to file
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)

            logger.debug(f"Checkpoint saved to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def load(self) -> bool:
        """
        Load state from disk.

        Returns:
            True if state was loaded successfully, False otherwise
        """
        if not self.state_file or not self.state_file.exists():
            return False

        try:
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)

            logger.info(f"Loaded state from {self.state_file}")
            logger.info(f"Agent: {self.state['agent_name']}, Iteration: {self.state['iteration']}")
            return True
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return False

    def mark_completed(self, final_result: Dict[str, Any]) -> None:
        """
        Mark execution as completed.

        Args:
            final_result: Final result from agent execution
        """
        self.state["status"] = "completed"
        self.state["final_result"] = final_result
        self.state["end_time"] = datetime.now().isoformat()
        self.checkpoint()

    def mark_failed(self, error: str) -> None:
        """
        Mark execution as failed.

        Args:
            error: Error message
        """
        self.state["status"] = "failed"
        self.state["error"] = error
        self.state["end_time"] = datetime.now().isoformat()
        self.checkpoint()

    def can_resume(self) -> bool:
        """
        Check if this state can be resumed.

        Returns:
            True if state is resumable, False otherwise
        """
        return (
            self.state.get("status") == "running" and
            self.state.get("iteration", 0) > 0 and
            len(self.state.get("conversation_history", [])) > 0
        )

    def get_resume_info(self) -> Dict[str, Any]:
        """
        Get information needed to resume execution.

        Returns:
            Dictionary with agent name, iteration, and conversation history
        """
        return {
            "agent_name": self.state.get("agent_name"),
            "iteration": self.state.get("iteration"),
            "conversation_history": self.state.get("conversation_history", []),
            "input_data": self.state.get("input_data", {}),
            "spawned_agents_count": len(self.state.get("spawned_agents", []))
        }

    def cleanup(self) -> None:
        """Remove state file if it exists."""
        if self.state_file and self.state_file.exists():
            try:
                self.state_file.unlink()
                logger.info(f"Cleaned up state file: {self.state_file}")
            except Exception as e:
                logger.error(f"Failed to cleanup state file: {e}")
