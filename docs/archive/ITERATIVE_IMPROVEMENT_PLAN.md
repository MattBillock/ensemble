# Iterative Improvement Plan - Milestone-Based Development

## Workflow Overview

**Continuous Improvement Loop**:
```
1. Implement recommendations from last analysis
2. Commit to GitHub + run next milestone
3. Comprehensive analysis (agents, separation of concerns, performance)
4. Extract recommendations for next iteration
5. REPEAT until application complete
```

## Domain-Driven Design Analysis

### Current Architecture vs DDD Principles

**DDD Core Concepts**:
- **Bounded Contexts**: Clear boundaries between subsystems
- **Ubiquitous Language**: Shared terminology across team/code
- **Aggregates**: Clusters of domain objects treated as units
- **Entities vs Value Objects**: Identity-based vs attribute-based
- **Domain Events**: State changes that trigger actions
- **Repositories**: Abstraction for persistence

### Current System Mapping to DDD

#### Bounded Contexts (Well-Defined ✅)
1. **Agent Runtime Context**
   - Aggregate Root: `AgentRuntime`
   - Entities: `AgentDefinition`, `ToolRegistry`
   - Value Objects: `InputData`, `OutputResult`
   - Domain Events: `AgentSpawned`, `ToolExecuted`, `AgentCompleted`

2. **Agent Orchestration Context**
   - Aggregate Root: `ExecutiveDirector`
   - Entities: `DevelopmentManager`, `Coordinator`, `Developer`
   - Value Objects: `Requirements`, `TaskBreakdown`, `Deliverables`
   - Domain Events: `RequirementsGathered`, `ArchitectureDesigned`, `CodeWritten`

3. **Permission & Validation Context**
   - Aggregate Root: `PermissionSystem`
   - Entities: `WriteFileTool`, `SpawnAgentTool`
   - Value Objects: `Permission`, `ValidationResult`
   - Domain Events: `RogueAgentDetected`, `PermissionDenied`

4. **Testing & Quality Context** (Needs Better Definition ⚠️)
   - Aggregate Root: `TDDCoordinator` (should be `TestingContext`)
   - Entities: `TestLead`, `TestWriter`
   - Value Objects: `TestSuite`, `CoverageReport`
   - Domain Events: `TestsFailed`, `TestsPassed`, `CoverageMet`

#### Issues with Current DDD Alignment

**1. Anemic Domain Model** 🔴
```python
# Current (Anemic - just data)
class AgentDefinition:
    name: str
    can_write_code: bool
    can_write_tests: bool

# Better (Rich Domain Model)
class AgentDefinition:
    name: str
    permissions: AgentPermissions

    def can_perform_action(self, action: Action) -> bool:
        return self.permissions.allows(action)

    def spawn_child(self, agent_type: str, inputs: dict) -> SpawnResult:
        # Business logic here, not in runtime
```

**2. Missing Domain Events** 🔴
Current system has no event system. Should emit:
- `AgentSpawned(agent_id, parent_id, timestamp)`
- `ToolExecuted(tool_name, agent_id, result)`
- `RogueAgentDetected(agent_id, attempted_action, reason)`
- `MilestoneCompleted(milestone_id, deliverables, metrics)`

**3. Leaky Abstractions** ⚠️
```python
# Current: Runtime knows about Anthropic API
from anthropic import Anthropic

# Better: Hide LLM provider behind domain interface
class LLMProvider(Protocol):
    def generate_response(self, prompt: PromptTemplate) -> Response
```

**4. Unclear Separation of Concerns** ⚠️
- AgentRuntime does too much (execution + state + API calls)
- Should separate: Executor, StateManager, LLMClient, EventPublisher

**5. No Repository Pattern** 🔴
```python
# Current: Direct file access everywhere
AgentDefinition.from_file(path)

# Better: Repository abstraction
class AgentRepository:
    def get_by_path(self, path: str) -> AgentDefinition
    def save(self, agent: AgentDefinition) -> None
    def find_by_role(self, role: str) -> List[AgentDefinition]
```

### Recommended DDD Refactoring

#### Phase 1: Extract Domain Entities (This Milestone)

