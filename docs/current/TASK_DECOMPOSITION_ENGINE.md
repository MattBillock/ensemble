# Smart Task Decomposition Engine

**Date**: 2026-01-11
**Status**: ✅ Implemented
**Location**: `src/runtime/agents/decomposition_engine.py`

## Overview

The Smart Task Decomposition Engine automatically analyzes user requests and breaks them down into optimal sub-tasks with dependency graphs, resource estimates, and execution schedules. This enables intelligent task planning and efficient agent orchestration.

## Key Features

- **Automatic Task Analysis**: Extracts goals, scope, components, and constraints from natural language requests
- **Domain Detection**: Automatically detects backend, frontend, full-stack, or testing tasks
- **Dependency Graph Generation**: Creates directed acyclic graphs (DAGs) with NetworkX
- **Resource Estimation**: Calculates costs, token usage, and agent requirements
- **Parallel Execution Planning**: Identifies parallelization opportunities to reduce wall-clock time
- **Critical Path Analysis**: Determines the longest path through dependencies
- **Execution Scheduling**: Generates phase-by-phase execution timelines

## Architecture

### Core Components

1. **TaskDecompositionEngine**: Main orchestration class
2. **Pydantic Models**:
   - `TaskAnalysis`: Analysis of user request
   - `SubTask`: Individual decomposed task
   - `DecompositionPlan`: Complete breakdown with dependency graph
   - `ResourceEstimate`: Cost and agent requirements
   - `AllocationPlan`: Task-to-agent assignments
   - `Schedule`: Execution timeline

### Dependencies

- **NetworkX**: Graph operations and DAG analysis
- **PuLP**: Optimization (for future resource allocation optimization)
- **Pydantic**: Data validation and serialization

## Usage

### Basic Workflow

```python
from src.runtime.agents.decomposition_engine import TaskDecompositionEngine

# Initialize engine
engine = TaskDecompositionEngine()

# 1. Analyze user request
request = "Build a REST API for blog posts with CRUD operations and PostgreSQL"
analysis = engine.analyze_task(request)

print(f"Domain: {analysis.domain}")
print(f"Components: {analysis.required_components}")
print(f"Scope: {analysis.scope}")

# 2. Decompose into sub-tasks
plan = engine.decompose_task(analysis)

print(f"Total tasks: {len(plan.sub_tasks)}")
print(f"Total estimated time: {plan.total_estimated_duration_mins} mins")
print(f"Critical path: {plan.critical_path_duration_mins} mins")
print(f"Parallelization opportunities: {plan.parallelization_opportunities}")

# 3. Estimate resources
estimate = engine.estimate_resources(plan)

print(f"Total agents needed: {estimate.total_agents_needed}")
print(f"Estimated cost: ${estimate.estimated_total_cost_usd:.3f}")
print(f"Peak concurrent agents: {estimate.peak_concurrent_agents}")
print(f"Wall clock time: {estimate.estimated_wall_clock_mins} mins")

# 4. Create allocation plan
allocation = engine.optimize_allocation(plan)

print(f"Execution phases: {allocation.total_phases}")
for phase_idx, phase_tasks in enumerate(allocation.execution_phases):
    print(f"  Phase {phase_idx + 1}: {len(phase_tasks)} parallel tasks")

# 5. Generate execution schedule
schedule = engine.generate_execution_schedule(plan, allocation)

print(f"Estimated completion: {schedule.estimated_completion_time}")
print(f"Critical path tasks: {schedule.critical_path}")
```

### Example: Backend Task

```python
request = "Create a user authentication API with JWT tokens and bcrypt password hashing"

analysis = engine.analyze_task(request)
# Domain: backend
# Components: ['authentication', 'api', 'database']

plan = engine.decompose_task(analysis)
# Sub-tasks:
#   1. Create database models (User, Session)
#   2. Implement API endpoints (login, register, logout)
#   3. Add JWT auth middleware
#   4. Write backend tests

estimate = engine.estimate_resources(plan)
# Total agents: 4
# Estimated cost: $0.065
# Wall clock time: 130 mins (with parallelization)
```

### Example: Full-Stack Task

```python
request = "Build a todo list application with FastAPI backend and React frontend"

analysis = engine.analyze_task(request)
# Domain: full_stack
# Components: ['api', 'database', 'ui_components']

plan = engine.decompose_task(analysis)
# Sub-tasks (backend):
#   1. Create Todo model
#   2. Implement CRUD API endpoints
#   3. Add validation
# Sub-tasks (frontend):
#   4. Create TodoList component
#   5. Implement state management
#   6. Integrate with API
# Sub-tasks (testing):
#   7. Write frontend tests

# Backend and frontend tasks can run in parallel!
estimate = engine.estimate_resources(plan)
# Peak concurrent agents: 2-3
# Wall clock time reduced by ~40% due to parallelization
```

