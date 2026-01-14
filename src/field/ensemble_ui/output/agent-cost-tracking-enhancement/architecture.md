# Architecture: Agent Cost Tracking Enhancement

## Overview
This document outlines the architecture for enhancing the ensemble UI to display cost estimates, execution duration, and model information for each agent task.

## System Context

### Current Architecture
The system has:
- **Backend**: Activity tracking via `activity_tracker.py` that monitors agent execution
- **API Layer**: WebSocket/REST endpoints in `main.py` that expose agent state
- **Frontend**: React-based UI with `AgentSummaryPane.jsx` displaying agent information
- **Agent Runtime**: `AgentRuntime` managing agent execution with Claude API

### Enhancement Goals
Add cost and timing metrics to the existing activity tracking and display pipeline.

---

## Component Architecture

### 1. Backend Components

#### 1.1 Activity Tracker Extension (`activity_tracker.py`)
**Current State**: Tracks agent lifecycle, tool usage, iterations, and status changes

**Enhancements**:
- Extend `record_agent_started()` to capture:
  - `started_at`: ISO timestamp
  - `model_used`: Model identifier from AgentRuntime
- Extend `record_agent_completed()` to capture:
  - `completed_at`: ISO timestamp
  - `duration_ms`: Calculated duration in milliseconds
  - `cost_estimate`: Calculated cost in USD
  - `token_usage`: Input/output tokens used

**Data Structure Changes**:
```python
# Enhanced agent_hierarchy entry
{
    "agent_id": str,
    "agent_name": str,
    "agent_type": str,
    "status": str,
    "started_at": str,  # ISO timestamp
    "completed_at": str,  # ISO timestamp (optional)
    "duration_ms": int,  # milliseconds (optional)
    "model_used": str,  # e.g., "claude-3-5-sonnet-20241022"
    "cost_estimate": float,  # USD (optional)
    "token_usage": {  # optional
        "input_tokens": int,
        "output_tokens": int,
        "total_tokens": int
    }
}
```

#### 1.2 Cost Calculator (New Module: `cost_calculator.py`)
**Purpose**: Calculate cost estimates based on token usage and model pricing

**Responsibilities**:
- Maintain model pricing table (per-token costs)
- Calculate cost from token usage
- Handle different model families (Sonnet, Opus, Haiku)
- Provide estimation when exact token counts unavailable

**Interface**:
```python
class CostCalculator:
    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost in USD"""
        pass
    
    def estimate_cost_from_chars(
        self,
        model: str,
        input_chars: int,
        output_chars: int
    ) -> float:
        """Estimate cost when token counts unavailable"""
        pass
```

**Model Pricing Table** (as of Jan 2024):
```python
MODEL_PRICING = {
    "claude-3-5-sonnet-20241022": {
        "input": 0.003 / 1000,  # $3 per million tokens
        "output": 0.015 / 1000   # $15 per million tokens
    },
    "claude-3-opus-20240229": {
        "input": 0.015 / 1000,
        "output": 0.075 / 1000
    },
    "claude-3-haiku-20240307": {
        "input": 0.00025 / 1000,
        "output": 0.00125 / 1000
    }
}
```

#### 1.3 AgentRuntime Integration
**Current State**: Manages agent execution, tracks iterations and tool use

**Enhancements**:
- Capture start time on initialization
- Extract model identifier from configuration
- Extract token usage from Claude API responses
- Calculate cost using `CostCalculator`
- Pass metrics to `activity_tracker` on completion

**Implementation Points**:
- In `__init__`: Record start time
- In `_process_response()`: Extract token usage from API response
- In completion/failure: Calculate duration and cost, pass to activity tracker

---

### 2. API Layer

#### 2.1 WebSocket/REST Endpoints (`main.py`)
**Current State**: Provides endpoints for agent state and activity data

**Enhancements**:
- Include new fields in agent state responses:
  - `started_at`, `completed_at`, `duration_ms`
  - `model_used`, `cost_estimate`, `token_usage`