```python
# src/domain/agent.py
@dataclass(frozen=True)
class AgentId:
    """Value Object: Unique agent identifier"""
    value: str

@dataclass
class AgentPermissions:
    """Value Object: What agent is allowed to do"""
    can_write_code: bool
    can_write_tests: bool
    allowed_tools: Set[str]

    def allows_action(self, action: str) -> bool:
        return action in self.allowed_tools

class Agent:
    """Entity: An executing agent instance"""
    def __init__(self, id: AgentId, definition: AgentDefinition):
        self.id = id
        self.definition = definition
        self._state = AgentState.INITIALIZING
        self._iteration = 0

    def execute_iteration(self, input_data: dict) -> IterationResult:
        """Execute one iteration of agent work"""
        # Business logic here

    def can_spawn_child(self, child_type: str) -> bool:
        """Domain logic: Can this agent spawn that type?"""
        return child_type in self.definition.allowed_spawns

# src/domain/events.py
@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events"""
    event_id: str
    timestamp: datetime
    aggregate_id: str

@dataclass(frozen=True)
class AgentSpawned(DomainEvent):
    agent_id: AgentId
    parent_id: Optional[AgentId]
    agent_type: str

@dataclass(frozen=True)
class RogueAgentDetected(DomainEvent):
    agent_id: AgentId
    attempted_action: str
    reason: str
```

#### Phase 2: Implement Repository Pattern

```python
# src/domain/repositories.py
class AgentDefinitionRepository(Protocol):
    def get_by_path(self, path: str) -> AgentDefinition
    def get_by_role(self, role: str) -> AgentDefinition
    def list_all(self) -> List[AgentDefinition]

class FileSystemAgentRepository(AgentDefinitionRepository):
    def __init__(self, base_path: Path):
        self.base_path = base_path

    def get_by_path(self, path: str) -> AgentDefinition:
        full_path = self.base_path / path
        return AgentDefinition.from_file(full_path)

class SessionRepository(Protocol):
    def save_session(self, session: Session) -> None
    def get_session(self, session_id: str) -> Session
    def list_active_sessions(self) -> List[Session]
```

#### Phase 3: Event-Driven Architecture

```python
# src/domain/event_bus.py
class EventBus:
    def __init__(self):
        self._handlers = defaultdict(list)

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable):
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent):
        for handler in self._handlers[type(event)]:
            handler(event)

# Usage in runtime:
event_bus.subscribe(RogueAgentDetected, log_security_incident)
event_bus.subscribe(AgentSpawned, update_metrics)
event_bus.subscribe(MilestoneCompleted, trigger_analysis)
```

#### Phase 4: Separate Application Services from Domain

```python
# src/domain/ - Pure business logic, no infrastructure
#   entities/
#   value_objects/
#   events/
#   repositories/ (interfaces only)

# src/application/ - Use cases, orchestration
#   services/
#     agent_execution_service.py
#     milestone_service.py
#   commands/
#     spawn_agent_command.py
#     execute_pipeline_command.py

# src/infrastructure/ - External concerns
#   llm/
#     anthropic_provider.py
#     openai_provider.py
#   persistence/
#     file_agent_repository.py
#     json_session_repository.py
#   api/
#     fastapi_routes.py
```

---

## Implementation Plan - Milestone by Milestone

### Milestone 0: Foundation Fixes (Current - Before UI Work)

**Objectives**:
1. Complete drum corps cleanup (339 → 0 references)
2. Consolidate agents (23 → 14)
3. Fix Executive Director coordination bug
4. Implement budget tier system
5. Apply initial DDD refactoring (extract domain entities)
6. Set up local CI/CD

**Deliverables**:
- ✅ All drum corps references removed
- ✅ Agent count reduced by 39%
- ✅ Budget tier selection working
- ✅ Domain layer extracted (`src/domain/`)
- ✅ Local CI running pre-commit hooks
- ✅ Updated documentation

**Success Criteria**:
- `grep -r "drum\|corps" returns 0 results (excluding historical docs)`
- Budget tier parameter works in ExecutiveDirector
- All tests pass with new domain layer
- Pre-commit hooks run tests automatically

**Analysis After Completion**:
- Agent performance comparison (before/after consolidation)
- Cost reduction from consolidation
- DDD refactoring impact on code clarity
- Coordination error rate (should decrease)

---

### Milestone 1: UI Backend Integration (Next)

**Objectives**:
1. Implement backend tasks from `src/field/ensemble_ui/backend_tasks.md`
2. Add UI features:
   - Model override selector
   - Application status endpoint
   - Agent file editing API
   - Config auto-reload
3. Apply DDD: Extract `ExecutionContext` aggregate
4. Implement repository pattern for agent definitions

**Deliverables**:
- ✅ FastAPI backend integrated with AgentRuntime
- ✅ WebSocket real-time updates working
- ✅ Model override API endpoint
- ✅ Agent repository pattern implemented
- ✅ Config hot-reload mechanism
- ✅ All backend tests passing (80%+ coverage)

