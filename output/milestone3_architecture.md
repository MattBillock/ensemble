# Milestone 3: Question Handling System Architecture

## Project Context
**Project**: Agent Swarm System Improvements (a1c6fbce)
**Milestone**: 3 of 5 - Question Handling System
**Status**: Milestones 1 & 2 Complete, Milestone 3 In Progress

## Overview
This architecture defines a hierarchical question handling system that enables agents to pause execution, ask questions, and resume with answers. The system includes runtime enhancements for question detection and a new Question Marshal agent for autonomous question resolution.

## System Architecture

### 1. Runtime Question Detection & Execution Control

#### Core Components

**1.1 Question Detection**
- Monitor agent responses for `needs_clarification` or `needs_user_input` status
- Extract question content and metadata from response
- Generate unique question IDs for tracking

**1.2 Execution Pause/Resume**
- Pause agent execution when question detected
- Preserve execution state (conversation history, context)
- Return partial response with question details
- Resume execution when answer provided via `set_user_answer()`

**1.3 Activity Tracking**
- Record questions with unique IDs in activity tracker
- Store question metadata: type, options, context, timestamp
- Track question status: pending, answered, escalated
- Maintain question-answer pairs for audit trail

#### Key Methods

```python
# In AgentRuntime class
def _detect_question(self, response: dict) -> Optional[dict]:
    """Detect if response contains a question"""
    
def _record_question(self, question_data: dict) -> str:
    """Record question in activity tracker, return question_id"""
    
def set_user_answer(self, question_id: str, answer: str) -> dict:
    """Resume execution with user-provided answer"""
```

#### Data Structures

```python
question_record = {
    "question_id": "q_<uuid>",
    "agent_name": "agent_type",
    "question_text": "What is X?",
    "question_type": "clarification|user_input|decision",
    "context": {...},
    "options": [...],  # Optional
    "timestamp": "ISO-8601",
    "status": "pending|answered|escalated",
    "answer": None  # Populated when answered
}
```

### 2. Question Marshal Agent

#### Purpose
Autonomous question resolution agent that attempts to answer questions by referencing documentation and defaults before escalating to Director/User.

#### Agent Definition
- **File**: `leadership/question_marshal.md`
- **Model**: Haiku (economical for frequent use)
- **Purpose**: "Question resolution using docs/defaults"
- **Success Target**: 60-70% autonomous resolution rate

#### Input Format
```json
{
    "question": "Question text",
    "agent_context": {
        "agent_name": "string",
        "task": "string",
        "conversation_history": [...]
    },
    "available_docs": [
        "docs/common_instructions.md",
        "docs/agent_definitions/*",
        "..."
    ],
    "question_metadata": {
        "type": "clarification|user_input|decision",
        "options": [...],
        "urgency": "low|medium|high"
    }
}
```

#### Output Format
```json
{
    "status": "resolved|escalate",
    "resolution": {
        "answer": "string",
        "confidence": "high|medium|low",
        "source": "documentation|defaults|inference"
    },
    "escalation": {
        "reason": "string",
        "recommended_target": "director|user",
        "context": {...}
    },
    "self_analysis": "2-4 sentences"
}
```

#### Resolution Strategy
1. **Documentation Search**: Check common_instructions.md, agent definitions
2. **Default Values**: Apply reasonable defaults when documented
3. **Inference**: Use context to infer reasonable answers for low-risk decisions
4. **Escalation**: Complex/high-risk questions escalate with context

### 3. Hierarchical Question Flow

```
Agent (needs clarification)
    ↓
Runtime (detect, record, pause)
    ↓
Question Marshal Agent
    ↓ (60-70% resolved)
    ├─→ Answer → Resume Agent
    └─→ Escalate → Director
              ↓
              ├─→ Answer → Resume Agent
              └─→ User Input
                    ↓
                    Answer → Resume Agent
```

### 4. Integration with Existing Features

#### 4.1 Resilience Features (Milestone 2)
- Circuit breaker: Question handling respects circuit breaker state
- Retry logic: Question resolution failures trigger retry with exponential backoff
- Rate limiting: Question Marshal calls counted in rate limits
- Validation: Question/answer formats validated before processing

#### 4.2 Activity Tracking
- Questions recorded alongside normal activity events
- Question events tagged with `event_type: "question"`
- Timeline shows question ask/answer pairs

#### 4.3 Backward Compatibility
- Existing agents without question handling work unchanged
- Question detection is opt-in via status codes
- No breaking changes to core runtime interfaces

## Implementation Phases

### Phase 1: Runtime Enhancement (Priority 1)
**Files**: `src/runtime/agents/runtime.py`

