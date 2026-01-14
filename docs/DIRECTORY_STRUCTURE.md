# Ensemble Project Directory Structure

**CRITICAL**: All agents MUST write files to the correct directories based on file type and purpose. This document defines the canonical directory structure for the entire ensemble project.

## Directory Structure Overview

```
ensemble/
├── src/                        # ALL SOURCE CODE (production)
│   ├── runtime/                # Agent runtime system
│   │   ├── agents/            # Agent execution and management
│   │   │   ├── naming/        # Agent naming utilities
│   │   │   ├── coordination/  # Agent coordination logic
│   │   │   └── tools/         # Agent tools and capabilities
│   │   └── execution/         # Execution engine
│   │
│   └── field/                  # Field-specific implementations
│       └── ensemble_ui/        # Ensemble web UI application
│           ├── frontend/       # React frontend application
│           │   ├── src/       # Frontend source code (WRITE CODE HERE)
│           │   │   ├── components/  # React components
│           │   │   ├── pages/       # Page components
│           │   │   ├── hooks/       # Custom React hooks
│           │   │   ├── utils/       # Utility functions
│           │   │   ├── styles/      # CSS/styling
│           │   │   └── App.jsx      # Main app component
│           │   ├── public/    # Static assets
│           │   └── tests/     # Frontend test files
│           │
│           ├── backend/        # Python FastAPI backend
│           │   ├── api/       # API endpoints (WRITE API CODE HERE)
│           │   ├── models/    # Data models
│           │   ├── services/  # Business logic services
│           │   ├── utils/     # Backend utilities
│           │   └── main.py    # FastAPI application entry
│           │
│           └── output/         # Agent-generated artifacts (NOT CODE)
│               ├── requirements.md       # Project requirements
│               ├── architecture.md      # Architecture documents
│               ├── milestones.md        # Milestone plans
│               ├── backend_tasks*.md    # Task breakdowns
│               ├── frontend_tasks*.md   # Task breakdowns
│               ├── test_tasks*.md       # Test task breakdowns
│               └── [feature-name]/      # Feature-specific docs
│
├── tests/                      # ALL TEST FILES
│   ├── runtime/                # Tests for runtime system
│   │   └── agents/            # Agent system tests
│   │       └── naming/        # Agent naming tests
│   ├── agents/                 # Tests for individual agents
│   ├── field/                  # Tests for field implementations
│   │   └── ensemble_ui/       # UI tests
│   │       ├── frontend/      # Frontend integration tests
│   │       └── backend/       # Backend API tests
│   └── tools/                  # Tool/utility tests
│
├── docs/                       # DOCUMENTATION (system-level)
│   ├── common_instructions.md  # Shared agent instructions
│   ├── DIRECTORY_STRUCTURE.md  # THIS FILE
│   ├── archive/               # Archived documentation
│   └── current/               # Current system documentation
│
├── leadership/                 # Leadership agent definitions
├── coordinators/               # Coordinator agent definitions
├── developers/                 # Developer agent definitions
├── testers/                    # Tester agent definitions
├── support/                    # Support agent definitions
│
└── scripts/                    # Utility scripts
    └── monitoring/             # Monitoring scripts
```

---

## File Type → Directory Mapping

### 1. FRONTEND CODE (React, JavaScript, JSX, TypeScript)

**File Extensions**: `.js`, `.jsx`, `.ts`, `.tsx`, `.css`, `.scss`

**Write To**:
- **Components**: `/src/field/ensemble_ui/frontend/src/components/`
- **Pages**: `/src/field/ensemble_ui/frontend/src/pages/`
- **Hooks**: `/src/field/ensemble_ui/frontend/src/hooks/`
- **Utils**: `/src/field/ensemble_ui/frontend/src/utils/`
- **Styles**: `/src/field/ensemble_ui/frontend/src/styles/`
- **Main App**: `/src/field/ensemble_ui/frontend/src/App.jsx`

**Frontend Tests**:
- **Unit Tests**: `/src/field/ensemble_ui/frontend/src/[component-name].test.jsx`
- **Integration Tests**: `/tests/field/ensemble_ui/frontend/`

**Example Paths**:
```
✓ CORRECT: /src/field/ensemble_ui/frontend/src/components/AgentCard.jsx
✓ CORRECT: /src/field/ensemble_ui/frontend/src/components/AgentCard.test.jsx
✓ CORRECT: /src/field/ensemble_ui/frontend/src/hooks/useAgentData.js
✗ WRONG: /src/field/ensemble_ui/output/AgentCard.jsx  ← DO NOT DO THIS
```

---

### 2. BACKEND CODE (Python, FastAPI)

