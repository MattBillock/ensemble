"""
Ollama provider implementation.

Uses Ollama's local API for running open-source LLMs locally.
Supports models like Llama, Mistral, CodeLlama, etc.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

from .base import (
    LLMProvider,
    ProviderType,
    ProviderResponse,
    ProviderError,
    ConnectionError,
    ContentBlock,
    TokenUsage,
    StopReason,
    ToolDefinition,
)

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """
    Ollama provider for local LLM inference.

    Uses Ollama's REST API to run models locally. Ollama must be installed
    and running for this provider to work.

    See: https://ollama.ai/
    """

    DEFAULT_HOST = "http://localhost:11434"

    def __init__(
        self,
        host: Optional[str] = None,
        timeout: int = 300,
        default_model: str = "llama3:8b"
    ):
        """
        Initialize Ollama provider.

        Args:
            host: Ollama API host URL. Defaults to http://localhost:11434
            timeout: Request timeout in seconds.
            default_model: Default model to use if not specified.
        """
        super().__init__(ProviderType.OLLAMA)
        self.host = host or os.environ.get("OLLAMA_HOST", self.DEFAULT_HOST)
        self.timeout = timeout
        self.default_model = default_model
        self._available_models: List[str] = []

    def initialize(self) -> bool:
        """Initialize and check if Ollama is available."""
        try:
            # Check if Ollama is running by hitting the /api/tags endpoint
            url = f"{self.host}/api/tags"
            request = urllib.request.Request(url)

            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                self._available_models = [
                    model['name'] for model in data.get('models', [])
                ]

            if self._available_models:
                self._available = True
                logger.info(f"Ollama provider initialized with {len(self._available_models)} models")
                return True
            else:
                logger.warning("Ollama is running but no models are installed")
                self._available = False
                return False

        except urllib.error.URLError as e:
            logger.warning(f"Cannot connect to Ollama at {self.host}: {e}")
            self._available = False
            return False
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama provider: {e}")
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
        """Send a message to Ollama."""
        if not self._available:
            raise ProviderError(
                "Ollama provider not available",
                ProviderType.OLLAMA,
                retryable=False
            )

        # Use default model if not specified or model not available
        if not model or model not in self._available_models:
            if self.default_model in self._available_models:
                model = self.default_model
            elif self._available_models:
                model = self._available_models[0]
            else:
                raise ProviderError(
                    f"No models available in Ollama",
                    ProviderType.OLLAMA,
                    retryable=False
                )

        start_time = time.time()

        try:
            # Convert messages to Ollama format
            ollama_messages = self._convert_messages(messages, system_prompt)

            # Build request payload
            payload = {
                "model": model,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }

            # Note: Ollama's tool support is limited, so we skip tools for now
            if tools:
                logger.warning("Ollama provider has limited tool support - tools will be ignored")

            # Make API call
            url = f"{self.host}/api/chat"
            request_data = json.dumps(payload).encode('utf-8')

            request = urllib.request.Request(
                url,
                data=request_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_data = json.loads(response.read().decode('utf-8'))

            latency_ms = int((time.time() - start_time) * 1000)

            # Convert to unified response
            provider_response = self._convert_response(response_data, model, latency_ms)
            self.record_success(provider_response)

            return provider_response

        except urllib.error.URLError as e:
            error = ConnectionError(
                f"Ollama connection error: {e}",
                ProviderType.OLLAMA,
                original_error=e
            )
            self.record_error(error)
            raise error
        except urllib.error.HTTPError as e:
            error = ProviderError(
                f"Ollama HTTP error {e.code}: {e.reason}",
                ProviderType.OLLAMA,
                retryable=e.code >= 500,
                original_error=e
            )
            self.record_error(error)
            raise error
        except Exception as e:
            error = ProviderError(
                f"Ollama error: {e}",
                ProviderType.OLLAMA,
                retryable=True,
                original_error=e
            )
            self.record_error(error)
            raise error

    def _convert_messages(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str]
    ) -> List[Dict[str, str]]:
        """Convert messages to Ollama format."""
        ollama_messages = []

        # Add system message
        if system_prompt:
            ollama_messages.append({
                "role": "system",
                "content": system_prompt
            })

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Handle structured content
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif item.get("type") == "tool_result":
                            text_parts.append(f"Tool result: {item.get('content', '')}")
                        elif item.get("type") == "tool_use":
                            text_parts.append(f"Using tool: {item.get('name', 'unknown')}")
                content = "\n".join(text_parts)

            ollama_messages.append({
                "role": role,
                "content": content if isinstance(content, str) else str(content)
            })

        return ollama_messages

    def _convert_response(
        self,
        response_data: Dict[str, Any],
        model: str,
        latency_ms: int
    ) -> ProviderResponse:
        """Convert Ollama response to unified format."""
        message = response_data.get("message", {})
        response_text = message.get("content", "")

        # Extract token counts
        eval_count = response_data.get("eval_count", 0)
        prompt_eval_count = response_data.get("prompt_eval_count", 0)

        content_blocks = [ContentBlock(
            type="text",
            text=response_text
        )]

        # Determine stop reason
        done_reason = response_data.get("done_reason", "stop")
        if done_reason == "length":
            stop_reason = StopReason.MAX_TOKENS
        else:
            stop_reason = StopReason.END_TURN

        return ProviderResponse(
            provider=ProviderType.OLLAMA,
            model=model,
            content=content_blocks,
            stop_reason=stop_reason,
            usage=TokenUsage(
                input_tokens=prompt_eval_count,
                output_tokens=eval_count
            ),
            raw_response=response_data,
            latency_ms=latency_ms
        )

    def get_available_models(self) -> List[str]:
        """Get list of models available in Ollama."""
        if not self._available_models:
            self.initialize()
        return self._available_models

    def pull_model(self, model: str) -> bool:
        """
        Pull (download) a model to Ollama.

        Args:
            model: Model name to pull (e.g., "llama3:8b", "codellama:34b")

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.host}/api/pull"
            payload = json.dumps({"name": model}).encode('utf-8')

            request = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            # This is a streaming endpoint, we just check for success
            with urllib.request.urlopen(request, timeout=600) as response:
                # Read all lines to complete the pull
                while True:
                    line = response.readline()
                    if not line:
                        break
                    status = json.loads(line.decode('utf-8'))
                    if status.get("status") == "success":
                        logger.info(f"Successfully pulled model: {model}")
                        self._available_models.append(model)
                        return True

            return False

        except Exception as e:
            logger.error(f"Failed to pull model {model}: {e}")
            return False

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """
        Estimate cost for Ollama inference.

        Local inference is free (no API costs), though there are electricity
        and hardware costs not captured here.
        """
        return 0.0

    def list_running_models(self) -> List[Dict[str, Any]]:
        """List models currently loaded in Ollama."""
        try:
            url = f"{self.host}/api/ps"
            request = urllib.request.Request(url)

            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data.get("models", [])

        except Exception as e:
            logger.error(f"Failed to list running models: {e}")
            return []
