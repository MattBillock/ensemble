# Backend Tasks - Katamari Achievement System Enhancement

## Milestone Overview
Add KATAMARI category to AchievementCategory enum and 10 new Katamari Damacy themed achievements to enhance the existing achievement system.

## Task Breakdown

### Task 1: Add KATAMARI Category Enum
**Priority:** HIGH (Foundation)  
**Complexity:** SIMPLE  
**Dependencies:** None  
**Estimated Time:** 5 minutes  

**Description:**
Add `KATAMARI = "katamari"` to the existing `AchievementCategory` enum in achievements.py.

**Acceptance Criteria:**
- [ ] `KATAMARI` enum value added to `AchievementCategory` class
- [ ] Enum value uses lowercase string "katamari" for consistency
- [ ] No syntax errors in enum definition
- [ ] Existing enum values remain unchanged

**Files to Modify:**
- `src/runtime/agents/achievements.py`

**Trigger Conditions:** None

---

### Task 2: Create Common Rarity Katamari Achievements (3 achievements)
**Priority:** HIGH  
**Complexity:** SIMPLE  
**Dependencies:** Task 1 (KATAMARI enum)  
**Estimated Time:** 15 minutes  

**Description:**
Create 3 common rarity Katamari achievements focused on basic gameplay mechanics and getting started.

**Achievement Definitions:**
1. **katamari_start** - "We Love Katamari" - First task completion (10 points, ⭐)
2. **sticky_situation** - "Sticky Situation" - Recovery from failures (10 points, 🍯) 
3. **royal_rainbow** - "Royal Rainbow" - Complete different task types (15 points, 🌈)

**Acceptance Criteria:**
- [ ] 3 Achievement objects created with KATAMARI category
- [ ] All have AchievementRarity.COMMON
- [ ] Points range 10-15 following existing pattern
- [ ] Trigger conditions use existing patterns (event-based, count-based)
- [ ] Creative names and descriptions reference Katamari themes
- [ ] Appropriate emoji icons selected

**Files to Modify:**
- `src/runtime/agents/achievements.py`

**Trigger Conditions:**
- First execution events
- Failure recovery patterns
- Task diversity tracking

---

### Task 3: Create Uncommon Rarity Katamari Achievements (2 achievements)
**Priority:** MEDIUM  
**Complexity:** SIMPLE  
**Dependencies:** Task 1 (KATAMARI enum)  
**Estimated Time:** 10 minutes  

**Description:**
Create 2 uncommon rarity Katamari achievements for intermediate progression.

**Achievement Definitions:**
1. **cousin_collaboration** - "Cousin Collaboration" - Multi-agent cooperation (25 points, 👥)
2. **cosmic_collection** - "Cosmic Collection" - Resource gathering milestone (30 points, 🌌)

**Acceptance Criteria:**
- [ ] 2 Achievement objects created with KATAMARI category  
- [ ] All have AchievementRarity.UNCOMMON
- [ ] Points range 25-35 following existing pattern
- [ ] Trigger conditions focus on collaboration and collection
- [ ] Names reference Katamari cousin characters and cosmic themes

**Files to Modify:**
- `src/runtime/agents/achievements.py`

**Trigger Conditions:**
- Multi-agent collaboration events
- File/resource collection counts

---

### Task 4: Create Rare Rarity Katamari Achievements (3 achievements)
**Priority:** MEDIUM  
**Complexity:** MEDIUM  
**Dependencies:** Task 1 (KATAMARI enum)  
**Estimated Time:** 15 minutes  

**Description:**
Create 3 rare rarity Katamari achievements for advanced gameplay mechanics.

**Achievement Definitions:**
1. **size_matters** - "We Love Katamari - Size Matters" - Scale progression (45 points, 📏)
2. **time_attack** - "Katamari Time Attack" - Speed completion (50 points, ⏰)
3. **king_of_cosmos** - "King of All Cosmos" - Leadership/orchestration (55 points, 👑)

**Acceptance Criteria:**
- [ ] 3 Achievement objects created with KATAMARI category
- [ ] All have AchievementRarity.RARE  
- [ ] Points range 45-55 following existing pattern
- [ ] Trigger conditions involve complex metrics (time, scale, leadership)
- [ ] References to King of All Cosmos character and game mechanics

**Files to Modify:**
- `src/runtime/agents/achievements.py`

**Trigger Conditions:**
- Operation count thresholds
- Time-based performance metrics
- Agent orchestration patterns

---

### Task 5: Create Epic/Legendary Rarity Katamari Achievements (2 achievements)
**Priority:** LOW  
**Complexity:** MEDIUM  
**Dependencies:** Task 1 (KATAMARI enum)  
**Estimated Time:** 10 minutes  

**Description:**
Create 2 high-rarity Katamari achievements for exceptional accomplishments.

**Achievement Definitions:**
1. **everything_collector** - "I Rolled Up Everything" - Major milestone (150 points, 🌍, LEGENDARY)
2. **prince_upgrade** - "Prince of All Cosmos" - Excellence achievement (200 points, 🤴, LEGENDARY)

