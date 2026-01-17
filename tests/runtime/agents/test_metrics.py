"""
Unit tests for metrics module.

Tests the AgentMetricsTracker class for performance metrics tracking.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta


class TestAgentMetricsTracker:
    """Test AgentMetricsTracker class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        try:
            db_path.unlink()
        except:
            pass

    @pytest.fixture
    def tracker(self, temp_db):
        """Create a AgentMetricsTracker instance."""
        from src.runtime.agents.metrics import AgentMetricsTracker
        return AgentMetricsTracker(db_path=temp_db)

    def test_init_creates_database(self, temp_db):
        """Test that initialization creates the database."""
        from src.runtime.agents.metrics import AgentMetricsTracker

        tracker = AgentMetricsTracker(db_path=temp_db)

        assert temp_db.exists()

    def test_init_creates_tables(self, tracker):
        """Test that initialization creates required tables."""
        with tracker._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='agent_executions'"
            )
            assert cursor.fetchone() is not None

    def test_record_execution(self, tracker):
        """Test recording an execution."""
        now = datetime.now().isoformat()

        record_id = tracker.record_execution(
            agent_id="agent-1",
            agent_type="developer",
            agent_name="Test Agent",
            model_used="claude-sonnet-4-5-20250929",
            task_complexity="routine",
            budget_tier="balanced",
            success=True,
            duration_ms=5000,
            iterations=5,
            created_at=now,
            completed_at=now,
            request_id="req-1"
        )

        assert record_id is not None
        assert record_id > 0

    def test_record_execution_with_all_params(self, tracker):
        """Test recording with all parameters."""
        now = datetime.now().isoformat()

        record_id = tracker.record_execution(
            agent_id="agent-1",
            agent_type="developer",
            agent_name="Test Agent",
            model_used="claude-sonnet-4-5-20250929",
            task_complexity="strategic",
            budget_tier="full_firepower",
            success=False,
            duration_ms=10000,
            iterations=10,
            created_at=now,
            completed_at=now,
            request_id="req-1",
            parent_agent_id="parent-1",
            spawned_agents_count=3,
            error_type="timeout",
            tokens_used=5000,
            input_tokens=3000,
            output_tokens=2000,
            estimated_cost=0.05,
            task_description="Test task",
            self_analysis="Test analysis",
            performance_analysis="Performance notes"
        )

        assert record_id is not None

    def test_record_execution_empty_name_fallback(self, tracker):
        """Test that empty agent_name uses fallback."""
        now = datetime.now().isoformat()

        record_id = tracker.record_execution(
            agent_id="leadership/tdd_coordinator_123",
            agent_type="coordinator",
            agent_name="",
            model_used="claude-sonnet-4-5-20250929",
            task_complexity="routine",
            budget_tier="balanced",
            success=True,
            duration_ms=1000,
            iterations=1,
            created_at=now,
            completed_at=now,
            request_id="req-1"
        )

        # Should still create record with fallback name
        assert record_id is not None

    def test_get_success_rate_by_agent(self, tracker):
        """Test getting success rates by agent."""
        now = datetime.now().isoformat()

        # Record some executions
        for i in range(5):
            tracker.record_execution(
                agent_id=f"agent-{i}",
                agent_type="developer",
                agent_name="Test Agent",
                model_used="claude-sonnet-4-5-20250929",
                task_complexity="routine",
                budget_tier="balanced",
                success=i % 2 == 0,  # Alternating success/failure
                duration_ms=1000,
                iterations=1,
                created_at=now,
                completed_at=now,
                request_id="req-1"
            )

        result = tracker.get_success_rate_by_agent(days=30)

        assert "period_days" in result
        assert "agents" in result
        assert len(result["agents"]) == 1
        assert result["agents"][0]["total_executions"] == 5

    def test_get_success_rate_by_agent_filtered(self, tracker):
        """Test getting success rates filtered by agent name."""
        now = datetime.now().isoformat()

        # Record executions for different agents
        tracker.record_execution(
            agent_id="agent-1",
            agent_type="developer",
            agent_name="Agent A",
            model_used="claude-sonnet-4-5-20250929",
            task_complexity="routine",
            budget_tier="balanced",
            success=True,
            duration_ms=1000,
            iterations=1,
            created_at=now,
            completed_at=now,
            request_id="req-1"
        )
        tracker.record_execution(
            agent_id="agent-2",
            agent_type="developer",
            agent_name="Agent B",
            model_used="claude-sonnet-4-5-20250929",
            task_complexity="routine",
            budget_tier="balanced",
            success=True,
            duration_ms=1000,
            iterations=1,
            created_at=now,
            completed_at=now,
            request_id="req-1"
        )

        result = tracker.get_success_rate_by_agent(agent_name="Agent A", days=30)

        assert len(result["agents"]) == 1
        assert result["agents"][0]["agent_name"] == "Agent A"

    def test_get_success_rate_by_model(self, tracker):
        """Test getting success rates by model."""
        now = datetime.now().isoformat()

        models = ["claude-sonnet-4-5-20250929", "claude-3-5-haiku-20241022"]
        for model in models:
            tracker.record_execution(
                agent_id=f"agent-{model}",
                agent_type="developer",
                agent_name="Test Agent",
                model_used=model,
                task_complexity="routine",
                budget_tier="balanced",
                success=True,
                duration_ms=1000,
                iterations=1,
                created_at=now,
                completed_at=now,
                request_id="req-1"
            )

        result = tracker.get_success_rate_by_model(days=30)

        assert "models" in result
        assert len(result["models"]) == 2

    def test_get_success_rate_by_complexity(self, tracker):
        """Test getting success rates by task complexity."""
        now = datetime.now().isoformat()

        complexities = ["routine", "creative", "strategic"]
        for complexity in complexities:
            tracker.record_execution(
                agent_id=f"agent-{complexity}",
                agent_type="developer",
                agent_name="Test Agent",
                model_used="claude-sonnet-4-5-20250929",
                task_complexity=complexity,
                budget_tier="balanced",
                success=True,
                duration_ms=1000,
                iterations=1,
                created_at=now,
                completed_at=now,
                request_id="req-1"
            )

        result = tracker.get_success_rate_by_complexity(days=30)

        assert "complexities" in result
        assert len(result["complexities"]) == 3

    def test_get_agent_model_correlation(self, tracker):
        """Test getting model correlation for an agent."""
        now = datetime.now().isoformat()

        models = ["claude-sonnet-4-5-20250929", "claude-3-5-haiku-20241022"]
        for model in models:
            tracker.record_execution(
                agent_id=f"agent-{model}",
                agent_type="developer",
                agent_name="Test Agent",
                model_used=model,
                task_complexity="routine",
                budget_tier="balanced",
                success=True,
                duration_ms=1000,
                iterations=1,
                created_at=now,
                completed_at=now,
                request_id="req-1"
            )

        result = tracker.get_agent_model_correlation("Test Agent", days=30)

        assert result["agent_name"] == "Test Agent"
        assert "model_performance" in result
        assert len(result["model_performance"]) == 2

    def test_get_error_analysis(self, tracker):
        """Test error analysis."""
        now = datetime.now().isoformat()

        error_types = ["timeout", "rate_limit", "validation_error"]
        for error in error_types:
            tracker.record_execution(
                agent_id=f"agent-{error}",
                agent_type="developer",
                agent_name="Test Agent",
                model_used="claude-sonnet-4-5-20250929",
                task_complexity="routine",
                budget_tier="balanced",
                success=False,
                duration_ms=1000,
                iterations=1,
                created_at=now,
                completed_at=now,
                request_id="req-1",
                error_type=error
            )

        result = tracker.get_error_analysis(days=30)

        assert "errors" in result
        assert len(result["errors"]) == 3

    def test_get_performance_trends(self, tracker):
        """Test performance trends."""
        now = datetime.now()

        # Record executions over multiple days
        for i in range(3):
            day = (now - timedelta(days=i)).isoformat()
            tracker.record_execution(
                agent_id=f"agent-{i}",
                agent_type="developer",
                agent_name="Test Agent",
                model_used="claude-sonnet-4-5-20250929",
                task_complexity="routine",
                budget_tier="balanced",
                success=True,
                duration_ms=1000,
                iterations=1,
                created_at=day,
                completed_at=day,
                request_id="req-1"
            )

        result = tracker.get_performance_trends(days=30)

        assert "daily_trends" in result
        assert len(result["daily_trends"]) >= 1

    def test_get_self_analyses(self, tracker):
        """Test getting self analyses."""
        now = datetime.now().isoformat()

        tracker.record_execution(
            agent_id="agent-1",
            agent_type="developer",
            agent_name="Test Agent",
            model_used="claude-sonnet-4-5-20250929",
            task_complexity="routine",
            budget_tier="balanced",
            success=True,
            duration_ms=1000,
            iterations=1,
            created_at=now,
            completed_at=now,
            request_id="req-1",
            self_analysis="I did well",
            performance_analysis="Good performance"
        )

        result = tracker.get_self_analyses(limit=10)

        assert len(result) == 1
        assert result[0]["self_analysis"] == "I did well"

    def test_get_summary_stats(self, tracker):
        """Test getting summary statistics."""
        now = datetime.now().isoformat()

        for i in range(5):
            tracker.record_execution(
                agent_id=f"agent-{i}",
                agent_type="developer",
                agent_name="Test Agent",
                model_used="claude-sonnet-4-5-20250929",
                task_complexity="routine",
                budget_tier="balanced",
                success=True,
                duration_ms=1000,
                iterations=1,
                created_at=now,
                completed_at=now,
                request_id="req-1",
                spawned_agents_count=1,
                input_tokens=100,
                output_tokens=50,
                estimated_cost=0.001
            )

        result = tracker.get_summary_stats(days=30)

        assert "overall" in result
        assert result["overall"]["total_executions"] == 5
        assert "most_active_agents" in result
        assert "best_performing_agents" in result

    def test_get_recent_executions(self, tracker):
        """Test getting recent executions."""
        now = datetime.now().isoformat()

        for i in range(3):
            tracker.record_execution(
                agent_id=f"agent-{i}",
                agent_type="developer",
                agent_name=f"Agent {i}",
                model_used="claude-sonnet-4-5-20250929",
                task_complexity="routine",
                budget_tier="balanced",
                success=True,
                duration_ms=1000,
                iterations=1,
                created_at=now,
                completed_at=now,
                request_id="req-1"
            )

        result = tracker.get_recent_executions(limit=5)

        assert len(result) == 3
        assert "agent_name" in result[0]
        assert "model_used" in result[0]
