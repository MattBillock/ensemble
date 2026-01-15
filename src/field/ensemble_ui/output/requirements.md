# Project Cleanup and Documentation Refinement Requirements

## Vision
Comprehensive cleanup of generated code, documentation, and temporary artifacts throughout the ensemble project. This includes reorganizing files, removing unnecessary artifacts, and refining documentation for accuracy.

## Objectives

### 1. Remove Temporary and Build Artifacts
- Remove all `__pycache__` directories throughout the project
- Remove all `.pyc` compiled Python files
- Clean up log files (keeping logs/ directory structure but clearing old logs)
- Remove any `.tmp`, `.bak` backup files not needed

### 2. Clean Up Output Directory (`/src/field/ensemble_ui/output/`)
The output directory has accumulated 90+ files from various project runs. Organize as follows:

**Files to Archive** (move to `output/archive/`):
- Older milestone plans and task breakdowns (keep only most recent versions)
- Completed project documentation from past work
- One-off analysis files that are no longer current

**Files to Keep in Root**:
- `requirements.md` - Current requirements (this file)
- `architecture.md` - Current architecture document
- `milestone_plan.md` - Current milestone plan
- `README.md` - Output directory readme
- `.gitignore` - Git ignore rules

**Directories to Review**:
- Consolidate related feature directories
- Remove empty directories

### 3. Clean Up Deprecated Scripts
The `/scripts/deprecated/` directory contains old pipeline scripts that are no longer used:
- `add_fail_fast_rules.py`
- `analyze_milestone.py`
- `build_milestone2.py`
- `cleanup_drum_corps.sh`
- `cli_pipeline.py`
- `complete_milestone2_frontend.py`
- `complete_ui_pipeline.py`
- `consolidate_agents.sh`
- `continue_ensemble.py`
- `milestone_0_pipeline.py`

**Decision**: These should be deleted as they are in a deprecated folder and the functionality has been superseded.

### 4. Clean Up Log Files
Log files found:
- `/backend.log` (15MB+) - Should be rotated/cleared
- `/logs/backend.log` - Duplicate
- `/logs/milestone_0_pipeline_run.log` - Old
- `/logs/cli_pipeline_run.log` - Old
- `/logs/model_selector_pipeline.log` - Old
- `/logs/ui_pipeline_run.log` - Old
- `/src/frontend.log` - Misplaced
- `/src/field/ensemble_ui/backend/backend.log` - Should be in logs/

**Decision**: Clear all old logs, ensure logging goes to `/logs/` directory only.

### 5. Clean Up Empty/Unused Directories
- `/performances/` - Empty directory
- `/rehearsals/` - Empty directory
- `/problems/` - Contains old problem definitions, may need archiving

### 6. Documentation Refinement

**README.md** (root): Current and accurate - no changes needed.

**QUICKSTART.md**: Verify commands are current and accurate.

**CLAUDE.md**: Verify project conventions are current.

**docs/DIRECTORY_STRUCTURE.md**: Comprehensive and accurate - no changes needed.

**Verify and update if needed**:
- `/docs/common_instructions.md`
- `/docs/project_milestones.md`
- `/docs/FILE_ORGANIZATION_PLAN.md`

**Archive old documentation** in `/docs/archive/`:
- Already properly archived - no action needed

### 7. Verify Agent Definitions
Ensure all agent markdown files in:
- `/leadership/`
- `/coordinators/`
- `/developers/`
- `/testers/`
- `/support/`
- `/designers/`

Are current and match the hierarchy described in README.md.

## Out of Scope
- No changes to runtime Python code in `/src/runtime/`
- No changes to UI code in `/frontend/` or `/backend/`
- No changes to test files in `/tests/`
- No new feature development

## Success Criteria
1. All `__pycache__` directories removed
2. Output directory organized with clear archive structure
3. Deprecated scripts removed
4. Log files cleaned up and consolidated to `/logs/`
5. Documentation verified for accuracy
6. No broken references or orphaned files

## Execution Notes
- This is a file organization/cleanup task, not a code development task
- Use shell commands for bulk operations (rm, mv, find)
- Create archive directories before moving files
- Commit changes in logical batches

## Assumptions Made
- Old log files can be safely deleted (not needed for audit)
- Deprecated scripts can be permanently removed (functionality superseded)
- Files older than 7 days in output/ can be archived
- Empty directories with no clear purpose can be removed
