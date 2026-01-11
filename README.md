# Ensemble

**AI agent swarm for software development using Test-Driven Development**

Ensemble is a hierarchical multi-agent system that builds software through coordinated collaboration. Each agent has specific expertise and works together to deliver complete software solutions using Test-Driven Development methodology.

## Overview

Ensemble uses specialized AI agents organized into a clear hierarchy with distinct responsibilities. Agents coordinate through a structured workflow to deliver high-quality code following TDD principles.

### Agent Hierarchy

**Leadership** - Strategic vision and coordination
- **Executive Director** - System orchestrator and entry point
- **Development Manager** - Drives implementation from requirements through delivery
- **System Architect** - Defines system architecture and technical design
- **TDD Coordinator** - Orchestrates test-driven development workflow

**Coordinators** - Task breakdown and planning
- **Backend Coordinator** - Breaks backend work into API, model, and service tasks
- **Frontend Coordinator** - Breaks frontend into components, pages, and services
- **Test Coordinator** - Defines comprehensive test strategy (unit, integration, e2e)

**Developers** - Code implementation
- **Frontend Lead** / **Frontend Developer** - React and UI development
- **Backend Lead** / **Backend Developer** - Business logic and services
- **API Lead** / **API Developer** - REST API and endpoints
- **Component Lead** / **Component Developer** - Reusable component architecture

**Testers** - Test implementation
- **Unit Test Lead** / **Unit Test Writer** - Unit tests and test fixtures
- **Integration Test Lead** / **Integration Test Writer** - Integration and E2E tests
- **Test Validator** - Validates test quality and coverage

**Designers** - Styling and visual
- **Style Lead** / **Style Developer** - CSS, Tailwind, and styling code

## Current Capabilities

Ensemble currently supports:
- ✅ Requirements analysis (Development Manager)
- ✅ Architecture design (System Architect)
- ✅ Test-Driven Development workflow (TDD Coordinator)
- ✅ Task breakdown and coordination (Coordinators)
- ✅ Code writing with supervision (Leads spawn Developers)
- ✅ Test writing with supervision (Test Leads spawn Writers)
- ✅ Rogue agent prevention (permission system enforces delegation)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd ensemble

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

### Development Workflow

The typical development workflow follows a structured hierarchy:

1. **Executive Director** - Receives user vision, spawns Development Manager
2. **Development Manager** - Breaks into milestones, spawns System Architect and Coordinators
3. **System Architect** - Designs architecture
4. **Coordinators** - Break work into detailed tasks
5. **TDD Coordinator** - Implements using RED-GREEN-REFACTOR cycle

### Example: Building with TDD

```python
from pathlib import Path
from dotenv import load_dotenv
import os

from src.runtime.agents import AgentDefinition, AgentRuntime
from src.runtime.agents.tools import ToolRegistry, SpawnAgentTool

load_dotenv()

# Define the problem
problem = """
Build a function that calculates the factorial of a number.
Handle edge cases like 0, 1, and negative numbers.
"""

# Load the TDD Coordinator
tdd_coordinator = AgentDefinition.from_file("leadership/tdd_coordinator.md")

# Set up tools
tools = ToolRegistry.default()
spawn_tool = SpawnAgentTool(
    agent_types_dir=Path("."),
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    tools=tools
)
tools.register(spawn_tool)

# Execute
runtime = AgentRuntime(tdd_coordinator, api_key=os.getenv("ANTHROPIC_API_KEY"), tools=tools)
result = runtime.execute({
    "problem_description": problem,
    "output_directory": "rehearsals/factorial"
})
```

## Project Structure

```
ensemble/
├── README.md, QUICKSTART.md, requirements.md  # Core documentation
│
├── Agent Definitions (Markdown agent specs)
│   ├── leadership/          # Strategic agents (Executive Director, Development Manager, etc.)
│   ├── coordinators/        # Task breakdown agents (Backend, Frontend, Test Coordinators)
│   ├── developers/          # Code writers and leads (Frontend, Backend, etc.)
│   ├── testers/             # Test writers and leads (Unit, Integration)
│   └── designers/           # Styling agents (Style Developer)
│
├── Source Code
│   └── src/
│       ├── runtime/agents/      # Agent runtime, tools, activity tracking, metrics
│       └── field/ensemble_ui/   # Web UI for monitoring agent execution
│           ├── backend/         # FastAPI server (port 8001)
│           └── frontend/        # React UI (port 5173)
│
├── Documentation
│   ├── docs/current/        # Active documentation (diagnostic reports, reviews)
│   └── docs/archive/        # Historical documentation and milestone records
│
├── Scripts
│   ├── scripts/deployment/  # start_backend.sh, start_frontend.sh, run_ensemble_ui.sh
│   ├── scripts/development/ # Test scripts and development utilities
│   └── scripts/deprecated/  # Old scripts kept for reference
│
└── logs/                # Execution logs
```

## Development Philosophy

### Test-Driven Development
All code is built following the Red-Green-Refactor cycle:
1. **RED** - Unit Test Writer creates failing tests
2. **GREEN** - Developers write minimal code to pass tests
3. **REFACTOR** - Code improvements while maintaining test coverage

### Hierarchical Delegation
- **Supervisors coordinate, never write code** - Leads and Coordinators delegate to writers
- **Permission system prevents rogue agents** - Enforced at tool level (can_write_code, can_write_tests)
- **Clear spawning patterns** - Each agent knows exactly which agents to spawn
- **Fail-fast rules** - If spawn fails, agents stop and return error (no fallback to writing code)

### Eating Our Own Dogfood
Ensemble is building itself. The UI and tooling are developed using the agent system.

## Key Features

### Rogue Agent Prevention
- Supervisors (Leads, Coordinators, Leadership) have `can_write_code: false`
- Writers (Developers, Test Writers) have explicit write permissions
- WriteFileTool enforces permissions and detects violations
- Test suite validates prevention system (5/5 tests passing)

### Agent Registry
See `docs/current/AGENT_REGISTRY.md` for complete agent paths and spawning patterns.

### State Persistence
Agent execution state is checkpointed for crash recovery and resume capability.

## Roadmap

### ✅ Phase 1: Core Infrastructure (Complete)
- [x] Requirements analysis
- [x] Architecture design
- [x] TDD workflow
- [x] Permission system
- [x] Agent naming refactor (drum corps → standard names)
- [x] Coordinators for task breakdown
- [x] Rogue agent prevention

### Phase 2: Enhanced Capabilities
- [ ] Error recovery and retry logic
- [ ] Enhanced TDD workflow validation
- [ ] File exploration agents
- [ ] Integration testing workflows
- [ ] Performance monitoring

### Phase 3: Self-Improvement
- [ ] Agent performance analytics
- [ ] Token usage optimization
- [ ] Automated agent refinement
- [ ] Continuous improvement feedback loops

## Contributing

This project is currently in active development. Contributions welcome!

## License

[To be determined]

## Acknowledgments

Built with Claude (Anthropic API) and inspired by the principles of clear communication, hierarchical organization, and systematic development.

---

*"Test first, code second, refactor always."*
