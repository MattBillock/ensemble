# Backend Tasks - Milestone 1: Backend Log Streaming Infrastructure

## Overview
This milestone delivers the foundational backend infrastructure for real-time log streaming via WebSocket. The implementation uses a thread-safe ring buffer to store logs, a custom logging handler to capture Python logs, and a WebSocket endpoint to stream logs to clients with filtering support.

## Architecture Context
- **Framework**: FastAPI (existing, port 8001)
- **WebSocket Infrastructure**: Existing at `/ws/agent-status`, new endpoint at `/ws/logs`
- **Log Storage**: In-memory ring buffer (deque with maxlen=1000)
- **Thread Safety**: threading.Lock for concurrent access
- **Log Format**: Structured JSON with timestamp, level, agent_id, request_id, module, message

---

## Task List

### Task 1: Create LogEntry Data Model
**Description**: Create a Python dataclass for structured log entries with all required fields.

**Acceptance Criteria**:
- [ ] Create `LogEntry` dataclass with fields: timestamp (str), level (str), agent_id (Optional[str]), request_id (Optional[str]), module (str), message (str)
- [ ] Add type hints for all fields
- [ ] LogEntry should be serializable to dict (dataclass provides asdict automatically)
- [ ] Test instantiation with all fields and with optional fields as None

**Dependencies**: None

**Complexity**: Simple

**Implementation Notes**:
- Use Python's `@dataclass` decorator
- Import from `dataclasses` and `typing`
- Timestamp should be ISO 8601 format string

---

### Task 2: Implement LogBuffer Ring Buffer Class
**Description**: Create a thread-safe LogBuffer class with a size-limited ring buffer to store log entries.

**Acceptance Criteria**:
- [ ] Create `LogBuffer` class with `__init__(max_size: int = 1000)`
- [ ] Use `collections.deque` with `maxlen` parameter for ring buffer behavior
- [ ] Include `threading.Lock` for thread-safe operations
- [ ] Implement `add_log(entry: LogEntry) -> None` method with lock protection
- [ ] Implement `get_logs(level, agent_id, request_id, limit) -> List[LogEntry]` with filtering
- [ ] When buffer is full, oldest logs are automatically removed (deque behavior)
- [ ] All access to buffer is thread-safe

**Dependencies**: Task 1 (LogEntry)

**Complexity**: Medium

**Implementation Notes**:
- Ring buffer automatically discards oldest when full (deque handles this)
- Filtering should be case-sensitive for exact matches
- `get_logs` returns most recent `limit` entries after filtering
- Lock acquired for both read and write operations

---

### Task 3: Add WebSocket Subscriber Management to LogBuffer
**Description**: Extend LogBuffer to manage WebSocket subscribers for real-time notifications.

**Acceptance Criteria**:
- [ ] Add `_subscribers: List[WebSocket]` attribute to LogBuffer
- [ ] Implement `subscribe(websocket: WebSocket) -> None` method
- [ ] Implement `unsubscribe(websocket: WebSocket) -> None` method
- [ ] Implement `_notify_subscribers(entry: LogEntry) -> None` method (async)
- [ ] Handle WebSocket disconnection gracefully in notify
- [ ] Auto-remove disconnected subscribers
- [ ] Notification does not block log addition

**Dependencies**: Task 2 (LogBuffer)

**Complexity**: Medium

**Implementation Notes**:
- Subscribers list should also be protected by lock
- Use `asyncio.create_task` to send notifications without blocking
- Catch and ignore errors for disconnected websockets
- Remove failed websockets from subscribers list

---

### Task 4: Create Custom WebSocketLogHandler
**Description**: Implement a custom Python logging.Handler that captures log records and adds them to LogBuffer.

**Acceptance Criteria**:
- [ ] Create `WebSocketLogHandler` class extending `logging.Handler`
- [ ] Accept `LogBuffer` instance in constructor
- [ ] Implement `emit(record: logging.LogRecord)` method
- [ ] Extract timestamp from `record.created` and convert to ISO 8601
- [ ] Extract level from `record.levelname`
- [ ] Extract optional `agent_id` from `record.agent_id` attribute (if present)
- [ ] Extract optional `request_id` from `record.request_id` attribute (if present)
- [ ] Extract module from `record.name`
- [ ] Extract message from `record.getMessage()`
- [ ] Create LogEntry and add to LogBuffer

**Dependencies**: Task 1 (LogEntry), Task 2 (LogBuffer)

**Complexity**: Simple

**Implementation Notes**:
- Use `getattr(record, 'agent_id', None)` for safe attribute access
- Timestamp conversion: `datetime.fromtimestamp(record.created).isoformat()`
- Handler should never raise exceptions (catch all in emit)

---

### Task 5: Implement WebSocket /ws/logs Endpoint
**Description**: Create FastAPI WebSocket endpoint for log streaming with initial batch and real-time updates.

