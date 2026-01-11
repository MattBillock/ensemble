# Test Strategy - Milestone 1: Naming Audit & Discovery

## Overview
This test strategy defines comprehensive testing for the naming audit and discovery phase of the Ensemble Project Generation Capability (EPGC). The focus is on verification tests for the audit process itself, validation of findings, and automated checks for naming consistency.

## Test Philosophy
**Audit Quality Over Code Coverage**: Since this milestone is primarily about discovery and documentation, testing focuses on:
- **Validation**: Ensuring audit findings are accurate and complete
- **Automation**: Creating tools to detect naming violations
- **Regression**: Ensuring no naming issues reappear after fixes

## Test Types Breakdown

### 1. Unit Tests (60% of effort)
Focus: Individual audit functions and utilities

**Purpose**: 
- Test file scanning logic
- Test pattern matching for terminology issues
- Test report generation functions

**Target Coverage**: 80%+ for all audit utility functions

### 2. Integration Tests (30% of effort)
Focus: End-to-end audit pipeline

**Purpose**:
- Test complete audit workflow from file scanning to report generation
- Verify cross-references between agent files are validated
- Test spawn path validation logic

**Target Coverage**: 100% of critical audit workflows

### 3. End-to-End Tests (10% of effort)
Focus: Complete audit execution

**Purpose**:
- Validate that audit can be run from command line
- Verify audit report output format and completeness
- Test audit report contains all required sections

**Target Coverage**: Happy path + error scenarios (missing files, malformed agents)

---

## Test Task Breakdown

### Task Group A: Audit Utility Unit Tests

#### Task A1: File Scanner Unit Tests
**Component**: File scanning and discovery logic  
**Type**: Unit Test  
**Priority**: HIGH  
**Estimated Effort**: 2 hours

**Test Cases**:
1. Test scanning all agent definition directories (leadership/, coordinators/, developers/, testers/, designers/, support/)
2. Test filtering for .md files only
3. Test handling of nested directories
4. Test handling of symlinks and special files
5. Test error handling for inaccessible directories
6. Test exclusion of non-agent files (README.md, etc.)

**Expected Coverage**: 90%+

**Mock Requirements**:
- Mock file system operations
- Mock os.walk() for controlled directory structures

---

#### Task A2: Terminology Pattern Detection Unit Tests
**Component**: Pattern matching for naming violations  
**Type**: Unit Test  
**Priority**: HIGH  
**Estimated Effort**: 3 hours

**Test Cases**:
1. Test detection of "drill writer" references
2. Test detection of "logistics manager" references
3. Test detection of "visual tech" references
4. Test detection of "drum corps" terminology
5. Test detection of camelCase agent names (should be snake_case)
6. Test detection of mismatched agent names vs. file paths
7. Test case-insensitive pattern matching
8. Test pattern matching in code blocks vs. prose
9. Test false positive handling (e.g., "writer" is not always wrong)
10. Test multiple violations in single file

**Expected Coverage**: 85%+

**Test Data Required**:
- Sample agent files with known violations
- Sample agent files that are compliant
- Edge case files (empty, malformed)

---

#### Task A3: Spawn Path Validation Unit Tests
**Component**: Validation of spawn_agent() references  
**Type**: Unit Test  
**Priority**: HIGH  
**Estimated Effort**: 2 hours

**Test Cases**:
1. Test extraction of spawn_agent() calls from agent files
2. Test validation that spawned agent paths exist
3. Test detection of incorrect path formats
4. Test detection of missing category prefixes (e.g., "leadership/")
5. Test validation of spawn path against actual file structure
6. Test handling of quoted vs. unquoted paths
7. Test detection of circular spawn references (if applicable)

**Expected Coverage**: 80%+

**Mock Requirements**:
- Mock file system for agent path existence checks

---

#### Task A4: Report Generation Unit Tests
**Component**: Markdown report creation logic  
**Type**: Unit Test  
**Priority**: MEDIUM  
**Estimated Effort**: 2 hours

**Test Cases**:
1. Test generation of summary statistics section
2. Test generation of violations by category table
3. Test generation of detailed findings section
4. Test generation of recommendations section
5. Test proper markdown formatting (headers, lists, code blocks)
6. Test handling of zero violations (clean audit)
7. Test handling of many violations (large report)
8. Test proper escaping of special characters in findings

**Expected Coverage**: 85%+

---

### Task Group B: Integration Tests

#### Task B1: Complete Audit Pipeline Integration Test
**Component**: Full audit workflow  
**Type**: Integration Test  
**Priority**: HIGH  
**Estimated Effort**: 3 hours

