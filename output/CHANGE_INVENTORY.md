# Change Inventory - Naming Standardization
## Actionable Checklist for Milestone 2

**Generated from**: NAMING_AUDIT_REPORT.md
**Purpose**: Step-by-step checklist of all changes needed to standardize naming

---

## Phase 1: Support Agent Renames (CRITICAL - Do First)

### P0 - Critical Priority (Blocks TDD Workflow)

- [ ] **File Rename: visual_tech.md → code_refactorer.md**
  - Path: `support/visual_tech.md` → `support/code_refactorer.md`
  - Rename the file first
  - Update file header: `# Visual Tech` → `# Code Refactorer`
  
- [ ] **Update TDD Coordinator spawn path** (DO IMMEDIATELY AFTER RENAME)
  - File: `leadership/tdd_coordinator.md`
  - Line 51: `"support/visual_tech"` → `"support/code_refactorer"`
  - Line 110: `spawn_agent("support/visual_tech", ...)` → `spawn_agent("support/code_refactorer", ...)`

### P1 - High Priority (Not Currently Spawned, Safe to Rename)

- [ ] **File Rename: drill_writer.md → documentation_writer.md**
  - Path: `support/drill_writer.md` → `support/documentation_writer.md`
  - Update file header: `# Drill Writer` → `# Documentation Writer`

- [ ] **File Rename: logistics_manager.md → code_explorer.md**
  - Path: `support/logistics_manager.md` → `support/code_explorer.md`
  - Update file header: `# Logistics Manager` → `# Code Explorer`

---

## Phase 2: Agent File Content Updates (By Folder)

### support/ Folder

- [ ] **support/code_refactorer.md** (formerly visual_tech.md)
  - Line 4: `"Cleans spacing, alignment, and technique."` → `"Improves code quality, readability, and structure."`

- [ ] **support/documentation_writer.md** (formerly drill_writer.md)
  - Line 4: `"Creates comprehensive documentation... The 'drill charts' that guide future performers."` → `"Creates comprehensive documentation for the development team's work."`
  - Line 59: `"You are the Drill Writer - you create the drill charts that guide the ensemble."` → `"You are the Documentation Writer - you create documentation that guides developers."`

- [ ] **support/code_explorer.md** (formerly logistics_manager.md)
  - Line 4: `"Surveys the 'venue' before the show begins."` → `"Explores the codebase before development begins."`

### leadership/ Folder

- [ ] **leadership/development_manager.md**
  - Line 44: `"You drive the show from concept through performance"` → `"You drive development from concept through delivery"`

- [ ] **leadership/system_architect.md**
  - Line 4: `"Designs the show formations and execution strategy"` → `"Designs the system architecture and implementation strategy"`

- [ ] **leadership/tdd_coordinator.md**
  - Line 4: `"Directs and coordinates the ensemble through rehearsal. Manages tempo, attitude, and execution."` → `"Directs and coordinates the development team through implementation cycles."`
  - Lines 46-51: `"Section Techs"` → `"Specialist Agents"`
  - Line 122: `"spawns Snare"` → `"spawns Unit Test Writer"`
  - Line 129: `"spawns Snare"` → `"spawns Unit Test Writer"`

### coordinators/ Folder

- [ ] **coordinators/test_coordinator.md**
  - Line 4: `"Coordinates with Backend Captain and Frontend Captain"` → `"Coordinates with Backend Lead and Frontend Lead"`

### testers/ Folder

- [ ] **testers/unit_test_lead.md**
  - Line 4: `"Guides Snare to create comprehensive, effective tests"` → `"Guides Unit Test Writer to create comprehensive, effective tests"`
  - Line 11: `"Unit tests written by Snare"` → `"Unit tests written by Unit Test Writer"`
  - Line 44: `"You're a unit testing expert supervising Snare"` → `"You're a unit testing expert supervising Unit Test Writer"`

- [ ] **testers/integration_test_lead.md**
  - Line 4: `"Writes tests that Tenor must pass"` → `"Writes tests that Integration Test Writer must pass"`
  - Line 46: `"supervising Tenor"` → `"supervising Integration Test Writer"`
  - Line 72: `"Tenor writes integration tests"` → `"Integration Test Writer writes tests"`

