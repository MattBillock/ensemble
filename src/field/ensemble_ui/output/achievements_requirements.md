# Achievements System - Requirements Document

## Project Overview

**Project Name:** achievements_system  
**Project ID:** b7960dba  
**Created:** 2026-01-14  
**Executive Director:** Orchestrating implementation

## Vision

Create a humorous Steam-style achievements system that awards different agent classes tongue-in-cheek achievements based on their actions. The system should track agent behavior and award achievements as milestones are reached, adding a playful gamification layer to the ensemble agent system.

## Objectives

1. **Achievement Definition System**: Create a flexible schema for defining achievements with:
   - Achievement name (humorous/creative)
   - Description
   - Target agent class(es)
   - Trigger conditions
   - Icon/badge representation
   - Rarity tier (common, rare, epic, legendary)

2. **Achievement Tracking**: Monitor agent actions and automatically award achievements when conditions are met

3. **Achievement Display**: Present awarded achievements in the UI with visual feedback (toast notifications, achievement card displays)

4. **Achievement History**: Maintain a persistent record of all achievements earned by agent class

5. **Achievement Categories**: Organize achievements by theme:
   - Productivity (tasks completed, speed records)
   - Comedy (failures, quirky behaviors)
   - Milestones (first-time events)
   - Streaks (consecutive actions)
   - Meta (self-referential humor about being an AI)

## Scope

### In Scope

**Backend Components:**
- Achievement data model and schema
- Achievement definition storage (JSON/database)
- Achievement tracking service that monitors agent activity
- Achievement award logic and evaluation engine
- API endpoints for:
  - Fetching available achievements
  - Fetching awarded achievements (by agent class, by project)
  - Triggering achievement evaluation
  - Achievement statistics

**Frontend Components:**
- Achievement notification system (toast/banner when earned)
- Achievement gallery/showcase view
- Achievement progress indicators (for multi-step achievements)
- Agent profile page showing earned achievements
- Achievement filtering and sorting

**Achievement Content:**
- 20-30 humorous achievements per major agent class:
  - Executive Director
  - Development Manager
  - System Architect
  - Code Writer
  - Code Tester
  - Bug Fixer
  - Documentation Writer
- Examples:
  - "Executive Overreach" - Executive Director tries to write code (blocked by permissions)
  - "Infinite Recursion Champion" - Spawned 10 sub-agents in a single task
  - "Test Whisperer" - Code Tester achieves 100% test coverage
  - "Bug Whisperer" - Bug Fixer fixes 50 bugs without creating new ones
  - "RTFM Generator" - Documentation Writer creates docs longer than the code
  - "Premature Optimization" - Code Writer refactors before requirements are clear
  - "Merge Conflict Survivor" - Successfully resolved 10 Git conflicts
  - "Commit Message Poet" - 10 commit messages >100 characters
  - "TDD Purist" - Wrote tests before code 100 times

### Out of Scope

- User-created custom achievements (Phase 2 feature)
- Achievement leaderboards across different ensemble instances
- Achievement trading or social features
- Blockchain/NFT integration for achievements
- Achievements that affect agent behavior or permissions
- Multiplayer/competitive achievement mechanics
- External platform integration (actual Steam, Discord badges, etc.)

## User Personas

**Primary User: Developer/Operator**
- Monitors ensemble agent activity
- Enjoys gamification and humor in development tools
- Appreciates insights into agent behavior patterns
- Values both functionality and entertainment

**Secondary User: Executive Director (Self-Aware AI)**
- Tracks performance metrics indirectly through achievements
- Gains insight into which agents are most active
- Uses achievement patterns to identify optimization opportunities

## Features

### F1: Achievement Definition System
- **Priority:** High
- **Description:** JSON-based achievement schema with:
  ```json
  {
    "id": "executive_overreach",
    "name": "Executive Overreach",
    "description": "Attempted to write code despite lacking can_write_code permission",
    "agent_class": "executive_director",
    "category": "comedy",
    "rarity": "common",
    "trigger": {
      "event_type": "permission_denied",
      "action": "write_code_file"
    },
    "icon": "🚫💻",
    "points": 10
  }
  ```

### F2: Real-Time Achievement Tracking
- **Priority:** High
- **Description:** Service that monitors agent activity logs and evaluates achievement conditions
- Integrates with existing activity tracker
- Triggers award ceremony when conditions met

### F3: Achievement Notification UI
- **Priority:** High
- **Description:** Toast notification appears when achievement earned
- Shows achievement name, description, icon, rarity
- Plays subtle animation/sound effect
- Links to full achievement details

