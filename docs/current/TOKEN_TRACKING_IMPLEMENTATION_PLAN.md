# Token Tracking & Agent Type Implementation Plan

**Date**: 2026-01-11
**Priority**: HIGH - Enables all cost optimizations
**Estimated Time**: 2-3 hours

## Problem Statement

From cost analysis, we identified two critical tracking issues:
1. **`tokens_used` is always NULL** - Cannot measure actual API costs
2. **`agent_type` is always "unknown"** - Cannot analyze costs by agent category

These prevent data-driven cost optimization.

## Root Causes

### 1. Token Tracking
**Location**: `src/runtime/agents/runtime.py:627`
```python
tokens_used=None,  # TODO: Extract from Anthropic response
```

**Issue**: Anthropic API response includes usage data but we're not capturing it:
```python
response = self.client.messages.create(**api_kwargs)  # Line 174
# response.usage contains:
# {
#   "input_tokens": 1234,
#   "output_tokens": 567
# }
```

### 2. Agent Type Tracking
**Location**: `src/runtime/agents/runtime.py:613`
```python
agent_type=agent_type,  # This is set to generic value
```

**Issue**: The agent_type variable is not derived from file path (leadership, coordinators, developers, etc.)

## Implementation Plan

### Phase 1: Add Token Tracking

#### Step 1.1: Track Usage in Runtime
**File**: `src/runtime/agents/runtime.py`

Add instance variable to track cumulative tokens:
```python
def __init__(self, ...):
    # ... existing init code ...
    self.total_input_tokens = 0
    self.total_output_tokens = 0
```

#### Step 1.2: Capture API Response Usage
**File**: `src/runtime/agents/runtime.py`

After API call (line 174), capture usage:
```python
response = self.client.messages.create(**api_kwargs)

# Capture usage from this iteration
if hasattr(response, 'usage'):
    self.total_input_tokens += response.usage.input_tokens
    self.total_output_tokens += response.usage.output_tokens
    logger.debug(f"Iteration {self.iteration_count}: "
                f"+{response.usage.input_tokens} input, "
                f"+{response.usage.output_tokens} output tokens")
```

#### Step 1.3: Pass Tokens to Metrics
**File**: `src/runtime/agents/runtime.py`

Update record_execution call (line 627):
```python
tokens_used=self.total_input_tokens + self.total_output_tokens,
```

#### Step 1.4: Add Token Breakdown to Metrics
**File**: `src/runtime/agents/metrics.py`

Optional enhancement - add separate input/output tracking:
```python
# In CREATE TABLE statement, add:
input_tokens INTEGER,
output_tokens INTEGER,

# Update record_execution signature to accept both
```

### Phase 2: Add Agent Category Tracking

#### Step 2.1: Add Category to AgentDefinition
**File**: `src/runtime/agents/definition.py`

Add category parameter to `__init__`:
```python
def __init__(
    self,
    name: str,
    # ... existing params ...
    task_complexity: str = "routine",
    category: str = "unknown",  # NEW
):
    # ... existing assignments ...
    self.category = category
```

#### Step 2.2: Derive Category from File Path
**File**: `src/runtime/agents/definition.py`

Update `from_file` method (line 73) to derive category:
```python
@classmethod
def from_file(cls, file_path: Path) -> "AgentDefinition":
    if not file_path.exists():
        raise FileNotFoundError(f"Agent definition file not found: {file_path}")

    # Derive category from parent directory
    category = "unknown"
    if file_path.parent.name in ["leadership", "coordinators", "developers", "testers", "designers"]:
        category = file_path.parent.name
    elif len(file_path.parts) >= 2:
        # Check if parent's parent is one of our categories
        parent_dir = file_path.parts[-2]
        if parent_dir in ["leadership", "coordinators", "developers", "testers", "designers"]:
            category = parent_dir

    content = file_path.read_text()
    # ... rest of existing code ...

    return cls(
        name=name,
        # ... existing params ...
        task_complexity=task_complexity,
        category=category,  # NEW
    )
```

#### Step 2.3: Use Category in Metrics
**File**: `src/runtime/agents/runtime.py`

Update metrics recording (line 613):
```python
metrics.record_execution(
    agent_id=self.agent_id,
    agent_type=self.definition.category,  # Use category instead of generic
    agent_name=self.definition.name,
    # ... rest of params ...
)
```

### Phase 3: Add Cost Calculation

#### Step 3.1: Add Cost Calculator
**File**: `src/runtime/agents/cost_calculator.py` (NEW)

```python
"""Cost calculation utilities for Anthropic API usage."""

class CostCalculator:
    """Calculate costs based on model and token usage."""

    # Pricing as of Jan 2026 (per million tokens)
    PRICING = {
        "claude-opus-4-5-20251101": {
            "input": 15.00,
            "output": 75.00
        },
        "claude-sonnet-4-5-20250929": {
            "input": 3.00,
            "output": 15.00
        },
        "claude-3-5-haiku-20241022": {
            "input": 0.80,
            "output": 4.00
        }
    }

    @classmethod
    def calculate_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for given usage.

        Returns:
            Cost in USD
        """
        if model not in cls.PRICING:
            # Unknown model, use Sonnet pricing as estimate
            pricing = cls.PRICING["claude-sonnet-4-5-20250929"]
        else:
            pricing = cls.PRICING[model]

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost
```

#### Step 3.2: Add Cost to Metrics Table
**File**: `src/runtime/agents/metrics.py`

Update schema:
```sql
CREATE TABLE IF NOT EXISTS agent_executions (
    -- ... existing columns ...
    tokens_used INTEGER,
    input_tokens INTEGER,       -- NEW
    output_tokens INTEGER,      -- NEW
    estimated_cost REAL,        -- NEW (in USD)
    -- ... rest of columns ...
)
```

