import pytest
from src.exceptions import GitSyncBaseException, GitSyncError, ErrorCode

class TestGitSyncExceptions:
    def test_base_exception_structure(self):
        """
        Verify that the base GitSync exception has the expected structure
        and can be instantiated with required parameters.
        """
        # Arrange
        error_code = ErrorCode.SYNC_FAILED
        message = "Git synchronization failed"
        context = {"repo": "test-repo", "branch": "main"}
        
        # Act
        exception = GitSyncBaseException(
            message=message, 
            error_code=error_code, 
            context=context
        )
        
        # Assert
        assert isinstance(exception, Exception)
        assert str(exception) == message
        assert exception.error_code == error_code
        assert exception.context == context

    def test_exception_inheritance(self):
        """
        Verify that custom Git sync exceptions inherit correctly
        and maintain expected exception characteristics.
        """
        # Arrange
        error_code = ErrorCode.MERGE_CONFLICT
        message = "Merge conflict detected"
        
        # Act
        git_sync_error = GitSyncError(
            message=message, 
            error_code=error_code
        )
        
        # Assert
        assert isinstance(git_sync_error, GitSyncBaseException)
        assert isinstance(git_sync_error, Exception)
        assert str(git_sync_error) == message
        assert git_sync_error.error_code == error_code

    def test_error_code_generation(self):
        """
        Verify that error codes are correctly generated and mapped
        for different types of Git sync exceptions.
        """
        # Arrange
        test_cases = [
            (ErrorCode.SYNC_FAILED, "Synchronization failed"),
            (ErrorCode.MERGE_CONFLICT, "Merge conflict"),
            (ErrorCode.AUTHENTICATION_ERROR, "Authentication failed")
        ]
        
        # Act & Assert
        for error_code, message in test_cases:
            exception = GitSyncBaseException(
                message=message, 
                error_code=error_code
            )
            assert exception.error_code == error_code
            assert exception.error_code.name in str(exception.error_code)