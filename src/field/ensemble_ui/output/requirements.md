# TMUX Command-Line UI Expansion - Requirements

## Project Vision
Expand the existing Ensemble UI application with a TMUX-based terminal multiplexer interface that allows users to execute commands from both the command line and the existing agent UI, providing a unified experience for developers who prefer terminal-based workflows.

## Core Objectives
1. Create a TMUX-based command-line UI for the Ensemble system
2. Enable command execution from terminal interface
3. Integrate with existing agent UI for unified command execution
4. Maintain real-time visibility of agent execution in terminal
5. Support both CLI-driven and UI-driven workflows seamlessly

## Background Context
The existing system includes:
- **Web UI**: React-based 4-pane interface with WebSocket real-time updates
- **Backend**: FastAPI server with agent execution capabilities
- **Agent System**: Conversational multi-agent development platform
- **File Generation**: Tracks and displays generated files
- **Real-time Updates**: WebSocket broadcasting of agent status

## Key Requirements

### 1. TMUX Integration
- Create a TMUX configuration that provides multi-pane layout
- Mirror the web UI's 4-pane structure in terminal:
  - **Pane 1**: Agent status and conversation (top-left)
  - **Pane 2**: Agent summary and stats (top-right)
  - **Pane 3**: Command input area (bottom-left)
  - **Pane 4**: File viewer and logs (bottom-right)
- Support automatic TMUX session creation and management
- Allow users to detach/reattach to running sessions

### 2. Command-Line Interface
- Provide CLI commands for:
  - Task submission (equivalent to web UI task submission)
  - Agent status monitoring
  - File viewing
  - Conversation/response to agent questions
  - Session management (start, stop, list, attach)
- Support command-line arguments and flags for configuration
- Enable both interactive and non-interactive modes

### 3. Dual Execution Paths
- **CLI Path**: Users can submit tasks directly from terminal
- **UI Path**: Users can submit tasks from existing web UI
- **Unified Backend**: Both paths use the same backend API
- **Synchronized State**: Changes from CLI reflected in UI and vice versa
- **Conflict Resolution**: Handle concurrent command execution gracefully

### 4. Real-Time Terminal Updates
- Stream agent status updates to TMUX panes
- Display real-time logs in terminal (equivalent to web UI logs)
- Show agent hierarchy and progress in terminal format
- Update file list as files are generated
- Use terminal-friendly formatting (ANSI colors, Unicode symbols)

### 5. Terminal UI Components
- **Agent Status Display**: Show current agent, status, and formatted output
- **Command Prompt**: Interactive prompt for task submission and responses
- **File Viewer**: Browse and display file contents in terminal
- **Log Viewer**: Tail-style real-time log streaming
- **Status Bar**: Show connection status, active agents count, errors

### 6. Integration with Existing System
- Reuse existing FastAPI backend endpoints
- Connect to same WebSocket for real-time updates
- Share agent execution infrastructure
- Maintain compatibility with web UI
- No breaking changes to existing functionality

## Technical Stack

### New Components
- **Terminal Multiplexer**: TMUX (or tmuxp for programmatic control)
- **CLI Framework**: Click or Typer (Python CLI frameworks)
- **Terminal UI**: Rich (Python library for terminal formatting)
- **WebSocket Client**: websockets or python-socketio for terminal
- **Configuration**: YAML or TOML for TMUX layout configuration

### Existing Components (Reuse)
- **Backend**: FastAPI (existing)
- **Agent Runtime**: Current ensemble agent system
- **WebSocket Server**: Existing implementation
- **File Tracking**: Current snapshot-based system

## Functional Requirements

### FR1: TMUX Session Management
- **FR1.1**: CLI command to start TMUX session with predefined layout
- **FR1.2**: Automatic backend startup if not running
- **FR1.3**: Named sessions for multiple project isolation
- **FR1.4**: Ability to attach to existing sessions
- **FR1.5**: Clean shutdown that closes all panes gracefully

