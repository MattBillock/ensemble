# Prompt: Backend Security Improvements

## Context

The backend has overly permissive CORS settings and lacks input validation on several parameters, which could cause issues in production.

## Priority
MEDIUM - Security hardening for V1

## Files to Modify

1. `src/field/ensemble_ui/backend/main.py`

## Requirements

### Part 1: Restrict CORS

**Current Code (lines 566-572):**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Fix for Development:**
```python
# For development, allow localhost origins
ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative dev port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
```

**For Production (configurable):**
```python
import os

ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
```

### Part 2: Add Input Validation

Add validation to query parameters using FastAPI's Query:

```python
from fastapi import Query

# For days parameter (used in many endpoints)
@app.get("/api/metrics/summary")
async def get_metrics_summary(
    days: int = Query(default=30, ge=1, le=365, description="Number of days")
):
    # ...

# For limit parameter
@app.get("/api/activity/recent")
async def get_recent_activity(
    agent_id: Optional[str] = Query(default=None),
    request_id: Optional[str] = Query(default=None),
    activity_types: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000)
):
    # ...

# For threshold_minutes
@app.get("/api/recovery/stalled")
async def get_stalled_agents(
    threshold_minutes: int = Query(default=5, ge=1, le=60)
):
    # ...
```

**Apply to these endpoints:**

| Endpoint | Parameter | Validation |
|----------|-----------|------------|
| /api/metrics/summary | days | ge=1, le=365 |
| /api/metrics/agents | days | ge=1, le=365 |
| /api/metrics/models | days | ge=1, le=365 |
| /api/metrics/complexity | days | ge=1, le=365 |
| /api/metrics/trends | days | ge=1, le=365 |
| /api/metrics/errors | days | ge=1, le=365 |
| /api/metrics/correlation/{agent} | days | ge=1, le=365 |
| /api/activity/recent | limit | ge=1, le=1000 |
| /api/requests | limit | ge=1, le=1000 |
| /api/swarm/sessions | limit | ge=1, le=1000 |
| /api/swarm/agents | limit | ge=1, le=1000 |
| /api/swarm/events | limit | ge=1, le=1000 |
| /api/recovery/stalled | threshold_minutes | ge=1, le=60 |
| /api/recovery/scan | threshold_minutes | ge=1, le=60 |
| /api/recovery/history | limit | ge=1, le=1000 |
| /api/costs/summary | days | ge=1, le=365 |
| /api/costs/by-agent | days | ge=1, le=365 |
| /api/costs/by-model | days | ge=1, le=365 |
| /api/costs/trends | days | ge=1, le=365 |

### Part 3: Validate Path Parameters

Add validation for path parameters that reference resources:

```python
from fastapi import Path

@app.get("/api/agents/{agent_tier}/{agent_name}")
async def get_agent_definition(
    agent_tier: str = Path(..., regex="^(leadership|coordinators|developers|testers|designers)$"),
    agent_name: str = Path(..., regex="^[a-z_]+$")
):
    # ...
```

### Part 4: Sanitize File Paths

When handling file paths (like in agent update), validate to prevent directory traversal:

```python
import os

@app.post("/api/agents/update")
async def update_agent_file(update: AgentFileUpdate):
    # Validate path doesn't escape agent directories
    allowed_dirs = ["leadership", "coordinators", "developers", "testers", "designers"]

    # Normalize and validate path
    normalized = os.path.normpath(update.agent_path)
    if normalized.startswith("..") or normalized.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid path")

    parts = normalized.split(os.sep)
    if len(parts) < 2 or parts[0] not in allowed_dirs:
        raise HTTPException(status_code=400, detail="Path must be in agent directory")

    # Continue with update...
```

### Part 5: Add Rate Limiting (Optional for V1)

If desired, add basic rate limiting:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/generate-solution")
@limiter.limit("10/minute")
async def generate_solution(request: Request, problem: ProblemRequest):
    # ...
```

Note: This requires adding `slowapi` to dependencies.

## Acceptance Criteria

1. CORS restricted to known origins
2. All query parameters have validation bounds
3. Invalid inputs return 400 with clear message
4. Path traversal attacks are prevented
5. No breaking changes to valid requests

## Test Plan

1. Test CORS:
   ```bash
   # From a different origin, should be blocked
   curl -H "Origin: http://evil.com" http://localhost:8001/api/status
   ```

2. Test input validation:
   ```bash
   # Should return 400
   curl "http://localhost:8001/api/metrics/summary?days=-1"
   curl "http://localhost:8001/api/metrics/summary?days=1000"
   curl "http://localhost:8001/api/activity/recent?limit=10000"

   # Should work
   curl "http://localhost:8001/api/metrics/summary?days=30"
   ```

3. Test path validation:
   ```bash
   # Should return 400
   curl -X POST http://localhost:8001/api/agents/update \
     -H "Content-Type: application/json" \
     -d '{"agent_path": "../../../etc/passwd", "content": "test"}'
   ```

## Notes

- These are minimum security improvements for V1
- More comprehensive security review needed for production
- Consider adding authentication for sensitive endpoints
- Rate limiting is optional but recommended
