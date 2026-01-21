# Frontend Tasks - Metrics Display Components

## Overview
This milestone implements frontend components to display agent execution metrics (cost, duration, model) with user-friendly formatting and intuitive visual design.

## User Flow Analysis
1. **User views agent summary** → sees basic agent info (current state)
2. **Agent starts executing** → sees start time and "Running" status
3. **Agent completes** → sees full metrics (duration, cost, model)
4. **User scans metrics** → quickly understands performance impact

## Task Breakdown

### Core Component Tasks

#### Task 1: Duration Formatter Utility
**Description**: Create utility function to format duration from milliseconds to human-readable format
**Acceptance Criteria**:
- Formats < 1000ms as "123ms"
- Formats < 60s as "2.3s" 
- Formats > 60s as "1m 45s"
- Handles null/undefined gracefully
- Returns consistent string format
**Dependencies**: None
**Complexity**: Simple
**Files**: `utils/formatters.js` (new)

#### Task 2: Cost Formatter Utility  
**Description**: Create utility function to format cost in USD to readable string
**Acceptance Criteria**:
- Formats costs as "$0.0042"
- Shows "<$0.0001" for very small costs
- Handles null/undefined as "N/A"
- Returns consistent currency format
- Handles edge cases (0, negative, very large)
**Dependencies**: None
**Complexity**: Simple
**Files**: `utils/formatters.js` (update)

#### Task 3: Model Name Formatter Utility
**Description**: Create utility to shorten model names for display
**Acceptance Criteria**:
- "claude-3-5-sonnet-20241022" → "Sonnet 3.5"
- "claude-3-opus-20240229" → "Opus"
- "claude-3-haiku-20240307" → "Haiku"
- Handles unknown models gracefully
- Returns consistent shortened names
**Dependencies**: None
**Complexity**: Simple
**Files**: `utils/formatters.js` (update)

#### Task 4: Time Display Utility
**Description**: Create utility to format timestamps for start/completion times
**Acceptance Criteria**:
- Shows ISO timestamps as "10:30:42" (time only)
- Handles timezone display appropriately
- Shows relative time for recent events ("2m ago")
- Handles null/undefined gracefully
- Consistent format across components
**Dependencies**: None
**Complexity**: Simple
**Files**: `utils/formatters.js` (update)

### Display Components

#### Task 5: Metrics Badge Component
**Description**: Create reusable badge component for displaying individual metrics
**Acceptance Criteria**:
- Displays icon + text in compact format
- Supports different badge types (duration, cost, model)
- Consistent styling with existing UI
- Handles missing data gracefully
- Responsive design for different screen sizes
**Dependencies**: Task 1-3 (formatters)
**Complexity**: Medium
**Files**: `components/MetricsBadge.jsx` (new)

#### Task 6: Metrics Row Component
**Description**: Create component to display all metrics in a horizontal row
**Acceptance Criteria**:
- Shows duration, cost, and model badges in row
- Proper spacing and alignment
- Responsive layout (stacks on mobile)
- Handles partial data (some metrics missing)
- Integrates with existing AgentSummaryPane styling
**Dependencies**: Task 5 (MetricsBadge)
**Complexity**: Medium
**Files**: `components/MetricsRow.jsx` (new)

#### Task 7: Execution Timeline Component
**Description**: Create component to show start → completion timeline
**Acceptance Criteria**:
- Displays "Started: 10:30:00" format
- Shows "Completed: 10:30:42" when done
- Shows "Running since: 10:30:00" for active agents
- Consistent time formatting
- Clear visual distinction between states
**Dependencies**: Task 4 (time formatter)
**Complexity**: Medium  
**Files**: `components/ExecutionTimeline.jsx` (new)

### Integration Tasks

#### Task 8: AgentSummaryPane Data Integration
**Description**: Update AgentSummaryPane to consume new metrics data from API
**Acceptance Criteria**:
- Receives metrics data from WebSocket/API updates
- Handles backward compatibility (missing fields)
- Updates state when agent transitions running → completed
- Maintains existing functionality unchanged
- Proper error handling for malformed data
**Dependencies**: None (data structure)
**Complexity**: Medium
**Files**: `components/AgentSummaryPane.jsx` (update)

#### Task 9: AgentSummaryPane Layout Update
**Description**: Update AgentSummaryPane layout to include metrics display
**Acceptance Criteria**:
- Integrates MetricsRow component below agent status
- Integrates ExecutionTimeline component appropriately
- Maintains existing visual hierarchy
- Responsive design works on all screen sizes
- No layout breaks with missing metrics data
**Dependencies**: Task 6, 7, 8 (components and data)
**Complexity**: Medium
**Files**: `components/AgentSummaryPane.jsx` (update)