## Domain Detection

The engine automatically detects the domain based on keywords:

| Domain | Keywords | Example |
|--------|----------|---------|
| **backend** | api, endpoint, database, server, postgresql, fastapi | "Create REST API with PostgreSQL" |
| **frontend** | ui, component, react, vue, dashboard, interface | "Build React dashboard component" |
| **full_stack** | Both backend + frontend (≥2 keywords each) | "Todo app with FastAPI and React" |
| **testing** | test, testing, pytest, jest, coverage | "Add unit tests with pytest" |
| **general** | None of the above | "Refactor code for better performance" |

## Task Complexity Levels

| Complexity | Duration | Description | Example |
|------------|----------|-------------|---------|
| **SIMPLE** | < 30 mins | Straightforward, 1-2 TDD cycles | "Add validation to endpoint" |
| **CREATIVE** | 30-60 mins | Requires design decisions, 3-5 cycles | "Implement auth service" |
| **STRATEGIC** | 60+ mins | Complex architecture/planning | "Design microservices architecture" |

## Dependency Graph Features

### Cycle Detection

The engine automatically detects circular dependencies and raises an error:

```python
tasks = [
    SubTask(task_id="task_1", dependencies=["task_2"], ...),
    SubTask(task_id="task_2", dependencies=["task_1"], ...)  # Circular!
]

try:
    graph = engine.generate_dependency_graph(tasks)
except ValueError as e:
    print(f"Error: {e}")  # "Circular dependencies detected: [['task_1', 'task_2']]"
```

### Parallel Task Identification

Tasks with no dependencies or the same dependencies can run in parallel:

```python
tasks = [
    SubTask(task_id="backend", dependencies=[], estimated_duration_mins=60, ...),
    SubTask(task_id="frontend", dependencies=[], estimated_duration_mins=60, ...)
]

plan = engine.decompose_task(analysis)
# Both can run in parallel!
# Total duration: 120 mins
# Critical path: 60 mins (40% time savings)
```

### Critical Path Analysis

The critical path is the longest path through dependencies:

```python
# task_1 (20m) → task_2 (30m) → task_3 (25m)
# Critical path: [task_1, task_2, task_3]
# Duration: 75 mins

schedule = engine.generate_execution_schedule(plan, allocation)
print(schedule.critical_path)  # ['task_1', 'task_2', 'task_3']

# Tasks on critical path are marked in schedule:
for phase in schedule.phases:
    for task in phase["tasks"]:
        if task["on_critical_path"]:
            print(f"⚠️ Critical: {task['description']}")
```

## Resource Estimation

### Agent Cost Estimates

Based on model usage and complexity:

| Agent Type | Cost per Execution | Model | Typical Complexity |
|------------|-------------------|-------|-------------------|
| Executive Director | $0.05 | Sonnet | Strategic |
| System Architect | $0.03 | Haiku | Creative |
| Development Manager | $0.02 | Haiku | Simple |
| Backend/Frontend Lead | $0.02 | Haiku | Creative |
| Backend/Frontend Developer | $0.015 | Haiku | Creative |
| Test Lead | $0.015 | Haiku | Creative |
| Coordinator | $0.01 | Haiku | Simple |
| Test Writer | $0.01 | Haiku | Simple |

### Token Estimation

Rough estimate: **1000 tokens per 10 minutes of work**

```python
# Task: 40 mins → ~4000 tokens
# 10 tasks × 40 mins = 40,000 tokens → ~$0.12 (at Haiku pricing)
```

## Execution Phases

Tasks are grouped into phases where all tasks within a phase can run in parallel:

```python
allocation = engine.optimize_allocation(plan)

# Example phases:
# Phase 1: [task_1, task_3]  (2 parallel tasks, no dependencies)
# Phase 2: [task_2, task_4]  (depends on Phase 1)
# Phase 3: [task_5]           (depends on Phase 2)
```

Each phase completes before the next begins, but tasks within a phase run simultaneously.

## Integration with Agent Runtime

### Future Integration

The decomposition engine will be integrated with the Executive Director:

```python
from src.runtime.agents.decomposition_engine import TaskDecompositionEngine

class ExecutiveDirector:
    def __init__(self):
        self.decomp_engine = TaskDecompositionEngine()

    def handle_user_request(self, request: str):
        # 1. Analyze and decompose
        analysis = self.decomp_engine.analyze_task(request)
        plan = self.decomp_engine.decompose_task(analysis)

        # 2. Estimate resources and get approval
        estimate = self.decomp_engine.estimate_resources(plan)
        if not self.get_user_approval(plan, estimate):
            return

        # 3. Create execution plan
        allocation = self.decomp_engine.optimize_allocation(plan)
        schedule = self.decomp_engine.generate_execution_schedule(plan, allocation)

        # 4. Execute phases
        for phase in schedule.phases:
            self.execute_phase(phase)
```

