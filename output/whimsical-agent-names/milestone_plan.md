# Whimsical Agent Names - Milestone Plan

## Project Overview
Replace cryptic alphanumeric agent identifiers with whimsical, memorable, American pop culture-inspired names that are family-friendly and fun.

## Milestone Structure

### Milestone 1: Core Name Generation Utility (Foundation)
**Objective**: Create the deterministic name generation utility that transforms agent IDs into whimsical names.

**Deliverables**:
1. `frontend/src/utils/whimsicalNames.js` - Core utility with:
   - Word lists (adjectives and nouns from requirements)
   - Deterministic hash function for agent IDs
   - `generateWhimsicalName(agentId)` function
   - Optional: `getAgentEmoji(agentType)` helper

2. `frontend/src/utils/__tests__/whimsicalNames.test.js` - Unit tests:
   - Determinism: same ID → same name every time
   - Coverage: different IDs produce varied names
   - Edge cases: empty strings, null, special characters

**Acceptance Criteria**:
- [ ] Function returns consistent names for same input
- [ ] Names follow "[Adjective] [Noun]" format
- [ ] All unit tests pass
- [ ] Word lists contain all items from requirements

**Dependencies**: None

**Estimated Effort**: Small

---

### Milestone 2: UI Component Integration
**Objective**: Integrate whimsical names into all relevant UI components.

**Deliverables**:
1. Update `AgentHierarchyTree.jsx` - Display whimsical names in tree view
2. Update `AgentStatusPane.jsx` - Show whimsical name as primary, technical ID secondary
3. Update `AgentSummaryPane.jsx` - Use whimsical names in summary cards
4. Update `ActivityFeed.jsx` - Show whimsical names in activity entries

**Acceptance Criteria**:
- [ ] All four components display whimsical names prominently
- [ ] Technical IDs remain accessible (tooltip or muted secondary text)
- [ ] Visual styling matches design requirements (bold primary, muted secondary)
- [ ] Optional emojis based on agent type display correctly
- [ ] All existing component tests pass
- [ ] No UI regressions

**Dependencies**: Milestone 1 complete

**Estimated Effort**: Medium

---

## Implementation Notes

### Technical Decisions
- **Hash Algorithm**: Use a simple string hashing function (e.g., djb2 or similar) that works in browser
- **Word List Storage**: Static arrays in the utility file
- **No Backend Changes**: All name generation is client-side only

### Risk Assessment
- **Low Risk**: Frontend-only change with clear scope
- **Testing Strategy**: Unit tests for utility, integration tests for components
- **Rollback Plan**: Revert component changes if issues arise

## Timeline Summary
| Milestone | Description | Effort | Dependencies |
|-----------|-------------|--------|--------------|
| 1 | Core Name Generation Utility | Small | None |
| 2 | UI Component Integration | Medium | M1 |

## Success Metrics
1. All agent identifiers display whimsical names in the UI
2. Names are deterministic (same ID = same name every time)
3. Technical IDs remain accessible for debugging
4. All existing tests pass
5. UI remains functional with no regressions
