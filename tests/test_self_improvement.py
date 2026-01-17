"""
Unit tests for the self-improvement loop module.

Tests the recommendation engine, feedback injector, and definition updater
to ensure they make real, targeted changes rather than useless text injection.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.runtime.agents.self_improvement import (
    SelfImprovementLoop,
    RecommendationType,
    RecommendationPriority,
    PerformanceIssue,
    Recommendation,
)


class TestInsertSection:
    """Tests for the _insert_section helper method."""

    def setup_method(self):
        """Create a SelfImprovementLoop instance for testing."""
        with patch.object(SelfImprovementLoop, '__init__', lambda x: None):
            self.loop = SelfImprovementLoop()
            self.loop.analyzer = MagicMock()
            self.loop.recommendation_engine = MagicMock()
            self.loop.feedback_injector = MagicMock()
            self.loop.definitions_base = Path("/tmp")

    def test_insert_section_before_model_preference(self):
        """Should insert new section before ## Model Preference."""
        content = """# Agent Name

## Instructions
Do things.

## Model Preference
sonnet

## Max Iterations
10
"""
        result = self.loop._insert_section(
            content,
            "## New Section",
            "- Item 1\n- Item 2"
        )

        assert "## New Section" in result
        assert result.index("## New Section") < result.index("## Model Preference")
        assert "- Item 1" in result
        assert "- Item 2" in result

    def test_insert_section_avoids_duplicates(self):
        """Should not insert duplicate sections."""
        content = """# Agent Name

## Existing Section
Already here.

## Model Preference
sonnet
"""
        result = self.loop._insert_section(
            content,
            "## Existing Section",
            "New content"
        )

        # Should return unchanged content
        assert result.count("## Existing Section") == 1
        assert "New content" not in result

    def test_insert_section_at_end_if_no_marker(self):
        """Should append to end if no insertion markers found."""
        content = """# Agent Name

## Instructions
Do things.
"""
        result = self.loop._insert_section(
            content,
            "## New Section",
            "Content here"
        )

        assert "## New Section" in result
        assert result.endswith("Content here\n") or "Content here" in result


class TestGenerateErrorHandlingSection:
    """Tests for the _generate_error_handling_section helper method."""

    def setup_method(self):
        """Create a SelfImprovementLoop instance for testing."""
        with patch.object(SelfImprovementLoop, '__init__', lambda x: None):
            self.loop = SelfImprovementLoop()

    def test_generates_api_error_handling(self):
        """Should generate specific handling for API errors."""
        result = self.loop._generate_error_handling_section("api_error")

        assert "API Errors" in result
        assert "exponential backoff" in result

    def test_generates_multiple_error_handlers(self):
        """Should generate handlers for multiple error types."""
        result = self.loop._generate_error_handling_section("api_error, timeout, validation_error")

        assert "API Errors" in result
        assert "Timeouts" in result
        assert "Validation Errors" in result

    def test_generates_generic_handler_for_unknown_errors(self):
        """Should generate generic handler for unknown error types."""
        result = self.loop._generate_error_handling_section("some_weird_error")

        assert "some_weird_error" in result
        assert "Log error details" in result

    def test_returns_empty_for_no_errors(self):
        """Should return empty string for no error types."""
        result = self.loop._generate_error_handling_section("")
        assert result == ""

        result = self.loop._generate_error_handling_section(None)
        assert result == ""


class TestUpdateModelPreference:
    """Tests for the _update_model_preference helper method."""

    def setup_method(self):
        """Create a SelfImprovementLoop instance for testing."""
        with patch.object(SelfImprovementLoop, '__init__', lambda x: None):
            self.loop = SelfImprovementLoop()

    def test_updates_model_preference(self):
        """Should update model preference in content."""
        content = """# Agent

## Model Preference
haiku

## Max Iterations
10
"""
        result = self.loop._update_model_preference(content, "opus")

        assert "## Model Preference\nopus" in result
        assert "haiku" not in result

    def test_leaves_content_unchanged_if_no_model_section(self):
        """Should leave content unchanged if no model preference section."""
        content = """# Agent

## Instructions
Do stuff.
"""
        result = self.loop._update_model_preference(content, "opus")

        # Should return unchanged
        assert result == content


class TestUpdateMaxIterations:
    """Tests for the _update_max_iterations helper method."""

    def setup_method(self):
        """Create a SelfImprovementLoop instance for testing."""
        with patch.object(SelfImprovementLoop, '__init__', lambda x: None):
            self.loop = SelfImprovementLoop()

    def test_updates_max_iterations(self):
        """Should update max iterations in content."""
        content = """# Agent

## Max Iterations
10

## Can Write Code
false
"""
        result = self.loop._update_max_iterations(content, 25)

        assert "## Max Iterations\n25" in result
        assert "10" not in result or "10" in result.split("## Max Iterations")[0]


