"""
Unit tests for guardrail_system module.

Tests the GuardrailSystem class and related components.
"""

import pytest
import tempfile
from pathlib import Path
from src.runtime.agents.guardrail_system import (
    GuardrailCategory,
    Guardrail,
    FailurePattern,
    GuardrailSystem,
    get_guardrail_system,
    UNIVERSAL_GUARDRAILS,
    AGENT_SPECIFIC_GUARDRAILS,
)


class TestGuardrailCategory:
    """Test GuardrailCategory enum."""

    def test_category_values(self):
        """Test all category values."""
        assert GuardrailCategory.SCOPE.value == "scope"
        assert GuardrailCategory.QUALITY.value == "quality"
        assert GuardrailCategory.PROCESS.value == "process"
        assert GuardrailCategory.RESOURCE.value == "resource"
        assert GuardrailCategory.SAFETY.value == "safety"
        assert GuardrailCategory.COMPLETENESS.value == "completeness"
        assert GuardrailCategory.FOCUS.value == "focus"


class TestGuardrail:
    """Test Guardrail dataclass."""

    def test_guardrail_creation(self):
        """Test creating a Guardrail."""
        guardrail = Guardrail(
            id="test_001",
            text="Do NOT do this thing",
            category=GuardrailCategory.SCOPE,
            agent_types=["*"],
            severity="critical",
        )

        assert guardrail.id == "test_001"
        assert guardrail.text == "Do NOT do this thing"
        assert guardrail.category == GuardrailCategory.SCOPE
        assert guardrail.agent_types == ["*"]
        assert guardrail.severity == "critical"
        # Defaults
        assert guardrail.success_rate == 0.0
        assert guardrail.times_applied == 0
        assert guardrail.times_helped == 0
        assert guardrail.created_at == ""
        assert guardrail.source == ""

    def test_guardrail_with_all_fields(self):
        """Test Guardrail with all optional fields."""
        guardrail = Guardrail(
            id="test_full",
            text="Full guardrail",
            category=GuardrailCategory.QUALITY,
            agent_types=["developers/*"],
            severity="important",
            success_rate=0.85,
            times_applied=100,
            times_helped=85,
            created_at="2024-01-01",
            source="learned",
        )

        assert guardrail.success_rate == 0.85
        assert guardrail.times_applied == 100
        assert guardrail.times_helped == 85
        assert guardrail.source == "learned"


class TestFailurePattern:
    """Test FailurePattern dataclass."""

    def test_failure_pattern_creation(self):
        """Test creating a FailurePattern."""
        pattern = FailurePattern(
            pattern_id="pattern_001",
            failure_type="scope_creep",
            description="Agent went beyond task scope",
            agent_types=["developers/code_writer"],
        )

        assert pattern.pattern_id == "pattern_001"
        assert pattern.failure_type == "scope_creep"
        assert pattern.agent_types == ["developers/code_writer"]
        # Defaults
        assert pattern.occurrences == 0
        assert pattern.suggested_guardrail == ""
        assert pattern.confidence == 0.0


class TestUniversalGuardrails:
    """Test UNIVERSAL_GUARDRAILS constant."""

    def test_universal_guardrails_not_empty(self):
        """Test that universal guardrails list is not empty."""
        assert len(UNIVERSAL_GUARDRAILS) > 0

    def test_universal_guardrails_have_required_fields(self):
        """Test all universal guardrails have required fields."""
        for g in UNIVERSAL_GUARDRAILS:
            assert g.id, "Guardrail must have id"
            assert g.text, "Guardrail must have text"
            assert isinstance(g.category, GuardrailCategory)
            assert g.agent_types, "Guardrail must have agent_types"
            assert g.severity in ["critical", "important", "advisory"]

    def test_universal_guardrails_all_apply_to_wildcard(self):
        """Test that universal guardrails apply to all agents."""
        for g in UNIVERSAL_GUARDRAILS:
            assert "*" in g.agent_types or any(
                at.endswith("/*") for at in g.agent_types
            )


class TestAgentSpecificGuardrails:
    """Test AGENT_SPECIFIC_GUARDRAILS constant."""

    def test_agent_specific_guardrails_not_empty(self):
        """Test that agent-specific guardrails dict is not empty."""
        assert len(AGENT_SPECIFIC_GUARDRAILS) > 0

    def test_agent_specific_guardrails_have_lists(self):
        """Test all entries have list values."""
        for agent_type, guardrails in AGENT_SPECIFIC_GUARDRAILS.items():
            assert isinstance(guardrails, list)
            assert len(guardrails) > 0

    def test_agent_specific_guardrails_match_agent_type(self):
        """Test guardrails match their declared agent type."""
        for agent_type, guardrails in AGENT_SPECIFIC_GUARDRAILS.items():
            for g in guardrails:
                assert agent_type in g.agent_types


