# Inter-Agent Communication Optimization

**Date**: 2026-01-11
**Status**: Design & Implementation Plan
**Estimated Token Savings**: 30-40% on agent-to-agent communication

## Problem Statement

Currently, all agents use the same verbose output format regardless of audience:
- **Agents talking to agents**: Receive full summaries, explanations, context
- **Agents talking to humans**: Also receive full summaries, explanations, context

**Issue**: Agents don't need human-friendly explanations. They only need the essential data to continue their work. This wastes tokens and money.

## Current Communication Pattern

### Example: Coordinator → Developer
**Current (Verbose)**:
```json
{
  "status": "success",
  "message": "I have successfully broken down the authentication feature into 3 tasks for you to implement",
  "summary": "After analyzing the requirements, I've identified three core components needed for the authentication system",
  "tasks": [
    {
      "task_id": "auth-1",
      "description": "Implement login endpoint with email/password validation",
      "rationale": "This is the core authentication mechanism users will interact with",
      "dependencies": []
    },
    ...
  ],
  "recommendations": "I suggest implementing these in order, starting with the login endpoint",
  "self_analysis": "Task breakdown was clear with proper dependencies..."
}
```

**Token count**: ~350 tokens

### Optimized (Agent-Only)
```json
{
  "tasks": [
    {"id": "auth-1", "desc": "Login endpoint email/password", "deps": []},
    {"id": "auth-2", "desc": "JWT token generation", "deps": ["auth-1"]},
    {"id": "auth-3", "desc": "Token validation middleware", "deps": ["auth-2"]}
  ]
}
```

**Token count**: ~80 tokens
**Savings**: 77% reduction!

## Proposed Solution

### 1. Add `output_mode` Parameter

Add to all agent definitions:
```markdown
## Output Mode
agent_to_agent
```

OR

```markdown
## Output Mode
human_facing
```

### 2. Agent Categories

**Human-Facing Agents** (need verbose output):
- Executive Director → User
- Development Manager → User (for status updates)
- Agents responding to user questions

**Agent-Only Agents** (can use compact output):
- All Coordinators → Developers
- All Developers → Test Writers
- Test Writers → Validators
- System Architect → Everyone (technical specs)

### 3. Optimized Output Formats

#### Compact Format (Agent-to-Agent)

```json
{
  "s": "success|failed",           // status (1 char key)
  "d": {...},                       // data (core payload)
  "e": "error message" // optional  // error
}
```

#### Verbose Format (Human-Facing)

```json
{
  "status": "success|failed",
  "summary": "Human-readable summary",
  "data": {...},
  "message": "Detailed explanation",
  "recommendations": "What to do next",
  "error": "Error details" // optional
}
```

### 4. Implementation Strategy

#### Option A: Dual Output Formats in Agent Definitions

Add both formats to each agent definition:

```markdown
## Output Format (Human-Facing)
```json
{
  "status": "success",
  "summary": "...",
  "tasks": [...]
}
```

## Output Format (Agent-to-Agent)
```json
{
  "s": "ok",
  "t": [...]
}
```
```

#### Option B: Runtime Output Transformation

Keep current formats, but add a transformer:

```python
class OutputOptimizer:
    def optimize_for_agent(self, output: Dict[str, Any], agent_type: str) -> Dict[str, Any]:
        """Strip unnecessary fields for agent-to-agent communication."""

        if agent_type == "human_facing":
            return output  # No optimization

        # Agent-to-agent: Keep only essential fields
        essential_fields = self._get_essential_fields(output)

        optimized = {}
        for field in essential_fields:
            if field in output:
                # Use shorter keys
                short_key = self._get_short_key(field)
                optimized[short_key] = output[field]

        return optimized

    def _get_essential_fields(self, output: Dict[str, Any]) -> List[str]:
        """Determine which fields are essential."""
        # Always keep status and core data
        essential = ["status"]

        # Keep data fields
        for key in ["data", "tasks", "requirements", "architecture", "code", "tests"]:
            if key in output:
                essential.append(key)

        # Keep errors
        if "error" in output or output.get("status") == "failed":
            essential.append("error")

        return essential

    def _get_short_key(self, field: str) -> str:
        """Map verbose keys to short keys."""
        key_map = {
            "status": "s",
            "data": "d",
            "error": "e",
            "tasks": "t",
            "requirements": "r",
            "architecture": "a",
            "code": "c",
            "tests": "ts",
            "message": "m"
        }
        return key_map.get(field, field)
```

#### Option C: Prompt-Based Optimization (RECOMMENDED)

Add instructions to agent prompts based on who will receive the output:

**For agents spawning other agents:**
```markdown
## Output Format (when spawning agents)
When providing output to another agent (not a human), use compact format:
- Omit: summary, message, recommendations, rationale, self_analysis
- Include ONLY: status, essential data (tasks/code/tests), errors
- Use concise descriptions
- No explanations of "why" - just "what"

Example:
```json
{
  "status": "success",
  "tasks": [
    {"id": "t1", "desc": "Login endpoint", "deps": []},
    {"id": "t2", "desc": "JWT generation", "deps": ["t1"]}
  ]
}
```

NOT:
```json
{
  "status": "success",
  "summary": "I analyzed the requirements and created a comprehensive breakdown...",
  "message": "After careful consideration of the authentication flow...",
  "tasks": [...with verbose descriptions...],
  "recommendations": "I suggest starting with task 1 because...",
  "self_analysis": "My breakdown was effective because..."
}
```
```

## Expected Impact

### Token Savings by Agent Type

