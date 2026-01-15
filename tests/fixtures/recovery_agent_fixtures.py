"""
Pytest fixtures for Recovery Agent testing.

This module provides factory functions and fixtures for generating test data
for recovery agent functionality, including valid and invalid inputs for
comprehensive test coverage.
"""

from datetime import datetime
from typing import Any, Dict, List
import pytest


# Valid Input Fixtures
# ====================


@pytest.fixture
def valid_recovery_task_input() -> Dict[str, Any]:
    """
    Fixture returning a valid RecoveryTaskInput dictionary.
    
    Returns:
        Dict[str, Any]: A dictionary containing all required fields for a valid
                        recovery task input with realistic test data.
    """
    return {
        "recovery_id": 1001,
        "agent_id": "agent_12345",
        "session_id": "session_67890",
        "agent_type": "code_writer",
        "agent_name": "CodeWriter-001",
        "input_data": {
            "task": "Write a function",
            "context": "Python module",
            "requirements": ["type hints", "docstrings"]
        },
        "reason": "Agent exceeded timeout limit",
        "strategy": "retry",
        "priority": 1,
        "attempts": 0,
        "max_attempts": 3,
        "created_at": datetime(2024, 1, 15, 10, 30, 0)
    }


@pytest.fixture
def valid_recovery_agent_input() -> Dict[str, Any]:
    """
    Fixture returning a valid RecoveryAgentInput dictionary.
    
    Returns:
        Dict[str, Any]: A dictionary containing all required fields for valid
                        recovery agent input data.
    """
    return {
        "recovery_task": {
            "recovery_id": 2001,
            "agent_id": "agent_99999",
            "session_id": "session_11111",
            "agent_type": "code_tester",
            "agent_name": "CodeTester-002",
            "input_data": {
                "test_file": "test_example.py",
                "test_cases": ["test_basic", "test_edge_case"]
            },
            "reason": "Test execution failed with assertion error",
            "strategy": "enhance_prompt",
            "priority": 2,
            "attempts": 1,
            "max_attempts": 5,
            "created_at": datetime(2024, 1, 15, 11, 0, 0)
        },
        "context": {
            "previous_attempts": 1,
            "error_history": ["AssertionError: Expected 5, got 3"],
            "environment": "test"
        },
        "options": {
            "verbose": True,
            "timeout": 300
        }
    }


@pytest.fixture
def valid_recovery_agent_output() -> Dict[str, Any]:
    """
    Fixture returning a valid RecoveryAgentOutput dictionary.
    
    Returns:
        Dict[str, Any]: A dictionary containing all required fields for valid
                        recovery agent output with status field from allowed values.
    """
    return {
        "status": "success",
        "recovery_id": 1001,
        "agent_id": "agent_12345",
        "resolved": True,
        "new_input_data": {
            "task": "Write a function with enhanced context",
            "context": "Python module with proper error handling",
            "requirements": ["type hints", "docstrings", "error handling"]
        },
        "strategy_applied": "enhance_prompt",
        "message": "Recovery successful: Enhanced prompt with additional context",
        "execution_time": 2.5,
        "timestamp": datetime(2024, 1, 15, 10, 32, 30)
    }


# Factory Fixtures
# ================


@pytest.fixture
def recovery_task_factory(valid_recovery_task_input: Dict[str, Any]):
    """
    Factory fixture for creating custom recovery tasks with overrides.
    
    Args:
        valid_recovery_task_input: Base valid recovery task input fixture.
    
    Returns:
        Callable: A factory function that accepts keyword arguments to override
                  default values in the recovery task input.
    
    Example:
        custom_task = recovery_task_factory(
            recovery_id=9999,
            strategy="escalate",
            priority=3
        )
    """
    def _create_recovery_task(**overrides: Any) -> Dict[str, Any]:
        """
        Create a recovery task with custom field values.
        
        Args:
            **overrides: Keyword arguments to override default field values.
        
        Returns:
            Dict[str, Any]: A recovery task input dictionary with overridden values.
        """
        task = valid_recovery_task_input.copy()
        task.update(overrides)
        return task
    
    return _create_recovery_task