**File Extensions**: `.py`

**Write To**:
- **API Endpoints**: `/src/field/ensemble_ui/backend/api/`
- **Models**: `/src/field/ensemble_ui/backend/models/`
- **Services**: `/src/field/ensemble_ui/backend/services/`
- **Utils**: `/src/field/ensemble_ui/backend/utils/`
- **Main App**: `/src/field/ensemble_ui/backend/main.py`

**Backend Tests**:
- **Unit Tests**: `/tests/field/ensemble_ui/backend/test_[module].py`
- **API Tests**: `/tests/field/ensemble_ui/backend/api/test_[endpoint].py`

**Example Paths**:
```
✓ CORRECT: /src/field/ensemble_ui/backend/api/agents.py
✓ CORRECT: /src/field/ensemble_ui/backend/services/agent_service.py
✓ CORRECT: /tests/field/ensemble_ui/backend/api/test_agents.py
✗ WRONG: /src/field/ensemble_ui/output/agent_service.py  ← DO NOT DO THIS
```

---

### 3. RUNTIME/AGENT SYSTEM CODE

**File Extensions**: `.py`

**Write To**:
- **Agent Logic**: `/src/runtime/agents/`
- **Coordination**: `/src/runtime/agents/coordination/`
- **Tools**: `/src/runtime/agents/tools/`
- **Naming**: `/src/runtime/agents/naming/`
- **Execution**: `/src/runtime/execution/`

**Runtime Tests**:
- **Agent Tests**: `/tests/runtime/agents/`
- **Tool Tests**: `/tests/tools/`

**Example Paths**:
```
✓ CORRECT: /src/runtime/agents/naming/name_data.py
✓ CORRECT: /src/runtime/agents/tools/spawn_agent.py
✓ CORRECT: /tests/runtime/agents/naming/test_name_data.py
✗ WRONG: /src/field/ensemble_ui/output/agent-naming-system/name_data.py
```

---

### 4. DOCUMENTATION & PLANNING (Markdown)

**File Extensions**: `.md`

**Write To**:

#### **A. Agent-Generated Project Artifacts** → `/src/field/ensemble_ui/output/`
These are outputs from the ensemble working on user projects:
- `requirements.md` - Project requirements
- `architecture.md` - Architecture design
- `milestones.md` - Milestone plans
- `backend_tasks.md` - Backend task breakdowns
- `frontend_tasks.md` - Frontend task breakdowns
- `test_tasks.md` - Test task breakdowns
- `[feature-name]/` - Feature-specific documentation subdirectories

#### **B. System-Level Documentation** → `/docs/`
Documentation about the ensemble system itself:
- `/docs/common_instructions.md` - Shared agent instructions
- `/docs/DIRECTORY_STRUCTURE.md` - This file
- `/docs/current/` - Current system documentation
- `/docs/archive/` - Archived system docs

#### **C. Agent Definitions** → Root-level agent directories
- `/leadership/*.md` - Leadership agent definitions
- `/coordinators/*.md` - Coordinator agent definitions
- `/developers/*.md` - Developer agent definitions
- `/testers/*.md` - Tester agent definitions

**Example Paths**:
```
✓ CORRECT: /src/field/ensemble_ui/output/requirements.md
✓ CORRECT: /src/field/ensemble_ui/output/ui-enhancements/architecture.md
✓ CORRECT: /docs/common_instructions.md
✓ CORRECT: /developers/frontend_developer.md
✗ WRONG: /src/field/ensemble_ui/frontend/src/requirements.md  ← NOT IN SRC
```

---

### 5. TEST FILES

**File Extensions**: `.test.js`, `.test.jsx`, `.spec.js`, `test_*.py`, `*_test.py`

**Write To**:

#### **A. Co-located Frontend Tests** (preferred for components)
- `/src/field/ensemble_ui/frontend/src/components/[Component].test.jsx`
- `/src/field/ensemble_ui/frontend/src/hooks/[hook].test.js`

#### **B. Separate Test Directories** (for integration/e2e tests)
- `/tests/field/ensemble_ui/frontend/` - Frontend integration tests
- `/tests/field/ensemble_ui/backend/` - Backend API tests
- `/tests/runtime/agents/` - Agent system tests
- `/tests/agents/` - Individual agent behavior tests

**Example Paths**:
```
✓ CORRECT: /src/field/ensemble_ui/frontend/src/components/AgentCard.test.jsx
✓ CORRECT: /tests/field/ensemble_ui/backend/api/test_agents.py
✓ CORRECT: /tests/agents/test_unit_test_writer.py
✗ WRONG: /src/field/ensemble_ui/output/tests/test_something.py  ← NOT IN OUTPUT
```