- [ ] **testers/unit_test_writer.md**
  - Line 4: `"Precision test writing tech. ... Crisp, precise, catches mistakes."` → `"Precision test writing specialist. Writes failing unit tests that define requirements."`

- [ ] **testers/integration_test_writer.md**
  - Line 8: `"Supervised by Integration Test Writer Tech"` → `"Supervised by Integration Test Lead"`
  - Line 55: `"Integration Test Writer Tech"` → `"Integration Test Lead"`

### developers/ Folder

- [ ] **developers/frontend_lead.md**
  - Line 7: `"task assigned by Brass Coordinator"` → `"task assigned by Frontend Coordinator"`
  - Line 12: `"Task completion reported to Brass Coordinator"` → `"Task completion reported to Frontend Coordinator"`
  - Lines 111, 165: Additional `"Brass Coordinator"` → `"Frontend Coordinator"`
  - Line 139: `"Dance Tech: UX patterns"` → REMOVE or `"UX Specialist: UX patterns"`

- [ ] **developers/backend_lead.md**
  - Line 7: `"task assigned by Brass Coordinator"` → `"task assigned by Backend Coordinator"`
  - Line 12: `"Task completion reported to Brass Coordinator"` → `"Task completion reported to Backend Coordinator"`
  - Line 102: `"Database needs with Synth Tech"` → REMOVE or `"Database needs with Database Specialist"`
  - Lines 109, 150, 178: Additional Brass/Synth Tech references → Update appropriately

- [ ] **developers/frontend_developer.md**
  - Line 10: `"When supervised by Frontend Developer Tech"` → `"When supervised by Frontend Lead"`
  - Line 165: `"Frontend Developer Tech"` → `"Frontend Lead"`

- [ ] **developers/backend_developer.md**
  - Line 120: `"Backend Developer Tech (backend development domain expert)"` → `"Backend Lead"`

### designers/ Folder

- [ ] **designers/style_developer.md**
  - Line 8: `"Supervised by Style Developer Tech"` → `"Supervised by Frontend Lead"`
  - Line 64: `"Style Developer Tech"` → `"Frontend Lead"`

---

## Phase 3: Documentation Updates

### P2 - Medium Priority

- [ ] **AGENT_REGISTRY.md**
  - Update support/ folder agent names in registry
  - Update any hierarchy diagrams

---

## Phase 4: Verification

### Post-Change Verification Steps

- [ ] **Run grep to verify no old terms remain:**
  ```bash
  grep -rn -i "drill_writer" .
  grep -rn -i "logistics_manager" .
  grep -rn -i "visual_tech" .
  grep -rn -i "Snare" leadership/ coordinators/ developers/ testers/ designers/ support/
  grep -rn -i "Tenor" leadership/ coordinators/ developers/ testers/ designers/ support/
  grep -rn -i "Brass Coordinator" .
  ```

- [ ] **Test TDD workflow:**
  - Run a sample TDD cycle
  - Verify Code Refactorer (formerly Visual Tech) is spawned correctly
  - Verify no spawn path errors

- [ ] **Run existing tests:**
  ```bash
  pytest tests/
  ```

---

## Summary Statistics

| Category | Count |
|----------|-------|
| File renames required | 3 |
| Spawn path updates | 2 |
| Agent files to update | 14 |
| Individual text changes | ~45 |
| Documentation files to update | 1 |

**Estimated Effort**: 3-4 hours for all changes

---

## Implementation Order (Recommended)

1. **Backup all agent files** (optional but recommended)
2. **Phase 1**: Rename `visual_tech.md` AND update TDD Coordinator spawn paths TOGETHER
3. **Phase 1**: Rename `drill_writer.md` and `logistics_manager.md`
4. **Test**: Run `pytest` to verify no breakage
5. **Phase 2**: Update all agent file content in order
6. **Phase 3**: Update documentation
7. **Phase 4**: Run all verification grep commands
8. **Final Test**: Run full test suite

---

## Rollback Plan

If issues occur:
1. Git restore all changed files: `git checkout -- <file>`
2. Or restore from backup
3. Identify which specific change caused the issue
4. Fix and retry

---

*Generated as part of Milestone 1: Naming Audit & Discovery*
