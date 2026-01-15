# Achievements System - Frontend Enhancement Requirements

## Project Context
The achievements system backend and dashboard are fully implemented. This document specifies the **missing frontend features** from the original requirements that need to be completed.

## Vision
Complete the achievements system user experience by adding toast notifications, header integration, and automatic achievement tracking to create an engaging, motivating gamification system.

## Objectives
1. Add toast notifications for achievement unlocks
2. Integrate achievement counter into header navigation
3. Enable automatic achievement checking during system operation
4. Polish visual feedback and user experience

## Requirements

### 1. Achievement Toast Notifications

**Description**: Display celebratory toast notifications when achievements are unlocked.

**User Story**: As a user, when I unlock an achievement, I want to see an immediate visual celebration so I feel rewarded and engaged.

**Functional Requirements**:
- Create `AchievementToast.jsx` component using React Bootstrap Toast
- Display achievement icon (emoji), name, and description
- Position toast in top-right corner (or configurable position)
- Auto-dismiss after 5 seconds
- Allow manual dismissal (X button)
- Click on toast to navigate to achievements dashboard
- Support multiple toasts stacked vertically
- Show rarity-based border color (common=gray, uncommon=green, rare=blue, epic=purple, legendary=gold)

**Technical Requirements**:
- Use React Bootstrap Toast component
- Integrate with existing toast notification system (if any)
- Store "last checked" timestamp to detect new unlocks
- Poll for new achievements or integrate with WebSocket (if available)
- Add celebration icon (🎉) next to achievement icon
- Use CSS animations for entrance (slide-in from right)

**Acceptance Criteria**:
- [ ] Toast appears within 2 seconds of achievement unlock
- [ ] Toast displays correct achievement icon, name, description
- [ ] Toast auto-dismisses after 5 seconds
- [ ] Clicking toast navigates to achievements dashboard
- [ ] Multiple toasts stack without overlapping
- [ ] Toast styling matches dark theme
- [ ] Border color reflects achievement rarity

### 2. Header Achievement Badge

**Description**: Add achievement counter and navigation to the main header.

**User Story**: As a user, I want to see my achievement progress in the header so I can quickly access the achievements dashboard and track my progress.

**Functional Requirements**:
- Add "🏆 Achievements" link to header navigation (next to Activity, Pipeline, Metrics tabs)
- Display achievement count badge: "X/Y unlocked"
- Highlight badge when new achievements are unlocked (red notification dot or "NEW" text)
- Badge persists until user visits achievements dashboard
- Clicking badge/link navigates to `/achievements` route
- Badge updates in real-time as achievements unlock

**Technical Requirements**:
- Update `App.jsx` to add Achievements tab
- Create achievement count state in App component
- Fetch achievement stats on app load and periodically
- Store "last visited" timestamp in localStorage
- Compare last visited with most recent unlock timestamp
- Use React Bootstrap Badge component
- Add CSS animation for "new achievement" pulsing effect

**Acceptance Criteria**:
- [ ] "🏆 Achievements" tab visible in header navigation
- [ ] Badge shows "X/Y unlocked" format
- [ ] Badge highlights when new achievements exist
- [ ] Clicking navigates to achievements dashboard
- [ ] Badge updates within 5 seconds of achievement unlock
- [ ] "NEW" indicator clears when dashboard is visited
- [ ] Badge styling matches existing header tabs

### 3. Automatic Achievement Checking

**Description**: Integrate achievement checking into the system's activity polling mechanism.

**User Story**: As a user, I don't want to manually trigger achievement checks - they should unlock automatically as I use the system.

**Functional Requirements**:
- Check for new achievements every polling interval (1-5 minutes)
- Trigger achievement check after key events:
  - Task completion
  - Agent spawn
  - File generation
  - System interactions
- Compare current achievement state with previous state
- Detect newly unlocked achievements
- Trigger toast notification for new unlocks
- Update header badge when achievements change

**Technical Requirements**:
- Add achievement polling to existing interval mechanism
- Create achievement state management (useState/useContext)
- Store previous achievement IDs in component state
- Use `getAchievementStats()` API for efficient checking
- Implement delta detection (compare previous vs current unlocked)
- Trigger toast component when new achievements detected
- Update achievement count in header badge

**Acceptance Criteria**:
- [ ] Achievements check automatically every polling interval
- [ ] New unlocks detected within one polling cycle
- [ ] Toast notifications trigger for new achievements
- [ ] Header badge updates when achievements unlock
- [ ] No duplicate toast notifications for same achievement
- [ ] Achievement checking doesn't impact UI performance
- [ ] Works correctly with existing polling system

### 4. Visual Polish & Enhancements

**Description**: Add subtle animations and visual feedback to improve user experience.

**User Story**: As a user, I want the achievements system to feel polished and rewarding with smooth animations and clear visual feedback.

**Functional Requirements**:
- Add entrance animation to achievement cards (fade-in, slide-up)
- Pulse/glow effect for newly unlocked achievements
- Smooth transition from locked to unlocked state
- Hover effects on achievement cards
- Loading states for achievement data fetching
- Empty states with encouraging messaging
- Confetti or particle effect for legendary achievement unlocks (optional)

**Technical Requirements**:
- Use CSS transitions and keyframe animations
- Add "newly-unlocked" CSS class with animation
- Remove animation class after 10 seconds
- Use React Spring or Framer Motion for advanced animations (optional)
- Ensure animations respect user's reduced-motion preferences
- Keep animations subtle and non-intrusive

**Acceptance Criteria**:
- [ ] Achievement cards animate on first load
- [ ] Newly unlocked achievements have visual indicator
- [ ] Hover effects provide clear interaction feedback
- [ ] Loading states prevent layout shift
- [ ] Animations enhance (not distract from) experience
- [ ] Performance remains smooth with 50+ achievements

## Technical Constraints
- Must integrate with existing React Bootstrap UI
- Must use existing FastAPI backend and API endpoints
- Must not disrupt existing polling mechanism
- Should leverage existing toast notification system (if any)
- Must work with dark theme (#1a1d29, #242836, #3a3f52)
- Must be responsive (mobile, tablet, desktop)

## Out of Scope
- Backend achievement logic changes
- New achievement definitions
- Achievement points/scoring modifications
- Leaderboards or social features
- Achievement customization
- Sound effects (can be added later)

## Success Criteria
1. ✅ Toast notifications appear within 2 seconds of achievement unlock
2. ✅ Header badge displays achievement count and "NEW" indicator
3. ✅ Achievements unlock automatically without user intervention
4. ✅ Visual polish animations enhance user experience
5. ✅ No performance degradation to existing UI
6. ✅ All features work consistently across browsers
7. ✅ Dark theme maintained throughout

## File Organization
All files should be created in the appropriate frontend directories:
- Components: `/src/field/ensemble_ui/frontend/src/components/`
- Services: `/src/field/ensemble_ui/frontend/src/services/`
- App updates: `/src/field/ensemble_ui/frontend/src/App.jsx`

## Assumptions
- Achievement backend and API are fully functional
- Polling mechanism already exists for activity tracking
- React Bootstrap is available and configured
- User wants automatic, seamless achievement tracking
- Frontend is React with Bootstrap styling
