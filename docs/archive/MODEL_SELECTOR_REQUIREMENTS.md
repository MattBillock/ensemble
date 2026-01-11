# ModelSelector Implementation Requirements

## Vision
Create a budget-aware model selection system that allows users to control cost vs quality tradeoffs while ensuring agents get appropriate model power for their task complexity.

## Core Objectives

1. **Budget Tier System** - 3 tiers with clear cost/quality tradeoffs
2. **Task Complexity Mapping** - Match agent tasks to model capabilities
3. **Clean Integration** - Works with existing AgentDefinition/AgentRuntime
4. **Extensible** - Easy to add new models or tiers

## Budget Tiers

### Tier 1: full_firepower
**Philosophy**: Best model for each task regardless of cost
**Use Case**: Critical production work, complex projects, when quality matters most
**Cost**: $$$

**Model Mapping**:
- Strategic (high reasoning): `claude-opus-4-5-20251101`
- Creative (language/design): `claude-3-5-sonnet-20241022`
- Routine (validation): `claude-3-5-sonnet-20241022`

### Tier 2: balanced (DEFAULT)
**Philosophy**: Sonnet for thinking, Haiku for execution
**Use Case**: Most development work, good balance of cost and quality
**Cost**: $$

**Model Mapping**:
- Strategic: `claude-3-5-sonnet-20241022`
- Creative: `claude-3-5-sonnet-20241022`
- Routine: `claude-3-5-haiku-20241022`

### Tier 3: economical
**Philosophy**: Haiku everywhere except critical strategic decisions
**Use Case**: Experimental work, prototyping, when budget is tight
**Cost**: $

