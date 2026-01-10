# Agent Registry - Complete Path Reference

**Purpose**: Single source of truth for all agent paths in the Ensemble system.

---

## Leadership Layer

| Agent | Path | Purpose | Can Write Code | Can Write Tests |
|-------|------|---------|----------------|-----------------|
| Executive Director | `leadership/executive_director` | Meta-orchestrator, manages entire project lifecycle | ❌ | ❌ |
| Development Manager | `leadership/development_manager` | Drives implementation from requirements through delivery | ❌ | ❌ |
| System Architect | `leadership/system_architect` | System architecture and technical design | ❌ | ❌ |
| TDD Coordinator | `leadership/tdd_coordinator` | TDD workflow coordinator, supervises test/code cycle | ❌ | ❌ |

## Coordinators (Task Breakdown)

| Agent | Path | Purpose | Can Write Code | Can Write Tests |
|-------|------|---------|----------------|-----------------|
| Backend Coordinator | `coordinators/backend_coordinator` | Break backend into API endpoints, models, routes | ❌ | ❌ |
| Frontend Coordinator | `coordinators/frontend_coordinator` | Break frontend into components, services, pages | ❌ | ❌ |
| Test Coordinator | `coordinators/test_coordinator` | Coordinate test strategy (unit, integration, e2e) | ❌ | ❌ |

## Developers (Code Writers & Leads)

| Agent | Path | Purpose | Can Write Code | Can Write Tests |
|-------|------|---------|----------------|-----------------|
| **Frontend Lead** | `developers/frontend_lead` | Supervise frontend code development | ❌ | ❌ |
| Frontend Developer | `developers/frontend_developer` | Write React/frontend code | ✅ | ❌ |
| **Backend Lead** | `developers/backend_lead` | Supervise backend code development | ❌ | ❌ |
| Backend Developer | `developers/backend_developer` | Write backend code (non-API) | ✅ | ❌ |
| **API Lead** | `developers/api_lead` | Supervise API development | ❌ | ❌ |
| API Developer | `developers/api_developer` | Write API code (FastAPI, REST endpoints) | ✅ | ❌ |
| **Component Lead** | `developers/component_lead` | Supervise component architecture | ❌ | ❌ |
| Component Developer | `developers/component_developer` | Write reusable component code | ✅ | ❌ |

## Testers (Test Writers & Leads)

| Agent | Path | Purpose | Can Write Code | Can Write Tests |
|-------|------|---------|----------------|-----------------|
| **Unit Test Lead** | `testers/unit_test_lead` | Supervise unit test development | ❌ | ❌ |
| Unit Test Writer | `testers/unit_test_writer` | Write unit tests | ❌ | ✅ |
| **Test Validator** | `testers/test_validator` | Validate test quality and coverage | ❌ | ❌ |
| Test Fixture Writer | `testers/test_fixture_writer` | Write test utilities and fixtures | ❌ | ✅ |
| **Integration Test Lead** | `testers/integration_test_lead` | Supervise integration testing | ❌ | ❌ |
| Integration Test Writer | `testers/integration_test_writer` | Write integration tests | ❌ | ✅ |

## Designers (Styling)

| Agent | Path | Purpose | Can Write Code | Can Write Tests |
|-------|------|---------|----------------|-----------------|
| **Style Lead** | `designers/style_lead` | Supervise styling and CSS work | ❌ | ❌ |
| Style Developer | `designers/style_developer` | Write CSS, Tailwind, styling code | ✅ | ❌ |

---

## Common Spawning Patterns

### Executive Director spawns:
```
spawn_agent("leadership/development_manager", {...})
```

### Development Manager spawns:
```
spawn_agent("leadership/system_architect", {...})         # For architecture
spawn_agent("coordinators/backend_coordinator", {...})   # For backend tasks
spawn_agent("coordinators/frontend_coordinator", {...})  # For frontend tasks
spawn_agent("coordinators/test_coordinator", {...})      # For test strategy
spawn_agent("leadership/tdd_coordinator", {...})          # For TDD implementation
```

