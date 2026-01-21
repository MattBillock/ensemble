"""
Multi-provider LLM abstraction layer.

Provides a unified interface for interacting with different LLM providers:
- Anthropic API (Claude models)
- OpenAI API (GPT models)
- Local OpenAI-compatible (LM Studio, LocalAI, vLLM, text-generation-webui)
- Local Claude (Claude Code CLI)
- Local LLMs (Ollama/local inference)
- ChatGPT macOS App (desktop app automation via AppleScript)
"""

from .base import (
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
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider
from .local_claude_provider import LocalClaudeProvider
from .ollama_provider import OllamaProvider
from .chatgpt_app_provider import ChatGPTAppProvider
from .provider_manager import (
    ProviderManager,
    get_provider_manager,
    reset_provider_manager,
    ProviderHealth,
    ProviderConfig,
    FailoverReason,
    FailoverEvent,
)

__all__ = [
    # Base classes and types
    "LLMProvider",
    "ProviderType",
    "ProviderResponse",
    "ProviderError",
    "RateLimitError",
    "AuthenticationError",
    "ConnectionError",
    "ContextLengthError",
    "ContentBlock",
    "TokenUsage",
    "StopReason",
    "ToolDefinition",
    # Providers
    "AnthropicProvider",
    "OpenAIProvider",
    "LocalClaudeProvider",
    "OllamaProvider",
    "ChatGPTAppProvider",
    # Manager and config
    "ProviderManager",
    "get_provider_manager",
    "reset_provider_manager",
    "ProviderHealth",
    "ProviderConfig",
    "FailoverReason",
    "FailoverEvent",
]
