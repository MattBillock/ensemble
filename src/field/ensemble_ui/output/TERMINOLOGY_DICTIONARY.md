# Terminology Dictionary
## Drum Corps → Software Development Mapping

**Purpose**: Reference document for translating legacy terminology to industry-standard terms.
**Audience**: Developers updating agent files, documentation writers

---

## Agent/Role Name Mappings

| Old Term | New Term | Context | Rationale |
|----------|----------|---------|-----------|
| Drill Writer | Documentation Writer | support/ agent | "Drill charts" are marching band diagrams; documentation is the software equivalent |
| Logistics Manager | Code Explorer | support/ agent | "Venue survey" is show terminology; codebase exploration is the software equivalent |
| Visual Tech | Code Refactorer | support/ agent | "Visual cleaning" is performance terminology; code refactoring is the software equivalent |
| Snare | Unit Test Writer | testers/ role | Snare drummers keep time; unit tests keep code correct |
| Tenor | Integration Test Writer | testers/ role | Tenor drummers provide rhythm; integration tests ensure components work together |
| Brass Coordinator | Backend/Frontend Coordinator | coordinators/ | Brass section leader; use specific coordinator name (Backend or Frontend) |
| Percussion Coordinator | Test Coordinator | coordinators/ | Percussion section leader; tests are now the coordination focus |
| Dance Tech | UX Specialist | developers/ specialist | Dance/color guard tech; UX focuses on user experience |
| Synth Tech | Database Specialist | developers/ specialist | Synthesizer tech; databases store and manage data |
| Section Techs | Specialist Agents | leadership/ | Section technicians; specialist agents assist with specific tasks |
| Frontend Developer Tech | Frontend Lead | developers/ | Section leader terminology; use "Lead" for clarity |
| Backend Developer Tech | Backend Lead | developers/ | Section leader terminology; use "Lead" for clarity |
| Style Developer Tech | Style Lead or Frontend Lead | designers/ | Section leader terminology; style work often done by frontend lead |
| Integration Test Writer Tech | Integration Test Lead | testers/ | Section leader terminology; use "Lead" for clarity |
| Captain | Lead | all | Military/band terminology; "Lead" is software industry standard |
| Performer | Developer/Agent | all | Show terminology; developer or agent is software equivalent |
| Ensemble | Team or Agent Swarm | all | Musical group; software team or agent collective |

---

## Activity/Process Term Mappings

| Old Term | New Term | Context | Rationale |
|----------|----------|---------|-----------|
| Show | Delivery/Release | project lifecycle | Performance event; software delivery is the equivalent |
| Rehearsal | Development Cycle | iteration process | Practice sessions; development cycles are iterative work |
| Performance | Production Deployment | final output | Show performance; production is where software runs |
| Drill Charts | Documentation | output artifacts | Marching formations; documentation guides development |
| Formation | Architecture | system design | Physical arrangement; architecture is software arrangement |
| Tempo | Pace/Velocity | workflow speed | Musical speed; velocity is agile terminology |
| Venue | Codebase/Environment | work location | Physical location; codebase is where code lives |
| Field | Project/Workspace | work area | Marching field; project or workspace is software equivalent |
| Marching | Progress/Iteration | movement | Physical movement; progress through iterations |

---

## Phrase Mappings

| Old Phrase | New Phrase | Location |
|------------|------------|----------|
| "drive the show from concept through performance" | "drive development from concept through delivery" | leadership/development_manager.md |
| "Designs the show formations" | "Designs the system architecture" | leadership/system_architect.md |
| "through rehearsal" | "through development cycles" | leadership/tdd_coordinator.md |
| "Manages tempo, attitude, and execution" | "Manages pace, quality, and execution" | leadership/tdd_coordinator.md |
| "drill charts that guide future performers" | "documentation that guides developers" | support/drill_writer.md |
| "Surveys the venue" | "Explores the codebase" | support/logistics_manager.md |
| "Cleans spacing, alignment, and technique" | "Improves code quality, readability, and structure" | support/visual_tech.md |
| "Guides Snare" | "Guides Unit Test Writer" | testers/unit_test_lead.md |
| "supervising Tenor" | "supervising Integration Test Writer" | testers/integration_test_lead.md |
| "task assigned by Brass Coordinator" | "task assigned by [Backend/Frontend] Coordinator" | developers/*_lead.md |

---

## Search Patterns for Finding Issues

### High-Priority Patterns (definitely need fixing)
```regex
# File names
drill_writer
logistics_manager
visual_tech

# Role references
\bSnare\b
\bTenor\b
Brass\s+Coordinator
Percussion\s+Coordinator
Section\s+Tech
```

### Medium-Priority Patterns (context-dependent)
```regex
# May be OK in some contexts
\bshow\b              # "show you've thought" is OK; "drive the show" is not
\bfield\b             # "output_field" is OK; "marching field" is not
\bperformance\b       # Code performance is OK; show performance is not
\bformation\b         # Data formation OK; drill formation not
```

### Low-Priority Patterns (rarely an issue)
```regex
# Usually fine in software context
\btempo\b             # Usually OK in technical context
\brehearsal\b         # Rare in codebase
\bvenue\b             # Rare in codebase
```

---

## False Positives to Ignore

These terms appear in the codebase but are **NOT** drum corps terminology:

| Term | Context | Why It's OK |
|------|---------|-------------|
| show | "show you've thought through options" | Common English usage |
| performance | "code performance", "performance metrics" | Software performance |
| field | "input_field", "output_field", "field.py" | Data/class fields |
| ensemble | In project name "Ensemble" | Project name (keep) |
| section | "code section", "section of the file" | Document structure |
| tech | "technology", "technical" | General tech term |

---

## Grep Commands for Audit

```bash
# Find all drum corps agent names
grep -rn -E "(drill_writer|logistics_manager|visual_tech)" . --include="*.md" --include="*.py"

# Find role references (case-insensitive)
grep -rni -E "\b(Snare|Tenor)\b" leadership/ coordinators/ developers/ testers/ designers/ support/

# Find Brass/Percussion Coordinator
grep -rni "Brass.*Coordinator\|Percussion.*Coordinator" .

# Find Section Tech references
grep -rni "Section.*Tech\|Developer.*Tech\|Writer.*Tech" .

# Find show/rehearsal/venue in context
grep -rni -E "(drive the show|through rehearsal|survey.*venue)" .
```

---

## Replacement sed Commands

```bash
# Warning: Test these in dry-run mode first!

# Replace Snare with Unit Test Writer (case-sensitive)
sed -i '' 's/Snare/Unit Test Writer/g' testers/unit_test_lead.md

# Replace Tenor with Integration Test Writer
sed -i '' 's/Tenor/Integration Test Writer/g' testers/integration_test_lead.md

# Replace Brass Coordinator with specific coordinator
# Note: Must manually determine if Backend or Frontend
sed -i '' 's/Brass Coordinator/Backend Coordinator/g' developers/backend_lead.md
sed -i '' 's/Brass Coordinator/Frontend Coordinator/g' developers/frontend_lead.md
```

---

## Notes for Implementation

1. **Order matters**: Rename files before updating spawn paths in other files
2. **Case sensitivity**: Some patterns are case-sensitive (Snare, Tenor)
3. **Context matters**: Read surrounding text before replacing
4. **Test after each phase**: Run `pytest` after major changes
5. **Use git**: Commit after each successful phase for easy rollback

---

*Generated as part of Milestone 1: Naming Audit & Discovery*
