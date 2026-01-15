# Ensemble Agent Swarm - Complete Work Queue

**Generated**: 2026-01-15
**Purpose**: Comprehensive inventory of all pending projects with agent swarm prompts

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Documentation Reorganization Plan](#documentation-reorganization-plan)
3. [Incomplete Projects Inventory](#incomplete-projects-inventory)
4. [Agent Swarm Prompts](#agent-swarm-prompts)
5. [Priority Order](#priority-order)

---

## Executive Summary

### Current State Analysis
- **Total Documentation Files**: 150+ markdown files across repository
- **Active Projects with Incomplete Tasks**: 10 projects
- **Total Incomplete Tasks Tracked**: 68 tasks across 45 project files
- **Critical Implementation Gaps**: 3 (Token tracking, Git integration, Request cleanup)

### Project Categories
| Category | Count | Status |
|----------|-------|--------|
| Core Infrastructure | 3 | Partial |
| UI Improvements | 4 | Partial |
| GitHub Bots Suite | 5 milestones | Only M1 complete |
| TMUX Dashboard | 2 milestones | Only M1 complete |
| Agent Enhancements | 5 | Various states |
| Testing/Quality | 2 | Pending |

---

## Documentation Reorganization Plan

### Proposed Structure
```
ensemble/
├── docs/
│   ├── system/              # Core system documentation
│   │   ├── AGENT_REGISTRY.md
│   │   ├── AGENT_HIERARCHY.md
│   │   ├── DIRECTORY_STRUCTURE.md
│   │   └── common_instructions.md
│   │
│   ├── architecture/        # Architecture documents
│   │   ├── runtime_architecture.md
│   │   ├── ui_architecture.md
│   │   └── cli_architecture.md
│   │
│   ├── features/           # Feature-specific docs (subdirs per feature)
│   │   ├── github-bots/
│   │   ├── tmux-dashboard/
│   │   ├── cost-tracking/
│   │   ├── achievements/
│   │   └── whimsical-names/
│   │
│   ├── research/           # Analysis and investigation outputs
│   │   ├── cost_optimization_analysis.md
│   │   ├── agent_creation_analysis.md
│   │   └── diagnostic_reports/
│   │
│   └── archive/            # Historical/superseded docs
│       └── [existing archive]
│
├── output/                  # ACTIVE swarm output (current work)
│   └── [project folders]
│
└── output-archive/          # Completed/superseded output
```

### Files to Relocate
| Current Location | New Location | Reason |
|-----------------|--------------|--------|
| `src/field/ensemble_ui/output/*.md` (non-project) | `docs/research/` | Analysis docs |
| `docs/current/COST_OPTIMIZATION_ANALYSIS.md` | `docs/research/` | Research output |
| `docs/current/DIAGNOSTIC_REPORT.md` | `docs/research/` | Research output |
| Feature subdirs in output/ | `docs/features/[feature]/` | Completed features |

---

## Incomplete Projects Inventory

### Category 1: CRITICAL - Core Implementation Gaps

#### 1.1 Token Tracking System
**Status**: NOT IMPLEMENTED
**Priority**: HIGH
**Location**: `docs/current/TOKEN_TRACKING_IMPLEMENTATION_PLAN.md`
**Issue**: Token extraction from Anthropic API responses not implemented
**Impact**: Cannot track actual API costs accurately

#### 1.2 Request Cleanup System
**Status**: INCOMPLETE
**Priority**: HIGH
**Location**: `docs/current/V1_CLEANUP_ISSUES.md:79-92`
**Issues**:
- `clear_request()` method incomplete
- Request filtering not implemented
- Activity cleanup causing memory growth

#### 1.3 Git Integration
**Status**: NOT IMPLEMENTED
**Priority**: HIGH
**Location**: `docs/current/DIAGNOSTIC_REPORT.md:73`
**Required**: Frequent coherent commits, branch-based development

---

### Category 2: GitHub Bots Suite (Milestones 2-6)

**Foundation Complete**: Milestone 1 done
**Pending Milestones**:

#### 2.1 Sync Bot (Milestone 2)
- Fetch/pull operations from remote
- Rebase operations with conflict handling
- Stash management
- Conflict detection and reporting

#### 2.2 Documentation Bot (Milestone 3)
- Diff analysis engine
- Change type detection (feat, fix, refactor, etc.)
- Conventional Commits message generator
- Issue/ticket reference extraction

#### 2.3 Commit Bot (Milestone 4)
- Staging operations
- Commit execution with validation
- GPG signing support
- Pre-commit hook handling

#### 2.4 Push Bot (Milestone 5)
- Push operations with scheduling
- Retry logic with exponential backoff
- Multi-remote support
- Tag pushing support

#### 2.5 Integration & Polish (Milestone 6)
- Bot coordination/orchestration
- End-to-end integration tests
- Docker deployment option

---

### Category 3: TMUX Dashboard (Milestones 2-3)

**Foundation Complete**: Milestone 1 done

#### 3.1 Task Watcher Script (Milestone 2)
- `scripts/monitoring/task_watcher.py`
- Parse project tracking JSON files
- Display tasks by status with icons
- Auto-refresh capability

#### 3.2 Full Integration & Polish (Milestone 3)
- Configuration options for all paths
- User documentation
- Error handling for dependencies

---

### Category 4: UI Improvements

#### 4.1 Achievements Integration - Phase 2
**Status**: Phase 1 complete, Phase 2 pending
**Location**: `output/achievements-integration/requirements_phase2.md`
**Pending**:
- Toast notifications for achievements
- Header badge/counter display
- Achievement animation effects

#### 4.2 UI Testing Suite
**Status**: Deferred
**Location**: `output/ui_improvements_2025/implementation_status.md`
**Pending**:
- Unit tests for StatusSummaryBar
- Integration tests for project grouping
- E2E tests for agent hierarchy

---

### Category 5: Stalled In-Progress Projects

#### 5.1 Local Weather Display Widget
**Project ID**: bb528d28
**Status**: Stalled since 2026-01-11
**Issue**: Dev Manager created planning docs but no implementation

#### 5.2 Ensemble UI Enhancements
**Project ID**: 0114ab16
**Status**: Architecture document mismatch
**Features**: Agent invocation descriptions, hide completed toggles

#### 5.3 Agent Hierarchy Organization
**Project ID**: 4af1c241
**Status**: Dev Manager started, no completion recorded
**Features**: Task-based hierarchy, brief activity titles

---

### Category 6: Unstarted Todo Tasks

#### 6.1 Agent Tracking Metrics Feature
**Project ID**: 84dd6401
**Scope**: Database schema, API endpoints, frontend UI

#### 6.2 Agent Cost Tracking Enhancement - Frontend
**Project ID**: 5f5892f3
**Scope**: Update AgentSummaryPane with cost/duration/model metrics

#### 6.3 Agent Cost Tracking Enhancement - Backend
**Project ID**: 66af6b69
**Tasks**:
- CostCalculator module
- ActivityTracker data structures
- AgentRuntime metric tracking

#### 6.4 Agent Completion Visibility
**Project ID**: d863e0cc
**Tasks**:
- Backend data enhancement
- Frontend UI updates
- Testing and polish

---

## Agent Swarm Prompts

### Instructions for Use
Feed these prompts to the Executive Director one at a time. Each prompt is self-contained with context and acceptance criteria.

---

### PROMPT 1: Token Tracking Implementation (CRITICAL)

```
Implement token tracking for all API calls in the ensemble agent system.

CONTEXT:
- The system currently passes tokens_used=None to the activity tracker
- We need to extract token usage from Anthropic API responses
- Token data should be stored and displayed in the UI

REQUIREMENTS:
1. Modify src/runtime/agents/runtime.py to extract token counts from API responses
2. Update ActivityTracker to store input_tokens, output_tokens, total_tokens
3. Add token aggregation to cost calculation
4. Expose token metrics through existing API endpoints

ACCEPTANCE CRITERIA:
- Every API call records actual token usage
- Token counts visible in agent state API
- Cost calculations use real token data
- Tests verify token extraction works

FILES TO MODIFY:
- src/runtime/agents/runtime.py
- src/runtime/agents/activity_tracker.py
- src/field/ensemble_ui/backend/main.py (if needed for API)

DO NOT modify the UI - backend only.
```

---

### PROMPT 2: Request Cleanup System (CRITICAL)

```
Fix the incomplete request cleanup system causing memory growth issues.

CONTEXT:
- The clear_request() method in ActivityTracker is incomplete
- Request filtering is not implemented
- Activities accumulate without cleanup, causing memory issues
- See: docs/current/V1_CLEANUP_ISSUES.md lines 79-92

REQUIREMENTS:
1. Complete the clear_request() implementation
2. Implement request-based activity filtering
3. Add cleanup mechanism for old activities (configurable retention)
4. Ensure no data loss for active requests

ACCEPTANCE CRITERIA:
- clear_request() fully removes request data
- Activities can be filtered by request_id
- Old activities are cleaned up automatically
- Memory usage remains stable over long sessions
- Existing functionality unaffected

FILES TO MODIFY:
- src/runtime/agents/activity_tracker.py
- Related test files

TDD APPROACH: Write failing tests first, then implement.
```

---

### PROMPT 3: GitHub Sync Bot (Milestone 2)

```
Implement the Sync Bot for the GitHub Bots suite (Milestone 2 of 6).

CONTEXT:
- Foundation (Milestone 1) is complete in src/field/ensemble_ui/output/github-bots/
- Base classes and configuration system exist
- See: output/github-bots/milestone_plan.md for full requirements

REQUIREMENTS:
1. Implement fetch/pull operations from remote
2. Add rebase operations with conflict handling
3. Implement stash management (save, restore, list)
4. Add conflict detection and clear error reporting
5. Support multiple remotes

ACCEPTANCE CRITERIA:
- Sync Bot successfully rebases a branch with upstream changes
- Uncommitted changes are safely stashed before sync
- Conflicts are detected and reported clearly
- Stashed changes are restored after successful sync
- Operations complete within 30 seconds for typical repos

FILES TO CREATE/MODIFY:
- src/field/ensemble_ui/output/github-bots/sync_bot.py
- tests/github_bots/test_sync_bot.py

TDD APPROACH: Write failing tests first for each capability.
```

---

### PROMPT 4: GitHub Documentation Bot (Milestone 3)

```
Implement the Documentation Bot for intelligent commit message generation.

CONTEXT:
- Part of GitHub Bots suite (Milestone 3 of 6)
- Foundation complete, Sync Bot should be complete first
- See: output/github-bots/milestone_plan.md

REQUIREMENTS:
1. Build diff analysis engine to parse staged changes
2. Detect change types (feat, fix, refactor, docs, test, chore)
3. Auto-detect scope from modified file paths
4. Generate Conventional Commits format messages
5. Extract issue/ticket references from branch names
6. Support custom templates

ACCEPTANCE CRITERIA:
- Generates valid Conventional Commits format
- Change types correctly identified from diff content
- Scope auto-detected from file paths (e.g., "backend" from backend/ files)
- Issue refs extracted (e.g., "PROJ-123" from branch name)
- Subject lines under 50 characters
- Generation completes within 5 seconds

FILES TO CREATE:
- src/field/ensemble_ui/output/github-bots/doc_bot.py
- tests/github_bots/test_doc_bot.py
```

---

### PROMPT 5: GitHub Commit Bot (Milestone 4)

```
Implement the Commit Bot for automated commits with validation.

CONTEXT:
- Part of GitHub Bots suite (Milestone 4 of 6)
- Requires Documentation Bot for message generation
- See: output/github-bots/milestone_plan.md

REQUIREMENTS:
1. Staging operations (all, specific files, patterns)
2. Commit execution with proper author information
3. Message validation against configured rules
4. GPG signing support (optional, configurable)
5. Pre-commit and commit-msg hook handling
6. Rollback capability for failed commits
7. Amend mode support

ACCEPTANCE CRITERIA:
- Creates commits with validated messages
- Respects pre-commit hooks
- GPG signing works when configured
- Failed commits can be rolled back
- Integrates with Documentation Bot for message generation

FILES TO CREATE:
- src/field/ensemble_ui/output/github-bots/commit_bot.py
- tests/github_bots/test_commit_bot.py
```

---

### PROMPT 6: GitHub Push Bot (Milestone 5)

```
Implement the Push Bot for regular pushing to GitHub.

CONTEXT:
- Part of GitHub Bots suite (Milestone 5 of 6)
- Requires Commit Bot for new commit signals
- See: output/github-bots/milestone_plan.md

REQUIREMENTS:
1. Push operations to configured remote
2. Scheduling system (interval-based triggers)
3. Multiple push strategies (immediate, batch, manual)
4. Retry logic with exponential backoff
5. Force push with safety checks (protected branch awareness)
6. Multi-remote push support
7. Tag pushing support

ACCEPTANCE CRITERIA:
- Pushes commits to remote on schedule
- Failed pushes retried with backoff (max 3 retries)
- Force push requires safety confirmation
- Push queue maintained for offline recovery
- Latency under 5 minutes from commit to GitHub

FILES TO CREATE:
- src/field/ensemble_ui/output/github-bots/push_bot.py
- tests/github_bots/test_push_bot.py
```

---

### PROMPT 7: GitHub Bots Integration (Milestone 6)

```
Complete the GitHub Bots suite with integration and polish.

CONTEXT:
- Final milestone (6 of 6) for GitHub Bots
- All individual bots should be complete
- See: output/github-bots/milestone_plan.md

REQUIREMENTS:
1. Bot coordination/orchestration system
2. End-to-end integration tests for full workflow
3. Comprehensive documentation (README, examples)
4. Installation scripts (pip install support)
5. GitHub Actions workflow definitions
6. Docker deployment option (Dockerfile)
7. Performance optimization pass

ACCEPTANCE CRITERIA:
- All bots work together seamlessly
- E2E tests pass for: stash -> sync -> commit -> push workflow
- Unit test coverage >80%
- Documentation complete with examples
- Docker container runs successfully
- pip install works

FILES TO CREATE:
- src/field/ensemble_ui/output/github-bots/orchestrator.py
- tests/github_bots/test_integration.py
- README.md in github-bots directory
- Dockerfile
- setup.py or pyproject.toml
```

---

### PROMPT 8: TMUX Task Watcher (Milestone 2)

```
Create the task watcher script for TMUX monitoring dashboard.

CONTEXT:
- Milestone 1 (basic layout) is complete
- Scripts exist in scripts/monitoring/
- See: output/tmux_monitoring_dashboard/milestones.md

REQUIREMENTS:
1. Create scripts/monitoring/task_watcher.py
2. Parse ~/.ensemble/projects/{project_id}/project.json files
3. Display tasks grouped by status with visual indicators:
   - Completed: checkmark
   - In-progress: spinner
   - Pending: clock
4. Show summary counts (e.g., "3 done | 2 active | 5 pending")
5. Auto-refresh every 1-2 seconds (configurable via arg)
6. Handle missing/empty project files gracefully
7. Works with Python 3.8+

ACCEPTANCE CRITERIA:
- Script runs standalone with: python task_watcher.py [project_id]
- Output is clean terminal display, suitable for tmux pane
- Graceful degradation when no project data
- CPU usage minimal during refresh loop
- Integrates cleanly with start_monitor.sh

FILES TO CREATE:
- scripts/monitoring/task_watcher.py
- Update scripts/monitoring/start_monitor.sh to use task_watcher.py
```

---

### PROMPT 9: TMUX Dashboard Polish (Milestone 3)

```
Complete TMUX monitoring dashboard with full integration.

CONTEXT:
- Milestones 1-2 should be complete
- See: output/tmux_monitoring_dashboard/milestones.md

REQUIREMENTS:
1. Update start_monitor.sh with full configuration support:
   - SESSION_NAME environment variable
   - OUTPUT_DIR environment variable
   - LOG_FILE environment variable
   - PROJECT_ID environment variable
2. Enhanced CLI integration for Pane 1 (ready to spawn agents)
3. Error handling for missing dependencies (tmux, vim, python)
4. User documentation in QUICKSTART.md or dedicated README

ACCEPTANCE CRITERIA:
- All configuration options work correctly
- Documentation covers installation, usage, navigation
- Error messages guide user to install missing deps
- All four panes work together seamlessly
- Default values sensible for typical usage

FILES TO MODIFY:
- scripts/monitoring/start_monitor.sh
- QUICKSTART.md (add monitoring section)
```

---

### PROMPT 10: Achievements Phase 2

```
Complete Achievements integration with toast notifications and badges.

CONTEXT:
- Phase 1 complete (AchievementsDashboard component exists)
- See: output/achievements-integration/requirements_phase2.md
- Need toast notifications and header badge

REQUIREMENTS:
1. Implement toast notification system for achievements
   - Appears when achievement unlocked
   - Shows achievement icon and name
   - Auto-dismisses after 5 seconds
2. Add header badge/counter showing unlocked achievement count
3. Achievement unlock animation effects
4. Sound effect option (configurable, default off)

ACCEPTANCE CRITERIA:
- Toast appears when new achievement unlocked
- Badge in header shows total unlocked count
- Animations are smooth, not jarring
- Works with existing dark theme
- No console errors

FILES TO MODIFY:
- src/field/ensemble_ui/frontend/src/App.jsx (header badge)
- Create: src/field/ensemble_ui/frontend/src/components/AchievementToast.jsx
- Update: src/field/ensemble_ui/frontend/src/App.scss (toast styles)
```

---

### PROMPT 11: UI Test Suite

```
Write comprehensive tests for UI components.

CONTEXT:
- UI Improvements 2025 complete but tests deferred
- Using Vitest + React Testing Library
- See: output/ui_improvements_2025/test_tasks_m1_m2.md

REQUIREMENTS:
1. Unit tests for StatusSummaryBar component
2. Unit tests for AgentHierarchyTree project grouping
3. Integration tests for project expand/collapse
4. Test API service mocking patterns
5. Achieve 80% coverage for new components

ACCEPTANCE CRITERIA:
- All tests pass with npm run test
- Coverage report shows >80% for target files
- Tests are readable and maintainable
- Mock patterns documented for reuse
- No flaky tests

FILES TO CREATE:
- src/field/ensemble_ui/frontend/src/components/StatusSummaryBar.test.jsx
- src/field/ensemble_ui/frontend/src/components/AgentHierarchyTree.test.jsx
```

---

### PROMPT 12: Agent Cost Tracking Backend

```
Implement backend cost tracking enhancements.

CONTEXT:
- Project ID: 66af6b69
- Three related tasks all in "todo" status
- Need cost calculator, activity data structures, runtime tracking

REQUIREMENTS:
1. Create CostCalculator module
   - Calculate costs based on model and tokens
   - Support different pricing tiers
   - Aggregate costs by agent, request, project
2. Update ActivityTracker data structures
   - Add cost fields to activity records
   - Support cost aggregation queries
3. Update AgentRuntime metric tracking
   - Track per-iteration costs
   - Track total agent costs
   - Expose via API

ACCEPTANCE CRITERIA:
- Costs calculated accurately per API pricing
- Cost data available in activity tracker
- API endpoint returns cost summaries
- Historical cost data queryable
- Tests verify calculations

FILES TO CREATE/MODIFY:
- src/runtime/agents/cost_calculator.py (new)
- src/runtime/agents/activity_tracker.py (modify)
- src/runtime/agents/runtime.py (modify)
- tests/test_cost_calculator.py (new)
```

---

### PROMPT 13: Agent Cost Tracking Frontend

```
Update frontend to display agent cost metrics.

CONTEXT:
- Project ID: 5f5892f3
- Backend cost tracking should be complete first
- Update AgentSummaryPane with cost display

REQUIREMENTS:
1. Display cost per agent in summary pane
2. Show duration and model tier for each agent
3. Add cost breakdown in agent details view
4. Show project-level cost totals
5. Format costs as currency ($0.00)

ACCEPTANCE CRITERIA:
- Cost visible in agent summary cards
- Duration shows as human-readable time
- Model tier badge visible
- No layout breaks on long numbers
- Works with existing dark theme

FILES TO MODIFY:
- src/field/ensemble_ui/frontend/src/components/AgentSummaryPane.jsx (or equivalent)
- May need to update API service for new endpoints
```

---

### PROMPT 14: Agent Completion Visibility

```
Enhance agent completion visibility across UI.

CONTEXT:
- Project ID: d863e0cc
- Three milestones: backend data, frontend UI, testing

REQUIREMENTS:
Backend:
1. Add completion timestamps to agent state
2. Add duration calculation (started -> completed)
3. Add final status summary fields

Frontend:
1. Visual indicator for completed agents (green checkmark)
2. Show completion time in agent details
3. Filter option: "Show completed" toggle
4. Sort by completion time option

Testing:
1. Unit tests for completion logic
2. UI tests for visibility features

ACCEPTANCE CRITERIA:
- Completed agents clearly distinguishable
- Completion time accurate and formatted nicely
- Filter works correctly
- Sort works correctly
- Tests pass

FILES TO MODIFY:
- Backend: src/field/ensemble_ui/backend/main.py
- Frontend: relevant components
- Tests: new test files
```

---

## Priority Order

### Immediate (Do First)
1. **PROMPT 1**: Token Tracking - Critical for cost accuracy
2. **PROMPT 2**: Request Cleanup - Critical for stability

### High Priority (Core Features)
3. **PROMPT 3-7**: GitHub Bots Suite (in order)
4. **PROMPT 8-9**: TMUX Dashboard completion

### Medium Priority (Enhancements)
5. **PROMPT 12-13**: Cost Tracking (backend then frontend)
6. **PROMPT 14**: Agent Completion Visibility
7. **PROMPT 10**: Achievements Phase 2

### Lower Priority (Polish)
8. **PROMPT 11**: UI Test Suite

---

## Usage Instructions

1. Copy one prompt at a time to the agent swarm
2. Wait for completion before starting next (unless independent)
3. GitHub Bots prompts 3-7 must be done in order
4. TMUX prompts 8-9 must be done in order
5. Cost tracking: do backend (12) before frontend (13)

---

## Notes

- All prompts are designed to be self-contained
- Each includes context, requirements, and acceptance criteria
- TDD approach recommended where noted
- Test existing functionality before modifying
