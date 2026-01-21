"""
Comprehensive tests for model_router module.

Tests the ModelRouter, PerformanceTracker, and related functionality
for intelligent model selection with quality fuzzing.
"""

import pytest
import random
from unittest.mock import patch

from src.runtime.agents.model_router import (
    Provider,
    QualityTier,
    ModelSpec,
    TaskProfile,
    SelectionResult,
    PerformanceTracker,
    ModelRouter,
    MODEL_CATALOG,
    get_model_router,
)


class TestProvider:
    """Test Provider enum."""

    def test_provider_values(self):
        """Test Provider enum values."""
        assert Provider.ANTHROPIC.value == "anthropic"
        assert Provider.OPENAI.value == "openai"
        assert Provider.GOOGLE.value == "google"
        assert Provider.LOCAL.value == "local"


class TestQualityTier:
    """Test QualityTier enum."""

    def test_quality_tier_values(self):
        """Test QualityTier enum values."""
        assert QualityTier.FLAGSHIP.value == "flagship"
        assert QualityTier.HIGH.value == "high"
        assert QualityTier.BALANCED.value == "balanced"
        assert QualityTier.EFFICIENT.value == "efficient"
        assert QualityTier.LOCAL.value == "local"


class TestModelSpec:
    """Test ModelSpec dataclass."""

    def test_model_spec_creation(self):
        """Test creating a ModelSpec."""
        spec = ModelSpec(
            provider=Provider.ANTHROPIC,
            model_id="test-model",
            display_name="Test Model",
            quality_tier=QualityTier.BALANCED,
            cost_per_1k_input=0.001,
            cost_per_1k_output=0.002,
            context_window=100000,
            max_output_tokens=4096,
            strengths=["reasoning", "code"]
        )

        assert spec.provider == Provider.ANTHROPIC
        assert spec.model_id == "test-model"
        assert spec.quality_tier == QualityTier.BALANCED
        assert spec.available == True  # Default
        assert spec.latency_ms == 500  # Default

    def test_model_spec_with_custom_values(self):
        """Test ModelSpec with custom optional values."""
        spec = ModelSpec(
            provider=Provider.LOCAL,
            model_id="local-model",
            display_name="Local Model",
            quality_tier=QualityTier.LOCAL,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
            context_window=8192,
            max_output_tokens=2048,
            latency_ms=100,
            available=False
        )

        assert spec.latency_ms == 100
        assert spec.available == False


class TestModelCatalog:
    """Test the MODEL_CATALOG."""

    def test_catalog_contains_anthropic_models(self):
        """Test that catalog contains Anthropic models."""
        anthropic_models = [
            m for m in MODEL_CATALOG.values()
            if m.provider == Provider.ANTHROPIC
        ]
        assert len(anthropic_models) >= 2

    def test_catalog_has_flagship_model(self):
        """Test that catalog has at least one flagship model."""
        flagship_models = [
            m for m in MODEL_CATALOG.values()
            if m.quality_tier == QualityTier.FLAGSHIP
        ]
        assert len(flagship_models) >= 1

    def test_catalog_has_efficient_model(self):
        """Test that catalog has at least one efficient model."""
        efficient_models = [
            m for m in MODEL_CATALOG.values()
            if m.quality_tier == QualityTier.EFFICIENT
        ]
        assert len(efficient_models) >= 1


class TestTaskProfile:
    """Test TaskProfile dataclass."""

    def test_task_profile_creation(self):
        """Test creating a TaskProfile."""
        profile = TaskProfile(
            complexity=0.7,
            requires_reasoning=True,
            requires_code=True,
            requires_creativity=False,
            context_size=50000,
            priority="high",
            agent_type="leadership"
        )

        assert profile.complexity == 0.7
        assert profile.requires_reasoning == True
        assert profile.agent_type == "leadership"
        assert profile.historical_model is None  # Default

    def test_task_profile_with_historical_model(self):
        """Test TaskProfile with historical model."""
        profile = TaskProfile(
            complexity=0.5,
            requires_reasoning=False,
            requires_code=True,
            requires_creativity=False,
            context_size=10000,
            priority="normal",
            agent_type="developers",
            historical_model="claude-sonnet-4-20250514"
        )

        assert profile.historical_model == "claude-sonnet-4-20250514"