class TestGuardrailSystem:
    """Test GuardrailSystem class."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        try:
            db_path.unlink()
        except:
            pass

    @pytest.fixture
    def guardrail_system(self, temp_db):
        """Create a fresh GuardrailSystem instance."""
        # Reset singleton
        GuardrailSystem._instance = None

        system = GuardrailSystem(db_path=temp_db)
        yield system

        # Cleanup singleton
        GuardrailSystem._instance = None

    def test_init_creates_database(self, temp_db):
        """Test that initialization creates database."""
        GuardrailSystem._instance = None
        system = GuardrailSystem(db_path=temp_db)

        assert temp_db.exists()

        GuardrailSystem._instance = None

    def test_singleton_pattern(self, temp_db):
        """Test singleton pattern."""
        GuardrailSystem._instance = None

        system1 = GuardrailSystem(db_path=temp_db)
        system2 = GuardrailSystem()

        assert system1 is system2

        GuardrailSystem._instance = None

    def test_loads_standard_guardrails(self, guardrail_system):
        """Test that standard guardrails are loaded."""
        guardrails = guardrail_system.get_guardrails_for_agent("*")

        # Should have some universal guardrails
        assert len(guardrails) > 0

    def test_get_guardrails_for_wildcard_agent(self, guardrail_system):
        """Test getting guardrails for wildcard agent type."""
        guardrails = guardrail_system.get_guardrails_for_agent("any_agent")

        # Should get universal guardrails that apply to "*"
        universal_ids = {g.id for g in UNIVERSAL_GUARDRAILS}
        retrieved_ids = {g.id for g in guardrails}

        assert len(retrieved_ids & universal_ids) > 0

    def test_get_guardrails_for_specific_agent(self, guardrail_system):
        """Test getting guardrails for a specific agent type."""
        guardrails = guardrail_system.get_guardrails_for_agent(
            "testers/unit_test_writer"
        )

        # Should get agent-specific guardrails
        agent_ids = {g.id for g in AGENT_SPECIFIC_GUARDRAILS.get("testers/unit_test_writer", [])}
        retrieved_ids = {g.id for g in guardrails}

        # Should include agent-specific guardrails
        if agent_ids:
            assert len(retrieved_ids & agent_ids) > 0

    def test_get_guardrails_with_category_filter(self, guardrail_system):
        """Test filtering guardrails by category."""
        guardrails = guardrail_system.get_guardrails_for_agent(
            "developers/code_writer",
            categories=[GuardrailCategory.SCOPE]
        )

        for g in guardrails:
            assert g.category == GuardrailCategory.SCOPE

    def test_get_guardrails_with_severity_filter(self, guardrail_system):
        """Test filtering guardrails by minimum severity."""
        guardrails = guardrail_system.get_guardrails_for_agent(
            "any_agent",
            severity_min="critical"
        )

        for g in guardrails:
            assert g.severity == "critical"

    def test_apply_guardrails_to_prompt(self, guardrail_system):
        """Test applying guardrails to a prompt."""
        prompt = "Please implement this feature.\n\nRequirements: ..."

        enhanced, applied_ids = guardrail_system.apply_guardrails_to_prompt(
            prompt,
            agent_type="developers/code_writer"
        )

        assert "CRITICAL CONSTRAINTS" in enhanced
        assert len(applied_ids) > 0

    def test_apply_guardrails_inserts_after_first_paragraph(self, guardrail_system):
        """Test that guardrails are inserted after first paragraph."""
        prompt = "First paragraph.\n\nSecond paragraph."

        enhanced, _ = guardrail_system.apply_guardrails_to_prompt(
            prompt,
            agent_type="developers/code_writer"
        )

        # Should have constraints between paragraphs
        assert "First paragraph." in enhanced
        assert "Second paragraph." in enhanced
        assert enhanced.index("CRITICAL") < enhanced.index("Second paragraph")

    def test_apply_guardrails_no_paragraph_break(self, guardrail_system):
        """Test applying guardrails to single paragraph prompt."""
        prompt = "Single paragraph prompt"

        enhanced, _ = guardrail_system.apply_guardrails_to_prompt(
            prompt,
            agent_type="developers/code_writer"
        )

        assert "Single paragraph prompt" in enhanced
        assert "CRITICAL CONSTRAINTS" in enhanced

    def test_apply_guardrails_max_limit(self, guardrail_system):
        """Test that max_guardrails limit is respected."""
        prompt = "Test prompt"

        _, applied_ids = guardrail_system.apply_guardrails_to_prompt(
            prompt,
            agent_type="developers/code_writer",
            max_guardrails=3
        )

        assert len(applied_ids) <= 3

    def test_record_guardrail_outcome_success(self, guardrail_system):
        """Test recording successful guardrail outcome."""
        # Apply guardrails first to get IDs
        _, applied_ids = guardrail_system.apply_guardrails_to_prompt(
            "Test",
            agent_type="developers/code_writer"
        )

        # Record success
        guardrail_system.record_guardrail_outcome(
            guardrail_ids=applied_ids[:1],
            agent_id="test-agent-1",
            session_id="session-1",
            success=True
        )

        # Verify times_helped increased
        guardrails = guardrail_system.get_guardrails_for_agent("developers/code_writer")
        matching = [g for g in guardrails if g.id == applied_ids[0]]

        if matching:
            assert matching[0].times_helped >= 1

    def test_record_guardrail_outcome_failure(self, guardrail_system):
        """Test recording failed guardrail outcome."""
        _, applied_ids = guardrail_system.apply_guardrails_to_prompt(
            "Test",
            agent_type="developers/code_writer"
        )

        # Record failure - should not increase times_helped
        guardrail_system.record_guardrail_outcome(
            guardrail_ids=applied_ids[:1],
            agent_id="test-agent-2",
            session_id="session-2",
            success=False
        )

        # Just verify it doesn't crash
        guardrails = guardrail_system.get_guardrails_for_agent("developers/code_writer")
        assert len(guardrails) > 0

    def test_learn_from_failure_scope_creep(self, guardrail_system):
        """Test learning from scope creep failure."""
        result = guardrail_system.learn_from_failure(
            agent_type="developers/code_writer",
            failure_type="scope_creep",
            failure_description="Agent implemented extra features",
            context={"scope": "specific task requirements"}
        )

        # First occurrence returns None (needs more occurrences to promote)
        assert result is None

    def test_learn_from_failure_max_iterations(self, guardrail_system):
        """Test learning from max iterations failure."""
        result = guardrail_system.learn_from_failure(
            agent_type="developers/code_writer",
            failure_type="max_iterations",
            failure_description="Agent exceeded iteration limit",
            context={"max_iterations": 15}
        )

        assert result is None

    def test_learn_from_failure_records_pattern(self, guardrail_system):
        """Test that learning from failure records the pattern."""
        # Learn a failure - should record pattern but not immediately promote
        result = guardrail_system.learn_from_failure(
            agent_type="developers/code_writer",
            failure_type="error_loop",
            failure_description="Agent kept retrying same approach",
            context={}
        )

        # First occurrence returns None (not yet promoted)
        assert result is None

        # Learn again (second occurrence)
        result = guardrail_system.learn_from_failure(
            agent_type="developers/code_writer",
            failure_type="error_loop",
            failure_description="Agent kept retrying same approach",
            context={}
        )

        # Still not promoted after just 2 occurrences
        assert result is None

    def test_learn_from_failure_unknown_type(self, guardrail_system):
        """Test learning from unknown failure type uses generic template."""
        result = guardrail_system.learn_from_failure(
            agent_type="developers/code_writer",
            failure_type="unknown_failure_type",
            failure_description="Some unknown failure happened",
            context={}
        )

        # Should still work (returns None, but records pattern)
        assert result is None

    def test_get_guardrail_stats(self, guardrail_system):
        """Test getting guardrail statistics."""
        stats = guardrail_system.get_guardrail_stats()

        assert "total_guardrails" in stats
        assert "learned_guardrails" in stats
        assert "manual_guardrails" in stats
        assert "most_effective" in stats
        assert "by_category" in stats

    def test_get_guardrail_stats_counts(self, guardrail_system):
        """Test that stats counts are accurate."""
        stats = guardrail_system.get_guardrail_stats()

        assert stats["total_guardrails"] >= len(UNIVERSAL_GUARDRAILS)
        assert stats["manual_guardrails"] == stats["total_guardrails"] - stats["learned_guardrails"]

    def test_format_guardrails_markdown(self, guardrail_system):
        """Test formatting guardrails as markdown."""
        formatted = guardrail_system.format_guardrails_for_agent_definition(
            "developers/code_writer",
            format_style="markdown"
        )

        assert "Anti-Patterns" in formatted
        assert "Constraints:" in formatted

    def test_format_guardrails_plain_text(self, guardrail_system):
        """Test formatting guardrails as plain text."""
        formatted = guardrail_system.format_guardrails_for_agent_definition(
            "developers/code_writer",
            format_style="plain"
        )

        assert "WHAT NOT TO DO:" in formatted

    def test_format_guardrails_empty_agent(self, guardrail_system):
        """Test formatting for agent with no specific guardrails."""
        # Use agent type that might not have specific guardrails
        formatted = guardrail_system.format_guardrails_for_agent_definition(
            "nonexistent_agent_type"
        )

        # May still have universal guardrails
        # If no guardrails, returns empty string


class TestGenerateGuardrailFromFailure:
    """Test _generate_guardrail_from_failure method."""

    @pytest.fixture
    def guardrail_system(self):
        """Create a fresh GuardrailSystem instance."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        GuardrailSystem._instance = None
        system = GuardrailSystem(db_path=db_path)

        yield system

        GuardrailSystem._instance = None
        try:
            db_path.unlink()
        except:
            pass

    def test_generates_scope_creep_guardrail(self, guardrail_system):
        """Test generating guardrail for scope creep."""
        guardrail = guardrail_system._generate_guardrail_from_failure(
            "developers/code_writer",
            "scope_creep",
            "Agent went beyond scope",
            {"scope": "only implement button"}
        )

        assert "Do NOT implement features beyond" in guardrail
        assert "only implement button" in guardrail

    def test_generates_max_iterations_guardrail(self, guardrail_system):
        """Test generating guardrail for max iterations."""
        guardrail = guardrail_system._generate_guardrail_from_failure(
            "developers/code_writer",
            "max_iterations",
            "Agent exceeded limit",
            {"max_iterations": 20}
        )

        assert "20" in guardrail
        assert "iteration" in guardrail.lower()

    def test_generates_no_activity_guardrail(self, guardrail_system):
        """Test generating guardrail for no activity."""
        guardrail = guardrail_system._generate_guardrail_from_failure(
            "developers/code_writer",
            "no_activity",
            "Agent stalled",
            {}
        )

        assert "stall" in guardrail.lower() or "block" in guardrail.lower()

    def test_generates_incomplete_guardrail(self, guardrail_system):
        """Test generating guardrail for incomplete task."""
        guardrail = guardrail_system._generate_guardrail_from_failure(
            "developers/code_writer",
            "incomplete",
            "Task marked complete but wasn't",
            {"criteria": "all tests pass"}
        )

        assert "complete" in guardrail.lower()

    def test_generates_file_sprawl_guardrail(self, guardrail_system):
        """Test generating guardrail for file sprawl."""
        guardrail = guardrail_system._generate_guardrail_from_failure(
            "developers/code_writer",
            "file_sprawl",
            "Too many files created",
            {"file_limit": 3}
        )

        assert "3" in guardrail
        assert "file" in guardrail.lower()

    def test_generates_error_loop_guardrail(self, guardrail_system):
        """Test generating guardrail for error loop."""
        guardrail = guardrail_system._generate_guardrail_from_failure(
            "developers/code_writer",
            "error_loop",
            "Agent kept retrying same approach",
            {}
        )

        assert "retry" in guardrail.lower() or "failing" in guardrail.lower()

    def test_generates_generic_guardrail_for_unknown(self, guardrail_system):
        """Test generating generic guardrail for unknown failure type."""
        guardrail = guardrail_system._generate_guardrail_from_failure(
            "developers/code_writer",
            "some_unknown_failure",
            "Something bad happened that we don't know about",
            {}
        )

        assert "Do NOT repeat" in guardrail


