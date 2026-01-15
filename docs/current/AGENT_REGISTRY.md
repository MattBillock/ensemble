# Agent Registry - Complete List

## Overview
**Total Agents**: 23
**Last Updated**: 2026-01-14

## Agent Hierarchy

```
Executive Director (strategic)
├── Development Manager (strategic)
│   ├── System Architect (strategic)
│   ├── Backend Coordinator (tactical)
│   │   ├── Backend Lead (supervises)
│   │   │   └── Backend Developer (implements)
│   │   ├── API Lead (supervises)
│   │   │   └── API Developer (implements)
│   │   └── Database Manager (implements)
│   ├── Frontend Coordinator (tactical)
│   │   ├── Frontend Lead (supervises)
│   │   └── Frontend Developer (implements)
│   ├── Test Coordinator (tactical)
│   │   ├── Unit Test Lead (supervises)
│   │   │   └── Unit Test Writer (writes)
│   │   ├── Integration Test Lead (supervises)
│   │   │   └── Integration Test Writer (writes)
│   │   └── API Test Writer (writes)
│   └── TDD Coordinator (workflow enforcer)
├── Code Quality Director (quality analysis)
├── System Polish Director (system optimization)
├── Question Marshal (user interaction)
└── Style Developer (UI/UX design)
```

## Agents by Tier

### Leadership Tier (7 agents) - Strategic Decision Making
**Path**: `leadership/`

1. **Executive Director** (`executive_director.md`)
   - **Role**: Meta-orchestrator for entire ensemble
   - **Spawns**: Development Manager, Code Quality Director, System Polish Director, Question Marshal
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

5. **Code Quality Director** (`code_quality_director.md`)
   - **Role**: Analyze code quality, identify improvement areas
   - **Spawns**: None
   - **Model**: sonnet
   - **Permissions**: can_write_code: false, can_write_tests: false

6. **System Polish Director** (`system_polish_director.md`)
   - **Role**: System-wide optimization and polishing
   - **Spawns**: None
   - **Model**: sonnet
   - **Permissions**: can_write_code: false, can_write_tests: false

7. **Question Marshal** (`question_marshal.md`)
   - **Role**: Manage user interactions and clarifying questions
   - **Spawns**: None
   - **Model**: haiku
   - **Permissions**: can_write_code: false, can_write_tests: false

### Coordinator Tier (3 agents) - Tactical Coordination
**Path**: `coordinators/`

8. **Backend Coordinator** (`backend_coordinator.md`)
   - **Role**: Coordinate backend development tasks
   - **Spawns**: Backend Lead, API Lead, Database Manager
   - **Model**: haiku
   - **Permissions**: can_write_code: false, can_write_tests: false

9. **Frontend Coordinator** (`frontend_coordinator.md`)
   - **Role**: Coordinate frontend development tasks
   - **Spawns**: Frontend Lead
   - **Model**: haiku
   - **Permissions**: can_write_code: false, can_write_tests: false

10. **Test Coordinator** (`test_coordinator.md`)
    - **Role**: Coordinate testing strategy and coverage
    - **Spawns**: Unit Test Lead, Integration Test Lead
    - **Model**: haiku
    - **Permissions**: can_write_code: false, can_write_tests: false

### Developer Tier (7 agents) - Implementation
**Path**: `developers/`

11. **Backend Lead** (`backend_lead.md`)
    - **Role**: Supervise backend developers, code review
    - **Spawns**: Backend Developer
    - **Model**: haiku
    - **Permissions**: can_write_code: false, can_write_tests: false
    - **Scope**: Server-side logic, databases, APIs

12. **Backend Developer** (`backend_developer.md`)
    - **Role**: Implement backend code (Python, Node.js, Go, etc.)
    - **Spawns**: None
    - **Model**: haiku
    - **Permissions**: can_write_code: TRUE, can_write_tests: false
    - **Scope**: Server code, data models, business logic

13. **API Lead** (`api_lead.md`)
    - **Role**: Supervise API developers, API design
    - **Spawns**: API Developer
    - **Model**: haiku
    - **Permissions**: can_write_code: false, can_write_tests: false
    - **Scope**: REST APIs, GraphQL, API contracts

14. **API Developer** (`api_developer.md`)
    - **Role**: Implement API endpoints
    - **Spawns**: None
    - **Model**: haiku
    - **Permissions**: can_write_code: TRUE, can_write_tests: false
    - **Scope**: API endpoints, request/response handling