### Coordinators spawn:
```
# Backend Coordinator spawns:
spawn_agent("developers/api_lead", {...})         # For API development
spawn_agent("developers/backend_lead", {...})     # For backend logic

# Frontend Coordinator spawns:
spawn_agent("developers/frontend_lead", {...})    # For UI components
spawn_agent("developers/component_lead", {...})   # For component architecture

# Test Coordinator spawns:
spawn_agent("testers/unit_test_lead", {...})           # For unit tests
spawn_agent("testers/integration_test_lead", {...})    # For integration tests
```

### TDD Coordinator spawns (TDD workflow):
```
# RED phase - Write tests first
spawn_agent("testers/unit_test_lead", {
  "task": "...",
  "test_file": "tests/test_feature.py",
  "code_file": "src/feature.py"
})

# GREEN phase - Write code to pass tests
spawn_agent("developers/api_lead", {          # Or frontend_lead, backend_lead
  "task": "...",
  "test_file": "tests/test_feature.py",
  "code_file": "src/feature.py",
  "requirements": "..."
})

# REFACTOR phase - Run Test Validator to validate
spawn_agent("testers/test_validator", {
  "test_file": "tests/test_feature.py",
  "code_file": "src/feature.py"
})
```

### Lead Agents spawn Developers/Writers:
```
# Unit Test Lead spawns Unit Test Writer
spawn_agent("testers/unit_test_writer", {
  "task": "...",
  "test_file": "tests/test_feature.py",
  "requirements": "..."
})

# Frontend Lead spawns Frontend Developer
spawn_agent("developers/frontend_developer", {
  "task": "...",
  "test_file": "tests/test_component.test.jsx",
  "code_file": "src/components/Component.jsx",
  "requirements": "..."
})

# API Lead spawns API Developer
spawn_agent("developers/api_developer", {
  "task": "...",
  "test_file": "tests/test_api.py",
  "code_file": "src/api/endpoint.py",
  "requirements": "..."
})
```

---

## ❌ NEVER Use These (Wrong Paths)

| ❌ Wrong (Old Drum Corps Names) | ✅ Correct (Standard Names) |
|---------|-----------|
| `program_coordinator` | `leadership/development_manager` |
| `leadership/program_coordinator` | `leadership/development_manager` |
| `designer` | `leadership/system_architect` |
| `leadership/designer` | `leadership/system_architect` |
| `drum_major` | `leadership/tdd_coordinator` |
| `leadership/drum_major` | `leadership/tdd_coordinator` |
| `caption_heads/backend_captain` | `coordinators/backend_coordinator` |
| `brass/trumpet` | `developers/frontend_developer` |
| `brass/tuba` | `developers/api_developer` |
| `percussion/snare` | `testers/unit_test_writer` |
| `guard/flag` | `designers/style_developer` |

---

## Agent Hierarchy

```
Executive Director (entry point)
  └─ Development Manager
      ├─ System Architect (architecture)
      ├─ Coordinators (task breakdown)
      │   ├─ Backend Coordinator
      │   ├─ Frontend Coordinator
      │   └─ Test Coordinator
      └─ TDD Coordinator (implementation)
          ├─ Leads (supervision)
          │   ├─ Frontend Lead → Frontend Developer
          │   ├─ Backend Lead → Backend Developer
          │   ├─ API Lead → API Developer
          │   ├─ Component Lead → Component Developer
          │   ├─ Unit Test Lead → Unit Test Writer
          │   ├─ Integration Test Lead → Integration Test Writer
          │   ├─ Test Validator (no writers)
          │   └─ Style Lead → Style Developer
          └─ Writers (implementation)
              ├─ Frontend Developer (code)
              ├─ Backend Developer (code)
              ├─ API Developer (code)
              ├─ Component Developer (code)
              ├─ Unit Test Writer (tests)
              ├─ Integration Test Writer (tests)
              ├─ Test Fixture Writer (tests)
              └─ Style Developer (styles)
```

---

## Agent Status Summary

| Status | Count | Agents |
|--------|-------|--------|
| ✅ Exists + Permissions | 26 | All leadership, coordinators, developers, testers, designers |
| ⚠️ Legacy Names Removed | N/A | Drum corps naming deprecated |

---

**Last Updated**: January 10, 2026 (after naming refactor)
**Total Agents**: 26 active agents
**Naming Scheme**: Standard developer terminology (no drum corps metaphor)
