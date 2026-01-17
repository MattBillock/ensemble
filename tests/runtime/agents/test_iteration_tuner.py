"""
Unit tests for iteration_tuner module.

Tests the IterationTuner class for automatic iteration limit adjustment.
"""

import pytest
import tempfile
from pathlib import Path


class TestTuningAction:
    """Test TuningAction enum."""

    def test_tuning_action_values(self):
        """Test that all tuning actions have expected values."""
        from src.runtime.agents.iteration_tuner import TuningAction

        assert TuningAction.INCREASED.value == "increased"
        assert TuningAction.DECREASED.value == "decreased"
        assert TuningAction.UNCHANGED.value == "unchanged"
        assert TuningAction.ESCALATION_FLAGGED.value == "escalation_flagged"


class TestTunedIterationConfig:
    """Test TunedIterationConfig dataclass."""

    def test_config_creation(self):
        """Test creating a TunedIterationConfig."""
        from src.runtime.agents.iteration_tuner import TunedIterationConfig

        config = TunedIterationConfig(
            agent_name="Test Agent",
            original_max_iterations=10,
            current_tuned_iterations=12,
            success_count=5,
            failure_count=3,
            escalation_flagged=False,
            last_adjustment_at="2024-01-01T00:00:00"
        )

        assert config.agent_name == "Test Agent"
        assert config.original_max_iterations == 10
        assert config.current_tuned_iterations == 12
        assert config.success_count == 5
        assert config.failure_count == 3
        assert config.escalation_flagged is False


