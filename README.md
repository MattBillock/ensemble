# Ensemble

**AI agent swarm for software development using Test-Driven Development**

Ensemble is a hierarchical multi-agent system that builds software through coordinated collaboration. Each agent has specific expertise and works together to deliver complete software solutions using Test-Driven Development methodology.

## Version 1.0-beta

This release includes:
- Complete agent hierarchy (25+ agents)
- Self-improvement loop with feedback injection
- Achievement system for gamification
- Real-time monitoring UI with Timeline view
- File overwrite guardrails for data protection

## Overview

Ensemble uses specialized AI agents organized into a clear hierarchy with distinct responsibilities. Agents coordinate through a structured workflow to deliver high-quality code following TDD principles.

**For detailed agent documentation, see [Agent Hierarchy Guide](docs/current/AGENT_HIERARCHY.md)**

### Agent Hierarchy

**Leadership** - Strategic vision and coordination
- **Executive Director** - System orchestrator and entry point
- **Development Manager** - Drives implementation from requirements through delivery
- **System Architect** - Defines system architecture and technical design
- **TDD Coordinator** - Orchestrates test-driven development workflow
- **Question Marshal** - Handles escalations and clarifications

**Coordinators** - Task breakdown and planning
- **Backend Coordinator** - Breaks backend work into API, model, and service tasks
- **Frontend Coordinator** - Breaks frontend into components, pages, and services
- **Test Coordinator** - Defines comprehensive test strategy (unit, integration, e2e)

**Developers** - Code implementation
- **Frontend Lead** / **Frontend Developer** - React and UI development
- **Backend Lead** / **Backend Developer** - Business logic and services
- **API Lead** / **API Developer** - REST API and endpoints
- **Database Manager** - Schema design and migrations

**Testers** - Test implementation
- **Unit Test Lead** / **Unit Test Writer** - Unit tests and test fixtures
- **Integration Test Lead** / **Integration Test Writer** - Integration tests
- **API Test Writer** - API endpoint testing

**Support** - Cross-cutting concerns
- **Code Reviewer** - Quality gate before commits
- **Visual Tech** - Code refactoring (TDD REFACTOR phase)
- **Drill Writer** - Documentation
- **Logistics Manager** - Codebase exploration

**Designers** - Styling and visual
- **Style Developer** - CSS, Tailwind, and styling code

## Current Capabilities

### Core Features
- Requirements analysis and architecture design
- Test-Driven Development workflow (RED-GREEN-REFACTOR)
- Hierarchical delegation with permission enforcement
- Real-time activity monitoring via Web UI
- Agent spawn tracking and timeline visualization

### Self-Improvement Loop (NEW)
- Automatic metrics collection on every agent execution
- Performance analysis and recommendation generation
- Feedback injection into agent prompts based on past performance
- Human-in-the-loop approval for recommendations
- Dashboard at `/improve` for managing recommendations

### Achievement System (NEW)
- 30+ achievements with ska music theme references
- Categories: Productivity, Comedy, Milestone, Streak, Meta, Ska
- Rarities from Common to Legendary
- Automatic tracking and award notifications
- Dashboard at `/achievements` for viewing progress

### Data Protection (NEW)
- Automatic backups before file overwrites
- Protected file patterns (requirements, architecture, readme, etc.)
- Timestamped backups in `~/.ensemble/backups/`
- Logging of all file overwrites

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

## Running the UI

```bash
# Start the backend (port 8001)
cd src/field/ensemble_ui/backend
python main.py

# In another terminal, start the frontend (port 5173)
cd src/field/ensemble_ui/frontend
npm install
npm run dev
```

Navigate to `http://localhost:5173` to access the UI.

### UI Views
- **Activity** - Real-time agent activity feed
- **Timeline** - Horizontal timeline showing task execution flow
- **Metrics** - Performance analytics and statistics
- **Improve** - Self-improvement recommendations
- **Achievements** - Gamification and progress tracking

## Usage

### Web UI Workflow

1. Open `http://localhost:5173`
2. Enter your problem description in the "New Task" form
3. Select budget tier (Economical/Balanced/Full Power)
4. Click "Start Task"
5. Watch agents spawn and execute in real-time

### Programmatic Usage

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

# Load the Executive Director
exec_dir = AgentDefinition.from_file("leadership/executive_director.md")

# Set up tools
tools = ToolRegistry.default()
spawn_tool = SpawnAgentTool(
    agent_types_dir=Path("."),
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    tools=tools
)
tools.register(spawn_tool)

