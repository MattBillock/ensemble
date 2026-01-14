"""Service for generating AI-powered prompt titles using Claude Haiku."""
import logging
from typing import Optional

from anthropic import Anthropic

logger = logging.getLogger(__name__)


class TitleGenerator:
    """Generate concise titles for prompts using Claude Haiku."""

    # Use Haiku for cost-efficient title generation
    MODEL = "claude-3-haiku-20240307"
    MAX_TOKENS = 50

    SYSTEM_PROMPT = """You are a title generator. Generate a concise 5-10 word title that summarizes the main task or goal in the user's prompt.

Rules:
- Return ONLY the title, nothing else
- No quotes, periods, or other punctuation
- Use action verbs when possible (Build, Create, Fix, Add, Implement)
- Be specific but brief
- If the prompt is about code, mention the technology/language if relevant

Examples:
- "Build user authentication with JWT tokens"
- "Fix pagination bug in product listing"
- "Add dark mode toggle to settings page"
- "Implement real-time chat with WebSockets"
- "Create REST API for user management"
"""

    def __init__(self, api_key: str):
        """
        Initialize the title generator.

        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)

    def generate_title(self, prompt: str) -> str:
        """
        Generate a short title for the given prompt.

        Args:
            prompt: The user's full prompt text

        Returns:
            A 5-10 word title summarizing the prompt
        """
        try:
            # Truncate very long prompts to save tokens
            truncated_prompt = prompt[:2000] if len(prompt) > 2000 else prompt

            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": truncated_prompt}]
            )

            title = response.content[0].text.strip()

            # Clean up any quotes or trailing punctuation
            title = title.strip('"\'')
            if title.endswith('.'):
                title = title[:-1]

            logger.info(f"Generated title: {title}")
            return title

        except Exception as e:
            logger.error(f"Failed to generate title: {e}")
            # Return a fallback title based on first few words
            return self._fallback_title(prompt)

    def _fallback_title(self, prompt: str) -> str:
        """
        Generate a fallback title if AI generation fails.

        Args:
            prompt: The user's prompt

        Returns:
            First ~8 words of prompt with ellipsis
        """
        words = prompt.split()[:8]
        title = " ".join(words)
        if len(prompt.split()) > 8:
            title += "..."
        return title


# Singleton instance for reuse
_generator_instance: Optional[TitleGenerator] = None


def get_title_generator(api_key: str) -> TitleGenerator:
    """
    Get or create the title generator instance.

    Args:
        api_key: Anthropic API key

    Returns:
        TitleGenerator instance
    """
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = TitleGenerator(api_key)
    return _generator_instance


async def generate_title_async(prompt: str, api_key: str) -> str:
    """
    Async wrapper for title generation.

    Args:
        prompt: The user's prompt
        api_key: Anthropic API key

    Returns:
        Generated title
    """
    generator = get_title_generator(api_key)
    return generator.generate_title(prompt)
