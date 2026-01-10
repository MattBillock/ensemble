# Agent Registry - Complete Path Reference

**Purpose**: Single source of truth for all agent paths in the Ensemble system.

---

## Leadership Layer

| Agent | Path | Purpose | Can Write Code | Can Write Tests |
|-------|------|---------|----------------|-----------------|
| Executive Director | `leadership/executive_director` | Meta-orchestrator, manages entire project lifecycle | ❌ | ❌ |
| Program Coordinator | `leadership/program_coordinator` | Drives implementation from requirements through delivery | ❌ | ❌ |
| Designer | `leadership/designer` | System architecture and technical design | ❌ | ❌ |
| Drum Major | `leadership/drum_major` | TDD workflow coordinator, supervises test/code cycle | ❌ | ❌ |

## Caption Heads (Task Breakdown)

| Agent | Path | Purpose | Can Write Code | Can Write Tests |
|-------|------|---------|----------------|-----------------|
| Backend Captain | `caption_heads/backend_captain` | **MISSING** - Break backend into API endpoints, models, routes | ❌ | ❌ |
| Frontend Captain | `caption_heads/frontend_captain` | **MISSING** - Break frontend into components, services, pages | ❌ | ❌ |
| Test Captain | `caption_heads/test_captain` | **MISSING** - Coordinate test strategy (unit, integration, e2e) | ❌ | ❌ |

## Brass Section (Code Writers & Supervisors)

| Agent | Path | Purpose | Can Write Code | Can Write Tests |
|-------|------|---------|----------------|-----------------|
| **Trumpet Tech** | `brass/trumpet_tech` | Supervise frontend code development | ❌ | ❌ |
| Trumpet | `brass/trumpet` | Write React/frontend code | ✅ | ❌ |
| **Baritone Tech** | `brass/baritone_tech` | Supervise backend code development | ❌ | ❌ |
| Baritone | `brass/baritone` | Write backend code (non-API) | ✅ | ❌ |
| **Tuba Tech** | `brass/tuba_tech` | Supervise API development | ❌ | ❌ |
| Tuba | `brass/tuba` | Write API code (FastAPI, REST endpoints) | ✅ | ❌ |
| **Horn Tech** | `brass/horn_tech` | Supervise component architecture | ❌ | ❌ |
| Horn | `brass/horn` | Write reusable component code | ✅ | ❌ |

## Percussion Section (Test Writers & Supervisors)

| Agent | Path | Purpose | Can Write Code | Can Write Tests |
|-------|------|---------|----------------|-----------------|
| **Snare Tech** | `percussion/snare_tech` | Supervise unit test development | ❌ | ❌ |
| Snare | `percussion/snare` | Write unit tests | ❌ | ✅ |
| **Cymbal Tech** | `percussion/cymbal_tech` | Validate test quality and coverage | ❌ | ❌ |
| Bass | `percussion/bass` | Write test utilities and fixtures | ❌ | ✅ |
| **Tenor Tech** | `percussion/tenor_tech` | Supervise integration testing | ❌ | ❌ |
| Tenor | `percussion/tenor` | Write integration tests | ❌ | ✅ |

## Color Guard (Styling)

| Agent | Path | Purpose | Can Write Code | Can Write Tests |
|-------|------|---------|----------------|-----------------|
| **Flag Tech** | `guard/flag_tech` | Supervise styling and CSS work | ❌ | ❌ |
| Flag | `guard/flag` | Write CSS, Tailwind, styling code | ✅ | ❌ |

---

## Common Spawning Patterns

### Executive Director spawns:
```
spawn_agent("leadership/program_coordinator", {...})
```

### Program Coordinator spawns:
```
spawn_agent("leadership/designer", {...})           # For architecture
spawn_agent("caption_heads/backend_captain", {...}) # For backend tasks
spawn_agent("caption_heads/frontend_captain", {...})# For frontend tasks
spawn_agent("leadership/drum_major", {...})         # For TDD implementation
```

### Caption Heads spawn:
```
# Backend Captain spawns:
spawn_agent("brass/tuba_tech", {...})      # For API development
spawn_agent("brass/baritone_tech", {...})  # For backend logic

# Frontend Captain spawns:
spawn_agent("brass/trumpet_tech", {...})   # For UI components
spawn_agent("brass/horn_tech", {...})      # For component architecture
```

### Drum Major spawns (TDD workflow):
```
# RED phase - Write tests first
spawn_agent("percussion/snare_tech", {
  "task": "...",
  "test_file": "tests/test_feature.py",
  "code_file": "src/feature.py"
})

# GREEN phase - Write code to pass tests
spawn_agent("brass/tuba_tech", {          # Or trumpet_tech, baritone_tech
  "task": "...",
  "test_file": "tests/test_feature.py",
  "code_file": "src/feature.py",
  "requirements": "..."
})

# REFACTOR phase - Run Cymbal Tech to validate
spawn_agent("percussion/cymbal_tech", {
  "test_file": "tests/test_feature.py",
  "code_file": "src/feature.py"
})
```

### Tech Supervisors spawn Writers:
```
# Snare Tech spawns Snare
spawn_agent("percussion/snare", {
  "task": "...",
  "test_file": "tests/test_feature.py",
  "requirements": "..."
})

# Trumpet Tech spawns Trumpet
spawn_agent("brass/trumpet", {
  "task": "...",
  "test_file": "tests/test_component.test.jsx",
  "code_file": "src/components/Component.jsx",
  "requirements": "..."
})

# Tuba Tech spawns Tuba
spawn_agent("brass/tuba", {
  "task": "...",
  "test_file": "tests/test_api.py",
  "code_file": "src/api/endpoint.py",
  "requirements": "..."
})
```

---

## ❌ NEVER Use These (Wrong Paths)

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| `program_coordinator` | `leadership/program_coordinator` |
| `code_writer` | `brass/trumpet`, `brass/tuba`, etc. (be specific!) |
| `test_writer` | `percussion/snare`, `percussion/tenor`, etc. (be specific!) |
| `caption_heads/backend_captain` | **Agent doesn't exist yet** - needs to be created |
| `backend_captain` | `caption_heads/backend_captain` (when it exists) |

---

## Agent Status Summary

| Status | Count | Agents |
|--------|-------|--------|
| ✅ Exists + Permissions | 20 | All leadership, brass, percussion, guard |
| ⚠️ Needs Creation | 3 | backend_captain, frontend_captain, test_captain |

---

**Last Updated**: January 10, 2026
**Total Agents**: 20 (17 working + 3 missing)