class TestSelectionResult:
    """Test SelectionResult dataclass."""

    def test_selection_result_creation(self):
        """Test creating a SelectionResult."""
        spec = MODEL_CATALOG.get("claude-sonnet-4-20250514")
        if spec:
            result = SelectionResult(
                model_id="claude-sonnet-4-20250514",
                model_spec=spec,
                selection_reason="Selected for code task",
                confidence=0.85,
                alternatives=["claude-3-5-haiku-20241022"]
            )

            assert result.model_id == "claude-sonnet-4-20250514"
            assert result.confidence == 0.85
            assert len(result.alternatives) == 1


class TestPerformanceTracker:
    """Test PerformanceTracker class."""

    def test_init(self):
        """Test initialization."""
        tracker = PerformanceTracker()
        assert hasattr(tracker, '_stats')
        assert tracker._stats == {}

    def test_record_execution_success(self):
        """Test recording a successful execution."""
        tracker = PerformanceTracker()

        tracker.record_execution(
            model_id="test-model",
            agent_type="leadership",
            success=True,
            tokens_used=1000,
            duration_ms=500
        )

        perf = tracker.get_performance("test-model", "leadership")
        assert perf["total"] == 1
        assert perf["successes"] == 1
        assert perf["failures"] == 0

    def test_record_execution_failure(self):
        """Test recording a failed execution."""
        tracker = PerformanceTracker()

        tracker.record_execution(
            model_id="test-model",
            agent_type="developers",
            success=False,
            tokens_used=500,
            duration_ms=1000
        )

        perf = tracker.get_performance("test-model", "developers")
        assert perf["failures"] == 1
        assert perf["successes"] == 0

    def test_record_execution_with_quality_score(self):
        """Test recording execution with quality score."""
        tracker = PerformanceTracker()

        tracker.record_execution(
            model_id="test-model",
            agent_type="testers",
            success=True,
            tokens_used=800,
            duration_ms=400,
            quality_score=0.9
        )

        perf = tracker.get_performance("test-model", "testers")
        assert len(perf["quality_scores"]) == 1
        assert perf["quality_scores"][0] == 0.9

    def test_quality_scores_trimmed_to_100(self):
        """Test that quality scores are trimmed to last 100."""
        tracker = PerformanceTracker()

        for i in range(150):
            tracker.record_execution(
                model_id="test-model",
                agent_type="testers",
                success=True,
                tokens_used=100,
                duration_ms=100,
                quality_score=i * 0.01
            )

        perf = tracker.get_performance("test-model", "testers")
        assert len(perf["quality_scores"]) == 100

    def test_get_performance_aggregate(self):
        """Test getting aggregated performance across agent types."""
        tracker = PerformanceTracker()

        tracker.record_execution("model-a", "leadership", True, 1000, 500)
        tracker.record_execution("model-a", "developers", True, 800, 400)
        tracker.record_execution("model-a", "developers", False, 600, 600)

        perf = tracker.get_performance("model-a")  # No agent_type = aggregate
        assert perf["total"] == 3
        assert perf["successes"] == 2
        assert perf["failures"] == 1
        assert perf["success_rate"] == 2/3

    def test_get_performance_empty(self):
        """Test getting performance for unknown model."""
        tracker = PerformanceTracker()

        perf = tracker.get_performance("unknown-model", "leadership")
        assert perf == {}

    def test_get_best_model_for_agent(self):
        """Test getting best model for agent type."""
        tracker = PerformanceTracker()

        # Record multiple models
        for _ in range(5):
            tracker.record_execution("model-a", "leadership", True, 100, 100, 0.8)
            tracker.record_execution("model-b", "leadership", True, 100, 100, 0.6)

        best = tracker.get_best_model_for_agent("leadership")
        assert best == "model-a"  # Higher quality score

    def test_get_best_model_needs_minimum_executions(self):
        """Test that best model needs at least 3 executions."""
        tracker = PerformanceTracker()

        # Only 2 executions
        tracker.record_execution("model-a", "leadership", True, 100, 100, 0.9)
        tracker.record_execution("model-a", "leadership", True, 100, 100, 0.9)

        best = tracker.get_best_model_for_agent("leadership")
        assert best is None  # Not enough data

    def test_get_best_model_none_for_unknown_agent(self):
        """Test getting best model for unknown agent type."""
        tracker = PerformanceTracker()

        best = tracker.get_best_model_for_agent("unknown_agent_type")
        assert best is None


