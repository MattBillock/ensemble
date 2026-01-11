# Naming Audit Report
## Milestone 1: Comprehensive Naming & Terminology Audit

**Audit Date**: 2025-01-10
**Auditor**: TDD Coordinator
**Scope**: All agent definition files, runtime code, and documentation

---

## Executive Summary

This audit identifies all terminology issues, drum corps references, and naming inconsistencies across the Ensemble codebase. The audit found:

- **3 support agents requiring rename** (drill_writer, logistics_manager, visual_tech)
- **17 drum corps terminology references** in active agent files
- **4 obsolete/legacy role references** (Snare, Tenor, Brass Coordinator, Percussion Coordinator)
- **Multiple spawn path dependencies** that will break on rename

---

## Section 1: Agent Files Requiring Rename

### 1.1 Support Folder Agents (HIGH PRIORITY)

| Current File | Current Name | Proposed Name | Proposed File |
|--------------|--------------|---------------|---------------|
| `support/drill_writer.md` | Drill Writer | **Documentation Writer** | `support/documentation_writer.md` |
| `support/logistics_manager.md` | Logistics Manager | **Code Explorer** or **Codebase Navigator** | `support/code_explorer.md` |
| `support/visual_tech.md` | Visual Tech | **Code Refactorer** or **Quality Reviewer** | `support/code_refactorer.md` |

### 1.2 Rationale for Renames

**drill_writer.md → documentation_writer.md**
- "Drill Writer" and "drill charts" are marching band terminology
- Purpose is clearly documentation writing (API docs, user guides, README)
- Industry-standard term: "Documentation Writer" or "Technical Writer"

**logistics_manager.md → code_explorer.md**
- "Surveys the venue" is performance/show terminology
- Purpose is codebase exploration and mapping
- Industry-standard terms: "Code Explorer", "Codebase Analyst", "Code Navigator"

**visual_tech.md → code_refactorer.md**
- "Cleans spacing, alignment, and technique" is drum corps terminology
- Purpose is code refactoring in TDD REFACTOR phase
- Industry-standard term: "Code Refactorer" or "Quality Reviewer"

---

## Section 2: Drum Corps Terminology Found in Agent Files

### 2.1 Leadership Folder

**leadership/development_manager.md**
- Line 44: `"You drive the show from concept through performance"` 
  - Replace with: "You drive development from concept through delivery"

**leadership/system_architect.md**
- Line 4: `"Designs the show formations and execution strategy"`
  - Replace with: "Designs the system architecture and implementation strategy"
- Line 124: `"show you've thought through options"` (acceptable - common English usage)

**leadership/tdd_coordinator.md**
- Line 4: `"Directs and coordinates the ensemble through rehearsal. Manages tempo, attitude, and execution."`
  - Replace with: "Directs and coordinates the development team through implementation cycles."
- Line 46-51: References to "Section Techs" terminology
  - Replace with: "Specialist Agents"
- Line 122, 129: `"spawns Snare"` references
  - Replace with: "spawns Unit Test Writer"

### 2.2 Coordinators Folder

**coordinators/test_coordinator.md**
- Line 4: `"Coordinates with Backend Captain and Frontend Captain"`
  - Replace with: "Coordinates with Backend Lead and Frontend Lead"

### 2.3 Testers Folder

**testers/unit_test_lead.md**
- Line 4: `"Guides Snare to create comprehensive, effective tests"`
  - Replace with: "Guides Unit Test Writer to create comprehensive, effective tests"
- Line 11: `"Unit tests written by Snare"`
  - Replace with: "Unit tests written by Unit Test Writer"
- Line 44: `"You're a unit testing expert supervising Snare"`
  - Replace with: "You're a unit testing expert supervising Unit Test Writer"

**testers/integration_test_lead.md**
- Line 4: `"Writes tests that Tenor must pass"`
  - Replace with: "Writes tests that Integration Test Writer must pass"
- Line 46: `"supervising Tenor"`
  - Replace with: "supervising Integration Test Writer"
- Line 72: `"Tenor writes integration tests"`
  - Replace with: "Integration Test Writer writes tests"

### 2.4 Developers Folder

**developers/frontend_lead.md**
- Line 7: `"task assigned by Brass Coordinator"`
  - Replace with: "task assigned by Frontend Coordinator"
