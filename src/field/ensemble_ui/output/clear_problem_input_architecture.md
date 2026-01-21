# Clear Problem Input Box - Architecture Design

## Overview
This document outlines the architecture and design for adding a clear/reset button to the ProblemInputForm component.

## Current Component Analysis

### Existing Structure
- **Location**: `src/field/ensemble_ui/frontend/src/components/ProblemInputForm.jsx`
- **State Management**: Uses React useState for `problemDescription` and `budgetTier`
- **Layout**: Horizontal flex layout with textarea, select, and submit button
- **Styling**: Tailwind CSS utility classes
- **Props**: Receives `onProblemSubmit` callback

### Current State Flow
1. User types in textarea → `setProblemDescription` updates state
2. User selects budget → `setBudgetTier` updates state
3. User clicks submit → `onProblemSubmit` called with both values

## Proposed Changes

### 1. Component Structure
**Add clear button** between budget select and submit button with:
- Icon or text label ("Clear" or "×")
- Outline or secondary styling (less prominent than submit)
- Disabled state when form is empty

### 2. State Management
**New handler function**: `handleClear`
```javascript
const handleClear = () => {
  setProblemDescription('');
  setBudgetTier('balanced');
};
```

**New computed value**: `isFormEmpty`
```javascript
const isFormEmpty = !problemDescription.trim();
```

### 3. UI/UX Design

#### Button Placement
Position clear button between select and submit:
```
[Textarea] [Budget Select] [Clear Button] [Submit Button]
```

#### Visual Hierarchy
- **Submit button**: Primary gradient (blue-to-cyan), bold
- **Clear button**: Secondary/outline style, less prominent
- **Disabled states**: Reduced opacity for both buttons

#### Styling Specification
```javascript
className="px-4 py-2 bg-white/10 border border-white/30 text-white rounded-lg 
           hover:bg-white/20 transition-all disabled:opacity-30 
           disabled:cursor-not-allowed"
```

### 4. Accessibility

#### Keyboard Navigation
- Tab order: textarea → select → clear → submit
- Enter key in textarea still submits form
- Clear button uses type="button" to prevent form submission

#### Screen Reader Support
```javascript
aria-label="Clear form"
title="Clear problem description and reset budget"
```

#### Visual Feedback
- Hover state for enabled button
- Cursor changes (pointer/not-allowed)
- Focus ring on keyboard navigation

### 5. Responsive Design

#### Desktop (≥768px)
- Horizontal layout as described
- Clear button: ~80px width

#### Mobile (<768px)
- Stack elements vertically if needed
- Full-width buttons
- Maintain button order

### 6. Testing Strategy

#### Unit Tests (ProblemInputForm.test.jsx)
1. **Render test**: Clear button renders correctly
2. **Disabled state**: Button disabled when form empty
3. **Enabled state**: Button enabled with text input
4. **Click behavior**: Clears textarea and resets budget
5. **Integration**: Doesn't interfere with submit
6. **Accessibility**: aria-label present, keyboard accessible

#### Test Cases
```javascript
describe('Clear functionality', () => {
  test('clear button is disabled when form is empty');
  test('clear button is enabled when form has content');
  test('clicking clear empties textarea');
  test('clicking clear resets budget to balanced');
  test('clear button has proper aria-label');
  test('submit still works after clear');
});
```

### 7. Implementation Phases

#### Phase 1: Core Functionality (Milestone 1)
- Add handleClear function
- Add isFormEmpty computed value
- Add clear button to JSX
- Basic styling

#### Phase 2: Polish & Accessibility (Milestone 2)
- Refine styling for visual hierarchy
- Add aria-labels and titles
- Ensure keyboard navigation
- Responsive design adjustments

#### Phase 3: Testing (Milestone 3)
- Write unit tests
- Manual testing across browsers
- Accessibility audit
- Integration testing

## Component API (No Changes)
The component maintains the same external API:
```javascript
<ProblemInputForm onProblemSubmit={handler} />
```

## Dependencies
- No new dependencies required
- Uses existing React hooks
- Uses existing Tailwind CSS

## Risk Assessment
- **Low Risk**: Minimal changes to existing code
- **No Breaking Changes**: Existing functionality untouched
- **Backwards Compatible**: Component API unchanged

## Success Metrics
- Clear button reduces user friction when correcting input
- No regression in existing submit functionality
- All accessibility checks pass
- 100% test coverage for new functionality

## Next Steps
1. Implement core functionality (handleClear, isFormEmpty, button)
2. Add styling and accessibility features
3. Write comprehensive unit tests
4. Manual QA and browser testing
5. Code review and merge
