import pytest
from src.runtime.agents.runtime import TokenUsage

class TestTokenUsage:
    def test_token_usage_initialization_default(self):
        """
        Test TokenUsage initialization with default values.
        Verifies that default values are correctly set when no arguments are provided.
        """
        token_usage = TokenUsage()
        
        assert token_usage.prompt_tokens == 0, "Default prompt tokens should be 0"
        assert token_usage.completion_tokens == 0, "Default completion tokens should be 0"
        assert token_usage.total_tokens == 0, "Default total tokens should be 0"

    def test_token_usage_initialization_with_values(self):
        """
        Test TokenUsage initialization with specific input values.
        Ensures correct handling of provided token values.
        """
        token_usage = TokenUsage(prompt_tokens=50, completion_tokens=30)
        
        assert token_usage.prompt_tokens == 50, "Prompt tokens should match input"
        assert token_usage.completion_tokens == 30, "Completion tokens should match input"
        assert token_usage.total_tokens == 80, "Total tokens should be sum of prompt and completion tokens"

    def test_token_accumulation(self):
        """
        Verify token accumulation across multiple method calls.
        Tests the ability to add tokens incrementally.
        """
        token_usage = TokenUsage()
        
        token_usage.add_tokens(prompt_tokens=25, completion_tokens=15)
        assert token_usage.prompt_tokens == 25, "First token addition should update prompt tokens"
        assert token_usage.completion_tokens == 15, "First token addition should update completion tokens"
        assert token_usage.total_tokens == 40, "Total tokens should reflect first addition"
        
        token_usage.add_tokens(prompt_tokens=30, completion_tokens=20)
        assert token_usage.prompt_tokens == 55, "Subsequent addition should accumulate prompt tokens"
        assert token_usage.completion_tokens == 35, "Subsequent addition should accumulate completion tokens"
        assert token_usage.total_tokens == 90, "Total tokens should reflect cumulative additions"

    def test_to_dict_conversion(self):
        """
        Validate dictionary conversion methods.
        Ensures TokenUsage can be correctly converted to a dictionary.
        """
        token_usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
        
        token_dict = token_usage.to_dict()
        
        assert isinstance(token_dict, dict), "to_dict() should return a dictionary"
        assert token_dict.get('prompt_tokens') == 100, "Dictionary should contain correct prompt tokens"
        assert token_dict.get('completion_tokens') == 50, "Dictionary should contain correct completion tokens"
        assert token_dict.get('total_tokens') == 150, "Dictionary should contain correct total tokens"

    def test_negative_token_handling(self):
        """
        Test handling of negative token values during initialization and addition.
        Ensures that negative values are handled appropriately.
        """
        with pytest.raises(ValueError, match="Token values cannot be negative"):
            TokenUsage(prompt_tokens=-10, completion_tokens=0)
        
        token_usage = TokenUsage()
        with pytest.raises(ValueError, match="Token values cannot be negative"):
            token_usage.add_tokens(prompt_tokens=-25, completion_tokens=0)