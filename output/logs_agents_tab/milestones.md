# Milestone Plan: Backend Logs Tab & Agent Definition Explorer

## Project Overview
Add a new "Logs & Agents" tab to the Ensemble UI with:
1. Real-time backend log streaming
2. Agent definition file explorer with view/edit capabilities

## Technical Decisions Made
- **WebSocket for log streaming**: Leverage existing WebSocket infrastructure (already have `/ws/agent-status`)
- **React Bootstrap for UI**: Match existing UI framework
- **Simple textarea for editing**: No need for Monaco editor initially (per requirements)
- **Existing API endpoints**: Leverage `/api/agents`, `/api/agents/{tier}/{name}`, `/api/agents/update`
- **Split-pane layout**: Use CSS flexbox for responsive split pane

---

## Milestone 1: Backend Log Streaming Infrastructure
**Objective**: Create WebSocket endpoint and log buffer for real-time log streaming

### Deliverables
1. Log buffer class with size-limited ring buffer (1000 entries)
2. WebSocket endpoint `/ws/logs` for log streaming
3. Log filtering by level (INFO, WARNING, ERROR, DEBUG)
4. Log filtering by agent_id and request_id
5. Structured log entries with timestamp, level, agent_id, request_id, message

### Acceptance Criteria
- [ ] WebSocket endpoint accepts connections and streams logs
- [ ] Log buffer doesn't exceed 1000 entries (memory safety)
- [ ] Logs include structured metadata (agent_id, request_id, timestamp, level)
- [ ] Filtering works on server-side before sending to client
- [ ] Existing logging continues to work (no performance degradation)

### Dependencies
- None (foundational milestone)

---

## Milestone 2: Frontend Log Viewer Component
**Objective**: Create React component to display streamed logs

### Deliverables
1. `LogStreamPanel.jsx` component
2. WebSocket connection to `/ws/logs`
3. Auto-scroll with toggle
4. Log level filter buttons (INFO, WARNING, ERROR, DEBUG)
5. Search filter for agent_id/request_id
6. Pause/Resume streaming
7. Clear logs button
8. Color coding by log level
9. Timestamp display (relative/absolute toggle)

### Acceptance Criteria
- [ ] Component connects to WebSocket and displays logs
- [ ] Auto-scroll works and can be toggled
- [ ] Filters work correctly (level, search)
- [ ] Pause/Resume controls work
- [ ] Clear button clears displayed logs
- [ ] Color coding matches log levels
- [ ] Timestamps are readable

### Dependencies
- Milestone 1 (backend log streaming)

---

## Milestone 3: Agent Definition Explorer Component
**Objective**: Create tree-view file explorer for agent definitions

### Deliverables
1. `AgentExplorer.jsx` component
2. Tree-view with collapsible directories
3. Integration with existing `/api/agents` endpoint
4. Directory structure: leadership/, coordinators/, developers/, testers/, designers/
5. Click to select agent file
6. Visual indicators for selected file

### Acceptance Criteria
- [ ] Tree displays all agent directories correctly
- [ ] Directories can be expanded/collapsed
- [ ] Clicking a file selects it
- [ ] Visual feedback for selection state
- [ ] Icons differentiate files and folders

### Dependencies
- None (can run in parallel with Milestone 2)

---

## Milestone 4: Agent Definition Viewer/Editor
**Objective**: Create component to view and edit agent definitions

### Deliverables
1. `AgentDefinitionViewer.jsx` component
2. Read-only view mode (default)
3. Edit mode with toggle
4. Textarea for editing content
5. Markdown preview panel
6. Save button with confirmation
7. Revert functionality (from backup)
8. Success/error feedback

### Acceptance Criteria
- [ ] View mode displays file content
- [ ] Edit toggle switches to editable textarea
- [ ] Save calls `/api/agents/update` endpoint
- [ ] Success message shows backup path
- [ ] Revert option works
- [ ] Error handling for failed saves

### Dependencies
- Milestone 3 (explorer provides file selection)

---

## Milestone 5: Tab Integration & Final Assembly
**Objective**: Integrate components into new tab in App.jsx

### Deliverables
1. Tab navigation component in App.jsx
2. "Main View" tab (existing content)
3. "Logs & Agents" tab (new content)
4. Split-pane layout in new tab
5. Responsive design
6. State management for tab switching

### Acceptance Criteria
- [ ] Tab navigation works smoothly
- [ ] Existing functionality preserved in "Main View"
- [ ] New tab shows logs panel + agent explorer/editor
- [ ] Split pane is resizable or has good default split
- [ ] UI follows existing dark theme
- [ ] All components integrate correctly

### Dependencies
- Milestones 2, 3, 4 (all components ready)

---

## Timeline Estimate
- Milestone 1: ~2 hours (backend)
- Milestone 2: ~3 hours (frontend)
- Milestone 3: ~2 hours (frontend)
- Milestone 4: ~3 hours (frontend)
- Milestone 5: ~2 hours (integration)

**Total**: ~12 hours of development work

## Risk Assessment
1. **Low Risk**: WebSocket infrastructure exists, just adding another endpoint
2. **Low Risk**: API endpoints for agents already exist
3. **Medium Risk**: Tab integration might need CSS adjustments for layout
4. **Low Risk**: React Bootstrap components are well-documented

## Success Metrics
1. Users can view real-time backend logs without page refresh
2. Users can browse all agent definition files in tree structure
3. Users can view and edit agent definitions with backup
4. Log streaming doesn't degrade backend performance
5. UI matches existing design patterns
