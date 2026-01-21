"""
Local Claude provider implementation.

Uses Claude Code CLI or similar local Claude installation for inference.
This provides a way to use Claude without direct API costs when running locally.
"""

import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional

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


class LocalClaudeProvider(LLMProvider):
    """
    Local Claude provider using Claude Code CLI.

    This provider uses the Claude Code CLI tool to interact with Claude
    locally, which may have different pricing/quota from direct API access.
    """

    # CLI command name to look for
    CLI_COMMANDS = ["claude", "claude-code"]

    def __init__(
        self,
        cli_path: Optional[str] = None,
        timeout: int = 300,
        working_dir: Optional[str] = None
    ):
        """
        Initialize local Claude provider.

        Args:
            cli_path: Path to Claude CLI executable. If not provided, searches PATH.
            timeout: Command timeout in seconds.
            working_dir: Working directory for CLI commands.
        """
        super().__init__(ProviderType.LOCAL_CLAUDE)
        self.cli_path = cli_path
        self.timeout = timeout
        self.working_dir = working_dir or os.getcwd()
        self._detected_cli = None

    def initialize(self) -> bool:
        """Initialize and check if Claude CLI is available."""
        # If explicit path provided, use it
        if self.cli_path:
            if os.path.isfile(self.cli_path) and os.access(self.cli_path, os.X_OK):
                self._detected_cli = self.cli_path
                self._available = True
                logger.info(f"Local Claude provider initialized with: {self.cli_path}")
                return True
            else:
                logger.warning(f"Specified CLI path not found or not executable: {self.cli_path}")
                self._available = False
                return False

        # Search for CLI in PATH
        for cmd in self.CLI_COMMANDS:
            cli_path = shutil.which(cmd)
            if cli_path:
                self._detected_cli = cli_path
                self._available = True
                logger.info(f"Local Claude provider found CLI: {cli_path}")
                return True

        logger.warning("Claude CLI not found in PATH")
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
        """Send a message using Claude CLI."""
        if not self._available or not self._detected_cli:
            raise ProviderError(
                "Local Claude provider not available",
                ProviderType.LOCAL_CLAUDE,
                retryable=False
            )

        start_time = time.time()

        try:
            # Build the prompt from messages
            prompt = self._build_prompt(messages, system_prompt)

            # Create a temporary file for the prompt (Claude CLI reads from files better)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                prompt_file = f.name

            try:
                # Build CLI command
                cmd = self._build_command(prompt, prompt_file, max_tokens, model)

                # Execute CLI
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=self.working_dir
                )

                if result.returncode != 0:
                    raise ProviderError(
                        f"Claude CLI failed: {result.stderr}",
                        ProviderType.LOCAL_CLAUDE,
                        retryable=True
                    )

                response_text = result.stdout.strip()

            finally:
                # Cleanup temp file
                if os.path.exists(prompt_file):
                    os.unlink(prompt_file)

            latency_ms = int((time.time() - start_time) * 1000)

            # Parse response
            provider_response = self._parse_response(response_text, model, latency_ms)
            self.record_success(provider_response)

            return provider_response

        except subprocess.TimeoutExpired:
            error = ConnectionError(
                f"Claude CLI timed out after {self.timeout}s",
                ProviderType.LOCAL_CLAUDE
            )
            self.record_error(error)
            raise error
        except ProviderError:
            raise
        except Exception as e:
            error = ProviderError(
                f"Local Claude error: {e}",
                ProviderType.LOCAL_CLAUDE,
                retryable=True,
                original_error=e
            )
            self.record_error(error)
            raise error

    def _build_prompt(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str]
    ) -> str:
        """Build a text prompt from messages."""
        parts = []

        if system_prompt:
            parts.append(f"System: {system_prompt}\n")

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if isinstance(content, list):
                # Handle structured content
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif item.get("type") == "tool_result":
                            text_parts.append(f"[Tool Result: {item.get('content', '')}]")
                content = "\n".join(text_parts)

            if role == "user":
                parts.append(f"Human: {content}\n")
            elif role == "assistant":
                parts.append(f"Assistant: {content}\n")

        # End with Assistant: to prompt response
        if not parts[-1].startswith("Assistant:"):
            parts.append("Assistant:")

        return "\n".join(parts)

    def _build_command(
        self,
        prompt: str,
        prompt_file: str,
        max_tokens: int,
        model: str
    ) -> List[str]:
        """Build the CLI command."""
        # Basic command - adjust based on actual CLI interface
        cmd = [self._detected_cli]

        # Try to use the prompt directly or via file
        # Different Claude CLI versions may have different interfaces
        if len(prompt) < 10000:
            # Short prompts can be passed directly
            cmd.extend(["--print", "-p", prompt])
        else:
            # Longer prompts via file
            cmd.extend(["--print", "-f", prompt_file])

        # Add max tokens if supported
        cmd.extend(["--max-tokens", str(max_tokens)])

        return cmd

    def _parse_response(
        self,
        response_text: str,
        model: str,
        latency_ms: int
    ) -> ProviderResponse:
        """Parse CLI response into unified format."""
        # Estimate tokens (rough approximation)
        input_tokens = len(response_text.split()) * 2  # Very rough estimate
        output_tokens = len(response_text.split()) * 2

        content_blocks = [ContentBlock(
            type="text",
            text=response_text
        )]

        return ProviderResponse(
            provider=ProviderType.LOCAL_CLAUDE,
            model=model,
            content=content_blocks,
            stop_reason=StopReason.END_TURN,
            usage=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens
            ),
            latency_ms=latency_ms
        )

    def get_available_models(self) -> List[str]:
        """Get list of available models (local Claude uses whatever is configured)."""
        # Local Claude typically uses whatever model the CLI is configured for
        return ["claude-local"]

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """
        Estimate cost for local Claude.

        Local Claude through CLI may have different pricing or may be included
        in a subscription. We return 0 as a baseline, but actual costs may vary.
        """
        # Local execution - no direct API cost (though there may be subscription costs)
        return 0.0
