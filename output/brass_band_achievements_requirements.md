# British Brass Band Achievements - Requirements Document

## Project Overview

**Project Name:** British Brass Band Achievements Expansion  
**Project ID:** 29b97d5e  
**Created:** 2026-01-14  
**Executive Director:** Orchestrating implementation

## Vision

Expand the existing Ensemble achievements system with a new "British Brass Band" category inspired by NABBA (North American Brass Band Association) and the British brass band tradition. These achievements celebrate the rich heritage of brass banding including competitions, sections, traditional instrumentation, and contest culture.

## Background: NABBA & British Brass Bands

NABBA (North American Brass Band Association) promotes British-style brass bands in North America since 1983. Key characteristics:
- **Contest Culture**: Championships with adjudicators scoring bands on test pieces
- **Section System**: Bands compete in divisions based on ability (Championship, Honor, Challenge, etc.)
- **Traditional Instrumentation**: Cornets, flugelhorn, tenor horns, baritones, euphoniums, trombones, tubas, percussion
- **Silver Band Tradition**: Many bands carry "Silver Band" in their name
- **Community Focus**: Youth bands, community bands, university bands

## Objectives

1. **Add New Category**: Create `BRASS_BAND` achievement category (parallel to existing `SKA` category)
2. **Achievement Content**: Add 10-15 British brass band themed achievements
3. **UI Updates**: Add brass band category to filter dropdown in AchievementsDashboard
4. **Maintain Consistency**: Follow existing achievement patterns for rarity, triggers, and points

## Scope

### In Scope

**Backend Changes** (`src/runtime/agents/achievements.py`):
- Add `BRASS_BAND = "brass_band"` to `AchievementCategory` enum
- Add 10-15 new `Achievement` objects to the `ACHIEVEMENTS` list
- Include variety of rarities (common through legendary)

**Frontend Changes** (`src/field/ensemble_ui/frontend/src/components/AchievementsDashboard.jsx`):
- Add brass_band category to filter dropdown with icon (🎺)
- Add brass_band to `getCategoryBadge` function
- Update "Brass/Band Facts" section or add separate fun facts

### Out of Scope
- New API endpoints (using existing endpoints)
- Database schema changes (existing schema supports new category)
- New UI components beyond filter updates

## Achievement Definitions

### Theme Guidelines
British brass band achievements should reference:
- Contest/competition terminology (adjudicator, test piece, draw, sections)
- Instrumentation (cornets, euphoniums, tubas, percussion)
- Band traditions (Silver Bands, marching, community, youth development)
- Famous brass band pieces and composers
- Section rankings and promotions
- NABBA-specific events and culture

### Proposed Achievements (10-15)

| ID | Name | Description | Rarity | Points | Icon |
|----|------|-------------|--------|--------|------|
| `championship_section` | Championship Section | Achieved legendary status with 50+ successful tasks | LEGENDARY | 200 | 🏆 |
| `silver_band` | Silver Band | First agent to maintain 100% success rate across 5 tasks | RARE | 50 | 🥈 |
| `principal_cornet` | Principal Cornet | Led 3+ sub-agents to successful completion in one task | UNCOMMON | 30 | 🎺 |
| `adjudicator` | The Adjudicator | Evaluated and passed judgment on 25+ test results | RARE | 60 | 📋 |
| `test_piece` | Test Piece Mastery | Completed a particularly challenging task (>10 iterations) | UNCOMMON | 25 | 📜 |
| `bandroom_practice` | Bandroom Practice | Executed 10 tasks total (like rehearsal makes perfect) | COMMON | 15 | 🎵 |
| `promotion` | Section Promotion | Improved success rate from <50% to >90% | EPIC | 100 | ⬆️ |
| `brass_section_harmony` | Brass Section Harmony | Multiple agents completed tasks simultaneously | RARE | 45 | 🎶 |
| `march_on_stage` | March on Stage | Completed first task of a new project | COMMON | 10 | 🚶 |
| `quick_march` | Quick March | Completed a task in under 10 seconds | RARE | 40 | ⚡ |
| `hymn_tune_encore` | Hymn Tune Encore | Recovered from failure and succeeded (like a well-loved encore) | UNCOMMON | 35 | 🙏 |
| `grand_shield` | Grand Shield | Completed 25 consecutive successful tasks | EPIC | 120 | 🛡️ |
| `fanfare` | Fanfare | Triggered 5+ achievements in a single session | RARE | 55 | 📯 |
| `youth_band_graduate` | Youth Band Graduate | New agent class completed its first 10 tasks | UNCOMMON | 20 | 🎓 |
| `national_finals` | National Finals | Participated in project completion (full lifecycle) | LEGENDARY | 150 | 🏅 |

### Achievement Implementation Details

```python
# Example achievement definition pattern (for Development Manager reference)
Achievement(
    id="silver_band",
    name="Silver Band",
    description="Maintained 100% success rate across 5 consecutive tasks - polished performance!",
    category=AchievementCategory.BRASS_BAND,
    rarity=AchievementRarity.RARE,
    icon="🥈",
    points=50,
    agent_classes=["*"],
    trigger_condition={"consecutive_successes": {"min": 5}}
)
```

## Technical Constraints

1. **Existing Patterns**: Must follow existing achievement definition pattern
2. **Category Enum**: Add to existing `AchievementCategory` enum
3. **Frontend Consistency**: Match existing category badge/filter patterns
4. **Trigger Conditions**: Use existing trigger condition types where possible

## Success Criteria

1. ✅ `BRASS_BAND` category added to `AchievementCategory` enum
2. ✅ 10-15 brass band achievements added to `ACHIEVEMENTS` list
3. ✅ Frontend filter dropdown includes brass_band with 🎺 icon
4. ✅ `getCategoryBadge` function handles brass_band category
5. ✅ All existing tests continue to pass
6. ✅ Achievements unlock correctly when conditions are met

## Implementation Notes

### Backend File to Modify
- `src/runtime/agents/achievements.py`

### Frontend File to Modify
- `src/field/ensemble_ui/frontend/src/components/AchievementsDashboard.jsx`

### Testing
- Run existing achievement tests to ensure no regressions
- Manually verify brass_band filter works in UI
- Verify at least one achievement can be triggered

## Assumptions Made

1. **Icon Choice**: Using 🎺 (trumpet) as primary brass band icon since cornet emoji isn't widely available
2. **Trigger Conditions**: Reusing existing trigger types (consecutive_successes, total_executions, etc.)
3. **Points Balance**: Following existing points range (10-200) based on rarity
4. **No New Events**: Not adding new event types to activity tracker

## Fun Facts for UI (Optional Enhancement)

Consider adding to the fun facts section:
> **Did you know?** British-style brass bands date back to the early 1800s and originated in the industrial areas of Northern England. The standard brass band uses 25-30 players on cornets, horns, baritones, euphoniums, trombones, and tubas - no woodwinds allowed! The Black Dyke Band (founded 1855) is one of the oldest and most successful brass bands in the world. NABBA has been bringing this tradition to North America since 1983! 🎺

---

**Status:** Requirements Complete - Ready for Implementation  
**Next Step:** Delegate to Development Manager for implementation
