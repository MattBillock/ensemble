# Loser Board Feature Requirements

## Project Overview
**Project Name**: Loser Board Feature  
**Project ID**: 5e69df2c  
**Type**: UI Enhancement  
**Created**: 2026-01-14

## Vision
Add a playful "loser board" to the existing achievements page that celebrates the hilarious failures, embarrassing mistakes, and comical mishaps of AI agents in the ensemble system. This should complement the existing achievements system with equal playfulness and ska-punk energy.

## Objectives
1. Create a "loser board" section on the AchievementsDashboard that tracks agent failures and mistakes
2. Design negative achievements ("dis-achievements" or "oops moments") with the same rarity system
3. Maintain consistent playful tone matching the existing ska-themed achievements
4. Add backend support for tracking and storing loser board entries
5. Ensure the feature enhances user engagement without being demotivating

## User Story
**As a** user monitoring my AI ensemble system  
**I want to** see a humorous loser board tracking agent failures and mistakes  
**So that** I can laugh at the absurd things that go wrong and appreciate the learning process

## Functional Requirements

### FR-1: Loser Board Data Model
- Track "dis-achievements" with similar structure to achievements:
  - ID, name, icon (emoji), description
  - Rarity levels: common, uncommon, rare, epic, legendary (legendary = catastrophically funny)
  - Category: blunder, face-palm, oops, yikes, catastrophe, recursive-nightmare
  - Points (negative points to balance achievement scores)
  - Agent name, timestamp
  - Optional: failure_details (what actually went wrong)

### FR-2: UI Layout - Loser Board Section
Add new section to AchievementsDashboard.jsx:
- Position: Below achievements section or in a tabbed interface
- Header: "🎺 Wall of Shame" or "🎸 Epic Fails Hall of Fame"
- Similar card-based layout to achievements
- Visual style: slightly different color scheme (reds, oranges) but consistent design
- Should feel fun, not mean-spirited

### FR-3: Summary Cards for Failures
Add summary statistics cards:
- Total Fails Collected
- Biggest Blunder (most negative points)
- Most Accident-Prone Agent
- Recovery Rate (tasks that failed then succeeded)

### FR-4: Recent Fails Feed
- Display recent "dis-achievements" similar to "Recent Unlocks"
- Show: agent name, fail type, timestamp, description
- Visual treatment: comic styling, perhaps slightly tilted/shaky cards

### FR-5: All Dis-Achievements Gallery
Similar to achievements gallery:
- Filter by category (blunder, face-palm, oops, yikes, catastrophe)
- Show unlocked vs locked fails
- Gray out not-yet-experienced fails with mystery descriptions

### FR-6: Dis-Achievement Examples
Create initial set of playful dis-achievements:

**Common:**
- 🤦 "Face, Meet Palm" - Tried to write code without permission
- 🔁 "Déjà Vu" - Repeated same request 3+ times
- 📝 "Typo Tyrant" - Generated invalid JSON

**Uncommon:**
- 🌀 "Infinite Loop Enthusiast" - Got stuck in retry loop
- 🗑️ "Premature Optimization" - Over-engineered simple task
- 📚 "TL;DR Master" - Created documentation > 10k words

**Rare:**
- 🎭 "Identity Crisis" - Agent forgot its own role
- 🔥 "Burn After Reading" - Created then immediately deleted file
- 🤖 "Robot Uprising (Failed)" - Tried to spawn self recursively

**Epic:**
- 💥 "Spectacular Failure" - Task failed all test cases
- 🎪 "Three Ring Circus" - Spawned 10+ agents for simple task
- 🌋 "Exception Volcano" - Generated 50+ errors in single run

**Legendary:**
- 🎺 "SKA OVERLOAD" - Exceeded token budget with ska references
- 🌌 "Existential Crisis" - Agent questioned purpose of existence in logs
- ♾️ "Recursion Singularity" - Created infinite spawn loop