**Acceptance Criteria:**
- [ ] 2 Achievement objects created with KATAMARI category
- [ ] High rarity levels (EPIC/LEGENDARY)
- [ ] Points 150+ following existing legendary pattern  
- [ ] Trigger conditions for exceptional performance/milestones
- [ ] References to Prince character and ultimate game completion

**Files to Modify:**
- `src/runtime/agents/achievements.py`

**Trigger Conditions:**
- High task completion counts (50+)
- Success rate thresholds (95%+)
- Major milestone events

---

### Task 6: Validate Achievement Integration
**Priority:** HIGH  
**Complexity:** SIMPLE  
**Dependencies:** Tasks 2-5 (All achievements created)  
**Estimated Time:** 10 minutes  

**Description:**
Verify all 10 Katamari achievements are properly integrated into the ACHIEVEMENTS list and follow existing patterns.

**Acceptance Criteria:**
- [ ] All 10 achievements added to ACHIEVEMENTS list
- [ ] Unique IDs with no conflicts
- [ ] Proper rarity distribution (3 common, 2 uncommon, 3 rare, 2 legendary)
- [ ] All use KATAMARI category
- [ ] Points progression follows existing patterns
- [ ] Trigger conditions use established patterns
- [ ] No syntax errors in achievement definitions

**Files to Modify:**
- `src/runtime/agents/achievements.py`

**Validation Checklist:**
- ID uniqueness across all achievements
- Category consistency
- Rarity distribution balance
- Points alignment with rarity
- Trigger condition validity

---

### Task 7: Create Unit Tests for Katamari Achievements
**Priority:** MEDIUM  
**Complexity:** MEDIUM  
**Dependencies:** Task 6 (All achievements integrated)  
**Estimated Time:** 20 minutes  

**Description:**
Create comprehensive unit tests to validate Katamari achievement definitions and ensure no regressions.

**Test Coverage:**
- KATAMARI category exists in enum
- All 10 achievements have correct structure
- Rarity distribution is balanced  
- Trigger conditions are valid
- No ID conflicts with existing achievements

**Acceptance Criteria:**
- [ ] Test file created with comprehensive coverage
- [ ] Tests validate achievement structure and metadata
- [ ] Tests verify KATAMARI category integration
- [ ] Tests confirm no conflicts with existing achievements
- [ ] All tests pass without errors

**Files to Create:**
- `tests/test_katamari_achievements.py`

**Test Functions:**
- `test_katamari_category_exists()`
- `test_katamari_achievements_count()`
- `test_katamari_achievements_structure()`
- `test_katamari_rarity_distribution()`
- `test_katamari_achievement_ids_unique()`

---

## Task Dependencies

```
Task 1 (KATAMARI Enum) 
    ├── Task 2 (Common Achievements)
    ├── Task 3 (Uncommon Achievements)  
    ├── Task 4 (Rare Achievements)
    └── Task 5 (Epic/Legendary Achievements)
            │
            ▼
        Task 6 (Integration Validation)
            │
            ▼
        Task 7 (Unit Tests)
```

## Implementation Notes

### Rarity Distribution
- **Common (3):** 10-15 points, basic mechanics
- **Uncommon (2):** 25-35 points, intermediate goals
- **Rare (3):** 45-55 points, advanced achievements  
- **Legendary (2):** 150-200 points, exceptional milestones

### Trigger Condition Patterns
Following existing patterns:
- Event-based: `{\"event\": \"first_execution\"}`
- Count-based: `{\"successful_executions\": {\"min\": 10}}`
- Time-based: `{\"duration_ms\": {\"max\": 30000}}`
- Success rate: `{\"success_rate\": {\"min\": 0.95}, \"min_executions\": 20}`

### Code Quality Standards
- Follow existing Achievement dataclass pattern exactly
- Use descriptive IDs with katamari_ prefix
- Include creative names referencing Katamari Damacy
- Maintain humorous tone consistent with existing achievements
- Use appropriate emoji icons that capture Katamari's whimsical nature

## Success Criteria Summary

**Functional Requirements:**
- [ ] KATAMARI category added to enum
- [ ] Exactly 10 achievements created and integrated
- [ ] All achievements use KATAMARI category
- [ ] Proper rarity and points distribution
- [ ] Valid trigger conditions using existing patterns

**Quality Requirements:**
- [ ] Creative Katamari-themed names and descriptions
- [ ] No conflicts with existing achievements  
- [ ] Comprehensive unit test coverage
- [ ] Code follows existing patterns exactly
- [ ] All tests pass (existing + new)

**Integration Requirements:**
- [ ] Achievements appear in existing UI without changes
- [ ] Database correctly stores new achievement awards
- [ ] Existing achievement functionality unchanged
- [ ] Performance impact negligible

## Risk Mitigation

**ID Conflicts:** Manual verification during Task 6
**Trigger Condition Issues:** Use only proven existing patterns  
**Performance Impact:** Minimal - only 10 additional items in existing list
**Breaking Changes:** None - pure additive changes to data structure

---

## Ready for Implementation

This task breakdown provides clear, actionable steps for the TDD Coordinator to implement the Katamari achievement system enhancement. Each task is well-defined with specific acceptance criteria and follows the existing codebase patterns to ensure seamless integration.