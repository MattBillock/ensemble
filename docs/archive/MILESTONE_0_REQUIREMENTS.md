# Milestone 0: Foundation Fixes

## Vision
Clean up technical debt, consolidate redundant agents, implement cost controls, and apply initial Domain-Driven Design principles. Create a solid foundation for UI development.

## Core Objectives

### 1. Complete Drum Corps Terminology Cleanup
**Current State**: 339 references remain across 20 files
**Target**: 0 references (excluding archived historical docs)

**Tasks**:
- Delete deprecated AGENT_ROSTER.md
- Scan all agent .md files in leadership/, coordinators/, developers/, testers/, designers/
- Replace all drum corps terminology in Purpose and Instructions sections
- Update code comments in test_rogue_detection.py, add_fail_fast_rules.py
- Clean references in .clinerules

**Success Criteria**:
- `grep -ri "drum\|corps\|brass\|percussion\|guard\|snare\|trumpet\|tuba" leadership/ coordinators/ developers/ testers/ designers/` returns 0 results
- AGENT_ROSTER.md deleted
- All agent Purpose sections use standard developer terminology

### 2. Agent Consolidation (23 → 14 Agents)
**Rationale**: Reduce coordination overhead, eliminate redundancy, improve clarity

**Consolidation Plan**:

**Frontend Tier** (4 → 2 agents):
- MERGE: `frontend_lead.md` + `component_lead.md` → `frontend_lead.md` (enhanced)
- MERGE: `frontend_developer.md` + `component_developer.md` → `frontend_developer.md` (enhanced)
- DELETE: `component_lead.md`, `component_developer.md`

**Backend Tier** (4 → 2 agents):
- MERGE: `backend_lead.md` + `api_lead.md` → `backend_lead.md` (enhanced)
- MERGE: `backend_developer.md` + `api_developer.md` → `backend_developer.md` (enhanced)
- DELETE: `api_lead.md`, `api_developer.md`

**Test Tier** (5 → 4 agents):
- MERGE: Test Validator functionality into `unit_test_lead.md` and `integration_test_lead.md`
- DELETE: `test_validator.md`
- KEEP: unit_test_lead, unit_test_writer, integration_test_lead, integration_test_writer

**Style Tier** (2 → 1 agent):
- MERGE: `style_lead.md` + `style_developer.md` → `style_developer.md` (enhanced)
- DELETE: `style_lead.md`

**Leadership Tier** (4 → 4 agents):
- KEEP ALL: executive_director, development_manager, system_architect, tdd_coordinator
- ENHANCE: Add budget tier support to executive_director

**Coordinators Tier** (3 → 3 agents):
- KEEP ALL: backend_coordinator, frontend_coordinator, test_coordinator

**New Total**: 14 agents (39% reduction)

**Success Criteria**:
- Only 14 .md files remain in agent directories
- AGENT_REGISTRY.md updated with new structure
- All references to deleted agents removed from remaining agents
- No broken spawn_agent calls

### 3. Fix Executive Director Coordination Bug
**Issue**: Executive Director forgets `requirements_file` parameter on first spawn of Development Manager

**Location**: `leadership/executive_director.md` line 60-67

**Fix Required**:
Add validation step before spawning:
```markdown
**Phase 2: Orchestrate Development**
5. Validate requirements document exists (read_file)
6. If missing → return error, do not spawn
7. Spawn Development Manager with ALL required fields:
   - requirements_file: "verified/path/to/requirements.md"
   - output_directory: "path/from/input"
   - project_name: "derived from user_vision or context"
8. Include example showing all three fields explicitly
```

**Success Criteria**:
- Executive Director spawns Development Manager successfully on first try
- No missing field errors in logs
- Instructions include validation step

### 4. Implement Budget Tier System
**Vision**: Give users cost control while ensuring quality

**Budget Tiers**:
1. **full_firepower**: Best model for each task regardless of cost
2. **balanced**: Sonnet for strategy, Haiku for execution (recommended)
3. **economical**: Haiku everywhere except critical decisions

**Implementation**:

