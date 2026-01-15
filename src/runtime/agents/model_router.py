"""
Model Router - Dynamic, self-managed LLM selection with quality fuzzing.

Provides intelligent model selection based on task complexity, agent performance
history, cost constraints, and randomized quality fuzzing for diversity.
Supports multiple providers: Anthropic, OpenAI, Google, and local models.
"""
import logging
import random
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Provider(Enum):
    """LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    LOCAL = "local"


class QualityTier(Enum):
    """Model quality tiers for fuzzing."""
    FLAGSHIP = "flagship"       # Best available (Opus, GPT-4o, etc.)
    HIGH = "high"               # Strong models (Sonnet, GPT-4-turbo)
    BALANCED = "balanced"       # Good balance (Sonnet, GPT-4)
    EFFICIENT = "efficient"     # Cost-effective (Haiku, GPT-3.5)
    LOCAL = "local"             # Local models (Ollama, etc.)


@dataclass
class ModelSpec:
    """Specification for an LLM model."""
    provider: Provider
    model_id: str
    display_name: str
    quality_tier: QualityTier
    cost_per_1k_input: float    # USD per 1000 input tokens
    cost_per_1k_output: float   # USD per 1000 output tokens
    context_window: int
    max_output_tokens: int
    strengths: List[str] = field(default_factory=list)  # e.g., ["reasoning", "code", "creative"]
    latency_ms: int = 500       # Typical latency
    available: bool = True


# Model catalog
MODEL_CATALOG: Dict[str, ModelSpec] = {
    # Anthropic models
    "claude-opus-4-5-20251101": ModelSpec(
        provider=Provider.ANTHROPIC,
        model_id="claude-opus-4-5-20251101",
        display_name="Claude Opus 4.5",
        quality_tier=QualityTier.FLAGSHIP,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        context_window=200000,
        max_output_tokens=32000,
        strengths=["reasoning", "code", "analysis", "creative", "complex_tasks"]
    ),
    "claude-sonnet-4-20250514": ModelSpec(
        provider=Provider.ANTHROPIC,
        model_id="claude-sonnet-4-20250514",
        display_name="Claude Sonnet 4",
        quality_tier=QualityTier.HIGH,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        context_window=200000,
        max_output_tokens=64000,
        strengths=["code", "analysis", "reasoning", "balanced"]
    ),
    "claude-haiku-3-5-20241022": ModelSpec(
        provider=Provider.ANTHROPIC,
        model_id="claude-haiku-3-5-20241022",
        display_name="Claude Haiku 3.5",
        quality_tier=QualityTier.EFFICIENT,
        cost_per_1k_input=0.0008,
        cost_per_1k_output=0.004,
        context_window=200000,
        max_output_tokens=8192,
        strengths=["fast", "simple_tasks", "cost_effective"]
    ),

    # OpenAI models (when configured)
    "gpt-4o": ModelSpec(
        provider=Provider.OPENAI,
        model_id="gpt-4o",
        display_name="GPT-4o",
        quality_tier=QualityTier.HIGH,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        context_window=128000,
        max_output_tokens=16384,
        strengths=["reasoning", "multimodal", "code"],
        available=False  # Requires OpenAI API key
    ),
    "gpt-4-turbo": ModelSpec(
        provider=Provider.OPENAI,
        model_id="gpt-4-turbo",
        display_name="GPT-4 Turbo",
        quality_tier=QualityTier.HIGH,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        context_window=128000,
        max_output_tokens=4096,
        strengths=["reasoning", "code", "balanced"],
        available=False
    ),
    "gpt-3.5-turbo": ModelSpec(
        provider=Provider.OPENAI,
        model_id="gpt-3.5-turbo",
        display_name="GPT-3.5 Turbo",
        quality_tier=QualityTier.EFFICIENT,
        cost_per_1k_input=0.0005,
        cost_per_1k_output=0.0015,
        context_window=16385,
        max_output_tokens=4096,
        strengths=["fast", "simple_tasks"],
        available=False
    ),

    # Google models (when configured)
    "gemini-pro": ModelSpec(
        provider=Provider.GOOGLE,
        model_id="gemini-pro",
        display_name="Gemini Pro",
        quality_tier=QualityTier.BALANCED,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.0005,
        context_window=32000,
        max_output_tokens=8192,
        strengths=["multimodal", "balanced"],
        available=False
    ),

    # Local models (when Ollama is running)
    "llama3:70b": ModelSpec(
        provider=Provider.LOCAL,
        model_id="llama3:70b",
        display_name="Llama 3 70B",
        quality_tier=QualityTier.BALANCED,
        cost_per_1k_input=0.0,  # Free, but uses local compute
        cost_per_1k_output=0.0,
        context_window=8192,
        max_output_tokens=4096,
        strengths=["privacy", "no_api_costs"],
        available=False
    ),
    "codellama:34b": ModelSpec(
        provider=Provider.LOCAL,
        model_id="codellama:34b",
        display_name="Code Llama 34B",
        quality_tier=QualityTier.EFFICIENT,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        context_window=16384,
        max_output_tokens=4096,
        strengths=["code", "privacy"],
        available=False
    ),
}


@dataclass
class TaskProfile:
    """Profile of a task for model selection."""
    complexity: float           # 0.0 to 1.0, estimated task complexity
    requires_reasoning: bool    # Deep reasoning required
    requires_code: bool         # Code generation/analysis
    requires_creativity: bool   # Creative output
    context_size: int           # Estimated context tokens needed
    priority: str               # "high", "normal", "low"
    agent_type: str             # Type of agent performing task
    historical_model: Optional[str] = None  # What model worked before


@dataclass
class SelectionResult:
    """Result of model selection."""
    model_id: str
    model_spec: ModelSpec
    selection_reason: str
    confidence: float           # 0.0 to 1.0
    alternatives: List[str]     # Other viable options


class PerformanceTracker:
    """Tracks model performance for intelligent selection."""

    def __init__(self):
        self._stats: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def record_execution(
        self,
        model_id: str,
        agent_type: str,
        success: bool,
        tokens_used: int,
        duration_ms: int,
        quality_score: Optional[float] = None
    ):
        """Record a model execution."""
        with self._lock:
            key = f"{model_id}:{agent_type}"

            if key not in self._stats:
                self._stats[key] = {
                    "total": 0,
                    "successes": 0,
                    "failures": 0,
                    "total_tokens": 0,
                    "total_duration_ms": 0,
                    "quality_scores": [],
                    "last_used": None
                }

            stats = self._stats[key]
            stats["total"] += 1
            if success:
                stats["successes"] += 1
            else:
                stats["failures"] += 1
            stats["total_tokens"] += tokens_used
            stats["total_duration_ms"] += duration_ms
            if quality_score is not None:
                stats["quality_scores"].append(quality_score)
                # Keep only last 100 scores
                stats["quality_scores"] = stats["quality_scores"][-100:]
            stats["last_used"] = datetime.now().isoformat()

    def get_performance(
        self,
        model_id: str,
        agent_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance stats for a model."""
        with self._lock:
            if agent_type:
                key = f"{model_id}:{agent_type}"
                return self._stats.get(key, {})
            else:
                # Aggregate across all agent types
                aggregate = {
                    "total": 0,
                    "successes": 0,
                    "failures": 0,
                    "success_rate": 0,
                    "avg_quality": 0
                }

                for key, stats in self._stats.items():
                    if key.startswith(f"{model_id}:"):
                        aggregate["total"] += stats["total"]
                        aggregate["successes"] += stats["successes"]
                        aggregate["failures"] += stats["failures"]

                if aggregate["total"] > 0:
                    aggregate["success_rate"] = aggregate["successes"] / aggregate["total"]

                return aggregate

    def get_best_model_for_agent(self, agent_type: str) -> Optional[str]:
        """Get the historically best-performing model for an agent type."""
        with self._lock:
            best_model = None
            best_score = -1

            for key, stats in self._stats.items():
                if not key.endswith(f":{agent_type}"):
                    continue

                model_id = key.split(":")[0]
                if stats["total"] < 3:  # Need at least 3 executions
                    continue

                success_rate = stats["successes"] / stats["total"]
                avg_quality = (
                    sum(stats["quality_scores"]) / len(stats["quality_scores"])
                    if stats["quality_scores"] else 0.5
                )

                # Combined score
                score = (success_rate * 0.6) + (avg_quality * 0.4)

                if score > best_score:
                    best_score = score
                    best_model = model_id

            return best_model