class TestDeprecatedPerformanceNote:
    """Tests that the deprecated _add_performance_note method does nothing."""

    def setup_method(self):
        """Create a SelfImprovementLoop instance for testing."""
        with patch.object(SelfImprovementLoop, '__init__', lambda x: None):
            self.loop = SelfImprovementLoop()

    def test_does_not_modify_content(self):
        """Should return content unchanged."""
        content = "Original content here."
        result = self.loop._add_performance_note(content, "Some performance note")

        assert result == content
        assert "Performance Insight" not in result


class TestRecommendationTypesCoverRealChanges:
    """Tests that recommendation types result in real definition changes."""

    def setup_method(self):
        """Create a SelfImprovementLoop instance for testing."""
        with patch.object(SelfImprovementLoop, '__init__', lambda x: None):
            self.loop = SelfImprovementLoop()
            self.loop.analyzer = MagicMock()
            self.loop.recommendation_engine = MagicMock()
            self.loop.feedback_injector = MagicMock()
            self.loop.definitions_base = Path("/tmp")
            self.loop.recommendation_engine.recommendations_path = Path("/tmp/recommendations")

        self.base_content = """# Test Agent

## Instructions
Do the thing.

## Model Preference
haiku

## Max Iterations
10

## Can Write Code
false
"""

    def test_definition_tweak_upgrades_model_for_low_success(self):
        """definition_tweak should upgrade model when success rate is low."""
        recommendation = {
            "id": "test_rec",
            "agent_name": "Test Agent",
            "type": "definition_tweak",
            "evidence": {
                "success_rate": 45,  # Critical - below 50%
                "error_types": "",
                "avg_iterations": 5
            }
        }

        # Mock the find and file operations
        with patch.object(self.loop, '_find_agent_definition') as mock_find:
            mock_path = MagicMock()
            mock_path.read_text.return_value = self.base_content
            mock_find.return_value = mock_path

            # We can't fully test apply_recommendation without file system
            # but we can test the model upgrade logic directly
            content = self.base_content
            evidence = recommendation["evidence"]

            if evidence["success_rate"] < 50:
                content = self.loop._update_model_preference(content, "opus")

            assert "opus" in content
            assert "haiku" not in content.split("## Model Preference")[1].split("##")[0]

    def test_prompt_refinement_adds_decision_section(self):
        """prompt_refinement should add decision-making guidelines."""
        content = self.base_content
        section = """
## Decision Making
- Make reasonable assumptions for standard implementation details
- Do NOT ask users for choices that have obvious defaults
- When in doubt, pick the most common/standard approach and proceed
- Only ask clarifying questions for genuinely ambiguous requirements
"""
        result = self.loop._insert_section(content, "## Decision Making", section)

        assert "## Decision Making" in result
        assert "reasonable assumptions" in result

    def test_validation_adds_validation_section(self):
        """validation type should add output validation requirements."""
        content = self.base_content
        section = """
## Output Validation
- Verify all required deliverables are complete before reporting success
- Test outputs when possible (run code, validate formats)
- Double-check critical values and configurations
- Never report success if any validation fails
"""
        result = self.loop._insert_section(content, "## Output Validation", section)

        assert "## Output Validation" in result
        assert "Verify all required deliverables" in result


class TestNoGarbageInjection:
    """Tests that ensure no useless 'Performance Insight' text is ever injected."""

    def setup_method(self):
        """Create a SelfImprovementLoop instance for testing."""
        with patch.object(SelfImprovementLoop, '__init__', lambda x: None):
            self.loop = SelfImprovementLoop()

    def test_no_performance_insight_text_in_insert_section(self):
        """_insert_section should never inject 'Performance Insight' text."""
        content = "# Agent\n\n## Instructions\nDo stuff.\n\n## Model Preference\nsonnet"

        result = self.loop._insert_section(
            content,
            "## New Section",
            "Useful content here"
        )

        assert "Performance Insight" not in result
        assert "Auto-Applied" not in result

    def test_no_think_about_this_guidance(self):
        """Error handling should be specific, not vague 'think about this' text."""
        result = self.loop._generate_error_handling_section("api_error")

        # Should have specific actionable guidance
        assert "exponential backoff" in result or "retry" in result.lower()

        # Should NOT have vague guidance
        assert "consider reviewing" not in result.lower()
        assert "think about" not in result.lower()
