# Tmux Monitoring Dashboard - Milestone Plan

## Project Overview
Creating a tmux-based 2x2 monitoring dashboard that provides real-time visibility into the ensemble agent swarm's operation, allowing developers to observe agent activity, browse output files, and track task progress in a single terminal view.

## Milestone Breakdown

### Milestone 1: Basic Tmux Layout (MVP)
**Objective**: Create a functional 2x2 tmux layout with basic monitoring capabilities

**Deliverables**:
- `scripts/deployment/start_monitor.sh` - Main script to launch tmux dashboard
- `scripts/deployment/stop_monitor.sh` - Script to cleanly stop the dashboard  
- Basic 2x2 tmux layout with:
  - Pane 1 (top-left): Shell ready for CLI interaction
  - Pane 2 (top-right): Live tail of backend.log
  - Pane 3 (bottom-left): Vim opened to output directory
  - Pane 4 (bottom-right): Basic watch command on project file

**Acceptance Criteria**:
- Single command launches complete dashboard
- All 4 panes display correctly in 2x2 grid
- Log streaming works in real-time
- File browser navigates output directory
- Session persists if terminal disconnects
- Clean shutdown script works

**Dependencies**: None

**Estimated Effort**: Medium

---

### Milestone 2: Enhanced Task Monitoring  
**Objective**: Create intelligent task watcher with formatted display and real-time updates

**Deliverables**:
- `scripts/monitoring/task_watcher.py` - Python script to parse project.json and display formatted task list
- Enhanced task display with:
  - Status icons (✅ ⚡ ⏳) for completed, in-progress, pending
  - Task count summary
  - Auto-refresh capability
  - Clean formatting

**Acceptance Criteria**:
- Task status updates in real-time as agents work
- Clear visual distinction between task states
- Summary count shows overall progress
- Performance is responsive (updates every 1-2 seconds)
- Handles missing/malformed project files gracefully

**Dependencies**: Milestone 1 complete

**Estimated Effort**: Medium

---

### Milestone 3: Full CLI Integration and Polish
**Objective**: Complete integration with Claude CLI and production-ready polish

**Deliverables**:
- Full Claude CLI integration in Pane 1
- Enhanced log formatting/filtering for Pane 2
- Configuration options for customization
- Complete documentation and usage examples
- Error handling and edge case management

**Acceptance Criteria**:
- Claude CLI runs automatically in Pane 1 with proper setup
- Log display is clean and informative
- User can customize session name, directories, project ID
- Documentation covers all features and troubleshooting
- Works reliably across macOS and Linux with tmux 3.0+

**Dependencies**: Milestone 2 complete

**Estimated Effort**: Medium

## Timeline Summary
- **Milestone 1**: Foundation (Basic tmux layout with monitoring)
- **Milestone 2**: Intelligence (Smart task tracking)  
- **Milestone 3**: Integration (Production-ready with CLI)

## Technical Strategy
1. Start with shell scripts for rapid prototyping
2. Use Python for task parsing and formatting logic
3. Leverage existing project tracking system at ~/.ensemble/projects/
4. Build incrementally - each milestone is independently valuable
5. Focus on reliability and user experience

## Risk Mitigation
- Test across different tmux versions and shell environments
- Handle edge cases like missing files, permission issues
- Provide clear error messages and troubleshooting guidance
- Keep dependencies minimal (standard tools: tmux, vim, python, bash)