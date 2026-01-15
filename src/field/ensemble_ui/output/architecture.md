# Architecture Document: Requirements Review & Approval Workflow

## 1. System Overview

This document defines the architecture for extending the Ensemble UI and agent system with a requirements review workflow that enables human-in-the-loop control over requirements documents.

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Requirements    │  │ Requirements    │  │ Activity Feed   │  │
│  │ List View       │  │ Detail View     │  │ (Extended)      │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
└───────────┼────────────────────┼────────────────────┼───────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Requirements    │  │ Requirements    │  │ Activity        │  │
│  │ CRUD API        │  │ Actions API     │  │ Ledger API      │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
└───────────┼────────────────────┼────────────────────┼───────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Requirements Document Store                    ││
│  │  (Integrates with existing persistence layer)               ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Agent System                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Requirements    │  │ Requirements    │  │ Requirements    │  │
│  │ Author Agent    │  │ Gatekeeper      │  │ Revision Agent  │  │
│  │ (planning)      │  │ (governance)    │  │ (planning)      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │     Modified Agents (Dev Manager, Coordinators)             ││
│  │     - requires_approved_requirements: true                  ││
│  │     - emit BLOCKED_BY_REQUIREMENTS                          ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## 3. Component Architecture

### 3.1 Frontend Components

```
src/
├── components/
│   └── requirements/
│       ├── RequirementsNav.tsx          # Navigation section entry
│       ├── RequirementsList.tsx         # List view component
│       ├── RequirementsListItem.tsx     # Individual list item
│       ├── RequirementsDetail.tsx       # Detail view container
│       ├── RequirementsContent.tsx      # Left pane - content viewer/editor
│       ├── RequirementsMetadata.tsx     # Right pane - metadata display
│       ├── RequirementsActions.tsx      # Action buttons (approve, reject, etc.)
│       ├── RequirementsStatusBadge.tsx  # Status indicator
│       └── RequirementsFilter.tsx       # Status filter controls
├── hooks/
│   └── useRequirements.ts               # Data fetching hook
├── types/
│   └── requirements.ts                  # TypeScript type definitions
└── api/
    └── requirements.ts                  # API client functions
```

### 3.2 Backend API Structure

```
backend/
├── api/
│   └── routes/
│       └── requirements.py              # API route handlers
├── models/
│   └── requirements.py                  # Pydantic models
├── services/
│   └── requirements_service.py          # Business logic
├── schemas/
│   └── requirements.py                  # Request/response schemas
└── events/
    └── requirements_events.py           # Activity event emission
```

### 3.3 Agent Definitions

```
agents/
├── planning/
│   ├── requirements_author.py           # Generates requirements
│   └── requirements_revision.py         # Handles revision requests
└── governance/
    └── requirements_gatekeeper.py       # Pipeline gating logic
```

## 4. Data Model

### 4.1 RequirementsDocument Model

```python
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class RequirementStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"

class Approval(BaseModel):
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None

class Revision(BaseModel):
    revision_id: str
    content: str
    updated_at: datetime
    updated_by: str

class RequirementsDocument(BaseModel):
    id: str
    title: str
    path: str
    content: str
    status: RequirementStatus = RequirementStatus.DRAFT
    source_agent: str
    related_milestone: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    approval: Optional[Approval] = None
    revision_history: List[Revision] = []
    blocking_agents: List[str] = []  # Agents waiting on this doc
```

### 4.2 Activity Types Extension

```python
class ActivityType(str, Enum):
    # Existing types...
    
    # New requirements-related types
    REQUIREMENTS_CREATED = "REQUIREMENTS_CREATED"
    REQUIREMENTS_UPDATED = "REQUIREMENTS_UPDATED"
    REQUIREMENTS_SUBMITTED_FOR_REVIEW = "REQUIREMENTS_SUBMITTED_FOR_REVIEW"
    REQUIREMENTS_APPROVED = "REQUIREMENTS_APPROVED"
    REQUIREMENTS_REJECTED = "REQUIREMENTS_REJECTED"
    REQUIREMENTS_REVISION_REQUESTED = "REQUIREMENTS_REVISION_REQUESTED"
    PIPELINE_BLOCKED_REQUIREMENTS = "PIPELINE_BLOCKED_REQUIREMENTS"
    PIPELINE_UNBLOCKED_REQUIREMENTS = "PIPELINE_UNBLOCKED_REQUIREMENTS"
```

## 5. API Endpoints

### 5.1 CRUD Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/requirements` | List all requirements (with filtering) |
| GET | `/api/requirements/{id}` | Get single requirement |
| POST | `/api/requirements` | Create new requirement |
| PUT | `/api/requirements/{id}` | Update requirement content |
| DELETE | `/api/requirements/{id}` | Delete requirement |

### 5.2 Status Transitions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/requirements/{id}/submit` | Submit for review |
| POST | `/api/requirements/{id}/approve` | Approve requirement |
| POST | `/api/requirements/{id}/reject` | Reject requirement |
| POST | `/api/requirements/{id}/request-changes` | Request changes |

### 5.3 Query Parameters

```
GET /api/requirements?status=pending_review&source_agent=dev_manager&sort=updated_at
```

## 6. State Machine

```
                    ┌─────────┐
                    │  DRAFT  │
                    └────┬────┘
                         │ submit()
                         ▼
                ┌────────────────┐
                │ PENDING_REVIEW │◄────────┐
                └───────┬────────┘         │
          ┌─────────────┼─────────────┐    │
          │             │             │    │ resubmit()
          ▼             ▼             ▼    │
    ┌──────────┐  ┌──────────┐  ┌──────────┴─┐
    │ APPROVED │  │ REJECTED │  │ REVISIONS  │
    └──────────┘  └──────────┘  │ REQUESTED  │
                                └────────────┘
```

## 7. Pipeline Gating Flow

```
1. Agent declares: requires_approved_requirements: true
2. Agent checks requirements store for approved status
3. If not approved:
   a. Agent emits BLOCKED_BY_REQUIREMENTS event
   b. Agent pauses execution
   c. Gatekeeper monitors for approval
4. On approval:
   a. Gatekeeper emits PIPELINE_UNBLOCKED_REQUIREMENTS
   b. Blocked agents resume
```

## 8. Integration Points

### 8.1 Activity Feed Integration
- All state changes emit activities via existing ActivityService
- Activities include requirements_doc_id, agent_id, user_id, note fields
- Activities visible in existing Activity Feed UI

### 8.2 Agent System Integration
- New agents use existing spawn_agent mechanism
- Agents declare requirements dependencies in their configuration
- Gatekeeper uses existing Action Ledger to monitor events

### 8.3 Persistence Integration
- RequirementsDocument stored via existing persistence layer
- Revision history maintained with each update
- Consistent with existing data patterns

## 9. Security Considerations

- Single-user context (no RBAC per requirements)
- All actions logged for audit trail
- Input validation on all API endpoints
- Markdown content sanitized before rendering

## 10. Performance Considerations

- List endpoint: < 500ms (NF1)
- Optimistic updates for edit mode (NF2)
- Pagination for large document sets
- Efficient revision history storage

## 11. Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, TailwindCSS, TypeScript |
| Backend | Python, FastAPI |
| Data | Existing persistence layer |
| Events | Existing Action Ledger |
| Agents | Existing agent spawning system |
