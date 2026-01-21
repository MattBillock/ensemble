# Requirements: Continuation of Unfinished Ensemble UI Enhancements

## Executive Summary
This document consolidates all unfinished requirements from the Ensemble UI project that need complete implementation including code, unit tests, and documentation.

## Priority 1: Agent Completion Summary Visibility (CRITICAL)

### Problem Statement
When agents complete, users cannot see what they accomplished without clicking through expandable sections. The completion summary, self_analysis, and deliverables data exists but is not exposed to the frontend.

### Current State Analysis
- **Backend (main.py)**: Stores `result` in `active_agents[agent_id]` on completion (line ~233)
- **Activity Tracker**: `record_agent_completed()` stores result in activity data but does NOT extract summary/deliverables to agent_states
- **Frontend (App.jsx)**: Shows status badge but no summary text for completed agents
- **Frontend (ActivityFeed.jsx)**: Shows generic "completed" without summary

### Required Changes

#### 1. Backend: activity_tracker.py - `record_agent_completed()` 
**Location**: `src/runtime/agents/activity_tracker.py` (~line 363)

**Change**: Extract summary, self_analysis, deliverables from result and store in agent_states

```python
def record_agent_completed(
    self,
    agent_id: str,
    agent_name: str,
    request_id: str,
    result: Optional[Dict[str, Any]] = None
):
    """Record agent completion."""
    # Existing activity recording...
    
    # ADD: Extract summary fields to agent_states for frontend access
    if agent_id in self.agent_states:
        self.agent_states[agent_id]["status"] = "completed"
        self.agent_states[agent_id]["completed_at"] = activity.timestamp
        
        # NEW: Extract key fields from result for UI display
        if result:
            self.agent_states[agent_id]["summary"] = result.get("summary", "")
            self.agent_states[agent_id]["self_analysis"] = result.get("self_analysis", "")
            self.agent_states[agent_id]["deliverables"] = result.get("deliverables", [])
            self.agent_states[agent_id]["message"] = result.get("message", "")
```

#### 2. Frontend: App.jsx - Agent Tasks Section
**Location**: `frontend/src/App.jsx` (~line 430-480 area where agent states are rendered)

**Change**: Add summary display below completed agent status

```jsx
{/* After status badge, add for completed agents: */}
{state.status === 'completed' && state.summary && (
  <div style={{ 
    fontSize: '12px', 
    color: '#9ca3af', 
    marginTop: '6px',
    padding: '6px 8px',
    backgroundColor: '#1a1a2e',
    borderRadius: '4px',
    borderLeft: '3px solid #10b981'
  }}>
    📝 {state.summary.slice(0, 200)}{state.summary.length > 200 ? '...' : ''}
  </div>
)}
{state.status === 'completed' && state.deliverables && state.deliverables.length > 0 && (
  <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '4px' }}>
    📁 {state.deliverables.length} deliverable(s) created
  </div>
)}
```

#### 3. Frontend: ActivityFeed.jsx - agent_completed case
**Location**: `frontend/src/components/ActivityFeed.jsx` - `renderActivityDetails` switch case

**Change**: Show summary in collapsed view for agent_completed activities

```jsx
case 'agent_completed':
  return (
    <div>
      {data.result?.summary && (
        <div style={{ marginBottom: '8px', color: '#9ca3af' }}>
          <strong>Summary:</strong> {data.result.summary}
        </div>
      )}
      {data.result?.deliverables?.length > 0 && (
        <div style={{ marginBottom: '8px' }}>
          <strong>📁 Deliverables:</strong> {data.result.deliverables.length} file(s)
          <ul style={{ margin: '4px 0', paddingLeft: '20px', fontSize: '11px' }}>
            {data.result.deliverables.slice(0, 5).map((d, i) => (
              <li key={i}>{d}</li>
            ))}
            {data.result.deliverables.length > 5 && (
              <li>...and {data.result.deliverables.length - 5} more</li>
            )}
          </ul>
        </div>
      )}
      {/* Existing expandable details... */}
    </div>
  );
```

### Unit Tests Required

