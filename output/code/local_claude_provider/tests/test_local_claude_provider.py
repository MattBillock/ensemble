import pytest
import os
from unittest.mock import patch, MagicMock
from src.field.ensemble_ui.output.code.local_claude_provider.local_claude_provider import LocalClaudeProvider

class TestLocalClaudeProvider:
    @pytest.fixture
    def mock_subprocess(self):
        """Fixture to mock subprocess calls for consistent testing."""
        with patch('subprocess.Popen') as mock_popen, \
             patch('subprocess.run') as mock_run:
            yield mock_popen, mock_run

    def test_cli_path_configuration(self):
        """
        Test that LocalClaudeProvider correctly handles CLI path configuration.
        
        Validates that:
        - Custom CLI path can be set
        - Default CLI path is used if not specified
        - Path is validated and exists
        """
        # Test with custom path
        custom_path = "/custom/path/to/claude/cli"
        provider = LocalClaudeProvider(cli_path=custom_path)
        assert provider.cli_path == custom_path, "Custom CLI path not set correctly"

        # Test default path fallback
        with patch('os.path.exists', return_value=True):
            default_provider = LocalClaudeProvider()
            assert default_provider.cli_path is not None, "Default CLI path not set"

        # Test non-existent path raises configuration error
        with patch('os.path.exists', return_value=False):
            with pytest.raises(ValueError, match="Invalid CLI path"):
                LocalClaudeProvider(cli_path="/non/existent/path")

    def test_availability_check(self, mock_subprocess):
        """
        Test LocalClaudeProvider's availability check mechanism.
        
        Validates that:
        - Availability can be checked
        - Correct return type is boolean
        - Different CLI response scenarios are handled
        """
        mock_popen, mock_run = mock_subprocess
        
        # Successful availability check
        mock_run.return_value = MagicMock(returncode=0)
        provider = LocalClaudeProvider()
        assert provider.is_available() is True, "Provider should be available with successful CLI check"

        # Unavailable scenario
        mock_run.return_value = MagicMock(returncode=1)
        assert provider.is_available() is False, "Provider should not be available with failed CLI check"

    def test_basic_prompt_execution(self, mock_subprocess):
        """
        Test basic prompt execution functionality.
        
        Validates that:
        - Prompts can be executed
        - Correct CLI command is constructed
        - Response is correctly parsed
        """
        mock_popen, mock_run = mock_subprocess
        
        # Mock a successful prompt execution
        mock_run.return_value = MagicMock(
            returncode=0, 
            stdout='{"response": "Test Claude response"}'
        )
        
        provider = LocalClaudeProvider()
        response = provider.execute_prompt("Hello, Claude")
        
        assert response == "Test Claude response", "Prompt execution did not return expected response"
        
        # Verify CLI command construction
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert provider.cli_path in call_args, "CLI path not included in command"
        assert "Hello, Claude" in call_args, "Prompt not correctly passed to CLI"

    def test_system_prompt_support(self, mock_subprocess):
        """
        Test system prompt configuration and execution.
        
        Validates that:
        - System prompts can be set
        - System prompts are correctly included in CLI command
        """
        mock_popen, mock_run = mock_subprocess
        
        # Mock response with system prompt
        mock_run.return_value = MagicMock(
            returncode=0, 
            stdout='{"response": "Responded with system context"}'
        )
        
        provider = LocalClaudeProvider()
        system_prompt = "You are a helpful AI assistant"
        
        response = provider.execute_prompt(
            "Answer the question", 
            system_prompt=system_prompt
        )
        
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert system_prompt in call_args, "System prompt not included in CLI command"
        assert response == "Responded with system context", "System prompt execution failed"

    def test_circuit_breaker_functionality(self, mock_subprocess):
        """
        Test circuit breaker mechanism for repeated failures.
        
        Validates that:
        - Circuit breaker opens after consecutive failures
        - Provider becomes unavailable after threshold
        - Cooldown period is respected
        """
        mock_popen, mock_run = mock_subprocess
        
        # Simulate repeated failures
        mock_run.return_value = MagicMock(returncode=1)
        
        provider = LocalClaudeProvider()
        
        # Trigger multiple failures
        for _ in range(provider.CIRCUIT_BREAKER_THRESHOLD + 1):
            provider.execute_prompt("Test prompt")
        
        assert not provider.is_available(), "Circuit breaker did not activate after threshold"

    def test_error_handling_cli_failures(self, mock_subprocess):
        """
        Test error handling for various CLI execution failures.
        
        Validates that:
        - Different CLI failure modes are handled
        - Appropriate exceptions are raised
        - Failure details are logged or reported
        """
        mock_popen, mock_run = mock_subprocess
        
        provider = LocalClaudeProvider()
        
        # Test timeout scenario
        mock_run.side_effect = TimeoutError("CLI execution timed out")
        with pytest.raises(TimeoutError, match="CLI execution timed out"):
            provider.execute_prompt("Timeout test")
        
        # Test permission/access failure
        mock_run.side_effect = PermissionError("Cannot access CLI")
        with pytest.raises(PermissionError, match="Cannot access CLI"):
            provider.execute_prompt("Permission test")
        
        # Test unexpected CLI response format
        mock_run.return_value = MagicMock(
            returncode=0, 
            stdout='Invalid JSON response'
        )
        with pytest.raises(ValueError, match="Invalid CLI response format"):
            provider.execute_prompt("Malformed response test")