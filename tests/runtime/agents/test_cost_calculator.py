"""
Unit tests for cost_calculator module.

Tests the CostCalculator class for accurate API cost calculations.
"""

import pytest
from src.runtime.agents.cost_calculator import CostCalculator, calculate_cost


class TestCostCalculator:
    """Test CostCalculator class."""

    def test_calculate_cost_sonnet(self):
        """Test cost calculation for Sonnet model."""
        # Sonnet: $3/1M input, $15/1M output
        cost = CostCalculator.calculate_cost(
            "claude-sonnet-4-5-20250929",
            input_tokens=1_000_000,
            output_tokens=1_000_000
        )
        assert cost == 18.0  # $3 + $15

    def test_calculate_cost_opus(self):
        """Test cost calculation for Opus model."""
        # Opus: $15/1M input, $75/1M output
        cost = CostCalculator.calculate_cost(
            "claude-opus-4-5-20251101",
            input_tokens=1_000_000,
            output_tokens=1_000_000
        )
        assert cost == 90.0  # $15 + $75

    def test_calculate_cost_haiku(self):
        """Test cost calculation for Haiku model."""
        # Haiku: $0.80/1M input, $4/1M output
        cost = CostCalculator.calculate_cost(
            "claude-3-5-haiku-20241022",
            input_tokens=1_000_000,
            output_tokens=1_000_000
        )
        assert cost == 4.8  # $0.80 + $4

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        cost = CostCalculator.calculate_cost(
            "claude-sonnet-4-5-20250929",
            input_tokens=0,
            output_tokens=0
        )
        assert cost == 0.0

    def test_calculate_cost_unknown_model(self):
        """Test cost calculation for unknown model falls back to Sonnet."""
        cost = CostCalculator.calculate_cost(
            "unknown-model",
            input_tokens=1_000_000,
            output_tokens=1_000_000
        )
        # Should use Sonnet pricing
        assert cost == 18.0

    def test_calculate_cost_small_amounts(self):
        """Test cost calculation for small token amounts."""
        # 10k input, 5k output with Sonnet
        cost = CostCalculator.calculate_cost(
            "claude-sonnet-4-5-20250929",
            input_tokens=10_000,
            output_tokens=5_000
        )
        # (10k/1M * $3) + (5k/1M * $15) = $0.03 + $0.075 = $0.105
        assert abs(cost - 0.105) < 0.0001

    def test_calculate_cost_legacy_opus(self):
        """Test cost calculation for legacy Opus model."""
        cost = CostCalculator.calculate_cost(
            "claude-3-opus-20240229",
            input_tokens=1_000_000,
            output_tokens=0
        )
        assert cost == 15.0

    def test_calculate_cost_legacy_haiku(self):
        """Test cost calculation for legacy Haiku model."""
        cost = CostCalculator.calculate_cost(
            "claude-3-haiku-20240307",
            input_tokens=1_000_000,
            output_tokens=1_000_000
        )
        # $0.25 + $1.25 = $1.50
        assert cost == 1.5


class TestGetPricingInfo:
    """Test get_pricing_info method."""

    def test_get_pricing_info_known_model(self):
        """Test getting pricing for a known model."""
        pricing = CostCalculator.get_pricing_info("claude-sonnet-4-5-20250929")
        assert pricing is not None
        assert pricing["input"] == 3.0
        assert pricing["output"] == 15.0

    def test_get_pricing_info_unknown_model(self):
        """Test getting pricing for unknown model returns None."""
        pricing = CostCalculator.get_pricing_info("unknown-model")
        assert pricing is None

    def test_get_pricing_info_all_models(self):
        """Test all models in PRICING have valid pricing."""
        for model in CostCalculator.PRICING:
            pricing = CostCalculator.get_pricing_info(model)
            assert pricing is not None
            assert "input" in pricing
            assert "output" in pricing
            assert pricing["input"] > 0
            assert pricing["output"] > 0


class TestEstimateCost:
    """Test estimate_cost method."""

    def test_estimate_cost_basic(self):
        """Test basic cost estimation."""
        estimate = CostCalculator.estimate_cost(
            "claude-sonnet-4-5-20250929",
            estimated_input_tokens=10_000,
            estimated_output_tokens=5_000
        )

        assert estimate["model"] == "claude-sonnet-4-5-20250929"
        assert estimate["estimated_input_tokens"] == 10_000
        assert estimate["estimated_output_tokens"] == 5_000
        assert estimate["total_tokens"] == 15_000
        assert abs(estimate["input_cost"] - 0.03) < 0.0001
        assert abs(estimate["output_cost"] - 0.075) < 0.0001
        assert abs(estimate["total_cost"] - 0.105) < 0.0001

    def test_estimate_cost_unknown_model(self):
        """Test estimation for unknown model uses Sonnet pricing."""
        estimate = CostCalculator.estimate_cost(
            "unknown-model",
            estimated_input_tokens=1_000_000,
            estimated_output_tokens=1_000_000
        )
        assert estimate["total_cost"] == 18.0

    def test_estimate_cost_includes_pricing_info(self):
        """Test estimation includes pricing per million tokens."""
        estimate = CostCalculator.estimate_cost(
            "claude-sonnet-4-5-20250929",
            estimated_input_tokens=100,
            estimated_output_tokens=100
        )
        assert estimate["pricing_per_1m_input"] == 3.0
        assert estimate["pricing_per_1m_output"] == 15.0


class TestCompareModels:
    """Test compare_models method."""

    def test_compare_models_returns_all_models(self):
        """Test that compare_models returns all available models."""
        comparison = CostCalculator.compare_models(
            input_tokens=10_000,
            output_tokens=5_000
        )

        assert len(comparison) == len(CostCalculator.PRICING)
        for model in CostCalculator.PRICING:
            assert model in comparison

    def test_compare_models_sorted_by_cost(self):
        """Test that compare_models returns models sorted by cost."""
        comparison = CostCalculator.compare_models(
            input_tokens=10_000,
            output_tokens=5_000
        )

        costs = [v["total_cost"] for v in comparison.values()]
        assert costs == sorted(costs)

    def test_compare_models_haiku_cheapest(self):
        """Test that Haiku is the cheapest model."""
        comparison = CostCalculator.compare_models(
            input_tokens=10_000,
            output_tokens=5_000
        )

        first_model = list(comparison.keys())[0]
        assert "haiku" in first_model.lower()

    def test_compare_models_opus_most_expensive(self):
        """Test that Opus is the most expensive model."""
        comparison = CostCalculator.compare_models(
            input_tokens=10_000,
            output_tokens=5_000
        )

        last_model = list(comparison.keys())[-1]
        assert "opus" in last_model.lower()


class TestConvenienceFunction:
    """Test the calculate_cost convenience function."""

    def test_convenience_function_works(self):
        """Test that the convenience function calls CostCalculator."""
        cost = calculate_cost(
            "claude-sonnet-4-5-20250929",
            input_tokens=10_000,
            output_tokens=5_000
        )
        expected = CostCalculator.calculate_cost(
            "claude-sonnet-4-5-20250929",
            input_tokens=10_000,
            output_tokens=5_000
        )
        assert cost == expected
