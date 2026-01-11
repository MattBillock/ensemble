# Smart Task Decomposition Engine - Architecture Design

## Overview
The Smart Task Decomposition Engine transforms complex user requests into optimized, parallel execution plans with resource estimation and continuous learning.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Frontend (React)                                │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    TaskDecompositionViewer.jsx                     │  │
│  │  - Mermaid dependency graph                                        │  │
│  │  - Resource estimates display                                      │  │
│  │  - Execution wave visualization                                    │  │
│  │  - Approve/Reject/Modify actions                                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                                 │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Endpoints:                                                        │  │
│  │  - POST /api/decompose                                             │  │
│  │  - POST /api/approve-plan                                          │  │
│  │  - GET /api/decomposition-history                                  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Core Decomposition Engine                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                  TaskDecompositionEngine                         │    │
│  │  decomposition_engine.py                                         │    │
│  │                                                                   │    │
│  │  Methods:                                                         │    │
│  │  - analyze_task() → TaskAnalysis                                  │    │
│  │  - decompose_task() → DecompositionPlan                          │    │
│  │  - generate_dependency_graph() → nx.DiGraph                      │    │
│  │  - estimate_resources() → ResourceEstimate                        │    │
│  │  - optimize_allocation() → AllocationPlan                         │    │
│  │  - generate_execution_schedule() → Schedule                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│                                    ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                   DecompositionLearner                           │    │
│  │  decomposition_learner.py                                        │    │
│  │                                                                   │    │
│  │  Methods:                                                         │    │
│  │  - record_execution()                                             │    │
│  │  - improve_estimates() → CalibrationReport                        │    │
│  │  - suggest_improvements()                                         │    │
│  │  - get_historical_accuracy() → AccuracyMetrics                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Existing Ensemble Infrastructure                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│  │  AgentRuntime     │  │  AgentMetrics    │  │  ModelSelector   │       │
│  │  runtime.py       │  │  metrics.py      │  │  model_selector  │       │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Models (Pydantic)

### Core Models

```python
# Task Analysis
class TaskAnalysis(BaseModel):
    complexity_score: int  # 1-10 scale
    domain: str  # e.g., "fullstack_web_app", "data_pipeline"
    estimated_human_hours: float
    key_requirements: List[str]
    risk_factors: List[str] = []

# Sub-Task
class SubTask(BaseModel):
    task_id: str
    description: str
    agent_type: str  # backend_lead, frontend_lead, etc.
    estimated_duration_minutes: int
    complexity: str  # simple, medium, complex
    dependencies: List[str] = []  # task_ids this depends on
    priority: int = 1  # 1 = highest

# Decomposition Plan
class DecompositionPlan(BaseModel):
    task_analysis: TaskAnalysis
    sub_tasks: List[SubTask]
    dependency_graph: Dict[str, List[str]]  # Serialized DAG

# Resource Estimate
class ResourceEstimate(BaseModel):
    agent_count: int
    peak_concurrent: int
    model_distribution: Dict[str, str]  # task_id -> model
    estimated_tokens: int
    estimated_cost: float
    critical_path_duration_minutes: int
    parallelization_factor: float

# Allocation Plan
class AllocationPlan(BaseModel):
    task_assignments: Dict[str, str]  # task_id -> agent_id
    model_selections: Dict[str, str]  # task_id -> model
    resource_utilization: float  # 0-1

# Execution Wave
class ExecutionWave(BaseModel):
    wave_number: int
    task_ids: List[str]
    estimated_duration_minutes: int

# Schedule
class Schedule(BaseModel):
    waves: List[ExecutionWave]
    total_duration_minutes: int
    estimated_start: datetime
    estimated_end: datetime

# Full Execution Plan
class ExecutionPlan(BaseModel):
    id: str
    user_request: str
    task_analysis: TaskAnalysis
    decomposition_plan: DecompositionPlan
    resource_estimate: ResourceEstimate
    allocation_plan: AllocationPlan
    schedule: Schedule
    created_at: datetime
    status: str  # pending_approval, approved, rejected, executing, completed
```

## Algorithm Design

### Task Analysis Algorithm
1. Use LLM to classify task domain and identify requirements
2. Calculate complexity based on:
   - Number of distinct components (frontend, backend, database, etc.)
   - Integration complexity (number of dependencies)
   - Technical risk factors
