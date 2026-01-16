"""
Tests for pending review functionality in swarm_state.py
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.runtime.agents.swarm_state import SwarmStateManager


# Ensure each test gets a fresh database by resetting the singleton


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    # Create manager with temp db - bypass singleton completely
    # SwarmStateManager uses a singleton pattern via __new__, so we need to reset it
    original_instance = SwarmStateManager._instance
    original_initialized = getattr(SwarmStateManager, '_instance_initialized', None)

    # Reset the singleton
    SwarmStateManager._instance = None

    # Create new manager with specific db_path
    manager = SwarmStateManager(db_path=db_path)

    yield manager

    # Restore original singleton state
    SwarmStateManager._instance = original_instance
    if original_initialized is not None:
        SwarmStateManager._instance_initialized = original_initialized

    try:
        os.unlink(db_path)
    except OSError:
        pass


class TestPendingReviewsCRUD:
    """Test pending reviews CRUD operations."""

    def test_add_pending_review(self, temp_db):
        """Test adding a pending review."""
        review_id = temp_db.add_pending_review(
            file_path="src/output/requirements.md",
            file_type="markdown",
            detection_method="auto",
            review_type="requirements",
            action="start_implementation",
            action_params={"budget_tier": "balanced"},
            content_preview="# Requirements\n\nThis is a test."
        )

        assert review_id is not None
        assert review_id > 0

    def test_add_pending_review_with_agent_info(self, temp_db):
        """Test adding a pending review with agent information."""
        review_id = temp_db.add_pending_review(
            file_path="src/output/architecture.md",
            file_type="markdown",
            detection_method="explicit",
            review_type="architecture",
            action="start_implementation",
            session_id="session-123",
            request_id="req-456",
            agent_id="agent-789",
            agent_name="System Architect"
        )

        review = temp_db.get_pending_review(review_id)
        assert review is not None
        assert review["agent_id"] == "agent-789"
        assert review["agent_name"] == "System Architect"

    def test_get_pending_review(self, temp_db):
        """Test retrieving a single pending review."""
        review_id = temp_db.add_pending_review(
            file_path="src/output/test_plan.md",
            file_type="markdown",
            detection_method="auto",
            review_type="test_plan",
            action="create_tests"
        )

        review = temp_db.get_pending_review(review_id)

        assert review is not None
        assert review["file_path"] == "src/output/test_plan.md"
        assert review["review_type"] == "test_plan"
        assert review["action"] == "create_tests"
        assert review["status"] == "pending"

    def test_get_pending_review_not_found(self, temp_db):
        """Test retrieving a non-existent review."""
        review = temp_db.get_pending_review(99999)
        assert review is None

    def test_get_pending_reviews_list(self, temp_db):
        """Test retrieving list of pending reviews."""
        # Add multiple reviews
        for i in range(5):
            temp_db.add_pending_review(
                file_path=f"src/output/file_{i}.md",
                file_type="markdown",
                detection_method="auto",
                review_type="requirements"
            )

        reviews = temp_db.get_pending_reviews(status="pending")

        assert len(reviews) == 5

    def test_get_pending_reviews_with_limit(self, temp_db):
        """Test retrieving reviews with limit."""
        for i in range(10):
            temp_db.add_pending_review(
                file_path=f"src/output/file_{i}.md",
                file_type="markdown",
                detection_method="auto"
            )

        reviews = temp_db.get_pending_reviews(limit=5)
        assert len(reviews) == 5

    def test_get_pending_reviews_with_offset(self, temp_db):
        """Test retrieving reviews with offset."""
        for i in range(10):
            temp_db.add_pending_review(
                file_path=f"src/output/file_{i}.md",
                file_type="markdown",
                detection_method="auto"
            )

        reviews = temp_db.get_pending_reviews(limit=5, offset=5)
        assert len(reviews) == 5

    def test_is_file_tracked_for_review(self, temp_db):
        """Test checking if file is already tracked."""
        file_path = "src/output/tracked_file.md"

        # Should not be tracked initially
        assert temp_db.is_file_tracked_for_review(file_path) is False

        # Add review
        temp_db.add_pending_review(
            file_path=file_path,
            file_type="markdown",
            detection_method="auto"
        )

        # Should now be tracked
        assert temp_db.is_file_tracked_for_review(file_path) is True

    def test_update_pending_review_status(self, temp_db):
        """Test updating review status."""
        review_id = temp_db.add_pending_review(
            file_path="src/output/to_approve.md",
            file_type="markdown",
            detection_method="auto"
        )

        # Update to approved
        temp_db.update_pending_review(review_id, status="approved")

        review = temp_db.get_pending_review(review_id)
        assert review["status"] == "approved"
        assert review["reviewed_by"] == "user"
        assert review["reviewed_at"] is not None

    def test_update_pending_review_with_result(self, temp_db):
        """Test updating review with execution result."""
        review_id = temp_db.add_pending_review(
            file_path="src/output/executed.md",
            file_type="markdown",
            detection_method="auto"
        )

        result = {"agent_id": "exec_123", "status": "success"}
        temp_db.update_pending_review(
            review_id,
            status="approved",
            execution_result=result
        )

        review = temp_db.get_pending_review(review_id)
        assert review["status"] == "approved"
        # execution_result is stored as JSON string, retrieved as dict
        assert "exec_123" in str(review.get("execution_result", ""))

    def test_get_reviews_by_status(self, temp_db):
        """Test filtering reviews by status."""
        # Add pending review
        temp_db.add_pending_review(
            file_path="src/output/pending.md",
            file_type="markdown",
            detection_method="auto"
        )

        # Add and approve another
        approved_id = temp_db.add_pending_review(
            file_path="src/output/approved.md",
            file_type="markdown",
            detection_method="auto"
        )
        temp_db.update_pending_review(approved_id, status="approved")

        pending = temp_db.get_pending_reviews(status="pending")
        approved = temp_db.get_pending_reviews(status="approved")

        assert len(pending) == 1
        assert len(approved) == 1
        assert pending[0]["file_path"] == "src/output/pending.md"
        assert approved[0]["file_path"] == "src/output/approved.md"


class TestAgentImprovementReports:
    """Test agent improvement reports functionality."""

    def test_add_improvement_report(self, temp_db):
        """Test adding an improvement report."""
        report_id = temp_db.add_improvement_report(
            agent_id="agent-123",
            agent_name="Test Agent",
            issue_type="missing_explicit_marking",
            file_path="src/output/unmarked.md",
            detection_method="auto",
            severity="warning",
            recommendation="Add YAML frontmatter with review_type field."
        )

        assert report_id is not None
        assert report_id > 0

    def test_get_improvement_reports(self, temp_db):
        """Test retrieving improvement reports."""
        # Add multiple reports
        for i in range(3):
            temp_db.add_improvement_report(
                agent_id=f"agent-{i}",
                agent_name=f"Agent {i}",
                issue_type="missing_explicit_marking",
                file_path=f"src/output/file_{i}.md",
                detection_method="auto"
            )

        reports = temp_db.get_improvement_reports()

        assert len(reports) == 3

    def test_get_improvement_reports_by_agent(self, temp_db):
        """Test filtering reports by agent."""
        # Add reports for different agents
        for i in range(2):
            temp_db.add_improvement_report(
                agent_id="agent-a",
                agent_name="Agent A",
                issue_type="missing_explicit_marking",
                file_path=f"src/output/a_{i}.md",
                detection_method="auto"
            )

        temp_db.add_improvement_report(
            agent_id="agent-b",
            agent_name="Agent B",
            issue_type="missing_explicit_marking",
            file_path="src/output/b.md",
            detection_method="auto"
        )

        reports_a = temp_db.get_improvement_reports(agent_id="agent-a")
        reports_b = temp_db.get_improvement_reports(agent_id="agent-b")

        assert len(reports_a) == 2
        assert len(reports_b) == 1

    def test_improvement_report_with_session_info(self, temp_db):
        """Test adding report with session information."""
        report_id = temp_db.add_improvement_report(
            agent_id="agent-xyz",
            agent_name="Session Agent",
            issue_type="missing_explicit_marking",
            file_path="src/output/session_file.md",
            detection_method="auto",
            session_id="session-abc",
            request_id="req-def"
        )

        reports = temp_db.get_improvement_reports(agent_id="agent-xyz")
        assert len(reports) == 1
        assert reports[0]["session_id"] == "session-abc"
        assert reports[0]["request_id"] == "req-def"


class TestActionParams:
    """Test action_params JSON handling."""

    def test_action_params_stored_as_json(self, temp_db):
        """Test that action_params is properly serialized and deserialized."""
        params = {
            "budget_tier": "full_firepower",
            "auto_continue": True,
            "custom_option": "value"
        }

        review_id = temp_db.add_pending_review(
            file_path="src/output/params_test.md",
            file_type="markdown",
            detection_method="explicit",
            action_params=params
        )

        review = temp_db.get_pending_review(review_id)

        assert review["action_params"] == params
        assert review["action_params"]["budget_tier"] == "full_firepower"
        assert review["action_params"]["auto_continue"] is True

    def test_action_params_none(self, temp_db):
        """Test handling of None action_params."""
        review_id = temp_db.add_pending_review(
            file_path="src/output/no_params.md",
            file_type="markdown",
            detection_method="auto",
            action_params=None
        )

        review = temp_db.get_pending_review(review_id)
        # Should handle None gracefully
        assert review is not None
