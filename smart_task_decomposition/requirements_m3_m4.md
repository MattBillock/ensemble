# Smart Task Decomposition Engine - Milestones 3 & 4 Requirements

## Overview
Complete the Smart Task Decomposition Engine by implementing the Learning Module (M3) and API Endpoints (M4) to enable historical tracking, estimate improvement, and web service integration.

## Current State
- ✅ Milestone 1: Core Decomposition Engine (COMPLETE)
  - TaskDecompositionEngine implemented in `src/runtime/agents/decomposition_engine.py`
  - All methods functional: analyze_task(), decompose_task(), generate_dependency_graph()
  - 16/16 tests passing in `tests/test_decomposition_engine.py`

- ✅ Milestone 2: Resource Optimization (COMPLETE)
  - estimate_resources(), optimize_allocation(), generate_execution_schedule() implemented
  - Linear programming optimization working
  - Parallel execution scheduling operational

## Milestone 3: Learning Module

### Objective
Build the DecompositionLearner to track execution history, calculate accuracy, and improve estimates over time.

### Deliverables
1. **New Module**: `src/runtime/agents/decomposition_learner.py`
2. **Database Integration**: Use existing SQLite infrastructure from `src/runtime/agents/metrics.py`
3. **Unit Tests**: `tests/test_decomposition_learner.py`

### Required Methods

#### 1. record_execution()
```python
def record_execution(
    self,
    decomposition_plan: DecompositionPlan,
    actual_execution: Dict[str, Any]
) -> None:
    """
    Record completed execution data to database.
    
    Args:
        decomposition_plan: The original plan
        actual_execution: Dict with:
            - actual_duration_mins: int
            - actual_cost_usd: float
            - actual_tokens: int
            - task_outcomes: Dict[task_id, outcome]
            - completed_at: str (ISO timestamp)
    """
```

**Acceptance Criteria**:
- Data persisted to SQLite database
- Stores both estimated and actual metrics
- Returns success/failure status
- Handles database errors gracefully

#### 2. improve_estimates()
```python
def improve_estimates(
    self,
    task_description: str,
    current_estimate_mins: int
) -> int:
    """
    Improve estimate based on historical data.
    
    Args:
        task_description: Description of the task
        current_estimate_mins: Current estimate
        
    Returns:
        Improved estimate in minutes
    """
```

**Acceptance Criteria**:
- Queries historical data for similar tasks
- Calculates adjustment factor based on past accuracy
- Returns adjusted estimate
- Falls back to current estimate if no history

#### 3. suggest_improvements()
```python
def suggest_improvements(
    self,
    decomposition_plan: DecompositionPlan
) -> List[str]:
    """
    Suggest improvements based on historical patterns.
    
    Returns:
        List of improvement suggestions
    """
```

**Acceptance Criteria**:
- Analyzes plan against historical patterns
- Identifies common bottlenecks or inefficiencies
- Returns actionable suggestions
- Empty list if no suggestions

#### 4. get_historical_accuracy()
```python
def get_historical_accuracy(
    self,
    domain: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get accuracy metrics from historical data.
    
    Args:
        domain: Filter by domain (backend/frontend/etc)
        limit: Max records to analyze
        
    Returns:
        Dict with accuracy metrics:
        - avg_duration_accuracy: float (0-1)
        - avg_cost_accuracy: float (0-1)
        - total_executions: int
        - accuracy_trend: List[float] (recent accuracy)
    """
```

**Acceptance Criteria**:
- Queries database for historical executions
- Calculates accuracy metrics
- Returns structured data
- Handles empty database gracefully

### Database Schema
Add to existing metrics database:

```sql
CREATE TABLE IF NOT EXISTS decomposition_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,
    domain TEXT NOT NULL,
    estimated_duration_mins INTEGER NOT NULL,
    actual_duration_mins INTEGER NOT NULL,
    estimated_cost_usd REAL NOT NULL,
    actual_cost_usd REAL NOT NULL,
    estimated_tokens INTEGER NOT NULL,
    actual_tokens INTEGER NOT NULL,
    task_count INTEGER NOT NULL,
    completed_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_domain ON decomposition_executions(domain);
CREATE INDEX IF NOT EXISTS idx_completed_at ON decomposition_executions(completed_at);
```

### Testing Requirements
- Unit tests for each method
- Test database initialization
- Test data persistence and retrieval
- Test accuracy calculations with sample data
- Test edge cases (empty database, invalid data)
- Coverage > 80%

---

## Milestone 4: API Endpoints

### Objective
Create FastAPI endpoints to expose decomposition engine functionality via REST API.

### Deliverables
1. **New Endpoints in**: `src/field/ensemble_ui/backend/main.py`
2. **Integration Tests**: `tests/backend/test_decomposition_api.py`

### Endpoint Specifications

#### 1. POST /api/decompose
**Purpose**: Analyze and decompose a user request into tasks.

**Request Body**:
```json
{
  "request": "string (user's task description)",
  "options": {
    "include_schedule": true,
    "include_resource_estimate": true
  }
}
```