- Ensure backward compatibility (new fields optional)

**Response Format**:
```json
{
  "agent_id": "exec_dir_1",
  "agent_name": "Executive Director",
  "agent_type": "executive_director",
  "status": "completed",
  "started_at": "2024-01-13T10:30:00.123Z",
  "completed_at": "2024-01-13T10:30:42.456Z",
  "duration_ms": 42333,
  "model_used": "claude-3-5-sonnet-20241022",
  "cost_estimate": 0.0042,
  "token_usage": {
    "input_tokens": 1200,
    "output_tokens": 350,
    "total_tokens": 1550
  },
  "current_task": "Completed",
  "children": []
}
```

---

### 3. Frontend Components

#### 3.1 AgentSummaryPane Enhancement (`AgentSummaryPane.jsx`)
**Current State**: Displays agent name, type, status, current task

**Enhancements**:
Add display sections for:
1. **Execution Timeline**: Start → End times (relative or absolute)
2. **Duration Badge**: Formatted duration (e.g., "2.3s", "1m 45s")
3. **Cost Badge**: Formatted cost (e.g., "$0.0042")
4. **Model Tag**: Shortened model name (e.g., "Sonnet 3.5")

**Layout Design**:
```
┌─────────────────────────────────────────┐
│ 🤖 Executive Director                   │
│ Status: ✅ Completed                     │
│                                         │
│ ⏱️ 2.3s  💰 $0.0042  🏷️ Sonnet 3.5     │
│                                         │
│ Started: 10:30:00                       │
│ Completed: 10:30:02                     │
│                                         │
│ Current Task: Completed                 │
└─────────────────────────────────────────┘
```

**Utility Functions**:
```javascript
// Format duration
function formatDuration(durationMs) {
  if (durationMs < 1000) return `${durationMs}ms`;
  if (durationMs < 60000) return `${(durationMs / 1000).toFixed(1)}s`;
  const mins = Math.floor(durationMs / 60000);
  const secs = ((durationMs % 60000) / 1000).toFixed(0);
  return `${mins}m ${secs}s`;
}

// Format cost
function formatCost(costUsd) {
  if (costUsd === null || costUsd === undefined) return 'N/A';
  if (costUsd < 0.0001) return '<$0.0001';
  return `$${costUsd.toFixed(4)}`;
}

// Shorten model name
function formatModelName(model) {
  if (model.includes('sonnet')) return 'Sonnet 3.5';
  if (model.includes('opus')) return 'Opus';
  if (model.includes('haiku')) return 'Haiku';
  return model;
}
```

---

## Data Flow

### 1. Agent Execution Start
```
AgentRuntime.__init__()
  ↓
Record start_time
  ↓
activity_tracker.record_agent_started(
  agent_id, agent_name, agent_type, model_used, started_at
)
  ↓
Update agent_hierarchy and agent_states
  ↓
Emit to WebSocket
  ↓
Frontend receives agent state
  ↓
AgentSummaryPane displays "Running" with start time
```

### 2. Agent Execution Completion
```
AgentRuntime completes
  ↓
Extract token_usage from API response
  ↓
Calculate duration_ms = now - start_time
  ↓
CostCalculator.calculate_cost(model, tokens)
  ↓
activity_tracker.record_agent_completed(
  agent_id, completed_at, duration_ms, cost_estimate, token_usage
)
  ↓
Update agent_hierarchy and agent_states
  ↓
Emit to WebSocket
  ↓
Frontend receives updated agent state
  ↓
AgentSummaryPane displays metrics badges
```

---

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: Existing activity_tracker system
- **API**: WebSocket/REST (existing)
- **New Module**: `cost_calculator.py`

### Frontend
- **Framework**: React
- **Component**: `AgentSummaryPane.jsx`
- **Styling**: Existing CSS/styling system

---

## Design Decisions

### 1. Cost Calculation Strategy
**Decision**: Calculate cost at agent completion time
**Rationale**: 
- Token counts only available after API response
- Avoids streaming cost updates (complexity)
- Matches milestone scope (show on completion)

