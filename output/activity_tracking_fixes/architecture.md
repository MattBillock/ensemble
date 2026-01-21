# Activity Tracking Fixes - Architecture Proposal

## Architecture Overview

### Problem Context
The current system lacks accurate tracking of agent activities, specifically file generation and request counts. The architecture proposal addresses this by introducing lightweight, non-intrusive tracking mechanisms that maintain existing system flexibility.

### Architectural Pattern
**Pattern**: Decorator/Wrapper Pattern with Context Propagation
- Existing tools remain unchanged
- Tracking logic added as optional context
- Backward compatibility preserved

## Tech Stack
- **Language**: Python 3.9+
- **Frameworks**: No additional frameworks required
- **Libraries**: 
  - Existing project utilities
  - Standard Python logging

## System Components

### 1. WriteFileTool Enhancement
```python
class WriteFileTool:
    def __init__(self, 
        agent_id=None, 
        agent_name=None, 
        request_id=None
    ):
        self.tracking_context = {
            'agent_id': agent_id,
            'agent_name': agent_name,
            'request_id': request_id
        }
    
    def execute(self, file_path, content):
        # Original file writing logic
        original_write_result = write_file(file_path, content)
        
        # Optional activity tracking
        if self.tracking_context.get('agent_id'):
            ActivityTracker.record_file_generated(
                file_path=file_path,
                **self.tracking_context
            )
        
        return original_write_result
```

### 2. ActivityTracker Enhancements
```python
class ActivityTracker:
    @classmethod
    def record_file_generated(cls, file_path, agent_id, agent_name, request_id):
        # Record file generation event
        cls._increment_request_counts(
            files=1, 
            agent_id=agent_id
        )
        
        # Log file generation details
        cls._log_file_event(
            file_path=file_path,
            agent_id=agent_id,
            agent_name=agent_name,
            request_id=request_id
        )
```

## File/Directory Structure
```
src/runtime/agents/
├── tools.py           # WriteFileTool modifications
├── activity_tracker.py  # Enhanced tracking logic
└── __init__.py
```

## Data Flow
1. Tool initialized with optional tracking context
2. File generation occurs
3. If context provided, activity recorded
4. Request counts automatically incremented

## Deployment Strategy
- In-place upgrade
- No database schema changes
- No API endpoint modifications
- Minimal runtime overhead

## Testing Strategy
1. **Unit Tests**:
   - WriteFileTool with/without tracking context
   - ActivityTracker increment methods
   - Tracking context propagation

2. **Integration Tests**:
   - Verify file tracking across different agent scenarios
   - Check request count increments
   - Validate backward compatibility

## Risks and Mitigations
- **Risk**: Potential performance overhead
  - **Mitigation**: Lightweight tracking, optional context
- **Risk**: Circular imports
  - **Mitigation**: Local imports, careful module design

## Alternatives Considered
1. Full instrumentation framework
   - **Pros**: Comprehensive tracking
   - **Cons**: Overengineered, complex implementation
2. Centralized logging solution
   - **Pros**: Standardized logging
   - **Cons**: Less flexible, more dependencies

## Open Questions
- Performance impact of tracking calls
- Granularity of tracking information needed

## Key Architectural Decisions
1. Optional tracking context
2. Minimal changes to existing tools
3. Lightweight, non-intrusive tracking mechanism

## Compatibility
- Works with existing agent infrastructure
- No breaking changes
- Gradual, opt-in tracking enhancement