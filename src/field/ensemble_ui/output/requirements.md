# Fix UI Panes Against Requirements Analysis

## Problem Description
User reports not seeing new agents in the metrics pane, but investigation reveals the actual issue is broader: multiple UI panes don't properly reflect the current system state and available agent types. The activity feed filtering is particularly limited and doesn't show all agent activity types.

## Current State Analysis

### Issues Identified

**1. Activity Feed Filter Limitations**
- Hardcoded dropdown options: "all", "agent_spawned", "agent_completed", "tool_use", "iteration_started", "error"
- Missing many actual activity types from the system
- Filter logic uses exact string matching only
- Cannot filter by agent states (failed, error, etc.)
- No way to see new agent types that have been added to the system

**2. Metrics Pane Functionality**
- Actually works correctly - shows aggregate metrics by agent performance
- User confusion may be about expecting individual agent visibility vs. aggregate metrics
- Missing some newer agent types in the data aggregation

**3. Agent States Display**
- Shows running agents correctly but filtering is basic
- Limited visibility into failed states and error details
- No filtering by agent type/category

## Root Cause Analysis
The UI was designed when fewer agent types existed and hasn't been updated to handle the expanded agent ecosystem. The filtering systems are static rather than dynamic.

## Requirements

### R1: Dynamic Activity Feed Filtering
**Must implement dynamic filter generation**:
- Scan actual activities to determine available activity types
- Generate filter options based on real data, not hardcoded values
- Support semantic groupings:
  - Agent Lifecycle: spawned, started, completed, failed
  - Iterations: started, completed
  - Tool Usage: tool_use_started, tool_use_completed, tool_use_failed
  - Communications: message, question, answer
  - System Events: status_change, task_update
  - Errors/Issues: any activity with error indicators

### R2: Enhanced Agent Type Visibility
**Must show all agent types currently in system**:
- Executive Director
- Development Manager
- System Architect
- TDD Coordinator
- Code Writer
- Code Tester
- Any newly spawned agent types

### R3: Real-time Filter Updates
**Must dynamically update filters**:
- When new activity types appear, add them to filters
- When new agent types are spawned, show them in relevant panes
- Count activities per filter option for user clarity

### R4: Improved Error/Failed State Visibility
**Must better highlight problems**:
- Failed agents prominently displayed
- Error activities easy to filter and find
- Clear visual distinction between different failure modes

### R5: Metrics Pane Agent Coverage  
**Must ensure metrics include all agent types**:
- Verify backend aggregation includes all agent types
- Display newer agent types in performance tables
- Show agent type distribution in summary

## Technical Implementation Plan

### Phase 1: Activity Feed Enhancement
1. **Dynamic Filter Generation**
   - Scan activities array for unique activity_type values
   - Create semantic groupings for related activity types
   - Build filter dropdown dynamically

2. **Smart Filter Logic**
   - Replace exact string matching with category-based filtering
   - Support multiple activity types per filter
   - Handle special cases (error detection, agent state filtering)

3. **Activity Count Display**
   - Show count of activities per filter option
   - Update counts as new activities arrive

### Phase 2: Metrics Pane Verification
1. **Backend API Check**
   - Verify all agent types are included in metrics aggregation
   - Ensure new agent types appear in performance tables

2. **Frontend Display Enhancement**
   - Improve agent name display and grouping
   - Add agent type categorization in metrics views

### Phase 3: Agent States Enhancement
1. **Enhanced Agent Type Filtering**
   - Add filtering by agent category (leadership, coordinators, developers, testers)
   - Show agent type in agent task display

2. **Better Error State Display**
   - Highlight failed agents more prominently
   - Show error details and failure reasons
   - Add quick filter for "problem agents"

## Success Criteria

### Functional Requirements
1. **Activity feed shows all activity types present in system**
2. **User can filter by semantic categories (errors, agent lifecycle, etc.)**
3. **All spawned agent types visible in relevant UI panes**
4. **Failed/error states clearly visible and filterable**
5. **Metrics pane includes performance data for all agent types**

### User Experience Requirements
1. **Filters are intuitive and self-explanatory**
2. **No confusion about where to find specific agent information**
3. **Clear visual indication of system problems/failures**
4. **Filters show activity counts for context**

### Technical Requirements
1. **Dynamic filter generation based on actual data**
2. **Performant with 200+ activities**
3. **Real-time updates as new agent types appear**
4. **Backward compatible with existing activity data**

## Implementation Priority
1. **HIGH**: Activity feed dynamic filtering (addresses primary user complaint)
2. **MEDIUM**: Agent type visibility improvements
3. **MEDIUM**: Enhanced error state display
4. **LOW**: Metrics pane verification (likely already working)

## Out of Scope
- Changes to backend activity tracking
- New activity types creation
- UI redesign or layout changes
- Search functionality within panes

## Constraints
- Must maintain existing UI performance
- Cannot break existing polling/update logic
- Must work with current activity data structure
- No backend API changes required

## Assumptions
- Activity data contains consistent activity_type field
- Agent spawning creates trackable activities
- Current metrics backend includes all agent types
- User wants to see real-time agent activity, not just aggregated metrics