class ModelRouter:
    """
    Dynamic model router with quality fuzzing and self-management.

    Features:
    - Multi-provider support (Anthropic, OpenAI, Google, Local)
    - Quality fuzzing for diversity
    - Performance-based learning
    - Cost-aware selection
    - Task complexity analysis
    - "All guns blazing" mode for critical tasks
    """

    def __init__(
        self,
        anthropic_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        google_key: Optional[str] = None,
        local_endpoint: Optional[str] = None,
        target_quality: float = 0.7,  # 0.0 to 1.0, target quality level
        quality_variance: float = 0.15,  # Fuzzing variance
        cost_weight: float = 0.3,  # How much to weight cost in selection
        enable_fuzzing: bool = True
    ):
        self.api_keys = {
            Provider.ANTHROPIC: anthropic_key,
            Provider.OPENAI: openai_key,
            Provider.GOOGLE: google_key,
        }
        self.local_endpoint = local_endpoint
        self.target_quality = target_quality
        self.quality_variance = quality_variance
        self.cost_weight = cost_weight
        self.enable_fuzzing = enable_fuzzing

        self.performance_tracker = PerformanceTracker()
        self._update_model_availability()

        logger.info(f"ModelRouter initialized with target_quality={target_quality}, fuzzing={enable_fuzzing}")

    def _update_model_availability(self):
        """Update which models are available based on API keys."""
        for model_id, spec in MODEL_CATALOG.items():
            if spec.provider == Provider.ANTHROPIC:
                spec.available = bool(self.api_keys.get(Provider.ANTHROPIC))
            elif spec.provider == Provider.OPENAI:
                spec.available = bool(self.api_keys.get(Provider.OPENAI))
            elif spec.provider == Provider.GOOGLE:
                spec.available = bool(self.api_keys.get(Provider.GOOGLE))
            elif spec.provider == Provider.LOCAL:
                spec.available = self._check_local_model(spec.model_id)

    def _check_local_model(self, model_id: str) -> bool:
        """Check if a local model is available."""
        if not self.local_endpoint:
            return False
        # Could ping Ollama to check model availability
        return False  # Disabled by default

    def select_model(
        self,
        task_profile: TaskProfile,
        mode: str = "dynamic",  # "dynamic", "full_power", "economical"
        excluded_models: Optional[List[str]] = None
    ) -> SelectionResult:
        """
        Select the best model for a task.

        Args:
            task_profile: Profile of the task
            mode: Selection mode
                - "dynamic": Self-managed selection with fuzzing
                - "full_power": Always use flagship model
                - "economical": Minimize cost
            excluded_models: Models to exclude from selection

        Returns:
            SelectionResult with selected model and reasoning
        """
        excluded = set(excluded_models or [])

        # Full power mode - always use flagship
        if mode == "full_power":
            flagship = self._get_flagship_model()
            return SelectionResult(
                model_id=flagship.model_id,
                model_spec=flagship,
                selection_reason="Full power mode - using flagship model",
                confidence=1.0,
                alternatives=[]
            )

        # Get available models
        available_models = [
            (mid, spec) for mid, spec in MODEL_CATALOG.items()
            if spec.available and mid not in excluded
        ]

        if not available_models:
            # Fallback to any Anthropic model
            for mid, spec in MODEL_CATALOG.items():
                if spec.provider == Provider.ANTHROPIC and mid not in excluded:
                    return SelectionResult(
                        model_id=mid,
                        model_spec=spec,
                        selection_reason="No configured models available - using default",
                        confidence=0.5,
                        alternatives=[]
                    )
            raise ValueError("No models available")

        # Score each model
        scored_models = []
        for model_id, spec in available_models:
            score = self._score_model(spec, task_profile, mode)
            scored_models.append((model_id, spec, score))

        # Sort by score
        scored_models.sort(key=lambda x: x[2], reverse=True)

        # Apply fuzzing if enabled and not economical mode
        if self.enable_fuzzing and mode != "economical":
            selected = self._apply_fuzzing(scored_models, task_profile)
        else:
            selected = scored_models[0]

        model_id, spec, score = selected

        # Build alternatives list
        alternatives = [m[0] for m in scored_models[1:4]]

        return SelectionResult(
            model_id=model_id,
            model_spec=spec,
            selection_reason=self._build_selection_reason(spec, task_profile, score),
            confidence=min(1.0, score),
            alternatives=alternatives
        )

    def _score_model(
        self,
        spec: ModelSpec,
        task_profile: TaskProfile,
        mode: str
    ) -> float:
        """Score a model for a task."""
        score = 0.0

        # Quality tier score (0.0 to 0.4)
        tier_scores = {
            QualityTier.FLAGSHIP: 0.4,
            QualityTier.HIGH: 0.3,
            QualityTier.BALANCED: 0.2,
            QualityTier.EFFICIENT: 0.1,
            QualityTier.LOCAL: 0.15
        }
        score += tier_scores.get(spec.quality_tier, 0.2)

        # Complexity matching (0.0 to 0.2)
        if task_profile.complexity > 0.7:
            if spec.quality_tier in (QualityTier.FLAGSHIP, QualityTier.HIGH):
                score += 0.2
        elif task_profile.complexity < 0.3:
            if spec.quality_tier in (QualityTier.EFFICIENT, QualityTier.LOCAL):
                score += 0.2
        else:
            if spec.quality_tier == QualityTier.BALANCED:
                score += 0.2

        # Strength matching (0.0 to 0.2)
        strength_matches = 0
        if task_profile.requires_reasoning and "reasoning" in spec.strengths:
            strength_matches += 1
        if task_profile.requires_code and "code" in spec.strengths:
            strength_matches += 1
        if task_profile.requires_creativity and "creative" in spec.strengths:
            strength_matches += 1
        score += min(0.2, strength_matches * 0.07)

        # Historical performance (0.0 to 0.15)
        perf = self.performance_tracker.get_performance(spec.model_id, task_profile.agent_type)
        if perf.get("total", 0) >= 3:
            success_rate = perf.get("success_rate", 0.5)
            score += success_rate * 0.15

        # Cost adjustment (negative score for expensive models if cost_weight > 0)
        if mode == "economical":
            # Heavy cost penalty
            cost_factor = spec.cost_per_1k_input + spec.cost_per_1k_output
            score -= cost_factor * 10  # Strong penalty
        else:
            cost_factor = spec.cost_per_1k_input + spec.cost_per_1k_output
            score -= cost_factor * self.cost_weight

        return max(0.0, score)

    def _apply_fuzzing(
        self,
        scored_models: List[Tuple[str, ModelSpec, float]],
        task_profile: TaskProfile
    ) -> Tuple[str, ModelSpec, float]:
        """Apply quality fuzzing to model selection."""
        if len(scored_models) < 2:
            return scored_models[0]

        # Calculate target quality with variance
        fuzzed_target = self.target_quality + random.gauss(0, self.quality_variance)
        fuzzed_target = max(0.0, min(1.0, fuzzed_target))

        # Adjust for task priority
        if task_profile.priority == "high":
            fuzzed_target = min(1.0, fuzzed_target + 0.2)
        elif task_profile.priority == "low":
            fuzzed_target = max(0.0, fuzzed_target - 0.2)

        # Map target to tier
        target_tier_idx = int(fuzzed_target * (len(scored_models) - 1))
        target_tier_idx = min(target_tier_idx, len(scored_models) - 1)

        # Add some randomness to final selection
        selection_range = min(2, len(scored_models) - target_tier_idx)
        final_idx = target_tier_idx + random.randint(0, selection_range - 1)
        final_idx = min(final_idx, len(scored_models) - 1)

        return scored_models[final_idx]

    def _get_flagship_model(self) -> ModelSpec:
        """Get the flagship model (for full power mode)."""
        for model_id, spec in MODEL_CATALOG.items():
            if spec.quality_tier == QualityTier.FLAGSHIP and spec.available:
                return spec

        # Fallback to highest quality available
        for tier in [QualityTier.HIGH, QualityTier.BALANCED, QualityTier.EFFICIENT]:
            for model_id, spec in MODEL_CATALOG.items():
                if spec.quality_tier == tier and spec.available:
                    return spec

        raise ValueError("No models available")

    def _build_selection_reason(
        self,
        spec: ModelSpec,
        task_profile: TaskProfile,
        score: float
    ) -> str:
        """Build a human-readable selection reason."""
        reasons = []

        if spec.quality_tier == QualityTier.FLAGSHIP:
            reasons.append("flagship model for complex task")
        elif spec.quality_tier == QualityTier.EFFICIENT:
            reasons.append("efficient model for cost savings")

        if task_profile.requires_code and "code" in spec.strengths:
            reasons.append("strong code capabilities")
        if task_profile.requires_reasoning and "reasoning" in spec.strengths:
            reasons.append("strong reasoning")

        if not reasons:
            reasons.append("balanced selection")

        return f"Selected {spec.display_name}: {', '.join(reasons)} (score: {score:.2f})"

    def record_execution_result(
        self,
        model_id: str,
        agent_type: str,
        success: bool,
        tokens_used: int,
        duration_ms: int,
        quality_score: Optional[float] = None
    ):
        """Record execution result for learning."""
        self.performance_tracker.record_execution(
            model_id, agent_type, success, tokens_used, duration_ms, quality_score
        )

    def adjust_target_quality(self, new_target: float):
        """Dynamically adjust target quality level."""
        self.target_quality = max(0.0, min(1.0, new_target))
        logger.info(f"Adjusted target quality to {self.target_quality}")

    def get_model_stats(self) -> Dict[str, Any]:
        """Get statistics about model usage."""
        stats = {
            "target_quality": self.target_quality,
            "quality_variance": self.quality_variance,
            "fuzzing_enabled": self.enable_fuzzing,
            "available_models": [],
            "performance": {}
        }

        for model_id, spec in MODEL_CATALOG.items():
            if spec.available:
                stats["available_models"].append({
                    "model_id": model_id,
                    "display_name": spec.display_name,
                    "provider": spec.provider.value,
                    "tier": spec.quality_tier.value,
                    "cost_per_1k": spec.cost_per_1k_input + spec.cost_per_1k_output
                })

                perf = self.performance_tracker.get_performance(model_id)
                if perf.get("total", 0) > 0:
                    stats["performance"][model_id] = perf

        return stats

    def analyze_task_profile(
        self,
        task_description: str,
        agent_type: str,
        context_size: int = 0
    ) -> TaskProfile:
        """Analyze a task and create a profile for model selection."""
        description_lower = task_description.lower()

        # Estimate complexity
        complexity = 0.5  # Default middle complexity

        high_complexity_indicators = [
            "architect", "design", "complex", "multiple", "integrate",
            "refactor", "optimize", "security", "scale", "distributed"
        ]
        low_complexity_indicators = [
            "simple", "basic", "fix", "typo", "rename", "format",
            "single", "minor", "small", "quick"
        ]

        for indicator in high_complexity_indicators:
            if indicator in description_lower:
                complexity += 0.1
        for indicator in low_complexity_indicators:
            if indicator in description_lower:
                complexity -= 0.1

        complexity = max(0.0, min(1.0, complexity))

        # Detect requirements
        requires_reasoning = any(w in description_lower for w in [
            "analyze", "evaluate", "decide", "choose", "compare",
            "architect", "design", "plan", "strategy"
        ])

        requires_code = any(w in description_lower for w in [
            "code", "implement", "write", "function", "class",
            "test", "debug", "refactor", "api", "endpoint"
        ])

        requires_creativity = any(w in description_lower for w in [
            "creative", "generate", "new", "innovative", "design",
            "style", "ui", "ux", "documentation"
        ])

        # Determine priority based on agent type
        priority = "normal"
        if any(x in agent_type.lower() for x in ["executive", "director", "architect"]):
            priority = "high"
        elif any(x in agent_type.lower() for x in ["drill", "documentation"]):
            priority = "low"

        return TaskProfile(
            complexity=complexity,
            requires_reasoning=requires_reasoning,
            requires_code=requires_code,
            requires_creativity=requires_creativity,
            context_size=context_size,
            priority=priority,
            agent_type=agent_type,
            historical_model=self.performance_tracker.get_best_model_for_agent(agent_type)
        )


# Global router instance
_model_router: Optional[ModelRouter] = None


def get_model_router(
    anthropic_key: Optional[str] = None,
    openai_key: Optional[str] = None,
    **kwargs
) -> ModelRouter:
    """Get or create the global model router."""
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter(
            anthropic_key=anthropic_key,
            openai_key=openai_key,
            **kwargs
        )
    return _model_router