**Analysis After Completion**:
- Which backend tasks were hardest? Why?
- Did repository pattern simplify code?
- Performance impact of config auto-reload
- API design quality assessment

---

### Milestone 2: UI Frontend Development

**Objectives**:
1. Implement frontend tasks from `src/field/ensemble_ui/frontend_tasks.md`
2. Add UI features:
   - Markdown WYSIWYG editor (use react-markdown-editor)
   - Model override dropdown
   - Agent file editor modal
   - Live application status
3. Apply DDD: Clear separation between UI components and domain

**Deliverables**:
- ✅ React components for all features
- ✅ Markdown editor with live preview
- ✅ Model override working end-to-end
- ✅ Agent editing UI functional
- ✅ All frontend tests passing

**Analysis After Completion**:
- Component reusability score
- UI/UX pain points
- WebSocket reliability
- Editor performance with large files

---

### Milestone 3: Testing & Quality

**Objectives**:
1. Implement strict TDD enforcement
2. Local CI/CD pipeline (GitHub Actions locally with `act`)
3. Comprehensive test coverage (90%+)
4. Apply DDD: Extract `TestingContext` as bounded context

**Deliverables**:
- ✅ Pre-commit hooks run all tests
- ✅ Local CI with act
- ✅ Coverage reports generated automatically
- ✅ Integration tests for agent pipeline
- ✅ E2E tests for UI

**Analysis After Completion**:
- Test coverage by module
- CI pipeline execution time
- Test failure patterns
- TDD enforcement effectiveness

---

### Milestone 4: Advanced Features

**Objectives**:
1. Always-on task monitoring
2. Performance metrics collection
3. Event-driven architecture (full DDD)
4. LLM provider abstraction

**Deliverables**:
- ✅ Task file watcher running
- ✅ Metrics dashboard in UI
- ✅ Event bus implemented
- ✅ Multi-provider support (Anthropic + OpenAI)

**Analysis After Completion**:
- Task processing latency
- Event system overhead
- Cost comparison across providers
- Metrics usefulness assessment

---

## Analysis Template (Run After Each Milestone)

### 1. Agent Performance Analysis
```
Agent Name          | Spawn Count | Success Rate | Avg Iterations | Issues
--------------------|-------------|--------------|----------------|--------
Executive Director  | X           | X%           | X.X            | List
Development Manager | X           | X%           | X.X            | List
...
```

### 2. Separation of Concerns Review
- Are responsibilities clearly divided?
- Any agents doing too much?
- Any agents doing too little?
- Recommend merges or splits

### 3. Code Quality Metrics
- Lines of code (by module)
- Cyclomatic complexity
- Test coverage %
- Documentation completeness

### 4. Performance Metrics
- Pipeline execution time
- API calls made
- Estimated cost
- Success rate

### 5. DDD Alignment Check
- Are bounded contexts clear?
- Is ubiquitous language consistent?
- Are domain events being used?
- Is business logic in domain layer?

### 6. What Went Well
- Which agents performed flawlessly?
- Which design decisions paid off?
- What should be expanded?

### 7. What Needs Improvement
- Which agents struggled?
- What coordination failures occurred?
- Where is code duplicated?
- What's still confusing?

### 8. Recommendations for Next Iteration
- High priority fixes
- Medium priority improvements
- Nice-to-haves
- Technical debt to address

---

## Automation: Continuous Analysis Script

```python
#!/usr/bin/env python3
"""analyze_milestone.py - Run after each milestone completion"""

import json
from pathlib import Path
from datetime import datetime

def analyze_milestone(milestone_name: str):
    """Comprehensive milestone analysis"""

    print(f"🔍 Analyzing Milestone: {milestone_name}")
    print("=" * 70)

    # 1. Agent Performance
    analyze_agent_performance()

    # 2. Code Metrics
    analyze_code_metrics()

    # 3. Test Coverage
    analyze_test_coverage()

    # 4. DDD Alignment
    analyze_ddd_alignment()

    # 5. Cost Estimation
    analyze_costs()

    # 6. Generate Report
    generate_analysis_report(milestone_name)

    print("✅ Analysis complete. See MILESTONE_ANALYSIS_{name}.md")

def analyze_agent_performance():
    """Parse logs to get agent performance stats"""
    # Read pipeline logs
    # Count spawns, successes, failures, iterations
    # Calculate success rates
    pass

def analyze_ddd_alignment():
    """Check if code follows DDD principles"""
    # Check for domain/ folder structure
    # Verify entities don't have infrastructure code
    # Check for event usage
    # Validate repository pattern
    pass

# ... more analysis functions
```

---

## Feature List: New UI Capabilities

