# Agent Completion Visibility - Milestone Plan

## Project Overview
Make agent completion results visible in the UI so users can see what each bot actually did. Currently, completion summaries are hidden behind expandable sections - users need to see them prominently without clicks.

## Milestone 1: Backend Data Enhancement
**Objective**: Ensure summary, self_analysis, and deliverables from agent output are properly stored and exposed to UI.

**Deliverables**:
- Update `activity_tracker.py` to extract and store summary fields when agent completes
- Ensure `/api/activity/states` endpoint returns summary, self_analysis, deliverables

**Acceptance Criteria**:
- Agent completion stores summary in agent_states
- API returns these fields when queried
- No breaking changes to existing behavior

**Dependencies**: None

## Milestone 2: Frontend UI Updates
**Objective**: Display agent completion summaries prominently in UI without requiring user clicks.

**Deliverables**:
- Update App.jsx Agent Tasks section to show summary below completed agents
- Update ActivityFeed.jsx to show summary in collapsed view for agent_completed activities
- Display deliverable counts with expand option

**Acceptance Criteria**:
- Completed agents show 1-2 sentence summary immediately visible
- Deliverable count shown (e.g., "📁 3 deliverables")
- Activity feed shows summary preview without expansion
- Graceful fallback when summary not available

**Dependencies**: Milestone 1

## Milestone 3: Testing & Polish
**Objective**: Verify all changes work correctly and handle edge cases.

**Deliverables**:
- Manual testing with actual agent completions
- Handle edge cases (missing summary, long text, no deliverables)
- Final UI polish and consistency check

**Acceptance Criteria**:
- All user stories satisfied
- No visual regressions
- Works with agents that don't return summary (fallback text)

**Dependencies**: Milestone 2

## Priority: HIGH
This directly impacts user experience and understanding of system behavior.

## Related Files
- `frontend/src/App.jsx` - Agent Tasks section (~lines 400-460)
- `frontend/src/components/ActivityFeed.jsx` - renderActivityDetails function  
- `backend/main.py` - Not needed for this change (already stores result)
- `src/runtime/agents/activity_tracker.py` - record_agent_completed function