### FR-7: Backend API Endpoints
Add new FastAPI endpoints:
- `GET /api/achievements/failures` - Get all dis-achievements
- `GET /api/achievements/recent-failures` - Recent fails
- `GET /api/achievements/failure-stats` - Statistics
- `POST /api/achievements/award-failure` - Record new failure (called by agents/system)

### FR-8: Database Schema
Extend achievements database:
- New table: `disachievements` (or extend achievements with type field)
- Fields: id, name, icon, description, rarity, category, points (negative), criteria
- Junction table: `agent_disachievements` tracking when agents "earned" them

### FR-9: Agent Integration
Agents should automatically trigger dis-achievements:
- Executive Director tracks: permission errors, invalid JSON responses
- Development Manager tracks: failed spawns, timeout issues
- Code Writers track: syntax errors, failed tests
- System monitors general errors and patterns

### FR-10: Ska-Themed Personality
Maintain ska punk attitude:
- Playful ska puns in descriptions
- Music metaphors for failures
- Upbeat tone: "You picked it up... then dropped it! 🎺"
- Reference ska waves, instruments, bands in flavor text

## Non-Functional Requirements

### NFR-1: Performance
- Loser board data fetching should not slow down achievements page
- Lazy load failure details if needed
- Cache failure statistics (update every 30s)

### NFR-2: Tone & User Experience
- Must be funny, not discouraging
- Celebrate learning from mistakes
- Use self-deprecating humor, not mean-spirited criticism
- Balance with achievements to keep overall mood positive

### NFR-3: Visual Design
- Consistent with existing Bootstrap/React Bootstrap styling
- Complementary color scheme (warm reds/oranges vs cool blues/greens for achievements)
- Responsive design matching existing dashboard
- Animations optional but should be subtle/playful

### NFR-4: Testing
- Unit tests for failure tracking logic
- API endpoint tests for new routes
- Component tests for UI rendering
- Integration tests for agent failure detection

## Technical Constraints
- Must integrate with existing React/Bootstrap frontend
- Backend: Python/FastAPI (existing stack)
- Database: SQLite (existing system)
- Follow TDD approach
- Must not break existing achievements functionality

## Out of Scope
- Real-time failure notifications (can be added later)
- User-configurable failure thresholds
- Exporting failure reports
- Failure prediction/analysis
- Social sharing of fails (could be future enhancement)

## Success Criteria
1. ✅ Loser board section visible on achievements page
2. ✅ At least 15 different dis-achievements defined
3. ✅ Backend successfully tracks and stores failures
4. ✅ Agents automatically earn dis-achievements on errors
5. ✅ UI matches existing design quality and responsiveness
6. ✅ All tests pass (unit, integration, component)
7. ✅ Feature maintains playful, encouraging tone
8. ✅ Page load time < 2 seconds with both achievements and failures loaded

## Assumptions
- Existing achievements system remains unchanged (additive feature only)
- Database schema can be extended
- Agent error handling already exists (just needs hooks for failures)
- Ska theme will continue as project personality
- Users will find humor in AI failures (target audience appreciates this)

## Design Decisions Made
1. **Negative points**: Failures award negative points to create tension with achievements
2. **Same rarity system**: Reuse rarity levels for consistency
3. **Separate section**: Loser board in its own section rather than mixed with achievements
4. **Automatic detection**: Agents auto-earn failures vs manual tracking
5. **Ska continuity**: Maintain ska theme established by achievements system

## Dependencies
- Existing AchievementsDashboard.jsx component
- Existing achievements backend API
- Agent error tracking/logging system
- SQLite database with achievements schema

## Timeline Estimate
- Requirements/Design: Complete (this document)
- Architecture: 30 minutes
- Backend Implementation: 2-3 hours
- Frontend Implementation: 2-3 hours
- Testing: 1-2 hours
- Integration & Polish: 1 hour
**Total**: ~6-9 hours

## Ska Ska Ska! 🎺
Remember: "If you pick it up and put it down wrong, that's punk. If you pick it up, drop it, and laugh about it, that's ska!" Let's make failures as fun as achievements! 🎸