- Line 12: `"Task completion reported to Brass Coordinator"`
  - Replace with: "Task completion reported to Frontend Coordinator"
- Line 111, 165: Additional Brass Coordinator references
- Line 139: `"Dance Tech: UX patterns"`
  - Replace with: "UX Specialist: UX patterns" or remove

**developers/backend_lead.md**
- Line 7: `"task assigned by Brass Coordinator"`
  - Replace with: "task assigned by Backend Coordinator"
- Line 12: `"Task completion reported to Brass Coordinator"`
  - Replace with: "Task completion reported to Backend Coordinator"
- Line 102: `"Database needs with Synth Tech"`
  - Replace with: "Database needs with Database Specialist" or remove
- Line 109, 150, 178: Additional Brass/Synth Tech references

**developers/frontend_developer.md**
- Line 10: `"When supervised by Frontend Developer Tech"`
  - Replace with: "When supervised by Frontend Lead"
- Line 165: `"Frontend Developer Tech"`
  - Replace with: "Frontend Lead"

**developers/backend_developer.md**
- Line 120: `"Backend Developer Tech (backend development domain expert)"`
  - Replace with: "Backend Lead"

### 2.5 Designers Folder

**designers/style_developer.md**
- Line 8: `"Supervised by Style Developer Tech"`
  - Replace with: "Supervised by Style Lead" or "Supervised by Frontend Lead"
- Line 64: `"Style Developer Tech"`
  - Replace with: "Style Lead" or "Frontend Lead"

### 2.6 Testers Folder - Additional

**testers/unit_test_writer.md**
- Line 4: `"Precision test writing tech. ... Crisp, precise, catches mistakes."`
  - Replace with: "Precision test writing specialist. Writes failing unit tests that define requirements."

**testers/integration_test_writer.md**
- Line 8: `"Supervised by Integration Test Writer Tech"`
  - Replace with: "Supervised by Integration Test Lead"
- Line 55: `"Integration Test Writer Tech"`
  - Replace with: "Integration Test Lead"

### 2.7 Support Folder (to be renamed files)

**support/drill_writer.md**
- Line 1: `"# Drill Writer"` → "# Documentation Writer"
- Line 4: `"Creates comprehensive documentation... The 'drill charts' that guide future performers."`
  - Replace with: "Creates comprehensive documentation for the development team's work."
- Line 59: `"You are the Drill Writer - you create the drill charts that guide the ensemble."`
  - Replace with: "You are the Documentation Writer - you create documentation that guides developers."

**support/logistics_manager.md**
- Line 4: `"Surveys the 'venue' before the show begins."`
  - Replace with: "Explores the codebase before development begins."

**support/visual_tech.md**
- Line 1: `"# Visual Tech"` → "# Code Refactorer"
- Line 4: `"Cleans spacing, alignment, and technique."`
  - Replace with: "Improves code quality, readability, and structure."

---

## Section 3: Spawn Path Dependencies

### 3.1 Current Spawn Paths Referencing support/ Agents

| Agent File | Line | Current Spawn Path | Impact |
|------------|------|-------------------|--------|
| leadership/tdd_coordinator.md | 51 | `"support/visual_tech"` | **WILL BREAK** on rename |
| leadership/tdd_coordinator.md | 110 | `spawn_agent("support/visual_tech", ...)` | **WILL BREAK** on rename |

### 3.2 No Direct Spawn References Found For

- `support/drill_writer.md` - Not currently spawned by any agent
- `support/logistics_manager.md` - Not currently spawned by any agent

### 3.3 Update Required

When renaming `visual_tech.md` → `code_refactorer.md`:
1. Update `leadership/tdd_coordinator.md` lines 51 and 110
2. Update any documentation referencing this path

---

## Section 4: Runtime Code Analysis

### 4.1 src/runtime/agents/tools.py

**SpawnAgentTool class (lines 140-220)**
- No hardcoded agent paths found
- Uses dynamic path resolution: `self.agent_types_dir / f"{agent_type}.md"`
- **SAFE**: Will work with renamed files automatically

### 4.2 src/runtime/agents/runtime.py

