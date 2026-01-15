# Prompt: Clean Up Agent Definition Files

## Context

Agent definition files contain:
1. Incorrect model preferences (don't match registry recommendations)
2. Old drum corps terminology that should be replaced
3. "Supervised By" fields referencing non-existent roles
4. Spawn permissions for non-existent agents

## Priority
MEDIUM - Documentation/configuration issues

## Files to Modify

### Model Fixes (Priority)
1. `leadership/development_manager.md` - Change model from haiku to sonnet
2. `leadership/system_architect.md` - Change model from haiku to opus
3. `leadership/tdd_coordinator.md` - Change model from haiku to sonnet

### Terminology Fixes
4. `developers/backend_lead.md` - Remove "Synth Tech" reference
5. `developers/frontend_lead.md` - Remove "Trumpet", "Dance Tech" references
6. `developers/backend_developer.md` - Fix "Supervised By" field
7. `developers/frontend_developer.md` - Fix "Supervised By" field
8. `testers/unit_test_lead.md` - Remove "Snare", "Percussion Coordinator" references
9. `testers/unit_test_writer.md` - Fix "Supervised By" field
10. `testers/integration_test_lead.md` - Remove "Percussion Coordinator" reference
11. `testers/integration_test_writer.md` - Fix "Supervised By" field
12. `designers/style_developer.md` - Fix "Supervised By" field

### Spawn Permission Fixes
13. `leadership/tdd_coordinator.md` - Remove "support/visual_tech" from spawn list

## Requirements

### Part 1: Fix Model Preferences

**development_manager.md:**
```yaml
# Find and change:
model_preference: haiku
# To:
model_preference: sonnet
```

**system_architect.md:**
```yaml
# Find and change:
model_preference: haiku
# To:
model_preference: opus
```

**tdd_coordinator.md:**
```yaml
# Find and change:
model_preference: haiku
# To:
model_preference: sonnet
```

### Part 2: Fix Supervised By Fields

The "Supervised By" field should reference actual agents in the hierarchy:

**Correct mappings:**
- Backend Lead -> "Development Manager" or "TDD Coordinator"
- Frontend Lead -> "Development Manager" or "TDD Coordinator"
- Backend Developer -> "Backend Lead"
- Frontend Developer -> "Frontend Lead"
- Unit Test Lead -> "TDD Coordinator"
- Unit Test Writer -> "Unit Test Lead"
- Integration Test Lead -> "TDD Coordinator"
- Integration Test Writer -> "Integration Test Lead"
- Style Developer -> "Frontend Lead"

**Example fix (backend_lead.md):**
```yaml
# Find:
Supervised By: Brass Coordinator
# Replace with:
Supervised By: TDD Coordinator
```

### Part 3: Remove Drum Corps Terminology

Search each file for these terms and remove or replace:

| Find | Replace With |
|------|--------------|
| Snare | Unit Test Writer |
| Trumpet | Frontend Developer |
| Synth | Backend Developer |
| Percussion Coordinator | Test Coordinator |
| Brass Coordinator | Backend/Frontend Coordinator |
| Visual Tech | Style Developer |
| Dance Tech | (remove or use Frontend Developer) |
| Section Techs | Developers |

**Example (unit_test_lead.md):**
```markdown
# Find text like:
"coordinate with Snare for test implementation"
# Replace with:
"coordinate with Unit Test Writer for test implementation"
```

### Part 4: Fix Spawn Permissions

**tdd_coordinator.md:**
```yaml
# Find in spawn_permissions:
- support/visual_tech
# Remove this line entirely (agent doesn't exist)
```

### Part 5: Add Missing Spawn Paths

**api_lead.md** - Verify spawn_permissions includes:
```yaml
spawn_permissions:
  - api_developer
```

**Check that api_test_writer has a spawn path:**
- Either add to API Lead's spawn permissions
- Or add to Unit Test Lead / Integration Test Lead
- Or document it as directly invocable

## Acceptance Criteria

1. Model preferences match AGENT_REGISTRY.md recommendations
2. No drum corps terminology in any agent files
3. All "Supervised By" fields reference real agents
4. No spawn permissions for non-existent agents
5. All agents have clear spawn paths documented

## Test Plan

1. Search for old terminology:
   ```bash
   grep -r "Snare\|Trumpet\|Synth\|Brass Coordinator\|Percussion" leadership/ coordinators/ developers/ testers/ designers/
   ```
   Should return no results.

2. Verify model preferences:
   ```bash
   grep "model_preference" leadership/*.md
   ```
   Compare against registry.

3. Check spawn permissions exist:
   ```bash
   grep -A 10 "spawn_permissions" leadership/tdd_coordinator.md
   ```
   Verify all listed agents exist.

## Notes

- Be careful not to change the meaning of instructions, just the terminology
- Some files may not have "Supervised By" - that's OK
- Model changes are most critical - they affect runtime behavior
- Terminology changes are for documentation clarity
