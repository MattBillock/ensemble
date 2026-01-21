# Backend Tasks - Milestone 1: Core Decomposition Engine

## Overview
Build the foundational TaskDecompositionEngine with task analysis, decomposition, and DAG generation capabilities.

## Task Breakdown

### Task 1: Core Data Models and Infrastructure
**Priority**: High (Foundation)
**Complexity**: Medium
**Estimated Duration**: 45 minutes

**Description**: Create Pydantic data models for task decomposition and set up the basic project structure.

**Acceptance Criteria**:
- [ ] TaskAnalysis model with complexity_score, domain, estimated_hours fields
- [ ] SubTask model with id, title, description, estimated_duration, dependencies, agent_type
- [ ] DecompositionPlan model containing task hierarchy and metadata
- [ ] ResourceEstimate model with agent_count, model_distribution, estimated_tokens, estimated_cost
- [ ] AllocationPlan and Schedule models for future milestones
- [ ] All models validate input data correctly
- [ ] Models export to/from JSON properly

**Dependencies**: None

**Technical Details**:
- Use Pydantic v2 BaseModel
- Include validation rules for duration ranges, complexity scores (1-10)
- Add __str__ methods for debugging
- Ensure JSON serialization works for API responses

---

### Task 2: Database Schema and Models
**Priority**: High
**Complexity**: Low
**Estimated Duration**: 30 minutes

**Description**: Set up SQLite database schema for storing decomposition history and metrics.

**Acceptance Criteria**:
- [ ] DecompositionHistory table with columns: id, original_request, plan_json, created_at, approved_at, executed_at
- [ ] ExecutionMetrics table for tracking actual vs estimated times
- [ ] Database initialization script
- [ ] Integration with existing metrics.py structure
- [ ] Proper foreign key relationships

**Dependencies**: Task 1 (needs data models)

**Technical Details**:
- Extend existing SQLite database
- Use SQLAlchemy ORM if already in use, or raw SQL
- Include indexes for performance
- Migration script for existing databases

---

### Task 3: Task Analysis Engine
**Priority**: High
**Complexity**: High
**Estimated Duration**: 60 minutes

**Description**: Implement analyze_task() method to parse user requests and determine complexity, domain, and initial estimates.

**Acceptance Criteria**:
- [ ] analyze_task() accepts natural language user request
- [ ] Returns TaskAnalysis with complexity_score (1-10), domain classification, estimated_hours
- [ ] Identifies key verbs, entities, and technical domains
- [ ] Handles edge cases (empty input, very long requests)
- [ ] Performance under 2 seconds for typical requests
- [ ] Consistent scoring for similar requests

**Dependencies**: Task 1 (needs TaskAnalysis model)

**Technical Details**:
- Use regex patterns and keyword matching for domain detection
- Implement complexity scoring based on:
  - Number of distinct actions/verbs
  - Technical complexity indicators
  - Cross-domain requirements
- Fallback to default estimates for unknown domains

---

### Task 4: Task Decomposition Logic
**Priority**: High
**Complexity**: High
**Estimated Duration**: 75 minutes

**Description**: Implement decompose_task() method to break complex tasks into 30-40 minute sub-tasks with proper hierarchy.

**Acceptance Criteria**:
- [ ] decompose_task() takes TaskAnalysis and produces hierarchical sub-tasks
- [ ] Sub-tasks target 30-40 minute duration chunks
- [ ] Maximum 3 levels of hierarchy (Goals → Tasks → Actions)
- [ ] Each sub-task has clear title, description, estimated duration
- [ ] Assigns appropriate agent_type for each sub-task
- [ ] Handles both simple and complex decompositions
- [ ] Produces consistent results for similar inputs

**Dependencies**: Task 1, 3 (needs models and analysis)

**Technical Details**:
- Implement hierarchical decomposition algorithm
- Use domain-specific templates for common patterns
- Agent type assignment based on task characteristics:
  - code_writer for implementation
  - code_tester for testing
  - data_analyst for analysis
  - etc.

---

### Task 5: Dependency Analysis and DAG Generation
**Priority**: High
**Complexity**: High
**Estimated Duration**: 60 minutes

**Description**: Implement generate_dependency_graph() method to create valid directed acyclic graphs of task dependencies.

**Acceptance Criteria**:
- [ ] generate_dependency_graph() produces NetworkX DiGraph
- [ ] DAG validation ensures no cycles
- [ ] Automatic dependency inference between related sub-tasks
- [ ] Topological ordering for execution sequence
- [ ] Critical path identification
- [ ] Graph serialization to JSON for API responses
- [ ] Performance under 3 seconds for complex graphs