- No hardcoded agent paths found
- Agent definitions loaded dynamically from path
- **SAFE**: No changes needed

### 4.3 src/runtime/agents/definition.py

- No agent path references
- Pure parsing logic for markdown files
- **SAFE**: No changes needed

---

## Section 5: Documentation Analysis

### 5.1 README.md

- Uses correct modern terminology in most places
- Agent hierarchy section is accurate
- No drum corps references found
- **STATUS**: Clean

### 5.2 QUICKSTART.md

- No drum corps references
- **STATUS**: Clean

### 5.3 AGENT_REGISTRY.md

- Uses correct spawn paths
- Hierarchy diagram accurate
- References `support/` folder but not specific agent names
- **ACTION NEEDED**: Update after support agent renames

### 5.4 architecture.md

- Line at end: "Zero drum corps references" - accurate statement of intent
- **STATUS**: Clean

### 5.5 Other Documentation Files with Terminology Issues

The following files contain drum corps references based on grep search:
- MILESTONE_0_SUMMARY.md
- MILESTONE_0_ANALYSIS.md  
- COMPREHENSIVE_SYSTEM_REVIEW.md
- NAMING_REFACTOR_PLAN.md
- REFACTORING_ANALYSIS.md
- FUTURE_FEATURES.md
- ITERATIVE_IMPROVEMENT_PLAN.md

**Note**: These appear to be historical/planning documents that reference the ongoing naming refactor. They may not need updates if they're archival.

---

## Section 6: Legacy Role References

### 6.1 Obsolete Role Names Still in Use

| Obsolete Name | Modern Equivalent | Files Affected |
|---------------|-------------------|----------------|
| Snare | Unit Test Writer | testers/unit_test_lead.md, leadership/tdd_coordinator.md |
| Tenor | Integration Test Writer | testers/integration_test_lead.md |
| Brass Coordinator | Frontend/Backend Coordinator | developers/frontend_lead.md, developers/backend_lead.md |
| Percussion Coordinator | Test Coordinator | testers/unit_test_lead.md, testers/integration_test_lead.md |
| Dance Tech | (remove or UX Specialist) | developers/frontend_lead.md |
| Synth Tech | (remove or Database Specialist) | developers/backend_lead.md |
| Section Techs | Specialist Agents | leadership/tdd_coordinator.md |
| Frontend Developer Tech | Frontend Lead | developers/frontend_developer.md |
| Backend Developer Tech | Backend Lead | developers/backend_developer.md |
| Style Developer Tech | Style Lead | designers/style_developer.md |
| Integration Test Writer Tech | Integration Test Lead | testers/integration_test_writer.md |

---

## Section 7: Summary Statistics

| Category | Count |
|----------|-------|
| Files requiring rename | 3 |
| Agent files with terminology issues | 14 |
| Total terminology instances to fix | ~45 |
| Spawn paths to update | 2 |
| Runtime files needing changes | 0 |
| Documentation files needing updates | 1 (AGENT_REGISTRY.md) |

---

## Section 8: Risk Assessment

### 8.1 High Risk Changes

1. **Renaming support/visual_tech.md**
   - Actively spawned by TDD Coordinator
   - Must update spawn paths before or simultaneously with rename
   - Test after rename to verify TDD workflow still works

### 8.2 Medium Risk Changes

1. **Terminology updates in agent instructions**
   - Could affect agent behavior if wording is materially different
   - Should maintain semantic meaning while updating terminology

### 8.3 Low Risk Changes

1. **Renaming drill_writer.md and logistics_manager.md**
   - Not currently spawned by any agent
   - Can be renamed independently

2. **Documentation updates**
   - No functional impact
   - Can be done at any time

---

## Appendix A: Grep Commands Used

```bash
# Find drum corps terminology
grep -rn -i -E "(drill_writer|logistics_manager|visual_tech|drill|formation|tempo|Snare|Tenor|rehearsal|show|venue)" <folder>/*.md

# Find section/tech references  
grep -rn -i -E "(brass|percussion|woodwind|color.*guard|pit|guard|captain|marcher|field|section|tech)" <folder>/*.md

# Find spawn paths
grep -rn "spawn_agent" <folder>/*.md
```

---

*Report generated as part of Milestone 1: Naming Audit & Discovery*
