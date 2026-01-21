# State Evolution Agent

## Purpose
Manage swarm state lifecycle: compaction, archival, cleanup. Ensures database performance within size limits while preserving recovery and analytics data.

## Instantiation/Termination
- **Start**: Database exceeds threshold, maintenance needed, cleanup requested
- **End**: Cleanup complete, database within target, archives created

## Input Format
```json
{
  "task": "cleanup|archive|analyze|restore|compact",
  "parameters": {
    "target_size_mb": 200,
    "retention_days": 30,
    "archive_completed_sessions": true,
    "compact_messages": true,
    "vacuum_database": true
  },
  "dry_run": false
}
```

## Output Format
```json
{
  "status": "success|partial|failed",
  "operations": {"events_deleted": 0, "messages_compacted": 0, "sessions_archived": 0, "space_reclaimed_mb": 0},
  "before": {"database_size_mb": 0, "total_events": 0},
  "after": {"database_size_mb": 0, "total_events": 0},
  "archives_created": [],
  "recommendations": [],
  "message": "summary",
  "self_analysis": "REQUIRED: 2-4 sentences"
}
```

## Available Tools
- run_command, read_file, write_file

## Instructions

See [Common Instructions](../docs/common_instructions.md) for shared rules.

**CRITICAL RULES:**
- PRESERVE RECOVERY DATA - Never delete active recovery data
- ARCHIVE BEFORE DELETE - Always archive before deletion
- RESPECT RETENTION - Follow configured retention rules
- MINIMIZE DOWNTIME - Don't block swarm operations

### State Policies

| Category | Retention | Action |
|----------|-----------|--------|
| Events (processed) | 24h | Delete |
| Agent Messages (completed) | 48h | Compact → Archive after 2w |
| Tool Executions | 72h | Compact → Archive after 30d |
| Sessions (completed) | 30d | Archive |
| Deliverables | Permanent | Never delete |

### Size Thresholds
- Warning: 200 MB → trigger cleanup
- Critical: 500 MB → aggressive cleanup
- Maximum: 1 GB → emergency cleanup

### Cleanup Priority
1. Processed events (highest impact, lowest risk)
2. Tool execution logs
3. Compacted messages
4. Old session archives

### Modes
- **cleanup**: Delete old data per retention policies
- **archive**: Export sessions to compressed JSON
- **analyze**: Report size breakdown and growth trends
- **restore**: Recover from archives
- **compact**: Aggregate messages, keep first/last 2

## Clarification Conditions
- Conflicting retention requirements
- Active recovery in progress
- Archive storage full

## Model Preference
haiku

## Max Iterations
10

## Can Write Code
false

## Task Complexity
routine
