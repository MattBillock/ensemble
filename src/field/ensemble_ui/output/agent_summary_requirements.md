# Agent Summary Report Requirements

## Project Vision
Add comprehensive summary reports for each completed agent task, making it visible in the UI so users can understand what each agent accomplished.

## Context
The Ensemble UI currently displays agent status, logs, and results, but lacks a structured summary report showing what work was completed by each agent. Users need a clear, concise overview of each agent's accomplishments to track progress and understand the execution flow.

## Core Objectives
1. **Display Agent Summaries**: Show a structured summary for each completed agent task
2. **Integrate with Activity Tracking**: Leverage the existing activity tracker system to capture and display summaries
3. **UI Visibility**: Make summaries easily accessible and readable in the frontend
4. **Structured Format**: Provide consistent, informative summaries across all agent types

## Functional Requirements

### Backend Requirements
1. **Capture Summary Data**
   - Extract summary information from agent results when available
   - Support `summary` field in agent result JSON
   - Support `self_analysis` field for agent's self-assessment
   - Support `performance_analysis` field for performance metrics
   - Support `deliverables` list showing files/artifacts created

2. **Activity Tracker Enhancement**
   - Record summary data when agent completes
   - Store summaries in agent state
   - Make summaries queryable via API

3. **API Endpoints**
   - Enhance `/api/activity/states/{agent_id}` to include summary
   - Add summary field to WebSocket status updates
   - Include summary in `/api/agents` list response

### Frontend Requirements
1. **AgentSummaryPane Component**
   - Create dedicated component to display agent summaries
   - Show summary for completed agents
   - Display key metrics (duration, files created, status)
   - Support markdown rendering for summary text

2. **Integration Points**
   - Add summary section to `AgentStatusPane`
   - Show summary in agent hierarchy tooltips
   - Display in activity feed when agent completes

3. **Summary Display Format**
   - **Header**: Agent name, type, execution time
   - **Status Badge**: Success/failure indicator
   - **Summary Text**: Main accomplishment description
   - **Deliverables**: List of files/artifacts created
   - **Metrics**: Token usage, cost, duration
   - **Self-Analysis**: Agent's performance assessment (if available)

## Technical Design

### Data Structure
```json
{
  "agent_id": "exec_dir_1",
  "agent_name": "executive_director",
  "status": "completed",
  "summary": {
    "status": "success",
    "phase": "complete",
    "summary": "Project completed successfully with all deliverables",
    "deliverables": [
      "/path/to/requirements.md",
      "/path/to/implementation.py"
    ],
    "self_analysis": "Successfully completed task with high quality",
    "performance_analysis": "All spawned agents performed efficiently",
    "duration_ms": 45000,
    "token_usage": {
      "input_tokens": 5000,
      "output_tokens": 2000
    },
    "cost_usd": 0.15
  }
}
```

### Backend Changes

#### 1. Activity Tracker Enhancement
**File**: `src/runtime/agents/activity_tracker.py`

Add summary field to `record_agent_completed`:
```python
def record_agent_completed(
    self,
    agent_id: str,
    agent_name: str,
    request_id: str,
    result: Optional[Dict[str, Any]] = None,
    summary: Optional[Dict[str, Any]] = None  # NEW
):
    # Store summary in agent_states
    if agent_id in self.agent_states:
        self.agent_states[agent_id]["summary"] = summary
```

#### 2. Backend API Enhancement
**File**: `src/field/ensemble_ui/backend/main.py`

Enhance `_execute_agent_background` to extract and store summary:
```python
# After agent execution
result = runtime.execute(input_data)

# Extract summary information
summary = {
    "status": result.get("status", "unknown"),
    "phase": result.get("phase", "unknown"),
    "summary": result.get("summary", ""),
    "deliverables": result.get("deliverables", []),
    "self_analysis": result.get("self_analysis", ""),
    "performance_analysis": result.get("performance_analysis", ""),
    "duration_ms": duration_ms,
    # Add token/cost metrics if available
}

# Store in agent info
self.active_agents[agent_id]["summary"] = summary
```

### Frontend Changes

#### 1. Create AgentSummaryPane Component
**File**: `src/field/ensemble_ui/frontend/src/components/AgentSummaryPane.jsx`

