# Backend Tasks - Milestone 1: Naming Audit & Discovery

## Milestone Overview
Audit all agent files and codebase for terminology issues, identify drum corps references, and create inventory of changes needed. This milestone is **discovery and documentation only** - no code changes will be made.

---

## Task Group 1: Codebase Scanning & Discovery

### Task 1.1: Scan Agent Definition Files
**Description**: Systematically read and audit all agent .md files for terminology issues and drum corps references.

**Acceptance Criteria**:
- All agent files in leadership/, coordinators/, developers/, testers/, designers/, support/ have been read
- Each file analyzed for:
  - Drum corps terminology (e.g., "drill writer", "visual tech", "field", "corps", "marching", "performance")
  - Non-standard agent naming conventions
  - Inconsistent spawn path references
  - Incorrect file naming patterns
- Findings documented in structured format (file path, issue type, specific text, line/section)

**Dependencies**: None

**Complexity**: Medium

**Implementation Notes**:
- Use grep/ripgrep for initial keyword search: `drill`, `corps`, `visual`, `field`, `logistics manager`, `drill writer`
- Manual review of all .md files to catch contextual issues
- Focus on active agent definitions, not archived/historical files

---

### Task 1.2: Scan Runtime Code for Agent References
**Description**: Audit src/runtime/agents/ Python code for hardcoded agent paths, spawn references, and terminology.

**Acceptance Criteria**:
- All Python files in src/runtime/agents/ scanned
- Identified any hardcoded spawn paths like "support/drill_writer"
- Identified string literals referencing drum corps terminology
- Documented agent name validation logic (if any)
- Findings documented with file path, line number, and issue type

**Dependencies**: None

**Complexity**: Medium

**Implementation Notes**:
- Search for spawn_agent() calls with agent paths
- Look for string patterns: "drill_writer", "logistics_manager", "visual_tech"
- Check agent registry/loader code for filename dependencies
- Identify any spawn path validation that might break with renames

---

### Task 1.3: Scan Documentation Files
**Description**: Audit README.md, QUICKSTART.md, and any other documentation for terminology and agent name references.

**Acceptance Criteria**:
- All .md files in project root and docs/ folder scanned
- Identified references to drum corps terminology
- Identified references to agents by name (especially support/ agents)
- Documented any spawn path examples or commands
- Findings documented with file path and specific text

**Dependencies**: None

**Complexity**: Simple

**Implementation Notes**:
- Check README.md, QUICKSTART.md, any CONTRIBUTING.md or similar
- Look for examples showing agent usage
- Note any user-facing commands that reference agent names

---

### Task 1.4: Scan Test Files for Agent References
**Description**: Audit test files for agent spawn paths, mocked agent names, and terminology.

**Acceptance Criteria**:
- All test files (tests/, test_*, *_test.py) scanned
- Identified test cases that spawn specific agents
- Identified mock objects or fixtures using agent names
- Documented test data/fixtures with agent paths
- Findings documented with file path and test case name

**Dependencies**: None

**Complexity**: Medium

**Implementation Notes**:
- Search for spawn_agent() calls in test files
- Look for test fixtures using "drill_writer", "logistics_manager", "visual_tech"
- Check integration tests that exercise full agent workflows
- Identify tests that will need updates after rename

---

## Task Group 2: Dependency Mapping

### Task 2.1: Map Agent Spawn Path Dependencies
**Description**: Create a dependency graph showing which agents spawn which other agents, with focus on support/ agents.

**Acceptance Criteria**:
- Complete list of all spawn_agent() calls across codebase
- Dependency graph showing: Agent A → spawns → Agent B
- Specific focus on spawn paths to support/drill_writer, support/logistics_manager, support/visual_tech
- Document which agents will be affected by support/ renames
- Visual diagram or structured data format (JSON, YAML, or markdown table)

**Dependencies**: Task 1.1, Task 1.2, Task 1.4

**Complexity**: Medium

**Implementation Notes**:
- Parse spawn_agent() calls to extract agent paths
- Create parent → child mapping
- Identify critical path agents (those spawned frequently)
- Use mermaid diagram or simple text format for visualization

---

### Task 2.2: Identify Breaking Change Points
**Description**: Document all locations where renaming support/ agents will cause breaking changes.

