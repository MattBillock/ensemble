# Prompt: Add Missing Documentation

## Context

Several areas of the codebase lack documentation, making maintenance harder.

## Priority
LOW - Improves maintainability

## Files to Modify

1. `src/field/ensemble_ui/backend/main.py` - Add endpoint docstrings
2. Various agent definition files - Clarify unclear sections
3. `src/runtime/agents/` - Document complex functions

## Requirements

### Part 1: Backend Endpoint Documentation

Add docstrings to all API endpoints following FastAPI best practices:

```python
@app.get("/api/metrics/summary")
async def get_metrics_summary(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get overall system metrics summary.

    Returns aggregated metrics including:
    - Total executions
    - Success rate
    - Average duration
    - Most active agents
    """
    # ...

@app.post("/api/generate-solution")
async def generate_solution(problem: ProblemRequest):
    """
    Submit a problem for the agent swarm to solve.

    Spawns an Executive Director agent who coordinates the solution.
    Returns immediately with an agent_id for tracking progress.

    Args:
        problem: Problem description and budget tier

    Returns:
        agent_id: Unique identifier for tracking
        status: Initial status ("started")
    """
    # ...
```

**Endpoints to document:**
- All POST endpoints (describe what they do)
- Complex GET endpoints (describe return structure)
- WebSocket endpoints (describe message protocol)

### Part 2: Document Data Models

Add docstrings to Pydantic models:

```python
class ProblemRequest(BaseModel):
    """Request to start solving a problem.

    Attributes:
        problem: Description of the problem to solve.
        budget_tier: Cost/capability tier - "economical", "balanced", or "full_firepower".
    """
    problem: str
    budget_tier: str = "balanced"

class StreamingConfig(BaseModel):
    """Configuration for real-time event streaming.

    Attributes:
        enabled: Whether streaming is active.
        poll_interval_ms: Polling interval in milliseconds (500-30000).
        event_types: Optional filter for specific event types.
    """
    enabled: bool = True
    poll_interval_ms: int = 2000
    event_types: Optional[List[str]] = None
```

### Part 3: Document Runtime Functions

Add docstrings to key runtime functions:

**activity_tracker.py:**
```python
def get_agent_hierarchy(self, request_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the agent spawn hierarchy.

    Args:
        request_id: Optional filter to get hierarchy for specific request.
                   If None, returns full hierarchy.

    Returns:
        Dict mapping agent_id to agent data including:
        - agent_name: Human-readable name
        - parent_id: ID of spawning agent
        - children: List of spawned agent IDs
        - status: Current status
    """
```

**metrics.py:**
```python
def record_execution(self,
                     agent_id: str,
                     agent_type: str,
                     success: bool,
                     duration_ms: int,
                     **kwargs):
    """
    Record an agent execution for analytics.

    Args:
        agent_id: Unique execution identifier
        agent_type: Type of agent (e.g., "backend_developer")
        success: Whether execution completed successfully
        duration_ms: Execution duration in milliseconds
        **kwargs: Additional fields (input_tokens, output_tokens, etc.)

    Note:
        Data is persisted to SQLite at ~/.ensemble/metrics.db
    """
```

### Part 4: Update CLAUDE.md If Needed

If any new patterns or conventions were established during cleanup, update CLAUDE.md:

- New error handling patterns
- API response formats
- Configuration options
- Security requirements

### Part 5: Create API_REFERENCE.md (Optional)

Consider creating an API reference document:

```markdown
# Ensemble API Reference

## Endpoints

### Agent Management
- POST /api/generate-solution - Start problem solving
- GET /api/status - Get system status
- GET /api/agents - List available agents

### Activity Tracking
- GET /api/activity/recent - Get recent activities
- GET /api/activity/hierarchy - Get agent hierarchy
...
```

## Acceptance Criteria

1. All POST endpoints have docstrings
2. Complex GET endpoints have docstrings
3. Data models have attribute documentation
4. Key runtime functions are documented
5. CLAUDE.md is up to date

## Test Plan

1. Run FastAPI and check /docs endpoint
2. Verify docstrings appear in OpenAPI UI
3. Review generated API documentation

## Notes

- Focus on "why" not "what" in docstrings
- Keep documentation concise
- Use consistent formatting
- Update as code changes
