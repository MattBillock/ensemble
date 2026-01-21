"""
Unit tests for title_generator module.

Tests the TitleGenerator class for AI-powered title generation.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestTitleGenerator:
    """Test TitleGenerator class."""

    def test_init_creates_client(self):
        """Test that initialization creates an Anthropic client."""
        with patch('src.runtime.agents.title_generator.Anthropic') as mock_anthropic:
            from src.runtime.agents.title_generator import TitleGenerator

            generator = TitleGenerator(api_key="test-key")

            mock_anthropic.assert_called_once_with(api_key="test-key")
            assert generator.client is not None

    def test_model_constant(self):
        """Test that MODEL constant is set correctly."""
        from src.runtime.agents.title_generator import TitleGenerator

        assert TitleGenerator.MODEL == "claude-3-haiku-20240307"

    def test_max_tokens_constant(self):
        """Test that MAX_TOKENS constant is set correctly."""
        from src.runtime.agents.title_generator import TitleGenerator

        assert TitleGenerator.MAX_TOKENS == 50

    def test_system_prompt_exists(self):
        """Test that SYSTEM_PROMPT is defined and contains key instructions."""
        from src.runtime.agents.title_generator import TitleGenerator

        assert TitleGenerator.SYSTEM_PROMPT is not None
        assert "title generator" in TitleGenerator.SYSTEM_PROMPT.lower()
        assert "5-10 word" in TitleGenerator.SYSTEM_PROMPT

    def test_generate_title_success(self):
        """Test successful title generation."""
        with patch('src.runtime.agents.title_generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Build user authentication system")]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            from src.runtime.agents.title_generator import TitleGenerator

            generator = TitleGenerator(api_key="test-key")
            title = generator.generate_title("Create a login system with JWT tokens")

            assert title == "Build user authentication system"
            mock_client.messages.create.assert_called_once()

    def test_generate_title_strips_quotes(self):
        """Test that generated titles have quotes stripped."""
        with patch('src.runtime.agents.title_generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text='"Fix pagination bug"')]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            from src.runtime.agents.title_generator import TitleGenerator

            generator = TitleGenerator(api_key="test-key")
            title = generator.generate_title("Fix the pagination bug")

            assert title == "Fix pagination bug"
            assert '"' not in title

    def test_generate_title_strips_trailing_period(self):
        """Test that generated titles have trailing periods stripped."""
        with patch('src.runtime.agents.title_generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Add dark mode toggle.")]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            from src.runtime.agents.title_generator import TitleGenerator

            generator = TitleGenerator(api_key="test-key")
            title = generator.generate_title("Add dark mode")

            assert title == "Add dark mode toggle"
            assert not title.endswith('.')

    def test_generate_title_truncates_long_prompts(self):
        """Test that long prompts are truncated to 2000 characters."""
        with patch('src.runtime.agents.title_generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Test title")]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            from src.runtime.agents.title_generator import TitleGenerator

            generator = TitleGenerator(api_key="test-key")
            long_prompt = "x" * 5000
            generator.generate_title(long_prompt)

            # Verify the prompt passed to the API was truncated
            call_args = mock_client.messages.create.call_args
            messages = call_args[1]['messages']
            assert len(messages[0]['content']) == 2000

    def test_generate_title_api_error_fallback(self):
        """Test that API errors trigger fallback title generation."""
        with patch('src.runtime.agents.title_generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API Error")
            mock_anthropic.return_value = mock_client

            from src.runtime.agents.title_generator import TitleGenerator

            generator = TitleGenerator(api_key="test-key")
            title = generator.generate_title("Create a simple test")

            # Should use fallback title
            assert title == "Create a simple test"

    def test_fallback_title_short_prompt(self):
        """Test fallback title with short prompt."""
        with patch('src.runtime.agents.title_generator.Anthropic'):
            from src.runtime.agents.title_generator import TitleGenerator

            generator = TitleGenerator(api_key="test-key")
            title = generator._fallback_title("Hello world test")

            assert title == "Hello world test"

    def test_fallback_title_long_prompt(self):
        """Test fallback title truncates to first 8 words with ellipsis."""
        with patch('src.runtime.agents.title_generator.Anthropic'):
            from src.runtime.agents.title_generator import TitleGenerator

            generator = TitleGenerator(api_key="test-key")
            long_prompt = "one two three four five six seven eight nine ten eleven twelve"
            title = generator._fallback_title(long_prompt)

            assert title == "one two three four five six seven eight..."
            assert title.endswith("...")

    def test_fallback_title_exactly_8_words(self):
        """Test fallback title with exactly 8 words doesn't add ellipsis."""
        with patch('src.runtime.agents.title_generator.Anthropic'):
            from src.runtime.agents.title_generator import TitleGenerator

            generator = TitleGenerator(api_key="test-key")
            prompt = "one two three four five six seven eight"
            title = generator._fallback_title(prompt)

            assert title == "one two three four five six seven eight"
            assert not title.endswith("...")


class TestGetTitleGenerator:
    """Test get_title_generator singleton function."""

    def test_get_title_generator_returns_instance(self):
        """Test that get_title_generator returns a TitleGenerator instance."""
        # Reset singleton for test
        import src.runtime.agents.title_generator as module
        module._generator_instance = None

        with patch('src.runtime.agents.title_generator.Anthropic'):
            from src.runtime.agents.title_generator import get_title_generator

            generator = get_title_generator("test-key")

            assert generator is not None

    def test_get_title_generator_returns_same_instance(self):
        """Test that get_title_generator returns the same instance."""
        import src.runtime.agents.title_generator as module
        module._generator_instance = None

        with patch('src.runtime.agents.title_generator.Anthropic'):
            from src.runtime.agents.title_generator import get_title_generator

            generator1 = get_title_generator("test-key")
            generator2 = get_title_generator("test-key")

            assert generator1 is generator2


class TestGenerateTitleAsync:
    """Test async title generation function."""

    @pytest.mark.asyncio
    async def test_generate_title_async(self):
        """Test async title generation wrapper."""
        import src.runtime.agents.title_generator as module
        module._generator_instance = None

        with patch('src.runtime.agents.title_generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Async test title")]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            from src.runtime.agents.title_generator import generate_title_async

            title = await generate_title_async("Test prompt", "test-key")

            assert title == "Async test title"