#### Test: activity_tracker_test.py
```python
def test_record_agent_completed_stores_summary():
    """Verify summary fields are extracted to agent_states on completion."""
    tracker = ActivityTracker()
    
    # Setup agent state
    tracker.agent_states["test_agent"] = {"status": "running"}
    
    # Complete with result containing summary
    result = {
        "status": "success",
        "summary": "Implemented feature X with Y approach",
        "self_analysis": "Performance was good",
        "deliverables": ["file1.py", "file2.py"]
    }
    
    tracker.record_agent_completed(
        agent_id="test_agent",
        agent_name="test",
        request_id="req123",
        result=result
    )
    
    state = tracker.agent_states["test_agent"]
    assert state["summary"] == "Implemented feature X with Y approach"
    assert state["self_analysis"] == "Performance was good"
    assert state["deliverables"] == ["file1.py", "file2.py"]

def test_record_agent_completed_handles_missing_summary():
    """Verify graceful handling when result has no summary."""
    tracker = ActivityTracker()
    tracker.agent_states["test_agent"] = {"status": "running"}
    
    tracker.record_agent_completed(
        agent_id="test_agent",
        agent_name="test",
        request_id="req123",
        result={"status": "success"}  # No summary
    )
    
    state = tracker.agent_states["test_agent"]
    assert state.get("summary", "") == ""
    assert state.get("deliverables", []) == []
```

#### Test: Frontend Component Tests
```jsx
// App.test.jsx additions
test('renders summary for completed agent', () => {
  const agentStates = {
    'agent1': {
      status: 'completed',
      summary: 'Completed task successfully',
      deliverables: ['file1.py', 'file2.py']
    }
  };
  // Verify summary text is rendered
  // Verify deliverables count is shown
});

// ActivityFeed.test.jsx additions
test('shows summary in agent_completed activity', () => {
  const activity = {
    activity_type: 'agent_completed',
    data: {
      result: {
        summary: 'Task completed',
        deliverables: ['output.md']
      }
    }
  };
  // Verify summary is visible without expansion
});
```

### Acceptance Criteria
1. ✓ When agent completes, summary text visible in Agent Tasks section without clicking
2. ✓ Deliverable count shown with icon (📁 3 deliverables)
3. ✓ Activity Feed shows summary preview for agent_completed events
4. ✓ Graceful fallback when summary not available
5. ✓ Unit tests pass with >80% coverage for new code
6. ✓ No regressions in existing functionality

---

## Priority 2: Hide Completed Toggle Enhancement (PARTIALLY DONE)

### Current State
- Toggle exists in App.jsx (`hideCompleted` state)
- NOT persisted to localStorage
- NOT available in ActivityFeed, GeneratedFiles panes

### Required Changes

#### 1. Add localStorage persistence
```jsx
// In App.jsx useEffect on mount
useEffect(() => {
  const savedHideCompleted = localStorage.getItem('hideCompleted');
  if (savedHideCompleted !== null) {
    setHideCompleted(savedHideCompleted === 'true');
  }
}, []);

// When toggle changes
const handleHideCompletedChange = (e) => {
  const value = e.target.checked;
  setHideCompleted(value);
  localStorage.setItem('hideCompleted', value.toString());
};
```

#### 2. Add toggle to ActivityFeed component
Pass `hideCompleted` prop and filter completed activities when enabled.

#### 3. Add toggle to GeneratedFiles component
Filter files from completed agents when toggle is enabled.

---

## Priority 3: Agent Invocation Context Display (FROM requirements.md)

### Required Changes
1. Capture invocation context when agents spawn (activity_tracker)
2. Display invocation description in AgentHierarchyTree, AgentStatusPane, AgentSummaryPane
3. Show what task each agent was specifically invoked to accomplish

### Implementation deferred to after Priority 1 completion

---

## Success Criteria for Full Completion
1. All Priority 1 changes implemented with tests
2. All Priority 2 changes implemented with tests  
3. Integration verified with live agent execution
4. No console errors or warnings
5. Documentation updated
6. Git commit with all changes

## Files to Modify
- `src/runtime/agents/activity_tracker.py`
- `frontend/src/App.jsx`
- `frontend/src/components/ActivityFeed.jsx`
- `frontend/src/components/GeneratedFiles.jsx` (Priority 2)

## Files to Create
- `src/runtime/agents/tests/test_activity_tracker_summary.py`
- `frontend/src/components/ActivityFeed.test.jsx` (if not exists)
