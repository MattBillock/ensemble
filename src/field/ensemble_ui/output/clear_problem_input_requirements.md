# Clear Problem Input Box Enhancement

## Project Overview
Add a clear/reset button to the ProblemInputForm component to allow users to easily clear the input fields.

## Requirements

### Functional Requirements
1. Add a clear button to the ProblemInputForm component
2. Button should clear the problem description textarea
3. Button should reset the budget tier to default ('balanced')
4. Button should be disabled when the form is already empty
5. Button should have appropriate visual styling consistent with the existing UI
6. Button should provide visual feedback on hover

### Technical Requirements
1. Maintain existing component structure and props
2. Use React hooks (useState) for state management
3. Follow existing styling patterns (Tailwind CSS)
4. Ensure accessibility (aria-labels, keyboard navigation)
5. Add unit tests for the new functionality

### User Experience Requirements
1. Clear button should be visually distinct but not overshadow the submit button
2. Button should be positioned logically within the form layout
3. Provide visual confirmation when clearing (button state change)
4. Maintain responsive design on different screen sizes

## Acceptance Criteria
- [ ] Clear button is visible in the ProblemInputForm
- [ ] Clicking clear button empties the textarea
- [ ] Clicking clear button resets budget tier to 'balanced'
- [ ] Clear button is disabled when form is empty
- [ ] Button styling is consistent with existing UI
- [ ] All existing tests continue to pass
- [ ] New tests added for clear functionality cover edge cases
- [ ] Component remains accessible (keyboard, screen readers)

## Technical Notes
- Component location: `src/field/ensemble_ui/frontend/src/components/ProblemInputForm.jsx`
- Test location: `src/field/ensemble_ui/frontend/src/components/ProblemInputForm.test.jsx`
- Styling: Tailwind CSS utility classes
- State management: React useState hook
