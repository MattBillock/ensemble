# Requirements: Agent Completion Summary Visibility

## Vision
Make agent completion results visible in the UI so users can see what each bot actually did. When agents complete, their summary should be prominently displayed - not hidden behind expandable sections.

## Problem Statement
User reports: "Bots show completed, but I don't see any UI changes. What was the status of the last task?"

The current system:
1. Agents produce structured outputs with `summary`, `self_analysis`, `deliverables` fields
2. These are stored in `result` data when agent completes  
3. BUT: The UI only shows "Completed" status - the actual summary is hidden in expandable detail sections
4. User cannot easily see what each agent accomplished without clicking through multiple levels

## Objectives
1. Display agent completion summaries prominently in the Agent Tasks section
2. Show two-sentence summary of what each agent did when it completes
3. Make deliverables list visible for completed agents
4. Enhance Activity Feed to highlight completion summaries
5. Provide better communication between bots and user

## Scope

### In Scope
- **Agent Tasks Section Enhancement**
  - When agent status is "completed", show summary text prominently below the status
  - Display up to 2-3 key points from `result.summary` or `result.self_analysis`
  - Show count of deliverables (e.g., "Created 3 files") with option to expand
  - Add visual indication that detailed info is available (e.g., info icon)

- **Activity Feed Enhancement**
  - For `agent_completed` activities, show summary text in the collapsed view
  - Make completion entries more informative without requiring expansion
  - Include deliverable count in activity entry

- **Agent State Storage Enhancement**  
  - Ensure `summary`, `self_analysis`, and `deliverables` from agent output are stored in agent_states
  - These fields should be accessible via `/api/activity/states` endpoint

### Out of Scope
- Real-time streaming of agent output (future enhancement)
- Notification system for completions
- Historical summary browsing
- Detailed cost/token display in summary

## User Stories

### Story 1: View Completion Summary
**As a** user monitoring agent progress  
**I want to** see a summary of what each agent accomplished when it completes  
**So that** I understand what happened without digging through logs

**Acceptance Criteria:**
- When agent status changes to "completed", a 1-2 sentence summary appears below the status badge
- Summary is visible without clicking or expanding anything
- If no summary is available, show "Completed successfully" or similar default

### Story 2: See Deliverables at a Glance
**As a** user tracking project output  
**I want to** see what files/artifacts each agent produced  
**So that** I know what to look for in the Generated Files section

**Acceptance Criteria:**
- Completed agents show deliverable count (e.g., "📁 3 deliverables")
- Clicking reveals the list of deliverable paths
- Links to corresponding entries in Generated Files section (if applicable)

### Story 3: Activity Feed Context
**As a** user reviewing activity history  
**I want to** see completion context in the Activity Feed  
**So that** I can scan through and understand what happened without expanding each item

**Acceptance Criteria:**
- Agent completion activities show first line of summary in preview
- Still expandable for full details
- Clear visual distinction for completion events

## Technical Requirements

### Data Flow (Existing - needs exposure to UI)
```
Agent Output → {
  status: "success",
  summary: "What was accomplished",
  self_analysis: "Performance reflection",
  deliverables: ["path1.md", "path2.py"],
  ...
}

↓ stored in ↓

activity_tracker.record_agent_completed(result={...})
agent_states[agent_id] = { status: "completed", ... }

↓ exposed via ↓

GET /api/activity/states → { agent_states: { agent_id: {...} } }
```

### Frontend Changes Needed

**App.jsx - Agent Tasks Section:**
```jsx
// After status badge, add:
{state.status === 'completed' && state.summary && (
  <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '6px' }}>
    📝 {state.summary.slice(0, 150)}...
  </div>
)}
{state.status === 'completed' && state.deliverables?.length > 0 && (
  <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '4px' }}>
    📁 {state.deliverables.length} deliverable(s)
  </div>
)}
```

**ActivityFeed.jsx - Completion Display:**
```jsx
case 'agent_completed':
  return (
    <div>
      {data.result?.summary && (
        <div style={{ marginBottom: '8px' }}>
          <strong>Summary:</strong> {data.result.summary}
        </div>
      )}
      {data.result?.deliverables?.length > 0 && (
        <div>
          <strong>Deliverables:</strong> {data.result.deliverables.length} file(s)
        </div>
      )}
      // ...existing detail expansion
    </div>
  );
```

### Backend Changes Needed

**backend/main.py - _execute_agent_background():**
Ensure result fields are stored in active_agents state:
```python
self.active_agents[agent_id]["status"] = "completed"
self.active_agents[agent_id]["result"] = result
# ADD: Extract key summary fields for easy access
self.active_agents[agent_id]["summary"] = result.get("summary", "")
self.active_agents[agent_id]["self_analysis"] = result.get("self_analysis", "")
self.active_agents[agent_id]["deliverables"] = result.get("deliverables", [])
```

**activity_tracker.py - record_agent_completed():**
Extract and store summary in agent_states:
```python
def record_agent_completed(self, agent_id, agent_name, request_id, result=None):
    # ... existing code ...
    
    # Update agent state with summary info
    if agent_id in self.agent_states:
        self.agent_states[agent_id]["summary"] = result.get("summary", "") if result else ""
        self.agent_states[agent_id]["deliverables"] = result.get("deliverables", []) if result else []
```

## Success Criteria
1. **Visibility**: Agent completion summaries visible without any clicks
2. **Informativeness**: User can understand what happened at a glance
3. **Non-disruptive**: Changes don't break existing functionality
4. **Graceful degradation**: Works when summary fields are missing (shows default text)

## Testing Requirements
1. Start a task and let agents complete
2. Verify summary text appears in Agent Tasks section for completed agents
3. Verify Activity Feed shows summary in agent_completed entries
4. Verify deliverable count displays correctly
5. Test with agents that don't return summary (should show fallback)

## Implementation Notes
- Keep changes minimal - enhance existing components rather than replacing
- Use existing styling patterns for consistency
- Summary text should truncate gracefully if too long
- Consider adding "Show more" link for full self_analysis

## Related Files
- `frontend/src/App.jsx` - Agent Tasks section (~lines 400-460)
- `frontend/src/components/ActivityFeed.jsx` - renderActivityDetails function
- `backend/main.py` - _execute_agent_background function
- `src/runtime/agents/activity_tracker.py` - record_agent_completed function

## Priority: HIGH
This directly impacts user experience and understanding of system behavior.
