# UI Improvements Requirements

## Project Vision
Enhance the Ensemble UI with two key improvements to better support multi-project workflows and provide clearer status visibility during agent execution.

## Core Objectives
1. **Project-Based Agent Organization**: Allow users to run multiple projects simultaneously with clear separation in the agent hierarchy
2. **Enhanced Status Indicators**: Provide real-time process stage visibility with expanded badging and status summary

## Key Requirements

### 1. Project-Based Agent Hierarchy Organization
**Problem**: Current agent hierarchy shows all agents in a flat/hierarchical structure without project grouping, making it difficult to track multiple concurrent projects.

**Solution**: 
- Group agents by project/task in the agent hierarchy tree
- Each submitted task should have a clear project identifier
- Agent hierarchy should show project groupings at the top level
- Users should be able to expand/collapse by project
- Each project group should show its own status summary (running, completed, failed agents)

**Technical Approach**:
- Extend backend to track project_id or task_id for each agent execution
- Modify AgentHierarchyTree component to group agents by project_id
- Add project-level badges and status indicators
- Maintain expand/collapse functionality at project level

### 2. Enhanced Status Line and Stage Indicators
**Problem**: Users need more immediate visibility into what stage of the process is active (requirements, architecture, planning, implementation, etc.)

**Solution**:
- Add a prominent status line showing current active work summary
- Expand badge system to indicate process stage for each agent/project
- Show stage progression (requirements → architecture → planning → implementation → testing → completion)
- Add visual indicators for current stage of each project
- Provide quick "at-a-glance" understanding of system state

**Technical Approach**:
- Create StatusSummaryBar component showing:
  - Currently active projects (count)
  - Current stage(s) being worked on
  - Active agents summary by stage
- Enhance badges to show stage information:
  - Stage icons (📋 requirements, 🏗️ architecture, 📝 planning, 💻 implementation, 🧪 testing, ✅ complete)
  - Stage colors/variants
- Add stage information to agent state tracking:
  - Backend should track and report current phase/stage
  - Frontend should display this prominently
- Add stage timeline/progress indicator for each project

## User Stories

### Story 1: Multi-Project Management
**As a** developer running multiple AI projects  
**I want** to see agents organized by project  
**So that** I can track multiple concurrent tasks without confusion

**Acceptance Criteria**:
- Agent hierarchy shows project groupings at top level
- Each project shows its own agent hierarchy beneath it
- Project groups show summary statistics (agent counts, status)
- Can expand/collapse by project
- Each project has clear visual separation

### Story 2: Stage Visibility
**As a** user monitoring agent progress  
**I want** to see what stage of the process is currently active  
**So that** I understand what's happening and how far along we are

**Acceptance Criteria**:
- Status bar shows current stage(s) being worked on
- Each agent/project shows its current stage with badge
- Stage progression is visually clear
- Can quickly identify if in requirements, implementation, testing, etc.
- Stage indicators use consistent iconography

### Story 3: Quick Status Summary
**As a** user with multiple projects running  
**I want** a quick summary of overall system state  
**So that** I can rapidly understand what needs attention

**Acceptance Criteria**:
- Single status line shows: active projects count, active stages, agent counts by status
- Status line updates in real-time
- Color coding indicates system health (all green, warnings, errors)
- Click on status elements to filter/navigate to details

## Technical Stack
- Frontend: React 18, React Bootstrap
- Backend: FastAPI (Python) - minimal changes needed
- State Management: React useState/useEffect
- Real-time Updates: Existing polling mechanism (1-2 second intervals)

## Implementation Scope

### In Scope
- Project-based grouping in agent hierarchy
- Enhanced badge system with stage indicators
- New StatusSummaryBar component
- Backend tracking of project_id and stage information
- Activity feed filtering by project
- Visual stage progression indicators

### Out of Scope
- Complex project management features (dependencies, scheduling)
- Historical project archive/management
- User authentication/multi-user support
- Project creation/configuration UI
- Advanced filtering beyond project grouping
- WebSocket/real-time streaming (continue using polling)

## Success Criteria
1. ✅ Can run multiple projects and see them clearly separated in hierarchy
2. ✅ Each project shows its own agent tree and status
3. ✅ Status bar shows current stage(s) across all active work
4. ✅ Badges include stage indicators with consistent icons
5. ✅ At-a-glance understanding of "what's happening now"
6. ✅ No regression in existing functionality
7. ✅ All existing tests pass
8. ✅ New tests cover project grouping and stage display
9. ✅ Performance remains good with multiple concurrent projects

## Constraints
- Use existing polling-based update mechanism
- Maintain current responsive design
- Follow existing Bootstrap theming/styling
- Keep changes minimal and focused
- Preserve backward compatibility with existing API
- No breaking changes to agent runtime

## Assumptions
- Projects are implicitly defined by each "generate-solution" API call
- Each submission creates a new project with unique ID
- Project lifecycle follows standard phases: requirements → architecture → planning → implementation → testing → complete
- Executive Director agent tracks and reports its current phase
- Existing activity tracker can be extended with minimal changes

## Non-Functional Requirements
- Real-time updates continue at 1-2 second intervals
- UI remains responsive with 10+ concurrent projects
- Stage indicators load and display within 100ms
- Project grouping/ungrouping is instantaneous
- No memory leaks with long-running sessions
- Graceful degradation if stage information unavailable