3. Estimate human hours based on similar historical tasks

### Decomposition Algorithm
1. **Hierarchical Decomposition**:
   - Goals: High-level objectives
   - Tasks: Specific deliverables (30-40 minute chunks)
   - Actions: Atomic operations
2. **Domain-Specific Patterns**:
   - Web App: DB Schema → API → Frontend → Integration → Deploy
   - Data Pipeline: Source → Transform → Load → Validate
3. **Dependency Inference**:
   - Use keyword matching and LLM assistance
   - Apply standard patterns (e.g., frontend depends on API)

### DAG Generation
```python
def generate_dependency_graph(sub_tasks: List[SubTask]) -> nx.DiGraph:
    G = nx.DiGraph()
    for task in sub_tasks:
        G.add_node(task.task_id, **task.dict())
        for dep in task.dependencies:
            G.add_edge(dep, task.task_id)
    
    # Validate DAG (no cycles)
    if not nx.is_directed_acyclic_graph(G):
        raise ValueError("Dependency graph contains cycles")
    
    return G
```

### Resource Estimation
- Agent count: Based on parallel paths in DAG
- Model selection: Based on task complexity
  - Simple tasks: Haiku ($0.25/1M tokens)
  - Complex tasks: Sonnet ($3/1M tokens)
- Token estimation: Based on task type and historical data
- Cost: Sum of (tokens * model_rate) for each task

### Optimization (Linear Programming)
Using PuLP to minimize:
- Objective: Minimize total cost subject to time constraints
- Constraints:
  - Maximum concurrent agents
  - Task dependencies respected
  - Budget limits

### Execution Scheduling
1. Topological sort of DAG
2. Group tasks into waves (tasks that can run in parallel)
3. Calculate wave durations based on longest task

## File Structure

```
src/
├── runtime/
│   └── agents/
│       ├── decomposition_engine.py    # NEW: Core engine
│       ├── decomposition_learner.py   # NEW: Learning module
│       ├── runtime.py                 # Existing
│       └── metrics.py                 # Existing (extend)
└── field/
    └── ensemble_ui/
        ├── backend/
        │   └── main.py                # Add new endpoints
        └── frontend/
            └── src/
                └── components/
                    └── TaskDecompositionViewer.jsx  # NEW

tests/
└── test_decomposition.py              # NEW: Test suite

TASK_DECOMPOSITION.md                   # NEW: Documentation
```

## Integration Points

### With Existing Metrics (metrics.py)
- Use `AgentMetricsTracker` for historical performance data
- Store decomposition accuracy metrics in same SQLite DB
- Add new table: `decomposition_history`

### With Model Selector (model_selector.py)
- Use for intelligent model assignment per task
- Respect budget tiers in optimization

### With Agent Runtime (runtime.py)
- Execute scheduled tasks through runtime
- Track actual vs. estimated performance

## API Contracts

### POST /api/decompose
```json
Request:
{
  "user_request": "Build a todo app with React frontend..."
}

Response:
{
  "plan_id": "uuid",
  "task_analysis": {...},
  "dependency_graph": {...},
  "execution_schedule": {...},
  "resource_estimate": {...},
  "mermaid_diagram": "graph TD; ..."
}
```

### POST /api/approve-plan
```json
Request:
{
  "plan_id": "uuid",
  "action": "approve|reject|modify",
  "modifications": {...}  // Optional
}

Response:
{
  "status": "approved|rejected|modified",
  "execution_id": "uuid"  // If approved
}
```

### GET /api/decomposition-history
```json
Response:
{
  "total_plans": 50,
  "avg_accuracy": 0.85,
  "recent_plans": [...]
}
```

## Performance Considerations

1. **Decomposition Speed**: Target < 5 seconds
   - Use async LLM calls
   - Cache common patterns
   
2. **Graph Operations**: O(V + E) for most operations
   - NetworkX is suitable for < 100 tasks
   
3. **Optimization**: PuLP suitable for < 100 variables
   - Use timeout for complex problems

## Error Handling

1. **Cycle Detection**: Fail fast with clear error
2. **LLM Failures**: Fallback to simple sequential plan
3. **Resource Constraints**: Warn user, suggest alternatives
4. **Invalid Input**: Validate with Pydantic, return helpful errors
