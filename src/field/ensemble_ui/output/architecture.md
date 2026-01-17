# Recovery Visibility Architecture Proposal

## 1. Architecture Overview

### System Purpose
Design a robust, stateful system for tracking and recovering AI agent swarm executions with persistent state management and comprehensive visibility.

### Architecture Pattern
**Layered Hexagonal Architecture** with clear separation of concerns:
- Persistence Layer (Database)
- State Management Layer
- API Layer
- UI Layer

## 2. Tech Stack

### Backend
- **Language**: Python 3.10+
- **Database**: SQLite (with SQLAlchemy ORM)
- **Web Framework**: FastAPI
- **State Management**: Pydantic models
- **Background Processing**: Asyncio

### Frontend
- **Framework**: React
- **State Management**: Redux
- **UI Library**: Chakra UI
- **HTTP Client**: Axios

### Tools
- **CI/CD**: GitHub Actions
- **Testing**: pytest (backend), Jest (frontend)
- **Containerization**: Docker

## 3. System Components

### Backend Components
1. **Persistence Manager**
   - Responsible for SQLite database interactions
   - Handles state serialization/deserialization
   - Manages database migrations

2. **Session Tracker**
   - Tracks overall swarm session lifecycle
   - Manages agent state reconstruction
   - Handles recovery and resumption logic

3. **API Controller**
   - Exposes RESTful endpoints for session management
   - Handles session listing, retrieval, and actions
   - Implements authentication and authorization

### Frontend Components
1. **Sessions Dashboard**
   - Displays current and historical sessions
   - Shows recovery status and actions
   - Provides detailed session exploration

2. **Session Detail View**
   - Renders comprehensive session information
   - Displays agent hierarchy and individual agent states
   - Supports resume/abandon actions

## 4. Data Flow

```
User Input → API Controller → Session Tracker → Persistence Manager
Persistence Manager → Session Tracker → API Controller → Frontend
```

## 5. Database Schema
```sql
CREATE TABLE swarm_sessions (
    session_id TEXT PRIMARY KEY,
    prompt TEXT,
    status TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    total_cost REAL,
    total_tokens INTEGER,
    family_name TEXT
);

CREATE TABLE agent_states (
    agent_id TEXT PRIMARY KEY,
    session_id TEXT,
    agent_type TEXT,
    status TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    iterations INTEGER,
    model_used TEXT,
    FOREIGN KEY(session_id) REFERENCES swarm_sessions(session_id)
);
```

## 6. API Design

### Session Endpoints
- `GET /api/sessions` - List all sessions
- `GET /api/sessions/{id}` - Get session details
- `POST /api/sessions/{id}/resume` - Resume session
- `POST /api/sessions/{id}/abandon` - Abandon session

## 7. Deployment Strategy
- Containerized deployment using Docker
- CI/CD pipeline with GitHub Actions
- Automated database migrations
- Minimal downtime during updates

## 8. Testing Strategy
- Unit tests for each component
- Integration tests for API endpoints
- State reconstruction tests
- Persistence scenario testing

## 9. Risks and Mitigations
1. **Data Corruption**
   - Mitigation: Use SQLite transactions
   - Implement robust error handling
   - Regular state checksums

2. **Performance Overhead**
   - Mitigation: Optimize database queries
   - Implement efficient serialization
   - Limit historical data retention

## 10. Open Questions
- Long-term storage strategy for historical sessions
- Potential read-replica for large-scale deployments

## 11. Key Trade-offs
- SQLite vs distributed database
- In-memory caching strategies
- Performance vs comprehensive tracking

## Conclusion
A robust, flexible architecture enabling comprehensive session tracking and recovery with minimal complexity and performance impact.