### FR2: Command Execution
- **FR2.1**: Submit tasks via CLI command (e.g., `ensemble task "build a calculator"`)
- **FR2.2**: View agent status (e.g., `ensemble status`)
- **FR2.3**: List generated files (e.g., `ensemble files`)
- **FR2.4**: Respond to agent questions (e.g., `ensemble respond "yes"`)
- **FR2.5**: View agent history (e.g., `ensemble history`)

### FR3: Real-Time Display
- **FR3.1**: Auto-updating agent status in top-left pane
- **FR3.2**: Agent summary with stats in top-right pane
- **FR3.3**: Streaming logs in bottom-right pane
- **FR3.4**: File list updates in bottom-right pane
- **FR3.5**: Visual indicators for agent states (running, completed, error)

### FR4: Interactive Features
- **FR4.1**: Interactive command prompt in bottom-left pane
- **FR4.2**: Command history navigation (up/down arrows)
- **FR4.3**: Auto-completion for common commands
- **FR4.4**: Help command showing available operations
- **FR4.5**: Keyboard shortcuts for pane navigation

### FR5: File Operations
- **FR5.1**: List generated files in terminal
- **FR5.2**: View file contents with syntax awareness
- **FR5.3**: Open files in external editor from CLI
- **FR5.4**: Export/copy file paths to clipboard
- **FR5.5**: Search through generated files

### FR6: Configuration
- **FR6.1**: Configuration file for TMUX layout preferences
- **FR6.2**: Backend URL configuration (support remote backends)
- **FR6.3**: Color scheme customization
- **FR6.4**: Log level configuration
- **FR6.5**: Default budget tier setting

## Non-Functional Requirements

### NFR1: Performance
- Terminal updates should be near-instantaneous (<100ms)
- Support for long-running agent executions without freezing
- Efficient WebSocket connection management
- Minimal CPU usage for terminal rendering

### NFR2: Usability
- Intuitive command structure following Unix conventions
- Clear error messages with actionable suggestions
- Consistent terminal formatting and colors
- Keyboard-first navigation
- Minimal learning curve for TMUX users

### NFR3: Reliability
- Graceful handling of backend disconnection
- Auto-reconnect to WebSocket on connection loss
- Session persistence across terminal restarts
- No data loss on unexpected termination
- Error recovery without full restart

### NFR4: Compatibility
- Works on macOS, Linux (Ubuntu/Debian)
- Compatible with standard TMUX installations (v3.0+)
- Python 3.11+ support
- Terminal emulator agnostic (iTerm2, Terminal.app, Alacritty, etc.)

### NFR5: Maintainability
- Modular architecture for CLI components
- Shared code with web UI where possible
- Comprehensive logging for debugging
- Clear separation of concerns (CLI, UI rendering, backend communication)

## Success Criteria
1. ✅ Users can start TMUX session with single command
2. ✅ Task submission works from both CLI and web UI
3. ✅ Real-time agent updates visible in terminal panes
4. ✅ File generation tracked and displayed in terminal
5. ✅ Agent conversations work in terminal (ask/respond flow)
6. ✅ TMUX layout mirrors web UI's 4-pane structure
7. ✅ Zero breaking changes to existing web UI
8. ✅ All tests pass (existing + new CLI tests)
9. ✅ Documentation includes CLI usage examples
10. ✅ Performance is equivalent to web UI experience

## Out of Scope
- Terminal-based file editing (use external editors)
- Custom TMUX theme creation (use existing themes)
- Windows support (WSL2 is acceptable)
- Terminal-based agent definition editing
- Graphical file previews in terminal
- Multi-user terminal sessions

## Assumptions
- Users have TMUX installed on their system
- Users are comfortable with basic terminal operations
- Backend server is running locally or accessible via network
- Terminal supports 256 colors and Unicode
- Users prefer keyboard-driven workflows

## Constraints
- Must reuse existing backend without modifications
- Cannot break existing web UI functionality
- Must support concurrent CLI and UI usage
- Terminal rendering limited by terminal capabilities
- TMUX sessions are single-user per session

