# Agent Hierarchy and Spawning Relationships

This document describes the complete agent hierarchy, spawning relationships, and supervision structure in the Ensemble system.

## Overview

Ensemble uses a hierarchical multi-agent system where agents are organized by role and capability. Each agent has specific permissions and can only spawn designated subordinates.

## Agent Categories

### Leadership (Strategic Layer)
Strategic agents that coordinate the overall development process.

| Agent | Purpose | Can Write Code | Model Preference |
|-------|---------|----------------|------------------|
| Executive Director | System orchestrator and entry point | No | Opus |
| Development Manager | Drives implementation from requirements through delivery | No | Sonnet |
| System Architect | Defines system architecture and technical design | No | Sonnet |
| TDD Coordinator | Orchestrates test-driven development workflow | No | Sonnet |
| Bug Fix Director | Autonomous bug fixing | No | Sonnet |
| Code Quality Director | Quality enforcement | No | Sonnet |
| System Polish Director | System optimization | No | Sonnet |
| Question Marshal | Question resolution | No | Haiku |

### Coordinators (Planning Layer)
Agents that break down tasks and define strategy.

| Agent | Purpose | Can Write Code | Model Preference |
|-------|---------|----------------|------------------|
| Backend Coordinator | Breaks backend work into API, model, and service tasks | No | Sonnet |
| Frontend Coordinator | Breaks frontend into components, pages, and services | No | Sonnet |
| Test Coordinator | Defines comprehensive test strategy | No | Sonnet |

### Developers (Implementation Layer)
Agents that write production code.

| Agent | Purpose | Can Write Code | Model Preference |
|-------|---------|----------------|------------------|
| Backend Lead | Backend supervision | No | Sonnet |
| Backend Developer | Backend code implementation | Yes | Haiku |
| Frontend Lead | Frontend supervision | No | Sonnet |
| Frontend Developer | Frontend code implementation | Yes | Haiku |
| API Lead | API development supervision | No | Sonnet |
| API Developer | API endpoint implementation | Yes | Haiku |
| Database Manager | Database schema and migrations | Yes | Sonnet |

### Testers (Quality Layer)
Agents that write tests.

| Agent | Purpose | Can Write Tests | Model Preference |
|-------|---------|-----------------|------------------|
| Unit Test Lead | Unit test supervision | No | Sonnet |
| Unit Test Writer | Unit test implementation | Yes | Haiku |
| Integration Test Lead | Integration test supervision | No | Sonnet |
| Integration Test Writer | Integration test implementation | Yes | Haiku |
| API Test Writer | API endpoint test implementation | Yes | Haiku |

### Designers (Styling Layer)
Agents that handle styling and visual design.

| Agent | Purpose | Can Write Code | Model Preference |
|-------|---------|----------------|------------------|
| Style Developer | CSS, Tailwind, and styling code | Yes | Haiku |

---

## Spawning Hierarchy

```
Executive Director (ROOT)
│
└─→ Development Manager
    │
    ├─→ System Architect
    │
    ├─→ Backend Coordinator ──────→ (no spawning - breakdown agent)
    │
    ├─→ Frontend Coordinator ─────→ (no spawning - breakdown agent)
    │
    ├─→ Test Coordinator ─────────→ (no spawning - breakdown agent)
    │
    ├─→ Code Quality Director ────→ CI Agent, Code Reviewer, etc.
    │
    ├─→ System Polish Director ───→ Various optimization agents
    │
    └─→ TDD Coordinator
        │
        ├─→ Backend Lead
        │   ├─→ Backend Developer
        │   └─→ Database Manager
        │
        ├─→ Frontend Lead
        │   ├─→ Frontend Developer
        │   └─→ Style Developer
        │
        ├─→ API Lead
        │   └─→ API Developer
        │
        ├─→ Unit Test Lead
        │   └─→ Unit Test Writer
        │
        └─→ Integration Test Lead
            └─→ Integration Test Writer
```

---

## Spawning Rules

### Who Can Spawn Whom

| Parent Agent | Can Spawn |
|--------------|-----------|
| Executive Director | Development Manager |
| Development Manager | System Architect, Backend Coordinator, Frontend Coordinator, Test Coordinator, TDD Coordinator, Code Quality Director, System Polish Director |
| TDD Coordinator | Backend Lead, Frontend Lead, API Lead, Unit Test Lead, Integration Test Lead |
| Backend Lead | Backend Developer, Database Manager |
| Frontend Lead | Frontend Developer, Style Developer |
| API Lead | API Developer |
| Unit Test Lead | Unit Test Writer |
| Integration Test Lead | Integration Test Writer |
| Bug Fix Director | Various sub-agents as needed |