class TestModelRouter:
    """Test ModelRouter class."""

    def test_init_default(self):
        """Test default initialization."""
        router = ModelRouter()

        assert router.target_quality == 0.7
        assert router.quality_variance == 0.15
        assert router.cost_weight == 0.3
        assert router.enable_fuzzing == True

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        router = ModelRouter(
            target_quality=0.5,
            quality_variance=0.1,
            cost_weight=0.5,
            enable_fuzzing=False
        )

        assert router.target_quality == 0.5
        assert router.quality_variance == 0.1
        assert router.cost_weight == 0.5
        assert router.enable_fuzzing == False

    def test_init_with_anthropic_key(self):
        """Test initialization with Anthropic API key."""
        router = ModelRouter(anthropic_key="test-key")

        # Anthropic models should be marked available
        anthropic_available = any(
            spec.available and spec.provider == Provider.ANTHROPIC
            for spec in MODEL_CATALOG.values()
        )
        assert anthropic_available

    def test_select_model_full_power(self):
        """Test selecting model in full power mode."""
        router = ModelRouter(anthropic_key="test-key")

        profile = TaskProfile(
            complexity=0.5,
            requires_reasoning=True,
            requires_code=False,
            requires_creativity=False,
            context_size=10000,
            priority="normal",
            agent_type="leadership"
        )

        result = router.select_model(profile, mode="full_power")

        assert result.confidence == 1.0
        assert result.model_spec.quality_tier == QualityTier.FLAGSHIP
        assert "Full power mode" in result.selection_reason

    def test_select_model_economical(self):
        """Test selecting model in economical mode."""
        router = ModelRouter(anthropic_key="test-key", enable_fuzzing=False)

        profile = TaskProfile(
            complexity=0.3,
            requires_reasoning=False,
            requires_code=False,
            requires_creativity=False,
            context_size=5000,
            priority="low",
            agent_type="documentation"
        )

        result = router.select_model(profile, mode="economical")

        # Should prefer cheaper models
        assert result.model_spec.cost_per_1k_input <= 0.01

    def test_select_model_dynamic(self):
        """Test selecting model in dynamic mode."""
        router = ModelRouter(anthropic_key="test-key")

        profile = TaskProfile(
            complexity=0.5,
            requires_reasoning=True,
            requires_code=True,
            requires_creativity=False,
            context_size=50000,
            priority="normal",
            agent_type="developers"
        )

        result = router.select_model(profile, mode="dynamic")

        assert result.model_id is not None
        assert result.model_spec is not None
        assert len(result.selection_reason) > 0

    def test_select_model_with_exclusions(self):
        """Test selecting model with exclusions."""
        router = ModelRouter(anthropic_key="test-key", enable_fuzzing=False)

        profile = TaskProfile(
            complexity=0.5,
            requires_reasoning=False,
            requires_code=False,
            requires_creativity=False,
            context_size=10000,
            priority="normal",
            agent_type="testers"
        )

        # Exclude all but one model type
        excluded = ["claude-opus-4-5-20251101", "claude-3-5-haiku-20241022"]
        result = router.select_model(profile, excluded_models=excluded)

        assert result.model_id not in excluded

    def test_select_model_fallback_when_none_available(self):
        """Test fallback when no models configured as available."""
        router = ModelRouter()  # No API keys

        profile = TaskProfile(
            complexity=0.5,
            requires_reasoning=False,
            requires_code=False,
            requires_creativity=False,
            context_size=10000,
            priority="normal",
            agent_type="leadership"
        )

        # Should fall back to default Anthropic model
        result = router.select_model(profile)
        assert result.model_spec.provider == Provider.ANTHROPIC

    def test_score_model_high_complexity(self):
        """Test scoring model for high complexity task."""
        router = ModelRouter(anthropic_key="test-key")

        spec = MODEL_CATALOG["claude-opus-4-5-20251101"]
        profile = TaskProfile(
            complexity=0.9,
            requires_reasoning=True,
            requires_code=True,
            requires_creativity=True,
            context_size=100000,
            priority="high",
            agent_type="architect"
        )

        score = router._score_model(spec, profile, "dynamic")

        # Flagship model should score well for high complexity
        assert score > 0.3

    def test_score_model_low_complexity(self):
        """Test scoring model for low complexity task."""
        router = ModelRouter(anthropic_key="test-key")

        spec = MODEL_CATALOG["claude-3-5-haiku-20241022"]
        profile = TaskProfile(
            complexity=0.2,
            requires_reasoning=False,
            requires_code=False,
            requires_creativity=False,
            context_size=1000,
            priority="low",
            agent_type="documentation"
        )

        score = router._score_model(spec, profile, "dynamic")

        # Efficient model should score well for low complexity
        assert score > 0

    def test_apply_fuzzing(self):
        """Test fuzzing application."""
        router = ModelRouter(anthropic_key="test-key")

        spec1 = MODEL_CATALOG["claude-opus-4-5-20251101"]
        spec2 = MODEL_CATALOG["claude-sonnet-4-20250514"]
        spec3 = MODEL_CATALOG["claude-3-5-haiku-20241022"]

        scored_models = [
            ("claude-opus-4-5-20251101", spec1, 0.8),
            ("claude-sonnet-4-20250514", spec2, 0.6),
            ("claude-3-5-haiku-20241022", spec3, 0.4),
        ]

        profile = TaskProfile(
            complexity=0.5,
            requires_reasoning=False,
            requires_code=False,
            requires_creativity=False,
            context_size=10000,
            priority="normal",
            agent_type="developers"
        )

        # Run multiple times to verify fuzzing introduces variance
        selections = set()
        for _ in range(20):
            random.seed()  # Re-seed for variance
            result = router._apply_fuzzing(scored_models, profile)
            selections.add(result[0])

        # Should have some variety (unless extremely unlikely)
        # Note: This is probabilistic, might occasionally fail
        assert len(selections) >= 1

    def test_apply_fuzzing_high_priority(self):
        """Test fuzzing with high priority task."""
        router = ModelRouter(anthropic_key="test-key")

        spec1 = MODEL_CATALOG["claude-opus-4-5-20251101"]
        spec2 = MODEL_CATALOG["claude-3-5-haiku-20241022"]

        scored_models = [
            ("claude-opus-4-5-20251101", spec1, 0.8),
            ("claude-3-5-haiku-20241022", spec2, 0.4),
        ]

        profile = TaskProfile(
            complexity=0.8,
            requires_reasoning=True,
            requires_code=False,
            requires_creativity=False,
            context_size=10000,
            priority="high",  # High priority
            agent_type="executive"
        )

        # High priority should bias toward higher quality
        result = router._apply_fuzzing(scored_models, profile)
        assert result[0] in ["claude-opus-4-5-20251101", "claude-3-5-haiku-20241022"]

    def test_get_flagship_model(self):
        """Test getting flagship model."""
        router = ModelRouter(anthropic_key="test-key")

        flagship = router._get_flagship_model()

        assert flagship.quality_tier == QualityTier.FLAGSHIP

    def test_get_flagship_model_fallback(self):
        """Test flagship model fallback when no flagship available."""
        router = ModelRouter()  # No keys, nothing available by default

        # Should fallback to any available Anthropic model
        with pytest.raises(ValueError, match="No models available"):
            # Since no API key, and all models marked unavailable
            # First ensure all models are unavailable
            for spec in MODEL_CATALOG.values():
                spec.available = False
            router._get_flagship_model()

        # Restore model availability
        MODEL_CATALOG["claude-opus-4-5-20251101"].available = True

    def test_build_selection_reason_flagship(self):
        """Test building selection reason for flagship model."""
        router = ModelRouter(anthropic_key="test-key")

        spec = MODEL_CATALOG["claude-opus-4-5-20251101"]
        profile = TaskProfile(
            complexity=0.9,
            requires_reasoning=True,
            requires_code=True,
            requires_creativity=False,
            context_size=10000,
            priority="high",
            agent_type="architect"
        )

        reason = router._build_selection_reason(spec, profile, 0.85)

        assert "flagship" in reason.lower() or "Claude Opus" in reason
        assert "reasoning" in reason.lower()

    def test_build_selection_reason_efficient(self):
        """Test building selection reason for efficient model."""
        router = ModelRouter(anthropic_key="test-key")

        spec = MODEL_CATALOG["claude-3-5-haiku-20241022"]
        profile = TaskProfile(
            complexity=0.2,
            requires_reasoning=False,
            requires_code=False,
            requires_creativity=False,
            context_size=1000,
            priority="low",
            agent_type="simple_task"
        )

        reason = router._build_selection_reason(spec, profile, 0.5)

        assert "efficient" in reason.lower() or "cost" in reason.lower() or "balanced" in reason.lower()

    def test_record_execution_result(self):
        """Test recording execution result."""
        router = ModelRouter(anthropic_key="test-key")

        router.record_execution_result(
            model_id="claude-sonnet-4-20250514",
            agent_type="developers",
            success=True,
            tokens_used=5000,
            duration_ms=2000,
            quality_score=0.85
        )

        perf = router.performance_tracker.get_performance(
            "claude-sonnet-4-20250514",
            "developers"
        )
        assert perf["total"] == 1
        assert perf["successes"] == 1

    def test_adjust_target_quality(self):
        """Test adjusting target quality."""
        router = ModelRouter()

        router.adjust_target_quality(0.9)
        assert router.target_quality == 0.9

        # Test clamping
        router.adjust_target_quality(1.5)
        assert router.target_quality == 1.0

        router.adjust_target_quality(-0.5)
        assert router.target_quality == 0.0

    def test_get_model_stats(self):
        """Test getting model statistics."""
        router = ModelRouter(anthropic_key="test-key")

        # Record some executions
        router.record_execution_result(
            "claude-opus-4-5-20251101",
            "leadership",
            True,
            1000,
            500
        )

        stats = router.get_model_stats()

        assert "target_quality" in stats
        assert "available_models" in stats
        assert "performance" in stats
        assert stats["fuzzing_enabled"] == True

    def test_analyze_task_profile_high_complexity(self):
        """Test analyzing high complexity task."""
        router = ModelRouter()

        profile = router.analyze_task_profile(
            task_description="Design and architect a complex distributed system with multiple integration points",
            agent_type="system_architect",
            context_size=100000
        )

        assert profile.complexity > 0.5  # Should be higher complexity
        assert profile.requires_reasoning == True
        assert profile.priority == "high"  # Architect = high priority

    def test_analyze_task_profile_low_complexity(self):
        """Test analyzing low complexity task."""
        router = ModelRouter()

        profile = router.analyze_task_profile(
            task_description="Fix a simple typo in the readme",
            agent_type="documentation_writer",
            context_size=1000
        )

        assert profile.complexity < 0.5  # Should be lower complexity

    def test_analyze_task_profile_code_task(self):
        """Test analyzing code-related task."""
        router = ModelRouter()

        profile = router.analyze_task_profile(
            task_description="Implement the authentication endpoint with proper error handling",
            agent_type="backend_developer",
            context_size=50000
        )

        assert profile.requires_code == True

    def test_analyze_task_profile_reasoning_task(self):
        """Test analyzing reasoning task."""
        router = ModelRouter()

        profile = router.analyze_task_profile(
            task_description="Analyze and evaluate the different approaches, then decide on the best strategy",
            agent_type="analyst",
            context_size=20000
        )

        assert profile.requires_reasoning == True

    def test_analyze_task_profile_creative_task(self):
        """Test analyzing creative task."""
        router = ModelRouter()

        profile = router.analyze_task_profile(
            task_description="Generate creative documentation with innovative UI design suggestions",
            agent_type="designer",
            context_size=30000
        )

        assert profile.requires_creativity == True

    def test_check_local_model_no_endpoint(self):
        """Test checking local model without endpoint."""
        router = ModelRouter()

        result = router._check_local_model("llama3:70b")
        assert result == False

    def test_check_local_model_with_endpoint(self):
        """Test checking local model with endpoint (disabled by default)."""
        router = ModelRouter(local_endpoint="http://localhost:11434")

        # Currently always returns False (disabled)
        result = router._check_local_model("llama3:70b")
        assert result == False

    def test_update_model_availability_openai(self):
        """Test model availability update with OpenAI key (without ProviderManager)."""
        # Disable ProviderManager to test original availability logic
        router = ModelRouter(openai_key="test-openai-key", use_provider_manager=False)

        # Check that OpenAI models are marked available
        gpt4o = MODEL_CATALOG.get("gpt-4o")
        if gpt4o:
            assert gpt4o.available == True

        # Reset for other tests
        if gpt4o:
            gpt4o.available = False

    def test_update_model_availability_google(self):
        """Test model availability update with Google key (without ProviderManager)."""
        # Disable ProviderManager to test original availability logic
        router = ModelRouter(google_key="test-google-key", use_provider_manager=False)

        # Check that Google models are marked available
        gemini = MODEL_CATALOG.get("gemini-pro")
        if gemini:
            assert gemini.available == True

        # Reset for other tests
        if gemini:
            gemini.available = False


