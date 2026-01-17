# Self-Improvement Recommendation Types

The self-improvement system analyzes agent performance metrics and applies targeted improvements to agent definitions. This document describes each recommendation type and its effects.

## Overview

The system continuously monitors agent executions stored in `~/.ensemble/metrics.db` and generates recommendations when performance patterns are detected. Recommendations require approval before being applied.

### Performance Thresholds

| Threshold | Value | Trigger |
|-----------|-------|---------|
| Critical | < 50% success | Immediate attention required |
| Warning | < 75% success | High priority improvement |
| High Performer | > 95% success | Cost optimization opportunity |

---

## Recommendation Types

### MODEL_UPGRADE
**Purpose**: Upgrade the agent's model tier for enhanced reasoning capability.

- **Trigger**: Success rate below target, tasks require more sophisticated reasoning
- **Action**: Updates `## Model Preference` in agent definition to higher tier
- **Tiers**: haiku (fast/cheap) → sonnet (balanced) → opus (most capable)
- **Effect**: Agent receives more powerful reasoning capabilities

### MODEL_DOWNGRADE
**Purpose**: Optimize costs by using a more efficient model tier.

- **Trigger**: Success rate >= 95% with 5+ executions
- **Action**: Updates `## Model Preference` to lower tier
- **Effect**: Reduced API costs while maintaining quality

### DEFINITION_TWEAK
**Purpose**: Minor adjustments to improve agent effectiveness.

- **Trigger**: Success rate between 50-75%
- **Action**: Combination of:
  - Model tier adjustment if needed
  - Iteration limit increases
  - Error handling additions
- **Effect**: Targeted improvements without major restructuring

### DEFINITION_MAJOR
**Purpose**: Comprehensive overhaul for critically failing agents.

- **Trigger**: Success rate below 50%
- **Action**: Multiple improvements including:
  - Upgrade to highest model tier (opus)
  - Extended iteration limits
  - Enhanced error handling
  - Detailed capability guidance
- **Effect**: Full capability enhancement

### ITERATION_INCREASE
**Purpose**: Allow more processing time for complex tasks.

- **Trigger**: Agent consistently using 80%+ of max iterations
- **Action**: Increases `## Max Iterations` value (typically +50%)
- **Effect**: Agent has more cycles to complete complex work

### ITERATION_DECREASE
**Purpose**: Reduce wasted iterations for efficient agents.

- **Trigger**: Agent consistently completing well under iteration limit
- **Action**: Decreases `## Max Iterations` value
- **Effect**: Faster completion, reduced costs

### COMPLEXITY_CHANGE
**Purpose**: Adjust task complexity rating to match actual workload.

- **Trigger**: Mismatch between configured and actual task complexity
- **Action**: Updates `## Task Complexity` field
- **Effect**: Better model selection via ModelSelector

---

## Specialized Enhancement Types

### PROMPT_REFINEMENT
**Purpose**: Improve instruction clarity and decision-making guidance.

- **Trigger**: Agent frequently asking unnecessary clarification questions
- **Action**: Adds `## Decision Making` section with:
  - Default assumption guidelines
  - When to ask vs proceed
  - Standard approach preferences
- **Effect**: More autonomous operation, fewer interruptions

### TOOL_OPTIMIZATION
**Purpose**: Improve tool usage patterns and reduce unnecessary calls.

- **Trigger**: Excessive tool calls detected in execution logs
- **Action**: Adds `## Tool Usage Optimization` section
- **Effect**: More efficient execution, reduced latency

### CONTEXT_TUNING (context_tuning)
**Purpose**: Optimize context window usage.

- **Trigger**: Context overflow or insufficient context retention
- **Action**: Adds `## Context Management` guidelines
- **Effect**: Better memory usage, more efficient processing

### OUTPUT_FORMAT (output_format)
**Purpose**: Improve output structure and parsing reliability.

- **Trigger**: Output parsing errors or inconsistent formatting
- **Action**: Adds `## Output Format Requirements` section
- **Effect**: More reliable structured outputs

### ERROR_HANDLING (error_handling)
**Purpose**: Better error recovery and graceful degradation.

- **Trigger**: Recurring specific error types in execution history
- **Action**: Adds `## Error Recovery` section with handlers for observed errors:
  - API errors: Retry with backoff
  - Timeouts: Chunk operations
  - Validation errors: Pre-validation steps
  - Parse errors: Try/catch patterns
- **Effect**: More resilient execution

### SPECIALIZATION (specialization)
**Purpose**: Narrow agent focus for better domain performance.

- **Trigger**: Agent attempting tasks outside its scope
- **Action**: Adds `## Focus Area` section
- **Effect**: Clearer boundaries, better delegation

### COLLABORATION (collaboration)
**Purpose**: Improve handoffs and coordination with other agents.

- **Trigger**: Poor sub-agent results or coordination issues
- **Action**: Adds `## Collaboration Protocol` section
- **Effect**: Better agent spawning and result handling

### MEMORY_STRATEGY (memory_strategy)
**Purpose**: Improve context retention across iterations.

- **Trigger**: Agent repeating work or losing track of progress
- **Action**: Adds `## Context Retention` guidelines
- **Effect**: Better continuity in long-running tasks

### TASK_DECOMPOSITION (task_decomposition)
**Purpose**: Better breaking down complex tasks into subtasks.

- **Trigger**: Monolithic task attempts, poor progress tracking
- **Action**: Adds `## Task Breakdown Strategy` section
- **Effect**: More manageable subtasks, clearer progress

### VALIDATION (validation)
**Purpose**: Better self-validation of outputs before completion.

- **Trigger**: Premature success reports, incomplete deliverables
- **Action**: Adds `## Output Validation` requirements
- **Effect**: Higher quality outputs, fewer false completions

---

## How Changes Are Applied

1. **Analysis** - System scans metrics.db for patterns
2. **Generation** - Recommendations created with evidence
3. **Review** - Pending recommendations visible in UI
4. **Approval** - Human approves via API or auto-approve
5. **Application** - Agent definition file modified
6. **Backup** - Original saved as `.md.pre_improvement`

### API Endpoints

```
GET  /api/self-improvement/recommendations    # List pending
POST /api/self-improvement/approve/{id}       # Approve one
POST /api/self-improvement/reject/{id}        # Reject one
POST /api/self-improvement/apply/{id}         # Apply approved
POST /api/self-improvement/auto-apply         # Auto-approve all
```

### File Changes

Changes are applied to agent definition markdown files in:
- `leadership/`
- `coordinators/`
- `developers/`
- `testers/`
- `designers/`

Original files backed up with `.pre_improvement` extension.

---

## Best Practices

1. **Review before auto-apply**: While auto-apply is available, manual review catches edge cases
2. **Monitor after changes**: Track if improvements actually help
3. **Minimum sample size**: System requires 3+ executions before generating recommendations
4. **Gradual upgrades**: Prefer stepping through tiers rather than jumping to opus
5. **Cost awareness**: High performers don't always need downgrades - consider task criticality

---

## Configuration

Performance analyzer constants in `src/runtime/agents/self_improvement.py`:

```python
CRITICAL_SUCCESS_THRESHOLD = 50.0   # Below = critical issue
WARNING_SUCCESS_THRESHOLD = 75.0    # Below = warning
HIGH_PERFORMER_THRESHOLD = 95.0     # Above = optimization candidate
MIN_EXECUTIONS_FOR_ANALYSIS = 3     # Minimum sample size
```

Recommendations stored in: `~/.ensemble/recommendations/recommendations_YYYYMMDD.json`