Update record_execution:
```python
def record_execution(
    self,
    # ... existing params ...
    tokens_used: Optional[int] = None,
    input_tokens: Optional[int] = None,   # NEW
    output_tokens: Optional[int] = None,  # NEW
    estimated_cost: Optional[float] = None,  # NEW
    # ... rest of params ...
):
    # ... insert with new fields ...
```

#### Step 3.3: Calculate Cost in Runtime
**File**: `src/runtime/agents/runtime.py`

```python
from .cost_calculator import CostCalculator

# In _record_execution_metrics method:
estimated_cost = CostCalculator.calculate_cost(
    model=self.model_used or "unknown",
    input_tokens=self.total_input_tokens,
    output_tokens=self.total_output_tokens
)

metrics.record_execution(
    # ... existing params ...
    tokens_used=self.total_input_tokens + self.total_output_tokens,
    input_tokens=self.total_input_tokens,
    output_tokens=self.total_output_tokens,
    estimated_cost=estimated_cost,
    # ... rest of params ...
)
```

### Phase 4: Testing & Validation

#### Test 1: Token Tracking
```python
# Run a simple agent
from src.runtime.agents import AgentDefinition, AgentRuntime

agent = AgentDefinition.from_file(Path("developers/frontend_developer.md"))
runtime = AgentRuntime(agent, api_key=os.getenv("ANTHROPIC_API_KEY"))
result = runtime.execute({"task": "Create a simple React component"})

# Check database
sqlite3 ~/.ensemble/metrics.db "SELECT tokens_used, input_tokens, output_tokens, estimated_cost FROM agent_executions ORDER BY id DESC LIMIT 1;"
# Should show actual token counts, not NULL
```

#### Test 2: Agent Category
```python
# Check category derivation
sqlite3 ~/.ensemble/metrics.db "SELECT agent_type, agent_name, COUNT(*) FROM agent_executions GROUP BY agent_type, agent_name;"
# Should show "developers", "leadership", etc. instead of "unknown"
```

#### Test 3: Cost Calculation
```python
# Verify cost accuracy
sqlite3 ~/.ensemble/metrics.db "SELECT model_used, input_tokens, output_tokens, estimated_cost FROM agent_executions WHERE estimated_cost > 0 LIMIT 5;"
# Manually verify: (input_tokens/1M * $3) + (output_tokens/1M * $15) for Sonnet
```

## Migration Plan

### Database Migration
No schema changes needed if we keep existing columns! The columns already exist:
- `tokens_used` - will go from NULL to actual values
- `agent_type` - will go from "unknown" to categories

If we want to add input_tokens, output_tokens, estimated_cost:
```python
# Migration script: scripts/development/migrate_metrics_schema.py
import sqlite3
from pathlib import Path

db = Path.home() / ".ensemble" / "metrics.db"
conn = sqlite3.connect(db)

# Add new columns
conn.execute("ALTER TABLE agent_executions ADD COLUMN input_tokens INTEGER")
conn.execute("ALTER TABLE agent_executions ADD COLUMN output_tokens INTEGER")
conn.execute("ALTER TABLE agent_executions ADD COLUMN estimated_cost REAL")

conn.commit()
conn.close()
```

## Expected Results

### Before Implementation
```sql
SELECT agent_type, model_used, COUNT(*), AVG(tokens_used)
FROM agent_executions GROUP BY agent_type, model_used;
```
Result:
```
unknown | haiku  | 48  | NULL
unknown | sonnet | 109 | NULL
unknown | opus   | 23  | NULL
```

### After Implementation
```sql
SELECT agent_type, model_used, COUNT(*), AVG(input_tokens), AVG(output_tokens), SUM(estimated_cost)
FROM agent_executions GROUP BY agent_type, model_used;
```
Expected:
```
leadership   | sonnet | 35  | 15234 | 4321  | $2.45
coordinators | haiku  | 28  | 8234  | 2100  | $0.35
developers   | haiku  | 52  | 6500  | 3200  | $0.47
testers      | haiku  | 31  | 5800  | 2800  | $0.38
```

## Benefits

1. ✅ **Accurate Cost Tracking** - Know exactly what each agent costs
2. ✅ **Category Analysis** - Identify expensive agent categories
3. ✅ **Model Comparison** - Compare costs across models for same tasks
4. ✅ **Optimization Targets** - Data-driven decisions on where to optimize
5. ✅ **Budget Alerts** - Can set thresholds and alerts based on real costs

## Next Steps After Implementation

1. Add cost dashboard to UI showing:
   - Daily/weekly/monthly costs
   - Cost by agent category
   - Cost by model
   - Expensive agents/tasks

2. Implement cost alerts:
   - Email when daily cost exceeds threshold
   - Warning when single agent exceeds budget
   - Notification of cost anomalies

3. Add cost optimization recommendations:
   - "Switch agent X to Haiku - saves $Y per execution"
   - "Agent Y uses 10x iterations - investigate prompt"
   - "Category Z costs $X/day - consolidation opportunity"

## Files to Modify

1. `src/runtime/agents/definition.py` - Add category field
2. `src/runtime/agents/runtime.py` - Track tokens, use category
3. `src/runtime/agents/metrics.py` - Add token/cost fields (optional)
4. `src/runtime/agents/cost_calculator.py` - NEW file for cost calculation
5. `scripts/development/migrate_metrics_schema.py` - NEW migration script (if adding columns)

## Time Estimate

- Phase 1 (Token Tracking): 30 minutes
- Phase 2 (Category Tracking): 30 minutes
- Phase 3 (Cost Calculation): 45 minutes
- Phase 4 (Testing): 30 minutes

**Total**: ~2.5 hours for complete implementation and validation
