# Smart Task Decomposition Engine for Ensemble AI

## Project Overview

### Vision
Transform the Ensemble AI Executive Director from a simple coordinator into an intelligent planner with a Smart Task Decomposition Engine that analyzes complex user requests, generates dependency graphs, estimates resources, and presents execution plans for user approval before proceeding.

### Core Problem
Currently, the Executive Director delegates work without intelligent decomposition, parallel execution optimization, or resource estimation. Users have no visibility into how their requests will be handled or what it will cost.

### Solution
A comprehensive Task Decomposition Engine that:
1. Analyzes task complexity and domain classification
2. Decomposes tasks hierarchically (Goals → Tasks → Actions)
3. Generates DAG-based dependency graphs
4. Optimizes resource allocation using linear programming
5. Schedules execution in parallel waves
6. Learns from execution history to improve estimates

## Objectives

1. **Intelligent Decomposition**: Break complex requests into optimal sub-tasks targeting 30-40 minute execution chunks
2. **Dependency Management**: Create DAGs showing task relationships with parallel execution opportunities
3. **Resource Optimization**: Minimize cost/time while maintaining quality through smart model selection
4. **User Transparency**: Provide clear visualization of execution plans before proceeding
5. **Continuous Learning**: Improve estimates based on historical execution data

## Scope

### In Scope

#### Phase 1: Core Decomposition Engine
**File**: `src/runtime/agents/decomposition_engine.py`

Classes and Methods:
- `TaskDecompositionEngine` class with:
  - `analyze_task(user_request: str) -> TaskAnalysis`
  - `decompose_task(task_analysis: TaskAnalysis) -> DecompositionPlan`
  - `generate_dependency_graph(sub_tasks: List[SubTask]) -> nx.DiGraph`
  - `estimate_resources(decomp_plan: DecompositionPlan) -> ResourceEstimate`
  - `optimize_allocation(graph, available_agents, constraints) -> AllocationPlan`
  - `generate_execution_schedule(allocation_plan: AllocationPlan) -> Schedule`

Data Models (Pydantic):
- `TaskAnalysis`: complexity_score, domain, estimated_human_hours, key_requirements
- `SubTask`: task_id, description, agent_type, estimated_duration, complexity, dependencies
- `DecompositionPlan`: task_analysis, sub_tasks, dependency_graph
- `ResourceEstimate`: agent_count, model_distribution, estimated_tokens, estimated_cost, critical_path_duration, parallelization_factor
- `AllocationPlan`: task_assignments, model_selections, resource_utilization
- `Schedule`: waves, total_duration, estimated_start_end_times

#### Phase 2: Learning Module
**File**: `src/runtime/agents/decomposition_learner.py`

Classes:
- `DecompositionLearner` class with:
  - `record_execution(plan, actual_execution) -> None`
  - `improve_estimates() -> CalibrationReport`
  - `suggest_improvements(task_type: str) -> List[Suggestion]`
  - `get_historical_accuracy() -> AccuracyMetrics`

#### Phase 3: Executive Director Integration
**File**: `leadership/executive_director.md`

Updates:
- New decomposition workflow before spawning Development Manager
- Extended output format with `decomposition_plan` field
- New `requires_user_approval` field for plan approval flow

#### Phase 4: Frontend Visualization
**File**: `src/field/ensemble_ui/frontend/src/components/TaskDecompositionViewer.jsx`

Features:
- Mermaid diagram rendering of task dependency graph
- Resource estimates display (agents, cost, time)
- Execution wave visualization
- Agent assignment table
- Approve/Reject/Modify action buttons
- Plan modification interface

#### Phase 5: API Endpoints
**File**: `src/field/ensemble_ui/backend/main.py` (additions)

Endpoints:
- `POST /api/decompose`: Decompose a user request into execution plan
- `POST /api/approve-plan`: Accept/reject/modify a decomposition plan
- `GET /api/decomposition-history`: Get historical decomposition accuracy