---

### 6. CONFIGURATION FILES

**File Extensions**: `.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.env`

**Write To**:
- **Project Root**: `/package.json`, `/pyproject.toml`, `/.env`
- **Frontend Config**: `/src/field/ensemble_ui/frontend/` for frontend-specific configs
- **Backend Config**: `/src/field/ensemble_ui/backend/` for backend-specific configs

**Example Paths**:
```
✓ CORRECT: /package.json
✓ CORRECT: /src/field/ensemble_ui/frontend/vite.config.js
✓ CORRECT: /src/field/ensemble_ui/backend/.env.example
```

---

## Rules for Agents

### Executive Director

**Writes**:
- ✓ `/src/field/ensemble_ui/output/requirements.md`
- ✓ `/src/field/ensemble_ui/output/milestones.md`
- ✓ Status reports in output/

**Does NOT Write**:
- ✗ Code files (`.js`, `.jsx`, `.py`, `.tsx`)
- ✗ Test files
- ✗ Anything in `/src/field/ensemble_ui/frontend/src/`
- ✗ Anything in `/src/field/ensemble_ui/backend/`

### Development Manager

**Writes**:
- ✓ `/src/field/ensemble_ui/output/architecture.md`
- ✓ `/src/field/ensemble_ui/output/milestone_plan.md`
- ✓ Task breakdown files in output/

**Does NOT Write**:
- ✗ Code files
- ✗ Test files

**Specifies for Spawned Agents**:
When spawning coordinators or developers, MUST provide exact paths:
```json
{
  "code_file": "/src/field/ensemble_ui/frontend/src/components/AgentCard.jsx",
  "test_file": "/src/field/ensemble_ui/frontend/src/components/AgentCard.test.jsx"
}
```

### Frontend Lead & Frontend Developer

**Writes Code To**:
- ✓ `/src/field/ensemble_ui/frontend/src/components/`
- ✓ `/src/field/ensemble_ui/frontend/src/pages/`
- ✓ `/src/field/ensemble_ui/frontend/src/hooks/`
- ✓ `/src/field/ensemble_ui/frontend/src/utils/`

**Writes Tests To**:
- ✓ `/src/field/ensemble_ui/frontend/src/[component].test.jsx` (co-located)
- ✓ `/tests/field/ensemble_ui/frontend/` (integration tests)

**Does NOT Write**:
- ✗ Anything in `/src/field/ensemble_ui/output/`

### Backend Lead & Backend Developer

**Writes Code To**:
- ✓ `/src/field/ensemble_ui/backend/api/`
- ✓ `/src/field/ensemble_ui/backend/services/`
- ✓ `/src/field/ensemble_ui/backend/models/`
- ✓ `/src/field/ensemble_ui/backend/utils/`

**Writes Tests To**:
- ✓ `/tests/field/ensemble_ui/backend/`
- ✓ `/tests/field/ensemble_ui/backend/api/`

**Does NOT Write**:
- ✗ Anything in `/src/field/ensemble_ui/output/`

### API Lead & API Developer

**Writes Code To**:
- ✓ `/src/field/ensemble_ui/backend/api/`
- ✓ `/src/field/ensemble_ui/backend/services/` (business logic)

**Writes Tests To**:
- ✓ `/tests/field/ensemble_ui/backend/api/`

**Does NOT Write**:
- ✗ Anything in `/src/field/ensemble_ui/output/`

### Unit Test Lead & Unit Test Writer

**Writes Tests To**:
- ✓ Co-located with code: `/src/field/ensemble_ui/frontend/src/[component].test.jsx`
- ✓ Test directories: `/tests/field/ensemble_ui/backend/test_[module].py`
- ✓ Agent tests: `/tests/agents/test_[agent].py`

**Does NOT Write**:
- ✗ Tests in `/src/field/ensemble_ui/output/tests/`

---

## Quick Reference Table

