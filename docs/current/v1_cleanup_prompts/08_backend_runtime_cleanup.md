# Prompt: Fix Backend and Runtime Cleanup Issues

## Context

There are several half-implemented features and data issues in the backend and runtime that need cleanup.

## Priority
HIGH - Features appear available but don't work

## Files to Modify

1. `src/field/ensemble_ui/backend/main.py`
2. `src/runtime/agents/metrics.py`
3. `src/runtime/agents/tools.py`

## Requirements

### Part 1: Fix System Polish Endpoints (main.py)

**Location:** Lines 1800-1829
**Issue:** `/api/system-polish/start` creates config but background job never runs

**Option A - Make it work:**
```python
from fastapi import BackgroundTasks

@app.post("/api/system-polish/start")
async def start_system_polish(
    request: SystemPolishRequest,
    background_tasks: BackgroundTasks
):
    polish_id = f"polish_{int(time.time())}"

    # Create config
    config = {
        "polish_id": polish_id,
        "status": "running",
        # ... other fields
    }

    # Save config
    config_path = os.path.join(output_dir, f"{polish_id}_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f)

    # Actually run the background task
    background_tasks.add_task(run_system_polish, polish_id, request)

    return {"polish_id": polish_id, "status": "started"}

async def run_system_polish(polish_id: str, request: SystemPolishRequest):
    """Background task to run system polish."""
    try:
        # Implement actual polish logic
        # Update status file when complete
        pass
    except Exception as e:
        # Update status to failed
        pass
```

**Option B - Remove the feature:**
If system polish isn't needed for V1, remove the endpoints entirely:
- DELETE `/api/system-polish/start`
- DELETE `/api/system-polish/status/{polish_id}`
- DELETE `/api/system-polish/history`

### Part 2: Fix Metrics Insert (metrics.py)

**Location:** Around line 161
**Issue:** INSERT statement doesn't include token/cost columns that exist in schema

**Current Code:**
```python
cursor.execute('''
    INSERT INTO agent_executions (
        agent_id, agent_type, agent_name, model_used, success,
        error_type, duration_ms, iteration_count, ...
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ...)
''', (...))
```

**Fix:** Add missing columns:
```python
cursor.execute('''
    INSERT INTO agent_executions (
        agent_id, agent_type, agent_name, model_used, success,
        error_type, duration_ms, iteration_count,
        input_tokens, output_tokens, total_tokens, estimated_cost,
        ...
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ...)
''', (
    ...,
    input_tokens or 0,
    output_tokens or 0,
    (input_tokens or 0) + (output_tokens or 0),
    estimated_cost or 0.0,
    ...
))
```

### Part 3: Fix Git Commit Agent Name (tools.py)

**Location:** Around line 720
**Issue:** Records agent_id instead of agent_name in git activity

**Current Code:**
```python
agent_name = self.agent_id  # Could be improved by passing agent_name
```

**Fix:** Pass agent_name through tool context:

1. Update tool initialization to accept agent_name:
```python
def __init__(self, agent_id: str, agent_name: str = None, ...):
    self.agent_id = agent_id
    self.agent_name = agent_name or agent_id
```

2. Use agent_name in activity recording:
```python
agent_name = self.agent_name  # Now properly set
```

3. Update callers to pass agent_name when creating tools.

### Part 4: Add Thread Safety to Streaming Config (main.py)

**Location:** Lines 1754-1758
**Issue:** Global `_streaming_config` modified without locks

**Fix:**
```python
import threading

_streaming_config_lock = threading.Lock()
_streaming_config = {
    "enabled": True,
    "poll_interval_ms": 2000,
    "event_types": None
}

@app.post("/api/streaming/config")
async def update_streaming_config(config: StreamingConfig):
    with _streaming_config_lock:
        _streaming_config["enabled"] = config.enabled
        _streaming_config["poll_interval_ms"] = max(500, min(30000, config.poll_interval_ms))
        _streaming_config["event_types"] = config.event_types
        return _streaming_config.copy()
```

### Part 5: Hardcoded Cost Constants (main.py)

**Issue:** Cost calculations use hardcoded values scattered throughout
**Locations:** Lines 1543-1544, 1585-1586, 1626-1633, 1675-1676

**Fix:** Create a shared cost configuration:
```python
# At top of file
MODEL_COSTS = {
    "claude-opus-4-5-20251101": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku-20241022": {"input": 0.8, "output": 4.0},
}

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for token usage."""
    costs = MODEL_COSTS.get(model, {"input": 3.0, "output": 15.0})  # Default to sonnet
    return (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1_000_000
```

Then use this function in all cost calculations.

## Acceptance Criteria

1. System polish either works or endpoints are removed
2. Token usage data persists to metrics database
3. Git commits show agent names, not just IDs
4. Streaming config updates are thread-safe
5. Cost calculations use shared configuration

## Test Plan

1. If keeping system polish:
   ```bash
   curl -X POST http://localhost:8001/api/system-polish/start
   # Should return polish_id
   curl http://localhost:8001/api/system-polish/status/{polish_id}
   # Should show running/completed status
   ```

2. For metrics:
   - Run an agent
   - Check SQLite database for token data:
   ```bash
   sqlite3 ~/.ensemble/metrics.db "SELECT input_tokens, output_tokens, estimated_cost FROM agent_executions LIMIT 5"
   ```

3. For git commits:
   - Make a change via agent
   - Check activity feed shows agent name not ID

## Notes

- Choose Option A or B for system polish based on V1 requirements
- Metrics fix is important for cost tracking accuracy
- Thread safety is a precaution - may not cause issues in practice
