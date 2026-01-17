"""
Unit tests for model_selector module.

Tests the ModelSelector class for model selection based on budget tier and task complexity.
"""

import pytest


class TestModelSelector:
    """Test ModelSelector class."""

    def test_select_model_defaults(self):
        """Test model selection with default parameters."""
        from src.runtime.agents.model_selector import ModelSelector

        model = ModelSelector.select_model()

        # Default is balanced + routine = haiku
        assert model == "claude-3-5-haiku-20241022"

    def test_select_model_balanced_strategic(self):
        """Test balanced tier with strategic complexity."""
        from src.runtime.agents.model_selector import ModelSelector

        model = ModelSelector.select_model("balanced", "strategic")

        assert model == "claude-sonnet-4-5-20250929"

    def test_select_model_balanced_creative(self):
        """Test balanced tier with creative complexity."""
        from src.runtime.agents.model_selector import ModelSelector

        model = ModelSelector.select_model("balanced", "creative")

        assert model == "claude-sonnet-4-5-20250929"

    def test_select_model_balanced_routine(self):
        """Test balanced tier with routine complexity."""
        from src.runtime.agents.model_selector import ModelSelector

        model = ModelSelector.select_model("balanced", "routine")

        assert model == "claude-3-5-haiku-20241022"

    def test_select_model_full_firepower_strategic(self):
        """Test full_firepower tier with strategic complexity."""
        from src.runtime.agents.model_selector import ModelSelector

        model = ModelSelector.select_model("full_firepower", "strategic")

        assert model == "claude-opus-4-5-20251101"

    def test_select_model_full_firepower_creative(self):
        """Test full_firepower tier with creative complexity."""
        from src.runtime.agents.model_selector import ModelSelector

        model = ModelSelector.select_model("full_firepower", "creative")

        assert model == "claude-sonnet-4-5-20250929"

    def test_select_model_full_firepower_routine(self):
        """Test full_firepower tier with routine complexity."""
        from src.runtime.agents.model_selector import ModelSelector

        model = ModelSelector.select_model("full_firepower", "routine")

        assert model == "claude-sonnet-4-5-20250929"

    def test_select_model_economical_strategic(self):
        """Test economical tier with strategic complexity."""
        from src.runtime.agents.model_selector import ModelSelector

        model = ModelSelector.select_model("economical", "strategic")

        # Can't compromise on strategic - uses sonnet
        assert model == "claude-sonnet-4-5-20250929"

    def test_select_model_economical_creative(self):
        """Test economical tier with creative complexity."""
        from src.runtime.agents.model_selector import ModelSelector

        model = ModelSelector.select_model("economical", "creative")

        assert model == "claude-3-5-haiku-20241022"

    def test_select_model_economical_routine(self):
        """Test economical tier with routine complexity."""
        from src.runtime.agents.model_selector import ModelSelector

        model = ModelSelector.select_model("economical", "routine")

        assert model == "claude-3-5-haiku-20241022"

    def test_select_model_with_agent_name(self):
        """Test model selection with agent name (for logging)."""
        from src.runtime.agents.model_selector import ModelSelector

        model = ModelSelector.select_model("balanced", "routine", agent_name="Test Agent")

        assert model == "claude-3-5-haiku-20241022"

    def test_select_model_invalid_tier(self):
        """Test model selection with invalid budget tier."""
        from src.runtime.agents.model_selector import ModelSelector

        with pytest.raises(ValueError) as exc_info:
            ModelSelector.select_model("invalid_tier", "routine")

        assert "Invalid budget_tier" in str(exc_info.value)
        assert "invalid_tier" in str(exc_info.value)

    def test_select_model_invalid_complexity(self):
        """Test model selection with invalid task complexity."""
        from src.runtime.agents.model_selector import ModelSelector

        with pytest.raises(ValueError) as exc_info:
            ModelSelector.select_model("balanced", "invalid_complexity")

        assert "Invalid task_complexity" in str(exc_info.value)
        assert "invalid_complexity" in str(exc_info.value)


