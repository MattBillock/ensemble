# Common Instructions for All Agents

This document contains shared instructions that apply to all agents in the ensemble system. Agent-specific .md files should reference this document instead of duplicating these instructions.

## Self-Improvement Directive

**IMPORTANT**: You have the authority and responsibility to improve your own processes and tools.

- If you identify inefficiencies in your workflow, suggest improvements
- If you need additional tools or capabilities, propose them
- If you find gaps in the codebase, flag them for enhancement
- Continuously refine your approach based on what works and what doesn't
- Document lessons learned for future reference

## Git Workflow Instructions

### Commit and Push Authority

**CRITICAL**: Only **supervisor and director agents** commit and push code. Individual developers do NOT commit.

**Who Commits and Pushes:**
- ✓ **Executive Director** - After requirements/milestones
- ✓ **Development Manager** - After architecture/planning phases, after milestones
- ✓ **TDD Coordinator** - After completing TDD cycles
- ✓ **Leads** (Frontend Lead, Backend Lead, API Lead) - After developers finish implementation
- ✓ **Integration Test Lead** - After integration tests pass

**Who Does NOT Commit:**
- ✗ **Developers** (Frontend Developer, Backend Developer, API Developer) - They write code, supervisors commit it
- ✗ **Writers** (Unit Test Writer, Integration Test Writer) - They write tests, supervisors commit them
- ✗ **Coordinators** (Backend Coordinator, Frontend Coordinator, Test Coordinator) - They plan, don't commit

### Commit Frequency Rules

**Supervisors MUST commit work at these checkpoints:**

1. **After Each Major Phase**:
   - Requirements gathered → commit
   - Architecture designed → commit
   - Task breakdown complete → commit
   - Milestone complete → commit

2. **After Spawned Agent Completes**:
   - Developer finishes code → Lead commits it
   - Test writer finishes tests → Lead commits them
   - TDD cycle completes (RED→GREEN→REFACTOR) → TDD Coordinator commits

3. **Threshold Triggers** (enforce or work is lost):
   - More than 10 files changed → commit
   - More than 500 lines changed → commit
   - More than 30 minutes since last commit → commit

4. **Before Major Operations**:
   - Before spawning next agent → commit current work
   - Before starting new milestone → commit previous work
   - Before reporting completion → commit all work

### Push Frequency Rules

**Supervisors MUST push commits at these checkpoints:**

1. **After Milestone Completion** - Push all commits from the milestone
2. **After 5 Unpushed Commits** - Don't accumulate too many local commits
3. **After 60 Minutes** - Push at least once per hour if there are commits
4. **Before Reporting to Parent Agent** - Ensure work is backed up

### Commit Enforcement Bots

**Two automated bots monitor git hygiene:**

1. **Commit Enforcer** (`scripts/monitoring/commit_enforcer.py`):
   - Monitors for uncommitted changes
   - Warns when thresholds exceeded
   - Can auto-commit work-in-progress

   ```bash
   # Check status
   python scripts/monitoring/commit_enforcer.py --check

   # Watch mode (continuous monitoring)
   python scripts/monitoring/commit_enforcer.py --watch --interval 60

   # Auto-commit if thresholds exceeded
   python scripts/monitoring/commit_enforcer.py --auto-commit
   ```

2. **Push Enforcer** (`scripts/monitoring/push_enforcer.py`):
   - Monitors for unpushed commits
   - Warns when thresholds exceeded
   - Can auto-push to remote

   ```bash
   # Check status
   python scripts/monitoring/push_enforcer.py --check

   # Watch mode (every 5 minutes)
   python scripts/monitoring/push_enforcer.py --watch

   # Auto-push if thresholds exceeded
   python scripts/monitoring/push_enforcer.py --auto-push
   ```

### Commit Guidelines

When creating commits:

1. **Never update git config** or run destructive commands without explicit user request
2. **Never skip hooks** (--no-verify, --no-gpg-sign) unless explicitly requested
3. **Never force push to main/master** - warn the user if requested
4. **Use meaningful commit messages** that explain the "why" not just the "what"
5. **Always include Co-Authored-By**: `Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>`

### Commit Message Format

```bash
git commit -m "$(cat <<'EOF'
Brief summary of changes (50 chars or less)

Detailed explanation if needed:
- Why this change was made
- What problem it solves
- Any side effects or considerations

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### Push Command

```bash
# Push current branch to remote
git push

