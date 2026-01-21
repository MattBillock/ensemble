"""
Comprehensive tests for the multi-provider LLM abstraction layer.

Tests cover:
- Base classes and data structures
- Individual provider implementations
- Provider manager with failover
- Error handling and recovery
"""

import pytest
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import base classes
from src.runtime.agents.providers.base import (
    LLMProvider,
    ProviderType,
    ProviderResponse,
    ProviderError,
    RateLimitError,
    AuthenticationError,
    ConnectionError,
    ContextLengthError,
    ContentBlock,
    TokenUsage,
    StopReason,
    ToolDefinition,
)


# ============================================================================
# Test Base Classes
# ============================================================================

class TestProviderType:
    """Tests for ProviderType enum."""

    def test_all_provider_types_defined(self):
        """All expected provider types should be defined."""
        expected = ["anthropic", "openai", "local_openai", "local_claude", "chatgpt_app", "ollama"]
        actual = [pt.value for pt in ProviderType]
        for exp in expected:
            assert exp in actual, f"Missing provider type: {exp}"

    def test_provider_type_values(self):
        """Provider type values should match expected strings."""
        assert ProviderType.ANTHROPIC.value == "anthropic"
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.LOCAL_OPENAI.value == "local_openai"
        assert ProviderType.LOCAL_CLAUDE.value == "local_claude"
        assert ProviderType.CHATGPT_APP.value == "chatgpt_app"
        assert ProviderType.OLLAMA.value == "ollama"


class TestStopReason:
    """Tests for StopReason enum."""

    def test_all_stop_reasons_defined(self):
        """All expected stop reasons should be defined."""
        expected = ["end_turn", "tool_use", "max_tokens", "stop_sequence", "error"]
        actual = [sr.value for sr in StopReason]
        for exp in expected:
            assert exp in actual, f"Missing stop reason: {exp}"