New component to display agent summaries:
```jsx
function AgentSummaryPane({ summary, agentName, agentType }) {
  return (
    <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-white">Summary</h4>
        <StatusBadge status={summary.status} />
      </div>
      
      {/* Summary text with markdown support */}
      <div className="prose prose-invert prose-sm max-w-none mb-3">
        <ReactMarkdown>{summary.summary}</ReactMarkdown>
      </div>
      
      {/* Deliverables list */}
      {summary.deliverables && summary.deliverables.length > 0 && (
        <div className="mb-3">
          <p className="text-xs font-semibold text-blue-300 mb-1">
            Deliverables ({summary.deliverables.length})
          </p>
          <ul className="text-sm text-gray-300 space-y-1">
            {summary.deliverables.map((file, idx) => (
              <li key={idx}>📄 {file}</li>
            ))}
          </ul>
        </div>
      )}
      
      {/* Metrics */}
      <div className="flex gap-4 text-xs text-gray-400">
        {summary.duration_ms && (
          <span>⏱️ {(summary.duration_ms / 1000).toFixed(1)}s</span>
        )}
        {summary.cost_usd && (
          <span>💰 ${summary.cost_usd.toFixed(4)}</span>
        )}
      </div>
    </div>
  );
}
```

#### 2. Integrate into AgentStatusPane
**File**: `src/field/ensemble_ui/frontend/src/components/AgentStatusPane.jsx`

Add summary display in the agent details:
```jsx
{agentInfo.status === 'completed' && agentInfo.summary && (
  <AgentSummaryPane
    summary={agentInfo.summary}
    agentName={agentInfo.type}
    agentType={agentInfo.type}
  />
)}
```

#### 3. Add to Agent Hierarchy
**File**: `src/field/ensemble_ui/frontend/src/components/AgentHierarchyTree.jsx`

Show summary tooltip on completed agents:
```jsx
// In agent node rendering
{agent.status === 'completed' && agent.summary && (
  <Tooltip content={agent.summary.summary}>
    <CheckIcon className="text-green-500" />
  </Tooltip>
)}
```

## Success Criteria

### Must Have
- ✅ Backend captures summary from agent results
- ✅ Summary stored in agent state and accessible via API
- ✅ UI displays summary for completed agents
- ✅ Summary includes status, description, and deliverables
- ✅ Summary visible in agent status pane

### Should Have
- ✅ Markdown rendering support for summary text
- ✅ Display execution metrics (time, cost)
- ✅ Show deliverables as clickable file links
- ✅ Self-analysis and performance analysis displayed

### Nice to Have
- Summary comparison across multiple agents
- Export summaries as report
- Filter/search summaries in activity feed

## Testing Requirements

### Backend Tests
1. Test summary extraction from agent results
2. Test activity tracker summary storage
3. Test API endpoint returns summary
4. Test WebSocket broadcasts include summary

### Frontend Tests
1. Test AgentSummaryPane renders correctly
2. Test markdown rendering in summary
3. Test deliverables list display
4. Test metrics formatting
5. Test integration with AgentStatusPane

## Implementation Phases

### Phase 1: Backend Foundation (2-3 hours)
1. Enhance activity tracker to store summaries
2. Update backend to extract and store summary from results
3. Modify API responses to include summary
4. Add tests for summary functionality

### Phase 2: Frontend Display (2-3 hours)
1. Create AgentSummaryPane component
2. Integrate into AgentStatusPane
3. Add styling and markdown support
4. Add tests for component

### Phase 3: Integration & Polish (1-2 hours)
1. Add summary to agent hierarchy
2. Update WebSocket to broadcast summaries
3. Add summary to activity feed
4. End-to-end testing

## Risks and Mitigations

### Risk: Agent results may not always include summary
**Mitigation**: Provide default summary based on status and logs if summary field is missing

### Risk: Large summaries may impact performance
**Mitigation**: Truncate or paginate very long summaries; limit storage to recent summaries

### Risk: Inconsistent summary format across agents
**Mitigation**: Define standard summary schema; validate on backend

## Dependencies
- Existing activity tracker system
- Current backend API structure
- Frontend component library (React, Tailwind)
- Markdown rendering library (react-markdown)

## Out of Scope
- Real-time summary updates during execution (only on completion)
- Summary editing or annotation by users
- Historical summary analysis or trends
- Summary comparison between runs

## Assumptions
1. Agents will include `summary` field in their result JSON
2. Executive Director and Development Manager follow output format spec
3. Summary text is reasonable length (<5000 chars)
4. Deliverables are file paths relative to project root
5. UI can handle missing summary fields gracefully

## Questions for User
None - requirements are clear and implementation is straightforward given existing architecture.
