# Architecture: Backend Logs Tab & Agent Definition Explorer

## Overview
This architecture extends the existing Ensemble UI to add a new "Logs & Agents" tab with real-time log streaming and agent definition management capabilities.

## System Context

### Existing Components (Do Not Modify)
- **FastAPI Backend** (`backend/main.py`): Port 8001, existing WebSocket at `/ws/agent-status`
- **React Frontend** (`frontend/src/App.jsx`): React Bootstrap, dark theme
- **Existing API Endpoints**:
  - `GET /api/agents` - List all agent definitions
  - `GET /api/agents/{tier}/{name}` - Get agent content
  - `POST /api/agents/update` - Update agent definition with backup

### New Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                 │
├─────────────────────────────────────────────────────────────────┤
│  App.jsx                                                         │
│  ├── TabNavigation (new)                                        │
│  ├── MainView (existing content)                                │
│  └── LogsAgentsTab (new)                                        │
│      ├── LogStreamPanel.jsx                                     │
│      │   ├── WebSocket connection to /ws/logs                   │
│      │   ├── Log display with auto-scroll                       │
│      │   └── Filter controls                                    │
│      └── AgentExplorerPanel.jsx                                 │
│          ├── AgentExplorer.jsx (tree view)                      │
│          └── AgentDefinitionViewer.jsx (view/edit)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Backend                                  │
├─────────────────────────────────────────────────────────────────┤
│  main.py                                                         │
│  ├── LogBuffer (new class)                                      │
│  │   ├── ring_buffer: deque(maxlen=1000)                        │
│  │   ├── add_log(entry)                                         │
│  │   └── get_filtered_logs(level, agent_id, request_id)         │
│  ├── LogStreamHandler (new)                                     │
│  │   └── Captures Python logging → LogBuffer                    │
│  └── /ws/logs endpoint (new)                                    │
│      ├── Accept WebSocket connection                            │
│      ├── Stream logs from LogBuffer                             │
│      └── Support filter parameters                              │
└─────────────────────────────────────────────────────────────────┘
```

## Component Specifications

### 1. Backend: LogBuffer Class

```python
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import threading

@dataclass
class LogEntry:
    timestamp: str
    level: str
    agent_id: Optional[str]
    request_id: Optional[str]
    module: str
    message: str

class LogBuffer:
    def __init__(self, max_size: int = 1000):
        self._buffer = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._subscribers = []  # WebSocket connections
    
    def add_log(self, entry: LogEntry) -> None:
        with self._lock:
            self._buffer.append(entry)
        # Notify subscribers
        self._notify_subscribers(entry)
    
    def get_logs(self, 
                 level: Optional[str] = None,
                 agent_id: Optional[str] = None,
                 request_id: Optional[str] = None,
                 limit: int = 100) -> List[LogEntry]:
        with self._lock:
            logs = list(self._buffer)
        
        # Apply filters
        if level:
            logs = [l for l in logs if l.level == level]
        if agent_id:
            logs = [l for l in logs if agent_id in (l.agent_id or '')]
        if request_id:
            logs = [l for l in logs if request_id in (l.request_id or '')]
        
        return logs[-limit:]
```

### 2. Backend: Custom Logging Handler

```python
import logging

class WebSocketLogHandler(logging.Handler):
    def __init__(self, log_buffer: LogBuffer):
        super().__init__()
        self.log_buffer = log_buffer
    
    def emit(self, record: logging.LogRecord):
        entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            agent_id=getattr(record, 'agent_id', None),
            request_id=getattr(record, 'request_id', None),
            module=record.name,
            message=record.getMessage()
        )
        self.log_buffer.add_log(entry)
```

### 3. Backend: WebSocket Endpoint

```python
@app.websocket("/ws/logs")
async def log_stream_ws(websocket: WebSocket):
    await websocket.accept()
    log_buffer.subscribe(websocket)
    
    try:
        # Send initial batch of logs
        initial_logs = log_buffer.get_logs(limit=100)
        await websocket.send_json({
            "type": "initial",
            "logs": [asdict(log) for log in initial_logs]
        })
        
        # Keep connection alive, send new logs as they arrive
        while True:
            try:
                # Receive filter updates from client
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
                # Handle filter change requests
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        pass
    finally:
        log_buffer.unsubscribe(websocket)
