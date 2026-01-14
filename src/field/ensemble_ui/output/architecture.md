# Agent Hierarchy Organization - System Architecture

## Executive Summary
This architecture implements a task-based agent hierarchy display system with whimsical naming and activity titles. The design extends the existing ensemble agent framework to track and display agent metadata without disrupting core functionality.

## System Overview

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                        Web UI Layer                          │
│  ┌─────────────────┐  ┌──────────────────────────────────┐ │
│  │ Agent Hierarchy │  │   Activity Title Display         │ │
│  │  Component      │  │   Whimsical Name Display         │ │
│  └─────────────────┘  └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  /api/agents - Get all agents with metadata            ││
│  │  /api/agents/{id} - Get specific agent                 ││
│  │  /ws/agents - Real-time agent updates                  ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                    Agent Management Layer                    │
│  ┌──────────────────┐  ┌─────────────────────────────────┐ │
│  │ Agent Tracker    │  │  Agent Metadata Manager         │ │
│  │ (existing +      │  │  - Whimsical names              │ │
│  │  enhancements)   │  │  - Activity titles              │ │
│  └──────────────────┘  │  - Task-based grouping          │ │
│                        └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                  Agent Spawning & Lifecycle                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Whimsical Name Generator                            │  │
│  │  - Name pool management                              │  │
│  │  - Uniqueness enforcement                            │  │
│  │  - Theme-based generation                            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. Agent Metadata Extension

**Purpose**: Extend agent data model to include new display fields.

**Schema**:
```python
{
    "agent_id": "string (uuid)",
    "agent_type": "string (existing)",
    "whimsical_name": "string (new)",
    "current_activity_title": "string (new)",
    "status": "string (existing)",
    "parent_id": "string (existing)",
    "created_at": "timestamp (existing)",
    "updated_at": "timestamp (existing)",
    "task_category": "string (new - for grouping)"
}
```

**Implementation Notes**:
- Backward compatible - new fields optional
- Metadata stored in agent tracking system
- Persisted across agent lifecycle

### 2. Whimsical Name Generator

**Purpose**: Generate unique, memorable names for agent instances.

**Design**:
```python
class WhimsicalNameGenerator:
    """
    Generates unique whimsical names combining:
    - Adjectives: Clever, Swift, Mighty, Wise, etc.
    - Nouns: Famous scientists, fictional characters, etc.
    
    Examples:
    - "Chomsky the Architect"
    - "Pixel the UI Builder"
    - "Tesla the Backend Guru"
    """
    
    def generate_name(agent_type: str) -> str:
        # Generate contextual name based on agent type
        pass
    
    def ensure_uniqueness(name: str) -> str:
        # Add suffix if name already exists
        pass
```

**Name Pools**:
- Scientists: Tesla, Curie, Turing, Lovelace, Einstein, Hawking
- Literary: Gatsby, Atticus, Sherlock, Gandalf, Hermione
- Adjectives: Swift, Clever, Mighty, Wise, Bold, Brilliant
- Tech: Pixel, Byte, Cache, Stack, Queue, Kernel

**Uniqueness Strategy**:
- Track active names in memory
- Append numeric suffix if collision: "Tesla-2"
- Release names when agent completes

### 3. Activity Title System

**Purpose**: Provide real-time descriptive titles for agent activities.

**Design**:
```python
class ActivityTitleManager:
    """
    Maps agent types and states to descriptive titles
    """
    
    TITLE_MAPPING = {
        "executive_director": {
            "initializing": "Coordinating Project",
            "delegating": "Assigning Tasks",
            "reviewing": "Reviewing Progress"
        },
        "system_architect": {
            "analyzing": "Designing Architecture",
            "documenting": "Writing Specifications"
        },
        "backend_coordinator": {
            "planning": "Planning Backend Work",
            "coordinating": "Organizing Tasks"
        },
        "code_writer": {
            "writing": "Writing Code",
            "refactoring": "Improving Code"
        },
        "test_coordinator": {
            "planning": "Planning Tests",
            "reviewing": "Reviewing Test Coverage"
        }
    }
    
    def get_title(agent_type: str, activity: str) -> str:
        # Return descriptive title based on type and activity
        pass
```

**Title Guidelines**:
- 2-5 words maximum
- Action-oriented (verb + object)
- Avoid technical jargon
- Update in real-time as agent progresses

### 4. Task-Based Hierarchy Grouping

**Purpose**: Organize agents by tasks/workflows rather than types.

**Grouping Strategy**:
```python
TASK_GROUPS = {
    "Planning & Architecture": [
        "executive_director",
        "system_architect",
        "development_manager"
    ],
    "Backend Development": [
        "backend_coordinator",
        "backend_section_leader",
        "backend_code_writer"
    ],
    "Frontend Development": [
        "frontend_coordinator", 
        "frontend_section_leader",
        "frontend_code_writer"
    ],
    "Testing & Quality": [
        "test_coordinator",
        "tdd_coordinator",
        "test_section_leader"
    ]
}
```

**Hierarchy Display Logic**:
1. Group agents by task category
2. Within each group, show hierarchy (parent-child)
3. Display whimsical name + activity title for each agent
4. Use visual indicators for active vs completed agents

### 5. API Layer

**Endpoints**:

```
GET /api/agents
Response: {
    "agents": [
        {
            "agent_id": "uuid",
            "agent_type": "system_architect",
            "whimsical_name": "Chomsky the Architect",
            "current_activity_title": "Designing Architecture",
            "status": "active",
            "task_category": "Planning & Architecture",
            "parent_id": "parent-uuid",
            "created_at": "timestamp"
        }
    ],
    "task_groups": {
        "Planning & Architecture": ["uuid1", "uuid2"],
        "Backend Development": ["uuid3", "uuid4"]
    }
}

GET /api/agents/{agent_id}
Response: {
    "agent_id": "uuid",
    "whimsical_name": "Tesla the Backend Guru",
    "current_activity_title": "Writing API Endpoints",
    "status": "active",
    "logs": [...],
    "children": [...]
}

WebSocket /ws/agents
Real-time updates when:
- New agent spawned
- Activity title changes
- Agent status changes
- Agent completes
```

### 6. UI Components

**Agent Hierarchy Component**:
```javascript
// Pseudo-code structure
<AgentHierarchy>
  <TaskGroup name="Planning & Architecture">
    <AgentNode 
      name="Chomsky the Architect"
      activity="Designing Architecture"
      status="active"
      children={[...]}
    />
  </TaskGroup>
  
  <TaskGroup name="Backend Development">
    <AgentNode 
      name="Tesla the Code Wizard"
      activity="Writing Services"
      status="active"
    />
  </TaskGroup>
</AgentHierarchy>
```

**Display Features**:
- Collapsible task groups
- Visual status indicators (spinner for active, checkmark for complete)
- Click to expand agent details
- Real-time updates via WebSocket
- Color coding by task category
- Indentation for hierarchy levels

## Data Flow

### Agent Spawning Flow:
```
1. Agent spawn request initiated
   ↓
2. WhimsicalNameGenerator.generate_name(agent_type)
   ↓
3. Create agent with metadata:
   - whimsical_name
   - initial activity_title
   - task_category
   ↓
4. Register with AgentTracker
   ↓
5. Broadcast creation event via WebSocket
   ↓
6. UI receives update and displays new agent
```

### Activity Update Flow:
```
1. Agent changes activity (e.g., starts writing code)
   ↓
2. Agent calls update_activity("writing_code")
   ↓
3. ActivityTitleManager.get_title(agent_type, "writing_code")
   ↓
4. Update agent metadata
   ↓
5. Broadcast update via WebSocket
   ↓
6. UI updates activity title in real-time
```

## Technology Stack

### Backend:
- **Language**: Python 3.10+
- **Framework**: FastAPI (existing)
- **WebSocket**: FastAPI WebSocket support
- **Storage**: In-memory (existing agent tracker) + enhancements

### Frontend:
- **Framework**: React (assumed from existing UI)
- **State Management**: React Context or Redux
- **WebSocket Client**: Native WebSocket API or socket.io-client
- **Styling**: CSS Modules or Styled Components

### Testing:
- **Unit Tests**: pytest
- **Integration Tests**: pytest + httpx
- **UI Tests**: Jest + React Testing Library
- **E2E Tests**: Playwright or Cypress

## Security Considerations
- **No authentication changes**: Uses existing auth system
- **Rate limiting**: Apply to API endpoints
- **Input validation**: Sanitize activity titles and names
- **WebSocket security**: Validate connections, prevent injection

## Performance Considerations
- **Name generation**: O(1) with hash-based uniqueness check
- **Metadata overhead**: ~100 bytes per agent
- **WebSocket updates**: Throttle to max 10 updates/second
- **UI rendering**: Virtual scrolling for large hierarchies
- **Memory**: Name pool + active names < 10KB total

## Scalability
- **Agent limit**: Current design supports 1000+ concurrent agents
- **WebSocket connections**: Standard FastAPI limits apply
- **Storage**: In-memory suitable for current scale
- **Future**: Can migrate to Redis if needed

## Backward Compatibility
- New fields optional in agent metadata
- Existing agent spawning works unchanged
- API versioning: /api/v1/agents (existing) + /api/v2/agents (enhanced)
- Graceful degradation: UI shows type name if whimsical name missing

## Migration Strategy
1. Deploy backend changes (metadata + name generator)
2. Update agent spawning to include new fields
3. Deploy API endpoints
4. Deploy UI changes
5. Monitor for issues
6. Gradually phase out old display logic

## Error Handling
- **Name generation failure**: Fall back to "Agent-{uuid}"
- **WebSocket disconnect**: Auto-reconnect with exponential backoff
- **API errors**: Display friendly message, retry logic
- **Missing metadata**: Use defaults (show agent type)

## Monitoring & Debugging
- **Whimsical names in logs**: Include in all log messages
- **Activity tracking**: Log all activity changes
- **Performance metrics**: Track API response times
- **WebSocket health**: Monitor connection stability

## Open Issues
None - design is complete and ready for implementation.

## Appendix: Example Whimsical Names by Agent Type

- **Executive Director**: "Napoleon the Coordinator", "Churchill the Strategist"
- **System Architect**: "Gaudi the Designer", "Wren the Planner"
- **Development Manager**: "Tesla the Manager", "Edison the Organizer"
- **Backend Coordinator**: "Turing the Orchestrator", "Lovelace the Planner"
- **Frontend Coordinator**: "Pixel the Designer", "Canvas the Coordinator"
- **Code Writer**: "Hemingway the Coder", "Austen the Developer"
- **Test Coordinator**: "Holmes the Inspector", "Poirot the Tester"
- **TDD Coordinator**: "Feynman the Scientist", "Curie the Experimenter"