**Dependencies**: Task 1, 4 (needs models and decomposed tasks)

**Technical Details**:
- Use NetworkX library for graph operations
- Implement dependency inference rules:
  - Setup tasks before implementation
  - Testing after implementation
  - Configuration before deployment
- Add cycle detection and resolution
- Include graph visualization data for frontend

---

### Task 6: Core Engine Integration
**Priority**: High
**Complexity**: Medium
**Estimated Duration**: 45 minutes

**Description**: Create main TaskDecompositionEngine class that orchestrates all components and provides the primary interface.

**Acceptance Criteria**:
- [ ] TaskDecompositionEngine class with clean public interface
- [ ] process_request() method that calls analyze → decompose → generate_dag
- [ ] Error handling for all failure modes
- [ ] Logging for debugging and monitoring
- [ ] Configuration management (timeouts, complexity thresholds)
- [ ] Thread-safe operation for concurrent requests
- [ ] Complete processing under 5 seconds total

**Dependencies**: Tasks 1-5 (needs all components)

**Technical Details**:
- Implement singleton or factory pattern for engine instance
- Add comprehensive error handling with specific exception types
- Include performance monitoring and metrics
- Configuration via environment variables or config file

---

### Task 7: Unit Test Suite
**Priority**: High
**Complexity**: Medium
**Estimated Duration**: 60 minutes

**Description**: Comprehensive unit test suite for all core decomposition functionality.

**Acceptance Criteria**:
- [ ] Test coverage > 90% for all core methods
- [ ] Unit tests for each data model validation
- [ ] Tests for analyze_task() with various input types
- [ ] Tests for decompose_task() with different complexity levels
- [ ] DAG generation tests including cycle detection
- [ ] Performance tests ensuring < 5 second total processing
- [ ] Error handling tests for edge cases
- [ ] All tests pass consistently

**Dependencies**: Tasks 1-6 (needs full implementation)

**Technical Details**:
- Use pytest framework
- Include fixtures for test data
- Mock external dependencies
- Performance benchmarks for regression testing
- Test data covering various domains and complexity levels

---

### Task 8: API Foundation and Error Handling
**Priority**: Medium
**Complexity**: Low
**Estimated Duration**: 30 minutes

**Description**: Set up basic FastAPI structure and error handling for future milestone integration.

**Acceptance Criteria**:
- [ ] Basic FastAPI app structure in place
- [ ] Custom exception classes for decomposition errors
- [ ] Error response models and handlers
- [ ] Health check endpoint
- [ ] Basic middleware for logging and monitoring
- [ ] CORS configuration for frontend integration

**Dependencies**: Task 6 (needs engine interface)

**Technical Details**:
- Follow existing project FastAPI patterns
- Include request/response logging
- Standardized error response format
- Rate limiting preparation for future endpoints

---

## Task Dependencies Graph

```
Task 1 (Data Models) → Task 2 (Database)
Task 1 → Task 3 (Analysis) → Task 4 (Decomposition) → Task 5 (DAG Generation)
Task 5 → Task 6 (Engine Integration) → Task 7 (Tests)
Task 6 → Task 8 (API Foundation)
```

## Execution Waves

**Wave 1 (Parallel)**: Task 1 (Data Models)
**Wave 2 (Parallel)**: Task 2 (Database), Task 3 (Analysis)  
**Wave 3 (Sequential)**: Task 4 (Decomposition)
**Wave 4 (Sequential)**: Task 5 (DAG Generation)
**Wave 5 (Sequential)**: Task 6 (Engine Integration)
**Wave 6 (Parallel)**: Task 7 (Tests), Task 8 (API Foundation)

## Resource Requirements

- **Total Estimated Duration**: 6.25 hours
- **Required Agents**: code_writer (primary), code_tester (for Task 7)
- **Critical Path**: Task 1 → Task 3 → Task 4 → Task 5 → Task 6
- **Key Technologies**: Pydantic, NetworkX, SQLite, FastAPI, pytest

## Success Criteria

- TaskDecompositionEngine processes requests in under 5 seconds
- All unit tests pass with >90% coverage
- DAG generation produces valid, cycle-free graphs
- Sub-task decomposition targets 30-40 minute chunks
- Foundation ready for Milestone 2 resource optimization