### Key Constraints

1. **No Upward Spawning**: Agents cannot spawn their supervisors or peers
2. **No Skip-Level Spawning**: Must go through hierarchy (e.g., TDD Coordinator cannot spawn Backend Developer directly)
3. **Permission Enforcement**: `can_write_code: false` prevents supervisors from writing code
4. **Fail-Fast**: If spawn fails, agents return error (no fallback to writing code)

---

## Supervision Relationships

| Agent | Supervised By | Supervises |
|-------|---------------|------------|
| Executive Director | (Root - no supervisor) | Development Manager |
| Development Manager | Executive Director | System Architect, Coordinators, TDD Coordinator |
| System Architect | Development Manager | (Specialist - no subordinates) |
| TDD Coordinator | Development Manager | All Leads |
| Backend Coordinator | Development Manager | (Breakdown agent) |
| Frontend Coordinator | Development Manager | (Breakdown agent) |
| Test Coordinator | Development Manager | (Breakdown agent) |
| Backend Lead | TDD Coordinator | Backend Developer, Database Manager |
| Frontend Lead | TDD Coordinator | Frontend Developer, Style Developer |
| API Lead | TDD Coordinator | API Developer |
| Unit Test Lead | TDD Coordinator | Unit Test Writer |
| Integration Test Lead | TDD Coordinator | Integration Test Writer |
| All Developers/Writers | Their respective Leads | (None - execution layer) |

---

## TDD Workflow

The system follows Red-Green-Refactor:

1. **RED Phase**: Test Writers create failing tests
2. **GREEN Phase**: Developers write minimal code to pass tests
3. **REFACTOR Phase**: Visual Tech improves code while maintaining tests

```
TDD Coordinator
    │
    ├─→ (RED) Test Leads spawn Test Writers
    │         └─→ Failing tests created
    │
    ├─→ (GREEN) Code Leads spawn Developers
    │           └─→ Minimal passing code
    │
    └─→ (REFACTOR) Visual Tech
                   └─→ Code improvement
```

---

## Standard Development Flow

```
User Request
    │
    └─→ Executive Director
        └─→ Development Manager
            ├─→ System Architect (if architecture needed)
            ├─→ Coordinators (task breakdown)
            └─→ TDD Coordinator (execution)
                └─→ Leads → Developers/Writers
                    └─→ Deliverables
```

---

## Bug Fix Flow (Autonomous)

```
Bug Report (via API)
    │
    └─→ Bug Fix Director
        ├─→ Analyze bug
        ├─→ Spawn appropriate specialists
        ├─→ Apply fixes
        └─→ Generate completion report
```

---

## Support Agents

These agents provide cross-cutting functionality:

| Agent | Purpose | When Used |
|-------|---------|-----------|
| Code Reviewer | Quality gate before commits | After code is written |
| Visual Tech | Code refactoring | REFACTOR phase of TDD |
| Drill Writer | Documentation | When docs are needed |
| Logistics Manager | Codebase exploration | Research tasks |
| Question Marshal | Escalation handling | When agents need clarification |

---

## Agent Definition Files

Agent definitions are stored as Markdown files:

```
ensemble/
├── leadership/           # Strategic agents
│   ├── executive_director.md
│   ├── development_manager.md
│   ├── system_architect.md
│   └── tdd_coordinator.md
├── coordinators/         # Planning agents
│   ├── backend_coordinator.md
│   ├── frontend_coordinator.md
│   └── test_coordinator.md
├── developers/           # Implementation agents
│   ├── backend_lead.md
│   ├── backend_developer.md
│   ├── frontend_lead.md
│   ├── frontend_developer.md
│   └── ...
├── testers/              # Quality agents
│   ├── unit_test_lead.md
│   ├── unit_test_writer.md
│   └── ...
├── designers/            # Styling agents
│   └── style_developer.md
└── support/              # Cross-cutting agents
    ├── code_reviewer.md
    └── visual_tech.md
```

Each definition file contains:
- Purpose and responsibilities
- Instantiation/termination conditions
- Input/output formats
- Available tools
- Supervision relationships
- Model preference
- Code writing permissions
