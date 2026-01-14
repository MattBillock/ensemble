# Architecture Document: Failed Task Cleanup System

**Project**: Failed Task Cleanup System  
**Date**: 2025-01-13  
**Architecture Pattern**: Modular Service-Oriented Architecture

---

## 1. Executive Summary

This document defines the architecture for a Failed Task Cleanup System that provides reliable failure capture, storage, and cleanup capabilities for task management. The system captures failure diagnostics without AI tool dependencies and links them to task records for easy access and review.

**Architecture Pattern**: Modular Service-Oriented Architecture  
**Technology Stack**: Python 3.x, File System Storage, Existing Task Tracking Integration  
**Core Principle**: Reliability - failure capture must never fail

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Task Management System                    │
│                     (Existing System)                        │
└───────────────┬─────────────────────────────┬───────────────┘
                │                             │
                ▼                             ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│  Failure Capture Module   │   │   Cleanup API Module      │
│  - Exception handling     │   │   - Cleanup operations    │
│  - File creation          │   │   - Retention policy      │
│  - No AI dependencies     │   │   - Batch processing      │
└──────────┬────────────────┘   └───────────┬───────────────┘
           │                                 │
           ▼                                 ▼
┌───────────────────────────────────────────────────────────┐
│              Failure Storage (File System)                 │
│           /output/failures/failure_<id>_<ts>.txt          │
└───────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────┐
│                    Web UI Integration                      │
│               - Display failure links                      │
│               - Serve failure files                        │
└───────────────────────────────────────────────────────────┘
```

### 2.2 Component Architecture

#### **Component 1: Failure Capture Module**
**Purpose**: Capture task failure diagnostics and store them to text files without AI dependencies.

**Responsibilities**:
- Intercept task failures via exception handling
- Extract diagnostic information (stack trace, error message, context)
- Generate structured failure description files
- Create files immediately upon failure
- Work reliably without AI tool availability

**Key Classes**:
```python
class FailureCapture:
    def capture_failure(task_id: str, exception: Exception, context: dict) -> str
    def _format_failure_report(task_id: str, exception: Exception, context: dict) -> str
    def _write_failure_file(task_id: str, content: str) -> str
    def _generate_filename(task_id: str) -> str
```

**Failure File Format**:
```
TASK FAILURE REPORT
===================
Task ID: <task_id>
Timestamp: <ISO 8601 timestamp>
Task Type: <agent_type or task_type>
Status: failed

ERROR MESSAGE:
<error message>

STACK TRACE:
<full stack trace if available>

TASK CONTEXT:
<task parameters, input data, etc.>

ADDITIONAL DIAGNOSTICS:
<any other captured information>
```

**File Naming Convention**: `failure_<task_id>_<timestamp>.txt`  
**Storage Location**: `/output/failures/`

#### **Component 2: Failure Linking Service**
**Purpose**: Link failed tasks to their failure description files in the task tracking system.

**Responsibilities**:
- Store failure file path in task record
- Retrieve failure file path for a given task
- Validate file existence and accessibility
- Provide API for web UI integration

**Key Classes**:
```python
class FailureLinker:
    def link_failure_to_task(task_id: str, failure_file_path: str) -> bool
    def get_failure_file_path(task_id: str) -> Optional[str]
    def validate_failure_file(file_path: str) -> bool
```

**Data Model Enhancement**:
```python
# Extension to existing task tracking
task_record = {
    "task_id": str,
    "status": str,
    "failure_file_path": Optional[str],  # NEW FIELD
    "failure_timestamp": Optional[datetime]  # NEW FIELD
}
```

#### **Component 3: Cleanup API Module**
**Purpose**: Provide APIs for cleaning up failed tasks while preserving failure files.

**Responsibilities**:
- Clean up individual failed tasks by task ID
- Batch cleanup by date/age
- Preserve failure files during cleanup
- Remove tasks from active state
- Implement retention policies

**Key Classes**:
```python
class CleanupAPI:
    def cleanup_task(task_id: str) -> CleanupResult
    def cleanup_tasks_before_date(cutoff_date: datetime) -> BatchCleanupResult
    def cleanup_tasks_by_status(status: str, age_days: int) -> BatchCleanupResult
    def _preserve_failure_file(task_id: str) -> bool
    def _remove_from_active_tasks(task_id: str) -> bool