**Acceptance Criteria**:
- List of all files containing spawn paths to support/ agents
- List of all test cases that will need updates
- List of any configuration files referencing agent names
- Categorized by impact: Critical (blocks functionality), High (causes test failures), Medium (documentation only)
- Impact assessment for each breaking change point

**Dependencies**: Task 1.1, Task 1.2, Task 1.3, Task 1.4, Task 2.1

**Complexity**: Medium

**Implementation Notes**:
- Cross-reference spawn path dependencies with file locations
- Estimate number of lines needing changes per file
- Identify any dynamic agent loading that could be fragile
- Document rollback strategy for each breaking change

---

## Task Group 3: Report Generation

### Task 3.1: Generate NAMING_AUDIT_REPORT.md
**Description**: Compile all findings into comprehensive audit report documenting current state, issues found, and recommended changes.

**Acceptance Criteria**:
- Report includes executive summary with key findings
- Section 1: Agent File Audit Results (findings from Task 1.1)
- Section 2: Runtime Code Audit Results (findings from Task 1.2)
- Section 3: Documentation Audit Results (findings from Task 1.3)
- Section 4: Test Audit Results (findings from Task 1.4)
- Section 5: Dependency Map (from Task 2.1)
- Section 6: Breaking Change Analysis (from Task 2.2)
- Section 7: Recommended Rename Plan
  - support/drill_writer.md → support/documentation_writer.md
  - support/logistics_manager.md → support/project_manager.md
  - support/visual_tech.md → support/architect_assistant.md
- Section 8: Impact Assessment (estimated effort, risk level)
- Report saved to output directory

**Dependencies**: All tasks in Group 1 and Group 2

**Complexity**: Medium

**Implementation Notes**:
- Use structured markdown format for easy parsing
- Include file counts, line counts, issue counts
- Provide specific line references for critical issues
- Include before/after examples for proposed renames
- Estimate effort in person-hours for Milestone 2 implementation

---

### Task 3.2: Generate Change Inventory Checklist
**Description**: Create actionable checklist of specific files and lines that need changes in Milestone 2.

**Acceptance Criteria**:
- Checklist format: [ ] Filename - Line X: Change description
- Organized by file type: Agent Definitions, Runtime Code, Tests, Documentation
- Each item includes:
  - File path
  - Line number or section
  - Current text
  - Proposed replacement text
  - Priority (P0-Critical, P1-High, P2-Medium, P3-Low)
- Saved as CHANGE_INVENTORY.md in output directory

**Dependencies**: Task 3.1

**Complexity**: Simple

**Implementation Notes**:
- Format for easy copy-paste into implementation tasks
- Include grep/sed commands where appropriate
- Cross-reference with breaking change analysis
- Order by implementation priority

---

### Task 3.3: Generate Agent Terminology Dictionary
**Description**: Create reference document mapping drum corps terms to standard development terms.

**Acceptance Criteria**:
- Table format: Old Term | New Term | Context | Rationale
- Includes all drum corps terminology found in audit
- Includes support/ agent name mappings
- Includes any field-specific terminology that should be generalized
- Saved as TERMINOLOGY_DICTIONARY.md in output directory

**Dependencies**: Task 1.1, Task 1.2, Task 1.3

**Complexity**: Simple

**Implementation Notes**:
- Focus on terminology that appears in multiple files
- Provide industry-standard alternatives
- Include search regex patterns for finding each term
- Add notes on edge cases (e.g., "field" in "output_field" is OK)

---

## Task Group 4: Validation & Quality Checks

### Task 4.1: Validate File Name Conventions
**Description**: Verify all agent files follow snake_case convention and match folder structure.

**Acceptance Criteria**:
- List of all agent .md files with their naming convention (snake_case, camelCase, kebab-case, etc.)
- Identify any files not following snake_case pattern
- Verify folder structure matches agent category (leadership/, coordinators/, etc.)
- Document any mismatches between filename and agent declaration inside file
- Report includes compliant vs. non-compliant counts

**Dependencies**: Task 1.1

**Complexity**: Simple

**Implementation Notes**:
- Use regex to validate snake_case: `^[a-z_][a-z0-9_]*\.md$`
- Check for consistency: filename should match agent name in file header
- Document exceptions (if any are intentional)

---

### Task 4.2: Cross-Reference Architecture Document
**Description**: Verify that architecture document matches actual codebase structure.