```

### 4. Frontend: LogStreamPanel Component

```jsx
// LogStreamPanel.jsx
const LogStreamPanel = () => {
  const [logs, setLogs] = useState([]);
  const [filters, setFilters] = useState({
    level: null,
    search: '',
    isPaused: false
  });
  const [autoScroll, setAutoScroll] = useState(true);
  const ws = useRef(null);
  const logsEndRef = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket('ws://localhost:8001/ws/logs');
    
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'initial') {
        setLogs(data.logs);
      } else if (data.type === 'log') {
        if (!filters.isPaused) {
          setLogs(prev => [...prev.slice(-999), data.log]);
        }
      }
    };
    
    return () => ws.current?.close();
  }, []);

  // Filter logs client-side
  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      if (filters.level && log.level !== filters.level) return false;
      if (filters.search && 
          !log.message.includes(filters.search) &&
          !log.agent_id?.includes(filters.search) &&
          !log.request_id?.includes(filters.search)) return false;
      return true;
    });
  }, [logs, filters]);

  return (
    <Card bg="dark" text="light">
      <Card.Header>
        {/* Filter controls */}
      </Card.Header>
      <Card.Body>
        {/* Log entries */}
      </Card.Body>
    </Card>
  );
};
```

### 5. Frontend: AgentExplorer Component

```jsx
// AgentExplorer.jsx
const AgentExplorer = ({ onSelectAgent }) => {
  const [agents, setAgents] = useState({});
  const [expandedDirs, setExpandedDirs] = useState(new Set(['leadership']));
  const [selectedAgent, setSelectedAgent] = useState(null);

  useEffect(() => {
    // Fetch agents from /api/agents
    fetchAgents().then(data => {
      // Group by tier
      const grouped = data.agents.reduce((acc, agent) => {
        if (!acc[agent.tier]) acc[agent.tier] = [];
        acc[agent.tier].push(agent);
        return acc;
      }, {});
      setAgents(grouped);
    });
  }, []);

  return (
    <div className="agent-explorer">
      {Object.entries(agents).map(([tier, tierAgents]) => (
        <div key={tier}>
          <div onClick={() => toggleDir(tier)}>
            {expandedDirs.has(tier) ? '📂' : '📁'} {tier}/
          </div>
          {expandedDirs.has(tier) && tierAgents.map(agent => (
            <div 
              key={agent.path}
              onClick={() => onSelectAgent(agent)}
              className={selectedAgent === agent.path ? 'selected' : ''}
            >
              📄 {agent.name}.md
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};
```

### 6. Frontend: AgentDefinitionViewer Component

```jsx
// AgentDefinitionViewer.jsx
const AgentDefinitionViewer = ({ agent }) => {
  const [content, setContent] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [status, setStatus] = useState(null);

  useEffect(() => {
    if (agent) {
      fetchAgentContent(agent.tier, agent.name).then(data => {
        setContent(data.content);
        setEditContent(data.content);
      });
    }
  }, [agent]);

  const handleSave = async () => {
    try {
      const result = await updateAgent(agent.path, editContent);
      setStatus({ type: 'success', message: `Saved! Backup: ${result.backup}` });
      setContent(editContent);
      setIsEditing(false);
    } catch (err) {
      setStatus({ type: 'error', message: err.message });
    }
  };

  return (
    <Card bg="dark" text="light">
      <Card.Header>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>{agent?.path || 'Select an agent'}</span>
          <ButtonGroup size="sm">
            <Button 
              variant={isEditing ? 'secondary' : 'primary'}
              onClick={() => setIsEditing(!isEditing)}
            >
              {isEditing ? 'Cancel' : 'Edit'}
            </Button>
            {isEditing && (
              <Button variant="success" onClick={handleSave}>Save</Button>
            )}
          </ButtonGroup>
        </div>
      </Card.Header>
      <Card.Body>
        {isEditing ? (
          <Form.Control
            as="textarea"
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            style={{ height: '400px', fontFamily: 'monospace' }}
          />
        ) : (
          <pre style={{ whiteSpace: 'pre-wrap' }}>{content}</pre>
        )}
      </Card.Body>
    </Card>
  );
};
```

## Data Flow

### Log Streaming Flow
```
Python Logger → WebSocketLogHandler → LogBuffer → /ws/logs → LogStreamPanel
```

### Agent Definition Flow
```
AgentExplorer ──onClick──> fetchAgentContent ──> AgentDefinitionViewer
                                                        │
                                                   [Edit Mode]
                                                        │
                                                   Save Click
                                                        │
                                                        ▼
                                               POST /api/agents/update
                                                        │
                                                        ▼
                                              Backup + Write + Validate
```

## File Structure

```
frontend/src/
├── App.jsx                          # Modified: Add tab navigation
├── components/
│   ├── LogStreamPanel.jsx           # NEW
│   ├── AgentExplorer.jsx            # NEW
│   ├── AgentDefinitionViewer.jsx    # NEW
│   └── ... (existing components)
└── services/
    └── api.js                       # Modified: Add log stream helpers

backend/
└── main.py                          # Modified: Add LogBuffer, /ws/logs
```

## Styling Guidelines

Match existing dark theme:
- Background: `#1a1d29`
- Card background: `#242836`
- Border: `#3a3f52`
- Text: `#e4e6eb`
- Muted text: `#9ca3af`

Log level colors:
- DEBUG: `#6b7280` (gray)
- INFO: `#60a5fa` (blue)
- WARNING: `#fbbf24` (yellow)
- ERROR: `#ef4444` (red)

## API Specifications

### New WebSocket Endpoint

**`WS /ws/logs`**

Connection establishes log streaming. Client can send filter updates:

```json
// Client → Server (filter update)
{
  "type": "filter",
  "level": "ERROR",          // Optional
  "agent_id": "exec_dir_1",  // Optional
  "request_id": "abc123"     // Optional
}
```

```json
// Server → Client (log entry)
{
  "type": "log",
  "log": {
    "timestamp": "2025-01-11T03:25:00.000",
    "level": "INFO",
    "agent_id": "exec_dir_1",
    "request_id": "abc12345",
    "module": "__main__",
    "message": "Starting agent execution"
  }
}
```

### Existing Endpoints (No Changes)
- `GET /api/agents` - Already returns agent list
- `GET /api/agents/{tier}/{name}` - Already returns content
- `POST /api/agents/update` - Already handles update with backup

## Error Handling

1. **WebSocket disconnection**: Auto-reconnect with exponential backoff
2. **Failed agent save**: Show error, content preserved in textarea
3. **Invalid agent definition**: Backend validates, returns error, restores backup

## Security Considerations

1. Log buffer size limited to 1000 entries (memory protection)
2. Agent file updates validated before write
3. Automatic backup before any modification
4. No new authentication required (inherits existing auth if any)

## Testing Strategy

1. **Backend Unit Tests**:
   - LogBuffer add/get/filter operations
   - WebSocket endpoint connection/disconnection

2. **Frontend Tests**:
   - LogStreamPanel renders and filters
   - AgentExplorer tree expansion
   - AgentDefinitionViewer save/revert

3. **Integration Tests**:
   - End-to-end log streaming
   - Agent edit → save → verify backup
