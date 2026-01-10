# Ensemble

**AI agent swarm for software development using Test-Driven Development**

Ensemble is a hierarchical multi-agent system that builds software through coordinated collaboration, inspired by the structure and organization of a drum and bugle corps.

## Overview

Ensemble uses specialized AI agents organized into a performance hierarchy. Each agent has specific expertise and works together to deliver complete software solutions using Test-Driven Development methodology.

### The Corps Structure

**Leadership** - Strategic vision and coordination
- **Executive Director** - System orchestrator (future)
- **Program Coordinator** - Requirements analysis
- **Designer** - Architecture design
- **Drum Major** - Task orchestration and TDD workflow

**Brass** - Frontend development
- **Trumpet** - Frontend code writer (future)
- **Horn** - Component writer (future)
- **Baritone** - Framework agent (future)
- **Tuba** - API writer (future)

**Percussion** - Backend development and testing
- **Snare** - Test writer (RED phase)
- **Tenor** - Integration test writer (future)
- **Bass** - Backend code writer (GREEN phase)
- **Cymbal** - Performance monitoring (future)

**Pit** - Infrastructure and deployment
- **Marimba** - Deployment agent (future)
- **Vibes** - CI/CD agent (future)
- **Synth** - Database agent (future)

**Guard** - Visual and styling
- **Flag** - Stylesheet writer (future)
- **Rifle** - Component styling (future)
- **Saber** - Animation agent (future)
- **Dance** - Interaction/UX agent (future)

**Support** - Assistance and optimization
- **Scout** - File explorer (future)
- **Visual Tech** - Refactor agent

## Current Capabilities

Ensemble currently supports:
- ✅ Requirements analysis (Program Coordinator)
- ✅ Architecture design (Designer)
- ✅ Test-Driven Development workflow (Drum Major)
- ✅ Test writing - RED phase (Snare)
- ✅ Backend code writing - GREEN phase (Bass)
- ✅ Code refactoring - REFACTOR phase (Visual Tech)

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

The typical development workflow follows the "season" metaphor:

1. **Charting** - Define requirements and architecture
2. **Rehearsal** - Development with TDD
3. **Performance** - Deployment

### Example: Solving a Problem with TDD

```python
from pathlib import Path
from dotenv import load_dotenv
import os

from src.runtime import AgentDefinition, AgentRuntime
from src.runtime.tools import ToolRegistry, SpawnAgentTool, ReadFileTool, RunCommandTool

load_dotenv()

# Define the problem
problem = """
Build a function that calculates the factorial of a number.
Handle edge cases like 0, 1, and negative numbers.
"""

# Load the Drum Major (TDD orchestrator)
drum_major = AgentDefinition.from_file("leadership/drum_major.md")

# Set up tools
tools = ToolRegistry.default()
# ... configure tools

# Execute
runtime = AgentRuntime(drum_major, api_key=os.getenv("ANTHROPIC_API_KEY"), tools=tools)
result = runtime.execute({
    "problem_description": problem,
    "output_directory": "rehearsals/factorial"
})
```

## Project Structure

```
ensemble/
├── leadership/          # Strategic agents
├── caption_heads/       # Domain orchestrators (future)
├── brass/               # Frontend agents (future)
├── percussion/          # Backend and testing agents
├── pit/                 # Infrastructure agents (future)
├── guard/               # Visual/styling agents (future)
├── support/             # Support agents
├── src/
│   ├── runtime/         # Agent runtime system
│   ├── tools/           # Tool implementations
│   └── field/           # Applications built by agents
├── rehearsals/          # Development projects
├── performances/        # Production deployments
├── charts/              # Generated documentation
└── tests/               # Test suite
```

## Development Philosophy

### Test-Driven Development
All code is built following the Red-Green-Refactor cycle:
1. **RED** - Snare writes failing tests
2. **GREEN** - Bass writes minimal code to pass tests
3. **REFACTOR** - Visual Tech improves code quality

### Hierarchical Coordination
- Strategic decisions flow from leadership
- Domain expertise handled by specialized techs
- Caption heads coordinate within domains
- Drum Major maintains tempo and workflow

### Eating Our Own Dogfood
Ensemble is building itself. The UI and tooling are developed using the agent system.

## Roadmap

### Phase 1: Core Infrastructure (Current)
- [x] Requirements analysis
- [x] Architecture design
- [x] Basic TDD workflow
- [ ] File exploration
- [ ] Integration testing

### Phase 2: Domain Specialization
- [ ] Frontend agents (Trumpet, Horn, Baritone)
- [ ] Specialized backend agents (Tuba for APIs, Synth for DB)
- [ ] Visual/styling agents (Flag, Rifle, Saber, Dance)
- [ ] Caption heads for domain orchestration

### Phase 3: Full Orchestration
- [ ] Executive Director (system-level orchestrator)
- [ ] Deployment agents (Marimba, Vibes)
- [ ] Performance monitoring (Cymbal)
- [ ] Error recovery and resilience

### Phase 4: Self-Improvement
- [ ] Agent performance analytics
- [ ] Token usage optimization
- [ ] Automated agent refinement
- [ ] Continuous deployment pipeline

## Contributing

This project is currently in active development. Contributions welcome!

## License

[To be determined]

## Acknowledgments

Built with Claude (Anthropic API) and inspired by the dedication, precision, and artistry of drum corps worldwide.

---

*"In rehearsal, we build. In performance, we deliver."*
