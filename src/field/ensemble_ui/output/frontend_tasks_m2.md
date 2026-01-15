# Frontend Tasks - UI Integration for Katamari Category Support

## Overview
Update the AchievementsDashboard component to support the new katamari (famous_mustards) achievement category with proper filtering and display styling.

## Context Analysis
- **Architecture**: Data-driven configuration with enumerated categories
- **Current State**: Dashboard supports 9 existing achievement categories (ska, brass_band, drum_corps, guitar_hero, productivity, comedy, milestone, streak, meta)
- **New Addition**: famous_mustards category needs frontend integration
- **Framework**: React with Bootstrap styling
- **Pattern**: Extend existing category filtering without breaking current functionality

## Task Breakdown

### Task 1: Update Category Dropdown Options
**Description**: Add famous_mustards category option to the filtering dropdown in AchievementsDashboard
**Type**: Component Enhancement
**Complexity**: Simple
**Files**: `/frontend/src/components/AchievementsDashboard.jsx`

**Acceptance Criteria**:
- Famous mustards option appears in category filter dropdown
- Option includes appropriate mustard-themed icon (🌭 or 🟡)  
- Dropdown maintains alphabetical or logical ordering
- Existing category options remain unchanged

**Implementation Details**:
- Add new `<option>` element in Form.Select for category filtering
- Use consistent icon pattern: `🌭 Famous Mustards` or `🟡 Famous Mustards`
- Place in logical position within dropdown (after existing categories or alphabetically)

**Dependencies**: None

---

### Task 2: Update Category Badge Display Function
**Description**: Extend getCategoryBadge function to handle famous_mustards category
**Type**: Function Enhancement  
**Complexity**: Simple
**Files**: `/frontend/src/components/AchievementsDashboard.jsx`

**Acceptance Criteria**:
- getCategoryBadge function returns appropriate badge for famous_mustards
- Badge uses mustard-themed icon (🌭, 🟡, or appropriate mustard emoji)
- Badge styling matches existing category badges
- Function maintains existing behavior for all current categories

**Implementation Details**:
- Add `famous_mustards: '🌭'` to icons object within getCategoryBadge
- Add `famous_mustards: 'Famous Mustards'` to displayNames object
- Consider alternative icons: 🟡 (yellow circle), 🌮 (taco), or other mustard-appropriate emoji

**Dependencies**: None

---

### Task 3: Update Filter Logic for New Category
**Description**: Ensure filtering logic properly handles famous_mustards category selection
**Type**: Logic Enhancement
**Complexity**: Simple
**Files**: `/frontend/src/components/AchievementsDashboard.jsx`

**Acceptance Criteria**:
- Selecting "Famous Mustards" from dropdown filters to show only famous_mustards achievements
- Filter logic works correctly when no famous_mustards achievements exist yet
- "All Categories" option continues to include famous_mustards achievements
- Filter state management handles new category properly

**Implementation Details**:
- Current filter logic in `filteredAchievements` should automatically handle new category
- Verify filter comparison: `filter !== 'all' && a.category !== filter` works with famous_mustards
- Test empty state handling when category exists but no achievements are unlocked

**Dependencies**: Backend must have famous_mustards category achievements available

---

### Task 4: Add Category Statistics Support
**Description**: Update category statistics display to include famous_mustards counts
**Type**: Data Display Enhancement
**Complexity**: Simple
**Files**: `/frontend/src/components/AchievementsDashboard.jsx`

**Acceptance Criteria**:
- Famous mustards category appears in "By Category" statistics card
- Progress bar renders correctly for famous_mustards count
- Statistics accurately reflect famous_mustards achievements when available
- Empty state handled gracefully when no famous_mustards achievements awarded yet

**Implementation Details**:
- Current stats.by_category mapping should automatically include famous_mustards
- getCategoryBadge call in stats iteration will use Task 2 implementation  
- Progress bar calculation handles division by zero gracefully
- Consider adding conditional rendering if category has zero achievements

**Dependencies**: Backend API must return famous_mustards in achievement statistics

---

### Task 5: Visual Styling Enhancements
**Description**: Ensure famous_mustards category has appropriate visual theming
**Type**: Styling Enhancement
**Complexity**: Medium
**Files**: `/frontend/src/components/AchievementsDashboard.jsx`

**Acceptance Criteria**:
- Famous mustards achievements display with consistent styling
- Category badge uses appropriate color scheme (yellow/mustard tones)
- Achievement cards maintain visual hierarchy and readability
- Hover states and interactive elements work properly for new category