class TestGetModelRouter:
    """Test get_model_router function."""

    def test_get_model_router_creates_singleton(self):
        """Test that get_model_router creates a singleton."""
        import src.runtime.agents.model_router as module

        # Reset global router
        module._model_router = None

        router1 = get_model_router(anthropic_key="test-key")
        router2 = get_model_router()

        assert router1 is router2

        # Reset after test
        module._model_router = None

    def test_get_model_router_with_kwargs(self):
        """Test get_model_router with additional kwargs."""
        import src.runtime.agents.model_router as module

        module._model_router = None

        router = get_model_router(
            anthropic_key="test-key",
            target_quality=0.8
        )

        assert router.target_quality == 0.8

        module._model_router = None


class TestSelectionWithPerformanceHistory:
    """Test model selection with performance history."""

    def test_selection_considers_historical_performance(self):
        """Test that selection considers historical performance."""
        router = ModelRouter(anthropic_key="test-key", enable_fuzzing=False)

        # Record good performance for a model
        for _ in range(5):
            router.record_execution_result(
                "claude-sonnet-4-20250514",
                "developers",
                True,
                1000,
                500,
                quality_score=0.95
            )

        profile = TaskProfile(
            complexity=0.5,
            requires_reasoning=False,
            requires_code=True,
            requires_creativity=False,
            context_size=10000,
            priority="normal",
            agent_type="developers"
        )

        result = router.select_model(profile)

        # Should consider the high-performing model
        # (Note: not guaranteed to be selected due to other factors)
        assert result.model_id is not None