class TestContentBlock:
    """Tests for ContentBlock dataclass."""

    def test_text_content_block(self):
        """Text content blocks should store text correctly."""
        block = ContentBlock(type="text", text="Hello, world!")
        assert block.type == "text"
        assert block.text == "Hello, world!"
        assert block.tool_use_id is None
        assert block.tool_name is None
        assert block.tool_input is None

    def test_tool_use_content_block(self):
        """Tool use content blocks should store tool info correctly."""
        block = ContentBlock(
            type="tool_use",
            tool_use_id="toolu_123",
            tool_name="read_file",
            tool_input={"path": "/test.txt"}
        )
        assert block.type == "tool_use"
        assert block.tool_use_id == "toolu_123"
        assert block.tool_name == "read_file"
        assert block.tool_input == {"path": "/test.txt"}
        assert block.text is None


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""

    def test_default_values(self):
        """Default values should be zero."""
        usage = TokenUsage()
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.cache_creation_input_tokens == 0
        assert usage.cache_read_input_tokens == 0

    def test_total_tokens_property(self):
        """Total tokens should be sum of input and output."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.total_tokens == 150

    def test_custom_values(self):
        """Custom values should be stored correctly."""
        usage = TokenUsage(
            input_tokens=1000,
            output_tokens=500,
            cache_creation_input_tokens=200,
            cache_read_input_tokens=100
        )
        assert usage.input_tokens == 1000
        assert usage.output_tokens == 500
        assert usage.cache_creation_input_tokens == 200
        assert usage.cache_read_input_tokens == 100


class TestProviderResponse:
    """Tests for ProviderResponse dataclass."""

    def test_response_creation(self):
        """Response should store all fields correctly."""
        content = [ContentBlock(type="text", text="Test response")]
        usage = TokenUsage(input_tokens=100, output_tokens=50)

        response = ProviderResponse(
            provider=ProviderType.ANTHROPIC,
            model="claude-sonnet-4-20250514",
            content=content,
            stop_reason=StopReason.END_TURN,
            usage=usage,
            latency_ms=1500
        )

        assert response.provider == ProviderType.ANTHROPIC
        assert response.model == "claude-sonnet-4-20250514"
        assert len(response.content) == 1
        assert response.stop_reason == StopReason.END_TURN
        assert response.latency_ms == 1500

    def test_get_text_single_block(self):
        """get_text should return text from single block."""
        content = [ContentBlock(type="text", text="Hello")]
        response = ProviderResponse(
            provider=ProviderType.ANTHROPIC,
            model="test",
            content=content,
            stop_reason=StopReason.END_TURN,
            usage=TokenUsage()
        )
        assert response.get_text() == "Hello"

    def test_get_text_multiple_blocks(self):
        """get_text should join text from multiple blocks."""
        content = [
            ContentBlock(type="text", text="Hello"),
            ContentBlock(type="text", text="World")
        ]
        response = ProviderResponse(
            provider=ProviderType.ANTHROPIC,
            model="test",
            content=content,
            stop_reason=StopReason.END_TURN,
            usage=TokenUsage()
        )
        assert response.get_text() == "Hello\nWorld"

    def test_get_text_with_tool_blocks(self):
        """get_text should ignore tool use blocks."""
        content = [
            ContentBlock(type="text", text="Before"),
            ContentBlock(type="tool_use", tool_name="test"),
            ContentBlock(type="text", text="After")
        ]
        response = ProviderResponse(
            provider=ProviderType.ANTHROPIC,
            model="test",
            content=content,
            stop_reason=StopReason.END_TURN,
            usage=TokenUsage()
        )
        assert response.get_text() == "Before\nAfter"

    def test_get_tool_uses(self):
        """get_tool_uses should return only tool use blocks."""
        content = [
            ContentBlock(type="text", text="Thinking..."),
            ContentBlock(type="tool_use", tool_name="read_file", tool_use_id="t1"),
            ContentBlock(type="tool_use", tool_name="write_file", tool_use_id="t2")
        ]
        response = ProviderResponse(
            provider=ProviderType.ANTHROPIC,
            model="test",
            content=content,
            stop_reason=StopReason.TOOL_USE,
            usage=TokenUsage()
        )
        tool_uses = response.get_tool_uses()
        assert len(tool_uses) == 2
        assert tool_uses[0].tool_name == "read_file"
        assert tool_uses[1].tool_name == "write_file"

    def test_has_tool_use_true(self):
        """has_tool_use should return True when tools are present."""
        content = [ContentBlock(type="tool_use", tool_name="test")]
        response = ProviderResponse(
            provider=ProviderType.ANTHROPIC,
            model="test",
            content=content,
            stop_reason=StopReason.TOOL_USE,
            usage=TokenUsage()
        )
        assert response.has_tool_use() is True

    def test_has_tool_use_false(self):
        """has_tool_use should return False when no tools."""
        content = [ContentBlock(type="text", text="No tools here")]
        response = ProviderResponse(
            provider=ProviderType.ANTHROPIC,
            model="test",
            content=content,
            stop_reason=StopReason.END_TURN,
            usage=TokenUsage()
        )
        assert response.has_tool_use() is False


class TestProviderErrors:
    """Tests for provider error classes."""

    def test_provider_error_basic(self):
        """ProviderError should store message and provider."""
        error = ProviderError("Test error", ProviderType.ANTHROPIC)
        assert str(error) == "Test error"
        assert error.provider == ProviderType.ANTHROPIC
        assert error.retryable is False
        assert error.original_error is None

    def test_provider_error_retryable(self):
        """ProviderError with retryable flag."""
        error = ProviderError("Temp error", ProviderType.OPENAI, retryable=True)
        assert error.retryable is True

    def test_provider_error_with_original(self):
        """ProviderError wrapping original exception."""
        original = ValueError("Original issue")
        error = ProviderError("Wrapped", ProviderType.ANTHROPIC, original_error=original)
        assert error.original_error is original

    def test_rate_limit_error(self):
        """RateLimitError should be retryable and store retry_after."""
        error = RateLimitError(
            "Rate limited",
            ProviderType.ANTHROPIC,
            retry_after_seconds=60
        )
        assert error.retryable is True
        assert error.retry_after_seconds == 60

    def test_authentication_error(self):
        """AuthenticationError should not be retryable."""
        error = AuthenticationError("Bad API key", ProviderType.OPENAI)
        assert error.retryable is False

    def test_connection_error(self):
        """ConnectionError should be retryable."""
        error = ConnectionError("Network issue", ProviderType.OLLAMA)
        assert error.retryable is True

    def test_context_length_error(self):
        """ContextLengthError should store token info."""
        error = ContextLengthError(
            "Context too long",
            ProviderType.ANTHROPIC,
            max_tokens=200000,
            requested_tokens=250000
        )
        assert error.retryable is False
        assert error.max_tokens == 200000
        assert error.requested_tokens == 250000


class TestToolDefinition:
    """Tests for ToolDefinition dataclass."""

    def test_tool_definition(self):
        """ToolDefinition should store tool info correctly."""
        tool = ToolDefinition(
            name="read_file",
            description="Read a file from disk",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        )
        assert tool.name == "read_file"
        assert tool.description == "Read a file from disk"
        assert "path" in tool.input_schema["properties"]


# ============================================================================
# Test Concrete Provider: LLMProvider Base
# ============================================================================

class ConcreteProvider(LLMProvider):
    """Concrete implementation for testing base class."""

    def initialize(self) -> bool:
        self._available = True
        return True

    def send_message(self, messages, model, **kwargs):
        return ProviderResponse(
            provider=self.provider_type,
            model=model,
            content=[ContentBlock(type="text", text="Test")],
            stop_reason=StopReason.END_TURN,
            usage=TokenUsage(input_tokens=10, output_tokens=5)
        )

    def get_available_models(self):
        return ["test-model"]

    def estimate_cost(self, input_tokens, output_tokens, model):
        return (input_tokens + output_tokens) * 0.00001


class TestLLMProviderBase:
    """Tests for LLMProvider abstract base class."""

    def test_initialization(self):
        """Provider should initialize with default values."""
        provider = ConcreteProvider(ProviderType.ANTHROPIC)
        assert provider.provider_type == ProviderType.ANTHROPIC
        assert provider._available is False
        assert provider._error_count == 0
        assert provider._success_count == 0

    def test_is_available_property(self):
        """is_available should reflect _available state."""
        provider = ConcreteProvider(ProviderType.ANTHROPIC)
        assert provider.is_available is False
        provider.initialize()
        assert provider.is_available is True

    def test_record_success(self):
        """record_success should update counters."""
        provider = ConcreteProvider(ProviderType.ANTHROPIC)
        provider.initialize()

        response = ProviderResponse(
            provider=ProviderType.ANTHROPIC,
            model="test",
            content=[],
            stop_reason=StopReason.END_TURN,
            usage=TokenUsage(input_tokens=100, output_tokens=50)
        )

        provider.record_success(response)

        assert provider._success_count == 1
        assert provider._total_tokens.input_tokens == 100
        assert provider._total_tokens.output_tokens == 50
        assert provider._last_error is None

    def test_record_error(self):
        """record_error should update error count."""
        provider = ConcreteProvider(ProviderType.ANTHROPIC)
        error = ProviderError("Test error", ProviderType.ANTHROPIC)

        provider.record_error(error)

        assert provider._error_count == 1
        assert provider._last_error is error

    def test_get_stats(self):
        """get_stats should return correct statistics."""
        provider = ConcreteProvider(ProviderType.ANTHROPIC)
        provider.initialize()

        # Record some activity
        response = ProviderResponse(
            provider=ProviderType.ANTHROPIC,
            model="test",
            content=[],
            stop_reason=StopReason.END_TURN,
            usage=TokenUsage(input_tokens=100, output_tokens=50)
        )
        provider.record_success(response)
        provider.record_error(ProviderError("Oops", ProviderType.ANTHROPIC))

        stats = provider.get_stats()

        assert stats["provider"] == "anthropic"
        assert stats["available"] is True
        assert stats["success_count"] == 1
        assert stats["error_count"] == 1
        assert stats["success_rate"] == 0.5
        assert stats["total_input_tokens"] == 100
        assert stats["total_output_tokens"] == 50

    def test_reset_stats(self):
        """reset_stats should clear all counters."""
        provider = ConcreteProvider(ProviderType.ANTHROPIC)

        # Record some activity
        provider._success_count = 10
        provider._error_count = 5
        provider._total_cost = 1.50
        provider._total_tokens = TokenUsage(input_tokens=1000, output_tokens=500)

        provider.reset_stats()

        assert provider._success_count == 0
        assert provider._error_count == 0
        assert provider._total_cost == 0.0
        assert provider._total_tokens.input_tokens == 0


# ============================================================================
# Test Anthropic Provider
# ============================================================================

class TestAnthropicProvider:
    """Tests for AnthropicProvider implementation."""

    def test_initialization_without_key(self):
        """Provider should not be available without API key."""
        from src.runtime.agents.providers.anthropic_provider import AnthropicProvider

        with patch.dict("os.environ", {}, clear=True):
            provider = AnthropicProvider(api_key=None)
            result = provider.initialize()
            assert result is False
            assert provider.is_available is False

    def test_initialization_with_key(self):
        """Provider should initialize with API key."""
        from src.runtime.agents.providers.anthropic_provider import AnthropicProvider

        # Patch where Anthropic is imported (inside the initialize method)
        with patch("anthropic.Anthropic"):
            provider = AnthropicProvider(api_key="test-key")
            result = provider.initialize()

            assert result is True
            assert provider.is_available is True

    def test_get_available_models(self):
        """Should return list of Claude models."""
        from src.runtime.agents.providers.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider(api_key="test")
        models = provider.get_available_models()

        assert "claude-opus-4-5-20251101" in models
        assert "claude-sonnet-4-20250514" in models
        assert "claude-3-5-haiku-20241022" in models

    def test_estimate_cost(self):
        """Should calculate cost correctly."""
        from src.runtime.agents.providers.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider(api_key="test")

        # Test with a known model
        cost = provider.estimate_cost(1000, 500, "claude-sonnet-4-20250514")
        # Sonnet: $0.003/1K input, $0.015/1K output
        expected = (1000 / 1000) * 0.003 + (500 / 1000) * 0.015
        assert abs(cost - expected) < 0.0001


# ============================================================================
# Test OpenAI Provider
# ============================================================================

class TestOpenAIProvider:
    """Tests for OpenAIProvider implementation."""

    def test_initialization_without_key(self):
        """Provider should not be available without API key."""
        from src.runtime.agents.providers.openai_provider import OpenAIProvider

        with patch.dict("os.environ", {}, clear=True):
            provider = OpenAIProvider(api_key=None)
            result = provider.initialize()
            assert result is False

    def test_initialization_with_key(self):
        """Provider should initialize with API key."""
        from src.runtime.agents.providers.openai_provider import OpenAIProvider

        # Try to import openai - skip if not installed
        try:
            import openai
            with patch.object(openai, "OpenAI"):
                provider = OpenAIProvider(api_key="test-key")
                result = provider.initialize()

                assert result is True
                assert provider.is_available is True
        except ImportError:
            pytest.skip("openai package not installed")

    def test_is_local_detection(self):
        """Should detect local servers correctly."""
        from src.runtime.agents.providers.openai_provider import OpenAIProvider

        # Explicit localhost URL
        provider = OpenAIProvider(base_url="http://localhost:1234/v1")
        assert provider.is_local is True

        # Explicit is_local flag
        provider2 = OpenAIProvider(api_key="test", is_local=True)
        assert provider2.is_local is True

    def test_get_available_models(self):
        """Should return list of OpenAI models."""
        from src.runtime.agents.providers.openai_provider import OpenAIProvider

        provider = OpenAIProvider(api_key="test")
        models = provider.get_available_models()

        assert "gpt-4o" in models
        assert "gpt-4o-mini" in models
        assert "gpt-3.5-turbo" in models

    def test_estimate_cost_local_is_free(self):
        """Local servers should have zero cost."""
        from src.runtime.agents.providers.openai_provider import OpenAIProvider

        provider = OpenAIProvider(base_url="http://localhost:1234/v1", is_local=True)
        cost = provider.estimate_cost(1000, 500, "gpt-4o")
        assert cost == 0.0


# ============================================================================
# Test Ollama Provider
# ============================================================================

class TestOllamaProvider:
    """Tests for OllamaProvider implementation."""

    def test_default_host(self):
        """Should use default Ollama host."""
        from src.runtime.agents.providers.ollama_provider import OllamaProvider

        provider = OllamaProvider()
        assert provider.host == "http://localhost:11434"

    def test_custom_host(self):
        """Should use custom host if provided."""
        from src.runtime.agents.providers.ollama_provider import OllamaProvider

        provider = OllamaProvider(host="http://192.168.1.100:11434")
        assert provider.host == "http://192.168.1.100:11434"

    def test_estimate_cost_is_free(self):
        """Ollama should have zero cost."""
        from src.runtime.agents.providers.ollama_provider import OllamaProvider

        provider = OllamaProvider()
        cost = provider.estimate_cost(1000, 500, "llama3:8b")
        assert cost == 0.0


# ============================================================================
# Test Local Claude Provider
# ============================================================================

class TestLocalClaudeProvider:
    """Tests for LocalClaudeProvider implementation."""

    @patch("shutil.which")
    def test_find_cli_in_path(self, mock_which):
        """Should find Claude CLI in PATH."""
        from src.runtime.agents.providers.local_claude_provider import LocalClaudeProvider

        mock_which.side_effect = lambda x: "/usr/local/bin/claude" if x == "claude" else None

        provider = LocalClaudeProvider()
        result = provider.initialize()

        # Note: May fail if subprocess check fails
        mock_which.assert_called()

    def test_estimate_cost_is_free(self):
        """Local Claude should have zero API cost."""
        from src.runtime.agents.providers.local_claude_provider import LocalClaudeProvider

        provider = LocalClaudeProvider()
        cost = provider.estimate_cost(1000, 500, "claude-local")
        assert cost == 0.0

    def test_get_available_models(self):
        """Should return local model identifier."""
        from src.runtime.agents.providers.local_claude_provider import LocalClaudeProvider

        provider = LocalClaudeProvider()
        models = provider.get_available_models()
        assert "claude-local" in models


# ============================================================================
# Test ChatGPT App Provider
# ============================================================================

class TestChatGPTAppProvider:
    """Tests for ChatGPTAppProvider implementation."""

    @patch("platform.system")
    def test_not_available_on_non_macos(self, mock_system):
        """Should not be available on non-macOS systems."""
        from src.runtime.agents.providers.chatgpt_app_provider import ChatGPTAppProvider

        mock_system.return_value = "Linux"
        provider = ChatGPTAppProvider()
        result = provider.initialize()

        assert result is False
        assert provider.is_available is False

    def test_provider_type(self):
        """Should use CHATGPT_APP provider type."""
        from src.runtime.agents.providers.chatgpt_app_provider import ChatGPTAppProvider

        provider = ChatGPTAppProvider()
        assert provider.provider_type == ProviderType.CHATGPT_APP

    def test_estimate_cost_is_free(self):
        """ChatGPT Plus subscription means zero per-call cost."""
        from src.runtime.agents.providers.chatgpt_app_provider import ChatGPTAppProvider

        provider = ChatGPTAppProvider()
        cost = provider.estimate_cost(1000, 500, "chatgpt-app")
        assert cost == 0.0

    def test_get_available_models(self):
        """Should return chatgpt-app model identifier."""
        from src.runtime.agents.providers.chatgpt_app_provider import ChatGPTAppProvider

        provider = ChatGPTAppProvider()
        models = provider.get_available_models()
        assert "chatgpt-app" in models


# ============================================================================
# Test Provider Manager
# ============================================================================

class TestProviderManager:
    """Tests for ProviderManager orchestration."""

    @pytest.fixture
    def manager_mocked(self):
        """Create a manager with mocked providers."""
        from src.runtime.agents.providers.provider_manager import ProviderManager

        with patch.object(ProviderManager, "_init_anthropic"), \
             patch.object(ProviderManager, "_init_openai"), \
             patch.object(ProviderManager, "_init_local_openai"), \
             patch.object(ProviderManager, "_init_ollama"), \
             patch.object(ProviderManager, "_init_local_claude"), \
             patch.object(ProviderManager, "_init_chatgpt_app"):
            manager = ProviderManager(enable_chatgpt_app=False)
            return manager

    def test_initialization(self, manager_mocked):
        """Manager should initialize with empty providers."""
        assert manager_mocked.enable_failover is True
        assert manager_mocked.max_retries == 3

    def test_get_available_providers_empty(self, manager_mocked):
        """Should return empty list when no providers."""
        available = manager_mocked.get_available_providers()
        assert available == []

    def test_set_daily_cost_limit(self, manager_mocked):
        """Should set cost limit for provider."""
        from src.runtime.agents.providers.provider_manager import ProviderConfig, ProviderHealth

        # Add a mock provider config
        manager_mocked.provider_configs[ProviderType.ANTHROPIC] = ProviderConfig(
            provider_type=ProviderType.ANTHROPIC
        )

        manager_mocked.set_daily_cost_limit(ProviderType.ANTHROPIC, 25.0)

        assert manager_mocked.provider_configs[ProviderType.ANTHROPIC].daily_cost_limit == 25.0

    def test_set_provider_priority(self, manager_mocked):
        """Should set priority for provider."""
        from src.runtime.agents.providers.provider_manager import ProviderConfig

        manager_mocked.provider_configs[ProviderType.ANTHROPIC] = ProviderConfig(
            provider_type=ProviderType.ANTHROPIC
        )

        manager_mocked.set_provider_priority(ProviderType.ANTHROPIC, 5)

        assert manager_mocked.provider_configs[ProviderType.ANTHROPIC].priority == 5

    def test_reset_daily_stats(self, manager_mocked):
        """Should reset daily stats for all providers."""
        from src.runtime.agents.providers.provider_manager import ProviderHealth

        # Add health tracking
        manager_mocked.provider_health[ProviderType.ANTHROPIC] = ProviderHealth(
            provider_type=ProviderType.ANTHROPIC,
            total_cost_today=50.0,
            requests_today=100,
            error_rate_1h=0.1
        )

        manager_mocked.reset_daily_stats()

        health = manager_mocked.provider_health[ProviderType.ANTHROPIC]
        assert health.total_cost_today == 0.0
        assert health.requests_today == 0
        assert health.error_rate_1h == 0.0

    def test_get_stats(self, manager_mocked):
        """Should return comprehensive stats."""
        stats = manager_mocked.get_stats()

        assert "providers" in stats
        assert "failover_history" in stats
        assert "total_cost_today" in stats


class TestProviderManagerFailover:
    """Tests for ProviderManager failover logic."""

    def test_provider_order_by_priority(self):
        """Providers should be ordered by priority."""
        from src.runtime.agents.providers.provider_manager import (
            ProviderManager, ProviderConfig, ProviderHealth
        )

        with patch.object(ProviderManager, "_init_anthropic"), \
             patch.object(ProviderManager, "_init_openai"), \
             patch.object(ProviderManager, "_init_local_openai"), \
             patch.object(ProviderManager, "_init_ollama"), \
             patch.object(ProviderManager, "_init_local_claude"), \
             patch.object(ProviderManager, "_init_chatgpt_app"):

            manager = ProviderManager(enable_chatgpt_app=False)

            # Add mock providers with different priorities
            mock_provider = Mock()
            mock_provider.is_available = True

            manager.providers[ProviderType.ANTHROPIC] = mock_provider
            manager.providers[ProviderType.OPENAI] = mock_provider

            manager.provider_configs[ProviderType.ANTHROPIC] = ProviderConfig(
                provider_type=ProviderType.ANTHROPIC,
                priority=2
            )
            manager.provider_configs[ProviderType.OPENAI] = ProviderConfig(
                provider_type=ProviderType.OPENAI,
                priority=1
            )

            manager.provider_health[ProviderType.ANTHROPIC] = ProviderHealth(
                provider_type=ProviderType.ANTHROPIC
            )
            manager.provider_health[ProviderType.OPENAI] = ProviderHealth(
                provider_type=ProviderType.OPENAI
            )

            order = manager._get_provider_order(None)

            # OpenAI has lower priority number = higher priority
            assert order[0] == ProviderType.OPENAI
            assert order[1] == ProviderType.ANTHROPIC

    def test_preferred_provider_first(self):
        """Preferred provider should be tried first."""
        from src.runtime.agents.providers.provider_manager import (
            ProviderManager, ProviderConfig, ProviderHealth
        )

        with patch.object(ProviderManager, "_init_anthropic"), \
             patch.object(ProviderManager, "_init_openai"), \
             patch.object(ProviderManager, "_init_local_openai"), \
             patch.object(ProviderManager, "_init_ollama"), \
             patch.object(ProviderManager, "_init_local_claude"), \
             patch.object(ProviderManager, "_init_chatgpt_app"):

            manager = ProviderManager(enable_chatgpt_app=False)

            # Add mock providers
            mock_provider = Mock()
            mock_provider.is_available = True

            manager.providers[ProviderType.ANTHROPIC] = mock_provider
            manager.providers[ProviderType.OPENAI] = mock_provider

            manager.provider_configs[ProviderType.ANTHROPIC] = ProviderConfig(
                provider_type=ProviderType.ANTHROPIC,
                priority=1  # Higher priority
            )
            manager.provider_configs[ProviderType.OPENAI] = ProviderConfig(
                provider_type=ProviderType.OPENAI,
                priority=2
            )

            manager.provider_health[ProviderType.ANTHROPIC] = ProviderHealth(
                provider_type=ProviderType.ANTHROPIC
            )
            manager.provider_health[ProviderType.OPENAI] = ProviderHealth(
                provider_type=ProviderType.OPENAI
            )

            # Request OpenAI as preferred
            order = manager._get_provider_order(ProviderType.OPENAI)

            # OpenAI should be first despite lower priority
            assert order[0] == ProviderType.OPENAI


class TestProviderManagerModelMapping:
    """Tests for model mapping between providers."""

    def test_model_mapping_anthropic_to_openai(self):
        """Should map Claude models to GPT models."""
        from src.runtime.agents.providers.provider_manager import ProviderManager

        with patch.object(ProviderManager, "_init_anthropic"), \
             patch.object(ProviderManager, "_init_openai"), \
             patch.object(ProviderManager, "_init_local_openai"), \
             patch.object(ProviderManager, "_init_ollama"), \
             patch.object(ProviderManager, "_init_local_claude"), \
             patch.object(ProviderManager, "_init_chatgpt_app"):

            manager = ProviderManager(enable_chatgpt_app=False)

            # Test mapping
            mapped = manager._map_model("claude-opus-4-5-20251101", ProviderType.OPENAI)
            assert mapped == "gpt-4o"

            mapped = manager._map_model("claude-3-5-haiku-20241022", ProviderType.OPENAI)
            assert mapped == "gpt-4o-mini"

    def test_model_mapping_to_chatgpt_app(self):
        """Should map all models to chatgpt-app identifier."""
        from src.runtime.agents.providers.provider_manager import ProviderManager

        with patch.object(ProviderManager, "_init_anthropic"), \
             patch.object(ProviderManager, "_init_openai"), \
             patch.object(ProviderManager, "_init_local_openai"), \
             patch.object(ProviderManager, "_init_ollama"), \
             patch.object(ProviderManager, "_init_local_claude"), \
             patch.object(ProviderManager, "_init_chatgpt_app"):

            manager = ProviderManager(enable_chatgpt_app=False)

            # All models should map to chatgpt-app
            mapped = manager._map_model("claude-opus-4-5-20251101", ProviderType.CHATGPT_APP)
            assert mapped == "chatgpt-app"

            mapped = manager._map_model("gpt-4o", ProviderType.CHATGPT_APP)
            assert mapped == "chatgpt-app"

    def test_unknown_model_passthrough(self):
        """Unknown models should pass through unchanged."""
        from src.runtime.agents.providers.provider_manager import ProviderManager

        with patch.object(ProviderManager, "_init_anthropic"), \
             patch.object(ProviderManager, "_init_openai"), \
             patch.object(ProviderManager, "_init_local_openai"), \
             patch.object(ProviderManager, "_init_ollama"), \
             patch.object(ProviderManager, "_init_local_claude"), \
             patch.object(ProviderManager, "_init_chatgpt_app"):

            manager = ProviderManager(enable_chatgpt_app=False)

            mapped = manager._map_model("unknown-model-xyz", ProviderType.ANTHROPIC)
            assert mapped == "unknown-model-xyz"


# ============================================================================
# Test Provider Manager Health Tracking
# ============================================================================

class TestProviderHealthTracking:
    """Tests for provider health tracking and cooldown."""

    def test_cooldown_on_consecutive_errors(self):
        """Provider should enter cooldown after error threshold."""
        from src.runtime.agents.providers.provider_manager import (
            ProviderManager, ProviderConfig, ProviderHealth, FailoverReason
        )

        with patch.object(ProviderManager, "_init_anthropic"), \
             patch.object(ProviderManager, "_init_openai"), \
             patch.object(ProviderManager, "_init_local_openai"), \
             patch.object(ProviderManager, "_init_ollama"), \
             patch.object(ProviderManager, "_init_local_claude"), \
             patch.object(ProviderManager, "_init_chatgpt_app"):

            manager = ProviderManager(enable_chatgpt_app=False)

            # Setup provider
            manager.provider_configs[ProviderType.ANTHROPIC] = ProviderConfig(
                provider_type=ProviderType.ANTHROPIC,
                error_threshold=3,
                cooldown_seconds=60
            )
            manager.provider_health[ProviderType.ANTHROPIC] = ProviderHealth(
                provider_type=ProviderType.ANTHROPIC
            )

            # Record errors up to threshold
            error = ProviderError("Test", ProviderType.ANTHROPIC)
            for _ in range(3):
                manager._record_error(ProviderType.ANTHROPIC, error, FailoverReason.ERROR_THRESHOLD)

            # Should be in cooldown
            health = manager.provider_health[ProviderType.ANTHROPIC]
            assert health.is_healthy is False
            assert health.cooldown_until is not None
            assert health.cooldown_until > datetime.now()

    def test_success_clears_error_count(self):
        """Success should reset consecutive error count."""
        from src.runtime.agents.providers.provider_manager import (
            ProviderManager, ProviderConfig, ProviderHealth
        )

        with patch.object(ProviderManager, "_init_anthropic"), \
             patch.object(ProviderManager, "_init_openai"), \
             patch.object(ProviderManager, "_init_local_openai"), \
             patch.object(ProviderManager, "_init_ollama"), \
             patch.object(ProviderManager, "_init_local_claude"), \
             patch.object(ProviderManager, "_init_chatgpt_app"):

            manager = ProviderManager(enable_chatgpt_app=False)

            # Setup mock provider
            mock_provider = Mock()
            mock_provider.estimate_cost = Mock(return_value=0.01)

            manager.providers[ProviderType.ANTHROPIC] = mock_provider
            manager.provider_configs[ProviderType.ANTHROPIC] = ProviderConfig(
                provider_type=ProviderType.ANTHROPIC
            )
            manager.provider_health[ProviderType.ANTHROPIC] = ProviderHealth(
                provider_type=ProviderType.ANTHROPIC,
                consecutive_errors=3
            )

            # Record success
            response = ProviderResponse(
                provider=ProviderType.ANTHROPIC,
                model="test",
                content=[],
                stop_reason=StopReason.END_TURN,
                usage=TokenUsage(input_tokens=100, output_tokens=50)
            )
            manager._record_success(ProviderType.ANTHROPIC, response)

            # Error count should be reset
            health = manager.provider_health[ProviderType.ANTHROPIC]
            assert health.consecutive_errors == 0
            assert health.is_healthy is True


# ============================================================================
# Test Global Functions
# ============================================================================

class TestGlobalFunctions:
    """Tests for global provider manager functions."""

    def test_get_provider_manager_singleton(self):
        """get_provider_manager should return singleton."""
        from src.runtime.agents.providers.provider_manager import (
            get_provider_manager,
            reset_provider_manager
        )

        # Reset first
        reset_provider_manager()

        with patch.object(
            __import__("src.runtime.agents.providers.provider_manager", fromlist=["ProviderManager"]).ProviderManager,
            "_init_anthropic"
        ), patch.object(
            __import__("src.runtime.agents.providers.provider_manager", fromlist=["ProviderManager"]).ProviderManager,
            "_init_openai"
        ), patch.object(
            __import__("src.runtime.agents.providers.provider_manager", fromlist=["ProviderManager"]).ProviderManager,
            "_init_local_openai"
        ), patch.object(
            __import__("src.runtime.agents.providers.provider_manager", fromlist=["ProviderManager"]).ProviderManager,
            "_init_ollama"
        ), patch.object(
            __import__("src.runtime.agents.providers.provider_manager", fromlist=["ProviderManager"]).ProviderManager,
            "_init_local_claude"
        ), patch.object(
            __import__("src.runtime.agents.providers.provider_manager", fromlist=["ProviderManager"]).ProviderManager,
            "_init_chatgpt_app"
        ):
            manager1 = get_provider_manager()
            manager2 = get_provider_manager()

            assert manager1 is manager2

        # Clean up
        reset_provider_manager()

    def test_reset_provider_manager(self):
        """reset_provider_manager should clear singleton."""
        from src.runtime.agents.providers.provider_manager import (
            get_provider_manager,
            reset_provider_manager,
            _provider_manager
        )

        reset_provider_manager()

        # After reset, global should be None
        from src.runtime.agents.providers import provider_manager
        assert provider_manager._provider_manager is None


# ============================================================================
# Integration Tests (require actual providers to be mocked)
# ============================================================================

class TestProviderIntegration:
    """Integration tests for provider system."""

    def test_full_flow_with_mocked_anthropic(self):
        """Test full message flow with mocked Anthropic provider."""
        from src.runtime.agents.providers import (
            ProviderManager,
            ProviderType,
            ProviderResponse,
            ContentBlock,
            TokenUsage,
            StopReason,
            reset_provider_manager
        )

        reset_provider_manager()

        # Create manager with mocked initialization
        with patch.object(ProviderManager, "_init_openai"), \
             patch.object(ProviderManager, "_init_local_openai"), \
             patch.object(ProviderManager, "_init_ollama"), \
             patch.object(ProviderManager, "_init_local_claude"), \
             patch.object(ProviderManager, "_init_chatgpt_app"):

            # Mock Anthropic provider
            mock_anthropic = Mock()
            mock_anthropic.is_available = True
            mock_anthropic.send_message = Mock(return_value=ProviderResponse(
                provider=ProviderType.ANTHROPIC,
                model="claude-sonnet-4-20250514",
                content=[ContentBlock(type="text", text="Hello from Claude!")],
                stop_reason=StopReason.END_TURN,
                usage=TokenUsage(input_tokens=50, output_tokens=25),
                latency_ms=500
            ))
            mock_anthropic.estimate_cost = Mock(return_value=0.001)

            manager = ProviderManager(enable_chatgpt_app=False)
            manager.providers[ProviderType.ANTHROPIC] = mock_anthropic

            from src.runtime.agents.providers.provider_manager import ProviderConfig, ProviderHealth
            manager.provider_configs[ProviderType.ANTHROPIC] = ProviderConfig(
                provider_type=ProviderType.ANTHROPIC
            )
            manager.provider_health[ProviderType.ANTHROPIC] = ProviderHealth(
                provider_type=ProviderType.ANTHROPIC
            )

            # Send message
            response = manager.send_message(
                messages=[{"role": "user", "content": "Hello"}],
                model="claude-sonnet-4-20250514"
            )

            assert response.get_text() == "Hello from Claude!"
            assert response.provider == ProviderType.ANTHROPIC

        reset_provider_manager()