```

**Cleanup Result Model**:
```python
@dataclass
class CleanupResult:
    task_id: str
    success: bool
    failure_file_preserved: bool
    error_message: Optional[str]

@dataclass
class BatchCleanupResult:
    total_tasks: int
    successful_cleanups: int
    failed_cleanups: int
    cleanup_results: List[CleanupResult]
```

**Retention Policy Configuration**:
```python
RETENTION_POLICY = {
    "default_retention_days": 90,
    "preserve_failure_files": True,
    "archive_on_cleanup": False
}
```

#### **Component 4: Web UI Integration**
**Purpose**: Display failure information and links in the web UI.

**Responsibilities**:
- Display failed tasks with failure indicators
- Provide clickable links to failure files
- Serve failure file content
- Handle missing/invalid files gracefully

**API Endpoints**:
```python
# Backend API
GET  /api/tasks/{task_id}/failure       # Get failure file path
GET  /api/failures/{failure_file}       # Serve failure file content
POST /api/cleanup/task/{task_id}        # Cleanup single task
POST /api/cleanup/batch                 # Batch cleanup
```

**UI Components**:
- Failed task badge/indicator
- Failure details modal/popup
- Link to download failure file
- Cleanup action buttons

---

## 3. Data Flow

### 3.1 Failure Capture Flow

```
Task Execution
      ↓
  Exception Occurs
      ↓
[FailureCapture.capture_failure()]
      ↓
Extract: task_id, exception, context
      ↓
Format failure report (structured text)
      ↓
Generate filename: failure_<task_id>_<timestamp>.txt
      ↓
Write to: /output/failures/
      ↓
[FailureLinker.link_failure_to_task()]
      ↓
Store failure_file_path in task record
      ↓
Task marked as "failed"
```

### 3.2 Cleanup Flow

```
Cleanup Request (API or Manual)
      ↓
[CleanupAPI.cleanup_task(task_id)]
      ↓
Validate task exists and is failed
      ↓
Get failure_file_path from task record
      ↓
Verify failure file exists
      ↓
Remove task from active task list/database
      ↓
Preserve failure file (do NOT delete)
      ↓
Return CleanupResult
```

### 3.3 Web UI Display Flow

```
User views task list
      ↓
UI requests task data with failure info
      ↓
Backend includes failure_file_path if present
      ↓
UI displays failed tasks with link icon
      ↓
User clicks failure link
      ↓
GET /api/failures/{failure_file}
      ↓
Backend serves failure file content
      ↓
UI displays in modal/new tab
```

---

## 4. Module Structure

```
failed_task_cleanup/
├── __init__.py
├── failure_capture.py      # FailureCapture class
├── failure_linker.py        # FailureLinker class
├── cleanup_api.py           # CleanupAPI class
├── models.py                # Data models (CleanupResult, etc.)
└── config.py                # Configuration (retention policy, paths)

web_ui/
├── api/
│   ├── failure_endpoints.py  # API endpoints for failures
│   └── cleanup_endpoints.py  # API endpoints for cleanup
└── components/
    ├── FailureIndicator.tsx  # UI component for failure display
    └── FailureModal.tsx       # UI component for failure details

tests/
├── test_failure_capture.py
├── test_failure_linker.py
├── test_cleanup_api.py
└── test_integration.py
```

---

## 5. Error Handling Strategy

### 5.1 Failure Capture Error Handling
**Principle**: Failure capture must never fail

**Strategy**:
- Wrap all file writes in try-except
- If file write fails, log to stderr as fallback
- If directory creation fails, log to /tmp as fallback
- Never raise exceptions from capture code

```python
def capture_failure(task_id, exception, context):
    try:
        # Primary: write to /output/failures/
        write_failure_file(task_id, exception, context)
    except Exception as e:
        try:
            # Fallback 1: write to /tmp/failures/
            write_to_tmp(task_id, exception, context)
        except Exception as e2:
            # Fallback 2: log to stderr
            sys.stderr.write(f"CRITICAL: Failure capture failed: {e2}\n")
```

### 5.2 Cleanup Error Handling

**Strategy**:
- Validate task exists before cleanup
- Check file existence before preserving
- Make cleanup operations idempotent
- Return detailed error messages
- Continue batch processing on individual failures

---

## 6. Integration Points

### 6.1 Task Tracking System Integration

**Assumptions**:
- Existing task tracking system has task records
- Can extend task model with new fields
- Can update task status and metadata

**Integration**:
```python
# Extend existing task tracking
from task_tracking import Task

# Add fields to Task model
Task.add_field("failure_file_path", Optional[str])
Task.add_field("failure_timestamp", Optional[datetime])

# Hook into task failure event
def on_task_failure(task: Task, exception: Exception):
    failure_file = FailureCapture.capture_failure(
        task.task_id, exception, task.context
    )
    FailureLinker.link_failure_to_task(task.task_id, failure_file)
    task.status = "failed"
    task.save()
```

### 6.2 Web UI Integration

**Assumptions**:
- Existing web UI framework (React, Vue, etc.)
- Can add new API endpoints
- Can add new UI components

**Integration**:
- Add failure endpoints to API router
- Create FailureIndicator component
- Update task list to show failure status
- Add cleanup buttons to admin interface

---

## 7. Testing Strategy

### 7.1 Unit Tests
- **test_failure_capture.py**: Test file creation, formatting, error handling
- **test_failure_linker.py**: Test linking, retrieval, validation
- **test_cleanup_api.py**: Test single cleanup, batch cleanup, retention
- **test_models.py**: Test data models

### 7.2 Integration Tests
- **test_integration.py**: Test full failure capture → link → display → cleanup flow
- Test with real exception scenarios
- Test with file system failures (mocked)
- Test cleanup preserves files

### 7.3 Performance Tests
- Test batch cleanup with 1000+ tasks
- Verify < 5 seconds for batch operations
- Test concurrent failure captures

### 7.4 Reliability Tests
- Test failure capture when disk full
- Test failure capture when permissions denied
- Test cleanup when files missing
- Verify fallback mechanisms work

---

## 8. Configuration

### 8.1 File Paths
```python
FAILURE_STORAGE_BASE = "/Users/mattbillock/Development/ai_exploration/ensemble/src/field/ensemble_ui/output/failures/"
FALLBACK_STORAGE = "/tmp/failures/"
```

### 8.2 Retention Policy
```python
RETENTION_POLICY = {
    "default_retention_days": 90,
    "max_failure_files": 10000,
    "archive_old_files": False,
    "preserve_on_cleanup": True
}
```

### 8.3 File Format
```python
FILENAME_PATTERN = "failure_{task_id}_{timestamp}.txt"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
```

---

## 9. Security Considerations

### 9.1 File Access
- Validate file paths to prevent path traversal
- Sanitize task IDs before using in filenames
- Restrict API access to authenticated users
- Log all cleanup operations for audit

### 9.2 Data Privacy
- Failure files may contain sensitive context data
- Consider PII redaction if needed
- Implement proper access controls

---

## 10. Performance Considerations

### 10.1 File System Performance
- Expected: ~100 failure files per day
- Storage: ~10KB per file
- Total: ~1MB per day, ~365MB per year
- Cleanup: Process 1000 tasks in < 5 seconds

### 10.2 Optimization Opportunities
- Index failure files by date for faster cleanup
- Cache failure file paths in memory
- Batch file operations for cleanup

---

## 11. Deployment

### 11.1 Installation
1. Create failures directory: `mkdir -p /output/failures/`
2. Install module: `pip install failed_task_cleanup`
3. Update task tracking to include failure fields
4. Add failure capture hooks to task execution
5. Deploy API endpoints
6. Deploy UI components

### 11.2 Verification
1. Trigger a test failure
2. Verify failure file created
3. Verify task linked to file
4. Verify UI displays failure
5. Test cleanup API
6. Verify failure file preserved after cleanup

---

## Document Control

**Version**: 1.0  
**Status**: Approved  
**Last Updated**: 2025-01-13