#### Phase 6: Tests
**File**: `tests/test_decomposition.py`

Test Categories:
- Unit tests for each decomposition method
- Integration tests for full decomposition → execution → metrics loop
- Graph validity tests (DAG, cycle detection, topological sorting)
- Benchmark tests (simple, medium, complex tasks)
- Learning accuracy tests

#### Phase 7: Documentation
**File**: `TASK_DECOMPOSITION.md`

Contents:
- Architecture overview
- Usage examples
- API reference
- Configuration options

### Out of Scope
- External API integrations (beyond existing Ensemble infrastructure)
- Payment processing for cost estimates
- Real-time collaborative plan editing
- Mobile-specific UI

## Technical Specifications

### Technologies
- **Python 3.11+**: Core engine implementation
- **NetworkX**: Graph creation, DAG validation, topological sorting
- **PuLP/OR-Tools**: Linear programming for optimal allocation (using PuLP for simplicity)
- **Pydantic**: Data validation and serialization
- **SQLite**: Historical performance storage (using existing metrics DB)
- **React 18+**: Frontend components
- **Mermaid.js**: Graph visualization

### Architecture Patterns
1. **Divide and Conquer**: Break tasks into 30-40 min chunks
2. **Dependency Injection**: Pass metrics DB, agent registry to engine
3. **Strategy Pattern**: Different decomposition strategies (sequential, parallel, hybrid)
4. **Observer Pattern**: Notify UI when plan changes
5. **Template Method**: Standard decomposition flow with customizable steps

### Algorithm Approaches
1. **Graph-Based Planning**: Model sub-tasks as DAG nodes, dependencies as edges
2. **Hierarchical Decomposition**: Three-level hierarchy (Goals → Tasks → Actions)
3. **Linear Programming**: Constraint satisfaction for optimal allocation
4. **Time-Optimized Decomposition**: Target 30-40 min chunks for best LLM performance

### Data Flow
```
User Request
    ↓
analyze_task() → TaskAnalysis
    ↓
decompose_task() → DecompositionPlan
    ↓
generate_dependency_graph() → nx.DiGraph
    ↓
estimate_resources() → ResourceEstimate
    ↓
optimize_allocation() → AllocationPlan
    ↓
generate_execution_schedule() → Schedule
    ↓
Present to User for Approval
    ↓
Execute According to Schedule
    ↓
record_execution() → Update Learning Model
```

## Constraints

### Performance
- Decomposition must complete in < 5 seconds for typical requests
- UI must render plans in < 500ms
- Learning model updates must not block execution

### Compatibility
- Must integrate with existing agent runtime (`src/runtime/agents/runtime.py`)
- Must use existing metrics database (`src/runtime/agents/metrics.py`)
- Must work with current Executive Director agent flow

### Quality
- All decompositions must produce valid DAGs (no cycles)
- Estimate accuracy must improve over time (measurable)
- UI must be accessible and responsive

## Success Criteria

1. ✅ **Intelligent Decomposition**: Complex requests broken into logical sub-tasks
2. ✅ **Dependency Awareness**: Correct ordering, parallel opportunities identified
3. ✅ **Resource Optimization**: Minimal cost/time while maintaining quality
4. ✅ **User Transparency**: Clear visualization of what will happen
5. ✅ **Learning Over Time**: Estimates improve with more executions
6. ✅ **Metrics Integration**: Uses historical performance data for decisions
7. ✅ **Graph Validity**: DAG structure, no cycles, proper topological ordering
8. ✅ **Error Handling**: Graceful degradation if decomposition fails

## Deliverables

1. `src/runtime/agents/decomposition_engine.py` - Core engine (Phase 1)
2. `src/runtime/agents/decomposition_learner.py` - Learning module (Phase 2)
3. Updated `leadership/executive_director.md` - Integration (Phase 3)
4. `src/field/ensemble_ui/frontend/src/components/TaskDecompositionViewer.jsx` - UI (Phase 4)
5. Updated `src/field/ensemble_ui/backend/main.py` - API endpoints (Phase 5)
6. `tests/test_decomposition.py` - Test suite (Phase 6)
7. `TASK_DECOMPOSITION.md` - Documentation (Phase 7)