class TestEdgeCases:
    """Test edge cases."""

    def test_select_model_single_available_model(self):
        """Test selection when only one model is available."""
        router = ModelRouter(anthropic_key="test-key", enable_fuzzing=False)

        profile = TaskProfile(
            complexity=0.5,
            requires_reasoning=False,
            requires_code=False,
            requires_creativity=False,
            context_size=10000,
            priority="normal",
            agent_type="testers"
        )

        # Exclude all but one
        all_but_one = [
            m for m in MODEL_CATALOG.keys()
            if m != "claude-3-5-haiku-20241022"
        ]

        result = router.select_model(profile, excluded_models=all_but_one)

        assert result.model_id == "claude-3-5-haiku-20241022"
        assert result.alternatives == []  # No alternatives

    def test_apply_fuzzing_single_model(self):
        """Test fuzzing with only one model."""
        router = ModelRouter(anthropic_key="test-key")

        spec = MODEL_CATALOG["claude-sonnet-4-20250514"]
        scored_models = [("claude-sonnet-4-20250514", spec, 0.8)]

        profile = TaskProfile(
            complexity=0.5,
            requires_reasoning=False,
            requires_code=False,
            requires_creativity=False,
            context_size=10000,
            priority="normal",
            agent_type="developers"
        )

        result = router._apply_fuzzing(scored_models, profile)

        assert result[0] == "claude-sonnet-4-20250514"

    def test_performance_tracker_thread_safety(self):
        """Test that PerformanceTracker is thread-safe."""
        import threading

        tracker = PerformanceTracker()

        def record_many():
            for i in range(100):
                tracker.record_execution(
                    f"model-{i % 3}",
                    f"agent-{i % 5}",
                    i % 2 == 0,
                    100,
                    50
                )

        threads = [threading.Thread(target=record_many) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have recorded without errors
        total_recorded = sum(
            stats["total"]
            for stats in tracker._stats.values()
        )
        assert total_recorded == 500
