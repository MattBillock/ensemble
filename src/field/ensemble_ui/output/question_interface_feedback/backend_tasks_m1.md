# Backend Tasks - Milestone 1: Backend Foundation & Storage

## Milestone Overview
Establish the core backend infrastructure for question storage, retrieval, and management. This milestone focuses on creating the foundational data layer and business logic for the question interface feature.

**Milestone Goal**: Create a robust, persistent storage system for questions with full CRUD operations, following the established feedback pattern architecture.

---

## Architecture Assumptions

Based on the requirements document and default backend standards:

- **Storage**: JSON files in `~/.ensemble/questions/` directory (matches feedback pattern)
- **Framework**: Python FastAPI (existing backend)
- **Data Format**: JSON with atomic writes for reliability
- **ID Generation**: UUID4 for unique question identifiers
- **Validation**: Pydantic models for data validation
- **Testing**: pytest with TDD approach, aim for >80% coverage
- **Error Handling**: Custom exceptions with clear error messages

---

## Task Breakdown

### Task 1: Create Question Data Model
**Priority**: CRITICAL (Foundation)  
**Complexity**: Simple  
**Estimated Effort**: 1-2 hours  
**Dependencies**: None

**Description**:
Create Pydantic models for question data structure, including validation rules and serialization logic.

**Implementation Details**:
- Define `QuestionStatus` enum (pending, answered)
- Create `QuestionBase` model with shared fields
- Create `QuestionCreate` model for creation (excludes id, timestamps)
- Create `Question` model for storage (includes all fields)
- Create `QuestionAnswer` model for answer submission
- Add validators for non-empty strings, valid UUIDs, status transitions

**Acceptance Criteria**:
- [ ] `QuestionStatus` enum with 'pending' and 'answered' values
- [ ] `Question` model includes: question_id (UUID), job_id (UUID), agent_type (str), question_text (str, max 1000 chars), context (str, max 5000 chars), status (QuestionStatus), created_at (datetime), answered_at (Optional[datetime]), answer_text (Optional[str, max 10000 chars]), original_input_data (dict)
- [ ] `QuestionCreate` model excludes generated fields (id, timestamps, status)
- [ ] `QuestionAnswer` model validates answer_text is non-empty (min 1 char)
- [ ] All string fields validated for non-null, appropriate max lengths
- [ ] Model can serialize to/from JSON without data loss
- [ ] Unit tests verify all validation rules
- [ ] Unit tests verify JSON serialization round-trip

**Files to Create**:
- `backend/app/models/question.py`
- `tests/unit/models/test_question.py`

---

### Task 2: Implement Question Storage Service (Core CRUD)
**Priority**: CRITICAL (Foundation)  
**Complexity**: Medium  
**Estimated Effort**: 3-4 hours  
**Dependencies**: Task 1 (Question Data Model)

**Description**:
Create service layer for question persistence using JSON file storage with atomic writes, following feedback pattern architecture.

**Implementation Details**:
- Create `QuestionStorageService` class with singleton pattern
- Implement storage directory management (`~/.ensemble/questions/`)
- Each question stored in separate file: `{question_id}.json`
- Add atomic write operations (write to temp file, then rename)
- Implement file locking for concurrent access protection
- Add index file for quick listing: `_index.json` with metadata
- Handle file I/O errors gracefully with custom exceptions

**CRUD Operations**:
- `create_question(question_data: QuestionCreate, job_id: str, agent_type: str, original_input_data: dict) -> Question`: Generate UUID, set timestamps, save to disk, update index
- `get_question(question_id: str) -> Optional[Question]`: Load from file, validate, return model
- `list_questions(status: Optional[QuestionStatus] = None, job_id: Optional[str] = None) -> List[Question]`: Read index, filter by criteria, load matching questions
- `update_question(question_id: str, updates: dict) -> Question`: Load, modify, atomic save
- `answer_question(question_id: str, answer_text: str) -> Question`: Validate pending status, set answer fields, update status, save

**Acceptance Criteria**:
- [ ] Service creates storage directory if not exists
- [ ] `create_question()` generates UUID4, sets created_at, initializes status='pending'
- [ ] Each question saved as `{uuid}.json` with proper formatting
- [ ] `get_question()` returns None for non-existent IDs without raising exception
- [ ] `list_questions()` returns empty list when no questions exist
- [ ] `list_questions(status='pending')` filters correctly
- [ ] `list_questions(job_id='xyz')` filters correctly
- [ ] `answer_question()` raises exception if question already answered
- [ ] `answer_question()` raises exception if question_id invalid
- [ ] `answer_question()` sets answered_at timestamp and status='answered'
- [ ] Atomic writes prevent partial file corruption
- [ ] Index file stays synchronized with individual files
- [ ] Concurrent operations don't corrupt data (basic file locking)
- [ ] All file I/O errors raise clear custom exceptions
- [ ] Unit tests cover all CRUD operations
- [ ] Unit tests cover edge cases (missing files, corrupted JSON, concurrent access)
- [ ] Integration tests verify persistence across service restarts

**Files to Create**:
- `backend/app/services/question_storage_service.py`
- `backend/app/exceptions/question_exceptions.py`
- `tests/unit/services/test_question_storage_service.py`
- `tests/integration/test_question_persistence.py`

---

### Task 3: Create Question Business Logic Service
**Priority**: HIGH  
**Complexity**: Medium  
**Estimated Effort**: 2-3 hours  
**Dependencies**: Task 2 (Storage Service)

**Description**:
Build higher-level business logic service that orchestrates question lifecycle, enforces business rules, and integrates with job tracking.

**Implementation Details**:
- Create `QuestionService` class wrapping storage service
- Add business rule validation (e.g., can't answer twice, question must exist)
- Integrate with job tracking system to update job state
- Add logging for all question lifecycle events
- Prepare for future agent resumption integration (Task 4)

**Methods**:
- `create_question_from_agent_output(agent_output: dict, job_id: str, agent_type: str, original_input_data: dict) -> Question`: Extract question data, validate format, create via storage service, log event
- `get_question_details(question_id: str) -> Question`: Retrieve with existence validation, raise if not found
- `list_all_questions(filters: dict) -> List[Question]`: Delegate to storage with logging
- `submit_answer(question_id: str, answer_text: str) -> Question`: Validate question exists and is pending, call storage service, log answer event, return updated question
- `get_questions_for_job(job_id: str) -> List[Question]`: Retrieve all questions related to a specific job

**Acceptance Criteria**:
- [ ] `create_question_from_agent_output()` validates agent output has required fields (question_text, context)
- [ ] `create_question_from_agent_output()` raises exception for malformed agent output
- [ ] `get_question_details()` raises `QuestionNotFoundException` for invalid IDs
- [ ] `submit_answer()` raises `QuestionNotFoundException` for invalid IDs
- [ ] `submit_answer()` raises `QuestionAlreadyAnsweredException` for answered questions
- [ ] `submit_answer()` validates answer_text is non-empty
- [ ] All operations logged with appropriate level (INFO for normal, WARNING for validation failures)
- [ ] Service methods have proper type hints and docstrings
- [ ] Unit tests cover all business logic paths
- [ ] Unit tests verify exception raising for invalid states
- [ ] Unit tests verify job state integration hooks (mocked)

**Files to Create**:
- `backend/app/services/question_service.py`
- `tests/unit/services/test_question_service.py`

---

### Task 4: Implement Agent Output Processing Integration
**Priority**: HIGH  
**Complexity**: Medium  
**Estimated Effort**: 2-3 hours  
**Dependencies**: Task 3 (Business Logic Service)

**Description**:
Integrate question creation into existing agent execution flow. When agents return "info_needed" status, automatically create question records.

**Implementation Details**:
- Locate existing agent output processing code (likely in job execution or agent spawn logic)
- Add handler for `status="info_needed"` in agent output
- Extract question data from agent output and create question record
- Update job state to "info_needed" when question created
- Store original agent input_data for future resumption
- Add error handling for malformed agent output

**Integration Points**:
- Agent spawn/execution system
- Job state tracking system
- Activity log (record question creation events)

**Acceptance Criteria**:
- [ ] Agent output with `status="info_needed"` triggers question creation
- [ ] Question record includes job_id, agent_type, original_input_data from execution context
- [ ] Job state updated to "info_needed" after question created
- [ ] Activity log records question creation event with question_id
- [ ] Malformed "info_needed" output logs error without crashing job
- [ ] Agents without "info_needed" status continue working normally (backward compatibility)
- [ ] Unit tests verify question creation from agent output
- [ ] Unit tests verify job state update
- [ ] Integration tests verify end-to-end flow (agent returns info_needed → question created → job state updated)

**Files to Modify**:
- Existing agent execution handler (location TBD during implementation)
- Existing job state management (location TBD)

**Files to Create**:
- `tests/integration/test_agent_question_creation.py`

---

### Task 5: Create Question Storage Maintenance Utilities
**Priority**: LOW  
**Complexity**: Simple  
**Estimated Effort**: 1-2 hours  
**Dependencies**: Task 2 (Storage Service)

**Description**:
Build utility functions for maintaining question storage health, including index rebuild, orphan cleanup, and data validation.

**Implementation Details**:
- Create `QuestionStorageUtils` class
- Add index rebuild from individual question files
- Add validation check for all stored questions
- Add orphan file cleanup (files in index but not on disk, vice versa)
- Add data migration helper for future schema changes

**Methods**:
- `rebuild_index()`: Scan all .json files, regenerate _index.json
- `validate_storage()`: Check all files valid JSON, match schema, return report
- `cleanup_orphans()`: Remove index entries without files, log orphaned files
- `get_storage_stats()`: Return counts, size, oldest/newest question

**Acceptance Criteria**:
- [ ] `rebuild_index()` successfully recreates index from files
- [ ] `rebuild_index()` handles missing or corrupted files gracefully
- [ ] `validate_storage()` returns detailed report of any issues
- [ ] `cleanup_orphans()` removes invalid index entries
- [ ] `cleanup_orphans()` logs warning for files not in index
- [ ] `get_storage_stats()` returns accurate counts and metadata
- [ ] All utilities can be run safely on production data (read-only where appropriate)
- [ ] Unit tests verify each utility function
- [ ] Documentation includes when/why to run each utility

**Files to Create**:
- `backend/app/utils/question_storage_utils.py`
- `tests/unit/utils/test_question_storage_utils.py`

---

### Task 6: Add Question Storage Performance Monitoring
**Priority**: LOW  
**Complexity**: Simple  
**Estimated Effort**: 1-2 hours  
**Dependencies**: Task 2 (Storage Service)

**Description**:
Implement timing and performance monitoring for question storage operations to ensure they meet performance requirements (<100ms create, <200ms retrieval).

**Implementation Details**:
- Add timing decorators to storage service methods
- Log slow operations (> threshold) with WARNING level
- Add metrics collection (operation counts, avg times, errors)
- Create performance report endpoint for monitoring

**Metrics to Track**:
- Operation type (create, get, list, update, answer)
- Operation duration (ms)
- Success/failure status
- Timestamp

**Acceptance Criteria**:
- [ ] All storage operations timed automatically
- [ ] Operations exceeding thresholds logged with timing details
- [ ] Metrics available via `get_performance_metrics()` method
- [ ] Performance data includes: operation count, avg time, min/max time, error count
- [ ] Metrics reset capability for testing
- [ ] Unit tests verify timing capture
- [ ] Unit tests verify threshold warnings

**Files to Create**:
- `backend/app/monitoring/question_performance.py`
- `tests/unit/monitoring/test_question_performance.py`

---

## Task Dependencies Graph

```
Task 1 (Data Model)
    ↓
Task 2 (Storage Service)
    ↓
    ├─→ Task 3 (Business Logic Service)
    │       ↓
    │   Task 4 (Agent Integration)
    │
    ├─→ Task 5 (Maintenance Utilities)
    │
    └─→ Task 6 (Performance Monitoring)
```

**Critical Path**: Task 1 → Task 2 → Task 3 → Task 4 (Required for API development in Milestone 2)

---

## Testing Strategy

### Unit Tests
- Test all models with valid/invalid data
- Test storage service CRUD operations in isolation (mock file system)
- Test business logic service rules and validations
- Mock all external dependencies (job tracking, activity log)
- Aim for >90% code coverage

### Integration Tests
- Test question persistence across service restarts
- Test concurrent operations (multiple questions created simultaneously)
- Test agent output processing end-to-end
- Test file system operations with real files (in test directory)
- Verify job state integration

### Performance Tests
- Verify create operation < 100ms (per requirements)
- Verify retrieval operation < 200ms (per requirements)
- Test list operation with 100+ questions < 1s
- Simulate concurrent access (5-10 simultaneous operations)

---

## Definition of Done (Milestone 1)

All tasks completed with:
- [ ] All acceptance criteria met
- [ ] Unit tests passing with >80% coverage
- [ ] Integration tests passing
- [ ] Performance tests meet requirements
- [ ] Code reviewed (if team review process exists)
- [ ] Documentation complete (docstrings, README updates)
- [ ] No critical or high-priority bugs
- [ ] Storage directory structure verified on fresh install
- [ ] Error messages clear and actionable
- [ ] Logging appropriate (not too verbose, not too sparse)

---

## Risk Mitigation

### Risk: File System Corruption
**Mitigation**: Atomic writes with temp files, index rebuild utility, comprehensive validation

### Risk: Concurrent Access Issues
**Mitigation**: File locking, unique filenames (UUID), index synchronization logic

### Risk: Performance Degradation with Many Questions
**Mitigation**: Index for fast listing, individual files prevent loading all data, monitoring to detect issues

### Risk: JSON Schema Evolution
**Mitigation**: Migration utility prepared, version field in model (future), backward-compatible changes only

---

## Next Steps (Milestone 2 Preview)

After Milestone 1 completion, Milestone 2 will focus on:
1. FastAPI endpoint creation (`GET /api/questions`, `POST /api/questions/{id}/answer`)
2. Request/response schema definitions
3. API validation and error handling
4. Agent resumption logic (spawn with answer context)
5. Job state transition management

---

**Document Version**: 1.0  
**Created**: 2026-01-14  
**Status**: Ready for TDD Implementation  
**Estimated Total Effort**: 10-16 hours  
**Target Completion**: Milestone 1 complete before API development begins