| Agent Type | Current Avg Tokens | Optimized Tokens | Savings |
|------------|-------------------|------------------|---------|
| Coordinators → Developers | 400 | 120 | 70% |
| System Architect → All | 800 | 300 | 62% |
| Test Writers → Validators | 350 | 100 | 71% |
| Leads → Writers | 300 | 100 | 67% |

### Cost Impact

Assuming 100 agent spawns per project:
- **Current**: 100 spawns × 400 tokens avg = 40,000 tokens
- **Optimized**: 100 spawns × 120 tokens avg = 12,000 tokens
- **Savings**: 28,000 tokens = **70% reduction in inter-agent communication**

At Sonnet pricing ($3 per 1M input tokens):
- **Current cost**: 40,000 tokens = $0.12
- **Optimized cost**: 12,000 tokens = $0.036
- **Savings per project**: $0.084 (70%)

For 100 projects/month: **$8.40/month savings** on just inter-agent communication.

## Implementation Plan

### Phase 1: Update Agent Prompts (Immediate)

1. Update all Coordinator agents (Backend, Frontend, Test)
   - Add "Output Format (Agent-to-Agent)" section
   - Emphasize: "When spawning agents, use compact format"

2. Update all Lead agents
   - Same compact output instructions

3. Update System Architect
   - Technical specs can be compact (no need to explain arch decisions to agents)

### Phase 2: Add Output Mode Detection (Week 2)

1. Add `output_mode` field to AgentDefinition
2. Parse from agent markdown files
3. Update runtime to pass this info to agents

### Phase 3: Add Validation (Week 3)

1. Create OutputValidator to check format compliance
2. Warn when agents use verbose format for agent-to-agent
3. Track compliance metrics

### Phase 4: Advanced Optimization (Month 2)

1. Implement OutputOptimizer class for automatic compression
2. Add compression for common patterns (task lists, file paths)
3. Create "communication profiles" for different agent pairs

## File Changes

### Agent Definitions to Update

**Coordinators** (high priority - spawn many agents):
- coordinators/backend_coordinator.md
- coordinators/frontend_coordinator.md
- coordinators/test_coordinator.md

**Leads** (medium priority):
- developers/backend_lead.md
- developers/frontend_lead.md
- testers/unit_test_lead.md
- testers/integration_test_lead.md

**Architects** (medium priority):
- leadership/system_architect.md

### New Files

- `src/runtime/agents/output_optimizer.py` (Phase 3)
- `src/runtime/agents/output_validator.py` (Phase 3)

## Example: Before vs After

### Backend Coordinator → Backend Developer

**Before (Current)**:
```json
{
  "status": "success",
  "summary": "I have analyzed the requirements and broken down the backend work into well-defined tasks",
  "message": "Based on the architecture document, I've identified three core backend components that need implementation. Each task has clear inputs and outputs to ensure smooth integration.",
  "tasks": [
    {
      "task_id": "backend-1",
      "description": "Implement user authentication service with bcrypt password hashing and JWT token generation",
      "requirements": "The service should handle login/signup, validate credentials, and return JWT tokens",
      "expected_output": "auth_service.py with UserAuth class",
      "rationale": "Authentication is foundational - all other services depend on it",
      "estimated_complexity": "medium",
      "dependencies": []
    },
    {
      "task_id": "backend-2",
      "description": "Create database models for User, Session, and RefreshToken using SQLAlchemy ORM",
      "requirements": "Models should include proper relationships, constraints, and indexes",
      "expected_output": "models.py with all entity definitions",
      "rationale": "Data persistence layer needed before business logic",
      "estimated_complexity": "low",
      "dependencies": ["backend-1"]
    }
  ],
  "recommendations": "I recommend implementing these in dependency order. Start with the auth service, then add database models. This ensures a solid foundation.",
  "self_analysis": "Task breakdown was clear and logical. Dependencies are properly sequenced. Complexity estimates are reasonable based on similar past implementations."
}
```
**Token count**: ~420 tokens

**After (Optimized)**:
```json
{
  "status": "success",
  "tasks": [
    {
      "id": "backend-1",
      "desc": "User auth service: bcrypt + JWT",
      "out": "auth_service.py",
      "deps": []
    },
    {
      "id": "backend-2",
      "desc": "DB models: User, Session, RefreshToken (SQLAlchemy)",
      "out": "models.py",
      "deps": ["backend-1"]
    }
  ]
}
```
**Token count**: ~85 tokens
**Savings**: 80%!

## Recommendations

1. **Start with Phase 1** (prompt-based) - Zero code changes, immediate savings
2. **Measure impact** - Track token usage before/after for 1 week
3. **Roll out incrementally** - Start with Coordinators (highest volume)
4. **Monitor quality** - Ensure agents still get required information
5. **Iterate** - Refine based on what works

## Potential Risks

1. **Information Loss**: Agents might miss important context
   - **Mitigation**: Start with redundant fields (summary, message), measure if agents reference them

2. **Debugging Harder**: Less verbose output harder to debug
   - **Mitigation**: Keep verbose logging separate from agent-to-agent communication

3. **Coordination Failures**: Agents might misunderstand compact format
   - **Mitigation**: Test thoroughly with key workflows first

## Next Steps

1. Update 3 coordinator agent definitions with compact output instructions
2. Run test workflow and compare token usage
3. Measure: tokens saved, agent success rate, output quality
4. If successful (>50% savings, no quality loss), roll out to all agent-to-agent communication
5. Implement automatic optimization in Phase 3

---

**Expected ROI**: 30-40% reduction in total token usage, 70% reduction in inter-agent communication, $8-15/month savings at current volumes.
