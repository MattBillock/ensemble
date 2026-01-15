# Prompt: Update Agent Registry Documentation

## Context

The AGENT_REGISTRY.md lists 16 agents but there are actually 19+ agent definition files. The registry needs to be updated to document ALL agents and their status (active, deprecated, special-purpose).

## Priority
HIGH - Documentation doesn't match reality

## Files to Modify

1. `docs/current/AGENT_REGISTRY.md`

## Requirements

### Part 1: Document All Existing Agents

Add the following agents that exist but aren't in the registry:

**API Agents (Add to Developer Tier):**
- `api_lead` - Supervises API endpoint development, can spawn api_developer
- `api_developer` - Writes API endpoint code, can_write_code: true
- `api_test_writer` - Writes API tests, can_write_tests: true

**Special Leadership Agents (Add new section):**
- `code_quality_director` - Oversees code quality and standards
- `system_polish_director` - Handles system refinement and polish
- `question_marshal` - Manages user questions and clarifications

**Database Agent (Add to Developer Tier or clarify status):**
- `database_manager` - Database schema and migrations, can_write_code: true
  - Note: Currently orphaned - no clear spawn path

### Part 2: Fix Model Preferences

Update the model preferences table to match what's actually needed:

| Agent | Current in Definitions | Recommended | Reason |
|-------|----------------------|-------------|--------|
| Executive Director | sonnet | sonnet | Strategic decisions, OK |
| Development Manager | haiku | sonnet | Strategic planning needs more capability |
| System Architect | haiku | opus | Architectural decisions are critical |
| TDD Coordinator | haiku | sonnet | Workflow enforcement needs reasoning |

### Part 3: Document Spawn Paths

Add clear spawn path documentation:

```
Executive Director
  └── Development Manager (spawned by exec_dir)
        ├── System Architect (spawned by dev_mgr)
        ├── Backend Coordinator (spawned by dev_mgr)
        │     └── (writes task breakdown files, no spawning)
        ├── Frontend Coordinator (spawned by dev_mgr)
        │     └── (writes task breakdown files, no spawning)
        ├── Test Coordinator (spawned by dev_mgr)
        │     └── (writes test strategy files, no spawning)
        └── TDD Coordinator (spawned by dev_mgr)
              ├── Backend Lead
              │     └── Backend Developer (code writer)
              ├── Frontend Lead
              │     └── Frontend Developer (code writer)
              ├── API Lead
              │     └── API Developer (code writer)
              ├── Unit Test Lead
              │     └── Unit Test Writer (test writer)
              └── Integration Test Lead
                    └── Integration Test Writer (test writer)

Style Developer (can be spawned by Frontend Lead)
Database Manager (unclear spawn path - needs clarification)

Special Purpose (Direct Invocation):
- Code Quality Director
- System Polish Director
- Question Marshal
```

### Part 4: Add Status Column

For each agent, add a status column:
- **active** - Part of normal workflow
- **special** - Invoked directly for specific purposes
- **deprecated** - Exists but shouldn't be used
- **orphaned** - Exists but has no spawn path (needs fix)

### Part 5: Fix Terminology References

Document the drum corps to standard name mapping for reference:
| Old Name | New Name |
|----------|----------|
| Snare | Unit Test Writer |
| Trumpet | Frontend Developer |
| Synth | Backend Developer |
| Percussion Coordinator | Test Coordinator |
| Brass Coordinator | Backend/Frontend Coordinator |

Note that these old names should NOT be used anywhere in agent definitions.

## Acceptance Criteria

1. All 19+ agents are documented
2. Model preferences match recommendations
3. Spawn paths are clearly documented
4. Each agent has a status (active/special/deprecated/orphaned)
5. Old terminology is documented but marked as deprecated
6. Total agent count is accurate

## Test Plan

1. Count all .md files in agent directories:
   ```bash
   find leadership coordinators developers testers designers -name "*.md" | wc -l
   ```
2. Compare count to registry
3. Verify each documented agent has a corresponding file
4. Verify spawn permissions match documented paths

## Notes

- This is a documentation task, no code changes
- Be thorough - the registry is the source of truth
- Include "Last Updated" date at top of file
- Consider adding a section on how to add new agents
