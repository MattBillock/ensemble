# Naming Refactor Plan - Drum Corps → Standard Developer Names

**Purpose**: Replace drum corps metaphor with intuitive, self-documenting agent names.

**Goal**: Any developer should immediately understand each agent's role without learning the metaphor.

---

## Renaming Strategy

### Hierarchy Levels:
1. **Directors** - Strategic oversight (executive_director)
2. **Managers** - Program/project management (program_coordinator)
3. **Architects** - Technical design (designer)
4. **Coordinators** - Task breakdown and orchestration (drum_major, caption_heads)
5. **Leads** - Supervise implementation (all *_tech agents)
6. **Engineers/Writers** - Do the work (brass, percussion, guard)

---

## Complete Renaming Map

### Leadership Layer

| Current | New | Rationale |
|---------|-----|-----------|
| `leadership/executive_director.md` | `leadership/executive_director.md` | **KEEP** - Already clear |
| `leadership/program_coordinator.md` | `leadership/development_manager.md` | More standard title |
| `leadership/designer.md` | `leadership/system_architect.md` | More descriptive |
| `leadership/drum_major.md` | `leadership/tdd_coordinator.md` | Describes actual role |

### Caption Heads (Task Coordinators)

| Current | New | Rationale |
|---------|-----|-----------|
| `caption_heads/backend_captain.md` | `coordinators/backend_coordinator.md` | Clearer hierarchy + role |
| `caption_heads/frontend_captain.md` | `coordinators/frontend_coordinator.md` | Clearer hierarchy + role |
| `caption_heads/test_captain.md` | `coordinators/test_coordinator.md` | Clearer hierarchy + role |

**Directory rename**: `caption_heads/` → `coordinators/`

### Brass Section (Code Writers + Supervisors)

| Current | New | Rationale |
|---------|-----|-----------|
| `brass/trumpet_tech.md` | `developers/frontend_lead.md` | Obvious role |
| `brass/trumpet.md` | `developers/frontend_developer.md` | Self-explanatory |
| `brass/baritone_tech.md` | `developers/backend_lead.md` | Obvious role |
| `brass/baritone.md` | `developers/backend_developer.md` | Self-explanatory |
| `brass/tuba_tech.md` | `developers/api_lead.md` | Obvious role |
| `brass/tuba.md` | `developers/api_developer.md` | Self-explanatory |
| `brass/horn_tech.md` | `developers/component_lead.md` | Obvious role |
| `brass/horn.md` | `developers/component_developer.md` | Self-explanatory |

**Directory rename**: `brass/` → `developers/`

### Percussion Section (Test Writers + Supervisors)

| Current | New | Rationale |
|---------|-----|-----------|
| `percussion/snare_tech.md` | `testers/unit_test_lead.md` | Obvious role |
| `percussion/snare.md` | `testers/unit_test_writer.md` | Self-explanatory |
| `percussion/cymbal_tech.md` | `testers/test_validator.md` | Describes function |
| `percussion/bass.md` | `testers/test_fixture_writer.md` | Describes function |
| `percussion/tenor_tech.md` | `testers/integration_test_lead.md` | Obvious role |
| `percussion/tenor.md` | `testers/integration_test_writer.md` | Self-explanatory |

**Directory rename**: `percussion/` → `testers/`

### Color Guard (Styling)

| Current | New | Rationale |
|---------|-----|-----------|
| `guard/flag_tech.md` | `designers/style_lead.md` | Obvious role |
| `guard/flag.md` | `designers/style_developer.md` | Self-explanatory |

**Directory rename**: `guard/` → `designers/`

---

## New Directory Structure

```
ensemble/
├── leadership/
│   ├── executive_director.md (unchanged)
│   ├── development_manager.md (was program_coordinator)
│   ├── system_architect.md (was designer)
│   └── tdd_coordinator.md (was drum_major)
├── coordinators/ (was caption_heads)
│   ├── backend_coordinator.md
│   ├── frontend_coordinator.md
│   └── test_coordinator.md
├── developers/ (was brass)
│   ├── frontend_lead.md (was trumpet_tech)
│   ├── frontend_developer.md (was trumpet)
│   ├── backend_lead.md (was baritone_tech)
│   ├── backend_developer.md (was baritone)
│   ├── api_lead.md (was tuba_tech)
│   ├── api_developer.md (was tuba)
│   ├── component_lead.md (was horn_tech)
│   └── component_developer.md (was horn)
├── testers/ (was percussion)
│   ├── unit_test_lead.md (was snare_tech)
│   ├── unit_test_writer.md (was snare)
│   ├── test_validator.md (was cymbal_tech)
│   ├── test_fixture_writer.md (was bass)
│   ├── integration_test_lead.md (was tenor_tech)
│   └── integration_test_writer.md (was tenor)
└── designers/ (was guard)
    ├── style_lead.md (was flag_tech)
    └── style_developer.md (was flag)
```

---

