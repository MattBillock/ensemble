"""Tests for ModelSelector class."""
import pytest
from src.runtime.agents.model_selector import ModelSelector


class TestModelSelector:
    """Test suite for ModelSelector functionality."""

    def test_select_model_full_firepower_strategic(self):
        """Test full_firepower tier with strategic complexity returns opus."""
        model = ModelSelector.select_model("full_firepower", "strategic")
        assert model == "claude-opus-4-5-20251101"

    def test_select_model_full_firepower_creative(self):
        """Test full_firepower tier with creative complexity returns sonnet."""
        model = ModelSelector.select_model("full_firepower", "creative")
        assert model == "claude-sonnet-4-5-20250929"

    def test_select_model_balanced_strategic(self):
        """Test balanced tier with strategic complexity returns sonnet."""
        model = ModelSelector.select_model("balanced", "strategic")
        assert model == "claude-sonnet-4-5-20250929"

    def test_select_model_balanced_routine(self):
        """Test balanced tier with routine complexity returns haiku."""
        model = ModelSelector.select_model("balanced", "routine")
        assert model == "claude-3-5-haiku-20241022"

    def test_select_model_economical_strategic(self):
        """Test economical tier still uses sonnet for strategic (can't compromise)."""
        model = ModelSelector.select_model("economical", "strategic")
        assert model == "claude-sonnet-4-5-20250929"

    def test_select_model_economical_creative(self):
        """Test economical tier uses haiku for creative tasks."""
        model = ModelSelector.select_model("economical", "creative")
        assert model == "claude-3-5-haiku-20241022"

    def test_select_model_economical_routine(self):
        """Test economical tier uses haiku for routine tasks."""
        model = ModelSelector.select_model("economical", "routine")
        assert model == "claude-3-5-haiku-20241022"

    def test_select_model_with_agent_name(self):
        """Test model selection with agent name provided (should not affect result)."""
        model = ModelSelector.select_model(
            "balanced", "strategic", agent_name="Test Agent"
        )
        assert model == "claude-sonnet-4-5-20250929"

    def test_select_model_default_parameters(self):
        """Test defaults to balanced/routine (haiku)."""
        model = ModelSelector.select_model()
        assert model == "claude-3-5-haiku-20241022"

    def test_select_model_invalid_tier(self):
        """Test invalid tier raises ValueError."""
        with pytest.raises(ValueError, match="Invalid budget_tier"):
            ModelSelector.select_model("super_expensive", "strategic")

    def test_select_model_invalid_complexity(self):
        """Test invalid complexity raises ValueError."""
        with pytest.raises(ValueError, match="Invalid task_complexity"):
            ModelSelector.select_model("balanced", "ultra_hard")

    def test_get_available_tiers(self):
        """Test returns all 3 tiers."""
        tiers = ModelSelector.get_available_tiers()
        assert len(tiers) == 3
        assert "balanced" in tiers
        assert "full_firepower" in tiers
        assert "economical" in tiers

    def test_get_available_complexities(self):
        """Test returns all 3 complexity levels."""
        complexities = ModelSelector.get_available_complexities()
        assert len(complexities) == 3
        assert "strategic" in complexities
        assert "creative" in complexities
        assert "routine" in complexities

    def test_estimate_cost_multiplier_economical(self):
        """Test economical tier is cheaper than balanced."""
        cost = ModelSelector.estimate_cost_multiplier("economical")
        assert cost < 1.0
        assert cost == 0.7

    def test_estimate_cost_multiplier_balanced(self):
        """Test balanced tier is baseline (1.0)."""
        cost = ModelSelector.estimate_cost_multiplier("balanced")
        assert cost == 1.0

    def test_estimate_cost_multiplier_full_firepower(self):
        """Test full_firepower tier is more expensive than balanced."""
        cost = ModelSelector.estimate_cost_multiplier("full_firepower")
        assert cost > 1.0
        assert cost == 2.5

    def test_estimate_cost_multiplier_invalid_tier(self):
        """Test invalid tier raises ValueError."""
        with pytest.raises(ValueError, match="Invalid tier"):
            ModelSelector.estimate_cost_multiplier("invalid")

    def test_get_tier_description(self):
        """Test tier descriptions are returned."""
        desc = ModelSelector.get_tier_description("balanced")
        assert "Sonnet" in desc
        assert "Haiku" in desc

    def test_all_tier_complexity_combinations(self):
        """Test all valid tier/complexity combinations return a model."""
        tiers = ModelSelector.get_available_tiers()
        complexities = ModelSelector.get_available_complexities()

        for tier in tiers:
            for complexity in complexities:
                model = ModelSelector.select_model(tier, complexity)
                assert model is not None
                assert isinstance(model, str)
                assert "claude" in model.lower()

    def test_strategic_always_uses_powerful_model(self):
        """Test strategic tasks always use sonnet or opus (never haiku)."""
        for tier in ModelSelector.get_available_tiers():
            model = ModelSelector.select_model(tier, "strategic")
            assert "haiku" not in model.lower()
            assert "sonnet" in model.lower() or "opus" in model.lower()