## Assumptions

1. **Model Costs**: Using standard Anthropic pricing (Haiku ~$0.25/1M tokens, Sonnet ~$3/1M tokens)
2. **Agent Types**: Using existing agent types from the registry (backend_lead, frontend_lead, test_coordinator, system_architect)
3. **Database**: Using SQLite with existing metrics schema, can extend as needed
4. **Graph Library**: NetworkX is appropriate for DAG operations at expected scale
5. **LP Solver**: PuLP is sufficient for optimization complexity (< 100 tasks)
6. **Execution Time**: 30-40 minute chunks are optimal based on research findings
7. **Parallelization**: Maximum practical parallelization is ~4-5 concurrent agents

## Example Input/Output

### Input
```
"Build a todo app with React frontend, FastAPI backend, PostgreSQL database,
user authentication, and deployment to AWS"
```

### Expected Output
```json
{
  "task_analysis": {
    "complexity_score": 8,
    "domain": "fullstack_web_app",
    "estimated_human_hours": 12,
    "key_requirements": [
      "React frontend with state management",
      "FastAPI REST API",
      "PostgreSQL database with migrations",
      "JWT authentication",
      "AWS deployment (EC2/RDS/S3)"
    ]
  },
  "dependency_graph": {
    "nodes": [
      {"id": "db_schema", "type": "backend", "agent": "backend_lead"},
      {"id": "auth_api", "type": "backend", "agent": "backend_lead", "depends_on": ["db_schema"]},
      {"id": "todo_api", "type": "backend", "agent": "backend_lead", "depends_on": ["db_schema"]},
      {"id": "react_components", "type": "frontend", "agent": "frontend_lead", "depends_on": []},
      {"id": "auth_ui", "type": "frontend", "agent": "frontend_lead", "depends_on": ["auth_api", "react_components"]},
      {"id": "todo_ui", "type": "frontend", "agent": "frontend_lead", "depends_on": ["todo_api", "react_components"]},
      {"id": "integration_tests", "type": "testing", "agent": "test_coordinator", "depends_on": ["auth_ui", "todo_ui"]},
      {"id": "aws_deployment", "type": "infrastructure", "agent": "system_architect", "depends_on": ["integration_tests"]}
    ]
  },
  "execution_schedule": {
    "wave_1": ["db_schema", "react_components"],
    "wave_2": ["auth_api", "todo_api"],
    "wave_3": ["auth_ui", "todo_ui"],
    "wave_4": ["integration_tests"],
    "wave_5": ["aws_deployment"]
  },
  "resource_estimate": {
    "total_agents": 4,
    "peak_concurrent": 2,
    "estimated_duration_min": 35,
    "estimated_cost": "$2.80",
    "model_distribution": {
      "db_schema": "haiku",
      "auth_api": "sonnet",
      "todo_api": "haiku",
      "react_components": "haiku",
      "auth_ui": "sonnet",
      "todo_ui": "haiku",
      "integration_tests": "haiku",
      "aws_deployment": "sonnet"
    }
  }
}
```

## Testing Strategy

### Unit Tests
- Each decomposition method independently
- Graph operations (create, validate, topological sort)
- Resource estimation calculations
- Learning model updates

### Integration Tests
- Full decomposition → execution → metrics loop
- API endpoint end-to-end
- UI component rendering with various plans

### Graph Tests
- DAG validity
- Cycle detection
- Topological sorting correctness

### Benchmark Tasks
- **Simple**: "Write a hello world script" → should NOT over-decompose (1-2 tasks)
- **Medium**: "Build a REST API for blog posts" → 3-5 sub-tasks
- **Complex**: "Build a SaaS app" → 8-15 sub-tasks with clear dependencies

### Learning Tests
- Verify estimates improve over 10+ executions
- Accuracy metrics tracking
