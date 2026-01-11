# Smart Task Decomposition Engine - Milestone Plan

## Project Overview
Transform the Ensemble AI Executive Director into an intelligent planner with a Smart Task Decomposition Engine that analyzes complex user requests, generates dependency graphs, estimates resources, and presents execution plans for user approval.

## Milestone Breakdown

---

### Milestone 1: Core Decomposition Engine
**Objective**: Build the foundational TaskDecompositionEngine with task analysis, decomposition, and DAG generation capabilities.

**Deliverables**:
1. `src/runtime/agents/decomposition_engine.py` - Core engine implementation
2. Pydantic data models (TaskAnalysis, SubTask, DecompositionPlan, ResourceEstimate, AllocationPlan, Schedule)
3. Methods: analyze_task(), decompose_task(), generate_dependency_graph()
4. Unit tests for core functionality

**Acceptance Criteria**:
- [ ] TaskDecompositionEngine class is functional
- [ ] analyze_task() returns valid TaskAnalysis with complexity_score, domain, estimated_hours
- [ ] decompose_task() produces hierarchical sub-tasks targeting 30-40 min chunks
- [ ] generate_dependency_graph() produces valid DAG with no cycles
- [ ] All unit tests pass
- [ ] Decomposition completes in < 5 seconds

**Dependencies**: None (foundational)

**Estimated Duration**: 2-3 hours

---

### Milestone 2: Resource Optimization
**Objective**: Add resource estimation, allocation optimization, and execution scheduling to the engine.

**Deliverables**:
1. estimate_resources() method
2. optimize_allocation() method using PuLP linear programming
3. generate_execution_schedule() method with parallel wave scheduling
4. Extended unit tests for optimization

**Acceptance Criteria**:
- [ ] ResourceEstimate includes agent_count, model_distribution, estimated_tokens, estimated_cost
- [ ] optimize_allocation() uses linear programming for optimal model/agent assignment
- [ ] generate_execution_schedule() produces parallel execution waves
- [ ] Critical path is correctly identified
- [ ] All tests pass

**Dependencies**: Milestone 1 (requires DAG from decomposition)

**Estimated Duration**: 2 hours

---

### Milestone 3: Learning Module
**Objective**: Build the DecompositionLearner for historical tracking and estimate improvement.

**Deliverables**:
1. `src/runtime/agents/decomposition_learner.py`
2. Methods: record_execution(), improve_estimates(), suggest_improvements(), get_historical_accuracy()
3. Integration with existing metrics.py database
4. Unit tests for learning module

**Acceptance Criteria**:
- [ ] Execution data is recorded to SQLite database
- [ ] Historical accuracy metrics are calculated
- [ ] Estimates improve measurably over 10+ executions
- [ ] Learning updates don't block execution (async-friendly)
- [ ] All tests pass

**Dependencies**: Milestone 1 & 2 (needs execution plans to record)

**Estimated Duration**: 1.5 hours

---

### Milestone 4: API Endpoints
**Objective**: Create FastAPI endpoints for decomposition workflow.

**Deliverables**:
1. `POST /api/decompose` endpoint
2. `POST /api/approve-plan` endpoint
3. `GET /api/decomposition-history` endpoint
4. API integration tests

**Acceptance Criteria**:
- [ ] /api/decompose accepts user request and returns full DecompositionPlan
- [ ] /api/approve-plan handles accept/reject/modify actions
- [ ] /api/decomposition-history returns accuracy metrics
- [ ] Endpoints integrate with existing backend structure
- [ ] API tests pass

**Dependencies**: Milestones 1, 2, 3 (needs engine and learner)

**Estimated Duration**: 1.5 hours

---

### Milestone 5: Frontend Visualization
**Objective**: Build React component for task decomposition visualization and approval.

**Deliverables**:
1. `TaskDecompositionViewer.jsx` component
2. Mermaid diagram integration for DAG visualization
3. Resource estimates display
4. Execution wave visualization
5. Approve/Reject/Modify action buttons

**Acceptance Criteria**:
- [ ] Dependency graph renders as Mermaid diagram
- [ ] Resource estimates (agents, cost, time) displayed clearly
- [ ] Execution waves shown in timeline format
- [ ] User can approve/reject/modify plans
- [ ] UI renders in < 500ms
- [ ] Component is responsive and accessible

**Dependencies**: Milestone 4 (needs API endpoints)

**Estimated Duration**: 2 hours

---

### Milestone 6: Executive Director Integration
**Objective**: Integrate decomposition engine into Executive Director workflow.

**Deliverables**:
1. Updated `leadership/executive_director.md`
2. New decomposition workflow before Development Manager spawn
3. Extended output format with decomposition_plan
4. requires_user_approval field for approval flow

**Acceptance Criteria**:
- [ ] Executive Director invokes decomposition before delegating
- [ ] User approval flow works correctly
- [ ] Output format includes decomposition plan
- [ ] Integration with existing Executive Director patterns

**Dependencies**: Milestones 1-4 (needs full engine)

**Estimated Duration**: 1 hour

---

### Milestone 7: Testing & Documentation
**Objective**: Comprehensive test suite and documentation.

**Deliverables**:
1. `tests/test_decomposition.py` - Full test suite
2. `TASK_DECOMPOSITION.md` - Documentation
3. Benchmark tests (simple, medium, complex)
4. Integration tests for full workflow

**Acceptance Criteria**:
- [ ] Unit tests cover all methods
- [ ] Integration tests verify end-to-end flow
- [ ] Graph validity tests (DAG, cycles, topological sort)
- [ ] Benchmark tests for different complexity levels
- [ ] Documentation includes architecture, usage, API reference
- [ ] All tests pass

**Dependencies**: All previous milestones

**Estimated Duration**: 2 hours

---

## Summary

| Milestone | Description | Est. Duration | Dependencies |
|-----------|-------------|---------------|--------------|
| 1 | Core Decomposition Engine | 2-3 hours | None |
| 2 | Resource Optimization | 2 hours | M1 |
| 3 | Learning Module | 1.5 hours | M1, M2 |
| 4 | API Endpoints | 1.5 hours | M1, M2, M3 |
| 5 | Frontend Visualization | 2 hours | M4 |
| 6 | Executive Director Integration | 1 hour | M1-M4 |
| 7 | Testing & Documentation | 2 hours | All |

**Total Estimated Duration**: 12-14 hours
**Critical Path**: M1 → M2 → M3 → M4 → M5/M6 → M7

## Technical Decisions Made

1. **Graph Library**: NetworkX for DAG operations
2. **LP Solver**: PuLP for resource optimization (simpler than OR-Tools)
3. **Database**: SQLite using existing metrics.py infrastructure
4. **Frontend**: React 18+ with Mermaid.js for visualization
5. **Validation**: Pydantic for data models
6. **Decomposition Strategy**: Hierarchical (Goals → Tasks → Actions) targeting 30-40 min chunks
