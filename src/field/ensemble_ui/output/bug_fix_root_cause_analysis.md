# Root Cause Analysis: UI Files Endpoint 404 Error

## Issue Summary

**Error**: Frontend receiving HTTP 404 "Not Found" when polling `/api/activity/files` endpoint  
**Date**: 2026-01-11  
**Severity**: High - Blocks file display functionality in UI

## Investigation Results

### 1. Backend Status
✅ **Backend is running** on port 8001 (confirmed via curl to `/api/status`)  
✅ **Endpoint is defined** in code at line 752 of `backend/main.py`  
❌ **Endpoint returns 404** when called via HTTP  
✅ **Endpoint works in TestClient** (returns 200 OK with empty files list)

### 2. Key Findings

**TestClient Success**:
```bash
$ python3 -c "from fastapi.testclient import TestClient; from src.field.ensemble_ui.backend.main import app; client = TestClient(app); response = client.get('/api/activity/files'); print(response.status_code)"
# Result: 200 OK
# Response: {"files": [], "count": 0}
```

**HTTP Request Failure**:
```bash
$ curl http://localhost:8001/api/activity/files
# Result: 404 Not Found
# Response: {"detail":"Not Found"}
```

### 3. Root Cause

**STALE SERVER PROCESS**

The running uvicorn server on port 8001 is using an **older version of main.py** that does not include the `/api/activity/files` endpoint. The endpoint was added to the source code but the server was not restarted.

**Evidence**:
1. Port 8001 is in use (lsof shows connections)
2. `/api/status` endpoint works (exists in both old and new versions)
3. `/api/activity/files` endpoint defined in current source code (line 752)
4. TestClient (loads fresh code) returns 200, but HTTP server returns 404
5. No python/uvicorn processes found in ps output (likely running in different terminal/IDE)

### 4. Why This Happened

**Most Likely Scenario**:
- Backend server was started during development
- `/api/activity/files` endpoint was added later (along with activity tracking features)
- Server was not restarted after code changes
- Uvicorn auto-reload may have failed or been disabled
- Server might be running in an IDE terminal, VSCode, or another window

**Alternative Possibilities**:
- Server running with `reload=False`
- Server started from different directory (loading wrong module)
- Server process orphaned/detached from terminal

## Solution

### Immediate Fix
**Restart the backend server**

1. Find and stop the running server:
   ```bash
   # Find the process
   lsof -ti :8001 | xargs kill -9
   
   # Or if running in visible terminal, press Ctrl+C
   ```

2. Restart with auto-reload enabled:
   ```bash
   cd /Users/mattbillock/Development/ai_exploration/ensemble/src/field/ensemble_ui/backend
   python3 main.py
   
   # Or with uvicorn directly:
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```

3. Verify fix:
   ```bash
   curl http://localhost:8001/api/activity/files
   # Should return: {"files": [], "count": 0}
   ```

### Verification Steps

1. **Backend health**: `curl http://localhost:8001/api/status` → 200 OK
2. **Files endpoint**: `curl http://localhost:8001/api/activity/files` → 200 OK (not 404)
3. **Frontend test**: Open UI in browser, check console for `/api/activity/files` errors
4. **Integration**: Trigger agent to generate file, verify it appears in UI

## Prevention Measures

### 1. Enforce Auto-Reload in Development
Update `main.py` to ensure reload is always on during development:

```python
if __name__ == "__main__":
    # Development mode with auto-reload
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,  # Already present - ensure this stays
        reload_dirs=[...],  # Already configured
    )
```

### 2. Add Startup Version Check
Add logging to show code version/timestamp on server start:

```python
@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 Backend started at {datetime.now().isoformat()}")
    logger.info(f"📁 Code location: {Path(__file__).resolve()}")
    logger.info(f"✅ Endpoints registered: {len(app.routes)}")
```

### 3. Health Endpoint Version Info
Add version/build info to `/api/status`:

```python
@app.get("/api/status")
async def get_application_status():
    return {
        "status": "running",
        "version": "1.0.0",  # Or git commit hash
        "code_timestamp": os.path.getmtime(__file__),
        "endpoints": len(app.routes),
        "active_agents": len(orchestrator.active_agents),
        ...
    }
```

### 4. Frontend Error Handling
Improve error messages in frontend to distinguish between:
- Backend down (connection refused)
- Backend stale (404 on known endpoint)
- Backend error (500)

### 5. Developer Documentation
Add to README:

```markdown
## Development Workflow

### Starting Backend
```bash
cd src/field/ensemble_ui/backend
python3 main.py  # Auto-reload enabled by default
```

### Code Changes
- Server auto-reloads when .py or .md files change
- If 404 errors appear after adding new endpoints: restart server manually
- Check terminal for reload errors (sometimes auto-reload fails silently)
```

## Conclusion

**Root Cause**: Stale backend server process serving old code without `/api/activity/files` endpoint

**Fix**: Restart backend server to load current code

**Impact**: 
- Frontend will stop seeing 404 errors
- Generated files will display correctly in UI
- Activity tracking features will work as intended

**Risk**: Low - This is a development environment issue, not a production bug

**Time to Fix**: < 1 minute (stop + restart server)