**A. Add budget_tier to AgentDefinition**:
```python
# src/runtime/agents/definition.py
@dataclass
class AgentDefinition:
    name: str
    model_preference: str  # Keep for backwards compatibility
    budget_tier: Optional[str] = None  # New field
    task_complexity: str = "routine"  # New: strategic|creative|routine
```

**B. Create ModelSelector**:
```python
# src/runtime/agents/model_selector.py
class ModelSelector:
    TIER_MAPPING = {
        "full_firepower": {
            "strategic": "claude-opus-4-5-20251101",
            "creative": "claude-3-5-sonnet-20241022",
            "routine": "claude-3-5-sonnet-20241022"
        },
        "balanced": {
            "strategic": "claude-3-5-sonnet-20241022",
            "creative": "claude-3-5-sonnet-20241022",
            "routine": "claude-3-5-haiku-20241022"
        },
        "economical": {
            "strategic": "claude-3-5-sonnet-20241022",
            "creative": "claude-3-5-haiku-20241022",
            "routine": "claude-3-5-haiku-20241022"
        }
    }

    @classmethod
    def select_model(cls, tier: str, complexity: str) -> str:
        return cls.TIER_MAPPING.get(tier, "balanced")[complexity]
```

**C. Update agent definitions** with `task_complexity`:
- **Strategic**: executive_director, development_manager, system_architect, tdd_coordinator
- **Creative**: all developers, integration_test_writer
- **Routine**: coordinators, leads, unit_test_writer

**D. Update Executive Director** to accept and propagate budget_tier:
```markdown
## Input Format
{
  "user_vision": "string",
  "output_directory": "string",
  "context": "string (optional)",
  "budget_tier": "full_firepower|balanced|economical (optional, default: balanced)"
}
```

**Success Criteria**:
- budget_tier parameter works in ExecutiveDirector
- ModelSelector class implemented and tested
- Agent definitions include task_complexity
- Tests pass showing correct model selection per tier

### 5. Initial Domain-Driven Design Refactoring
**Vision**: Separate domain logic from infrastructure concerns

**Phase 1 Tasks** (Milestone 0):

**A. Create domain layer structure**:
```
src/
├── domain/           # Pure business logic (NEW)
│   ├── __init__.py
│   ├── entities/
│   │   ├── agent.py         # Agent, AgentId
│   │   └── session.py       # Session, SessionId
│   ├── value_objects/
│   │   ├── permissions.py   # AgentPermissions
│   │   └── result.py        # ExecutionResult
│   ├── events/
│   │   ├── base.py          # DomainEvent
│   │   └── agent_events.py  # AgentSpawned, RogueAgentDetected
│   └── repositories/
│       └── agent_repository.py  # Interface (Protocol)
├── runtime/          # Application layer (EXISTING - refactor)
│   └── agents/
└── infrastructure/   # External concerns (NEW)
    ├── llm/
    │   └── anthropic_provider.py
    └── persistence/
        └── file_agent_repository.py
```

**B. Extract core domain entities**:
- `AgentId` (value object)
- `AgentPermissions` (value object)
- `Agent` (entity with business logic)
- `DomainEvent` (base class)
- `AgentSpawned`, `RogueAgentDetected` (events)

**C. Create repository interface**:
```python
# src/domain/repositories/agent_repository.py
class AgentRepository(Protocol):
    def get_by_path(self, path: str) -> AgentDefinition:
        """Load agent definition from path"""

    def list_all(self) -> List[AgentDefinition]:
        """List all available agents"""
```

**D. Implement file-based repository**:
```python
# src/infrastructure/persistence/file_agent_repository.py
class FileAgentRepository(AgentRepository):
    def __init__(self, base_path: Path):
        self.base_path = base_path

    def get_by_path(self, path: str) -> AgentDefinition:
        return AgentDefinition.from_file(self.base_path / path)
```

**Success Criteria**:
- Domain folder structure exists
- Core entities extracted (Agent, AgentId, AgentPermissions)
- Repository interface defined
- At least one repository implementation (FileAgentRepository)
- Existing code refactored to use repository
- All tests still pass

