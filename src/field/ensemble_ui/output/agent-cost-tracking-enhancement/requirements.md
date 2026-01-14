# Requirements: Agent Cost Tracking Enhancement

## Vision
Enhance the ensemble UI to display cost estimates, execution duration, and model information for each agent task. This will provide better visibility into agent performance and resource usage.

## Objectives
1. Display execution cost estimates for each agent in the agent summary
2. Show start time, completion time, and duration of execution
3. Tag each agent with the model it used during execution
4. Ensure data flows from backend tracking to frontend display

## Scope

### In Scope
1. **Backend Enhancements**:
   - Capture start time, end time, and duration for agent executions
   - Track the model used by each agent (from AgentRuntime)
   - Calculate cost estimates based on token usage and model pricing
   - Include this data in activity tracking and agent states

2. **Frontend Enhancements**:
   - Display cost estimate in AgentSummaryPane component
   - Show execution duration (started → completed)
   - Display model tag/badge for each agent
   - Format costs in a user-friendly way (e.g., "$0.0042")
   - Format durations in appropriate units (ms, seconds, minutes)

3. **Data Flow**:
   - Extend Activity Tracker to capture cost and model data
   - Update API endpoints to return this information
   - Update AgentSummaryPane to consume and display the data

### Out of Scope
- Historical cost aggregation/reporting (future feature)
- Budget alerts or limits (future feature)
- Per-tool cost breakdown (future feature)
- Real-time cost streaming during execution (will show on completion)

## Technical Constraints
- Must work with existing activity_tracker.py system
- Should integrate with existing AgentRuntime metrics
- Frontend changes limited to AgentSummaryPane component
- Backend must be backward compatible with existing agent executions

## Success Criteria
1. ✅ Each completed agent shows:
   - Start time (ISO format or relative time)
   - Completion time (ISO format or relative time)
   - Duration (e.g., "2.3s", "1m 45s")
   - Cost estimate (e.g., "$0.0042")
   - Model tag (e.g., "claude-3-5-sonnet-20241022")

2. ✅ Data is captured reliably from backend
3. ✅ UI displays information in a readable, compact format
4. ✅ No performance degradation to existing functionality

## Assumptions
1. AgentRuntime already tracks token usage and model selection
2. Model pricing information is available (from model_selector.py or similar)
3. Activity tracker can be extended without breaking existing consumers
4. Frontend has access to activity data via WebSocket or polling

## User Stories
1. **As a developer**, I want to see how much each agent execution costs so I can optimize expensive operations
2. **As a developer**, I want to see execution duration so I can identify slow agents
3. **As a developer**, I want to see which model was used so I can correlate performance with model choice

## Technical Approach

### Backend Changes
1. Extend `record_agent_completed()` in activity_tracker.py to accept:
   - `started_at`: ISO timestamp
   - `completed_at`: ISO timestamp  
   - `duration_ms`: milliseconds
   - `model_used`: model identifier
   - `cost_estimate`: float (USD)

2. Update AgentRuntime to:
   - Track start time on initialization
   - Calculate cost based on token usage and model pricing
   - Pass this data to activity tracker on completion

3. Update API response in main.py to include these fields in agent state

### Frontend Changes
1. Update AgentSummaryPane.jsx to:
   - Display execution timeline (started → completed)
   - Show duration badge
   - Show cost estimate badge
   - Show model tag
   - Handle formatting for readability

### Data Structure
```javascript
// Expected agent info structure
{
  agent_id: "exec_dir_1",
  type: "executive_director",
  status: "completed",
  started_at: "2024-01-13T10:30:00Z",
  completed_at: "2024-01-13T10:30:42Z",
  duration_ms: 42000,
  model_used: "claude-3-5-sonnet-20241022",
  cost_estimate: 0.0042,
  // ... existing fields
}
```

## Implementation Notes
- Cost calculation should use actual token counts from Claude API responses
- If token counts unavailable, estimate based on character counts with clear "~" prefix
- Duration should handle both running (show elapsed) and completed states
- Model tags should be shortened for display (e.g., "sonnet-3.5" instead of full name)
