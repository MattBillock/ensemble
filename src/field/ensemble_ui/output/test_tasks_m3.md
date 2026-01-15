# Test Tasks - Milestone 3: Integration Testing & Verification

## Overview
Verify all components work together: backend enum/achievements, frontend filter/badges, and existing tests continue to pass.

**Total Tasks**: 3  
**Estimated Complexity**: Simple

---

## Task List

### Task 1: Run Existing Achievement Tests
**ID**: TEST-M3-001  
**Complexity**: Simple

**Description**:
Run all existing achievement-related tests to verify no regressions from our changes.

**Acceptance Criteria**:
- [ ] All existing achievement tests pass
- [ ] No new test failures introduced
- [ ] Backend achievements.py imports correctly
- [ ] Frontend component tests pass

**Commands**:
```bash
# Backend tests
pytest tests/test_achievements.py -v

# Frontend tests (if applicable)
cd src/field/ensemble_ui/frontend && npm test
```

**Dependencies**: 
- Milestone 1 (Backend) complete
- Milestone 2 (Frontend) complete

---

### Task 2: Backend Integration Verification
**ID**: TEST-M3-002  
**Complexity**: Simple

**Description**:
Verify backend changes integrate properly with achievement system.

**Acceptance Criteria**:
- [ ] BRASS_BAND category is accessible via AchievementCategory enum
- [ ] 15 brass_band achievements load with ACHIEVEMENTS list
- [ ] Can filter achievements by category="brass_band"
- [ ] Achievement registry/manager recognizes new achievements
- [ ] No import errors in achievement module

**Test Approach**:
```python
# Manual verification script
from src.runtime.agents.achievements import AchievementCategory, ACHIEVEMENTS

# Verify enum
assert AchievementCategory.BRASS_BAND.value == "brass_band"

# Verify achievements
brass_band_achievements = [a for a in ACHIEVEMENTS if a.category == AchievementCategory.BRASS_BAND]
assert len(brass_band_achievements) == 15

# Verify no duplicates
ids = [a.id for a in brass_band_achievements]
assert len(ids) == len(set(ids))
```

**Dependencies**: 
- Task BE-M1-001 and BE-M1-002 complete

---

### Task 3: Frontend Integration Verification
**ID**: TEST-M3-003  
**Complexity**: Simple

**Description**:
Verify frontend filter and badge work correctly with brass_band category.

**Acceptance Criteria**:
- [ ] brass_band filter appears in dropdown
- [ ] Selecting brass_band filter displays correct achievements
- [ ] getCategoryBadge returns proper badge for brass_band
- [ ] No JavaScript console errors
- [ ] Badge displays with correct styling
- [ ] Filter reset returns to all achievements

**Manual Test Checklist**:
1. Load AchievementsDashboard in browser
2. Verify "Brass Band 🎺" option in filter dropdown
3. Select brass_band filter
4. Verify only brass_band achievements display
5. Verify badges show with gold/warning styling
6. Check browser console for errors
7. Click "All Categories" to reset
8. Verify all achievements display again

**Dependencies**: 
- Tasks FE-M2-001, FE-M2-002, FE-M2-003 complete
- Backend achievements available (or mock data)

---

## End-to-End Test Scenario

### Scenario: User Filters by Brass Band Category

**Pre-conditions**:
- Backend has BRASS_BAND category and 15 achievements
- Frontend has brass_band filter and badge support

**Steps**:
1. User opens application
2. User navigates to Achievements Dashboard
3. User clicks category filter dropdown
4. User sees "Brass Band 🎺" option
5. User selects "Brass Band"
6. Dashboard updates to show only brass_band achievements
7. Each achievement card displays "🎺 Brass Band" badge
8. User selects "All Categories"
9. Dashboard shows all achievements again

**Expected Results**:
- Filter correctly queries backend for category="brass_band"
- Only brass_band achievements displayed when filtered
- Badge styling is visually distinct (gold/warning theme)
- No errors in browser console or backend logs

---

## Regression Test Checklist

### Backend Regressions
- [ ] Other categories (SKA, etc.) still work
- [ ] Achievement triggering still works
- [ ] Points calculation still works
- [ ] Agent class filtering still works

### Frontend Regressions
- [ ] Other category filters still work
- [ ] Achievement cards render correctly
- [ ] Rarity badges display correctly
- [ ] Points display correctly
- [ ] Achievement unlock animations work

---

## Dependencies and Order

```
Milestone 1 Complete (Backend)
    ↓
Milestone 2 Complete (Frontend)
    ↓
TEST-M3-001 (Run Existing Tests)
    ↓
TEST-M3-002 (Backend Integration)
    ↓
TEST-M3-003 (Frontend Integration)
```

---

## Success Metrics

**Definition of Done**:
1. ✅ All existing tests pass
2. ✅ BRASS_BAND category accessible and functional
3. ✅ 15 achievements correctly categorized
4. ✅ Frontend filter works correctly
5. ✅ Badge displays with proper styling
6. ✅ No console errors
7. ✅ No regressions in existing functionality

---

**Status**: Ready for Verification (after Milestones 1 & 2)  
**Next Step**: Execute tests after implementation complete
