import pytest
from datetime import timedelta, datetime
from typing import List

from pydantic import ValidationError

# Import the models to be tested
from runtime.agents.failed_task_cleanup.models import CleanupResult, BatchCleanupResult

class TestCleanupResult:
    def test_cleanup_result_valid_creation(self):
        """
        Test creating a valid CleanupResult instance with all required fields.
        """
        now = datetime.now()
        cleanup_result = CleanupResult(
            task_id="test-task-123",
            is_success=True,
            cleaned_resources=["resource1", "resource2"],
            cleanup_duration=timedelta(seconds=10),
            cleanup_timestamp=now
        )
        
        assert cleanup_result.task_id == "test-task-123"
        assert cleanup_result.is_success is True
        assert cleanup_result.cleaned_resources == ["resource1", "resource2"]
        assert cleanup_result.cleanup_duration == timedelta(seconds=10)
        assert cleanup_result.cleanup_timestamp == now
        assert cleanup_result.error_message is None

    def test_cleanup_result_failed_with_error_message(self):
        """
        Test creating a CleanupResult for a failed cleanup with an error message.
        """
        now = datetime.now()
        cleanup_result = CleanupResult(
            task_id="test-task-fail",
            is_success=False,
            cleaned_resources=[],
            error_message="Cleanup failed due to network error",
            cleanup_duration=timedelta(seconds=5),
            cleanup_timestamp=now
        )
        
        assert cleanup_result.task_id == "test-task-fail"
        assert cleanup_result.is_success is False
        assert cleanup_result.cleaned_resources == []
        assert cleanup_result.error_message == "Cleanup failed due to network error"
        assert cleanup_result.cleanup_duration == timedelta(seconds=5)
        assert cleanup_result.cleanup_timestamp == now

    def test_cleanup_result_validation_errors(self):
        """
        Test validation errors for CleanupResult with invalid inputs.
        """
        # Test missing required fields
        with pytest.raises(ValidationError):
            CleanupResult(
                is_success=True,
                cleaned_resources=["resource1"]
            )

        # Test invalid field types
        with pytest.raises(ValidationError):
            CleanupResult(
                task_id=123,  # Invalid: not a string
                is_success=True,
                cleaned_resources=["resource1"],
                cleanup_duration=10,  # Invalid: not a timedelta
                cleanup_timestamp=None
            )

        # Test invalid is_success and error_message logic
        with pytest.raises(ValidationError):
            CleanupResult(
                task_id="test-task",
                is_success=False,
                cleaned_resources=[],
                cleanup_duration=timedelta(seconds=1),
                cleanup_timestamp=datetime.now()
                # Missing error_message when is_success is False
            )

    def test_cleanup_result_json_serialization(self):
        """
        Test JSON serialization and deserialization of CleanupResult.
        """
        now = datetime.now()
        cleanup_result = CleanupResult(
            task_id="test-task-serialization",
            is_success=True,
            cleaned_resources=["resource1", "resource2"],
            cleanup_duration=timedelta(seconds=15),
            cleanup_timestamp=now
        )
        
        # Convert to JSON dict
        json_data = cleanup_result.model_dump()
        
        # Validate JSON data
        assert json_data['task_id'] == "test-task-serialization"
        assert json_data['is_success'] is True
        assert json_data['cleaned_resources'] == ["resource1", "resource2"]
        assert isinstance(json_data['cleanup_duration'], float)  # timedelta serialized as float
        assert isinstance(json_data['cleanup_timestamp'], str)  # datetime serialized as ISO string

        # Deserialize from JSON
        reconstructed_result = CleanupResult.model_validate(json_data)
        assert reconstructed_result == cleanup_result


class TestBatchCleanupResult:
    def test_batch_cleanup_result_valid_creation(self):
        """
        Test creating a valid BatchCleanupResult with multiple CleanupResults.
        """
        now = datetime.now()
        cleanup_results = [
            CleanupResult(
                task_id="task-1",
                is_success=True,
                cleaned_resources=["resource1"],
                cleanup_duration=timedelta(seconds=5),
                cleanup_timestamp=now
            ),
            CleanupResult(
                task_id="task-2",
                is_success=False,
                cleaned_resources=[],
                error_message="Cleanup failed",
                cleanup_duration=timedelta(seconds=3),
                cleanup_timestamp=now
            )
        ]
        
        batch_result = BatchCleanupResult(
            cleanup_results=cleanup_results,
            batch_timestamp=now
        )
        
        assert len(batch_result.cleanup_results) == 2
        assert batch_result.batch_timestamp == now
        assert batch_result.cleanup_results[0].task_id == "task-1"
        assert batch_result.cleanup_results[1].task_id == "task-2"

    def test_batch_cleanup_result_validation_errors(self):
        """
        Test validation errors for BatchCleanupResult.
        """
        # Test empty cleanup_results
        with pytest.raises(ValidationError):
            BatchCleanupResult(
                cleanup_results=[],
                batch_timestamp=datetime.now()
            )

        # Test invalid input types
        with pytest.raises(ValidationError):
            BatchCleanupResult(
                cleanup_results=["not a CleanupResult"],  # Invalid type
                batch_timestamp=datetime.now()
            )

    def test_batch_cleanup_result_json_serialization(self):
        """
        Test JSON serialization and deserialization of BatchCleanupResult.
        """
        now = datetime.now()
        cleanup_results = [
            CleanupResult(
                task_id="task-serialization-1",
                is_success=True,
                cleaned_resources=["resource1"],
                cleanup_duration=timedelta(seconds=5),
                cleanup_timestamp=now
            )
        ]
        
        batch_result = BatchCleanupResult(
            cleanup_results=cleanup_results,
            batch_timestamp=now
        )
        
        # Convert to JSON dict
        json_data = batch_result.model_dump()
        
        # Validate JSON data
        assert len(json_data['cleanup_results']) == 1
        assert json_data['cleanup_results'][0]['task_id'] == "task-serialization-1"
        assert isinstance(json_data['batch_timestamp'], str)

        # Deserialize from JSON
        reconstructed_batch_result = BatchCleanupResult.model_validate(json_data)
        assert reconstructed_batch_result == batch_result