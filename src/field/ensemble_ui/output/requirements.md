# Requirements: Backend Logs Tab & Agent Definition Explorer

## Vision
Add a new tab to the Ensemble UI that provides two key capabilities:
1. **Backend Log Viewer**: Real-time tail of backend logs showing agent activity as it happens
2. **Agent Definition Explorer**: A file explorer interface for viewing and editing agent definition files (.md files in leadership/, coordinators/, developers/, testers/, designers/ directories)

## Objectives
1. Enable users to monitor backend execution in real-time through streamed log output
2. Provide a file-explorer style interface for browsing agent definition files
3. Allow viewing the contents of any agent definition file
4. Enable suggesting updates to agent definitions that can be incorporated into the system

## Scope

### In Scope
1. **New "Logs & Agents" Tab** in the main UI
   - Tab navigation to switch between existing views and the new tab
   - Split-pane layout: logs on one side, agent explorer on the other

2. **Backend Log Streaming**
   - WebSocket or SSE endpoint to stream backend logs
   - Real-time log display with auto-scroll (toggle-able)
   - Log level filtering (INFO, WARNING, ERROR, DEBUG)
   - Search/filter by agent ID or request ID
   - Clear logs button
   - Pause/resume log streaming
   - Timestamp display with relative/absolute toggle
   - Color coding by log level

3. **Agent Definition Explorer**
   - Tree-view file explorer showing agent directory structure:
     - leadership/ (executive_director.md, development_manager.md, system_architect.md, tdd_coordinator.md)
     - coordinators/ (backend_coordinator.md, frontend_coordinator.md, test_coordinator.md)
     - developers/ (backend_developer.md, backend_lead.md, frontend_developer.md, frontend_lead.md)
     - testers/ (any test agent definitions)
     - designers/ (any design agent definitions)
   - Click to view file contents
   - Syntax highlighting for markdown
   - Collapsible directory tree

4. **Agent Definition Viewer/Editor**
   - Display selected agent definition content
   - Read-only view by default
   - "Edit" mode toggle
   - Markdown preview alongside raw content
   - "Save Suggestion" button (uses existing `/api/agents/update` endpoint)
   - Validation before save (backend validates agent definition structure)
   - Backup confirmation (show backup file path)
   - Revert option (restore from backup)

5. **Backend API Enhancements**
   - `/api/logs/stream` - WebSocket endpoint for log streaming
   - Leverage existing `/api/agents` endpoint for listing agents
   - Leverage existing `/api/agents/{tier}/{name}` endpoint for getting content
   - Leverage existing `/api/agents/update` endpoint for updates

### Out of Scope
- Creating new agent definition files (only edit existing)
- Deleting agent definition files
- Git integration for version control
- Multi-user collaboration on edits
- Syntax validation/linting for agent markdown format

## User Stories

### Log Viewer
1. As a user, I want to see backend logs in real-time so I can monitor what agents are doing
2. As a user, I want to filter logs by level so I can focus on errors or important events
3. As a user, I want to search logs by agent ID so I can trace a specific agent's activity
4. As a user, I want to pause log streaming so I can read a specific section
5. As a user, I want to clear logs to start fresh when debugging

### Agent Explorer
1. As a user, I want to browse agent definitions in a tree structure so I can find agents easily
2. As a user, I want to click an agent to see its full definition
3. As a user, I want to edit agent definitions and submit updates
4. As a user, I want confirmation that my changes were saved with a backup
5. As a user, I want to revert to the backup if my changes don't work

## Technical Constraints

### Existing System Integration
- Must integrate with existing React/Bootstrap UI framework
- Must use existing FastAPI backend on port 8001
- Must maintain existing WebSocket infrastructure
- Must work with current file structure at `/Users/mattbillock/Development/ai_exploration/ensemble/`

### Backend Requirements
- Log streaming should use Python's logging infrastructure
- Logs should include structured data (agent_id, request_id, timestamp, level, message)
- Log buffer should be limited to prevent memory issues (e.g., last 1000 entries)
- Must not impact performance of agent execution