**Model Mapping**:
- Strategic: `claude-3-5-sonnet-20241022` (can't compromise here)
- Creative: `claude-3-5-haiku-20241022`
- Routine: `claude-3-5-haiku-20241022`

## Task Complexity Classification

### Strategic (High Reasoning)
**Characteristics**: Architecture decisions, planning, complex problem-solving
**Agents**:
- Executive Director (delegates quickly, but sets strategy)
- Development Manager (milestone planning, resource allocation)
- System Architect (technology choices, system design)
- TDD Coordinator (workflow enforcement, process decisions)

### Creative (Language & Design)
**Characteristics**: Code generation, documentation, UI design
**Agents**:
- Backend Developer, Frontend Developer
- Integration Test Writer (complex test scenarios)
- Style Developer
- All Leads (code review, supervision)

### Routine (Validation & Execution)
**Characteristics**: Straightforward tasks, validation, simple decisions
**Agents**:
- All Coordinators (task breakdown, delegation)
- Unit Test Writer (focused unit tests)
- Test runners, validators

## Implementation Requirements

### 1. ModelSelector Class

**Location**: `src/runtime/agents/model_selector.py`

**Interface**:
```python
class ModelSelector:
    """Select appropriate model based on budget tier and task complexity."""

    @classmethod
    def select_model(
        cls,
        budget_tier: str = "balanced",
        task_complexity: str = "routine",
        agent_name: Optional[str] = None
    ) -> str:
        """
        Select model for agent execution.

        Args:
            budget_tier: One of 'full_firepower', 'balanced', 'economical'
            task_complexity: One of 'strategic', 'creative', 'routine'
            agent_name: Optional agent name for logging

        Returns:
            Full model identifier (e.g., 'claude-3-5-haiku-20241022')

        Raises:
            ValueError: If tier or complexity is invalid
        """

    @classmethod
    def get_available_tiers(cls) -> List[str]:
        """Return list of available budget tiers."""

    @classmethod
    def estimate_cost_multiplier(cls, tier: str) -> float:
        """Return approximate cost multiplier for tier (relative to balanced)."""
```

**Tier Mapping**:
```python
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
```

### 2. AgentDefinition Updates

**Add field**: `task_complexity: str = "routine"`

**Update agent .md files** with task_complexity:
- Executive Director: `strategic`
- Development Manager: `strategic`
- System Architect: `strategic`
- TDD Coordinator: `strategic`
- All Developers: `creative`
- Integration Test Writer: `creative`
- Style Developer: `creative`
- All Coordinators: `routine`
- All Leads: `routine` (supervise but don't solve hard problems)
- Unit Test Writer: `routine`

### 3. AgentRuntime Integration

**Update**: `AgentRuntime.__init__` to accept `budget_tier` parameter
**Update**: Model selection to use `ModelSelector.select_model()`

**Before**:
```python
model = agent_definition.model_preference or "claude-3-5-haiku-20241022"
```

**After**:
```python
model = ModelSelector.select_model(
    budget_tier=self.budget_tier,
    task_complexity=agent_definition.task_complexity,
    agent_name=agent_definition.name
)
```

### 4. ExecutiveDirector Input Update

**Add budget_tier to input**:
```json
{
  "user_vision": "string",
  "output_directory": "string",
  "context": "string (optional)",
  "budget_tier": "balanced|full_firepower|economical (optional, default: balanced)"
}
```

**Propagate to spawned agents**: When Executive Director spawns Development Manager, pass budget_tier through.

## Testing Requirements

### Unit Tests Required

**test_model_selector.py**:
```python
def test_select_model_full_firepower_strategic():
    """Test full_firepower tier with strategic complexity returns opus."""
    model = ModelSelector.select_model("full_firepower", "strategic")
    assert model == "claude-opus-4-5-20251101"

def test_select_model_balanced_routine():
    """Test balanced tier with routine complexity returns haiku."""
    model = ModelSelector.select_model("balanced", "routine")
    assert model == "claude-3-5-haiku-20241022"

def test_select_model_invalid_tier():
    """Test invalid tier raises ValueError."""
    with pytest.raises(ValueError):
        ModelSelector.select_model("super_expensive", "strategic")

def test_select_model_default_parameters():
    """Test defaults to balanced/routine."""
    model = ModelSelector.select_model()
    assert model == "claude-3-5-haiku-20241022"

def test_get_available_tiers():
    """Test returns all 3 tiers."""
    tiers = ModelSelector.get_available_tiers()
    assert len(tiers) == 3
    assert "balanced" in tiers

def test_estimate_cost_multiplier():
    """Test cost multipliers are reasonable."""
    assert ModelSelector.estimate_cost_multiplier("economical") < 1.0
    assert ModelSelector.estimate_cost_multiplier("balanced") == 1.0
    assert ModelSelector.estimate_cost_multiplier("full_firepower") > 1.0
```

### Integration Tests Required

**test_budget_tier_integration.py**:
```python
def test_executive_director_accepts_budget_tier():
    """Test Executive Director accepts and uses budget_tier parameter."""
    # Create input with budget_tier
    # Run agent
    # Verify model selection respects tier

def test_budget_tier_propagates_to_children():
    """Test budget_tier is passed to spawned agents."""
    # Exec Dir spawns Dev Manager with tier
    # Verify Dev Manager uses same tier
```

## Success Criteria

1. ✅ ModelSelector class implemented with all methods
2. ✅ All 9 tier/complexity combinations tested
3. ✅ AgentDefinition includes task_complexity field
4. ✅ AgentRuntime uses ModelSelector for model selection
5. ✅ Executive Director accepts budget_tier parameter
6. ✅ Budget tier propagates through agent spawn chain
7. ✅ All tests passing (10+ unit tests, 2+ integration tests)
8. ✅ Documentation updated (docstrings, README)

## Deliverables

**New Files**:
1. `src/runtime/agents/model_selector.py` - ModelSelector class
2. `tests/test_model_selector.py` - Unit tests
3. `tests/test_budget_tier_integration.py` - Integration tests

**Modified Files**:
1. `src/runtime/agents/definition.py` - Add task_complexity field
2. `src/runtime/agents/runtime.py` - Use ModelSelector
3. `leadership/executive_director.md` - Add budget_tier to input
4. All 16 agent .md files - Add task_complexity value

**Documentation**:
1. Update README.md with budget tier usage
2. Add MODEL_SELECTION.md explaining tiers and complexity

## Out of Scope

- Cost tracking implementation (Milestone 3)
- Performance metrics collection (Milestone 3)
- Multi-provider support (Milestone 4)
- UI for tier selection (Milestone 2)

## Technical Constraints

- Must work with existing AgentDefinition format
- Backward compatible (if no budget_tier specified, use balanced)
- No breaking changes to current agent pipeline
- All existing tests must still pass

## Example Usage

```python
# Using agent pipeline with budget tier
input_data = {
    "user_vision": "Build a REST API",
    "output_directory": "./my-api",
    "budget_tier": "full_firepower"  # Use best models
}

# ModelSelector in action
model = ModelSelector.select_model(
    budget_tier="balanced",
    task_complexity="strategic",
    agent_name="System Architect"
)
# Returns: "claude-3-5-sonnet-20241022"

model = ModelSelector.select_model(
    budget_tier="full_firepower",
    task_complexity="strategic"
)
# Returns: "claude-opus-4-5-20251101"
```

## Cost Impact Estimates

**Assumptions**:
- Average pipeline: 40 API calls (from metrics)
- Mixed complexity: 10% strategic, 40% creative, 50% routine

**Estimated Cost per Pipeline**:
- **economical**: ~$0.10 (baseline)
- **balanced**: ~$0.15 (+50%)
- **full_firepower**: ~$0.40 (+300%)

**Recommendation**: Default to `balanced` for best cost/quality ratio.
