# Prompt: Clean Up Frontend Components

## Context

Several frontend components were created but are not integrated into the main App. Additionally, some components use inconsistent styling (Tailwind vs Bootstrap).

## Priority
MEDIUM - Dead code and inconsistent UX

## Files to Review

1. `src/field/ensemble_ui/frontend/src/components/AgentStatusPane.jsx`
2. `src/field/ensemble_ui/frontend/src/components/FileViewerPane.jsx`
3. `src/field/ensemble_ui/frontend/src/components/PipelineTreeView.jsx`
4. `src/field/ensemble_ui/frontend/src/components/ProblemInputForm.jsx`
5. `src/field/ensemble_ui/frontend/src/components/ChatInterface.jsx`

## Requirements

### Part 1: Audit Component Usage

First, check which components are actually imported and used:

```bash
# Check imports in App.jsx
grep -E "^import.*from.*components" src/field/ensemble_ui/frontend/src/App.jsx

# Check for any usage of unimported components
grep -r "AgentStatusPane\|FileViewerPane\|PipelineTreeView\|ProblemInputForm\|ChatInterface" src/field/ensemble_ui/frontend/src/
```

### Part 2: Decision - Integrate or Remove

For each unused component, decide:

**Option A: Remove if not needed for V1**
- Delete the file
- Remove any imports

**Option B: Integrate if useful**
- Add import to App.jsx
- Add to appropriate view/tab

### Part 3: Fix Styling Inconsistencies

If keeping components, standardize on React Bootstrap:

**PipelineTreeView.jsx - Lines 81, 86:**
```javascript
// Current (broken Tailwind):
className={`ml-${depth * 6}`}

// Fixed (inline style):
style={{ marginLeft: `${depth * 1.5}rem` }}
```

**AgentStatusPane.jsx:**
- This component uses Tailwind exclusively
- Either convert to Bootstrap OR document as exception

### Part 4: Recommended Actions

Based on analysis:

**AgentStatusPane.jsx:**
- CHECK: Is this used anywhere?
- If NOT used: Consider removing OR integrating into Activity view
- If KEEPING: Convert Tailwind to Bootstrap for consistency

**FileViewerPane.jsx:**
- CHECK: Is there a file viewing feature needed?
- If NOT used: Remove
- If KEEPING: Add to Activity view or create Files tab

**PipelineTreeView.jsx:**
- CHECK: Is this an alternative to AgentHierarchyTree?
- If DUPLICATE: Remove in favor of AgentHierarchyTree
- If DIFFERENT PURPOSE: Document and integrate

**ProblemInputForm.jsx:**
- CHECK: How is problem input currently handled in App.jsx?
- If INLINE: Keep inline, remove component
- If SHOULD USE COMPONENT: Refactor to use component

**ChatInterface.jsx:**
- CHECK: Is agent messaging implemented?
- If NOT USED: Remove
- If USED: Verify it's properly integrated

## Acceptance Criteria

1. All components in /components/ are either:
   - Used in App.jsx, OR
   - Documented as standalone utility, OR
   - Removed
2. No unused imports
3. Consistent styling approach (preferably Bootstrap)
4. No broken Tailwind dynamic classes

## Test Plan

1. After changes, run:
   ```bash
   npm run build
   ```
   Should have no unused import warnings.

2. Run dev server:
   ```bash
   npm run dev
   ```
   Navigate all views, verify no broken styling.

3. Check browser console for warnings about missing components.

## Notes

- Don't remove components that might be used in future phases
- If unsure, comment out rather than delete
- Document any components kept for future use
- The goal is clean, working code for V1
