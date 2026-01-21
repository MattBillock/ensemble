"""
Unit tests for state module.

Tests the StateManager class for execution state management.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock


class TestStateManager:
    """Test StateManager class."""

    @pytest.fixture
    def temp_state_file(self):
        """Create a temporary state file path."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            state_path = Path(f.name)
        # Delete the file so we can test creation
        state_path.unlink()
        yield state_path
        try:
            state_path.unlink()
        except:
            pass

    @pytest.fixture
    def manager(self, temp_state_file):
        """Create a StateManager instance."""
        from src.runtime.agents.state import StateManager
        return StateManager(state_file=temp_state_file)

    def test_init_without_state_file(self):
        """Test initialization without state file."""
        from src.runtime.agents.state import StateManager

        manager = StateManager(state_file=None)

        assert manager.state_file is None
        assert manager.state["status"] == "running"
        assert manager.state["iteration"] == 0

    def test_init_with_state_file(self, temp_state_file):
        """Test initialization with state file path."""
        from src.runtime.agents.state import StateManager

        manager = StateManager(state_file=temp_state_file)

        assert manager.state_file == temp_state_file

    def test_init_loads_existing_state(self, temp_state_file):
        """Test that existing state is loaded on init."""
        from src.runtime.agents.state import StateManager

        # Create an existing state file
        existing_state = {
            "agent_name": "Existing Agent",
            "iteration": 5,
            "conversation_history": [],
            "spawned_agents": [],
            "tool_results": [],
            "start_time": "2024-01-01T00:00:00",
            "last_checkpoint": None,
            "input_data": {"test": "data"},
            "status": "running"
        }
        temp_state_file.write_text(json.dumps(existing_state))

        manager = StateManager(state_file=temp_state_file)

        assert manager.state["agent_name"] == "Existing Agent"
        assert manager.state["iteration"] == 5

    def test_init_execution(self, manager):
        """Test initializing a new execution."""
        manager.init_execution(
            agent_name="Test Agent",
            input_data={"problem": "test problem"}
        )

        assert manager.state["agent_name"] == "Test Agent"
        assert manager.state["iteration"] == 0
        assert manager.state["input_data"]["problem"] == "test problem"
        assert manager.state["status"] == "running"
        assert manager.state["start_time"] is not None

    def test_record_iteration(self, manager):
        """Test recording an iteration."""
        manager.init_execution("Test Agent", {})

        manager.record_iteration(1, {
            "role": "assistant",
            "content": "Test response"
        })

        assert manager.state["iteration"] == 1
        assert len(manager.state["conversation_history"]) == 1
        assert manager.state["conversation_history"][0]["role"] == "assistant"
        assert manager.state["conversation_history"][0]["iteration"] == 1

    def test_record_iteration_serializes_content(self, manager):
        """Test that content is properly serialized."""
        manager.init_execution("Test Agent", {})

        # Simulate Anthropic object with model_dump method
        mock_block = MagicMock()
        mock_block.model_dump.return_value = {"type": "text", "text": "Hello"}

        manager.record_iteration(1, {
            "role": "assistant",
            "content": [mock_block]
        })

        assert len(manager.state["conversation_history"]) == 1
        content = manager.state["conversation_history"][0]["content"]
        assert content[0] == {"type": "text", "text": "Hello"}

    def test_make_serializable_list(self, manager):
        """Test serializing lists."""
        result = manager._make_serializable([1, 2, 3])

        assert result == [1, 2, 3]

    def test_make_serializable_dict(self, manager):
        """Test serializing dicts."""
        result = manager._make_serializable({"key": "value"})

        assert result == {"key": "value"}

    def test_make_serializable_anthropic_object(self, manager):
        """Test serializing Anthropic objects."""
        mock_obj = MagicMock()
        mock_obj.model_dump.return_value = {"serialized": True}

        result = manager._make_serializable(mock_obj)

        assert result == {"serialized": True}

    def test_make_serializable_primitive(self, manager):
        """Test serializing primitive types."""
        assert manager._make_serializable("string") == "string"
        assert manager._make_serializable(123) == 123
        assert manager._make_serializable(True) is True
        assert manager._make_serializable(None) is None

    def test_record_tool_result(self, manager):
        """Test recording tool results."""
        manager.init_execution("Test Agent", {})

        manager.record_tool_result(
            tool_name="write_file",
            inputs={"path": "/test.py"},
            result={"success": True}
        )

        assert len(manager.state["tool_results"]) == 1
        assert manager.state["tool_results"][0]["tool"] == "write_file"
        assert manager.state["tool_results"][0]["result"]["success"] is True

    def test_record_tool_result_spawn_agent(self, manager):
        """Test that spawn_agent results are tracked separately."""
        manager.init_execution("Test Agent", {})

        manager.record_tool_result(
            tool_name="spawn_agent",
            inputs={"agent_type": "developer"},
            result={"success": True, "result": {"agent_id": "agent-1"}}
        )

        assert len(manager.state["spawned_agents"]) == 1
        assert manager.state["spawned_agents"][0]["agent_type"] == "developer"
        assert manager.state["spawned_agents"][0]["success"] is True

    def test_checkpoint_saves_state(self, manager, temp_state_file):
        """Test that checkpoint saves state to disk."""
        manager.init_execution("Test Agent", {"test": "data"})
        manager.checkpoint()

        assert temp_state_file.exists()

        saved_state = json.loads(temp_state_file.read_text())
        assert saved_state["agent_name"] == "Test Agent"

    def test_checkpoint_without_state_file(self):
        """Test checkpoint does nothing without state file."""
        from src.runtime.agents.state import StateManager

        manager = StateManager(state_file=None)
        manager.init_execution("Test Agent", {})

        # Should not raise
        manager.checkpoint()

    def test_load_returns_false_without_file(self, temp_state_file):
        """Test load returns False when file doesn't exist."""
        from src.runtime.agents.state import StateManager

        # Don't create the file
        manager = StateManager(state_file=temp_state_file)

        result = manager.load()

        assert result is False

    def test_load_success(self, temp_state_file):
        """Test successful state load."""
        from src.runtime.agents.state import StateManager

        # Create state file
        existing_state = {
            "agent_name": "Test Agent",
            "iteration": 3,
            "conversation_history": [],
            "spawned_agents": [],
            "tool_results": [],
            "start_time": "2024-01-01T00:00:00",
            "last_checkpoint": None,
            "input_data": {},
            "status": "running"
        }
        temp_state_file.write_text(json.dumps(existing_state))

        manager = StateManager(state_file=temp_state_file)
        result = manager.load()

        assert result is True
        assert manager.state["agent_name"] == "Test Agent"

    def test_mark_completed(self, manager):
        """Test marking execution as completed."""
        manager.init_execution("Test Agent", {})

        manager.mark_completed({"output": "result"})

        assert manager.state["status"] == "completed"
        assert manager.state["final_result"] == {"output": "result"}
        assert manager.state["end_time"] is not None

    def test_mark_failed(self, manager):
        """Test marking execution as failed."""
        manager.init_execution("Test Agent", {})

        manager.mark_failed("Test error message")

        assert manager.state["status"] == "failed"
        assert manager.state["error"] == "Test error message"
        assert manager.state["end_time"] is not None

    def test_can_resume_true(self, manager):
        """Test can_resume returns True for valid state."""
        manager.init_execution("Test Agent", {})
        manager.record_iteration(1, {"role": "assistant", "content": "Test"})

        assert manager.can_resume() is True

    def test_can_resume_false_no_iterations(self, manager):
        """Test can_resume returns False with no iterations."""
        manager.init_execution("Test Agent", {})

        assert manager.can_resume() is False

    def test_can_resume_false_completed(self, manager):
        """Test can_resume returns False for completed execution."""
        manager.init_execution("Test Agent", {})
        manager.record_iteration(1, {"role": "assistant", "content": "Test"})
        manager.mark_completed({"result": "done"})

        assert manager.can_resume() is False

    def test_get_resume_info(self, manager):
        """Test getting resume information."""
        manager.init_execution("Test Agent", {"input": "data"})
        manager.record_iteration(1, {"role": "assistant", "content": "Test"})
        manager.record_tool_result("spawn_agent", {"agent_type": "dev"}, {"success": True})

        info = manager.get_resume_info()

        assert info["agent_name"] == "Test Agent"
        assert info["iteration"] == 1
        assert len(info["conversation_history"]) == 1
        assert info["input_data"] == {"input": "data"}
        assert info["spawned_agents_count"] == 1

    def test_cleanup(self, manager, temp_state_file):
        """Test cleanup removes state file."""
        manager.init_execution("Test Agent", {})
        manager.checkpoint()

        assert temp_state_file.exists()

        manager.cleanup()

        assert not temp_state_file.exists()

    def test_cleanup_without_file(self):
        """Test cleanup does nothing without file."""
        from src.runtime.agents.state import StateManager

        manager = StateManager(state_file=None)

        # Should not raise
        manager.cleanup()
