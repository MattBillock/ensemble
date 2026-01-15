import pytest
from unittest.mock import Mock, patch
import asyncio
import sys
from typing import List, Dict

# Assuming the ActivityTracker will be imported from the specified path
sys.path.append('src/runtime/agents')
from activity_tracker import ActivityTracker

@pytest.fixture
def mock_activity_tracker():
    """Fixture to create a fresh ActivityTracker instance for each test."""
    return ActivityTracker()

def test_cleanup_empty_tracker(mock_activity_tracker):
    """
    Test cleanup behavior when the activity tracker is initially empty.
    
    Expected behavior:
    - No errors should be raised
    - Internal data structures remain in a valid state
    """
    mock_activity_tracker.cleanup()
    assert len(mock_activity_tracker._active_requests) == 0
    assert len(mock_activity_tracker._completed_requests) == 0

@pytest.mark.parametrize("request_count", [10, 100, 1000])
def test_cleanup_with_multiple_requests(mock_activity_tracker, request_count):
    """
    Test cleanup with multiple requests in various states.
    
    Verifies:
    - Can handle large number of requests
    - Removes completed and stale requests
    - Maintains internal consistency
    """
    # Populate tracker with mock requests
    for i in range(request_count):
        mock_request = Mock()
        mock_request.is_completed = i % 3 == 0  # Mark some as completed
        mock_request.is_stale = i % 4 == 0  # Mark some as stale
        mock_activity_tracker._active_requests[f'request_{i}'] = mock_request

    mock_activity_tracker.cleanup()
    
    # Verify cleanup removed completed and stale requests
    remaining_requests = mock_activity_tracker._active_requests
    assert len(remaining_requests) < request_count
    assert all(not req.is_completed and not req.is_stale for req in remaining_requests.values())

@pytest.mark.asyncio
async def test_concurrent_cleanup():
    """
    Test concurrent cleanup to ensure thread-safety and prevent race conditions.
    
    Verifies:
    - Multiple cleanup operations can be initiated concurrently
    - No data corruption or unexpected state changes
    """
    tracker = ActivityTracker()
    
    # Simulate concurrent cleanup attempts
    cleanup_tasks = [
        asyncio.create_task(tracker.cleanup()) 
        for _ in range(5)
    ]
    
    await asyncio.gather(*cleanup_tasks)
    
    # Verify no unexpected side effects from concurrent cleanups
    assert len(tracker._active_requests) == 0
    assert len(tracker._completed_requests) == 0

def test_request_filtering_by_age(mock_activity_tracker):
    """
    Test filtering of requests based on age/timestamp.
    
    Verifies:
    - Can filter out requests older than a specified threshold
    - Preserves recent and relevant requests
    """
    # Create mock requests with different timestamps
    now = asyncio.get_event_loop().time()
    old_request = Mock(timestamp=now - 3600)  # 1 hour old
    recent_request = Mock(timestamp=now - 60)  # 1 minute old
    
    mock_activity_tracker._active_requests = {
        'old': old_request,
        'recent': recent_request
    }
    
    mock_activity_tracker.cleanup(max_age=1800)  # 30 minutes threshold
    
    # Verify only recent requests remain
    assert len(mock_activity_tracker._active_requests) == 1
    assert 'recent' in mock_activity_tracker._active_requests

@pytest.mark.performance
def test_cleanup_performance_large_dataset():
    """
    Performance test for cleanup with large number of requests.
    
    Verifies:
    - Cleanup operation remains efficient with large datasets
    - No significant performance degradation
    """
    tracker = ActivityTracker()
    
    # Populate with a large number of mock requests
    for i in range(10000):
        mock_request = Mock()
        mock_request.is_completed = i % 10 == 0
        tracker._active_requests[f'request_{i}'] = mock_request
    
    # Measure cleanup time
    start_time = asyncio.get_event_loop().time()
    tracker.cleanup()
    cleanup_time = asyncio.get_event_loop().time() - start_time
    
    assert cleanup_time < 0.5  # Should complete within 500ms
    assert len(tracker._active_requests) < 10000

def test_memory_leak_prevention(mock_activity_tracker):
    """
    Test that cleanup prevents memory leaks by removing unnecessary references.
    
    Verifies:
    - Completed and stale requests are fully removed
    - No lingering references that could cause memory growth
    """
    # Create requests that should be cleaned up
    for i in range(100):
        mock_request = Mock()
        mock_request.is_completed = True
        mock_activity_tracker._active_requests[f'request_{i}'] = mock_request
    
    initial_memory = sys.getsizeof(mock_activity_tracker._active_requests)
    mock_activity_tracker.cleanup()
    cleanup_memory = sys.getsizeof(mock_activity_tracker._active_requests)
    
    assert cleanup_memory < initial_memory
    assert len(mock_activity_tracker._active_requests) == 0

def test_error_handling_during_cleanup(mock_activity_tracker):
    """
    Verify robust error handling during cleanup operations.
    
    Ensures:
    - Errors in individual request cleanup do not crash entire process
    - Failed request removals are logged or handled gracefully
    """
    # Create some requests with potential cleanup errors
    def create_problematic_request(should_raise=False):
        mock_request = Mock()
        if should_raise:
            mock_request.cleanup = Mock(side_effect=Exception("Cleanup error"))
        mock_request.is_completed = True
        return mock_request
    
    mock_activity_tracker._active_requests = {
        'normal': create_problematic_request(False),
        'problematic': create_problematic_request(True)
    }
    
    # Should not raise unhandled exceptions
    mock_activity_tracker.cleanup()
    
    # Verify tracker remains in a consistent state
    assert len(mock_activity_tracker._active_requests) < 2