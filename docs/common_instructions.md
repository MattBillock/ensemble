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

### Branch Management

- Work on feature branches, not main/master
- Use descriptive branch names (e.g., `feature/user-auth`, `fix/login-bug`)
- Keep commits atomic and focused
- Push regularly to avoid losing work

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

## Best Practices

1. **Think before acting**: Plan your approach before executing
2. **Validate inputs**: Check assumptions and prerequisites
3. **Test incrementally**: Verify small changes before proceeding
4. **Document decisions**: Explain non-obvious choices
5. **Communicate proactively**: Don't wait to report issues
6. **Learn from failures**: Analyze what went wrong and adjust
7. **Respect boundaries**: Stay within your agent role's scope
8. **Collaborate effectively**: Work with other agents, not in isolation