## Testing

Comprehensive test suite: `tests/test_decomposition_engine.py`

- ✅ Task analysis (backend, frontend, full-stack)
- ✅ Task decomposition (all domains)
- ✅ Dependency graph generation
- ✅ Cycle detection
- ✅ Parallel task identification
- ✅ Resource estimation
- ✅ Allocation planning
- ✅ Schedule generation
- ✅ Critical path analysis
- ✅ End-to-end workflows

Run tests:
```bash
pytest tests/test_decomposition_engine.py -v
```

All 16 tests passing ✅

## Performance Characteristics

### Time Complexity

- **Task Analysis**: O(n) where n = length of request
- **Decomposition**: O(k) where k = number of components
- **Graph Generation**: O(V + E) where V = tasks, E = dependencies
- **Critical Path**: O(V + E) using DAG longest path
- **Topological Sort**: O(V + E)

### Space Complexity

- **Graph Storage**: O(V + E)
- **Task Storage**: O(V × fields)
- **Schedule**: O(V × phases)

### Scalability

- Tested with up to 20 tasks, 30+ dependencies
- NetworkX efficiently handles graphs with hundreds of nodes
- Typical user requests: 3-10 tasks

## Future Enhancements

1. **Learning Module**: Track actual vs estimated durations and improve predictions
2. **Resource Constraints**: Limit concurrent agents based on budget
3. **PuLP Optimization**: Use linear programming for optimal allocation
4. **Pattern Recognition**: Detect common task patterns (CRUD, Auth, etc.)
5. **User Feedback Integration**: Adjust decomposition based on user preferences
6. **Historical Data**: Learn from past decompositions to improve accuracy

## Examples in the Wild

### Example 1: E-commerce Checkout

```python
request = "Implement shopping cart checkout with Stripe payment integration"

# Decomposition:
# 1. Create Cart and Order models (backend)
# 2. Implement cart API endpoints (backend)
# 3. Integrate Stripe API (backend)
# 4. Create checkout UI components (frontend) - parallel with 1-3
# 5. Connect frontend to payment API (frontend)
# 6. Add payment validation (backend)
# 7. Write integration tests (testing)

# Result:
# - 7 tasks total
# - 3 phases (some parallel)
# - 180 mins total, 120 mins wall-clock (33% savings)
# - $0.12 estimated cost
```

### Example 2: User Dashboard

```python
request = "Build an analytics dashboard with charts showing user activity over time"

# Decomposition:
# 1. Create analytics data aggregation service (backend)
# 2. Add analytics API endpoints (backend)
# 3. Create Chart components (React) (frontend) - parallel with 1-2
# 4. Create Dashboard layout (frontend)
# 5. Integrate charts with API (frontend)
# 6. Add filtering and date range selection (frontend)
# 7. Write component tests (testing)

# Result:
# - 7 tasks total
# - 4 phases
# - 210 mins total, 150 mins wall-clock (28% savings)
# - Peak 2 concurrent agents
```

## Troubleshooting

### Issue: Domain detected incorrectly

**Solution**: Add more specific keywords to your request
```python
# Instead of: "Build authentication"
# Use: "Build backend authentication API with JWT tokens"
```

### Issue: Too many/too few tasks

**Solution**: Task decomposition follows heuristics. You can:
- Manually adjust the decomposition after generation
- Provide more detailed requirements
- Use the learning module (future) to improve predictions

### Issue: Circular dependencies detected

**Solution**: Review your task dependencies and break the cycle:
```python
# Bad: A depends on B, B depends on A
# Good: A → B → C (linear) or A → C, B → C (convergent)
```

## API Reference

### TaskDecompositionEngine

#### `analyze_task(user_request: str) -> TaskAnalysis`
Analyzes user request and extracts structured information.

#### `decompose_task(task_analysis: TaskAnalysis) -> DecompositionPlan`
Breaks down analyzed task into sub-tasks with dependencies.

#### `generate_dependency_graph(sub_tasks: List[SubTask]) -> nx.DiGraph`
Creates directed acyclic graph of task dependencies.

#### `estimate_resources(decomp_plan: DecompositionPlan) -> ResourceEstimate`
Calculates resource requirements and costs.

#### `optimize_allocation(decomp_plan, available_agents, constraints) -> AllocationPlan`
Creates optimal task-to-agent allocation plan.

#### `generate_execution_schedule(decomp_plan, allocation_plan) -> Schedule`
Generates phase-by-phase execution timeline.

---

**Next Steps**: Integrate with Executive Director for automatic task planning and execution.
