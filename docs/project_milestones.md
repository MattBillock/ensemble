# Agent Swarm System Improvements - Milestone Plan

**Project**: Agent Swarm System Improvements  
**Project ID**: a1c6fbce  
**Date**: 2026-01-13  
**Development Manager**: Active

---

## Milestone 1: Analysis & Token Optimization
**Objective**: Analyze current system and implement token optimization by extracting common instructions.

**Duration Estimate**: 1-2 days

**Deliverables**:
1. Analysis report of `src/runtime/agents/runtime.py` with findings
2. Analysis report of all agent definition files with token waste identification
3. `/docs/common_instructions.md` - Extracted shared instructions
4. Updated agent definitions (7+ files) referencing common instructions
5. Token usage comparison metrics

**Acceptance Criteria**:
- All agent definition files analyzed
- Common patterns identified and documented
- Token reduction of 35-40% achieved
- All agents still function correctly after updates
- No breaking changes to agent behavior

**Dependencies**: None (first milestone)

**Key Tasks**:
- Analyze runtime.py for patterns and issues
- Analyze all agent `.md` files for redundant instructions
- Create common_instructions.md with shared directives
- Update agent definitions to reference common instructions
- Validate all agents still work

---

## Milestone 2: Runtime Resilience & Performance
**Objective**: Implement circuit breaker, retry logic, and performance optimizations in runtime.

**Duration Estimate**: 2-3 days

**Deliverables**:
1. `src/runtime/agents/resilience.py` - Circuit breaker, retry, rate limiter
2. `src/runtime/agents/validation.py` - Response validation module
3. Updated `src/runtime/agents/runtime.py` - Integrated resilience patterns
4. `tests/test_resilience.py` - Comprehensive resilience tests
5. `tests/test_validation.py` - Validation tests

**Acceptance Criteria**:
- Circuit breaker prevents cascade failures (5 failure threshold, 60s timeout)
- Retry logic with exponential backoff (3 retries, base 1s delay)
- Rate limiter functional
- Response validation catches malformed responses
- Regex patterns cached at class level
- Message history pruning implemented (max 50 messages)
- All tests passing (95+ tests)
- Performance improvement measurable

**Dependencies**: 
- Milestone 1 (analysis findings inform implementation)

**Key Tasks**:
- Implement circuit breaker pattern
- Implement retry with exponential backoff
- Implement rate limiter
- Create response validation module
- Integrate resilience into runtime.py
- Cache regex patterns
- Implement message pruning
- Write comprehensive tests

---

## Milestone 3: Question Handling System
**Objective**: Enable agents to ask questions, pause execution, and resume with answers.

**Duration Estimate**: 2-3 days

**Deliverables**:
1. Updated `src/runtime/agents/runtime.py` - Question detection and pausing
2. `leadership/question_marshal.md` - Question Marshal agent definition
3. Integration tests for question flow
4. Updated test writer agent definitions with authority clarification

**Acceptance Criteria**:
- Runtime detects `needs_clarification` or `needs_user_input` status
- Questions recorded in activity tracker
- Execution pauses and returns partial response
- `set_user_answer()` method resumes execution
- Question Marshal can resolve questions using docs/defaults
- Question Marshal resolves 60-70% of questions internally
- Hierarchical question flow works (sub-agent → Question Marshal → Director → User)
- Test writers have explicit file creation authority
- No backend/frontend changes required

**Dependencies**: 
- Milestone 2 (resilient runtime required for question handling)

**Key Tasks**:
- Implement question detection in runtime
- Add question recording to activity tracker
- Implement execution pause/resume
- Create Question Marshal agent definition
- Update test writer agent definitions
- Test hierarchical question flow
- Validate with integration tests

---

## Milestone 4: Testing & Validation
**Objective**: Ensure all improvements work correctly and all tests pass.

**Duration Estimate**: 1-2 days

**Deliverables**:
1. All new tests passing
2. Updated existing tests for new model names (Sonnet 4.5)
3. Integration test suite for complete workflows
4. Performance benchmark results

**Acceptance Criteria**:
- 95+ tests passing
- No regressions in existing functionality
- All new features covered by tests
- Performance metrics collected and documented
- Backward compatibility verified

**Dependencies**: 
- Milestones 1, 2, 3 (all implementation complete)

**Key Tasks**:
- Run all existing tests
- Update tests for new model names
- Create integration tests for end-to-end workflows
- Run performance benchmarks
- Fix any failing tests
- Validate backward compatibility

---

## Milestone 5: Documentation & Completion
**Objective**: Document all changes, metrics, and system improvements.

**Duration Estimate**: 1 day

**Deliverables**:
1. `docs/current/AGENT_SWARM_IMPROVEMENTS_2026-01.md` - Full improvement report
2. `docs/current/QUESTION_HANDLING_SYSTEM.md` - Question system documentation
3. Updated README files as needed
4. Performance metrics report

**Acceptance Criteria**:
- Executive summary written
- All issues identified with line numbers documented
- All improvements documented with before/after metrics
- Question handling system fully documented
- Workflow examples provided
- API reference complete
- All changes committed to version control

**Dependencies**: 
- Milestones 1, 2, 3, 4 (all work complete)

**Key Tasks**:
- Write comprehensive improvement report
- Document question handling system architecture
- Create workflow examples
- Document API changes
- Collect and document metrics
- Commit all changes with proper messages

---

## Project Success Criteria Summary

✅ Token usage reduced by 35-40% per execution  
✅ API calls have retry logic with exponential backoff  
✅ Circuit breaker prevents cascade failures  
✅ Agents can pause for user questions and resume with answers  
✅ Question Marshal resolves 60-70% questions internally  
✅ All tests passing (95+ tests)  
✅ No redundant instructions in agent definitions  
✅ Test writers have clear file creation authority  
✅ Complete documentation of all changes  

---

## Risk Assessment

**Low Risk**:
- Token optimization (non-breaking)
- Documentation updates

**Medium Risk**:
- Runtime resilience integration (needs thorough testing)
- Question handling system (new functionality)

**Mitigation**:
- Comprehensive test coverage
- Backward compatibility validation
- Incremental rollout per milestone

---

**Total Estimated Duration**: 7-11 days  
**Critical Path**: Milestone 1 → Milestone 2 → Milestone 3 → Milestone 4 → Milestone 5