**Implementation Details**:
- Consider adding custom color for famous_mustards in getRarityColor function (if category-specific colors desired)
- Ensure badge background color provides good contrast with mustard icon
- Test achievement card display with mustard-themed descriptions and icons
- Verify responsive behavior with longer category name

**Dependencies**: Tasks 1-4 completed

---

### Task 6: Add Loading State Handling
**Description**: Ensure proper loading states when famous_mustards achievements are being fetched
**Type**: Error Handling Enhancement
**Complexity**: Simple  
**Files**: `/frontend/src/components/AchievementsDashboard.jsx`

**Acceptance Criteria**:
- Loading spinner shows appropriately when fetching achievements
- Empty state messaging handles missing famous_mustards gracefully
- Error states don't break when famous_mustards category is involved
- Toast notifications work for new famous_mustards achievements

**Implementation Details**:
- Current loading logic should handle new category transparently
- Verify toast notifications work with famous_mustards achievement unlocks
- Test error boundary behavior with famous_mustards data
- Ensure empty results don't cause UI breaks

**Dependencies**: None (enhances existing error handling)

---

### Task 7: Update Achievement Grid Layout
**Description**: Optimize grid layout to handle additional category without breaking responsive design
**Type**: Layout Enhancement
**Complexity**: Simple
**Files**: `/frontend/src/components/AchievementsDashboard.jsx`

**Acceptance Criteria**:
- Achievement grid displays famous_mustards achievements properly on all screen sizes
- Card spacing and alignment maintained with new category
- Filter controls remain accessible and functional
- No horizontal scrolling introduced

**Implementation Details**:
- Current Bootstrap grid (Col md={4}) should handle new achievements automatically
- Test responsive behavior with larger number of total achievements
- Verify dropdown doesn't overflow with additional option
- Check mobile layout with longer "Famous Mustards" text

**Dependencies**: None

---

### Task 8: Add Contextual Help/Description
**Description**: Add contextual information about the famous_mustards achievement category
**Type**: UX Enhancement  
**Complexity**: Simple
**Files**: `/frontend/src/components/AchievementsDashboard.jsx`

**Acceptance Criteria**:
- User can understand what famous_mustards category represents
- Help text or tooltip explains mustard-themed achievement concept
- Information is discoverable but not intrusive
- Maintains consistency with existing help patterns

**Implementation Details**:
- Consider adding famous_mustards entry to rotating facts section
- Add tooltip to category badge explaining theme
- Include mustard facts in SKA_FACTS array with mustard trivia
- Use existing Toast pattern for contextual information

**Dependencies**: None

---

## Component Architecture

### Modified Functions
1. **getCategoryBadge()** - Add famous_mustards case
2. **filteredAchievements logic** - Handle new category filtering  
3. **Category dropdown JSX** - Add new option

### New/Updated State
- No new state required (existing filter state handles new category)
- Existing `filter` state supports famous_mustards value

### Data Flow
1. User selects "Famous Mustards" from dropdown
2. `setFilter('famous_mustards')` updates state  
3. `filteredAchievements` filters to famous_mustards category
4. Achievement cards re-render with filtered results
5. Statistics update to show famous_mustards counts

### Error Handling
- Empty state when no famous_mustards achievements exist
- Graceful degradation if category not returned by API
- Loading states during achievement fetch operations

## Testing Considerations

### Manual Testing
- [ ] Category dropdown includes famous_mustards option
- [ ] Filtering works correctly for famous_mustards
- [ ] Category badge displays with appropriate icon/styling
- [ ] Statistics include famous_mustards counts
- [ ] Achievement cards render properly for new category
- [ ] Responsive design maintained across screen sizes
- [ ] Empty states handled gracefully

### Integration Points
- Backend API must return famous_mustards achievements
- Achievement data structure must include category field
- Statistics endpoint must aggregate famous_mustards

### Rollback Plan
- Changes are purely additive to frontend code
- Can safely deploy even before backend has famous_mustards achievements
- Graceful degradation ensures no breaking changes

## Dependencies Summary
- **Backend Ready**: famous_mustards category exists in achievement system
- **API Support**: Achievement endpoints return famous_mustards data  
- **Data Structure**: Achievements include famous_mustards as category value

## Estimated Effort
- **Simple Tasks (1-4, 6-8)**: 30 minutes each = 3.5 hours
- **Medium Task (5)**: 1 hour  
- **Total**: ~4.5 hours of development time

## Implementation Order
1. Tasks 1-2 (Core functionality)
2. Task 3 (Filter logic)  
3. Tasks 4-5 (Display enhancements)
4. Tasks 6-8 (Polish and error handling)

This approach ensures core functionality works first, then adds enhancements progressively.