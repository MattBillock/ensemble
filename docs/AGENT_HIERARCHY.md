# Agent Hierarchy and Spawn Permissions

This document defines the complete agent hierarchy, spawn permissions, and capability matrix for the Ensemble system.

## Hierarchy Overview

```
                                    USER
                                      │
                                      ▼
                        ┌─────────────────────────────┐
                        │     EXECUTIVE DIRECTOR      │
                        │  (leadership/executive_dir) │
                        │  can_write_code: false      │
                        │  can_write_tests: false     │
                        └─────────────┬───────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
    ┌───────────────────────┐  ┌───────────────┐  ┌───────────────────┐
    │  DEVELOPMENT MANAGER  │  │   QUESTION    │  │  SYSTEM POLISH    │
    │ (leadership/dev_mgr)  │  │    MARSHAL    │  │    DIRECTOR       │
    │ can_write: false      │  │ (leadership/) │  │ (leadership/)     │
    └───────────┬───────────┘  └───────────────┘  └───────────────────┘
                │
     ┌──────────┼──────────┬──────────────────────┐
     ▼          ▼          ▼                      ▼
┌─────────┐ ┌─────────┐ ┌─────────┐        ┌───────────┐
│ SYSTEM  │ │BACKEND  │ │FRONTEND │        │   TEST    │
│ARCHITECT│ │ COORD   │ │ COORD   │        │   COORD   │
└─────────┘ └────┬────┘ └────┬────┘        └─────┬─────┘
                 │           │                   │
                 └─────┬─────┘                   │
                       ▼                         ▼
              ┌────────────────┐        ┌────────────────┐
              │ TDD COORDINATOR│        │  CODE QUALITY  │
              │ (leadership/)  │        │   DIRECTOR     │
              │ can_write:false│        └────────────────┘
              └───────┬────────┘
                      │
      ┌───────────────┼───────────────┐
      ▼               ▼               ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│ BACKEND   │  │ FRONTEND  │  │   API     │
│   LEAD    │  │   LEAD    │  │   LEAD    │
│(developers)│  │(developers)│ │(developers)│
└─────┬─────┘  └─────┬─────┘  └─────┬─────┘
      │              │              │
      ▼              ▼              ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│ BACKEND   │  │ FRONTEND  │  │   API     │
│ DEVELOPER │  │ DEVELOPER │  │ DEVELOPER │
│can_code:T │  │can_code:T │  │can_code:T │
└───────────┘  └───────────┘  └───────────┘

                      │
      ┌───────────────┼───────────────┐
      ▼               ▼               ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│ UNIT TEST │  │INTEGRATION│  │  API TEST │
│   LEAD    │  │ TEST LEAD │  │  WRITER   │
│(testers/) │  │(testers/) │  │can_tests:T│
└─────┬─────┘  └─────┬─────┘  └───────────┘
      │              │
      ▼              ▼
┌───────────┐  ┌───────────┐
│ UNIT TEST │  │INTEGRATION│
│  WRITER   │  │TEST WRITER│
│can_tests:T│  │can_tests:T│
└───────────┘  └───────────┘
```

## Spawn Permission Matrix

### Leadership Tier (Strategic)

| Agent | Can Spawn | Cannot Spawn |
|-------|-----------|--------------|
| **Executive Director** | `leadership/development_manager` | Any code writers, any test writers |
| **Development Manager** | `leadership/system_architect`, `coordinators/*`, `leadership/tdd_coordinator` | Developers directly, testers directly |
| **System Architect** | None - produces documents only | Everything |
| **Question Marshal** | None - queries parent only | Everything |
| **Code Quality Director** | `support/ci_agent`, `support/code_reviewer` | Code writers |
| **System Polish Director** | `support/*` analysis agents | Code writers |
| **TDD Coordinator** | `developers/*_lead`, `testers/*_lead` | Code writers directly |

### Coordinator Tier (Planning)

| Agent | Can Spawn | Cannot Spawn |
|-------|-----------|--------------|
| **Backend Coordinator** | None - produces task breakdown only | Everything |
| **Frontend Coordinator** | None - produces task breakdown only | Everything |
| **Test Coordinator** | None - produces test strategy only | Everything |

### Lead Tier (Supervision)

| Agent | Can Spawn | Cannot Spawn |
|-------|-----------|--------------|
| **Backend Lead** | `developers/backend_developer` | Other leads, coordinators |
| **Frontend Lead** | `developers/frontend_developer` | Other leads, coordinators |
| **API Lead** | `developers/api_developer` | Other leads, coordinators |
| **Unit Test Lead** | `testers/unit_test_writer` | Code writers, other leads |
| **Integration Test Lead** | `testers/integration_test_writer` | Code writers, other leads |

### Developer Tier (Implementation)