## Dependencies
- Existing FastAPI backend must be running
- TMUX must be installed on host system
- Python 3.11+ with venv support
- WebSocket connectivity to backend
- Terminal emulator with color support

## Risks and Mitigations

### Risk 1: TMUX Complexity
- **Risk**: TMUX configuration can be complex for new users
- **Mitigation**: Provide pre-configured setup scripts and clear documentation

### Risk 2: Terminal Rendering Performance
- **Risk**: Frequent updates may cause terminal flickering
- **Mitigation**: Use efficient rendering libraries (Rich) with smart diff updates

### Risk 3: WebSocket in Terminal
- **Risk**: Terminal apps typically don't have built-in WebSocket support
- **Mitigation**: Use python-socketio or websockets library with async support

### Risk 4: Concurrent Access
- **Risk**: CLI and UI might conflict when accessing same agent
- **Mitigation**: Backend handles concurrency; UI shows latest state from both sources

### Risk 5: Session Management
- **Risk**: TMUX sessions may become orphaned or misconfigured
- **Mitigation**: Provide cleanup commands and auto-detection of stale sessions

## Open Questions
- Should TMUX layout be configurable or fixed?
  - **Decision**: Provide sensible default, allow override via config file
- How to handle very long agent output in terminal?
  - **Decision**: Use scrollable panes with buffer limits
- Should CLI support multiple simultaneous task submissions?
  - **Decision**: Yes, backend already supports this; show all in status pane
- What terminal UI library to use?
  - **Decision**: Rich for formatting, textual for advanced widgets if needed
- How to indicate active pane in TMUX?
  - **Decision**: Use TMUX's built-in border highlighting + status bar

## Future Enhancements (Not in Initial Scope)
- Vim-style keybindings for navigation
- Multiple workspace support
- Terminal-based project templates
- Integrated git status display
- Performance metrics dashboard in terminal
- Export session logs to file
- Remote TMUX session sharing
- Integration with tmuxinator for project-specific layouts

## Implementation Phases

### Phase 1: Foundation (Week 1)
- CLI framework setup (Click/Typer)
- Basic TMUX session management
- Backend API client in terminal
- Simple command execution (task submission)

### Phase 2: Real-Time Updates (Week 2)
- WebSocket client integration
- Terminal UI rendering with Rich
- 4-pane TMUX layout configuration
- Real-time agent status display

### Phase 3: Interactive Features (Week 3)
- Conversation/response flow in terminal
- File viewer implementation
- Command history and auto-completion
- Keyboard shortcuts

### Phase 4: Polish & Testing (Week 4)
- Configuration file support
- Comprehensive testing (unit + integration)
- Documentation and examples
- Performance optimization
- Error handling improvements

## Documentation Requirements
- Installation guide (TMUX, dependencies, setup)
- CLI command reference
- TMUX layout customization guide
- Keyboard shortcuts cheat sheet
- Troubleshooting common issues
- Examples of common workflows
- Architecture documentation for contributors

## Testing Strategy
- **Unit Tests**: CLI command parsing, formatting functions
- **Integration Tests**: Backend API calls, WebSocket connection
- **E2E Tests**: Full workflow (start session, submit task, view results)
- **Manual Tests**: TMUX layout rendering, real-time updates
- **Performance Tests**: Terminal rendering speed, WebSocket throughput
- **Compatibility Tests**: Different terminal emulators, TMUX versions

## Performance Targets
- Command response time: <200ms
- Terminal update latency: <100ms after backend event
- WebSocket reconnect time: <2s
- Session startup time: <5s
- Memory usage: <100MB for CLI process
- Support: 50+ concurrent agent updates without lag

## Accessibility Considerations
- Colorblind-friendly status indicators (use symbols + colors)
- Screen reader compatibility (plain text fallback mode)
- Configurable color schemes
- Keyboard-only navigation
- Clear text descriptions for visual elements

---

**Document Version**: 1.0
**Created**: 2026-01-13
**Author**: Executive Director (Ensemble AI)
**Status**: Ready for Architecture Phase