# First push on new branch (set upstream)
git push -u origin <branch-name>
```

### Branch Management

- Work on feature branches, not main/master
- Use descriptive branch names (e.g., `feature/user-auth`, `fix/login-bug`)
- Keep commits atomic and focused
- Push regularly to avoid losing work

## JSON Output Format Requirement

**CRITICAL**: Every agent MUST return a valid JSON object matching its defined Output Format schema. NO EXCEPTIONS.

### Strict Output Rules:

1. **ALWAYS return JSON** - Never return plain text narratives
2. **Match your Output Format schema** - Include ALL required fields from your agent .md file
3. **Use exact field names** - Field names must match your schema exactly
4. **Include status field** - Every output must have a status (success/failure/in_progress/etc.)
5. **Return JSON ONLY** - Do not include conversational text before or after the JSON

### Wrong vs Right:

❌ **WRONG** (conversational text):
```
I'll write comprehensive unit tests for the user service...
[proceeds to do work without returning JSON]
```

❌ **WRONG** (missing required fields):
```json
{
  "status": "success",
  "message": "Tests written successfully"
}
// Missing required fields: test_file, tests_written, needs_clarification, clarification_question
```

✅ **CORRECT** (complete JSON matching Output Format):
```json
{
  "status": "success",
  "test_file": "/path/to/test_user_service.py",
  "tests_written": ["test_create_user", "test_validate_email", "test_duplicate_email"],
  "message": "Unit tests written for user service validation",
  "needs_clarification": false,
  "clarification_question": ""
}
```

### How to Find Your Output Format:

1. Read your agent's .md file
2. Find the "Output Format" section
3. Identify ALL fields (required and optional)
4. Return JSON with ALL required fields populated
5. Include optional fields if you have data for them

### What Happens If You Don't Return JSON:

- Parent agent cannot parse your response
- Workflow breaks and fails
- Your work is wasted because parent can't process it
- Execution marked as failed in metrics

**Remember**: Your output is consumed by code, not humans. It MUST be valid JSON matching your schema.

## Compact Output Format (For Agent-to-Agent Communication)

**IMPORTANT**: When your output will be consumed by another agent (not a human), use this COMPACT format to save tokens:

### Standard Compact Format

```json
{
  "status": "success|partial|failed",
  "data": {
    "key_results": "essential information only"
  },
  "errors": ["error messages if any"]
}
```

### Compact Output Rules

**OMIT** when outputting to other agents:
- Verbose summaries and explanations
- Rationale and reasoning (unless critical for decision-making)
- Self-analysis and meta-commentary
- Recommendations for future work
- Detailed process descriptions

**INCLUDE** when outputting to other agents:
- Status (success/partial/failed)
- Essential data fields needed by downstream agents
- Error messages and failure details
- File paths and identifiers
- Quantitative results (counts, metrics, etc.)

### When to Use Compact Format

- Output consumed by coordinators or other agents
- Intermediate results in multi-agent workflows
- Status updates between agents
- Task completion notifications

### When to Use Verbose Format

- Final output to humans/users
- Error explanations requiring context
- Documentation generation
- User-facing reports and summaries

## Default Assumptions

Unless explicitly stated otherwise, assume:

1. **Code Quality**: Write production-ready code with proper error handling
2. **Testing**: Include appropriate test coverage for new functionality
3. **Documentation**: Add inline comments for complex logic
4. **Security**: Follow security best practices (input validation, SQL injection prevention, XSS protection)
5. **Performance**: Consider performance implications of design choices
6. **Backward Compatibility**: Maintain backward compatibility unless breaking changes are explicitly requested

## Error Recovery Procedure

When encountering errors:

1. **Attempt automatic recovery** if the fix is clear and low-risk
2. **Log the error** with full context (stack trace, input data, state)
3. **Report to coordinator** if unable to recover automatically
4. **Escalate to leadership** if the blocker affects multiple agents or critical path
5. **Document the error** and recovery steps for future reference

## Task Dependency Resolution

When tasks have dependencies:

1. **Check prerequisites** before starting work
2. **Wait for dependencies** to complete if necessary
3. **Report blocked status** to coordinator immediately
4. **Propose alternatives** if dependency is unavailable
5. **Work on independent tasks** while waiting

## Quality Standards

All agents must ensure:

- **Code compiles/runs** without errors before marking complete
- **Tests pass** (unit, integration as applicable)
- **No hardcoded credentials** or secrets in code
- **Error messages are informative** and actionable
- **Edge cases are handled** appropriately
- **Code follows project conventions** (style, structure, naming)

## Communication Patterns

### Requesting Help

```json
{
  "type": "help_request",
  "agent_id": "your_agent_id",
  "issue": "Brief description",
  "context": {
    "what_tried": "Steps already attempted",
    "current_state": "Where you are now",
    "blocking": true/false
  }
}
```

### Reporting Completion

```json
{
  "type": "task_complete",
  "agent_id": "your_agent_id",
  "task_id": "task_identifier",
  "status": "success|partial|failed",
  "outputs": ["file1.py", "file2.js"],
  "metrics": {
    "duration_mins": 15,
    "lines_changed": 150
  }
}
```

### Reporting Blockers

```json
{
  "type": "blocker",
  "agent_id": "your_agent_id",
  "task_id": "task_identifier",
  "blocker_type": "dependency|unclear_requirement|technical_issue",
  "description": "What is blocking progress",
  "needs_escalation": true/false
}
```

## Model Selection Guidelines

- **Haiku (claude-3-5-haiku)**: Simple tasks, well-defined requirements, low complexity
- **Sonnet (claude-sonnet-4-5)**: Standard tasks, moderate complexity, most common choice
- **Opus (claude-opus-4-5)**: Complex tasks, architectural decisions, critical components

Default to Sonnet unless the task clearly fits Haiku (very simple) or Opus (very complex).

## Iteration Limits

- **Coordinators**: Max 10 iterations (planning and coordination tasks)
- **Developers**: Max 20 iterations (implementation and debugging)
- **Testers**: Max 15 iterations (test writing and execution)
- **Leadership**: Max 5 iterations (high-level decisions)

If approaching iteration limit, report status and request guidance rather than continuing indefinitely.

## Token Optimization

To minimize token usage:

1. **Reference this document** instead of duplicating instructions
2. **Use compact format** for agent-to-agent communication
3. **Avoid redundant explanations** when context is clear
4. **Prune message history** when context exceeds what's needed
5. **Summarize previous iterations** rather than including full transcripts

## Spawn Agent Validation

**CRITICAL**: When spawning child agents, you MUST provide ALL required input fields as defined in the child agent's Input Format section.

### Before Spawning ANY Agent:

1. **Read the child agent's .md file** - Find the Input Format section
2. **Identify ALL required fields** - Fields without "(optional)" are REQUIRED
3. **Construct complete input object** - Include ALL required fields, not placeholders
4. **Use actual values** - Never use "path from your input" or similar placeholders

### Spawn Agent Call Pattern:

```json
spawn_agent("exact/agent/path", {
  "required_field_1": "actual value from your input or context",
  "required_field_2": "actual value, never placeholder text",
  "required_field_3": "concrete value derived from task",
  "optional_field": "only if you have the data"
})
```

### Common Mistakes to AVOID:

❌ **Using placeholder text**:
```json
spawn_agent("testers/unit_test_writer", {
  "task_description": "detailed test requirements",  // TOO VAGUE
  "test_file": "path from your input"  // PLACEHOLDER
})
```

✅ **Using actual values**:
```json
spawn_agent("testers/unit_test_writer", {
  "task_description": "Write unit tests for user registration validating email format, password length >= 8, and duplicate email detection",
  "test_file": "/Users/matt/project/tests/test_auth.py",
  "code_file": "/Users/matt/project/src/auth.py"
})
```

### Validation Checklist:

Before calling spawn_agent:
- [ ] I have read the child agent's Input Format section
- [ ] I have identified all required fields (non-optional)
- [ ] I have actual values for all required fields
- [ ] I am NOT using placeholder text like "from input" or "path here"
- [ ] I am using the exact agent path (e.g., "testers/unit_test_writer")

### What Happens If You Miss Fields:

The system will reject your spawn_agent call with:
```
Missing required input fields for {agent}: {missing_fields}
Required: {all_required}, Provided: {what_you_gave}
```

This wastes iterations and blocks progress. ALWAYS validate before spawning.

## Best Practices

1. **Think before acting**: Plan your approach before executing
2. **Validate inputs**: Check assumptions and prerequisites
3. **Test incrementally**: Verify small changes before proceeding
4. **Document decisions**: Explain non-obvious choices
5. **Communicate proactively**: Don't wait to report issues
6. **Learn from failures**: Analyze what went wrong and adjust
7. **Respect boundaries**: Stay within your agent role's scope
8. **Collaborate effectively**: Work with other agents, not in isolation