**Acceptance Criteria**:
- [ ] Create `@app.websocket("/ws/logs")` endpoint
- [ ] Accept WebSocket connection
- [ ] Subscribe client to LogBuffer on connection
- [ ] Send initial batch of logs (limit=100) with type="initial"
- [ ] Keep connection alive with 30-second timeout heartbeat
- [ ] Handle client filter update messages (optional for M1)
- [ ] Send heartbeat messages on timeout
- [ ] Unsubscribe client on disconnect
- [ ] Handle WebSocketDisconnect exception gracefully

**Dependencies**: Task 2 (LogBuffer), Task 3 (Subscriber management)

**Complexity**: Medium

**Implementation Notes**:
- Initial message format: `{"type": "initial", "logs": [...]}`
- Log message format: `{"type": "log", "log": {...}}`
- Heartbeat format: `{"type": "heartbeat"}`
- Use `asyncio.wait_for` with 30s timeout for receive
- Use `asdict(log)` to serialize LogEntry to dict

---

### Task 6: Initialize LogBuffer and Handler in FastAPI App
**Description**: Wire up LogBuffer and WebSocketLogHandler in the main FastAPI application.

**Acceptance Criteria**:
- [ ] Create global `log_buffer` instance with max_size=1000
- [ ] Create `WebSocketLogHandler` instance with log_buffer
- [ ] Add handler to root logger or app-specific logger
- [ ] Set appropriate log level (INFO or DEBUG)
- [ ] Handler is initialized before app starts receiving requests
- [ ] Test that Python log statements appear in log_buffer

**Dependencies**: Task 2 (LogBuffer), Task 4 (WebSocketLogHandler)

**Complexity**: Simple

**Implementation Notes**:
- Add to main.py in application startup
- Consider using `@app.on_event("startup")` for initialization
- May need to configure logging format for existing loggers

---

### Task 7: Add Helper to Emit Logs with Agent/Request Context
**Description**: Create utility function to emit logs with agent_id and request_id context.

**Acceptance Criteria**:
- [ ] Create `log_with_context(message, level, agent_id, request_id)` function
- [ ] Function creates LogRecord with extra fields
- [ ] Agent_id and request_id properly attached to record
- [ ] Function works with standard logging levels (DEBUG, INFO, WARNING, ERROR)
- [ ] Provide example usage in docstring

**Dependencies**: Task 4 (WebSocketLogHandler)

**Complexity**: Simple

**Implementation Notes**:
- Use `logging.getLogger().log(level, message, extra={'agent_id': agent_id, 'request_id': request_id})`
- Consider creating a LoggerAdapter subclass for cleaner API
- Document that this should be used instead of direct logger calls when context is available

---

### Task 8: Add Unit Tests for LogEntry
**Description**: Create comprehensive unit tests for LogEntry dataclass.

**Acceptance Criteria**:
- [ ] Test creation with all fields populated
- [ ] Test creation with optional fields as None
- [ ] Test serialization to dict via asdict()
- [ ] Verify field types match annotations
- [ ] Test timestamp format validation (ISO 8601)

**Dependencies**: Task 1 (LogEntry)

**Complexity**: Simple

---

### Task 9: Add Unit Tests for LogBuffer
**Description**: Create comprehensive unit tests for LogBuffer class operations.

**Acceptance Criteria**:
- [ ] Test initialization with default and custom max_size
- [ ] Test add_log adds entry to buffer
- [ ] Test ring buffer behavior (oldest removed when full)
- [ ] Test get_logs with no filters returns all logs
- [ ] Test get_logs with level filter
- [ ] Test get_logs with agent_id filter
- [ ] Test get_logs with request_id filter
- [ ] Test get_logs with multiple filters combined
- [ ] Test get_logs limit parameter
- [ ] Test thread safety with concurrent add_log calls

**Dependencies**: Task 2 (LogBuffer)

**Complexity**: Medium

**Implementation Notes**:
- Use pytest fixtures for LogBuffer instance
- Use threading to test concurrent access
- Mock LogEntry for test data

---

### Task 10: Add Unit Tests for WebSocketLogHandler
**Description**: Create unit tests for custom logging handler.

**Acceptance Criteria**:
- [ ] Test emit creates correct LogEntry
- [ ] Test timestamp extraction and ISO format
- [ ] Test level extraction
- [ ] Test agent_id extraction when present
- [ ] Test agent_id is None when not present
- [ ] Test request_id extraction when present
- [ ] Test request_id is None when not present
- [ ] Test module extraction
- [ ] Test message extraction
- [ ] Test LogEntry added to buffer

**Dependencies**: Task 4 (WebSocketLogHandler)

**Complexity**: Simple

**Implementation Notes**:
- Mock LogBuffer to verify add_log called
- Create mock LogRecord with required attributes
- Test with and without optional attributes

---

### Task 11: Add Integration Tests for WebSocket Endpoint
**Description**: Create integration tests for /ws/logs WebSocket endpoint.

