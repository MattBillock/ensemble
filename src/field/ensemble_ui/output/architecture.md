# Activity Tracking Fixes - System Architecture

## A) Architecture Overview
A focused, surgical fix to the Ensemble UI activity tracking system. The architecture addresses three specific bugs preventing file generation tracking and request count updates with minimal system disruption and maximum backward compatibility.

## B) Current System Analysis

### Existing Components (Working Correctly)
- **ActivityTracker** (`src/runtime/agents/activity_tracker.py`) - Core tracking logic works
- **Activity APIs** (`src/field/ensemble_ui/backend/main.py`) - Endpoints correctly query tracker
- **Frontend Display** - UI correctly consumes API data
- **Agent Execution** - Agents successfully create files and complete tasks

### Problem Areas (Requiring Fixes)
1. **WriteFileTool** - Doesn't record file generation to ActivityTracker
2. **Request Counting** - `increment_request_counts()` method never called
3. **File Discovery** - Limited to output directory only

## C) Proposed Architecture Changes

### 1. Enhanced WriteFileTool with Context Propagation

**Current Architecture:**
```
AgentRuntime → ToolRegistry → WriteFileTool → File System
                                    ↓
                              (No tracking)
```

**Fixed Architecture:**
```
AgentRuntime → ToolRegistry → WriteFileTool → File System
     ↓              ↓              ↓
 Context Info → Tracking Params → ActivityTracker.record_file_generated()
```

**Implementation Pattern:**
- **Context Injection**: Pass agent_id, request_id, agent_name through tool construction
- **Optional Parameters**: Maintain backward compatibility with optional tracking parameters
- **Error Isolation**: Wrap tracking calls in try-catch to prevent tool failures

### 2. Auto-Increment Request Counters

**Pattern:** Hook into existing activity recording methods

```
record_agent_started() → increment_request_counts(agents=+1)
record_file_generated() → increment_request_counts(files=+1) 
record_git_commit() → increment_request_counts(commits=+1)
```

**Thread Safety:** Leverage existing ActivityTracker synchronization mechanisms

### 3. Enhanced File Discovery (Optional Enhancement)

**Current:** Scan output directory only
**Enhanced:** Scan multiple directories with intelligent filtering

```
File Discovery Strategy:
- Output directory (priority 1)
- Test directories (priority 2) 
- Source directories (priority 3)
- Filter by file extensions and relevance
```

## D) Technical Implementation Details

### WriteFileTool Modification
```python
class WriteFileTool:
    def __init__(
        self, 
        agent_definition: Optional["AgentDefinition"] = None,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        # Store tracking context
        self.tracking_context = {
            'agent_id': agent_id,
            'agent_name': agent_name or (agent_definition.name if agent_definition else 'unknown'),
            'request_id': request_id
        }
    
    def execute(self, file_path: str, content: str):
        # ... existing file write logic ...
        
        # Add tracking after successful write
        if self.tracking_context['agent_id'] and self.tracking_context['request_id']:
            self._record_file_generation(file_path, content)
```

### ToolRegistry Context Injection
```python
def default(agent_definition, agent_id=None, request_id=None):
    registry = ToolRegistry()
    
    # Pass context to tools that support it
    registry.register(WriteFileTool(
        agent_definition=agent_definition,
        agent_id=agent_id,
        agent_name=agent_definition.name if agent_definition else None,
        request_id=request_id
    ))
    
    return registry
```

### ActivityTracker Auto-Increment Integration
```python
def record_file_generated(self, agent_id, agent_name, request_id, file_path, ...):
    # ... existing record logic ...
    
    # Auto-increment file count
    self.increment_request_counts(request_id, files=1)
```

## E) Data Flow Architecture

### Before (Broken):
```
Agent Executes → WriteFileTool → File Created ✓
                      ↓
                (No tracking) ✗
                      ↓
              ActivityTracker (empty) ✗
                      ↓
                 API Returns [] ✗
                      ↓
                UI Shows "No Activity" ✗
```

### After (Fixed):
```
Agent Executes → WriteFileTool → File Created ✓
                      ↓              ↓
                Tracking Context → ActivityTracker.record_file_generated() ✓
                      ↓              ↓
                Auto-increment → Request Counters Updated ✓
                      ↓
                 API Returns [files...] ✓
                      ↓
                UI Shows Real Activity ✓
```

## F) Backward Compatibility Strategy

### Design Principles:
1. **Optional Parameters** - All tracking parameters have defaults
2. **Graceful Degradation** - Tools work without tracking context
3. **Error Isolation** - Tracking failures don't break tool execution
4. **Existing Test Compatibility** - No changes to existing test interfaces

### Migration Path:
- **Phase 1**: Add optional tracking parameters
- **Phase 2**: Update calling code to pass context
- **Phase 3**: Monitor and validate tracking works
- **Phase 4**: Remove old parameter patterns (future)

## G) Risk Mitigation

### Import Cycles
**Risk**: ActivityTracker import in tools.py creates circular dependency
**Mitigation**: Use local imports within methods, lazy loading

### Performance Impact
**Risk**: Tracking adds overhead to file operations
**Mitigation**: Minimal tracking code, efficient data structures

### Thread Safety
**Risk**: Concurrent access to ActivityTracker
**Mitigation**: Leverage existing thread-safe implementation

### Error Propagation
**Risk**: Tracking errors break tool execution
**Mitigation**: Comprehensive try-catch around all tracking calls

## H) Testing Strategy

### Unit Tests:
- WriteFileTool with and without tracking context
- ActivityTracker increment methods
- ToolRegistry context propagation

### Integration Tests:
- End-to-end agent execution with tracking
- API endpoint data validation
- UI display verification

### Regression Tests:
- All existing tool tests continue passing
- Backward compatibility validation

## I) Deployment Considerations

### Zero-Downtime Deployment:
- Changes are additive and backward compatible
- No API endpoint modifications required
- No database schema changes needed

### Rollback Strategy:
- Simple code revert restores original behavior
- No data migration concerns

## J) Success Metrics

### Primary:
- `/api/activity/files` returns files created by agents
- `/api/activity/timeline` shows non-zero counts for active requests

### Secondary:
- Zero regression in existing functionality
- All tests pass
- Performance overhead < 5%

## K) Future Enhancements

### Potential Additions:
- More granular file type detection
- Activity analytics and reporting
- Historical activity trending
- Performance monitoring integration

### Architecture Scalability:
- Current design supports future activity types
- Extensible tracking context system
- Plugin architecture for custom tracking

---
*Architecture Design: 2026-01-14*
*Project: Activity Tracking Fixes*
*System Architect: AI Assistant*