## Path Updates Required

### In Agent Instructions

Every agent that spawns other agents needs path updates:

**Executive Director** spawns:
- ❌ `leadership/program_coordinator`
- ✅ `leadership/development_manager`

**Development Manager** (was Program Coordinator) spawns:
- ❌ `leadership/designer`
- ✅ `leadership/system_architect`
- ❌ `caption_heads/backend_captain`
- ✅ `coordinators/backend_coordinator`
- ❌ `caption_heads/frontend_captain`
- ✅ `coordinators/frontend_coordinator`
- ❌ `caption_heads/test_captain`
- ✅ `coordinators/test_coordinator`
- ❌ `leadership/drum_major`
- ✅ `leadership/tdd_coordinator`

**TDD Coordinator** (was Drum Major) spawns:
- ❌ `percussion/snare_tech`
- ✅ `testers/unit_test_lead`
- ❌ `brass/trumpet_tech`
- ✅ `developers/frontend_lead`
- ❌ `brass/baritone_tech`
- ✅ `developers/backend_lead`
- ❌ `brass/tuba_tech`
- ✅ `developers/api_lead`

**All *_lead agents** spawn their corresponding writers:
- ❌ `brass/trumpet`
- ✅ `developers/frontend_developer`
- ❌ `brass/tuba`
- ✅ `developers/api_developer`
- ❌ `percussion/snare`
- ✅ `testers/unit_test_writer`
- etc.

### In Python Code

**Files to update**:
- `src/runtime/agents/definition.py` - No changes (loads from paths)
- `build_milestone2.py` - Update paths
- `complete_milestone2_frontend.py` - Update paths
- `test_rogue_detection.py` - Update paths
- Any scripts that reference agent paths

### In Documentation

- `AGENT_REGISTRY.md` - Complete rewrite with new paths
- `COMPREHENSIVE_REVIEW.md` - Add note about renaming
- Any other docs referencing agent names

---

## Migration Script Tasks

1. **Rename directories**:
   - `mv caption_heads coordinators`
   - `mv brass developers`
   - `mv percussion testers`
   - `mv guard designers`

2. **Rename files** (25 files):
   - All files in the mapping above

3. **Update file contents** (all .md files):
   - Update ## Purpose section
   - Update spawn_agent paths in ## Instructions
   - Update Available Tools section

4. **Update Python scripts** (4 files):
   - build_milestone2.py
   - complete_milestone2_frontend.py
   - test_rogue_detection.py
   - update_agent_permissions.py
   - add_fail_fast_rules.py

5. **Update documentation**:
   - AGENT_REGISTRY.md
   - README (if exists)

6. **Run tests**:
   - test_rogue_detection.py should still pass
   - Verify agent loading works

---

## Backward Compatibility

**NOT MAINTAINED** - Clean break, no aliases.

Rationale:
- System is young, not in production
- Clean slate is better than complexity
- Old paths will fail fast and be obvious

---

## Benefits of New Names

### Before (Drum Corps):
```python
spawn_agent("brass/trumpet_tech", {...})  # What does this do?
spawn_agent("percussion/snare", {...})     # Test writer? Sound effect?
spawn_agent("guard/flag", {...})           # What's guard?
```

### After (Standard Names):
```python
spawn_agent("developers/frontend_lead", {...})     # Obvious!
spawn_agent("testers/unit_test_writer", {...})     # Crystal clear!
spawn_agent("designers/style_developer", {...})    # Self-documenting!
```

### Learning Curve:
- **Before**: Must learn entire drum corps metaphor
- **After**: Immediately obvious from name

### Onboarding:
- **Before**: "Trumpet is frontend, Tuba is API, Snare is tests..."
- **After**: Names explain themselves

---

## Risks & Mitigations

### Risk: Breaking existing agent spawns
**Mitigation**: Update all spawn paths in single atomic commit

### Risk: Missing path references
**Mitigation**: Grep for all old names, ensure none remain

### Risk: State files reference old paths
**Mitigation**: Delete old state files, start fresh

---

## Execution Order

1. Create migration script (`rename_agents.py`)
2. Run script to rename all files and directories
3. Update all agent instruction content (spawn paths)
4. Update Python scripts
5. Update AGENT_REGISTRY.md
6. Delete old state files (milestone2_exec_state.json)
7. Run test_rogue_detection.py
8. Commit everything
9. Test with fresh Milestone 2 build

---

## Success Criteria

✅ All files renamed
✅ All directories renamed
✅ All spawn_agent paths updated
✅ All Python scripts work
✅ test_rogue_detection.py passes
✅ No references to old drum corps names remain
✅ AGENT_REGISTRY.md reflects new structure
✅ Fresh agent spawn works with new paths

---

**Total Files to Update**: ~40 files
**Total Time Estimate**: 30-45 minutes with automated script
**Breaking Changes**: YES - intentional clean break

**Next Step**: Create and run `rename_agents.py`