| Agent | Can Spawn | Capabilities |
|-------|-----------|--------------|
| **Backend Developer** | None | `can_write_code: true`, `can_write_tests: false` |
| **Frontend Developer** | None | `can_write_code: true`, `can_write_tests: false` |
| **API Developer** | None | `can_write_code: true`, `can_write_tests: false` |
| **Database Manager** | None | `can_write_code: true` (migrations only) |

### Tester Tier (Verification)

| Agent | Can Spawn | Capabilities |
|-------|-----------|--------------|
| **Unit Test Writer** | None | `can_write_code: false`, `can_write_tests: true` |
| **Integration Test Writer** | None | `can_write_code: false`, `can_write_tests: true` |
| **API Test Writer** | None | `can_write_code: false`, `can_write_tests: true` |

### Support Tier (Services)

| Agent | Can Spawn | Capabilities |
|-------|-----------|--------------|
| **Code Reviewer** | None | Read only |
| **CI Agent** | None | Run commands only |
| **Visual Tech** | None | `can_write_code: true` (refactoring only) |
| **Logistics Manager** | None | Read and explore only |
| **Knowledge Repository** | None | Read and write ADRs only |
| **Drill Writer** | None | Write documentation only |
| **Parameter Enhancer** | None | Read and analyze only |
| **Agent Refactorer** | None | Write agent definitions only |
| **State Evolution Agent** | None | Database maintenance only |

## Key Rules

### 1. Code Writing Authority
Only these agents have `can_write_code: true`:
- Backend Developer
- Frontend Developer
- API Developer
- Database Manager (migrations only)
- Visual Tech (refactoring only)

### 2. Test Writing Authority
Only these agents have `can_write_tests: true`:
- Unit Test Writer
- Integration Test Writer
- API Test Writer

### 3. Spawn Chain
Agents can ONLY spawn agents in the tier below them:
- **Leadership** → Coordinators, other Leadership (lateral), TDD Coordinator
- **TDD Coordinator** → Leads
- **Leads** → Writers/Developers
- **Writers/Developers** → Nothing (leaf nodes)
- **Support** → Nothing (service tier)

### 4. Forbidden Spawns
**NEVER** spawn:
- Code writers from Leadership tier (except through TDD Coordinator chain)
- Test writers directly (always through Test Leads)
- Upward in hierarchy (child cannot spawn parent)
- Across domains (Backend Lead cannot spawn Frontend Developer)

## Spawn Validation

Before calling `spawn_agent()`, validate:

```python
# Pseudocode for spawn validation
def validate_spawn(caller_agent, target_agent):
    # Check tier order
    if get_tier(target_agent) <= get_tier(caller_agent):
        raise Error("Cannot spawn same or higher tier")

    # Check domain alignment
    if not domains_compatible(caller_agent, target_agent):
        raise Error("Domain mismatch")

    # Check permissions
    if requires_code_write(target_task) and not agent_can_write_code(target_agent):
        raise Error("Target agent cannot write code")

    return True
```

## Agent Path Reference

### Leadership (`leadership/`)
- `leadership/executive_director`
- `leadership/development_manager`
- `leadership/system_architect`
- `leadership/tdd_coordinator`
- `leadership/question_marshal`
- `leadership/code_quality_director`
- `leadership/system_polish_director`

### Coordinators (`coordinators/`)
- `coordinators/backend_coordinator`
- `coordinators/frontend_coordinator`
- `coordinators/test_coordinator`

### Developers (`developers/`)
- `developers/backend_developer`
- `developers/frontend_developer`
- `developers/api_developer`
- `developers/backend_lead`
- `developers/frontend_lead`
- `developers/api_lead`
- `developers/database_manager`

### Testers (`testers/`)
- `testers/unit_test_writer`
- `testers/unit_test_lead`
- `testers/integration_test_writer`
- `testers/integration_test_lead`
- `testers/api_test_writer`

### Support (`support/`)
- `support/code_reviewer`
- `support/ci_agent`
- `support/visual_tech`
- `support/logistics_manager`
- `support/knowledge_repository`
- `support/drill_writer`
- `support/parameter_enhancer`
- `support/agent_refactorer`
- `support/state_evolution_agent`

## Domain Alignment

```
Backend Domain:
  Backend Coordinator → Backend Lead → Backend Developer

Frontend Domain:
  Frontend Coordinator → Frontend Lead → Frontend Developer

API Domain:
  Backend Coordinator → API Lead → API Developer

Testing Domain:
  Test Coordinator → Unit Test Lead → Unit Test Writer
  Test Coordinator → Integration Test Lead → Integration Test Writer
```

## Recovery System Integration

When the recovery system needs to spawn replacement agents, it respects the hierarchy:
- Only spawns at the same tier level as the failed agent
- Uses parent context to determine appropriate spawn
- Never escalates directly to code writers from recovery

## Updates

This document should be updated when:
- New agents are added to the ensemble
- Agent permissions change
- Hierarchy structure is modified
- New spawn rules are introduced
