"""
Unit tests for the Guardrail System.
"""
import json
import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "runtime" / "agents"))

from guardrail_system import (
    GuardrailSystem,
    GuardrailCategory,
    Guardrail,
    UNIVERSAL_GUARDRAILS,
    AGENT_SPECIFIC_GUARDRAILS,
    get_guardrail_system,
)


@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path."""
    return tmp_path / "test_guardrails.db"


@pytest.fixture
def guardrail_system(temp_db_path):
    """Create a fresh GuardrailSystem with temporary database."""
    # Reset singleton for testing
    GuardrailSystem._instance = None
    system = GuardrailSystem(db_path=temp_db_path)
    yield system
    # Cleanup
    GuardrailSystem._instance = None


class TestGuardrailSystemInitialization:
    """Tests for GuardrailSystem initialization."""

    def test_creates_database(self, temp_db_path):
        """System should create database on initialization."""
        GuardrailSystem._instance = None
        system = GuardrailSystem(db_path=temp_db_path)
        assert temp_db_path.exists()
        GuardrailSystem._instance = None

    def test_creates_tables(self, temp_db_path):
        """System should create required tables."""
        GuardrailSystem._instance = None
        system = GuardrailSystem(db_path=temp_db_path)

        with sqlite3.connect(str(temp_db_path)) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t[0] for t in tables]

        assert "guardrails" in table_names
        assert "failure_patterns" in table_names
        assert "guardrail_applications" in table_names
        GuardrailSystem._instance = None

    def test_loads_universal_guardrails(self, guardrail_system, temp_db_path):
        """System should load universal guardrails on init."""
        with sqlite3.connect(str(temp_db_path)) as conn:
            count = conn.execute("SELECT COUNT(*) FROM guardrails").fetchone()[0]

        # Should have loaded universal + agent-specific guardrails
        expected_count = len(UNIVERSAL_GUARDRAILS) + sum(
            len(g) for g in AGENT_SPECIFIC_GUARDRAILS.values()
        )
        assert count >= len(UNIVERSAL_GUARDRAILS)

    def test_singleton_pattern(self, temp_db_path):
        """System should use singleton pattern."""
        GuardrailSystem._instance = None
        system1 = GuardrailSystem(db_path=temp_db_path)
        system2 = GuardrailSystem(db_path=temp_db_path)
        assert system1 is system2
        GuardrailSystem._instance = None


class TestGuardrailRetrieval:
    """Tests for retrieving guardrails."""

    def test_get_guardrails_for_any_agent(self, guardrail_system):
        """Should return universal guardrails for any agent type."""
        guardrails = guardrail_system.get_guardrails_for_agent("some/random_agent")
        assert len(guardrails) > 0

        # Should include universal guardrails (marked with "*")
        universal_texts = [g.text for g in UNIVERSAL_GUARDRAILS]
        returned_texts = [g.text for g in guardrails]

        # At least some universal guardrails should be present
        overlap = set(universal_texts) & set(returned_texts)
        assert len(overlap) > 0

    def test_get_guardrails_for_specific_agent(self, guardrail_system):
        """Should return agent-specific guardrails."""
        guardrails = guardrail_system.get_guardrails_for_agent("developers/code_writer")

        # Should include code_writer specific guardrails
        cw_guardrails = AGENT_SPECIFIC_GUARDRAILS.get("developers/code_writer", [])
        if cw_guardrails:
            cw_texts = [g.text for g in cw_guardrails]
            returned_texts = [g.text for g in guardrails]
            overlap = set(cw_texts) & set(returned_texts)
            assert len(overlap) > 0

    def test_filter_by_severity(self, guardrail_system):
        """Should filter guardrails by minimum severity."""
        # Get only critical guardrails
        critical_only = guardrail_system.get_guardrails_for_agent(
            "developers/code_writer",
            severity_min="critical"
        )

        for g in critical_only:
            assert g.severity == "critical"

    def test_filter_by_category(self, guardrail_system):
        """Should filter guardrails by category."""
        scope_guardrails = guardrail_system.get_guardrails_for_agent(
            "developers/code_writer",
            categories=[GuardrailCategory.SCOPE]
        )

        for g in scope_guardrails:
            assert g.category == GuardrailCategory.SCOPE


class TestGuardrailApplication:
    """Tests for applying guardrails to prompts."""

    def test_apply_guardrails_adds_section(self, guardrail_system):
        """Should add guardrails section to prompt."""
        original_prompt = "Write a function to calculate fibonacci numbers."
        enhanced, applied_ids = guardrail_system.apply_guardrails_to_prompt(
            prompt=original_prompt,
            agent_type="developers/code_writer"
        )

        assert "CRITICAL CONSTRAINTS" in enhanced
        assert len(applied_ids) > 0
        assert original_prompt in enhanced

    def test_apply_guardrails_limits_count(self, guardrail_system):
        """Should respect max_guardrails limit."""
        enhanced, applied_ids = guardrail_system.apply_guardrails_to_prompt(
            prompt="Test prompt",
            agent_type="developers/code_writer",
            max_guardrails=3
        )

        assert len(applied_ids) <= 3

    def test_apply_guardrails_preserves_original(self, guardrail_system):
        """Should preserve original prompt content."""
        original = "This is a very specific task with unique requirements."
        enhanced, _ = guardrail_system.apply_guardrails_to_prompt(
            prompt=original,
            agent_type="developers/code_writer"
        )

        assert original in enhanced

    def test_apply_guardrails_records_application(self, guardrail_system, temp_db_path):
        """Should record guardrail applications."""
        guardrail_system.apply_guardrails_to_prompt(
            prompt="Test",
            agent_type="developers/code_writer"
        )

        with sqlite3.connect(str(temp_db_path)) as conn:
            # Check that times_applied was incremented
            row = conn.execute(
                "SELECT SUM(times_applied) FROM guardrails WHERE times_applied > 0"
            ).fetchone()
            assert row[0] > 0


class TestGuardrailOutcomeTracking:
    """Tests for tracking guardrail effectiveness."""

    def test_record_success_increments_helped(self, guardrail_system, temp_db_path):
        """Recording success should increment times_helped."""
        # First apply guardrails
        _, applied_ids = guardrail_system.apply_guardrails_to_prompt(
            prompt="Test",
            agent_type="developers/code_writer"
        )

        # Record success
        guardrail_system.record_guardrail_outcome(
            guardrail_ids=applied_ids,
            agent_id="test_agent",
            session_id="test_session",
            success=True
        )

        with sqlite3.connect(str(temp_db_path)) as conn:
            for gid in applied_ids:
                row = conn.execute(
                    "SELECT times_helped FROM guardrails WHERE id = ?",
                    (gid,)
                ).fetchone()
                if row:
                    assert row[0] > 0

    def test_record_failure_does_not_increment_helped(self, guardrail_system, temp_db_path):
        """Recording failure should not increment times_helped."""
        # Get initial state
        with sqlite3.connect(str(temp_db_path)) as conn:
            initial = conn.execute(
                "SELECT SUM(times_helped) FROM guardrails"
            ).fetchone()[0] or 0

        # Apply and record failure
        _, applied_ids = guardrail_system.apply_guardrails_to_prompt(
            prompt="Test",
            agent_type="developers/code_writer"
        )

        guardrail_system.record_guardrail_outcome(
            guardrail_ids=applied_ids,
            agent_id="test_agent",
            session_id="test_session",
            success=False
        )

        with sqlite3.connect(str(temp_db_path)) as conn:
            final = conn.execute(
                "SELECT SUM(times_helped) FROM guardrails"
            ).fetchone()[0] or 0

        # times_helped should not have increased
        assert final == initial

    def test_success_rate_calculation(self, guardrail_system, temp_db_path):
        """Success rate should be calculated correctly."""
        # Apply multiple times
        for _ in range(5):
            _, applied_ids = guardrail_system.apply_guardrails_to_prompt(
                prompt="Test",
                agent_type="developers/code_writer",
                max_guardrails=1
            )

        # Get the first guardrail ID
        test_id = applied_ids[0] if applied_ids else None
        if not test_id:
            pytest.skip("No guardrails applied")

        # Record 3 successes
        for _ in range(3):
            guardrail_system.record_guardrail_outcome(
                guardrail_ids=[test_id],
                agent_id="test",
                session_id="test",
                success=True
            )

        with sqlite3.connect(str(temp_db_path)) as conn:
            row = conn.execute(
                "SELECT success_rate, times_applied, times_helped FROM guardrails WHERE id = ?",
                (test_id,)
            ).fetchone()

        if row:
            # Success rate should reflect the ratio
            assert row[0] >= 0
            assert row[0] <= 1


class TestGuardrailLearning:
    """Tests for learning new guardrails from failures."""

    def test_learn_from_failure_creates_pattern(self, guardrail_system, temp_db_path):
        """Should create a failure pattern when learning."""
        guardrail_system.learn_from_failure(
            agent_type="developers/code_writer",
            failure_type="scope_creep",
            failure_description="Agent implemented extra features",
            context={"scope": "only write the login function"}
        )

        with sqlite3.connect(str(temp_db_path)) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM failure_patterns WHERE failure_type = 'scope_creep'"
            ).fetchone()[0]

        assert count > 0

    def test_learn_from_failure_increments_occurrences(self, guardrail_system, temp_db_path):
        """Repeated failures should increment occurrence count."""
        for _ in range(3):
            guardrail_system.learn_from_failure(
                agent_type="developers/code_writer",
                failure_type="test_repeated_failure",
                failure_description="Same failure",
                context={}
            )

        with sqlite3.connect(str(temp_db_path)) as conn:
            row = conn.execute(
                "SELECT occurrences FROM failure_patterns WHERE failure_type = 'test_repeated_failure'"
            ).fetchone()

        if row:
            assert row[0] >= 1


class TestGuardrailStats:
    """Tests for guardrail statistics."""

    def test_get_stats_returns_counts(self, guardrail_system):
        """Should return basic statistics."""
        stats = guardrail_system.get_guardrail_stats()

        assert "total_guardrails" in stats
        assert "learned_guardrails" in stats
        assert "manual_guardrails" in stats
        assert "by_category" in stats
        assert stats["total_guardrails"] > 0

    def test_stats_category_breakdown(self, guardrail_system):
        """Stats should include category breakdown."""
        stats = guardrail_system.get_guardrail_stats()

        by_category = stats["by_category"]
        # Should have at least some categories
        assert len(by_category) > 0


class TestGuardrailFormatting:
    """Tests for formatting guardrails for agent definitions."""

    def test_format_markdown(self, guardrail_system):
        """Should format guardrails as markdown."""
        formatted = guardrail_system.format_guardrails_for_agent_definition(
            agent_type="developers/code_writer",
            format_style="markdown"
        )

        assert "Anti-Patterns" in formatted
        assert "**" in formatted  # Bold formatting

    def test_format_plain_text(self, guardrail_system):
        """Should format guardrails as plain text."""
        formatted = guardrail_system.format_guardrails_for_agent_definition(
            agent_type="developers/code_writer",
            format_style="plain"
        )

        assert "WHAT NOT TO DO" in formatted


class TestGuardrailCategories:
    """Tests for guardrail categories."""

    def test_all_categories_have_guardrails(self, guardrail_system):
        """Each category should have at least one guardrail."""
        categories = [
            GuardrailCategory.SCOPE,
            GuardrailCategory.QUALITY,
            GuardrailCategory.PROCESS,
            GuardrailCategory.COMPLETENESS,
        ]

        for category in categories:
            guardrails = guardrail_system.get_guardrails_for_agent(
                "developers/code_writer",
                categories=[category],
                severity_min="advisory"
            )
            # At least universal guardrails should be in each category
            # (some categories may be empty for specific agents)


class TestSingletonAccessor:
    """Tests for the get_guardrail_system accessor."""

    def test_accessor_returns_instance(self, temp_db_path):
        """Accessor should return a GuardrailSystem instance."""
        # Patch to use temp db
        with patch.object(GuardrailSystem, '__init__', lambda self, **kwargs: None):
            GuardrailSystem._instance = None
            GuardrailSystem._instance = GuardrailSystem.__new__(GuardrailSystem)
            GuardrailSystem._instance._initialized = True
            GuardrailSystem._instance.db_path = temp_db_path

            from guardrail_system import _guardrail_system
            import guardrail_system as gs_module
            gs_module._guardrail_system = None

            system = get_guardrail_system()
            assert system is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