### 6. Set Up Local CI/CD with Strict TDD
**Vision**: Catch errors before commit, enforce quality standards

**Tasks**:

**A. Install pre-commit hooks**:
```bash
pip install pre-commit
pre-commit install
```

**B. Create `.pre-commit-config.yaml`**:
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: Run all tests
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true

      - id: pytest-cov
        name: Check test coverage (80%+)
        entry: pytest --cov=src --cov-fail-under=80
        language: system
        pass_filenames: false

      - id: mypy
        name: Type checking
        entry: mypy src/ --strict
        language: system
        pass_filenames: false

      - id: ruff
        name: Linting
        entry: ruff check src/
        language: system
        pass_filenames: false
```

**C. Add GitHub Actions workflow** (`.github/workflows/ci.yml`):
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=src --cov-report=xml
      - run: mypy src/
      - run: ruff check src/
```

**D. Install `act` for local GitHub Actions**:
```bash
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

**E. Test locally**:
```bash
act -j test
```

**Success Criteria**:
- Pre-commit hooks installed and running
- Tests run automatically on commit
- GitHub Actions workflow exists
- Can run CI locally with `act`
- All current tests pass

## Out of Scope (Save for Later Milestones)

- UI implementation (Milestone 1 & 2)
- Event bus implementation (Milestone 4)
- LLM provider abstraction (Milestone 4)
- Always-on task monitoring (Milestone 4)
- Performance metrics collection (Milestone 3)

## Technical Constraints

- **Backward Compatibility**: Keep model_preference field for now (deprecated but functional)
- **No Breaking Changes**: Repository pattern should wrap existing code, not replace it yet
- **Test Coverage**: Maintain current coverage (don't decrease)
- **Agent Behavior**: Consolidated agents must perform all tasks of merged agents

## Success Criteria Summary

1. ✅ 0 drum corps references in active agent files
2. ✅ 14 agents (down from 23)
3. ✅ Executive Director spawns Development Manager correctly on first try
4. ✅ Budget tier selection working (3 tiers available)
5. ✅ Domain layer created with core entities
6. ✅ Pre-commit hooks running
7. ✅ All tests passing
8. ✅ Documentation updated (AGENT_REGISTRY.md, README.md)

## Deliverables

1. Updated agent definition files (14 total)
2. New files:
   - `src/runtime/agents/model_selector.py`
   - `src/domain/entities/agent.py`
   - `src/domain/value_objects/permissions.py`
   - `src/domain/repositories/agent_repository.py`
   - `src/infrastructure/persistence/file_agent_repository.py`
   - `.pre-commit-config.yaml`
   - `.github/workflows/ci.yml`
3. Deleted files:
   - `AGENT_ROSTER.md`
   - `component_lead.md`, `component_developer.md`
   - `api_lead.md`, `api_developer.md`
   - `test_validator.md`
   - `style_lead.md`
4. Updated files:
   - `AGENT_REGISTRY.md`
   - `README.md`
   - `leadership/executive_director.md`
   - All remaining agent .md files (drum corps cleanup)

## Testing Requirements

**Unit Tests Required**:
- `test_model_selector.py`: All tier/complexity combinations
- `test_agent_permissions.py`: Permission checking logic
- `test_agent_repository.py`: Repository implementations
- `test_executive_director_spawn.py`: Coordination bug fix verification

**Integration Tests Required**:
- `test_budget_tier_pipeline.py`: Full pipeline with each tier
- `test_consolidated_agents.py`: Merged agents perform all original tasks

**Coverage Target**: 80%+ overall, 90%+ for domain layer

## Analysis After Completion

Run comprehensive analysis covering:
1. Agent performance (spawn success rate, iterations)
2. Code metrics (LOC, complexity, coverage)
3. DDD alignment (domain purity check)
4. Cost impact (estimated savings from consolidation)
5. What went well (successful decisions to expand)
6. What needs improvement (issues to address in Milestone 1)
7. Recommendations for next iteration