### 1. Model Override Selector
**Location**: Problem submission form
**Functionality**:
- Dropdown: `Auto (Recommended)`, `Haiku`, `Sonnet`, `Opus`
- Overrides default model for entire pipeline
- Shows estimated cost impact
- Persists in session state

**Implementation**:
```typescript
interface ModelOverride {
  model: 'auto' | 'haiku' | 'sonnet' | 'opus';
  estimatedCost: number;
}

const ModelSelector: React.FC = () => {
  const [selectedModel, setSelectedModel] = useState<ModelOverride>({
    model: 'auto',
    estimatedCost: 0
  });

  return (
    <select onChange={handleModelChange}>
      <option value="auto">Auto (Recommended)</option>
      <option value="haiku">Haiku - Fast & Economical ($)</option>
      <option value="sonnet">Sonnet - Balanced ($$)</option>
      <option value="opus">Opus - Maximum Power ($$$)</option>
    </select>
  );
};
```

### 2. Markdown WYSIWYG Editor
**Location**: Problem submission, requirements editing
**Functionality**:
- Split view: editor | preview
- Syntax highlighting
- Toolbar: bold, italic, code, lists, links
- Auto-save to local storage
- Export to .md file

**Library**: `react-markdown-editor-lite` or `@uiw/react-md-editor`

### 3. Application Status Link
**Location**: Header/navbar
**Functionality**:
- Live status indicator: 🟢 Idle | 🟡 Processing | 🔴 Error
- Click to open status modal showing:
  - Current agent executing
  - Progress percentage
  - Time elapsed
  - Recent events log
- WebSocket connection status

### 4. Agent File Editor
**Location**: Settings or admin panel
**Functionality**:
- List all agent .md files
- Click to open in modal editor
- Syntax highlighting for markdown
- Save triggers config reload
- Version history (git-based)
- Validation before save (check required fields)

**Security**: Read-only by default, enable edit mode with flag

### 5. Auto-Reload Configs
**Backend Implementation**:
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AgentConfigWatcher(FileSystemEventHandler):
    def __init__(self, agent_registry):
        self.registry = agent_registry

    def on_modified(self, event):
        if event.src_path.endswith('.md'):
            print(f"Reloading {event.src_path}")
            self.registry.reload_agent(event.src_path)

observer = Observer()
observer.schedule(watcher, path='./agents', recursive=True)
observer.start()
```

---

## Local CI/CD Setup

### Pre-Commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: Run tests
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true

      - id: mypy
        name: Type checking
        entry: mypy src/
        language: system
        pass_filenames: false

      - id: ruff
        name: Linting
        entry: ruff check src/
        language: system
        pass_filenames: false

      - id: black
        name: Code formatting
        entry: black --check src/
        language: system
        pass_filenames: false
```

### GitHub Actions (Local with `act`)
```yaml
# .github/workflows/ci.yml
name: Continuous Integration

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov mypy ruff black

      - name: Run tests
        run: pytest --cov=src --cov-report=xml

      - name: Type checking
        run: mypy src/

      - name: Linting
        run: ruff check src/

      - name: Code formatting
        run: black --check src/

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

Run locally: `act -j test`

---

## Next Steps: Execution Order

1. ✅ Create this plan document
2. 🔄 Execute Milestone 0 (Foundation Fixes)
   - Use agent pipeline to implement fixes
   - Run comprehensive analysis after
3. 🔄 Execute Milestone 1 (Backend)
   - Use agent pipeline for implementation
   - Analysis after completion
4. 🔄 Execute Milestone 2 (Frontend)
5. 🔄 Execute Milestone 3 (Testing)
6. 🔄 Execute Milestone 4 (Advanced Features)

**After each milestone**:
- Run `analyze_milestone.py`
- Review generated analysis report
- Extract recommendations
- Commit improvements
- Start next milestone

---

## Success Metrics Across All Milestones

**Agent System**:
- Agent count: 23 → 14 (milestone 0)
- Success rate: 78% → 95%+ (by milestone 2)
- Avg iterations: 4.4 → 3.0 (by milestone 3)

**Code Quality**:
- Test coverage: Current → 90%+ (milestone 3)
- DDD alignment: 0% → 80%+ (milestone 4)
- Drum corps refs: 339 → 0 (milestone 0)

**Features**:
- Budget tiers: 0 → 3 (milestone 0)
- UI capabilities: 0 → 5 (milestone 2)
- LLM providers: 1 → 2+ (milestone 4)

**Performance**:
- Pipeline time: Baseline → 30% faster (milestone 4)
- Cost per run: Baseline → 40% cheaper (balanced tier, milestone 4)