**Test Cases**:
1. Test scanning → pattern detection → report generation pipeline
2. Test audit with known violations produces correct report
3. Test audit with clean codebase produces clean report
4. Test audit handles missing agent directories gracefully
5. Test audit aggregates findings from multiple agent categories
6. Test audit cross-references spawn paths with actual files
7. Test audit report includes file paths relative to project root
8. Test audit preserves violation context (surrounding lines)

**Expected Coverage**: 100% of critical paths

**Test Environment**:
- Mock agent directory structure with known violations
- Sample agent files in each category
- Control over file system for deterministic testing

---

#### Task B2: Agent Cross-Reference Validation Integration Test
**Component**: Spawn path and agent name consistency checks  
**Type**: Integration Test  
**Priority**: MEDIUM  
**Estimated Effort**: 2 hours

**Test Cases**:
1. Test validation that all spawned agents exist
2. Test detection when agent file name doesn't match spawn path
3. Test validation of agent name in file matches file path
4. Test detection of orphaned agent files (never spawned)
5. Test validation of agent category consistency

**Expected Coverage**: 100% of cross-reference logic

---

#### Task B3: Audit Report Validation Integration Test
**Component**: Report output validation  
**Type**: Integration Test  
**Priority**: MEDIUM  
**Estimated Effort**: 2 hours

**Test Cases**:
1. Test report contains all required sections
2. Test report statistics match actual violations found
3. Test report recommendations are specific and actionable
4. Test report includes file paths and line numbers for violations
5. Test report groups violations by type and category
6. Test report outputs to specified file path
7. Test report is valid markdown that renders correctly

**Expected Coverage**: 100% of report validation

---

### Task Group C: End-to-End Tests

#### Task C1: Command-Line Audit Execution E2E Test
**Component**: Complete audit from CLI  
**Type**: E2E Test  
**Priority**: MEDIUM  
**Estimated Effort**: 2 hours

**Test Cases**:
1. Test audit runs successfully via command line
2. Test audit with custom output path
3. Test audit with verbose logging enabled
4. Test audit handles missing directories gracefully (non-zero exit)
5. Test audit produces report file at expected location
6. Test audit exit codes (0 for success, non-zero for failures)

**Expected Coverage**: Happy path + critical error scenarios

**Test Environment**:
- Real file system with test agent structures
- Subprocess execution for CLI testing

---

#### Task C2: Audit Report Completeness E2E Test
**Component**: Verification of audit findings  
**Type**: E2E Test  
**Priority**: HIGH  
**Estimated Effort**: 2 hours

**Test Cases**:
1. Test audit identifies all known support/ agent naming issues
2. Test audit identifies spawn path references to renamed agents
3. Test audit generates actionable recommendations
4. Test audit report can be used as input for Milestone 2 changes
5. Test audit finds all drum corps terminology in active agent files
6. Test audit distinguishes active vs. archived agent files

**Expected Coverage**: All FR-1 requirements validated

---

### Task Group D: Validation Scripts

#### Task D1: Automated Naming Convention Validator
**Component**: Reusable validator for future CI/CD  
**Type**: Unit + Integration Test  
**Priority**: MEDIUM  
**Estimated Effort**: 3 hours

**Test Cases**:
1. Test validator script runs in CI environment
2. Test validator detects new naming violations
3. Test validator has zero false positives on clean code
4. Test validator outputs machine-readable format (JSON)
5. Test validator can be configured with custom patterns
6. Test validator performance on large codebases

**Expected Coverage**: 80%+ for validator logic

**Deliverable**: Reusable script for ongoing naming validation

---

## Coverage Goals

| Test Type | Target Coverage | Rationale |
|-----------|----------------|-----------|
| Unit Tests | 80%+ | Critical for audit utility functions |
| Integration Tests | 100% (critical paths) | Ensure audit workflow is reliable |
| E2E Tests | Happy path + key errors | Validate audit can be run successfully |
| Overall | 85%+ | High confidence in audit accuracy |

---

## Test Data Requirements

### Sample Agent Files Needed
1. **Compliant agent file** - Correct naming, no violations
2. **drill_writer.md** - Known violation (drum corps terminology)
3. **logistics_manager.md** - Known violation (non-standard name)
4. **visual_tech.md** - Known violation (non-standard name)
5. **Agent with camelCase** - Should be snake_case
6. **Agent with invalid spawn paths** - References non-existent agents
7. **Empty agent file** - Edge case handling
8. **Malformed agent file** - Invalid markdown structure

