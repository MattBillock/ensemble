# Recovery Dashboard Visibility & Stateful Persistence

## Problem Statement
1. **Recovery Visibility**: Recovered agents don't appear in the dashboard as first-class citizens
2. **State Loss**: Process restarts or memory issues cause loss of all swarm state
3. **No Historical Context**: Cannot see what prompts were submitted, their status, or results

## Current State Analysis

### What We Have
- `~/.ensemble/projects/` contains project tracking JSON files
- Activity tracker stores agent states in memory only
- Recovery system can restart failed agents but they don't integrate with UI
- Generated markdown files contain some context but aren't queryable

### What We're Missing
- Persistent storage of complete swarm state
- Dashboard integration for recovered agents
- Prompt history and status tracking
- Automatic state reload on backend restart

## Requirements

### Part 1: Persistent Swarm State

#### 1.1 Data Model
Store the following for each swarm session:

```python
SwarmSession:
  session_id: str           # UUID
  started_at: datetime
  prompt: str               # Original user prompt
  budget_tier: str          # economical/balanced/full_firepower
  status: str               # running/completed/failed/paused
  project_id: str           # Link to project tracking
  family_name: str          # Agent family (new feature)

  # Metrics
  total_cost: float
  total_tokens: int
  duration_ms: int

  # Agent tracking
  agents: Dict[str, AgentState]
  hierarchy: Dict           # Parent-child relationships

  # Results
  deliverables: List[str]   # Generated file paths
  summary: str              # Final summary
  errors: List[str]         # Any errors encountered

AgentState:
  agent_id: str
  agent_type: str
  whimsical_name: str
  family_name: str
  status: str               # running/completed/failed
  started_at: datetime
  completed_at: datetime
  iterations: int
  max_iterations: int
  model_used: str
  cost: float
  input_tokens: int
  output_tokens: int
  current_task: str
  summary: str
  self_analysis: str
  parent_id: str            # For hierarchy reconstruction
```

#### 1.2 Storage Backend
- Use SQLite for persistent storage (already have agent_metrics.db)
- Tables: `swarm_sessions`, `agent_states`, `activities`
- JSON fields for complex nested data
- Automatic schema migrations

#### 1.3 Persistence Points
- Save state on:
  - Agent spawn
  - Agent completion/failure
  - Iteration milestone (every 5 iterations)
  - Tool use completion
  - Question asked/answered
  - Process shutdown (graceful)

### Part 2: Recovery Dashboard Integration

#### 2.1 On Backend Startup
1. Load all incomplete sessions from database
2. Reconstruct agent states into memory
3. Mark sessions as "recovered" with original state preserved
4. Display recovered agents in dashboard immediately

#### 2.2 Recovered Agent Display
- Show with special indicator (e.g., "Recovered" badge)
- Display original prompt and context
- Show what was completed vs pending
- Allow user to:
  - Resume execution
  - Mark as abandoned
  - View full history

#### 2.3 API Endpoints
```
GET  /api/sessions                    # List all sessions (active + historical)
GET  /api/sessions/{id}               # Get session details
GET  /api/sessions/{id}/agents        # Get agents for session
POST /api/sessions/{id}/resume        # Resume recovered session
POST /api/sessions/{id}/abandon       # Mark session as abandoned

GET  /api/history                     # Paginated prompt history
GET  /api/history/{prompt_id}/status  # Status of specific prompt
```

### Part 3: Dashboard UI Changes

#### 3.1 Session List View
Add a "Sessions" or "History" tab showing:
- All swarm sessions (current and historical)
- Status indicator (running/completed/failed/recovered)
- Original prompt (truncated)
- Start time and duration
- Cost and agent count
- Click to expand details

#### 3.2 Recovered Session Card
```
┌────────────────────────────────────────────┐
│ 🔄 RECOVERED SESSION                       │
│ Prompt: "Implement token tracking..."      │
│ Started: 2 hours ago | Cost: $0.45        │
│ Progress: 3/5 agents completed            │
│                                           │
│ [Resume] [View Details] [Abandon]         │
└────────────────────────────────────────────┘
```

#### 3.3 Status Indicators
- 🟢 Running - Active execution
- ✅ Completed - Successfully finished
- ❌ Failed - Execution failed
- 🔄 Recovered - Loaded from persistence, needs action
- ⏸️ Paused - Waiting for user input

### Part 4: Graceful Shutdown

#### 4.1 Shutdown Procedure
1. Detect SIGTERM/SIGINT signals
2. Mark all running agents as "interrupted"
3. Save current state to database
4. Complete any pending database writes
5. Exit cleanly

#### 4.2 Crash Recovery
- Database transactions ensure atomic writes
- On crash, last persisted state is recovered
- Some in-flight operations may be lost (acceptable)

## Implementation Plan

### Phase 1: Database Schema (Backend)
1. Create SQLite tables for sessions and agent states
2. Add persistence hooks to ActivityTracker
3. Implement save/load functions
4. Add graceful shutdown handling

### Phase 2: Recovery Integration (Backend)
1. Load state on backend startup
2. Reconstruct agent hierarchy
3. Mark recovered sessions appropriately
4. Add API endpoints for session management

### Phase 3: Dashboard Integration (Frontend)
1. Add sessions/history view
2. Display recovered sessions
3. Implement resume/abandon actions
4. Add status indicators throughout UI

## Acceptance Criteria
1. Backend restart preserves all swarm state
2. Recovered agents appear in dashboard immediately after restart
3. Users can resume or abandon recovered sessions
4. Full prompt history accessible via UI
5. No data loss on graceful shutdown
6. Crash recovery restores last known state
7. Performance impact minimal (<100ms startup overhead)

## Files to Modify/Create

### New Files
- `src/runtime/agents/persistence.py` - State persistence layer
- `src/runtime/agents/session_manager.py` - Session lifecycle management
- Database migration scripts

### Modified Files
- `src/runtime/agents/activity_tracker.py` - Add persistence hooks
- `src/field/ensemble_ui/backend/main.py` - Add API endpoints, startup recovery
- Frontend components for session display

## Out of Scope
- Distributed state (multi-node persistence)
- Real-time sync between instances
- State export/import functionality