# Execute
runtime = AgentRuntime(exec_dir, api_key=os.getenv("ANTHROPIC_API_KEY"), tools=tools)
result = runtime.execute({
    "user_vision": problem,
    "output_directory": "output/factorial"
})
```

## Project Structure

```
ensemble/
├── README.md                    # This file
├── CLAUDE.md                    # Project guide for Claude
├── requirements.txt             # Python dependencies
│
├── Agent Definitions (Markdown agent specs)
│   ├── leadership/              # Executive Director, Development Manager, etc.
│   ├── coordinators/            # Backend, Frontend, Test Coordinators
│   ├── developers/              # Frontend, Backend, API, Database agents
│   ├── testers/                 # Unit, Integration, API test agents
│   ├── support/                 # Code Reviewer, Visual Tech, Drill Writer
│   └── designers/               # Style Developer
│
├── Source Code
│   └── src/
│       ├── runtime/agents/      # Agent runtime, tools, metrics, achievements
│       │   ├── runtime.py       # Core agent execution
│       │   ├── tools.py         # Available tools (write_file, spawn_agent, etc.)
│       │   ├── metrics.py       # Performance metrics collection
│       │   ├── activity_tracker.py  # Real-time activity tracking
│       │   ├── self_improvement.py  # Self-improvement loop
│       │   └── achievements.py  # Achievement system
│       │
│       └── field/ensemble_ui/   # Web UI for monitoring
│           ├── backend/         # FastAPI server (port 8001)
│           └── frontend/        # React UI (port 5173)
│
├── Documentation
│   ├── docs/                    # Technical documentation
│   │   └── current/
│   │       └── AGENT_HIERARCHY.md  # Agent spawning and supervision guide
│   └── CLAUDE.md               # Project conventions
│
├── Data Directories
│   └── ~/.ensemble/             # User data (created at runtime)
│       ├── metrics.db           # Performance metrics database
│       ├── achievements.db      # Achievement tracking
│       ├── recommendations/     # Self-improvement recommendations
│       ├── backups/            # Automatic file backups
│       └── projects/           # Project state tracking
│
└── scripts/                     # Deployment and development scripts
```

## Development Philosophy

### Test-Driven Development
All code is built following the Red-Green-Refactor cycle:
1. **RED** - Test Writers create failing tests
2. **GREEN** - Developers write minimal code to pass tests
3. **REFACTOR** - Visual Tech improves code while maintaining tests

### Hierarchical Delegation
- **Supervisors coordinate, never write code** - Leads and Coordinators delegate
- **Permission system prevents rogue agents** - Enforced at tool level
- **Clear spawning patterns** - Each agent knows which agents to spawn
- **Fail-fast rules** - If spawn fails, return error (no fallback)

### Continuous Improvement
- Every execution records metrics (success rate, duration, tokens)
- Agents provide self-analysis and performance analysis
- System generates recommendations based on patterns
- Feedback is injected into future agent prompts

## Key Features

### Rogue Agent Prevention
- Supervisors have `can_write_code: false`
- Writers have explicit write permissions
- WriteFileTool enforces permissions
- Automatic backup on protected file overwrites

### Budget Tiers
- **Economical** - Uses Claude Haiku for most tasks
- **Balanced** - Uses Claude Sonnet for complex tasks
- **Full Firepower** - Uses Claude Opus for strategic decisions

### Real-Time Monitoring
- WebSocket-based activity streaming
- Agent hierarchy visualization
- File generation tracking
- Timeline view with AI-generated task titles

## API Endpoints

### Core Endpoints
- `POST /api/generate-solution` - Start a new task
- `GET /api/status` - Get system status
- `GET /api/agents` - List available agents
- `WS /ws/agent-status` - WebSocket for real-time updates

### Metrics Endpoints
- `GET /api/metrics/summary` - Overall statistics
- `GET /api/metrics/agents` - Per-agent performance
- `GET /api/metrics/trends` - Performance over time

### Self-Improvement Endpoints
- `GET /api/self-improvement/status` - Loop status
- `GET /api/self-improvement/analyze` - Run analysis
- `GET /api/self-improvement/recommendations` - Pending recommendations

### Achievement Endpoints
- `GET /api/achievements` - All achievements
- `GET /api/achievements/recent` - Recent unlocks
- `GET /api/achievements/stats` - Achievement statistics

## Roadmap

### Completed
- [x] Core agent hierarchy
- [x] TDD workflow
- [x] Permission system
- [x] Real-time UI monitoring
- [x] Timeline view
- [x] Self-improvement loop
- [x] Achievement system
- [x] File overwrite guardrails

### Future Enhancements
- [ ] Security testing agents
- [ ] Performance testing agents
- [ ] E2E testing agents
- [ ] DevOps/deployment agents
- [ ] Multi-project support
- [ ] Team collaboration features

## Contributing

This project is in active development. Contributions welcome!

## License

[To be determined]

## Acknowledgments

Built with Claude (Anthropic API) and inspired by the principles of clear communication, hierarchical organization, and systematic development.

---

*"Pick it up! Pick it up! Pick it up!"* 🎺