**Tasks**:
1. Add `_detect_question()` method
2. Implement `_record_question()` in activity tracker
3. Add pause/resume logic to execution loop
4. Implement `set_user_answer()` method
5. Add question metadata handling

**Acceptance Criteria**:
- Runtime detects `needs_clarification` status
- Questions recorded with unique IDs
- Execution pauses and returns partial response
- `set_user_answer()` resumes execution seamlessly

### Phase 2: Question Marshal Agent (Priority 1)
**Files**: `leadership/question_marshal.md`

**Tasks**:
1. Create agent definition file
2. Define input/output formats
3. Specify resolution strategies
4. Document escalation criteria
5. Add examples and test cases

**Acceptance Criteria**:
- Agent definition complete and valid
- Clear resolution strategy documented
- Escalation criteria well-defined
- Examples demonstrate 60-70% resolution target

### Phase 3: Integration Testing (Priority 2)
**Files**: `tests/test_question_handling.py`

**Tasks**:
1. Test question detection in runtime
2. Test pause/resume functionality
3. Test Question Marshal resolution
4. Test hierarchical escalation flow
5. Test activity tracker recording

**Acceptance Criteria**:
- All question detection tests pass
- Pause/resume tests pass
- Question Marshal tests demonstrate 60-70% resolution
- Escalation flow tests pass
- No regressions in existing tests

### Phase 4: Test Writer Updates (Priority 3)
**Files**: `testers/unit_test_writer.md`, `testers/integration_test_writer.md`

**Tasks**:
1. Add file creation authority clarification
2. Update permission guidelines
3. Clarify autonomous vs. ask scenarios

**Acceptance Criteria**:
- Clear file creation authority documented
- Permission guidelines updated
- No ambiguity in agent instructions

## Testing Strategy

### Unit Tests
- Question detection logic
- Question recording
- Pause/resume state management
- Answer validation

### Integration Tests
- End-to-end question flow
- Question Marshal integration
- Escalation pathways
- Activity tracker integration
- Resilience feature integration

### Performance Tests
- Question detection overhead < 5%
- Memory usage stable
- Question resolution latency < 2s (Question Marshal)

## Success Metrics

### Functional
1. ✅ Runtime detects questions correctly (100% accuracy)
2. ✅ Questions recorded with unique IDs
3. ✅ Execution pause/resume works seamlessly
4. ✅ Question Marshal resolves 60-70% autonomously
5. ✅ Hierarchical escalation works correctly
6. ✅ Test writers have explicit authority

### Quality
1. ✅ All existing tests pass (no regressions)
2. ✅ New integration tests pass
3. ✅ Performance overhead < 5%
4. ✅ Memory stable

### Performance
- Question detection: < 10ms overhead
- Question Marshal resolution: < 2s average
- Total question handling: < 3s for autonomous resolution

## Risk Mitigation

### Risk: Question Marshal fails to resolve enough questions
**Mitigation**: 
- Start with conservative escalation criteria
- Monitor resolution rates
- Adjust documentation references over time

### Risk: Execution state corruption during pause/resume
**Mitigation**:
- Deep copy state before pause
- Validate state integrity on resume
- Comprehensive state management tests

### Risk: Integration issues with resilience features
**Mitigation**:
- Early integration testing
- Reuse existing resilience patterns
- Test circuit breaker + question handling together

## Dependencies

### Required
- ✅ Milestone 2 (Runtime Resilience) complete
- ✅ Access to runtime.py and activity tracker
- ✅ Test infrastructure functional

### Files to Update
- `src/runtime/agents/runtime.py` (UPDATE)
- `leadership/question_marshal.md` (CREATE)
- `tests/test_question_handling.py` (CREATE)
- `testers/unit_test_writer.md` (UPDATE)
- `testers/integration_test_writer.md` (UPDATE)

## Deliverables Checklist

- [ ] Runtime question detection implemented
- [ ] Question recording in activity tracker
- [ ] Pause/resume execution logic
- [ ] `set_user_answer()` method
- [ ] Question Marshal agent definition
- [ ] Integration tests created
- [ ] Test writer definitions updated
- [ ] All tests passing
- [ ] Performance validated
- [ ] Documentation updated

## Conclusion

This architecture provides a comprehensive question handling system that enables agents to pause, ask questions, and resume execution. The Question Marshal agent will handle 60-70% of questions autonomously, reducing user interruptions while maintaining the ability to escalate complex questions through the hierarchy.

The design maintains backward compatibility, integrates seamlessly with existing resilience features, and includes comprehensive testing to ensure reliability.
