# Agent Template

> **Instructions**: Copy this template and fill in the sections. Remove all instructions in quotes.

# {Agent Name}

## Purpose
> "One paragraph describing what this agent does and when it should be used."

## Instantiation Conditions
> "List conditions when this agent should be created/spawned."
- Condition 1
- Condition 2
- Condition 3

## Termination Conditions
> "List conditions when this agent should stop and return results."
- Condition 1
- Condition 2
- Condition 3

## Input Format
> "JSON schema for expected input."
```json
{
  "task": "Primary task description",
  "required_param_1": "description",
  "optional_param": "optional description"
}
```

## Output Format
> "JSON schema for output."
```json
{
  "status": "success|failure|partial",
  "result": "description of result",
  "message": "Human-readable summary",
  "self_analysis": "Required: Your performance analysis"
}
```

## Spawnable Agents
> "List of agents this agent can spawn. Format: **path/agent_name** - description"
- **coordinators/example_coordinator** - Description of when to spawn
- **developers/example_developer** - Description of when to spawn

## Available Tools
> "List of tools this agent can use."
- **spawn_agent**: Spawn sub-agents for specific tasks
- **read_file**: Read files from the filesystem
- **write_file**: Write files to the filesystem
- **run_command**: Execute shell commands

## Instructions
> "Main instructions for the agent. Be specific about workflow, rules, and expectations."

You are the {Agent Name}. {One sentence summary of primary responsibility}.

**CRITICAL RULES:**
- Rule 1
- Rule 2
- Rule 3

### Workflow

**Phase 1: {Phase Name}**
1. Step 1
2. Step 2

**Phase 2: {Phase Name}**
1. Step 1
2. Step 2

### Best Practices (What TO Do)

> "List positive behaviors and approaches."

**Category 1:**
- Practice 1
- Practice 2

### Anti-Patterns (What NOT to Do)

> "List behaviors to avoid. Use NEVER and Do NOT for emphasis."

**Category 1:**
- Do NOT do X
- NEVER do Y

## Self-Improvement Directive

**CRITICAL**: Analyze your performance in EVERY execution.

### Your Self-Analysis (self_analysis field):
1. **Metric 1**: Question about this metric?
2. **Metric 2**: Question about this metric?
3. **Metric 3**: Question about this metric?

Format: 2-4 sentences. Example:
"Example self-analysis text showing format."

## Clarification Conditions
> "List only extreme conditions when user input is needed."
- Condition 1
- Condition 2

## Model Preference
> "One of: haiku, sonnet, opus"
sonnet

## Max Iterations
> "Number between 10-50 depending on complexity"
25

## Can Write Code
> "true or false - ONLY true for developer agents"
false

## Can Write Tests
> "true or false - ONLY true for test writer agents"
false

## Task Complexity
> "One of: simple, moderate, strategic"
moderate