class TestGetGuardrailSystem:
    """Test get_guardrail_system function."""

    def test_returns_instance(self):
        """Test get_guardrail_system returns instance."""
        import src.runtime.agents.guardrail_system as module
        module._guardrail_system = None
        GuardrailSystem._instance = None

        system = get_guardrail_system()

        assert system is not None
        assert isinstance(system, GuardrailSystem)

        # Cleanup
        module._guardrail_system = None
        GuardrailSystem._instance = None

    def test_returns_same_instance(self):
        """Test get_guardrail_system returns same instance."""
        import src.runtime.agents.guardrail_system as module
        module._guardrail_system = None
        GuardrailSystem._instance = None

        system1 = get_guardrail_system()
        system2 = get_guardrail_system()

        assert system1 is system2

        # Cleanup
        module._guardrail_system = None
        GuardrailSystem._instance = None


class TestWildcardMatching:
    """Test wildcard matching in guardrail application."""

    @pytest.fixture
    def guardrail_system(self):
        """Create a fresh GuardrailSystem instance."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        GuardrailSystem._instance = None
        system = GuardrailSystem(db_path=db_path)

        yield system

        GuardrailSystem._instance = None
        try:
            db_path.unlink()
        except:
            pass

    def test_wildcard_matches_any_agent(self, guardrail_system):
        """Test that '*' matches any agent type."""
        guardrails = guardrail_system.get_guardrails_for_agent("completely_random_type")

        # Should get universal guardrails with "*"
        assert len(guardrails) > 0

    def test_category_wildcard_matches(self, guardrail_system):
        """Test that 'category/*' matches agents in that category."""
        # Add guardrail with category wildcard
        guardrails = guardrail_system.get_guardrails_for_agent("developers/custom_developer")

        # Should match guardrails with "developers/*"
        developer_guardrails = [g for g in guardrails if "developers/" in str(g.agent_types)]
        # May or may not have any depending on loaded guardrails
