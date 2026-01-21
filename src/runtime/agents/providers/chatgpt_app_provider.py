"""
ChatGPT macOS App provider implementation.

Uses AppleScript automation to interact with the ChatGPT desktop app on macOS.
This is an experimental provider that automates the ChatGPT.app GUI.
"""

import logging
import os
import platform
import subprocess
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


# Add CHATGPT_APP to ProviderType if not already there
# Note: We'll need to add this to base.py


class ChatGPTAppProvider(LLMProvider):
    """
    ChatGPT macOS App provider using AppleScript automation.

    This provider interacts with the ChatGPT desktop application on macOS
    by sending messages through UI automation. This is experimental and
    may break if the app's UI changes.

    Requirements:
    - macOS operating system
    - ChatGPT.app installed (from Mac App Store or OpenAI)
    - Accessibility permissions for the terminal/script running this code
    """

    APP_NAME = "ChatGPT"
    BUNDLE_ID = "com.openai.chat"

    def __init__(
        self,
        timeout: int = 120,
        poll_interval: float = 0.5,
        wait_for_response: bool = True
    ):
        """
        Initialize ChatGPT App provider.

        Args:
            timeout: Maximum seconds to wait for a response.
            poll_interval: Seconds between checking for response completion.
            wait_for_response: Whether to wait for the full response.
        """
        super().__init__(ProviderType.CHATGPT_APP)
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.wait_for_response = wait_for_response
        self._is_macos = platform.system() == "Darwin"

    def initialize(self) -> bool:
        """Check if ChatGPT app is available on macOS."""
        if not self._is_macos:
            logger.warning("ChatGPT App provider only works on macOS")
            self._available = False
            return False

        # Check if ChatGPT.app is installed
        try:
            result = subprocess.run(
                ["mdfind", f"kMDItemCFBundleIdentifier == '{self.BUNDLE_ID}'"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                self._available = True
                logger.info(f"ChatGPT App found: {result.stdout.strip().split()[0]}")
                return True
            else:
                logger.warning("ChatGPT.app not found on this system")
                self._available = False
                return False

        except Exception as e:
            logger.error(f"Failed to check for ChatGPT.app: {e}")
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
        """Send a message to ChatGPT via the desktop app."""
        if not self._available:
            raise ProviderError(
                "ChatGPT App provider not available",
                ProviderType.CHATGPT_APP,
                retryable=False
            )

        if tools:
            logger.warning("ChatGPT App provider does not support tools - ignoring")

        start_time = time.time()

        try:
            # Build the message to send
            prompt = self._build_prompt(messages, system_prompt)

            # Activate the app and send the message
            self._activate_app()
            time.sleep(0.5)  # Wait for app to focus

            # Start a new chat if needed
            self._start_new_chat()
            time.sleep(0.3)

            # Type and send the message
            self._send_text(prompt)

            # Wait for response
            response_text = self._wait_for_response()

            latency_ms = int((time.time() - start_time) * 1000)

            # Parse response
            provider_response = self._parse_response(response_text, model, latency_ms)
            self.record_success(provider_response)

            return provider_response

        except Exception as e:
            error = ProviderError(
                f"ChatGPT App error: {e}",
                ProviderType.CHATGPT_APP,
                retryable=True,
                original_error=e
            )
            self.record_error(error)
            raise error

    def _activate_app(self):
        """Activate (bring to front) the ChatGPT app."""
        script = f'''
        tell application "{self.APP_NAME}"
            activate
        end tell
        '''
        self._run_applescript(script)

    def _start_new_chat(self):
        """Start a new chat in ChatGPT app using keyboard shortcut."""
        # Cmd+N is typically new chat
        script = '''
        tell application "System Events"
            keystroke "n" using command down
        end tell
        '''
        try:
            self._run_applescript(script)
        except Exception:
            # New chat might fail if already in new chat state
            pass

    def _send_text(self, text: str):
        """Type text and send it in the ChatGPT app."""
        # Escape special characters for AppleScript
        escaped_text = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

        # Type the message
        script = f'''
        tell application "System Events"
            tell process "{self.APP_NAME}"
                -- Set the text in the input field
                set value of text area 1 of group 1 of window 1 to "{escaped_text}"
                delay 0.2
                -- Press Enter to send
                keystroke return
            end tell
        end tell
        '''

        try:
            self._run_applescript(script)
        except Exception as e:
            # Fallback: use clipboard
            logger.warning(f"Direct input failed, trying clipboard: {e}")
            self._send_via_clipboard(text)

    def _send_via_clipboard(self, text: str):
        """Send text by pasting from clipboard."""
        # Copy to clipboard
        subprocess.run(
            ["pbcopy"],
            input=text.encode('utf-8'),
            check=True
        )

        # Paste and send
        script = f'''
        tell application "System Events"
            tell process "{self.APP_NAME}"
                keystroke "v" using command down
                delay 0.3
                keystroke return
            end tell
        end tell
        '''
        self._run_applescript(script)

    def _wait_for_response(self) -> str:
        """Wait for ChatGPT to finish responding and return the text."""
        start_time = time.time()
        last_response = ""
        stable_count = 0

        while time.time() - start_time < self.timeout:
            try:
                # Try to get the last message from the conversation
                response = self._get_last_response()

                if response and response != last_response:
                    last_response = response
                    stable_count = 0
                elif response:
                    stable_count += 1
                    # If response hasn't changed for a few polls, assume it's complete
                    if stable_count >= 3:
                        return response

            except Exception as e:
                logger.warning(f"Error getting response: {e}")

            time.sleep(self.poll_interval)

        # Timeout reached, return whatever we have
        if last_response:
            return last_response

        raise ConnectionError(
            f"Timeout waiting for ChatGPT response after {self.timeout}s",
            ProviderType.CHATGPT_APP
        )

    def _get_last_response(self) -> Optional[str]:
        """Get the last assistant response from the ChatGPT window."""
        # This is tricky and depends on the app's UI structure
        # We'll try to get text from the conversation area
        script = f'''
        tell application "System Events"
            tell process "{self.APP_NAME}"
                -- Try to get the last message content
                -- This may need adjustment based on actual UI structure
                try
                    set allText to value of text area 1 of scroll area 1 of group 1 of window 1
                    return allText
                on error
                    return ""
                end try
            end tell
        end tell
        '''

        try:
            result = self._run_applescript(script)
            if result:
                # Extract the last assistant message
                # This parsing may need refinement
                return result.strip()
        except Exception:
            pass

        return None

    def _run_applescript(self, script: str) -> str:
        """Run an AppleScript and return the output."""
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            raise RuntimeError(f"AppleScript failed: {result.stderr}")

        return result.stdout.strip()

    def _build_prompt(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str]
    ) -> str:
        """Build a text prompt from messages."""
        parts = []

        if system_prompt:
            parts.append(f"[System Instructions: {system_prompt}]\n")

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif item.get("type") == "tool_result":
                            text_parts.append(f"[Tool Result: {item.get('content', '')}]")
                content = "\n".join(text_parts)

            if role == "user":
                parts.append(content)
            elif role == "assistant":
                parts.append(f"[Previous response: {content}]")

        return "\n\n".join(parts)

    def _parse_response(
        self,
        response_text: str,
        model: str,
        latency_ms: int
    ) -> ProviderResponse:
        """Parse response into unified format."""
        # Estimate tokens
        input_tokens = len(response_text.split()) * 2
        output_tokens = len(response_text.split()) * 2

        content_blocks = [ContentBlock(
            type="text",
            text=response_text
        )]

        return ProviderResponse(
            provider=ProviderType.CHATGPT_APP,  # Use OLLAMA as stand-in
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
        """Get available models (ChatGPT app uses whatever is selected in settings)."""
        return ["chatgpt-app"]

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """
        Estimate cost for ChatGPT App.

        The desktop app is included with ChatGPT Plus subscription ($20/month)
        so there's no per-token cost, but there may be usage limits.
        """
        return 0.0
