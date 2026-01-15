# Prompt: Fix Backend Error Handling

## Context

The FastAPI backend has inconsistent error response formats and bare except clauses that swallow all exceptions. This makes debugging difficult and causes frontend issues.

## Priority
CRITICAL - Causes silent failures and inconsistent API behavior

## Files to Modify

1. `src/field/ensemble_ui/backend/main.py`

## Requirements

### Part 1: Fix Inconsistent Error Responses

**Location:** Line 865 and similar locations
**Current Code:**
```python
return ({"error": "Agent not found"}, 404)  # Wrong!
```

**Fixed Code:**
```python
from fastapi import HTTPException
# ...
raise HTTPException(status_code=404, detail="Agent not found")
```

Find and fix ALL locations that return tuples for errors. Search for patterns like:
- `return ({"error":`,
- `return {"error":` followed by `, 404)` or similar

Proper error responses should use HTTPException:
```python
raise HTTPException(status_code=404, detail="Resource not found")
raise HTTPException(status_code=400, detail="Invalid input")
raise HTTPException(status_code=500, detail="Internal server error")
```

### Part 2: Fix Bare Except Clauses

**Location:** Lines 643, 784 (WebSocket handlers)
**Current Code:**
```python
except:
    pass
```

**Fixed Code:**
```python
except Exception as e:
    logger.warning(f"WebSocket error: {e}")
```

Search for ALL bare `except:` clauses and replace with `except Exception as e:` with logging.

**Locations to check:**
- WebSocket handlers (`/ws/agent-status`, `/ws/events`)
- Any other try-except blocks without specific exception types

### Part 3: Add Input Validation

Add validation for query parameters that could cause issues:

```python
from fastapi import Query

@app.get("/api/metrics/summary")
async def get_metrics_summary(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze")
):
    # ...

@app.get("/api/activity/recent")
async def get_recent_activity(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum activities to return")
):
    # ...
```

Add validation to these parameters:
- `days` - should be >= 1 and <= 365
- `limit` - should be >= 1 and <= 1000
- `threshold_minutes` - should be >= 1 and <= 60

### Part 4: Standardize Error Response Format

Ensure all error responses follow the same format:
```json
{
  "detail": "Human readable error message"
}
```

This is FastAPI's default HTTPException format. Do NOT use custom formats like `{"error": "..."}`.

## Acceptance Criteria

1. No bare `except:` clauses in the codebase
2. All error responses use HTTPException
3. Error responses have consistent format
4. Query parameters have validation bounds
5. WebSocket errors are logged properly
6. Invalid inputs return 400 with clear messages

## Test Plan

1. Start backend: `cd src/field/ensemble_ui/backend && python main.py`
2. Test invalid inputs:
   ```bash
   curl http://localhost:8001/api/metrics/summary?days=-1
   # Should return 400 with validation error

   curl http://localhost:8001/api/agents/invalid/notfound
   # Should return 404 with proper JSON
   ```
3. Check logs for proper error logging
4. Verify no 500 errors from validation issues

## Notes

- Use `logger.warning()` for expected errors (4xx)
- Use `logger.error()` for unexpected errors (5xx)
- Include traceback for 500 errors: `logger.exception("Unexpected error")`
- Keep error messages user-friendly but informative
