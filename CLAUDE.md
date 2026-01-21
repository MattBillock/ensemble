# CLAUDE.md - Ensemble Project Guide

## Project Overview

**Ensemble** is a hierarchical multi-agent system for software development using Test-Driven Development (TDD). AI agents are organized into a clear hierarchy with distinct responsibilities, coordinating through structured workflows to deliver high-quality code.

The project follows a "eating our own dogfood" philosophy - the UI and tooling are built using the agent system itself.

## Quick Start

```bash
# Backend (Terminal 1)
cd ~/Development/ai_exploration/ensemble
source venv/bin/activate
cd src/field/ensemble_ui/backend
python main.py  # Port 8001

# Frontend (Terminal 2)
cd ~/Development/ai_exploration/ensemble/src/field/ensemble_ui/frontend
npm run dev  # Port 5173
```

**Service URLs:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8001
- API Docs: http://localhost:8001/docs
- WebSocket: ws://localhost:8001/ws/agent-status

## Project Architecture

```
ensemble/
├── agents/              # ALL agent definitions (consolidated location)
│   ├── leadership/      # Strategic agents (Executive Director, Development Manager, etc.)
│   ├── coordinators/    # Task breakdown agents (Backend, Frontend, Test Coordinators)
│   ├── developers/      # Code writers (Frontend, Backend, API Developers)
│   ├── testers/         # Test writers (Unit Test, Integration Test Writers)
│   ├── designers/       # Styling agents (Style Developer)
│   └── support/         # Support agents (Code Reviewer, CI Agent, etc.)
├── src/
│   ├── runtime/agents/  # Agent runtime, tools, activity tracking, metrics
│   └── field/ensemble_ui/
│       ├── backend/     # FastAPI server
│       └── frontend/    # React UI (Vite + React 19 + Redux + Tailwind)
├── docs/
│   ├── current/         # Active documentation
│   └── archive/         # Historical records
├── scripts/
│   ├── deployment/      # Startup scripts
│   ├── development/     # Dev utilities
│   └── monitoring/      # Enforcement scripts
└── tests/               # Comprehensive test suite
```

## Technology Stack

### Frontend
- **React 19** with functional components and hooks
- **Redux Toolkit** for state management
- **Vite 7** for builds and dev server
- **Tailwind CSS 4** + **SASS** for styling
- **React-Bootstrap 2** for UI components
- **Vitest** + **React Testing Library** for tests

### Backend
- **FastAPI** with async endpoints
- **Uvicorn** web server
- **Pydantic** for data validation
- **WebSocket** for real-time updates

### Python Core
- **anthropic** SDK for Claude API
- **Python 3.10+**
- **pytest** for testing
- **black** (line-length 100) and **ruff** for formatting

## Agent System Architecture

### Hierarchy
1. **Leadership** - Strategic coordination (Executive Director, Development Manager, System Architect, TDD Coordinator)
2. **Coordinators** - Task breakdown (Backend, Frontend, Test Coordinators)
3. **Developers** - Code implementation (Frontend/Backend/API Leads and Developers)
4. **Testers** - Test implementation (Unit Test/Integration Test Writers)
5. **Designers** - Styling (Style Developer)

### Key Principles
- **Supervisors coordinate, never write code** - Leads delegate to Writers
- **Permission system prevents rogue agents** - `can_write_code` flags enforced at tool level
- **Fail-fast rules** - If spawn fails, agents stop (no fallback to writing code)
- **TDD workflow** - RED (failing tests) → GREEN (minimal passing code) → REFACTOR

### Spawning Pattern
```
Executive Director
  └── Development Manager
        ├── System Architect
        └── Coordinators
              └── Leads
                    └── Developers/Writers
```

## Code Conventions

### Python
- Line length: 100 characters
- Format with `black` and `ruff`
- Type hints for function signatures
- Structured JSON logging with request_id and agent_id tracking
- Use `pydantic` for API data validation

### React/JavaScript
- Functional components with hooks
- File naming: `PascalCase.jsx` for components
- Use Redux Toolkit patterns (`createSlice`, `configureStore`)
- Prefer destructuring for props
- Dark theme colors: `#1a1d29` background, `#242836` cards, `#3a3f52` borders

### Testing
- Python: pytest with 80%+ coverage target
- Frontend: Vitest + React Testing Library with jsdom environment
- Test files: `test_*.py` (Python), `*.test.jsx` (React)

## Important Patterns

### Activity Tracking
All agent activity flows through `ActivityTracker`:
- Agent spawning, completion, failure
- Tool usage and iterations
- Questions/answers
- File generation

### WebSocket Updates
Real-time UI updates via `/ws/agent-status` endpoint with auto-reconnect.

### Budget Tiers
- `economical` - Haiku (fast, cheap)
- `balanced` - Sonnet (default)
- `full_firepower` - Opus (complex tasks)

### Rate Limiting
Multi-dimensional rate limiter respects Anthropic API limits:
- 2,000 requests/minute
- 800,000 input tokens/minute
- 4,000,000 output tokens/minute

Implemented in `src/runtime/agents/resilience.py` as `MultiDimensionalRateLimiter`.
Automatically integrated into all agent API calls.

### Bug Fix Director
Autonomous bug fixing system via `POST /api/fix-bug`:
- Analyzes bug reports automatically
- Spawns appropriate sub-agents
- Generates summary reports in `output/completed/`
- Minimal user interaction required

Agent definition: `agents/leadership/bug_fix_director.md`

### UI Features
- **Pending Review Dashboard** - Review agent-generated documents before implementation
- **Agent Stats** - View agent activity, achievements, and performance
- **Achievement System** - Gamified agent tracking with rarity tiers
- **Cost Tracking** - Monitor API usage and costs

## Common Tasks

### Run Tests
```bash
# Backend
pytest tests/

# Frontend
cd src/field/ensemble_ui/frontend
npm run test
npm run test:coverage
```

### Lint/Format
```bash
# Python
black --line-length 100 .
ruff check .

# Frontend
cd src/field/ensemble_ui/frontend
npm run lint
```

## What NOT To Do

1. **Don't bypass the hierarchy** - Agents must spawn appropriate subordinates
2. **Don't skip tests** - TDD is the core philosophy
3. **Don't ignore permission flags** - `can_write_code: false` means NO writing
4. **Don't hardcode paths** - Use relative paths from project root
5. **Don't forget request_id tracking** - All operations should be traceable
6. **Don't use deprecated drum corps naming** - Use standard role names

## File References

- Agent Registry: `docs/current/AGENT_REGISTRY.md`
- Architecture: `src/field/ensemble_ui/architecture.md`
- Quick Start: `QUICKSTART.md`
- UI Implementation: `src/field/ensemble_ui/IMPLEMENTATION_SUMMARY.md`
- Agent Template: `agents/leadership/AGENT_TEMPLATE.md`
- Bug Fix Director: `agents/leadership/bug_fix_director.md`
- Artifact Status: `src/field/ensemble_ui/output/ARTIFACT_STATUS.md`
- Rate Limiter: `src/runtime/agents/resilience.py` (MultiDimensionalRateLimiter class)
