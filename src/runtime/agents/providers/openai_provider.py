"""
OpenAI API provider implementation.

Wraps the OpenAI Python SDK for GPT models.
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
OPENAI_PRICING = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "o1": {"input": 0.015, "output": 0.06},
    "o1-mini": {"input": 0.003, "output": 0.012},
    # Fallback for unknown models
    "default": {"input": 0.01, "output": 0.03},
}


class OpenAIProvider(LLMProvider):
    """
    OpenAI API provider for GPT models.

    Uses the official OpenAI Python SDK. Can also connect to OpenAI-compatible
    local servers (LM Studio, LocalAI, text-generation-webui, vLLM) by setting
    a custom base_url.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        organization: Optional[str] = None,
        base_url: Optional[str] = None,
        is_local: bool = False
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key. If not provided, uses OPENAI_API_KEY env var.
                    For local servers, this may be any string (often "not-needed").
            organization: Optional organization ID.
            base_url: Custom base URL for OpenAI-compatible servers (e.g.,
                     "http://localhost:1234/v1" for LM Studio).
            is_local: Set True if connecting to a local server (affects cost estimation).
        """
        super().__init__(ProviderType.OPENAI)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.organization = organization or os.environ.get("OPENAI_ORG_ID")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL")
        self.is_local = is_local or (self.base_url is not None and "localhost" in self.base_url)
        self.client = None

    def initialize(self) -> bool:
        """Initialize the OpenAI client and check availability."""
        # For local servers, API key might not be required
        if not self.api_key and not self.base_url:
            logger.warning("OpenAI API key not configured and no local server specified")
            self._available = False
            return False

        try:
            from openai import OpenAI
            client_kwargs = {"api_key": self.api_key or "not-needed"}

            if self.organization:
                client_kwargs["organization"] = self.organization

            if self.base_url:
                client_kwargs["base_url"] = self.base_url
                logger.info(f"Using custom OpenAI-compatible server: {self.base_url}")

            self.client = OpenAI(**client_kwargs)
            self._available = True

            if self.is_local:
                logger.info(f"OpenAI-compatible local provider initialized: {self.base_url}")
            else:
                logger.info("OpenAI provider initialized successfully")
            return True
        except ImportError:
            logger.warning("openai package not installed - OpenAI provider unavailable")
            self._available = False
            return False
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
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
        """Send a message to GPT via OpenAI API."""
        if not self._available or not self.client:
            raise ProviderError(
                "OpenAI provider not available",
                ProviderType.OPENAI,
                retryable=False
            )

        start_time = time.time()

        try:
            # Convert messages to OpenAI format
            openai_messages = self._convert_messages(messages, system_prompt)

            # Build API kwargs
            api_kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": openai_messages,
                "temperature": temperature,
            }

            if tools:
                api_kwargs["tools"] = self._format_tools(tools)
                api_kwargs["tool_choice"] = "auto"

            # Make API call
            response = self.client.chat.completions.create(**api_kwargs)

            latency_ms = int((time.time() - start_time) * 1000)

            # Convert to unified response
            provider_response = self._convert_response(response, model, latency_ms)
            self.record_success(provider_response)

            return provider_response

        except Exception as e:
            error = self._convert_error(e)
            self.record_error(error)
            raise error

    def _convert_messages(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Convert messages to OpenAI format."""
        openai_messages = []

        # Add system message first
        if system_prompt:
            openai_messages.append({
                "role": "system",
                "content": system_prompt
            })

        # Convert each message
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Handle tool results (OpenAI uses 'tool' role)
            if role == "user" and isinstance(content, list):
                # Check if this is a tool result message
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        openai_messages.append({
                            "role": "tool",
                            "tool_call_id": item.get("tool_use_id", ""),
                            "content": str(item.get("content", ""))
                        })
                continue

            # Handle assistant messages with tool calls
            if role == "assistant" and isinstance(content, list):
                tool_calls = []
                text_content = ""
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "tool_use":
                            import json
                            tool_calls.append({
                                "id": item.get("id", ""),
                                "type": "function",
                                "function": {
                                    "name": item.get("name", ""),
                                    "arguments": json.dumps(item.get("input", {}))
                                }
                            })
                        elif item.get("type") == "text":
                            text_content = item.get("text", "")

                assistant_msg = {"role": "assistant"}
                if text_content:
                    assistant_msg["content"] = text_content
                if tool_calls:
                    assistant_msg["tool_calls"] = tool_calls
                openai_messages.append(assistant_msg)
                continue

            # Standard message
            openai_messages.append({
                "role": role,
                "content": content if isinstance(content, str) else str(content)
            })

        return openai_messages

    def _format_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Convert tool definitions to OpenAI format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
            }
            for tool in tools
        ]

    def _convert_response(
        self,
        response: Any,
        model: str,
        latency_ms: int
    ) -> ProviderResponse:
        """Convert OpenAI response to unified format."""
        import json

        choice = response.choices[0]
        message = choice.message

        # Extract content blocks
        content_blocks = []

        # Add text content if present
        if message.content:
            content_blocks.append(ContentBlock(
                type="text",
                text=message.content
            ))

        # Add tool calls if present
        if message.tool_calls:
            for tool_call in message.tool_calls:
                try:
                    tool_input = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_input = {"raw": tool_call.function.arguments}

                content_blocks.append(ContentBlock(
                    type="tool_use",
                    tool_use_id=tool_call.id,
                    tool_name=tool_call.function.name,
                    tool_input=tool_input
                ))

        # Map stop reason
        finish_reason = choice.finish_reason
        if finish_reason == "tool_calls":
            stop_reason = StopReason.TOOL_USE
        elif finish_reason == "length":
            stop_reason = StopReason.MAX_TOKENS
        elif finish_reason == "stop":
            stop_reason = StopReason.END_TURN
        else:
            stop_reason = StopReason.END_TURN

        # Extract usage
        usage = TokenUsage(
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )

        return ProviderResponse(
            provider=ProviderType.OPENAI,
            model=model,
            content=content_blocks,
            stop_reason=stop_reason,
            usage=usage,
            raw_response=response,
            latency_ms=latency_ms
        )

    def _convert_error(self, error: Exception) -> ProviderError:
        """Convert OpenAI SDK errors to unified errors."""
        error_str = str(error)

        try:
            from openai import (
                APIError,
                APIConnectionError as OpenAIConnectionError,
                RateLimitError as OpenAIRateLimitError,
                AuthenticationError as OpenAIAuthError,
            )

            if isinstance(error, OpenAIRateLimitError):
                return RateLimitError(
                    f"OpenAI rate limit exceeded: {error_str}",
                    ProviderType.OPENAI,
                    original_error=error
                )

            if isinstance(error, OpenAIAuthError):
                return AuthenticationError(
                    f"OpenAI authentication failed: {error_str}",
                    ProviderType.OPENAI,
                    original_error=error
                )

            if isinstance(error, OpenAIConnectionError):
                return ConnectionError(
                    f"OpenAI connection error: {error_str}",
                    ProviderType.OPENAI,
                    original_error=error
                )

            if isinstance(error, APIError):
                # Check for context length errors
                if "context_length" in error_str.lower() or "maximum context" in error_str.lower():
                    return ContextLengthError(
                        f"Context length exceeded: {error_str}",
                        ProviderType.OPENAI,
                        max_tokens=0,
                        requested_tokens=0,
                        original_error=error
                    )

                return ProviderError(
                    f"OpenAI API error: {error_str}",
                    ProviderType.OPENAI,
                    retryable=True,
                    original_error=error
                )

        except ImportError:
            pass

        return ProviderError(
            f"Unexpected OpenAI error: {error_str}",
            ProviderType.OPENAI,
            retryable=False,
            original_error=error
        )

    def get_available_models(self) -> List[str]:
        """Get list of available GPT models."""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1",
            "o1-mini",
        ]

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Estimate cost for OpenAI API call."""
        # Local servers have no API cost
        if self.is_local:
            return 0.0

        pricing = OPENAI_PRICING.get(model, OPENAI_PRICING["default"])
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost
