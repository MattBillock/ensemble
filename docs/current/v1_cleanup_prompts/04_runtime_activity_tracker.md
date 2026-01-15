# Prompt: Fix Runtime Activity Tracker

## Context

The activity tracker has two critical incomplete implementations:
1. Request filtering returns unfiltered data
2. Request cleanup is not implemented, causing memory growth

## Priority
CRITICAL - Memory leaks and incorrect data isolation

## Files to Modify

1. `src/runtime/agents/activity_tracker.py`

## Requirements

### Part 1: Fix Request Filtering in get_agent_hierarchy

**Location:** Around line 525
**Current Code:**
```python
def get_agent_hierarchy(self, request_id: Optional[str] = None) -> Dict[str, Any]:
    if not request_id:
        return self.agent_hierarchy
    # Filter by request_id
    # This would require storing request_id in hierarchy
    return self.agent_hierarchy  # RETURNS UNFILTERED!
```

**Fix:** The hierarchy needs to track request_id. Modify the data structure to support filtering:

```python
def get_agent_hierarchy(self, request_id: Optional[str] = None) -> Dict[str, Any]:
    if not request_id:
        return self.agent_hierarchy

    # Filter hierarchy to only include agents from this request
    filtered_hierarchy = {}
    for agent_id, agent_data in self.agent_hierarchy.items():
        if agent_data.get('request_id') == request_id:
            filtered_hierarchy[agent_id] = agent_data
    return filtered_hierarchy
```

**Also Required:** When agents are added to hierarchy, store request_id:
```python
def record_agent_started(self, agent_id: str, ..., request_id: str = None):
    # ... existing code ...
    self.agent_hierarchy[agent_id] = {
        # ... existing fields ...
        'request_id': request_id,
    }
```

### Part 2: Implement Request Cleanup

**Location:** Around line 543-550
**Current Code:**
```python
def clear_request(self, request_id: str):
    """Clear all data for a request."""
    # Remove activities
    self.activities = [a for a in self.activities if a.request_id != request_id]
    # Remove from hierarchy and states
    # (This is tricky without tracking request_id in hierarchy)
    # For now, we'll keep the data
```

**Fixed Code:**
```python
def clear_request(self, request_id: str):
    """Clear all data for a request."""
    # Remove activities for this request
    self.activities = [a for a in self.activities if a.request_id != request_id]

    # Remove from hierarchy
    agents_to_remove = [
        agent_id for agent_id, data in self.agent_hierarchy.items()
        if data.get('request_id') == request_id
    ]
    for agent_id in agents_to_remove:
        del self.agent_hierarchy[agent_id]
        # Also remove from agent_states if present
        if agent_id in self.agent_states:
            del self.agent_states[agent_id]

    # Remove from pending questions
    self.pending_questions = {
        qid: q for qid, q in self.pending_questions.items()
        if q.get('request_id') != request_id
    }

    logger.info(f"Cleared {len(agents_to_remove)} agents for request {request_id}")
```

### Part 3: Fix Answer Activity Missing Request ID

**Location:** Around line 321
**Current Code:**
```python
activity = Activity(
    ...
    request_id="",  # Would need to track this
)
```

**Fix:** Pass request_id through the answer recording:
```python
def record_answer(self, question_id: str, answer: str, request_id: str = None):
    """Record an answer to a pending question."""
    # ... existing code ...
    activity = Activity(
        ...
        request_id=request_id or "",
    )
```

### Part 4: Ensure All Recording Methods Accept request_id

Review and update these methods to properly pass request_id:
- `record_agent_started`
- `record_agent_completed`
- `record_agent_failed`
- `record_iteration_started`
- `record_iteration_completed`
- `record_tool_use_started`
- `record_tool_use_completed`
- `record_question`
- `record_answer`
- `record_file_generated`

All should accept `request_id` parameter and include it in the Activity object.

## Acceptance Criteria

1. `get_agent_hierarchy(request_id="abc")` returns only agents from that request
2. `clear_request(request_id="abc")` removes all traces of that request
3. Answer activities have proper request_id
4. No memory growth for completed requests after cleanup
5. Filtering works correctly for multi-request scenarios

## Test Plan

1. Start the system and submit two different problems
2. Call `get_agent_hierarchy(request_id=<first_request>)`
3. Verify only agents from first request are returned
4. Call `clear_request(request_id=<first_request>)`
5. Verify hierarchy no longer contains first request's agents
6. Verify activities list doesn't contain first request's data
7. Memory usage should decrease after cleanup

## Notes

- Be careful with thread safety when modifying shared dictionaries
- Consider using copy-on-write for filtering if performance is concern
- Log cleanup actions for debugging
- Don't break existing functionality for callers that don't pass request_id
