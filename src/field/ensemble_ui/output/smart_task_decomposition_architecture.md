# Smart Task Decomposition Engine - Architecture Document

## 1. System Overview

The Smart Task Decomposition Engine is an intelligent planning layer that sits between user requests and the Ensemble AI execution pipeline. It transforms high-level user requirements into optimized, dependency-aware execution plans.

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER REQUEST                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              TASK DECOMPOSITION ENGINE                           │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│  │ Task Analyzer │─▶│ Decomposer    │─▶│ Resource Estimator│   │
│  └───────────────┘  └───────────────┘  └───────────────────┘   │
│         │                  │                     │              │
│         ▼                  ▼                     ▼              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│  │ TaskAnalysis  │  │ DAG Generator │  │ AllocationOptimizer│   │
│  └───────────────┘  └───────────────┘  └───────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│                    ┌───────────────────┐                       │
│                    │ Schedule Generator │                       │
│                    └───────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 USER APPROVAL (UI)                               │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│  │ Mermaid Graph │  │ Cost Estimate │  │ Action Buttons    │   │
│  └───────────────┘  └───────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│             EXECUTION (Development Manager + Agents)             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              DECOMPOSITION LEARNER                               │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│  │ Record Exec   │  │ Calibrate Est │  │ Suggest Improve   │   │
│  └───────────────┘  └───────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Core Components

### 2.1 Task Decomposition Engine (`decomposition_engine.py`)

**Purpose**: Core engine for analyzing, decomposing, and scheduling tasks.

**Classes**:

```python
# Pydantic Models
class TaskAnalysis(BaseModel):
    complexity_score: int  # 1-10
    domain: str  # "frontend", "backend", "fullstack_web_app", etc.
    estimated_human_hours: float
    key_requirements: List[str]

class SubTask(BaseModel):
    task_id: str
    description: str
    agent_type: str  # "backend_lead", "frontend_lead", etc.
    estimated_duration_min: int  # Target: 30-40 min
    complexity: str  # "simple", "moderate", "complex"
    dependencies: List[str]  # task_ids this depends on

class DecompositionPlan(BaseModel):
    task_analysis: TaskAnalysis
    sub_tasks: List[SubTask]
    dependency_graph: Dict  # Serialized graph

class ResourceEstimate(BaseModel):
    agent_count: int
    model_distribution: Dict[str, str]  # task_id -> model
    estimated_tokens: int
    estimated_cost: float
    critical_path_duration: int  # minutes
    parallelization_factor: float

class AllocationPlan(BaseModel):
    task_assignments: Dict[str, str]  # task_id -> agent_type
    model_selections: Dict[str, str]  # task_id -> model
    resource_utilization: float

class Schedule(BaseModel):
    waves: List[List[str]]  # List of parallel task groups
    total_duration: int  # minutes
    estimated_start_end_times: Dict[str, Tuple[int, int]]

# Main Engine
class TaskDecompositionEngine:
    def __init__(self, metrics_db: Optional[MetricsTracker] = None)
    def analyze_task(self, user_request: str) -> TaskAnalysis
    def decompose_task(self, task_analysis: TaskAnalysis) -> DecompositionPlan
    def generate_dependency_graph(self, sub_tasks: List[SubTask]) -> nx.DiGraph
    def estimate_resources(self, decomp_plan: DecompositionPlan) -> ResourceEstimate
    def optimize_allocation(self, graph: nx.DiGraph, agents: List[str], constraints: Dict) -> AllocationPlan
    def generate_execution_schedule(self, allocation_plan: AllocationPlan) -> Schedule
```

**Key Algorithms**:

1. **Task Analysis**: LLM-based classification with structured output
2. **Decomposition**: Hierarchical breakdown targeting 30-40 min chunks
3. **DAG Generation**: NetworkX DiGraph with cycle detection
4. **Resource Optimization**: PuLP linear programming for allocation
5. **Scheduling**: Topological sort → parallel wave grouping

### 2.2 Decomposition Learner (`decomposition_learner.py`)

**Purpose**: Learn from execution history to improve estimates.

```python
class DecompositionLearner:
    def __init__(self, db_path: str = "ensemble_decomposition.db")
    def record_execution(self, plan: DecompositionPlan, actual: ExecutionResult) -> None
    def improve_estimates(self) -> CalibrationReport
    def suggest_improvements(self, task_type: str) -> List[Suggestion]
    def get_historical_accuracy(self) -> AccuracyMetrics

class CalibrationReport(BaseModel):
    task_type: str
    original_estimate: float
    actual_average: float
    adjustment_factor: float
    confidence: float

class AccuracyMetrics(BaseModel):
    overall_accuracy: float
    by_domain: Dict[str, float]
    by_complexity: Dict[str, float]
    improvement_trend: List[float]  # Last N executions
```

### 2.3 Integration Points

**Executive Director Integration**:
- New phase between requirements and spawning Development Manager
- Extended output format with `decomposition_plan` field
- User approval workflow gate

**API Endpoints**:
```
POST /api/decompose
  Input: { user_request: str, budget_tier: str }
  Output: { plan: DecompositionPlan, estimate: ResourceEstimate, schedule: Schedule }

POST /api/approve-plan
  Input: { plan_id: str, action: "approve"|"reject"|"modify", modifications?: Dict }
  Output: { success: bool, execution_id?: str }

GET /api/decomposition-history
  Output: { accuracy: AccuracyMetrics, recent_executions: List }
```

