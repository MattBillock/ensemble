# Project Cleanup and Documentation Refinement - Milestone Plan

## Project Overview
Comprehensive cleanup of the ensemble project including removing temporary artifacts, organizing the output directory, removing deprecated scripts, and verifying documentation.

---

## Milestone 1: Remove Temporary and Build Artifacts
**Objective**: Clean all __pycache__ directories and compiled Python files
**Duration**: Immediate (automated)

### Deliverables
- All `__pycache__` directories removed (excluding venv/)
- All `.pyc` files removed (excluding venv/)
- All `.tmp` and `.bak` files removed

### Acceptance Criteria
- No `__pycache__` directories exist in project source code
- Virtual environment remains untouched
- Project still runs correctly after cleanup

---

## Milestone 2: Clean Up Log Files
**Objective**: Consolidate and clean log files
**Duration**: Immediate (automated)

### Deliverables
- Root `/backend.log` (15MB) cleared
- Duplicate `/logs/backend.log` cleared  
- Old pipeline logs archived or removed
- Misplaced `/src/frontend.log` removed
- Misplaced `/src/field/ensemble_ui/backend/backend.log` removed

### Acceptance Criteria
- All logs consolidated to `/logs/` directory
- No log files outside designated log directory
- Log directory structure maintained

---

## Milestone 3: Remove Deprecated Scripts
**Objective**: Delete scripts in `/scripts/deprecated/`
**Duration**: Immediate (automated)

### Deliverables
- All 10 deprecated scripts removed:
  - add_fail_fast_rules.py
  - analyze_milestone.py
  - build_milestone2.py
  - cleanup_drum_corps.sh
  - cli_pipeline.py
  - complete_milestone2_frontend.py
  - complete_ui_pipeline.py
  - consolidate_agents.sh
  - continue_ensemble.py
  - milestone_0_pipeline.py

### Acceptance Criteria
- Deprecated directory is empty or removed
- No broken references to removed scripts

---

## Milestone 4: Organize Output Directory
**Objective**: Archive old files, keep only current working files
**Duration**: 10 minutes

### Deliverables
- Create `/output/archive/` directory
- Move older milestone plans, task breakdowns, and analysis files to archive
- Keep only current working files in root

### Files to Keep in Root:
- requirements.md
- architecture.md  
- milestone_plan.md
- README.md
- .gitignore

### Acceptance Criteria
- Output directory has < 20 files in root
- Archive directory contains organized historical files
- Clear separation between current and historical work

---

## Milestone 5: Clean Up Empty/Unused Directories
**Objective**: Remove empty directories, archive old content
**Duration**: 5 minutes

### Deliverables
- `/performances/` removed (empty)
- `/rehearsals/` removed (empty)
- `/problems/` archived or removed

### Acceptance Criteria
- No empty directories in project root
- Old problem definitions preserved if valuable

---

## Milestone 6: Documentation Verification
**Objective**: Verify all documentation is current and accurate
**Duration**: 15 minutes

### Deliverables
- QUICKSTART.md verified
- CLAUDE.md verified
- docs/common_instructions.md verified
- docs/project_milestones.md verified
- docs/FILE_ORGANIZATION_PLAN.md verified

### Acceptance Criteria
- All documentation matches current project state
- No broken links or outdated instructions

---

## Success Criteria (Overall)
1. ✓ All `__pycache__` directories removed (outside venv)
2. ✓ Output directory organized with clear archive structure
3. ✓ Deprecated scripts removed
4. ✓ Log files cleaned up and consolidated to `/logs/`
5. ✓ Documentation verified for accuracy
6. ✓ No broken references or orphaned files

---

## Execution Plan
This is a file organization/cleanup task executed via shell commands.
No TDD workflow required - direct file operations only.