**Response**:
```json
{
  "success": true,
  "plan": {
    "analysis": { ... },
    "sub_tasks": [ ... ],
    "total_estimated_duration_mins": 120,
    "critical_path_duration_mins": 90,
    "parallelization_opportunities": 3,
    "dependency_layers": 4
  },
  "resource_estimate": {
    "total_agents_needed": 5,
    "agents_by_type": { ... },
    "estimated_total_cost_usd": 0.12,
    "estimated_tokens": 12000,
    "peak_concurrent_agents": 2,
    "estimated_wall_clock_mins": 90
  },
  "schedule": {
    "phases": [ ... ],
    "start_time": "2024-01-01T10:00:00",
    "estimated_completion_time": "2024-01-01T11:30:00",
    "critical_path": ["task_1", "task_2", "task_3"]
  }
}
```

**Acceptance Criteria**:
- Accepts plain text task description
- Returns complete DecompositionPlan JSON
- Includes resource estimate and schedule if requested
- Responds within 5 seconds
- Returns 400 for invalid requests
- Returns 500 for internal errors with details

#### 2. POST /api/approve-plan
**Purpose**: Handle user approval/rejection of decomposition plan.

**Request Body**:
```json
{
  "plan_id": "string",
  "action": "approve|reject|modify",
  "modifications": {
    // Optional: modified plan details
  }
}
```

**Response**:
```json
{
  "success": true,
  "action": "approve",
  "execution_started": true,
  "message": "Plan approved and execution initiated"
}
```

**Acceptance Criteria**:
- Handles all three actions (approve/reject/modify)
- For approve: initiates execution (placeholder for now)
- For reject: logs rejection reason if provided
- For modify: validates modifications and returns updated plan
- Returns appropriate status codes (200/400/404)

#### 3. GET /api/decomposition-history
**Purpose**: Return historical accuracy metrics.

**Query Parameters**:
- `domain` (optional): Filter by domain
- `limit` (optional, default=100): Max records

**Response**:
```json
{
  "success": true,
  "metrics": {
    "avg_duration_accuracy": 0.87,
    "avg_cost_accuracy": 0.92,
    "total_executions": 45,
    "accuracy_trend": [0.75, 0.80, 0.85, 0.87]
  },
  "recent_executions": [
    {
      "plan_id": "abc123",
      "domain": "backend",
      "estimated_duration_mins": 120,
      "actual_duration_mins": 135,
      "completed_at": "2024-01-01T12:00:00"
    }
  ]
}
```

**Acceptance Criteria**:
- Returns accuracy metrics from DecompositionLearner
- Includes recent execution details
- Supports domain filtering
- Returns empty metrics if no history
- Responds within 1 second

### Integration Requirements
- Use existing FastAPI app instance in main.py
- Follow existing endpoint patterns
- Use Pydantic models for request/response validation
- Add proper error handling and logging
- Add OpenAPI documentation tags

### Testing Requirements
- Integration tests for each endpoint
- Test all request validation
- Test error handling (invalid input, missing data)
- Test with real DecompositionEngine
- Mock database for learner tests
- Coverage > 80%

---

## Technical Constraints

1. **No Breaking Changes**: Don't modify existing TaskDecompositionEngine
2. **Database**: Use existing SQLite patterns from metrics.py
3. **Async-Friendly**: Learning updates should not block execution
4. **Error Handling**: Comprehensive logging and graceful degradation
5. **Testing**: TDD approach - write tests first
6. **Documentation**: Docstrings for all public methods

## Success Criteria

### Milestone 3 Complete When:
- [x] DecompositionLearner class implemented
- [x] All 4 methods functional and tested
- [x] Database schema created and migrations work
- [x] Historical data persists correctly
- [x] Accuracy calculations verified with test data
- [x] All unit tests pass (target: 15+ tests)

### Milestone 4 Complete When:
- [x] All 3 endpoints implemented in main.py
- [x] Request/response Pydantic models defined
- [x] Full integration with DecompositionEngine
- [x] Error handling comprehensive
- [x] All API tests pass (target: 10+ tests)
- [x] OpenAPI docs generated correctly

---

## Architecture Notes

### Code Organization
```
src/
├── runtime/
│   └── agents/
│       ├── decomposition_engine.py (existing - M1/M2)
│       ├── decomposition_learner.py (new - M3)
│       └── metrics.py (existing - reuse patterns)
├── field/
│   └── ensemble_ui/
│       └── backend/
│           └── main.py (modify - M4)
tests/
├── test_decomposition_engine.py (existing)
├── test_decomposition_learner.py (new - M3)
└── backend/
    └── test_decomposition_api.py (new - M4)
```

### Dependencies
- TaskDecompositionEngine (existing)
- metrics.py database patterns (existing)
- FastAPI app instance (existing)
- Pydantic v2+ (existing)

### Performance Targets
- Decomposition: < 5 seconds
- History query: < 1 second
- Database writes: < 100ms
- API response time: < 100ms overhead

---

## References

- Milestone Plan: `smart_task_decomposition/milestone_plan.md`
- Existing Engine: `src/runtime/agents/decomposition_engine.py`
- Existing Tests: `tests/test_decomposition_engine.py`
- Backend Main: `src/field/ensemble_ui/backend/main.py`
- Metrics Module: `src/runtime/agents/metrics.py`