### 2. Token Usage Source
**Decision**: Extract from Claude API response `usage` field
**Rationale**:
- Most accurate source
- Already available in API responses
- Fallback to estimation if unavailable

### 3. Model Pricing Storage
**Decision**: Hardcode pricing in `cost_calculator.py`
**Rationale**:
- Pricing changes infrequently
- Simple to update
- Future: Could load from config file

### 4. Duration Precision
**Decision**: Store in milliseconds, display with appropriate units
**Rationale**:
- Milliseconds provide precision
- Display formatting adapts to duration length
- Easy to aggregate for analytics later

### 5. Backward Compatibility
**Decision**: All new fields optional in API responses
**Rationale**:
- Existing consumers won't break
- Graceful degradation if data missing
- Frontend checks for field existence

---

## Non-Functional Requirements

### Performance
- Cost calculation: < 1ms per agent
- No impact on agent execution speed
- Activity tracker overhead: < 5% of execution time

### Reliability
- Handle missing token usage gracefully
- Fallback to estimation when needed
- Never crash agent execution due to tracking failures

### Maintainability
- Model pricing centralized and easy to update
- Clear separation of concerns (tracking, calculation, display)
- Well-documented data structures

---

## Testing Strategy

### Unit Tests
1. **CostCalculator**:
   - Test cost calculation for each model
   - Test estimation fallback
   - Test edge cases (zero tokens, unknown model)

2. **ActivityTracker**:
   - Test new fields captured correctly
   - Test backward compatibility
   - Test data structure updates

### Integration Tests
1. **End-to-End Flow**:
   - Agent execution → cost calculation → API → Frontend
   - Verify metrics display correctly
   - Test with different models

2. **API Tests**:
   - Verify new fields in responses
   - Test backward compatibility
   - Test WebSocket updates

### Frontend Tests
1. **Component Tests**:
   - Test duration formatting
   - Test cost formatting
   - Test model name shortening
   - Test missing data handling

---

## Security Considerations

### Data Privacy
- Cost data not sensitive but could reveal usage patterns
- No additional authentication required (existing auth applies)

### Input Validation
- Validate token counts are non-negative
- Validate duration is non-negative
- Handle malformed model names gracefully

---

## Deployment Strategy

### Phase 1: Backend (Milestone 1)
- Deploy `cost_calculator.py`
- Update `activity_tracker.py`
- Update `AgentRuntime` integration
- Test with existing agents

### Phase 2: API (Milestone 2)
- Update API responses
- Test backward compatibility
- Deploy to staging

### Phase 3: Frontend (Milestone 3)
- Update `AgentSummaryPane.jsx`
- Test display formatting
- Deploy to production

### Rollback Plan
- Backend changes backward compatible
- Frontend can gracefully handle missing fields
- Can rollback each phase independently

---

## Future Enhancements

### Out of Current Scope
1. **Historical Analytics**:
   - Cost aggregation by agent type
   - Cost trends over time
   - Budget tracking

2. **Budget Controls**:
   - Alert when cost exceeds threshold
   - Pause execution on budget limit
   - Per-project cost limits

3. **Detailed Breakdown**:
   - Per-tool cost attribution
   - Cost by iteration
   - Cost heatmaps

4. **Real-Time Streaming**:
   - Stream cost updates during execution
   - Live token counting
   - Incremental cost display

---

## Appendix

### A. File Locations
- Backend: `/src/runtime/agents/activity_tracker.py`
- New Module: `/src/runtime/agents/cost_calculator.py`
- AgentRuntime: `/src/runtime/agents/runtime.py` (or similar)
- API: `/src/field/ensemble_ui/main.py`
- Frontend: `/src/field/ensemble_ui/frontend/src/components/AgentSummaryPane.jsx`

### B. Model Pricing Reference
Updated pricing at: https://www.anthropic.com/pricing

### C. Claude API Token Usage Format
```json
{
  "usage": {
    "input_tokens": 1200,
    "output_tokens": 350
  }
}
```