### Directory Structures Needed
1. **Full agent hierarchy** - leadership/, coordinators/, developers/, testers/, designers/, support/
2. **Missing category** - Test handling of missing directories
3. **Nested agents** - Test recursive scanning
4. **Mixed valid/invalid** - Test partial violations

---

## Testing Frameworks & Tools

### Backend Testing (Python)
- **Framework**: pytest
- **Mocking**: pytest-mock, unittest.mock
- **Coverage**: pytest-cov
- **Fixtures**: pytest fixtures for sample agent structures

### Linting & Static Analysis
- **Tool**: pylint, flake8
- **Purpose**: Ensure test code quality
- **Coverage**: 100% of test files

### CI/CD Integration
- **Platform**: GitHub Actions (assumed)
- **Triggers**: On pull request, on push to main
- **Required Checks**: All tests pass, coverage ≥ 85%

---

## Test Execution Strategy

### Phase 1: Unit Tests (Week 1)
1. Implement file scanner tests (Task A1)
2. Implement pattern detection tests (Task A2)
3. Implement spawn path validation tests (Task A3)
4. Implement report generation tests (Task A4)

### Phase 2: Integration Tests (Week 1-2)
1. Implement complete audit pipeline test (Task B1)
2. Implement cross-reference validation test (Task B2)
3. Implement report validation test (Task B3)

### Phase 3: E2E Tests (Week 2)
1. Implement CLI execution test (Task C1)
2. Implement report completeness test (Task C2)

### Phase 4: Validation Scripts (Week 2)
1. Implement automated naming validator (Task D1)
2. Integrate validator into CI/CD pipeline

---

## Success Criteria

### Testing Success Metrics
1. ✅ All unit tests pass with 80%+ coverage
2. ✅ All integration tests pass with 100% critical path coverage
3. ✅ All E2E tests pass for happy path + key errors
4. ✅ Automated validator can be run in CI/CD
5. ✅ Zero false positives in naming violation detection
6. ✅ Audit report accurately identifies all support/ agent naming issues

### Quality Gates
- **Pre-Milestone 2**: All audit tests must pass
- **Regression**: Naming validator runs on every commit
- **Documentation**: Test strategy document reviewed and approved

---

## Risk Mitigation

### Risk 1: False Positives in Pattern Matching
**Mitigation**: 
- Comprehensive test data with edge cases
- Manual review of initial audit results
- Configurable pattern exclusions

### Risk 2: Incomplete Agent Discovery
**Mitigation**:
- Test with various directory structures
- Validate against known agent count
- Manual cross-check of discovered agents

### Risk 3: Report Generation Failures
**Mitigation**:
- Test with large violation sets
- Test with zero violations
- Validate markdown syntax with linter

---

## Appendix: Test Task Summary

| Task ID | Name | Type | Priority | Effort | Coverage Goal |
|---------|------|------|----------|--------|---------------|
| A1 | File Scanner Unit Tests | Unit | HIGH | 2h | 90%+ |
| A2 | Terminology Pattern Detection | Unit | HIGH | 3h | 85%+ |
| A3 | Spawn Path Validation | Unit | HIGH | 2h | 80%+ |
| A4 | Report Generation | Unit | MEDIUM | 2h | 85%+ |
| B1 | Complete Audit Pipeline | Integration | HIGH | 3h | 100% |
| B2 | Cross-Reference Validation | Integration | MEDIUM | 2h | 100% |
| B3 | Audit Report Validation | Integration | MEDIUM | 2h | 100% |
| C1 | CLI Audit Execution | E2E | MEDIUM | 2h | Happy + Errors |
| C2 | Audit Report Completeness | E2E | HIGH | 2h | All FR-1 |
| D1 | Automated Naming Validator | Unit + Integration | MEDIUM | 3h | 80%+ |

**Total Estimated Effort**: 23 hours  
**Total Test Tasks**: 10  
**Overall Coverage Goal**: 85%+

---

## Handoff to TDD Coordinator

This test strategy is ready for implementation. The TDD Coordinator should:

1. **Review and approve** this test breakdown
2. **Prioritize tasks** based on Milestone 1 timeline
3. **Assign tasks** to Unit Test Leads and Integration Test Leads
4. **Coordinate** test data preparation (sample agent files)
5. **Monitor** test execution and coverage metrics
6. **Validate** that all tests pass before Milestone 2 begins

**Key Dependencies for Test Implementation**:
- Sample agent files with known violations (provided above)
- Mock file system utilities for unit tests
- CI/CD pipeline configuration for automated validator

**Expected Outcome**: 
A comprehensive, automated test suite that validates the naming audit is accurate, complete, and repeatable. This ensures that Milestone 2 naming changes can be made with confidence.