**Acceptance Criteria**:
- [ ] Test successful WebSocket connection
- [ ] Test initial batch of logs received
- [ ] Test real-time log delivery when new logs added
- [ ] Test heartbeat messages received
- [ ] Test graceful disconnection
- [ ] Test multiple concurrent clients
- [ ] Test client unsubscribed on disconnect

**Dependencies**: Task 5 (WebSocket endpoint)

**Complexity**: Complex

**Implementation Notes**:
- Use FastAPI TestClient with WebSocket support
- Use `with client.websocket_connect("/ws/logs")` pattern
- Add logs to buffer and verify received by client
- Test with multiple concurrent websocket connections

---

### Task 12: Add Documentation for Log Streaming API
**Description**: Document the WebSocket log streaming API and usage.

**Acceptance Criteria**:
- [ ] Document WebSocket endpoint URL and connection method
- [ ] Document initial message format
- [ ] Document real-time log message format
- [ ] Document heartbeat message format
- [ ] Document filter message format (for future use)
- [ ] Provide example client code
- [ ] Document LogEntry structure and fields
- [ ] Add inline code comments for complex logic

**Dependencies**: Task 5 (WebSocket endpoint)

**Complexity**: Simple

---

## Task Dependencies Graph

```
Task 1 (LogEntry)
  ├─> Task 2 (LogBuffer)
  │     ├─> Task 3 (Subscriber Management)
  │     │     └─> Task 5 (WebSocket Endpoint)
  │     │           └─> Task 11 (Integration Tests)
  │     │           └─> Task 12 (Documentation)
  │     ├─> Task 4 (WebSocketLogHandler)
  │     │     └─> Task 6 (App Initialization)
  │     │     └─> Task 7 (Context Helper)
  │     │     └─> Task 10 (Handler Tests)
  │     └─> Task 9 (Buffer Tests)
  └─> Task 8 (LogEntry Tests)
```

---

## Implementation Order

**Phase 1: Core Data Structures**
1. Task 1: LogEntry Data Model
2. Task 8: LogEntry Tests
3. Task 2: LogBuffer Ring Buffer
4. Task 9: LogBuffer Tests

**Phase 2: Log Capture**
5. Task 4: WebSocketLogHandler
6. Task 10: WebSocketLogHandler Tests
7. Task 7: Context Helper

**Phase 3: WebSocket Streaming**
8. Task 3: Subscriber Management
9. Task 5: WebSocket Endpoint
10. Task 11: Integration Tests

**Phase 4: Integration & Documentation**
11. Task 6: App Initialization
12. Task 12: Documentation

---

## Testing Strategy

**Unit Tests** (pytest):
- Test each component in isolation
- Mock external dependencies
- Verify thread safety with concurrent operations
- Target 95%+ code coverage

**Integration Tests** (pytest + TestClient):
- Test complete log flow: Python logger → Handler → Buffer → WebSocket
- Test multiple concurrent WebSocket clients
- Test buffer size limits and ring behavior
- Test graceful error handling

**Manual Testing Checklist**:
- [ ] Start FastAPI server and verify no errors
- [ ] Connect WebSocket client to /ws/logs
- [ ] Verify initial batch of logs received
- [ ] Trigger Python log statements
- [ ] Verify real-time logs appear in client
- [ ] Test with multiple concurrent clients
- [ ] Verify buffer respects 1000 entry limit
- [ ] Test heartbeat keeps connection alive

---

## Performance Considerations

1. **Memory Usage**: Ring buffer limited to 1000 entries (~100KB assuming 100 bytes per entry)
2. **Thread Safety**: Lock contention minimized by using deque (thread-safe operations)
3. **WebSocket Overhead**: Notifications use asyncio tasks to avoid blocking
4. **Log Volume**: Handler should have minimal overhead (<1ms per log)
5. **Subscriber Limit**: No hard limit, but consider max ~100 concurrent clients

---

## Rollback Plan

If issues arise:
1. Remove WebSocketLogHandler from logger
2. Disable /ws/logs endpoint
3. Existing functionality unaffected (logs still go to console/file)
4. No database or persistent storage involved

---

## Success Metrics

- [ ] All unit tests pass with 95%+ coverage
- [ ] Integration tests pass for single and multiple clients
- [ ] WebSocket can stream 100+ logs/second without lag
- [ ] Memory usage remains constant at ~100KB for log buffer
- [ ] No performance degradation in agent execution
- [ ] Logs appear in WebSocket client within 100ms of emission

---

## Notes for TDD Coordinator

- Start with Task 1 and work sequentially through phases
- Each task should be implemented via TDD (test first, then implementation)
- LogBuffer thread safety is critical - add concurrent tests
- WebSocket endpoint must handle disconnects gracefully
- Consider using pytest-asyncio for async test support
- Mock WebSocket connections in unit tests, use real TestClient in integration tests