15. **Database Manager** (`database_manager.md`)
    - **Role**: Manage database schema, migrations, queries
    - **Spawns**: None
    - **Model**: haiku
    - **Permissions**: can_write_code: TRUE, can_write_tests: false
    - **Scope**: SQL, ORMs, migrations, query optimization

16. **Frontend Lead** (`frontend_lead.md`)
    - **Role**: Supervise frontend developers, component architecture
    - **Spawns**: Frontend Developer
    - **Model**: haiku
    - **Permissions**: can_write_code: false, can_write_tests: false
    - **Scope**: React/Vue/Angular apps, components, state management

17. **Frontend Developer** (`frontend_developer.md`)
    - **Role**: Implement frontend code (React, Vue, Angular, etc.)
    - **Spawns**: None
    - **Model**: haiku
    - **Permissions**: can_write_code: TRUE, can_write_tests: false
    - **Scope**: UI components, client-side logic, styling

### Tester Tier (5 agents) - Quality Assurance
**Path**: `testers/`

18. **Unit Test Lead** (`unit_test_lead.md`)
    - **Role**: Supervise unit test creation, coverage analysis
    - **Spawns**: Unit Test Writer
    - **Model**: haiku
    - **Permissions**: can_write_code: false, can_write_tests: false

19. **Unit Test Writer** (`unit_test_writer.md`)
    - **Role**: Write unit tests (pytest, Jest, etc.)
    - **Spawns**: None
    - **Model**: haiku
    - **Permissions**: can_write_code: false, can_write_tests: TRUE
    - **Focus**: Individual functions/methods, isolated behavior

20. **Integration Test Lead** (`integration_test_lead.md`)
    - **Role**: Supervise integration test creation
    - **Spawns**: Integration Test Writer
    - **Model**: haiku
    - **Permissions**: can_write_code: false, can_write_tests: false

21. **Integration Test Writer** (`integration_test_writer.md`)
    - **Role**: Write integration tests (E2E, etc.)
    - **Spawns**: None
    - **Model**: haiku
    - **Permissions**: can_write_code: false, can_write_tests: TRUE
    - **Focus**: Component interactions, workflows

22. **API Test Writer** (`api_test_writer.md`)
    - **Role**: Write API contract tests
    - **Spawns**: None
    - **Model**: haiku
    - **Permissions**: can_write_code: false, can_write_tests: TRUE
    - **Focus**: API contracts, request/response validation

### Designer Tier (1 agent) - UI/UX Design
**Path**: `designers/`

23. **Style Developer** (`style_developer.md`)
    - **Role**: Create stylesheets, design systems, theming
    - **Spawns**: None
    - **Model**: haiku
    - **Permissions**: can_write_code: true (CSS/SCSS counts as code), can_write_tests: false
    - **Scope**: CSS, SCSS, Tailwind, styled-components

## Path Reference (Quick Lookup)

```
leadership/executive_director.md
leadership/development_manager.md
leadership/system_architect.md
leadership/tdd_coordinator.md
leadership/code_quality_director.md
leadership/system_polish_director.md
leadership/question_marshal.md

coordinators/backend_coordinator.md
coordinators/frontend_coordinator.md
coordinators/test_coordinator.md

developers/backend_lead.md
developers/backend_developer.md
developers/api_lead.md
developers/api_developer.md
developers/database_manager.md
developers/frontend_lead.md
developers/frontend_developer.md

testers/unit_test_lead.md
testers/unit_test_writer.md
testers/integration_test_lead.md
testers/integration_test_writer.md
testers/api_test_writer.md

designers/style_developer.md
```

## Model Recommendations by Complexity

### Strategic (High Reasoning)
- Executive Director: haiku (delegates quickly)
- Development Manager: **sonnet**
- System Architect: **opus**
- TDD Coordinator: **sonnet**
- Code Quality Director: **sonnet**
- System Polish Director: **sonnet**

### Creative (Language/Design)
- All Developers: haiku
- Style Developer: haiku
- Test Writers: haiku

### Routine (Validation/Execution)
- Coordinators: haiku
- Leads: haiku
- Question Marshal: haiku

## Validation at Each Level
- **Spawn failure**: Supervisor returns error, DOES NOT write code
- **Missing inputs**: Spawn fails immediately with clear error
- **Permission violation**: WriteFileTool blocks, logs ROGUE AGENT

## Common Spawn Mistakes to Avoid

1. Missing required input field - Check agent's Input Format before spawning
2. Supervisor writes code - Supervisor spawns developer
3. Skipping TDD cycle - Tests first (RED), then code (GREEN)