| File Type | Extension | Write To | Example |
|-----------|-----------|----------|---------|
| React Component | `.jsx`, `.tsx` | `frontend/src/components/` | `frontend/src/components/AgentCard.jsx` |
| React Hook | `.js`, `.ts` | `frontend/src/hooks/` | `frontend/src/hooks/useAgentData.js` |
| Frontend Util | `.js`, `.ts` | `frontend/src/utils/` | `frontend/src/utils/formatDate.js` |
| Frontend Test | `.test.jsx` | `frontend/src/[component].test.jsx` | `frontend/src/components/AgentCard.test.jsx` |
| Backend API | `.py` | `backend/api/` | `backend/api/agents.py` |
| Backend Service | `.py` | `backend/services/` | `backend/services/agent_service.py` |
| Backend Test | `.py` | `tests/field/ensemble_ui/backend/` | `tests/field/ensemble_ui/backend/test_agents.py` |
| Requirements | `.md` | `output/requirements.md` | `output/requirements.md` |
| Architecture | `.md` | `output/architecture.md` | `output/architecture.md` |
| Task Breakdown | `.md` | `output/[type]_tasks.md` | `output/backend_tasks_m1.md` |
| System Docs | `.md` | `docs/` | `docs/common_instructions.md` |
| Agent Tests | `.py` | `tests/agents/` | `tests/agents/test_unit_test_writer.py` |
| Runtime Code | `.py` | `src/runtime/agents/` | `src/runtime/agents/naming/name_data.py` |

---

## Validation Checklist

Before writing ANY file, check:

- [ ] Is this a code file? → Write to `src/field/ensemble_ui/[frontend|backend]/`
- [ ] Is this a test file? → Write to `tests/` or co-located with code
- [ ] Is this project documentation? → Write to `src/field/ensemble_ui/output/`
- [ ] Is this system documentation? → Write to `docs/`
- [ ] Is this runtime/agent code? → Write to `src/runtime/agents/`
- [ ] Am I using absolute paths from project root? (e.g., `/src/...`)
- [ ] Have I checked that my Output Format specifies the correct directory?

---

## What Goes in `/src/field/ensemble_ui/output/`?

**ONLY these types of files**:

1. **Requirements documents** - User project requirements
2. **Architecture documents** - System architecture designs
3. **Milestone plans** - Project milestone breakdowns
4. **Task breakdowns** - Developer/tester task lists
5. **Reports** - Analysis, status, completion reports
6. **Feature documentation** - Feature-specific planning docs

**NEVER**:
- ❌ Source code (`.js`, `.jsx`, `.py`, `.tsx`)
- ❌ Test code (`.test.js`, `test_*.py`)
- ❌ Configuration files (`.json`, `.yaml`)
- ❌ Compiled files (`.pyc`, `__pycache__`)

---

## Common Mistakes to Avoid

### ❌ WRONG

```python
# Executive Director writing code to output/
write_file("/src/field/ensemble_ui/output/AgentCard.jsx", ...)  # NO!
```

```python
# Frontend Developer writing code to output/
write_file("/src/field/ensemble_ui/output/components/UserList.jsx", ...)  # NO!
```

```python
# Backend Developer writing code to output/
write_file("/src/field/ensemble_ui/output/api/agents.py", ...)  # NO!
```

### ✓ CORRECT

```python
# Frontend Developer writing code to proper directory
write_file("/src/field/ensemble_ui/frontend/src/components/AgentCard.jsx", ...)  # YES!
```

```python
# Backend Developer writing code to proper directory
write_file("/src/field/ensemble_ui/backend/api/agents.py", ...)  # YES!
```

```python
# Executive Director writing documentation to output/
write_file("/src/field/ensemble_ui/output/requirements.md", ...)  # YES!
```

---

## Path Construction Guidelines

### Always use ABSOLUTE paths from project root:

```python
# ✓ CORRECT - Absolute path
code_file = "/src/field/ensemble_ui/frontend/src/components/AgentCard.jsx"

# ✗ WRONG - Relative path
code_file = "src/components/AgentCard.jsx"

# ✗ WRONG - Missing project structure
code_file = "AgentCard.jsx"
```

### When spawning agents, construct paths explicitly:

```python
# ✓ CORRECT
spawn_agent("developers/frontend_developer", {
    "task_description": "Create AgentCard component...",
    "code_file": "/src/field/ensemble_ui/frontend/src/components/AgentCard.jsx",
    "test_file": "/src/field/ensemble_ui/frontend/src/components/AgentCard.test.jsx"
})

# ✗ WRONG
spawn_agent("developers/frontend_developer", {
    "task_description": "Create AgentCard component...",
    "code_file": "/src/field/ensemble_ui/output/AgentCard.jsx",  # NO!
    "test_file": "/src/field/ensemble_ui/output/tests/AgentCard.test.jsx"  # NO!
})
```

---

## Summary

**Golden Rules**:

1. **Code goes in `src/`, not `output/`**
2. **Tests go in `tests/` or co-located with code**
3. **Documentation goes in `output/` (project) or `docs/` (system)**
4. **Always use absolute paths from project root**
5. **Check your agent's Output Format section for path examples**
6. **When in doubt, reference this document**

**This document is the single source of truth for file organization in the ensemble project.**
