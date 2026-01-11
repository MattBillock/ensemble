# Agent Registry - Complete List (Post-Consolidation)

## Overview
**Total Agents**: 16 (reduced from 23 = 30% consolidation)
**Last Updated**: 2026-01-10

## Agent Hierarchy

```
Executive Director (strategic)
├── Development Manager (strategic)
│   ├── System Architect (strategic)
│   ├── Backend Coordinator (tactical)
│   │   ├── Backend Lead (supervises)
│   │   └── Backend Developer (implements)
│   ├── Frontend Coordinator (tactical)
│   │   ├── Frontend Lead (supervises)
│   │   └── Frontend Developer (implements)
│   ├── Test Coordinator (tactical)
│   │   ├── Unit Test Lead (supervises)
│   │   │   └── Unit Test Writer (writes)
│   │   └── Integration Test Lead (supervises)
│   │       └── Integration Test Writer (writes)
│   └── TDD Coordinator (workflow enforcer)
└── Style Developer (UI/UX design)
```

## Agents by Tier

### Leadership Tier (4 agents) - Strategic Decision Making
**Path**: `leadership/`

1. **Executive Director** (`executive_director.md`)
   - **Role**: Meta-orchestrator for entire ensemble
   - **Spawns**: Development Manager
   - **Model**: haiku (quick delegation)
   - **Permissions**: can_write_code: false, can_write_tests: false

2. **Development Manager** (`development_manager.md`)
   - **Role**: Drive development from requirements through delivery
   - **Spawns**: System Architect, Coordinators, TDD Coordinator
   - **Model**: sonnet (strategic planning)
   - **Permissions**: can_write_code: false, can_write_tests: false

3. **System Architect** (`system_architect.md`)
   - **Role**: Design system architecture, technology choices
   - **Spawns**: None
   - **Model**: opus (architectural decisions)
   - **Permissions**: can_write_code: false, can_write_tests: false

4. **TDD Coordinator** (`tdd_coordinator.md`)
   - **Role**: Enforce Test-Driven Development workflow (RED-GREEN-REFACTOR)
   - **Spawns**: Test Leads
   - **Model**: sonnet (workflow enforcement)
   - **Permissions**: can_write_code: false, can_write_tests: false

### Coordinator Tier (3 agents) - Tactical Coordination
**Path**: `coordinators/`

5. **Backend Coordinator** (`backend_coordinator.md`)
   - **Role**: Coordinate backend development tasks
   - **Spawns**: Backend Lead
   - **Model**: haiku
   - **Permissions**: can_write_code: false, can_write_tests: false

6. **Frontend Coordinator** (`frontend_coordinator.md`)
   - **Role**: Coordinate frontend development tasks
   - **Spawns**: Frontend Lead
   - **Model**: haiku
   - **Permissions**: can_write_code: false, can_write_tests: false

7. **Test Coordinator** (`test_coordinator.md`)
   - **Role**: Coordinate testing strategy and coverage
   - **Spawns**: Unit Test Lead, Integration Test Lead (via TDD Coordinator)
   - **Model**: haiku
   - **Permissions**: can_write_code: false, can_write_tests: false

### Developer Tier (4 agents) - Implementation
**Path**: `developers/`

8. **Backend Lead** (`backend_lead.md`)
   - **Role**: Supervise backend developers, code review, API design
   - **Spawns**: Backend Developer
   - **Model**: haiku
   - **Permissions**: can_write_code: false, can_write_tests: false
   - **Scope**: Server-side logic, databases, APIs, microservices

9. **Backend Developer** (`backend_developer.md`)
   - **Role**: Implement backend code (Python, Node.js, Go, etc.)
   - **Spawns**: None
   - **Model**: haiku
   - **Permissions**: can_write_code: TRUE, can_write_tests: false
   - **Scope**: Server code, API endpoints, data models, business logic

10. **Frontend Lead** (`frontend_lead.md`)
    - **Role**: Supervise frontend developers, component architecture, UI/UX coordination
    - **Spawns**: Frontend Developer
    - **Model**: haiku
    - **Permissions**: can_write_code: false, can_write_tests: false
    - **Scope**: React/Vue/Angular apps, components, state management, routing

11. **Frontend Developer** (`frontend_developer.md`)
    - **Role**: Implement frontend code (React, Vue, Angular, etc.)
    - **Spawns**: None
    - **Model**: haiku
    - **Permissions**: can_write_code: TRUE, can_write_tests: false
    - **Scope**: UI components, client-side logic, styling integration

### Tester Tier (4 agents) - Quality Assurance
**Path**: `testers/`

12. **Unit Test Lead** (`unit_test_lead.md`)
    - **Role**: Supervise unit test creation, coverage analysis
    - **Spawns**: Unit Test Writer
    - **Model**: haiku
    - **Permissions**: can_write_code: false, can_write_tests: false

