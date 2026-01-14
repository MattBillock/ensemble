"""Unit tests for AgentActivityTracker.record_agent_completed method."""
import os
import sys
import pytest

# Add the project root to the path to import the tracker module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from runtime.agents.activity_tracker import AgentActivityTracker


class TestRecordAgentCompletedFieldExtraction:
    """Test suite for record_agent_completed result field extraction."""

    @pytest.fixture
    def tracker(self):
        """Create a fresh AgentActivityTracker instance for each test."""
        tracker = AgentActivityTracker()
        # Initialize an agent first so we have agent_states to update
        tracker.record_agent_started(
            agent_id="test_agent_1",
            agent_name="Test Agent",
            agent_type="test",
            request_id="req_123"
        )
        return tracker

    def test_summary_field_extracted_from_result(self, tracker):
        """Test that summary field is set from result['summary']."""
        # Arrange
        agent_id = "test_agent_1"
        result = {
            "summary": "Task completed successfully with all objectives met",
            "status": "success"
        }
        
        # Act
        tracker.record_agent_completed(
            agent_id=agent_id,
            agent_name="Test Agent",
            request_id="req_123",
            result=result
        )
        
        # Assert
        agent_state = tracker.get_agent_state(agent_id)
        assert agent_state is not None, "Agent state should exist"
        assert "summary" in agent_state, "Summary field should be in agent state"
        assert agent_state["summary"] == "Task completed successfully with all objectives met", \
            "Summary should match the value from result['summary']"

    def test_summary_fallback_to_message(self, tracker):
        """Test that summary field falls back to result['message'] if no summary key."""
        # Arrange
        agent_id = "test_agent_1"
        result = {
            "message": "Operation completed with fallback message",
            "status": "success"
        }
        
        # Act
        tracker.record_agent_completed(
            agent_id=agent_id,
            agent_name="Test Agent",
            request_id="req_123",
            result=result
        )
        
        # Assert
        agent_state = tracker.get_agent_state(agent_id)
        assert agent_state is not None, "Agent state should exist"
        assert "summary" in agent_state, "Summary field should be in agent state"
        assert agent_state["summary"] == "Operation completed with fallback message", \
            "Summary should fall back to result['message'] when summary key is missing"

    def test_self_analysis_field_extracted(self, tracker):
        """Test that self_analysis field is set from result['self_analysis']."""
        # Arrange
        agent_id = "test_agent_1"
        result = {
            "self_analysis": "Agent performed well, completed task in 3 iterations",
            "status": "success"
        }
        
        # Act
        tracker.record_agent_completed(
            agent_id=agent_id,
            agent_name="Test Agent",
            request_id="req_123",
            result=result
        )
        
        # Assert
        agent_state = tracker.get_agent_state(agent_id)
        assert agent_state is not None, "Agent state should exist"
        assert "self_analysis" in agent_state, "self_analysis field should be in agent state"
        assert agent_state["self_analysis"] == "Agent performed well, completed task in 3 iterations", \
            "self_analysis should match the value from result['self_analysis']"

    def test_deliverables_field_extracted(self, tracker):
        """Test that deliverables field is set from result['deliverables'] list."""
        # Arrange
        agent_id = "test_agent_1"
        result = {
            "deliverables": [
                "file1.py",
                "file2.txt",
                "output.json"
            ],
            "status": "success"
        }
        
        # Act
        tracker.record_agent_completed(
            agent_id=agent_id,
            agent_name="Test Agent",
            request_id="req_123",
            result=result
        )
        
        # Assert
        agent_state = tracker.get_agent_state(agent_id)
        assert agent_state is not None, "Agent state should exist"
        assert "deliverables" in agent_state, "deliverables field should be in agent state"
        assert isinstance(agent_state["deliverables"], list), "deliverables should be a list"
        assert len(agent_state["deliverables"]) == 3, "deliverables list should have 3 items"
        assert agent_state["deliverables"] == ["file1.py", "file2.txt", "output.json"], \
            "deliverables should match the list from result['deliverables']"

    def test_none_result_doesnt_add_extra_fields(self, tracker):
        """Test that None result doesn't add extra fields to agent_states."""
        # Arrange
        agent_id = "test_agent_1"
        
        # Act
        tracker.record_agent_completed(
            agent_id=agent_id,
            agent_name="Test Agent",
            request_id="req_123",
            result=None
        )
        
        # Assert
        agent_state = tracker.get_agent_state(agent_id)
        assert agent_state is not None, "Agent state should exist"
        # Check that no extra fields were added
        assert "summary" not in agent_state, "summary field should not be added when result is None"
        assert "self_analysis" not in agent_state, "self_analysis field should not be added when result is None"
        assert "deliverables" not in agent_state, "deliverables field should not be added when result is None"
        # Basic fields should still be present
        assert agent_state["status"] == "completed", "Status should be set to completed"

    def test_all_fields_extracted_together(self, tracker):
        """Test that all fields (summary, self_analysis, deliverables) are extracted together."""
        # Arrange
        agent_id = "test_agent_1"
        result = {
            "summary": "Complete analysis finished",
            "self_analysis": "All objectives achieved efficiently",
            "deliverables": ["report.pdf", "data.csv"],
            "status": "success",
            "other_field": "ignored"
        }
        
        # Act
        tracker.record_agent_completed(
            agent_id=agent_id,
            agent_name="Test Agent",
            request_id="req_123",
            result=result
        )
        
        # Assert
        agent_state = tracker.get_agent_state(agent_id)
        assert agent_state is not None, "Agent state should exist"
        assert agent_state["summary"] == "Complete analysis finished", \
            "summary should be extracted"
        assert agent_state["self_analysis"] == "All objectives achieved efficiently", \
            "self_analysis should be extracted"
        assert agent_state["deliverables"] == ["report.pdf", "data.csv"], \
            "deliverables should be extracted"
        assert agent_state["status"] == "completed", \
            "status should still be set to completed"

    def test_empty_result_dict_doesnt_cause_errors(self, tracker):
        """Test that empty result dict doesn't cause errors."""
        # Arrange
        agent_id = "test_agent_1"
        result = {}
        
        # Act
        tracker.record_agent_completed(
            agent_id=agent_id,
            agent_name="Test Agent",
            request_id="req_123",
            result=result
        )
        
        # Assert
        agent_state = tracker.get_agent_state(agent_id)
        assert agent_state is not None, "Agent state should exist"
        # Verify no errors occurred and basic fields are set
        assert agent_state["status"] == "completed", "Status should be set to completed"
        assert agent_state["current_task"] == "Completed", "Current task should be set"
        # Empty result should not add optional fields
        assert "summary" not in agent_state or agent_state.get("summary") is None, \
            "summary should not be set for empty result dict"
