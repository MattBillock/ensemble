"""Cost calculation utilities for Anthropic API usage."""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class CostCalculator:
    """Calculate costs based on model and token usage."""

    # Pricing as of January 2026 (per million tokens)
    # Source: https://www.anthropic.com/pricing
    PRICING = {
        "claude-opus-4-5-20251101": {
            "input": 15.00,
            "output": 75.00
        },
        "claude-sonnet-4-5-20250929": {
            "input": 3.00,
            "output": 15.00
        },
        "claude-3-5-haiku-20241022": {
            "input": 0.80,
            "output": 4.00
        },
        # Fallback for older models
        "claude-3-opus-20240229": {
            "input": 15.00,
            "output": 75.00
        },
        "claude-3-sonnet-20240229": {
            "input": 3.00,
            "output": 15.00
        },
        "claude-3-haiku-20240307": {
            "input": 0.25,
            "output": 1.25
        }
    }

    @classmethod
    def calculate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for given usage.

        Args:
            model: Model ID (e.g., "claude-sonnet-4-5-20250929")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD

        Example:
            >>> CostCalculator.calculate_cost("claude-sonnet-4-5-20250929", 10000, 5000)
            0.105  # $0.105 = (10k/1M * $3) + (5k/1M * $15)
        """
        if not input_tokens and not output_tokens:
            return 0.0

        # Get pricing for this model (fallback to Sonnet if unknown)
        pricing = cls.PRICING.get(model)
        if not pricing:
            logger.warning(f"Unknown model '{model}', using Sonnet pricing as estimate")
            pricing = cls.PRICING["claude-sonnet-4-5-20250929"]

        # Calculate costs
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        total_cost = input_cost + output_cost

        logger.debug(
            f"Cost for {model}: {input_tokens} input + {output_tokens} output = ${total_cost:.6f}"
        )

        return total_cost

    @classmethod
    def get_pricing_info(cls, model: str) -> Optional[Dict[str, float]]:
        """
        Get pricing information for a specific model.

        Args:
            model: Model ID

        Returns:
            Dict with 'input' and 'output' pricing per million tokens, or None if unknown
        """
        return cls.PRICING.get(model)

    @classmethod
    def estimate_cost(
        cls,
        model: str,
        estimated_input_tokens: int,
        estimated_output_tokens: int
    ) -> Dict[str, float]:
        """
        Estimate cost for a planned API call.

        Args:
            model: Model ID
            estimated_input_tokens: Estimated input tokens
            estimated_output_tokens: Estimated output tokens

        Returns:
            Dict with 'cost', 'input_cost', 'output_cost', 'total_tokens'
        """
        pricing = cls.get_pricing_info(model)
        if not pricing:
            pricing = cls.PRICING["claude-sonnet-4-5-20250929"]

        input_cost = (estimated_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (estimated_output_tokens / 1_000_000) * pricing["output"]

        return {
            "model": model,
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "total_tokens": estimated_input_tokens + estimated_output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
            "pricing_per_1m_input": pricing["input"],
            "pricing_per_1m_output": pricing["output"]
        }

    @classmethod
    def compare_models(
        cls,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare costs across all available models for given token usage.

        Args:
            input_tokens: Input token count
            output_tokens: Output token count

        Returns:
            Dict mapping model names to cost breakdowns

        Example:
            >>> CostCalculator.compare_models(10000, 5000)
            {
                "claude-opus-4-5-20251101": {"total_cost": 0.525, ...},
                "claude-sonnet-4-5-20250929": {"total_cost": 0.105, ...},
                "claude-3-5-haiku-20241022": {"total_cost": 0.028, ...}
            }
        """
        comparison = {}

        for model in cls.PRICING.keys():
            comparison[model] = cls.estimate_cost(model, input_tokens, output_tokens)

        # Sort by total cost
        comparison = dict(sorted(comparison.items(), key=lambda x: x[1]["total_cost"]))

        return comparison


# Convenience function for quick calculations
def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Convenience function for calculating API cost.

    Args:
        model: Model ID
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD
    """
    return CostCalculator.calculate_cost(model, input_tokens, output_tokens)
