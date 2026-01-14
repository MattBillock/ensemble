"""TDD tests for AgentActivityTracker.record_agent_completed() summary field extraction.

These tests define the EXPECTED behavior for extracting summary fields from result dict
and storing them in agent_states. The current implementation does NOT do this yet.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from runtime.agents.activity_tracker import AgentActivityTracker, ActivityType


@pytest.fixture
def tracker():
    """Create a fresh AgentActivityTracker instance."""
    return AgentActivityTracker()


@pytest.fixture
def mock_datetime():
    """Mock datetime.now() to return a fixed timestamp."""
    fixed_time = datetime(2024, 1, 15, 10, 30, 0)
    with patch('runtime.agents.activity_tracker.datetime') as mock_dt:
        mock_dt.now.return_value = fixed_time
        yield mock_dt


@pytest.fixture
def initialized_agent(tracker, mock_datetime):
    """Create a tracker with an initialized agent."""
    agent_id = "test-agent-001"
    agent_name = "TestAgent"
    agent_type = "test_agent"
    request_id = "req-001"
    
    tracker.record_agent_started(
        agent_id=agent_id,
        agent_name=agent_name,
        agent_type=agent_type,
        request_id=request_id,
        input_data={"task": "test task"}
    )
    
    return {
        "tracker": tracker,
        "agent_id": agent_id,
        "agent_name": agent_name,
        "request_id": request_id
    }


class TestRecordAgentCompletedSummaryExtraction:
    """Test suite for record_agent_completed() summary field extraction functionality."""

    def test_record_agent_completed_stores_summary(self, initialized_agent, mock_datetime):
        """
        Verify all summary fields are stored in agent_states when result contains all fields.
        
        This is the core TDD test - the current implementation does NOT extract these fields.
        Expected behavior:
        - Extract 'status' from result and store in agent_states[agent_id]['status']
        - Extract 'completion_report' and store in agent_states[agent_id]['completion_report']
        - Extract 'summary' and store in agent_states[agent_id]['summary']
        - Extract 'next_steps' and store in agent_states[agent_id]['next_steps']
        - Emit activity with AGENT_COMPLETED type
        """
        # Arrange
        tracker = initialized_agent["tracker"]
        agent_id = initialized_agent["agent_id"]
        agent_name = initialized_agent["agent_name"]
        request_id = initialized_agent["request_id"]
        
        result = {
            'status': 'success',
            'completion_report': 'Task completed successfully',
            'summary': 'Comprehensive work summary detailing all actions taken',
            'next_steps': 'Follow up with stakeholders and deploy changes'
        }
        
        # Act
        tracker.record_agent_completed(
            agent_id=agent_id,
            agent_name=agent_name,
            request_id=request_id,
            result=result
        )
        
        # Assert - Verify summary fields are extracted and stored in agent_states
        agent_state = tracker.agent_states[agent_id]
        
        # The agent_states should have 'status' set to 'completed'
        assert agent_state['status'] == 'completed', \
            f"Expected status to be 'completed', got '{agent_state.get('status')}'"
        
        # NEW EXPECTED BEHAVIOR: completion_report should be extracted from result
        assert 'completion_report' in agent_state, \
            "Expected 'completion_report' to be extracted from result and stored in agent_states"
        assert agent_state['completion_report'] == 'Task completed successfully', \
            f"Expected completion_report to be 'Task completed successfully', got '{agent_state.get('completion_report')}'"
        
        # NEW EXPECTED BEHAVIOR: summary should be extracted from result
        assert 'summary' in agent_state, \
            "Expected 'summary' to be extracted from result and stored in agent_states"
        assert agent_state['summary'] == 'Comprehensive work summary detailing all actions taken', \
            f"Expected summary to match result['summary'], got '{agent_state.get('summary')}'"
        
        # NEW EXPECTED BEHAVIOR: next_steps should be extracted from result
        assert 'next_steps' in agent_state, \
            "Expected 'next_steps' to be extracted from result and stored in agent_states"
        assert agent_state['next_steps'] == 'Follow up with stakeholders and deploy changes', \
            f"Expected next_steps to match result['next_steps'], got '{agent_state.get('next_steps')}'"
        
        # Verify activity was emitted with correct type
        activities = tracker.get_activities(agent_id=agent_id)
        completed_activities = [a for a in activities if a['activity_type'] == ActivityType.AGENT_COMPLETED.value]
        assert len(completed_activities) == 1, \
            f"Expected exactly 1 AGENT_COMPLETED activity, found {len(completed_activities)}"
        
        # Verify result is stored in activity data
        assert completed_activities[0]['data']['result'] == result, \
            "Expected result to be stored in activity data"

    def test_record_agent_completed_handles_none_result(self, initialized_agent, mock_datetime):
        """
        Verify agent completes gracefully when result is None.
        
        Expected behavior:
        - No exception raised
        - agent_states[agent_id]['status'] set to 'completed'
        - No summary fields added (or they default to empty)
        - Activity emitted successfully
        """
        # Arrange
        tracker = initialized_agent["tracker"]
        agent_id = initialized_agent["agent_id"]
        agent_name = initialized_agent["agent_name"]
        request_id = initialized_agent["request_id"]
        
        # Act - should not raise exception
        try:
            tracker.record_agent_completed(
                agent_id=agent_id,
                agent_name=agent_name,
                request_id=request_id,
                result=None
            )
        except Exception as e:
            pytest.fail(f"record_agent_completed raised unexpected exception with None result: {e}")
        
        # Assert
        agent_state = tracker.agent_states[agent_id]
        
        # Status should be 'completed'
        assert agent_state['status'] == 'completed', \
            f"Expected status to be 'completed' even with None result, got '{agent_state.get('status')}'"
        
        # Verify activity was emitted
        activities = tracker.get_activities(agent_id=agent_id)
        completed_activities = [a for a in activities if a['activity_type'] == ActivityType.AGENT_COMPLETED.value]
        assert len(completed_activities) == 1, \
            "Expected AGENT_COMPLETED activity to be emitted even with None result"

    def test_record_agent_completed_handles_empty_result(self, initialized_agent, mock_datetime):
        """
        Verify agent completes with defaults when result is empty dict.
        
        Expected behavior:
        - agent_states[agent_id]['status'] set to 'completed'
        - Summary fields (completion_report, summary, next_steps) default to empty string ''
        - No exception raised
        """
        # Arrange
        tracker = initialized_agent["tracker"]
        agent_id = initialized_agent["agent_id"]
        agent_name = initialized_agent["agent_name"]
        request_id = initialized_agent["request_id"]
        
        # Act
        tracker.record_agent_completed(
            agent_id=agent_id,
            agent_name=agent_name,
            request_id=request_id,
            result={}
        )
        
        # Assert
        agent_state = tracker.agent_states[agent_id]
        
        # Status should be 'completed'
        assert agent_state['status'] == 'completed', \
            f"Expected status to be 'completed' with empty result, got '{agent_state.get('status')}'"
        
        # NEW EXPECTED BEHAVIOR: Empty result should default summary fields to empty strings
        assert agent_state.get('completion_report', '') == '', \
            f"Expected completion_report to default to empty string, got '{agent_state.get('completion_report')}'"
        
        assert agent_state.get('summary', '') == '', \
            f"Expected summary to default to empty string, got '{agent_state.get('summary')}'"
        
        assert agent_state.get('next_steps', '') == '', \
            f"Expected next_steps to default to empty string, got '{agent_state.get('next_steps')}'"

    def test_record_agent_completed_handles_partial_result(self, initialized_agent, mock_datetime):
        """
        Verify partial fields are stored and missing fields default to empty string.
        
        Expected behavior:
        - Present fields (status, completion_report) are extracted and stored
        - Missing fields (summary, next_steps) default to empty string ''
        - Agent completes successfully
        """
        # Arrange
        tracker = initialized_agent["tracker"]
        agent_id = initialized_agent["agent_id"]
        agent_name = initialized_agent["agent_name"]
        request_id = initialized_agent["request_id"]
        
        # Result with only some fields
        result = {
            'status': 'success',
            'completion_report': 'Task finished'
            # Missing: 'summary' and 'next_steps'
        }
        
        # Act
        tracker.record_agent_completed(
            agent_id=agent_id,
            agent_name=agent_name,
            request_id=request_id,
            result=result
        )
        
        # Assert
        agent_state = tracker.agent_states[agent_id]
        
        # Status should be 'completed'
        assert agent_state['status'] == 'completed', \
            f"Expected status to be 'completed', got '{agent_state.get('status')}'"
        
        # NEW EXPECTED BEHAVIOR: Present fields should be stored
        assert 'completion_report' in agent_state, \
            "Expected 'completion_report' to be extracted from partial result"
        assert agent_state['completion_report'] == 'Task finished', \
            f"Expected completion_report to be 'Task finished', got '{agent_state.get('completion_report')}'"
        
        # NEW EXPECTED BEHAVIOR: Missing fields should default to empty string
        assert agent_state.get('summary', '') == '', \
            f"Expected missing 'summary' field to default to empty string, got '{agent_state.get('summary')}'"
        
        assert agent_state.get('next_steps', '') == '', \
            f"Expected missing 'next_steps' field to default to empty string, got '{agent_state.get('next_steps')}'"
