# Katamari Damacy Achievements - Requirements Document

## Project Overview

**Project Name:** Katamari Damacy Achievements  
**Project ID:** 12a0e2a7  
**Created:** 2026-01-15  
**Executive Director:** Orchestrating implementation

## Vision

Add 10 new achievements from the "Katamari Damacy" category to the existing Ensemble achievements system. Katamari Damacy is a beloved Japanese video game where players roll a katamari (magic ball) around to collect objects and grow larger, with quirky humor and delightful chaos.

## Background: Katamari Damacy

Katamari Damacy (2004) is a unique puzzle-action video game created by Keita Takahashi. Key themes:
- **Rolling Ball Mechanics**: Start small, roll up objects to grow larger
- **Absurd Scale**: Begin picking up thumbtacks, end up rolling up buildings and mountains
- **Whimsical Humor**: Eccentric King of All Cosmos, bizarre storylines, surreal physics
- **Size Progression**: Measured in centimeters/meters, achieving specific size targets
- **Collection Gameplay**: Pick up everything from paper clips to skyscrapers
- **Time Limits**: Many levels have strict time constraints
- **Colorful Chaos**: Vibrant, playful aesthetics with Japanese quirkiness

## Objectives

1. **Add New Category**: Create `KATAMARI` achievement category in the enum
2. **Achievement Content**: Add exactly 10 Katamari Damacy themed achievements
3. **UI Updates**: Add katamari category to filter dropdown in AchievementsDashboard
4. **Maintain Consistency**: Follow existing achievement patterns for rarity, triggers, and points

## Scope

### In Scope

**Backend Changes** (`src/runtime/agents/achievements.py`):
- Add `KATAMARI = "katamari"` to `AchievementCategory` enum
- Add 10 new `Achievement` objects to the `ACHIEVEMENTS` list
- Include variety of rarities (common through legendary)

**Frontend Changes** (`src/field/ensemble_ui/frontend/src/components/AchievementsDashboard.jsx`):
- Add katamari category to filter dropdown with appropriate icon
- Add katamari to `getCategoryBadge` function
- Consider adding Katamari facts to fun facts section

### Out of Scope
- New API endpoints (using existing endpoints)
- Database schema changes (existing schema supports new category)
- New UI components beyond filter updates

## Achievement Definitions

### Theme Guidelines
Katamari achievements should reference:
- Rolling mechanics (rolling up objects, growing bigger)
- Size progression (centimeters to kilometers)  
- Collection themes (picking up various items)
- Time constraints and urgency
- The King of All Cosmos and royal family
- Absurd scale jumps (tiny to cosmic)
- Japanese terminology (katamari, cousin characters)

### Proposed Achievements (Exactly 10)

| ID | Name | Description | Rarity | Points | Icon |
|----|------|-------------|--------|--------|------|
| `katamari_start` | We Love Katamari | Completed your first task - starting to roll! | COMMON | 10 | 🌟 |
| `royal_rainbow` | Royal Rainbow | Successfully completed 5 different types of tasks | UNCOMMON | 25 | 🌈 |
| `cosmic_collection` | Cosmic Collection | Gathered 25+ files/resources in a single session | RARE | 45 | 🌌 |
| `king_of_cosmos` | King of All Cosmos | Orchestrated 10+ sub-agents like the King commanding cousins | EPIC | 80 | 👑 |
| `size_matters` | We Love Katamari - Size Matters | Grew from small task to handling 100+ operations | RARE | 50 | 📏 |
| `sticky_situation` | Sticky Situation | Recovered from 3 failures and succeeded (things stick to the katamari) | UNCOMMON | 30 | 🍯 |
| `cousin_collaboration` | Cousin Collaboration | Multiple agents working together successfully | UNCOMMON | 35 | 👥 |
| `time_attack` | Katamari Time Attack | Completed task under extreme time pressure (<30 seconds) | RARE | 55 | ⏰ |
| `everything_collector` | I Rolled Up Everything | Completed 50 total tasks - you've rolled up the whole universe! | LEGENDARY | 150 | 🌍 |
| `prince_upgrade` | Prince of All Cosmos | Achieved 95%+ success rate across 20+ tasks | LEGENDARY | 200 | 🤴 |

### Achievement Implementation Pattern

```python
# Example achievement definition pattern
Achievement(
    id="katamari_start",
    name="We Love Katamari",
    description="Completed your first task - starting to roll!",
    category=AchievementCategory.KATAMARI,
    rarity=AchievementRarity.COMMON,
    icon="🌟",
    points=10,
    agent_classes=["*"],
    trigger_condition={"event": "first_execution"}
)
```

## Technical Constraints

1. **Existing Patterns**: Must follow existing achievement definition pattern in achievements.py
2. **Category Enum**: Add to existing `AchievementCategory` enum
3. **Frontend Consistency**: Match existing category badge/filter patterns
4. **Trigger Conditions**: Use existing trigger condition types where possible

## Success Criteria

1. ✅ `KATAMARI` category added to `AchievementCategory` enum
2. ✅ Exactly 10 Katamari achievements added to `ACHIEVEMENTS` list
3. ✅ Frontend filter dropdown includes katamari with appropriate icon
4. ✅ `getCategoryBadge` function handles katamari category
5. ✅ All existing tests continue to pass
6. ✅ Achievements unlock correctly when conditions are met

## Implementation Notes

### Files to Modify
- **Backend**: `src/runtime/agents/achievements.py`
- **Frontend**: `src/field/ensemble_ui/frontend/src/components/AchievementsDashboard.jsx`

### Icon Choice
Using 🌟 as primary katamari icon since actual katamari ball isn't available in standard emoji sets.

### Testing
- Run existing achievement tests to ensure no regressions
- Manually verify katamari filter works in UI
- Verify at least one achievement can be triggered

## Assumptions Made

1. **Icon Choice**: Using 🌟, 👑, 🌈, 🌌 and other playful emojis to capture Katamari's whimsical aesthetic
2. **Trigger Conditions**: Reusing existing trigger types (first_execution, consecutive_successes, etc.)
3. **Points Balance**: Following existing points range (10-200) based on rarity
4. **Theme Interpretation**: Focusing on universal Katamari themes (rolling, collecting, growing) rather than obscure game references

## Fun Facts for UI (Optional Enhancement)

Consider adding to the fun facts section:
> **Did you know?** Katamari Damacy was created by Keita Takahashi in 2004 as an anti-game that rejected traditional video game violence. Players roll a magical adhesive ball called a "katamari" to pick up objects, starting with thumbtacks and paperclips and eventually collecting buildings, islands, and even stars! The King of All Cosmos destroyed all the stars (accidentally, of course) and tasks the Prince with rolling up replacements. The game's absurd humor and unique physics made it a cult classic that spawned multiple sequels. Na na na na na na na na Katamari Damacy! 🌟

---

**Status:** Requirements Complete - Ready for Implementation  
**Next Step:** Delegate to Development Manager for implementation