@pytest.fixture
def invalid_recovery_input_missing_field():
    """
    Factory fixture for generating invalid recovery inputs with missing fields.
    
    Returns:
        Callable: A function that takes a field_name parameter and returns a
                  recovery input dictionary with that field missing, useful for
                  negative testing scenarios.
    
    Example:
        invalid_input = invalid_recovery_input_missing_field("recovery_id")
        # Returns input dict without the recovery_id field
    """
    def _create_invalid_input(field_name: str) -> Dict[str, Any]:
        """
        Generate an invalid recovery input missing the specified field.
        
        Args:
            field_name: The name of the field to omit from the input.
        
        Returns:
            Dict[str, Any]: A recovery task input dictionary missing the specified field.
        """
        complete_input = {
            "recovery_id": 3001,
            "agent_id": "agent_test_123",
            "session_id": "session_test_456",
            "agent_type": "code_reviewer",
            "agent_name": "CodeReviewer-001",
            "input_data": {"code": "def test(): pass"},
            "reason": "Code review failed quality checks",
            "strategy": "retry",
            "priority": 2,
            "attempts": 0,
            "max_attempts": 3,
            "created_at": datetime(2024, 1, 15, 12, 0, 0)
        }
        
        # Remove the specified field
        if field_name in complete_input:
            del complete_input[field_name]
        
        return complete_input
    
    return _create_invalid_input


# Enumeration Fixtures
# ====================


@pytest.fixture
def all_recovery_strategies() -> List[str]:
    """
    Fixture returning all valid recovery strategy values.
    
    Returns:
        List[str]: A list of all valid recovery strategies that can be used
                   in recovery task inputs.
    """
    return ["retry", "enhance_prompt", "escalate"]


@pytest.fixture
def all_recovery_statuses() -> List[str]:
    """
    Fixture returning all valid recovery status values.
    
    Returns:
        List[str]: A list of all valid recovery status values that can be
                   returned in recovery agent outputs.
    """
    return ["success", "failed", "needs_user_input"]


# Parametrization Helper Fixtures
# ================================


@pytest.fixture
def recovery_strategy_samples(all_recovery_strategies: List[str]) -> List[Dict[str, Any]]:
    """
    Fixture providing sample recovery tasks for each strategy type.
    
    Args:
        all_recovery_strategies: Fixture providing all valid strategies.
    
    Returns:
        List[Dict[str, Any]]: A list of recovery task dictionaries, one for each
                              strategy, useful for parametrized testing.
    """
    samples = []
    for idx, strategy in enumerate(all_recovery_strategies):
        samples.append({
            "recovery_id": 4000 + idx,
            "agent_id": f"agent_strategy_{idx}",
            "session_id": f"session_strategy_{idx}",
            "agent_type": "test_agent",
            "agent_name": f"TestAgent-{strategy}",
            "input_data": {"test": f"data_for_{strategy}"},
            "reason": f"Testing {strategy} strategy",
            "strategy": strategy,
            "priority": idx + 1,
            "attempts": 0,
            "max_attempts": 3,
            "created_at": datetime(2024, 1, 15, 13, idx, 0)
        })
    return samples


@pytest.fixture
def recovery_status_samples(all_recovery_statuses: List[str]) -> List[Dict[str, Any]]:
    """
    Fixture providing sample recovery outputs for each status type.
    
    Args:
        all_recovery_statuses: Fixture providing all valid statuses.
    
    Returns:
        List[Dict[str, Any]]: A list of recovery output dictionaries, one for each
                              status, useful for parametrized testing.
    """
    samples = []
    for idx, status in enumerate(all_recovery_statuses):
        samples.append({
            "status": status,
            "recovery_id": 5000 + idx,
            "agent_id": f"agent_status_{idx}",
            "resolved": status == "success",
            "new_input_data": {"result": f"data_for_{status}"},
            "strategy_applied": "retry",
            "message": f"Recovery resulted in {status}",
            "execution_time": 1.0 + idx * 0.5,
            "timestamp": datetime(2024, 1, 15, 14, idx, 0)
        })
    return samples
