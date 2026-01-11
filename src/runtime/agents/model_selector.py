"""Model selection based on budget tier and task complexity."""
from typing import Dict, List, Optional


class ModelSelector:
    """Select appropriate LLM model based on budget tier and task complexity."""

    # Model tier mappings: budget_tier -> task_complexity -> model_id
    # Updated January 2025 with current Claude model IDs
    TIER_MAPPING: Dict[str, Dict[str, str]] = {
        "full_firepower": {
            "strategic": "claude-opus-4-5-20251101",
            "creative": "claude-sonnet-4-5-20250929",
            "routine": "claude-sonnet-4-5-20250929",
        },
        "balanced": {
            "strategic": "claude-sonnet-4-5-20250929",
            "creative": "claude-sonnet-4-5-20250929",
            "routine": "claude-3-5-haiku-20241022",
        },
        "economical": {
            "strategic": "claude-sonnet-4-5-20250929",  # Can't compromise on strategic
            "creative": "claude-3-5-haiku-20241022",
            "routine": "claude-3-5-haiku-20241022",
        },
    }

    # Cost multipliers relative to balanced tier
    COST_MULTIPLIERS: Dict[str, float] = {
        "economical": 0.7,
        "balanced": 1.0,
        "full_firepower": 2.5,
    }

    @classmethod
    def select_model(
        cls,
        budget_tier: str = "balanced",
        task_complexity: str = "routine",
        agent_name: Optional[str] = None,
    ) -> str:
        """
        Select appropriate model for agent execution.

        Args:
            budget_tier: One of 'full_firepower', 'balanced', 'economical'
            task_complexity: One of 'strategic', 'creative', 'routine'
            agent_name: Optional agent name for logging/debugging

        Returns:
            Full model identifier (e.g., 'claude-3-5-haiku-20241022')

        Raises:
            ValueError: If tier or complexity is invalid

        Examples:
            >>> ModelSelector.select_model("balanced", "strategic")
            'claude-sonnet-4-5-20250929'

            >>> ModelSelector.select_model("full_firepower", "strategic")
            'claude-opus-4-5-20251101'

            >>> ModelSelector.select_model()  # Defaults
            'claude-3-5-haiku-20241022'
        """
        # Validate inputs
        if budget_tier not in cls.TIER_MAPPING:
            valid_tiers = ", ".join(cls.TIER_MAPPING.keys())
            raise ValueError(
                f"Invalid budget_tier '{budget_tier}'. "
                f"Must be one of: {valid_tiers}"
            )

        if task_complexity not in cls.TIER_MAPPING[budget_tier]:
            valid_complexities = ", ".join(cls.TIER_MAPPING[budget_tier].keys())
            raise ValueError(
                f"Invalid task_complexity '{task_complexity}'. "
                f"Must be one of: {valid_complexities}"
            )

        # Select model
        model = cls.TIER_MAPPING[budget_tier][task_complexity]

        # Optional logging (can be enhanced later)
        if agent_name:
            pass  # Could log: f"Selected {model} for {agent_name} (tier={budget_tier}, complexity={task_complexity})"

        return model

    @classmethod
    def get_available_tiers(cls) -> List[str]:
        """
        Return list of available budget tiers.

        Returns:
            List of tier names

        Example:
            >>> ModelSelector.get_available_tiers()
            ['full_firepower', 'balanced', 'economical']
        """
        return list(cls.TIER_MAPPING.keys())

    @classmethod
    def get_available_complexities(cls) -> List[str]:
        """
        Return list of available task complexities.

        Returns:
            List of complexity levels

        Example:
            >>> ModelSelector.get_available_complexities()
            ['strategic', 'creative', 'routine']
        """
        # All tiers have same complexities, so just grab from any tier
        return list(next(iter(cls.TIER_MAPPING.values())).keys())

    @classmethod
    def estimate_cost_multiplier(cls, tier: str) -> float:
        """
        Return approximate cost multiplier for tier relative to balanced.

        Args:
            tier: Budget tier name

        Returns:
            Cost multiplier (1.0 = baseline 'balanced' tier)

        Raises:
            ValueError: If tier is invalid

        Example:
            >>> ModelSelector.estimate_cost_multiplier("economical")
            0.7
            >>> ModelSelector.estimate_cost_multiplier("balanced")
            1.0
            >>> ModelSelector.estimate_cost_multiplier("full_firepower")
            2.5
        """
        if tier not in cls.COST_MULTIPLIERS:
            valid_tiers = ", ".join(cls.COST_MULTIPLIERS.keys())
            raise ValueError(
                f"Invalid tier '{tier}'. Must be one of: {valid_tiers}"
            )

        return cls.COST_MULTIPLIERS[tier]

    @classmethod
    def get_tier_description(cls, tier: str) -> str:
        """
        Get human-readable description of budget tier.

        Args:
            tier: Budget tier name

        Returns:
            Description string

        Example:
            >>> ModelSelector.get_tier_description("balanced")
            'Sonnet for strategic, Haiku for routine - best cost/quality balance'
        """
        descriptions = {
            "full_firepower": "Best model for each task - maximum quality, highest cost",
            "balanced": "Sonnet for strategic, Haiku for routine - best cost/quality balance",
            "economical": "Haiku everywhere possible - minimum cost, good quality",
        }
        return descriptions.get(tier, "Unknown tier")