13. **Unit Test Writer** (`unit_test_writer.md`)
    - **Role**: Write unit tests (pytest, Jest, etc.)
    - **Spawns**: None
    - **Model**: haiku
    - **Permissions**: can_write_code: false, can_write_tests: TRUE
    - **Focus**: Individual functions/methods, isolated behavior

14. **Integration Test Lead** (`integration_test_lead.md`)
    - **Role**: Supervise integration test creation
    - **Spawns**: Integration Test Writer
    - **Model**: haiku
    - **Permissions**: can_write_code: false, can_write_tests: false

15. **Integration Test Writer** (`integration_test_writer.md`)
    - **Role**: Write integration tests (API tests, E2E, etc.)
    - **Spawns**: None
    - **Model**: haiku
    - **Permissions**: can_write_code: false, can_write_tests: TRUE
    - **Focus**: Component interactions, API contracts, workflows

### Designer Tier (1 agent) - UI/UX Design
**Path**: `designers/`

16. **Style Developer** (`style_developer.md`)
    - **Role**: Create stylesheets, design systems, theming
    - **Spawns**: None
    - **Model**: haiku
    - **Permissions**: can_write_code: true (CSS/SCSS counts as code), can_write_tests: false
    - **Scope**: CSS, SCSS, Tailwind, styled-components

## Agent Spawn Patterns

### Typical Full Pipeline
```
1. User → Executive Director (requirements.md)
2. Executive Director → Development Manager
3. Development Manager → System Architect (architecture.md)
4. Development Manager → Backend Coordinator (backend_tasks.md)
5. Backend Coordinator → Backend Lead
6. Backend Lead → Backend Developer (code files)
7. Development Manager → TDD Coordinator (enforce TDD)
8. TDD Coordinator → Unit Test Lead
9. Unit Test Lead → Unit Test Writer (test files)
10. TDD Coordinator → Backend Developer (GREEN phase - make tests pass)
```

### Validation at Each Level
- **Spawn failure**: Supervisor returns error, DOES NOT write code
- **Missing inputs**: Spawn fails immediately with clear error
- **Permission violation**: WriteFileTool blocks, logs ROGUE AGENT

## Model Recommendations by Complexity

### Strategic (High Reasoning)
- Executive Director: haiku (delegates quickly)
- Development Manager: **sonnet** ← UPGRADED from haiku
- System Architect: **opus** ← UPGRADED from haiku
- TDD Coordinator: **sonnet** ← UPGRADED from haiku

### Creative (Language/Design)
- All Developers: haiku
- Style Developer: haiku
- Integration Test Writer: haiku

### Routine (Validation/Execution)
- Coordinators: haiku
- Leads: haiku
- Unit Test Writer: haiku

## Changes from Previous Version

### Deleted Agents (7 total)
- ❌ `component_lead.md` → merged into `frontend_lead.md`
- ❌ `component_developer.md` → merged into `frontend_developer.md`
- ❌ `api_lead.md` → merged into `backend_lead.md`
- ❌ `api_developer.md` → merged into `backend_developer.md`
- ❌ `test_validator.md` → functionality merged into test leads
- ❌ `test_fixture_writer.md` → merged into test writers
- ❌ `style_lead.md` → merged into `style_developer.md`
- ❌ `AGENT_ROSTER.md` → deprecated, deleted

### Consolidation Impact
- **Before**: 23 agents (16 supervisors + 7 writers)
- **After**: 16 agents (11 supervisors + 5 writers)
- **Reduction**: 30% fewer agents
- **Benefit**: Fewer coordination failures, clearer responsibilities

## Path Reference (Quick Lookup)

```
leadership/executive_director.md
leadership/development_manager.md
leadership/system_architect.md
leadership/tdd_coordinator.md

coordinators/backend_coordinator.md
coordinators/frontend_coordinator.md
coordinators/test_coordinator.md

developers/backend_lead.md
developers/backend_developer.md
developers/frontend_lead.md
developers/frontend_developer.md

testers/unit_test_lead.md
testers/unit_test_writer.md
testers/integration_test_lead.md
testers/integration_test_writer.md

designers/style_developer.md
```

## Common Spawn Mistakes to Avoid

1. ❌ `spawn_agent("program_coordinator", ...)` → ✅ `spawn_agent("leadership/development_manager", ...)`
2. ❌ Missing required input field → ✅ Check agent's Input Format before spawning
3. ❌ Supervisor writes code → ✅ Supervisor spawns developer
4. ❌ Skipping TDD cycle → ✅ Tests first (RED), then code (GREEN)

## See Also
- `README.md` - System overview
- `COMPREHENSIVE_SYSTEM_REVIEW.md` - Performance analysis
- `ITERATIVE_IMPROVEMENT_PLAN.md` - Development workflow
- Individual agent .md files for detailed instructions