**Acceptance Criteria**:
- Architecture document (epgc_architecture.md) compared against actual files
- Identify agents mentioned in architecture but missing in codebase
- Identify agents in codebase but not documented in architecture
- Verify spawn path examples in architecture are correct
- Document any discrepancies with severity assessment

**Dependencies**: Task 1.1, Task 2.1

**Complexity**: Simple

**Implementation Notes**:
- Parse agent hierarchy from architecture document
- Compare against actual directory listing
- Validate spawn path syntax in architecture examples
- Note if architecture is ahead of or behind actual implementation

---

## Task Summary

| Task ID | Task Name | Complexity | Estimated Effort | Dependencies |
|---------|-----------|------------|------------------|--------------|
| 1.1 | Scan Agent Definition Files | Medium | 2 hours | None |
| 1.2 | Scan Runtime Code for Agent References | Medium | 2 hours | None |
| 1.3 | Scan Documentation Files | Simple | 1 hour | None |
| 1.4 | Scan Test Files for Agent References | Medium | 2 hours | None |
| 2.1 | Map Agent Spawn Path Dependencies | Medium | 2 hours | 1.1, 1.2, 1.4 |
| 2.2 | Identify Breaking Change Points | Medium | 2 hours | 1.1, 1.2, 1.3, 1.4, 2.1 |
| 3.1 | Generate NAMING_AUDIT_REPORT.md | Medium | 3 hours | All Group 1 & 2 |
| 3.2 | Generate Change Inventory Checklist | Simple | 1 hour | 3.1 |
| 3.3 | Generate Agent Terminology Dictionary | Simple | 1 hour | 1.1, 1.2, 1.3 |
| 4.1 | Validate File Name Conventions | Simple | 1 hour | 1.1 |
| 4.2 | Cross-Reference Architecture Document | Simple | 1 hour | 1.1, 2.1 |

**Total Estimated Effort**: 18 hours

---

## Implementation Order

1. **Phase 1: Discovery (Parallel)** - Tasks 1.1, 1.2, 1.3, 1.4, 4.1 can run in parallel
2. **Phase 2: Analysis** - Tasks 2.1, 2.2, 4.2 (requires Phase 1 completion)
3. **Phase 3: Reporting** - Tasks 3.1, 3.2, 3.3 (requires Phase 2 completion)

---

## Risk Assessment

### Low Risk Tasks
- Task 1.3 (Documentation Scan) - Read-only operation
- Task 4.1 (File Name Validation) - Automated checking

### Medium Risk Tasks
- Task 2.1 (Dependency Mapping) - Requires accurate parsing, but no code changes
- Task 3.1 (Report Generation) - Synthesis of multiple inputs, potential for missed items

### High Risk Tasks
- Task 2.2 (Breaking Change Identification) - Critical for Milestone 2 success; incomplete analysis could cause production issues

---

## Quality Gates

- All scanning tasks must achieve 100% file coverage (no agent files skipped)
- Dependency map must be validated against manual code review (spot-check 20% of spawn paths)
- NAMING_AUDIT_REPORT.md must be peer-reviewed before Milestone 2 begins
- Breaking change analysis must include rollback procedures

---

## Output Artifacts

All artifacts saved to: `/Users/mattbillock/Development/ai_exploration/ensemble/src/field/ensemble_ui/output/`

1. **NAMING_AUDIT_REPORT.md** - Comprehensive audit findings
2. **CHANGE_INVENTORY.md** - Actionable checklist for Milestone 2
3. **TERMINOLOGY_DICTIONARY.md** - Old → New terminology mapping
4. **DEPENDENCY_GRAPH.json** - Machine-readable spawn path dependencies
5. **BREAKING_CHANGES.md** - Detailed impact analysis

---

## Notes for TDD Coordinator

This milestone is **documentation and analysis only**. No code changes, no test writing. All tasks are:
- Reading existing files
- Analyzing content
- Generating reports

Recommended approach:
1. Use automated scanning tools (grep, ripgrep, ast parsers) for initial discovery
2. Manual review for context-sensitive issues
3. Structured data formats (JSON/YAML) for machine-readable outputs
4. Markdown reports for human readability
5. Include specific line numbers and file paths for all findings

**Critical**: Do not make any changes to agent files, spawn paths, or runtime code during this milestone. All changes happen in Milestone 2.