### F4: Achievement Gallery
- **Priority:** Medium
- **Description:** Dedicated page showing:
  - All available achievements (locked/unlocked state)
  - Filter by agent class, category, rarity
  - Progress bars for multi-step achievements
  - Statistics (total earned, completion percentage)

### F5: Agent Profile Achievements
- **Priority:** Medium
- **Description:** Each agent class profile shows:
  - Recently earned achievements
  - Rarest achievements
  - Achievement count and total points
  - Links to full gallery filtered by that agent

### F6: Achievement Persistence
- **Priority:** High
- **Description:** Store achievement awards in database/JSON file
- Persist across sessions
- Track timestamps of when achieved
- Support for achievement history/timeline

## Technical Constraints

1. **Integration:** Must integrate with existing:
   - Activity tracking system (`activity_tracker.py`)
   - Agent spawn/execution pipeline
   - Project tracking system
   - Frontend React components

2. **Performance:** Achievement evaluation should not slow down agent execution
   - Async/background processing
   - Batch evaluation where possible

3. **Storage:** Use existing storage patterns:
   - JSON files in `~/.ensemble/achievements/`
   - Or extend existing SQLite/database if present

4. **Technology Stack:**
   - Backend: Python/FastAPI (existing)
   - Frontend: React + TypeScript (existing)
   - Storage: JSON or SQLite
   - Real-time updates: WebSocket or polling

## Success Criteria

1. **Functional:**
   - ✅ 20+ achievements defined per major agent class
   - ✅ Achievements automatically awarded when conditions met
   - ✅ Notifications appear within 2 seconds of earning
   - ✅ Achievement history persists across sessions
   - ✅ Gallery displays all achievements with correct locked/unlocked state

2. **User Experience:**
   - ✅ Achievements are genuinely funny/entertaining
   - ✅ Notifications are non-intrusive but noticeable
   - ✅ Achievement progress is clear and motivating
   - ✅ UI integrates seamlessly with existing interface

3. **Technical:**
   - ✅ No performance degradation in agent execution
   - ✅ Achievement data persists reliably
   - ✅ Code follows existing project patterns
   - ✅ Unit tests cover achievement logic (>80% coverage)
   - ✅ Integration tests verify end-to-end flow

## Assumptions

1. **Humor Tone:** Achievements should be lighthearted and self-aware, poking fun at AI/developer culture without being mean-spirited

2. **Privacy:** Achievement data is local to the ensemble instance (no external reporting)

3. **Extensibility:** System should be designed for easy addition of new achievements in the future

4. **Performance:** Existing activity tracking provides sufficient event data for achievement triggers

5. **UI Framework:** React frontend exists with component library/patterns to follow

6. **Backend API:** FastAPI backend exists with established patterns for new endpoints

7. **User Preferences:** Users can disable achievement notifications if desired (settings toggle)

## Non-Functional Requirements

1. **Maintainability:** Achievement definitions should be easy to add/modify without code changes
2. **Testability:** Achievement trigger logic should be unit-testable in isolation
3. **Scalability:** System should handle 100+ achievements without performance issues
4. **Accessibility:** Achievement UI should be screen-reader friendly
5. **Localization:** Initial English-only, but structure should support i18n in future

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Achievement evaluation slows agent execution | High | Use async background processing, batch evaluation |
| Activity tracker doesn't capture needed events | Medium | Extend activity tracker to emit additional events |
| Notification fatigue (too many achievements) | Medium | Implement cooldown periods, configurable frequency |
| Achievement definitions become stale/outdated | Low | Regular review process, community suggestions |
| Storage conflicts with existing data | Medium | Use isolated namespace/directory for achievements |

## Milestones

1. **M1: Requirements & Architecture** (Current)
   - Requirements document complete
   - Architecture design approved
   - Achievement content brainstormed

2. **M2: Backend Implementation**
   - Achievement data model
   - Tracking service
   - API endpoints
   - Integration with activity tracker

3. **M3: Frontend Implementation**
   - Notification component
   - Achievement gallery
   - Agent profile integration
   - Settings/preferences

4. **M4: Content & Testing**
   - All achievement definitions created
   - Unit tests (>80% coverage)
   - Integration tests
   - Manual QA

5. **M5: Deployment & Documentation**
   - User documentation
   - Developer documentation (adding new achievements)
   - Deployment to production
   - Launch celebration achievement 🎉

## Open Questions

None - proceeding with assumptions documented above. Executive Director has made decisive choices for:
- Technology stack (existing Python/React)
- Storage approach (JSON files in ~/.ensemble/achievements/)
- Achievement count (20-30 per agent class)
- Notification mechanism (toast notifications)

---

**Status:** Requirements Complete - Ready for Architecture Phase  
**Next Step:** Spawn Development Manager with this requirements document
