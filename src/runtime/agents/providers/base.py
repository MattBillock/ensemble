"""
Base classes for LLM provider abstraction.

Defines the interface that all providers must implement and common
data structures for responses and errors.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Types of LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    LOCAL_OPENAI = "local_openai"  # LM Studio, LocalAI, vLLM, etc.
    LOCAL_CLAUDE = "local_claude"
    CHATGPT_APP = "chatgpt_app"    # ChatGPT macOS desktop app
    OLLAMA = "ollama"


class StopReason(Enum):
    """Reasons for generation completion."""
    END_TURN = "end_turn"
    TOOL_USE = "tool_use"
    MAX_TOKENS = "max_tokens"
    STOP_SEQUENCE = "stop_sequence"
    ERROR = "error"


@dataclass
class ContentBlock:
    """A block of content in a response."""
    type: str  # "text" or "tool_use"
    text: Optional[str] = None
    # Tool use fields
    tool_use_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None


@dataclass
class TokenUsage:
    """Token usage statistics."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class ProviderResponse:
    """
    Unified response from any LLM provider.

    Normalizes responses from different providers into a common format.
    """
    provider: ProviderType
    model: str
    content: List[ContentBlock]
    stop_reason: StopReason
    usage: TokenUsage
    raw_response: Any = None  # Original provider response
    latency_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_text(self) -> str:
        """Extract text content from response."""
        texts = []
        for block in self.content:
            if block.type == "text" and block.text:
                texts.append(block.text)
        return "\n".join(texts)

    def get_tool_uses(self) -> List[ContentBlock]:
        """Extract tool use blocks from response."""
        return [b for b in self.content if b.type == "tool_use"]

    def has_tool_use(self) -> bool:
        """Check if response contains tool use."""
        return self.stop_reason == StopReason.TOOL_USE or len(self.get_tool_uses()) > 0


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(
        self,
        message: str,
        provider: ProviderType,
        retryable: bool = False,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.retryable = retryable
        self.original_error = original_error


class RateLimitError(ProviderError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str,
        provider: ProviderType,
        retry_after_seconds: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, provider, retryable=True, original_error=original_error)
        self.retry_after_seconds = retry_after_seconds


class AuthenticationError(ProviderError):
    """Authentication failed (invalid API key, etc.)."""

    def __init__(self, message: str, provider: ProviderType, original_error: Optional[Exception] = None):
        super().__init__(message, provider, retryable=False, original_error=original_error)


class ConnectionError(ProviderError):
    """Connection to provider failed."""

    def __init__(self, message: str, provider: ProviderType, original_error: Optional[Exception] = None):
        super().__init__(message, provider, retryable=True, original_error=original_error)


class ContextLengthError(ProviderError):
    """Context length exceeded."""

    def __init__(
        self,
        message: str,
        provider: ProviderType,
        max_tokens: int,
        requested_tokens: int,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message, provider, retryable=False, original_error=original_error)
        self.max_tokens = max_tokens
        self.requested_tokens = requested_tokens


@dataclass
class ToolDefinition:
    """Definition of a tool for the LLM."""
    name: str
    description: str
    input_schema: Dict[str, Any]


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement this interface to be used with the
    multi-provider system.
    """

    def __init__(self, provider_type: ProviderType):
        self.provider_type = provider_type
        self._available = False
        self._last_error: Optional[ProviderError] = None
        self._error_count = 0
        self._success_count = 0
        self._total_cost = 0.0
        self._total_tokens = TokenUsage()

    @property
    def is_available(self) -> bool:
        """Check if provider is available for use."""
        return self._available

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the provider and check availability.

        Returns:
            True if provider is available, False otherwise.
        """
        pass

    @abstractmethod
    def send_message(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[ToolDefinition]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> ProviderResponse:
        """
        Send a message to the LLM and get a response.

        Args:
            messages: List of message dicts with "role" and "content"
            model: Model identifier
            system_prompt: Optional system prompt
            tools: Optional list of tool definitions
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            **kwargs: Provider-specific options

        Returns:
            ProviderResponse with normalized response data

        Raises:
            ProviderError: On any error
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models from this provider."""
        pass

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """
        Estimate cost for given token usage.

        Returns:
            Cost in USD
        """
        pass

    def record_success(self, response: ProviderResponse):
        """Record a successful API call."""
        self._success_count += 1
        self._total_tokens.input_tokens += response.usage.input_tokens
        self._total_tokens.output_tokens += response.usage.output_tokens
        self._total_cost += self.estimate_cost(
            response.usage.input_tokens,
            response.usage.output_tokens,
            response.model
        )
        self._last_error = None

    def record_error(self, error: ProviderError):
        """Record a failed API call."""
        self._error_count += 1
        self._last_error = error

    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics."""
        total_calls = self._success_count + self._error_count
        return {
            "provider": self.provider_type.value,
            "available": self._available,
            "success_count": self._success_count,
            "error_count": self._error_count,
            "success_rate": self._success_count / total_calls if total_calls > 0 else 0,
            "total_cost": self._total_cost,
            "total_input_tokens": self._total_tokens.input_tokens,
            "total_output_tokens": self._total_tokens.output_tokens,
            "last_error": str(self._last_error) if self._last_error else None
        }

    def reset_stats(self):
        """Reset provider statistics."""
        self._error_count = 0
        self._success_count = 0
        self._total_cost = 0.0
        self._total_tokens = TokenUsage()
        self._last_error = None
