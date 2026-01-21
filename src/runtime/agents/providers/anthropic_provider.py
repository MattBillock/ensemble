"""
Anthropic API provider implementation.

Wraps the Anthropic Python SDK for Claude models.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

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

logger = logging.getLogger(__name__)

# Model pricing per 1K tokens (as of 2025)
ANTHROPIC_PRICING = {
    "claude-opus-4-5-20251101": {"input": 0.015, "output": 0.075},
    "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
    "claude-sonnet-4-5-20250929": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku-20241022": {"input": 0.0008, "output": 0.004},
    # Fallback for unknown models
    "default": {"input": 0.003, "output": 0.015},
}


class AnthropicProvider(LLMProvider):
    """
    Anthropic API provider for Claude models.

    Uses the official Anthropic Python SDK.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.
        """
        super().__init__(ProviderType.ANTHROPIC)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = None

    def initialize(self) -> bool:
        """Initialize the Anthropic client and check availability."""
        if not self.api_key:
            logger.warning("Anthropic API key not configured")
            self._available = False
            return False

        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            # Test the connection with a minimal request
            # Note: We don't actually make a test call to avoid costs
            self._available = True
            logger.info("Anthropic provider initialized successfully")
            return True
        except ImportError:
            logger.error("anthropic package not installed")
            self._available = False
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic provider: {e}")
            self._available = False
            return False

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
        """Send a message to Claude via Anthropic API."""
        if not self._available or not self.client:
            raise ProviderError(
                "Anthropic provider not available",
                ProviderType.ANTHROPIC,
                retryable=False
            )

        start_time = time.time()

        try:
            # Build API kwargs
            api_kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages,
            }

            if system_prompt:
                api_kwargs["system"] = system_prompt

            if temperature != 0.7:  # Only set if non-default
                api_kwargs["temperature"] = temperature

            if tools:
                api_kwargs["tools"] = self._format_tools(tools)

            # Make API call
            response = self.client.messages.create(**api_kwargs)

            latency_ms = int((time.time() - start_time) * 1000)

            # Convert to unified response
            provider_response = self._convert_response(response, model, latency_ms)
            self.record_success(provider_response)

            return provider_response

        except Exception as e:
            error = self._convert_error(e)
            self.record_error(error)
            raise error

    def _format_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Convert tool definitions to Anthropic format."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for tool in tools
        ]

    def _convert_response(
        self,
        response: Any,
        model: str,
        latency_ms: int
    ) -> ProviderResponse:
        """Convert Anthropic response to unified format."""
        # Extract content blocks
        content_blocks = []
        for block in response.content:
            if hasattr(block, 'type'):
                if block.type == "text":
                    content_blocks.append(ContentBlock(
                        type="text",
                        text=block.text
                    ))
                elif block.type == "tool_use":
                    content_blocks.append(ContentBlock(
                        type="tool_use",
                        tool_use_id=block.id,
                        tool_name=block.name,
                        tool_input=block.input
                    ))

        # Map stop reason
        stop_reason_map = {
            "end_turn": StopReason.END_TURN,
            "tool_use": StopReason.TOOL_USE,
            "max_tokens": StopReason.MAX_TOKENS,
            "stop_sequence": StopReason.STOP_SEQUENCE,
        }
        stop_reason = stop_reason_map.get(response.stop_reason, StopReason.END_TURN)

        # Extract usage
        usage = TokenUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cache_creation_input_tokens=getattr(response.usage, 'cache_creation_input_tokens', 0),
            cache_read_input_tokens=getattr(response.usage, 'cache_read_input_tokens', 0),
        )

        return ProviderResponse(
            provider=ProviderType.ANTHROPIC,
            model=model,
            content=content_blocks,
            stop_reason=stop_reason,
            usage=usage,
            raw_response=response,
            latency_ms=latency_ms
        )

    def _convert_error(self, error: Exception) -> ProviderError:
        """Convert Anthropic SDK errors to unified errors."""
        from anthropic import (
            APIError,
            APIConnectionError as AnthropicConnectionError,
            RateLimitError as AnthropicRateLimitError,
            AuthenticationError as AnthropicAuthError,
        )

        error_str = str(error)

        if isinstance(error, AnthropicRateLimitError):
            # Try to extract retry-after from headers
            retry_after = None
            if hasattr(error, 'response') and error.response:
                retry_after = error.response.headers.get('retry-after')
                if retry_after:
                    try:
                        retry_after = int(retry_after)
                    except ValueError:
                        retry_after = None

            return RateLimitError(
                f"Anthropic rate limit exceeded: {error_str}",
                ProviderType.ANTHROPIC,
                retry_after_seconds=retry_after,
                original_error=error
            )

        if isinstance(error, AnthropicAuthError):
            return AuthenticationError(
                f"Anthropic authentication failed: {error_str}",
                ProviderType.ANTHROPIC,
                original_error=error
            )

        if isinstance(error, AnthropicConnectionError):
            return ConnectionError(
                f"Anthropic connection error: {error_str}",
                ProviderType.ANTHROPIC,
                original_error=error
            )

        if isinstance(error, APIError):
            # Check for context length errors
            if "context_length" in error_str.lower() or "too long" in error_str.lower():
                return ContextLengthError(
                    f"Context length exceeded: {error_str}",
                    ProviderType.ANTHROPIC,
                    max_tokens=0,  # Unknown from error
                    requested_tokens=0,
                    original_error=error
                )

            # Generic API error
            return ProviderError(
                f"Anthropic API error: {error_str}",
                ProviderType.ANTHROPIC,
                retryable=True,
                original_error=error
            )

        # Unknown error
        return ProviderError(
            f"Unexpected Anthropic error: {error_str}",
            ProviderType.ANTHROPIC,
            retryable=False,
            original_error=error
        )

    def get_available_models(self) -> List[str]:
        """Get list of available Claude models."""
        return [
            "claude-opus-4-5-20251101",
            "claude-sonnet-4-20250514",
            "claude-sonnet-4-5-20250929",
            "claude-3-5-haiku-20241022",
        ]

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Estimate cost for Anthropic API call."""
        pricing = ANTHROPIC_PRICING.get(model, ANTHROPIC_PRICING["default"])
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost
