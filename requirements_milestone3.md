# Milestone 3: Question Handling System Requirements

## Project Context
Agent Swarm System Improvements (Project ID: a1c6fbce)

## Status
- **Milestone 1**: ✅ COMPLETE - Token optimization and analysis
- **Milestone 2**: ✅ COMPLETE - Runtime resilience and performance
- **Milestone 3**: 🔄 IN PROGRESS - Question Handling System
- **Milestone 4**: ⏳ Pending - Testing & Validation 
- **Milestone 5**: ⏳ Pending - Documentation & Completion

## Milestone 3 Objective
Enable agents to ask questions, pause execution, and resume with answers through a hierarchical question handling system.

## Deliverables

### 1. Enhanced Runtime Question Detection
**File**: `src/runtime/agents/runtime.py` (UPDATE EXISTING)

**Requirements**:
- Detect agent responses with `needs_clarification` or `needs_user_input` status
- Record questions in activity tracker with unique question IDs
- Pause execution and return partial response with question
- Implement `set_user_answer()` method for resuming execution
- Support question metadata (question type, options, etc.)

### 2. Question Marshal Agent
**File**: `leadership/question_marshal.md` (CREATE NEW)

**Requirements**:
- New agent definition with purpose: "Question resolution using docs/defaults"
- Model preference: Haiku (economical for frequent use)
- Can resolve 60-70% of questions internally by referencing documentation
- Falls back to Director/User for complex questions
- Input format: question, agent context, available docs
- Output format: resolution or escalation

### 3. Integration Tests
**File**: `tests/test_question_handling.py` (CREATE NEW)

**Requirements**:
- Test question detection in runtime
- Test execution pause/resume with user answers
- Test Question Marshal agent functionality
- Test hierarchical question flow (agent → Question Marshal → Director → User)
- Test question recording in activity tracker

### 4. Updated Test Writer Definitions
**Files**: `testers/unit_test_writer.md`, `testers/integration_test_writer.md` (UPDATE EXISTING)

**Requirements**:
- Add explicit file creation authority clarification
- Update instructions to confirm file write permissions
- Clarify when to ask for permission vs. proceed autonomously

## Technical Constraints

### Compatibility
- **MUST** maintain backward compatibility with existing runtime
- **NO** breaking changes to existing agent behavior
- **MUST** integrate with existing resilience features (circuit breaker, retry logic)

### Error Handling
- Proper validation of question format
- Graceful fallback if Question Marshal fails
- Timeout handling for question resolution

### Performance
- Minimal overhead for question detection
- Efficient question tracking and storage

## Success Metrics

### Functional Requirements
1. ✅ Runtime detects `needs_clarification` status correctly
2. ✅ Questions recorded with unique IDs in activity tracker
3. ✅ Execution pauses and returns partial response
4. ✅ `set_user_answer()` method resumes execution seamlessly
5. ✅ Question Marshal resolves 60-70% of questions autonomously
6. ✅ Hierarchical escalation flow works correctly
7. ✅ Test writers have explicit file creation authority

### Quality Gates
- ✅ All existing tests continue to pass (no regressions)
- ✅ New integration tests pass
- ✅ Performance overhead < 5% for question detection
- ✅ Memory usage remains stable

## Implementation Strategy

### Phase 1: Runtime Enhancement (Days 1-2)
1. Update `runtime.py` to detect question status
2. Implement question recording in activity tracker
3. Add execution pause/resume logic
4. Implement `set_user_answer()` method

### Phase 2: Question Marshal (Day 2)
1. Create Question Marshal agent definition
2. Define input/output formats
3. Implement question resolution logic
4. Test autonomous resolution capabilities

### Phase 3: Integration & Testing (Day 3)
1. Create comprehensive integration tests
2. Test hierarchical question flow
3. Update test writer agent definitions
4. Validate no regressions in existing functionality

### Phase 4: Validation (Day 3)
1. End-to-end testing of question scenarios
2. Performance validation
3. Error handling validation
4. Documentation updates

## Dependencies
- Milestone 2 (Runtime Resilience) must be complete ✅
- Access to existing runtime.py and activity tracker ✅
- Test infrastructure must be functional ✅

## Risk Assessment
- **Low Risk**: Question detection implementation
- **Medium Risk**: Question Marshal agent functionality
- **Medium Risk**: Integration with existing runtime features
- **Low Risk**: Test writer definition updates

## Success Criteria
Milestone 3 is complete when:
1. All deliverables implemented and tested
2. Question handling system functional end-to-end
3. No regressions in existing functionality
4. Integration tests passing
5. Question Marshal achieving 60-70% autonomous resolution rate

## Output Directory
Use standard output directory: `src/field/ensemble_ui/output/`

## Timeline
Estimated Duration: 2-3 days
Critical Path: Runtime Enhancement → Question Marshal → Integration Testing