#### Task 10: Visual Design Polish
**Description**: Apply consistent styling and visual design to metrics display
**Acceptance Criteria**:
- Metrics visually integrated with existing UI theme
- Appropriate icons for each metric type (⏱️ 💰 🏷️)
- Consistent color scheme and typography
- Proper visual hierarchy (metrics support, don't dominate)
- Accessibility compliant (contrast, screen readers)
**Dependencies**: Task 9 (layout integration)
**Complexity**: Medium
**Files**: `components/AgentSummaryPane.jsx`, CSS files (update)

### Testing Tasks

#### Task 11: Formatter Unit Tests
**Description**: Create unit tests for all formatter utilities
**Acceptance Criteria**:
- Tests all formatter functions comprehensively
- Tests edge cases (null, undefined, extreme values)
- Tests formatting consistency
- 100% code coverage for formatters
- Fast execution (< 100ms total)
**Dependencies**: Task 1-4 (formatters)
**Complexity**: Simple
**Files**: `utils/formatters.test.js` (new)

#### Task 12: Component Unit Tests
**Description**: Create unit tests for MetricsBadge and MetricsRow components
**Acceptance Criteria**:
- Tests rendering with various props
- Tests missing data handling
- Tests responsive behavior
- Tests accessibility attributes
- Uses React Testing Library best practices
**Dependencies**: Task 5-6 (components)
**Complexity**: Medium
**Files**: `components/MetricsBadge.test.jsx`, `components/MetricsRow.test.jsx` (new)

#### Task 13: Integration Tests
**Description**: Create integration tests for AgentSummaryPane with metrics
**Acceptance Criteria**:
- Tests full data flow (API → component → display)
- Tests agent state transitions (running → completed)
- Tests missing/partial metrics data
- Tests WebSocket updates
- Verifies visual layout correctness
**Dependencies**: Task 8-10 (integration)
**Complexity**: Complex
**Files**: `components/AgentSummaryPane.integration.test.jsx` (new)

## Component Hierarchy

```
AgentSummaryPane
├── [existing content]
├── ExecutionTimeline
│   └── (start/completion times)
└── MetricsRow
    ├── MetricsBadge (duration)
    ├── MetricsBadge (cost)
    └── MetricsBadge (model)
```

## Data Dependencies

### Required API Fields
```javascript
{
  // Existing fields...
  started_at: "2024-01-13T10:30:00.123Z",     // ISO timestamp
  completed_at: "2024-01-13T10:30:42.456Z",   // ISO timestamp (optional)
  duration_ms: 42333,                         // milliseconds (optional)
  model_used: "claude-3-5-sonnet-20241022",   // model identifier
  cost_estimate: 0.0042,                      // USD (optional)
  token_usage: {                              // optional
    input_tokens: 1200,
    output_tokens: 350,
    total_tokens: 1550
  }
}
```

## File Structure

```
src/
├── utils/
│   ├── formatters.js (new)
│   └── formatters.test.js (new)
├── components/
│   ├── MetricsBadge.jsx (new)
│   ├── MetricsBadge.test.jsx (new)
│   ├── MetricsRow.jsx (new)  
│   ├── MetricsRow.test.jsx (new)
│   ├── ExecutionTimeline.jsx (new)
│   ├── AgentSummaryPane.jsx (update)
│   └── AgentSummaryPane.integration.test.jsx (new)
└── styles/
    └── metrics.css (new, if needed)
```

## Implementation Order

**Phase 1: Foundation** (Tasks 1-4)
- Build all formatter utilities
- Create comprehensive unit tests

**Phase 2: Components** (Tasks 5-7)  
- Build reusable display components
- Test components in isolation

**Phase 3: Integration** (Tasks 8-10)
- Integrate with AgentSummaryPane
- Apply visual design and polish

**Phase 4: Quality** (Tasks 11-13)
- Complete test coverage
- End-to-end testing

## Visual Design Mockup

```
┌───────────────────────────────────────────┐
│ 🤖 Executive Director                     │
│ Status: ✅ Completed                      │
│                                           │
│ ⏱️ 2.3s  💰 $0.0042  🏷️ Sonnet 3.5      │
│                                           │
│ Started: 10:30:00                         │
│ Completed: 10:30:02                       │
│                                           │
│ Current Task: Completed                   │
└───────────────────────────────────────────┘
```

## Success Metrics
- All 13 tasks completed and tested
- Metrics display consistently across all agent types
- No performance degradation from existing functionality  
- Visual design integrates seamlessly with current UI
- 100% backward compatibility with existing data