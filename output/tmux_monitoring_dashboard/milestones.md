# Tmux Monitoring Dashboard - Milestone Plan

## Project Overview
Create a tmux-based 2x2 monitoring dashboard for the ensemble agent swarm providing real-time visibility into agent activity, output files, and task progress.

## Implementation Status: PARTIAL
**Last Updated**: 2026-01-15
**Implemented by**: Claude Opus 4.5 (manual implementation)

Milestone 1 complete. Milestones 2-3 pending.

## Milestone Breakdown

### Milestone 1: Basic Tmux Layout (MVP) - ✅ COMPLETE
**Objective:** Create the foundational tmux session management scripts with 2x2 layout.

**Deliverables:**
- `scripts/monitoring/start_monitor.sh` - Main script to launch tmux dashboard
- `scripts/monitoring/stop_monitor.sh` - Script to cleanly stop the dashboard
- Basic 2x2 layout with placeholder functionality

**Acceptance Criteria:**
- [x] Single command launches tmux session with 2x2 grid
- [x] Session named "ensemble-monitor" (configurable)
- [x] Pane 1 (top-left): Shell ready for CLI commands
- [x] Pane 2 (top-right): `tail -f` on backend.log
- [x] Pane 3 (bottom-left): vim opened to output directory with netrw
- [x] Pane 4 (bottom-right): Simple watch on project file (placeholder)
- [x] stop_monitor.sh cleanly kills session
- [x] Works on macOS and Linux
- [x] Works with bash and zsh

**Dependencies:** None

**Estimated Effort:** Small

---

### Milestone 2: Task Watcher Script - ⏳ PENDING
**Objective:** Create a Python script that monitors and displays task status from the project tracking system.

**Deliverables:**
- `scripts/monitoring/task_watcher.py` - Task monitoring and display script
- Integration with Pane 4 of the tmux dashboard

**Acceptance Criteria:**
- [ ] Parses `~/.ensemble/projects/{project_id}/project.json`
- [ ] Displays tasks grouped by status (completed ✅, in-progress 🔄, pending ⏳)
- [ ] Shows summary counts (e.g., "3 done | 2 active | 5 pending")
- [ ] Auto-refreshes every 1-2 seconds (configurable)
- [ ] Short task descriptions (<10 words)
- [ ] Handles missing/empty project file gracefully
- [ ] Works with Python 3.8+

**Dependencies:** Milestone 1 (basic layout to integrate into)

**Estimated Effort:** Small-Medium

---

### Milestone 3: Full Integration & Polish - ⏳ PENDING
**Objective:** Connect all components, add configuration options, and create documentation.

**Deliverables:**
- Updated `start_monitor.sh` with full configuration support
- Enhanced CLI integration for Pane 1
- User documentation (README section)
- Example usage documentation

**Acceptance Criteria:**
- [ ] CLI launches with configurable entry point (Executive Director, etc.)
- [ ] All configuration options work:
  - Session name
  - Output directory
  - Log file path
  - Project ID for task tracking
- [ ] Documentation covers:
  - Installation requirements
  - Quick start guide
  - Configuration options
  - Tmux navigation tips
- [ ] All four panes work together seamlessly
- [ ] Error handling for missing dependencies (tmux, vim, python)

**Dependencies:** Milestones 1 and 2

**Estimated Effort:** Small

---

## Summary

| Milestone | Description | Dependencies | Estimated Effort |
|-----------|-------------|--------------|------------------|
| 1 | Basic Tmux Layout (MVP) | None | Small |
| 2 | Task Watcher Script | Milestone 1 | Small-Medium |
| 3 | Full Integration & Polish | Milestones 1, 2 | Small |

## Technical Decisions Made

1. **Polling vs Filesystem Watching:** Start with polling (simpler cross-platform), optimize later if needed
2. **Raw logs vs Parsed events:** Start with raw backend.log, consider parsed view as future enhancement
3. **CLI auto-start:** Start with shell ready for user command, consider auto-start option later
4. **Directory structure:** Scripts placed in `scripts/monitoring/` to organize with other deployment scripts
5. **Python for task_watcher:** Use Python for better JSON parsing and formatting capabilities
