# Prompt: Make Hardcoded Values Configurable

## Context

Several values are hardcoded throughout the codebase that should be configurable for different environments.

## Priority
LOW - Improves flexibility

## Files to Modify

1. `src/field/ensemble_ui/backend/main.py`
2. `src/runtime/agents/runtime.py`
3. `src/runtime/agents/activity_tracker.py`
4. `src/runtime/agents/websocket_manager.py`

## Requirements

### Part 1: Create Configuration Module

Create a central configuration file:

```python
# src/runtime/agents/config.py
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class RuntimeConfig:
    # API Settings
    api_port: int = 8001
    api_host: str = "0.0.0.0"

    # Model Costs (per million tokens)
    model_costs: dict = None

    # Resilience
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    max_retries: int = 3

    # Activity Tracking
    max_activities: int = 10000
    max_message_history: int = 50

    # WebSocket
    websocket_buffer_size: int = 100
    websocket_heartbeat_interval: int = 30

    # Timeouts
    default_command_timeout: int = 30
    max_command_timeout: int = 600

    def __post_init__(self):
        if self.model_costs is None:
            self.model_costs = {
                "claude-opus-4-5-20251101": {"input": 15.0, "output": 75.0},
                "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
                "claude-3-5-haiku-20241022": {"input": 0.8, "output": 4.0},
            }

def load_config() -> RuntimeConfig:
    """Load configuration from environment variables."""
    return RuntimeConfig(
        api_port=int(os.environ.get("ENSEMBLE_API_PORT", 8001)),
        api_host=os.environ.get("ENSEMBLE_API_HOST", "0.0.0.0"),
        circuit_breaker_threshold=int(os.environ.get("ENSEMBLE_CB_THRESHOLD", 5)),
        circuit_breaker_timeout=int(os.environ.get("ENSEMBLE_CB_TIMEOUT", 60)),
        max_retries=int(os.environ.get("ENSEMBLE_MAX_RETRIES", 3)),
        max_activities=int(os.environ.get("ENSEMBLE_MAX_ACTIVITIES", 10000)),
        websocket_buffer_size=int(os.environ.get("ENSEMBLE_WS_BUFFER", 100)),
    )

# Global config instance
config = load_config()
```

### Part 2: Update Backend to Use Config

**main.py:**
```python
from runtime.agents.config import config

# Replace hardcoded port
if __name__ == "__main__":
    uvicorn.run(app, host=config.api_host, port=config.api_port)

# Replace hardcoded costs
def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    costs = config.model_costs.get(model, {"input": 3.0, "output": 15.0})
    return (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1_000_000
```

### Part 3: Update Runtime to Use Config

**runtime.py:**
```python
from .config import config

class AgentRuntime:
    def __init__(self, ...):
        # Replace hardcoded values
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_breaker_threshold,
            recovery_timeout=config.circuit_breaker_timeout
        )
        self.max_retries = config.max_retries
```

**activity_tracker.py:**
```python
from .config import config

class ActivityTracker:
    def __init__(self):
        self.max_activities = config.max_activities
        # ...
```

**websocket_manager.py:**
```python
from .config import config

class WebSocketManager:
    def __init__(self):
        self.buffer_size = config.websocket_buffer_size
        self.heartbeat_interval = config.websocket_heartbeat_interval
```

### Part 4: Environment Variable Documentation

Create a .env.example file:

```bash
# src/field/ensemble_ui/.env.example

# API Configuration
ENSEMBLE_API_PORT=8001
ENSEMBLE_API_HOST=0.0.0.0

# Resilience Settings
ENSEMBLE_CB_THRESHOLD=5      # Circuit breaker failure threshold
ENSEMBLE_CB_TIMEOUT=60       # Circuit breaker recovery timeout (seconds)
ENSEMBLE_MAX_RETRIES=3       # Max API retries

# Activity Tracking
ENSEMBLE_MAX_ACTIVITIES=10000  # Max activities to keep in memory

# WebSocket Settings
ENSEMBLE_WS_BUFFER=100       # Event buffer size

# CORS (comma-separated origins)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Part 5: Frontend Configuration

For frontend, use environment variables via Vite:

```javascript
// src/field/ensemble_ui/frontend/src/services/api.js
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';
```

Create `.env` file:
```bash
# src/field/ensemble_ui/frontend/.env
VITE_API_BASE=http://localhost:8001
```

## Acceptance Criteria

1. All hardcoded values moved to config
2. Environment variables documented
3. Sensible defaults for all config values
4. No breaking changes when running without env vars
5. .env.example files created

## Test Plan

1. Run without any environment variables - should use defaults
2. Set custom values and verify they're used:
   ```bash
   ENSEMBLE_API_PORT=9000 python main.py
   # Should start on port 9000
   ```
3. Verify frontend API_BASE is configurable

## Notes

- Keep defaults matching current hardcoded values
- Document all configuration options
- Use descriptive environment variable names
- Consider using python-dotenv for .env file support