**Frontend Component**:
```jsx
<TaskDecompositionViewer
  plan={decompositionPlan}
  estimate={resourceEstimate}
  schedule={schedule}
  onApprove={handleApprove}
  onReject={handleReject}
  onModify={handleModify}
/>
```

## 3. Data Flow

```
1. User submits request
   └──▶ POST /api/decompose
        └──▶ TaskDecompositionEngine.analyze_task()
             └──▶ Returns TaskAnalysis

2. TaskAnalysis passed to decomposition
   └──▶ TaskDecompositionEngine.decompose_task()
        └──▶ Returns DecompositionPlan with SubTasks

3. Generate dependency graph
   └──▶ TaskDecompositionEngine.generate_dependency_graph()
        └──▶ Returns nx.DiGraph (validated DAG)

4. Estimate resources
   └──▶ TaskDecompositionEngine.estimate_resources()
        └──▶ Returns ResourceEstimate with cost/time

5. Optimize allocation
   └──▶ TaskDecompositionEngine.optimize_allocation()
        └──▶ Returns AllocationPlan with model selections

6. Generate schedule
   └──▶ TaskDecompositionEngine.generate_execution_schedule()
        └──▶ Returns Schedule with parallel waves

7. Present to user via TaskDecompositionViewer
   └──▶ User approves/rejects/modifies

8. If approved:
   └──▶ POST /api/approve-plan
        └──▶ Executive Director spawns Development Manager with plan

9. After execution:
   └──▶ DecompositionLearner.record_execution()
        └──▶ Updates historical data for future improvements
```

## 4. Technology Stack

| Component | Technology | Justification |
|-----------|------------|---------------|
| Data Models | Pydantic v2 | Type safety, serialization, validation |
| Graph Operations | NetworkX | Mature DAG library, topological sort |
| LP Optimization | PuLP | Simple LP solver, sufficient for <100 tasks |
| Database | SQLite | Existing infrastructure, lightweight |
| Frontend | React 18 | Existing UI stack |
| Visualization | Mermaid.js | Declarative graph diagrams |

## 5. Model Selection Strategy

Based on task complexity:

| Complexity | Model | Reasoning |
|------------|-------|-----------|
| simple | haiku | Cost-effective for boilerplate |
| moderate | sonnet | Balance of capability and cost |
| complex | sonnet/opus | Critical decisions need best model |

Default pricing assumptions:
- Haiku: $0.25/1M tokens
- Sonnet: $3.00/1M tokens
- Opus: $15.00/1M tokens

## 6. DAG Validation Rules

1. **No Cycles**: Use `nx.is_directed_acyclic_graph()`
2. **Connected Components**: All tasks must be reachable
3. **Valid Dependencies**: Referenced task_ids must exist
4. **Reasonable Depth**: Max depth of 10 levels
5. **Reasonable Width**: Max parallel tasks of 8

## 7. Parallel Execution Waves

Algorithm:
```python
def generate_waves(dag: nx.DiGraph) -> List[List[str]]:
    waves = []
    remaining = set(dag.nodes())
    
    while remaining:
        # Find tasks with no unexecuted dependencies
        ready = [
            task for task in remaining
            if all(dep not in remaining for dep in dag.predecessors(task))
        ]
        waves.append(ready)
        remaining -= set(ready)
    
    return waves
```

## 8. Error Handling

| Error Type | Handling |
|------------|----------|
| Cycle Detected | Return error, suggest manual review |
| Invalid Dependencies | Ignore missing deps, log warning |
| LP Infeasible | Fall back to greedy allocation |
| LLM Parse Error | Retry with simplified prompt |
| Timeout | Return partial results with warning |

## 9. Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| analyze_task | <2s | LLM response time |
| decompose_task | <2s | LLM + processing |
| generate_dependency_graph | <100ms | In-memory graph |
| estimate_resources | <200ms | Calculation |
| optimize_allocation | <500ms | LP solve time |
| generate_execution_schedule | <100ms | Topological sort |
| **Total Decomposition** | **<5s** | End-to-end |

## 10. File Structure

```
ensemble/
├── src/
│   ├── runtime/
│   │   └── agents/
│   │       ├── decomposition_engine.py    # Core engine
│   │       └── decomposition_learner.py   # Learning module
│   └── field/
│       └── ensemble_ui/
│           ├── backend/
│           │   └── main.py                # API endpoints (updated)
│           └── frontend/
│               └── src/
│                   └── components/
│                       └── TaskDecompositionViewer.jsx
├── leadership/
│   └── executive_director.md              # Integration (updated)
├── tests/
│   └── test_decomposition.py              # Test suite
└── TASK_DECOMPOSITION.md                  # Documentation
```

## 11. Security Considerations

1. **Input Validation**: Sanitize user requests before LLM processing
2. **Cost Limits**: Maximum budget cap for plan approval
3. **Plan Tampering**: Validate plan integrity before execution
4. **History Access**: Rate limit history API to prevent data harvesting

## 12. Future Extensibility

1. **Custom Decomposition Strategies**: Plugin architecture for domain-specific strategies
2. **Multi-LLM Support**: Allow different LLM providers for decomposition
3. **Real-time Collaboration**: WebSocket-based plan editing
4. **External Integrations**: JIRA, GitHub Issues export