class TestModelSelectorUtilities:
    """Test ModelSelector utility methods."""

    def test_get_available_tiers(self):
        """Test getting available tiers."""
        from src.runtime.agents.model_selector import ModelSelector

        tiers = ModelSelector.get_available_tiers()

        assert "full_firepower" in tiers
        assert "balanced" in tiers
        assert "economical" in tiers
        assert len(tiers) == 3

    def test_get_available_complexities(self):
        """Test getting available complexities."""
        from src.runtime.agents.model_selector import ModelSelector

        complexities = ModelSelector.get_available_complexities()

        assert "strategic" in complexities
        assert "creative" in complexities
        assert "routine" in complexities
        assert len(complexities) == 3

    def test_estimate_cost_multiplier_economical(self):
        """Test cost multiplier for economical tier."""
        from src.runtime.agents.model_selector import ModelSelector

        multiplier = ModelSelector.estimate_cost_multiplier("economical")

        assert multiplier == 0.7

    def test_estimate_cost_multiplier_balanced(self):
        """Test cost multiplier for balanced tier."""
        from src.runtime.agents.model_selector import ModelSelector

        multiplier = ModelSelector.estimate_cost_multiplier("balanced")

        assert multiplier == 1.0

    def test_estimate_cost_multiplier_full_firepower(self):
        """Test cost multiplier for full_firepower tier."""
        from src.runtime.agents.model_selector import ModelSelector

        multiplier = ModelSelector.estimate_cost_multiplier("full_firepower")

        assert multiplier == 2.5

    def test_estimate_cost_multiplier_invalid(self):
        """Test cost multiplier with invalid tier."""
        from src.runtime.agents.model_selector import ModelSelector

        with pytest.raises(ValueError) as exc_info:
            ModelSelector.estimate_cost_multiplier("invalid_tier")

        assert "Invalid tier" in str(exc_info.value)

    def test_get_tier_description_full_firepower(self):
        """Test tier description for full_firepower."""
        from src.runtime.agents.model_selector import ModelSelector

        desc = ModelSelector.get_tier_description("full_firepower")

        assert "Best model" in desc
        assert "highest cost" in desc

    def test_get_tier_description_balanced(self):
        """Test tier description for balanced."""
        from src.runtime.agents.model_selector import ModelSelector

        desc = ModelSelector.get_tier_description("balanced")

        assert "cost/quality balance" in desc

    def test_get_tier_description_economical(self):
        """Test tier description for economical."""
        from src.runtime.agents.model_selector import ModelSelector

        desc = ModelSelector.get_tier_description("economical")

        assert "minimum cost" in desc

    def test_get_tier_description_unknown(self):
        """Test tier description for unknown tier."""
        from src.runtime.agents.model_selector import ModelSelector

        desc = ModelSelector.get_tier_description("unknown")

        assert desc == "Unknown tier"


class TestTierMapping:
    """Test TIER_MAPPING constant."""

    def test_tier_mapping_structure(self):
        """Test TIER_MAPPING has correct structure."""
        from src.runtime.agents.model_selector import ModelSelector

        assert len(ModelSelector.TIER_MAPPING) == 3

        for tier in ModelSelector.TIER_MAPPING:
            assert len(ModelSelector.TIER_MAPPING[tier]) == 3
            for complexity in ["strategic", "creative", "routine"]:
                assert complexity in ModelSelector.TIER_MAPPING[tier]

    def test_tier_mapping_values_are_valid_models(self):
        """Test all mapped values are valid model IDs."""
        from src.runtime.agents.model_selector import ModelSelector

        valid_models = {
            "claude-opus-4-5-20251101",
            "claude-sonnet-4-5-20250929",
            "claude-3-5-haiku-20241022"
        }

        for tier in ModelSelector.TIER_MAPPING.values():
            for model in tier.values():
                assert model in valid_models


class TestCostMultipliers:
    """Test COST_MULTIPLIERS constant."""

    def test_cost_multipliers_has_all_tiers(self):
        """Test COST_MULTIPLIERS has all tiers."""
        from src.runtime.agents.model_selector import ModelSelector

        for tier in ModelSelector.TIER_MAPPING.keys():
            assert tier in ModelSelector.COST_MULTIPLIERS

    def test_balanced_is_baseline(self):
        """Test balanced tier is the baseline (1.0)."""
        from src.runtime.agents.model_selector import ModelSelector

        assert ModelSelector.COST_MULTIPLIERS["balanced"] == 1.0

    def test_economical_is_cheaper(self):
        """Test economical is cheaper than balanced."""
        from src.runtime.agents.model_selector import ModelSelector

        assert ModelSelector.COST_MULTIPLIERS["economical"] < ModelSelector.COST_MULTIPLIERS["balanced"]

    def test_full_firepower_is_most_expensive(self):
        """Test full_firepower is most expensive."""
        from src.runtime.agents.model_selector import ModelSelector

        assert ModelSelector.COST_MULTIPLIERS["full_firepower"] > ModelSelector.COST_MULTIPLIERS["balanced"]