### Frontend Requirements
- Use existing dark theme styling (backgroundColor: #1a1d29, cards: #242836)
- Use Bootstrap components (Card, Button, Badge, etc.)
- Tab component for navigation
- Monaco or simple textarea for editing
- Split pane layout for logs/explorer

## Success Criteria
1. Users can view real-time backend logs without page refresh
2. Users can browse all agent definition files in a tree structure
3. Users can view the contents of any agent definition
4. Users can edit and save agent definitions with automatic backup
5. Log streaming does not degrade backend performance
6. UI is responsive and follows existing design patterns

## Assumptions Made
- Using existing React Bootstrap for UI components
- Using existing WebSocket infrastructure for log streaming
- Log entries will be JSON-structured for easy parsing
- Backend logging is already producing structured logs (confirmed in main.py)
- A simple textarea is sufficient for editing (no need for Monaco editor initially)
- Users are technical and understand markdown format for agent definitions

## Technical Notes

### Existing API Endpoints Available
- `GET /api/agents` - Lists all agent definitions (already exists)
- `GET /api/agents/{tier}/{name}` - Gets agent content (already exists)
- `POST /api/agents/update` - Updates agent file with backup (already exists)

### Required New Endpoints
- `WS /ws/logs` or `GET /api/logs/stream` - Stream backend logs

### Existing Agent Directories
- `/Users/mattbillock/Development/ai_exploration/ensemble/leadership/`
- `/Users/mattbillock/Development/ai_exploration/ensemble/coordinators/`
- `/Users/mattbillock/Development/ai_exploration/ensemble/developers/`
- `/Users/mattbillock/Development/ai_exploration/ensemble/testers/`
- `/Users/mattbillock/Development/ai_exploration/ensemble/designers/`

### Existing UI Components (for reference)
- `App.jsx` - Main application with 3-column layout
- `ActivityFeed.jsx` - Activity display component
- `AgentHierarchyTree.jsx` - Tree display component
- `PendingQuestions.jsx` - Question handling component

## UI Layout Suggestion

```
+------------------------------------------------------------------+
| 🎭 Ensemble AI | [Online] | [Running] | [Completed] | [Interval] |
+------------------------------------------------------------------+
| [Main View] | [Logs & Agents] |                                   |
+------------------------------------------------------------------+
|                    |                                              |
| Log Stream Panel   | Agent Definition Explorer                    |
| +--------------+   | +----------------------------------------+   |
| | Log entries  |   | | 📁 leadership/                         |   |
| | auto-scroll  |   | |   📄 executive_director.md             |   |
| | ...          |   | |   📄 development_manager.md            |   |
| | filters:     |   | | 📁 coordinators/                       |   |
| | [INFO][ERR]  |   | |   📄 backend_coordinator.md            |   |
| | [search...]  |   | +----------------------------------------+   |
| +--------------+   | +----------------------------------------+   |
|                    | | Agent Content Viewer                   |   |
| [Pause][Clear]     | | [View] [Edit]                          |   |
|                    | | # Executive Director                   |   |
|                    | | ...markdown content...                 |   |
|                    | | [Save Changes] [Revert]                |   |
|                    | +----------------------------------------+   |
+------------------------------------------------------------------+
```

## Milestones

### Milestone 1: Backend Log Streaming
- Create WebSocket endpoint for log streaming
- Implement log buffer with size limit
- Add log filtering by level

### Milestone 2: Frontend Log Viewer Component
- Create LogStreamPanel component
- Implement auto-scroll with toggle
- Add log level filters and search
- Add pause/resume and clear functionality

### Milestone 3: Agent Explorer Component
- Create AgentExplorer tree component
- Implement directory expansion/collapse
- Click to select agent file

### Milestone 4: Agent Viewer/Editor
- Create AgentDefinitionViewer component
- Implement view/edit toggle
- Add save with validation
- Add revert functionality

### Milestone 5: Tab Integration
- Add tab navigation to main App.jsx
- Integrate both panels into new tab
- Ensure seamless switching between tabs