class TestIterationTuner:
    """Test IterationTuner class."""

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
    def tuner(self, temp_db):
        """Create a fresh IterationTuner instance."""
        from src.runtime.agents.iteration_tuner import IterationTuner

        # Reset singleton for testing
        IterationTuner._instance = None

        tuner = IterationTuner(db_path=temp_db)
        yield tuner

        # Reset singleton after test
        IterationTuner._instance = None

    def test_init_creates_database(self, temp_db):
        """Test that initialization creates database."""
        from src.runtime.agents.iteration_tuner import IterationTuner

        IterationTuner._instance = None
        tuner = IterationTuner(db_path=temp_db)

        assert temp_db.exists()

        # Verify tables created
        with tuner._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            assert "tuned_iterations" in tables
            assert "tuning_history" in tables

        IterationTuner._instance = None

    def test_singleton_pattern(self, temp_db):
        """Test singleton pattern."""
        from src.runtime.agents.iteration_tuner import IterationTuner

        IterationTuner._instance = None

        tuner1 = IterationTuner(db_path=temp_db)
        tuner2 = IterationTuner()

        assert tuner1 is tuner2

        IterationTuner._instance = None

    def test_get_tuned_iterations_not_found(self, tuner):
        """Test getting tuned iterations for unknown agent."""
        result = tuner.get_tuned_iterations("Unknown Agent")

        assert result is None

    def test_get_effective_max_iterations_no_tuning(self, tuner):
        """Test getting effective iterations with no tuning record."""
        result = tuner.get_effective_max_iterations("Test Agent", 10)

        assert result == 10

    def test_record_execution_first_success(self, tuner):
        """Test recording first successful execution."""
        from src.runtime.agents.iteration_tuner import TuningAction

        action = tuner.record_execution_result(
            agent_name="Test Agent",
            success=True,
            original_max=10,
            actual_iterations=5
        )

        assert action == TuningAction.DECREASED
        config = tuner.get_tuned_iterations("Test Agent")
        assert config is not None
        assert config.current_tuned_iterations == 9  # 10 - 1
        assert config.success_count == 1

    def test_record_execution_first_failure(self, tuner):
        """Test recording first failed execution."""
        from src.runtime.agents.iteration_tuner import TuningAction

        action = tuner.record_execution_result(
            agent_name="Test Agent",
            success=False,
            original_max=10,
            actual_iterations=10
        )

        assert action == TuningAction.INCREASED
        config = tuner.get_tuned_iterations("Test Agent")
        assert config is not None
        assert config.current_tuned_iterations == 11  # 10 + 1
        assert config.failure_count == 1

    def test_record_execution_hits_floor(self, tuner):
        """Test that iteration decrease stops at floor."""
        from src.runtime.agents.iteration_tuner import TuningAction

        # Original 10, floor is max(5, 3) = 5
        # Record many successes to hit the floor
        for _ in range(10):
            tuner.record_execution_result("Test Agent", True, 10, 5)

        config = tuner.get_tuned_iterations("Test Agent")
        assert config.current_tuned_iterations >= 5  # Should hit floor

    def test_record_execution_hits_ceiling_and_flags_escalation(self, tuner):
        """Test that hitting ceiling flags escalation."""
        from src.runtime.agents.iteration_tuner import TuningAction

        # Original 10, ceiling is 20
        # Record many failures to hit ceiling
        for i in range(10):
            action = tuner.record_execution_result("Test Agent", False, 10, 10)

        config = tuner.get_tuned_iterations("Test Agent")
        # Should be at or near ceiling (20)
        assert config.current_tuned_iterations == 20

        # One more failure should flag escalation
        action = tuner.record_execution_result("Test Agent", False, 10, 10)
        # Already at ceiling, so unchanged, but flagged
        config = tuner.get_tuned_iterations("Test Agent")
        assert config.escalation_flagged is True

    def test_get_effective_max_iterations_with_tuning(self, tuner):
        """Test getting effective iterations with tuning record."""
        # Create a tuning record
        tuner.record_execution_result("Test Agent", True, 10, 5)

        result = tuner.get_effective_max_iterations("Test Agent", 10)

        assert result == 9  # Should return tuned value

    def test_check_escalation_needed_false(self, tuner):
        """Test check_escalation_needed returns False initially."""
        result = tuner.check_escalation_needed("Unknown Agent")

        assert result is False

    def test_check_escalation_needed_true(self, tuner):
        """Test check_escalation_needed returns True after flagging."""
        # Flag for escalation by hitting ceiling
        for _ in range(15):
            tuner.record_execution_result("Test Agent", False, 10, 10)

        result = tuner.check_escalation_needed("Test Agent")

        assert result is True

    def test_get_flagged_for_escalation(self, tuner):
        """Test getting all flagged agents."""
        # Flag an agent for escalation
        for _ in range(15):
            tuner.record_execution_result("Test Agent", False, 10, 10)

        flagged = tuner.get_flagged_for_escalation()

        assert len(flagged) >= 1
        assert flagged[0]["agent_name"] == "Test Agent"

    def test_get_all_tuned_agents(self, tuner):
        """Test getting all tuned agents."""
        tuner.record_execution_result("Agent A", True, 10, 5)
        tuner.record_execution_result("Agent B", False, 20, 15)

        agents = tuner.get_all_tuned_agents()

        assert len(agents) == 2
        names = [a["agent_name"] for a in agents]
        assert "Agent A" in names
        assert "Agent B" in names

    def test_get_tuning_history(self, tuner):
        """Test getting tuning history."""
        tuner.record_execution_result("Test Agent", True, 10, 5)
        tuner.record_execution_result("Test Agent", False, 10, 10)

        history = tuner.get_tuning_history()

        assert len(history) >= 2

    def test_get_tuning_history_filtered(self, tuner):
        """Test getting tuning history filtered by agent."""
        tuner.record_execution_result("Agent A", True, 10, 5)
        tuner.record_execution_result("Agent B", True, 10, 5)

        history = tuner.get_tuning_history(agent_name="Agent A")

        assert len(history) == 1
        assert history[0]["agent_name"] == "Agent A"

    def test_reset_agent_tuning_not_found(self, tuner):
        """Test resetting tuning for unknown agent."""
        result = tuner.reset_agent_tuning("Unknown Agent")

        assert result is False

    def test_reset_agent_tuning(self, tuner):
        """Test resetting tuning for agent."""
        tuner.record_execution_result("Test Agent", True, 10, 5)
        tuner.record_execution_result("Test Agent", True, 10, 5)

        result = tuner.reset_agent_tuning("Test Agent")

        assert result is True

        config = tuner.get_tuned_iterations("Test Agent")
        assert config.current_tuned_iterations == 10  # Back to original
        assert config.success_count == 0
        assert config.failure_count == 0

    def test_reset_all_tuning(self, tuner):
        """Test resetting tuning for all agents."""
        tuner.record_execution_result("Agent A", True, 10, 5)
        tuner.record_execution_result("Agent B", True, 20, 10)

        count = tuner.reset_all_tuning()

        assert count == 2

        config_a = tuner.get_tuned_iterations("Agent A")
        config_b = tuner.get_tuned_iterations("Agent B")
        assert config_a.current_tuned_iterations == 10
        assert config_b.current_tuned_iterations == 20


class TestGetIterationTuner:
    """Test get_iteration_tuner function."""

    def test_get_iteration_tuner_returns_instance(self):
        """Test get_iteration_tuner returns instance."""
        import src.runtime.agents.iteration_tuner as module
        module._tuner_instance = None
        module.IterationTuner._instance = None

        from src.runtime.agents.iteration_tuner import get_iteration_tuner

        tuner = get_iteration_tuner()

        assert tuner is not None

        # Cleanup
        module._tuner_instance = None
        module.IterationTuner._instance = None

    def test_get_iteration_tuner_returns_same_instance(self):
        """Test get_iteration_tuner returns same instance."""
        import src.runtime.agents.iteration_tuner as module
        module._tuner_instance = None
        module.IterationTuner._instance = None

        from src.runtime.agents.iteration_tuner import get_iteration_tuner

        tuner1 = get_iteration_tuner()
        tuner2 = get_iteration_tuner()

        assert tuner1 is tuner2

        # Cleanup
        module._tuner_instance = None
        module.IterationTuner._instance = None
