# Mobile Responsive UI Enhancement Requirements

## Project Overview

**Vision**: Make the Ensemble AI web UI responsive and usable on mobile devices while addressing system stability issues with stalled agents.

**Background**: The current Ensemble UI is built with React and Bootstrap, but lacks proper mobile responsiveness. The three-column layout doesn't adapt well to smaller screens. Additionally, the system has several agents that have failed with BadRequestError, suggesting configuration or API issues that need resolution.

## Objectives

### Primary Objectives
1. **Mobile Responsiveness**: Make the UI fully responsive and usable on mobile devices (320px-768px width)
2. **Agent Recovery**: Resume/fix high priority stalled agents that have failed with BadRequestError
3. **Improved UX**: Ensure all features are accessible and usable on touch devices

### Success Criteria
1. UI renders correctly on mobile devices (320px-768px viewport)
2. All interactive elements are touch-friendly (minimum 44x44px tap targets)
3. Navigation works seamlessly on mobile
4. Failed agents are identified and issues resolved
5. System can successfully spawn and run agents without BadRequestError
6. All existing functionality remains working on desktop

## Scope

### In Scope

#### 1. Mobile UI Enhancements
- **Responsive Layout**: Convert 3-column layout to stack vertically on mobile
- **Navigation**: Add mobile-friendly navigation (hamburger menu or tab system)
- **Touch Optimization**: Ensure buttons, controls, and interactive elements are touch-friendly
- **Viewport Configuration**: Add proper meta tags for mobile rendering
- **Typography**: Adjust font sizes for readability on small screens
- **Collapsible Sections**: Ensure all collapsible sections work well on mobile
- **Form Inputs**: Optimize form controls for mobile (larger touch targets, appropriate keyboard types)

#### 2. Agent System Recovery
- **Error Analysis**: Identify root cause of BadRequestError failures
- **Configuration Fix**: Correct API configuration issues (model names, API keys, parameters)
- **Agent Resume**: Implement mechanism to resume or restart failed agents
- **Priority Agents**: Focus on high-priority agents first:
  - leadership/development_manager
  - testers/unit_test_lead
  - executive_director instances

#### 3. Responsive Breakpoints
- **Mobile**: 320px-767px (single column, stacked layout)
- **Tablet**: 768px-1023px (two column or adaptive layout)
- **Desktop**: 1024px+ (current three-column layout)

### Out of Scope
- Complete UI redesign or rebranding
- Adding new features beyond responsiveness
- Backend API changes (unless required for agent recovery)
- Performance optimization beyond responsive design
- Accessibility audit (though basic accessibility will be maintained)
- Progressive Web App (PWA) features
- Offline functionality

## Constraints

### Technical Constraints
1. Must maintain existing React + Bootstrap architecture
2. Must not break existing desktop functionality
3. Should use CSS media queries and Bootstrap responsive utilities
4. Must work in modern mobile browsers (Safari iOS 14+, Chrome Android 90+)

### Resource Constraints
1. Changes should be minimal and focused on responsiveness
2. Avoid major architectural changes
3. Use existing Bootstrap grid system and utilities

## Requirements

### Functional Requirements

#### FR1: Mobile Layout Adaptation
- **FR1.1**: On screens < 768px, convert 3-column layout to single-column stacked layout
- **FR1.2**: Sections should stack in order: Input Form → Questions → Activity Feed → Agent Tasks → Files → Hierarchy
- **FR1.3**: All sections should be independently scrollable or use native page scrolling

#### FR2: Mobile Navigation
- **FR2.1**: Add tab navigation or collapsible sections for main content areas
- **FR2.2**: Header should remain fixed or easily accessible on mobile
- **FR2.3**: Poll interval controls should be accessible but not take excessive space

#### FR3: Touch-Friendly Controls
- **FR3.1**: All buttons and interactive elements must be minimum 44x44px
- **FR3.2**: Form inputs should have appropriate spacing (padding) for touch
- **FR3.3**: Dropdown selects should be mobile-friendly
- **FR3.4**: Badge and status indicators should remain readable

#### FR4: Responsive Typography
- **FR4.1**: Font sizes should scale appropriately for mobile (14px-16px body text)
- **FR4.2**: Headers should be proportionally sized
- **FR4.3**: Code blocks and file content should be readable with horizontal scroll if needed

#### FR5: Agent Recovery System
- **FR5.1**: Identify all agents with BadRequestError
- **FR5.2**: Analyze error logs to determine root cause (likely model name or API configuration)
- **FR5.3**: Fix configuration issues in agent spawning code or API calls
- **FR5.4**: Provide mechanism to retry failed agents or restart from checkpoint

### Non-Functional Requirements

#### NFR1: Performance
- Mobile responsiveness should not impact load time
- CSS media queries should use efficient selectors
- No significant increase in bundle size

#### NFR2: Compatibility
- Must work on iOS Safari 14+
- Must work on Chrome Android 90+
- Must work on Firefox Mobile
- Maintain backward compatibility with desktop browsers

#### NFR3: Maintainability
- Use Bootstrap's built-in responsive utilities where possible
- Keep custom CSS organized and documented
- Follow existing code style and conventions

## Assumptions

1. **Mobile viewport meta tag** is missing and needs to be added to index.html
2. **BadRequestError** is likely caused by incorrect model names or API configuration
3. Users will primarily use portrait orientation on mobile devices
4. The backend API endpoints are already responsive and work on mobile
5. No authentication or authorization changes are needed
6. The agent system has the capability to resume/retry failed tasks

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Bootstrap grid doesn't adapt well | High | Low | Use custom CSS media queries if needed |
| Touch targets too small | Medium | Medium | Test on real devices, increase button sizes |
| Agent errors require backend changes | High | Medium | Document findings, coordinate with backend if needed |
| Layout breaks on specific devices | Medium | Low | Test on multiple devices/emulators |
| Performance degradation on mobile | Low | Low | Profile and optimize if issues arise |

## Implementation Approach

### Phase 1: Mobile UI Implementation
1. Add viewport meta tag to HTML
2. Implement responsive breakpoints using Bootstrap grid
3. Convert 3-column to stacked layout on mobile
4. Adjust typography and spacing for mobile
5. Ensure touch-friendly controls
6. Test on multiple device sizes

### Phase 2: Agent System Analysis & Recovery
1. Query metrics database for failed agents
2. Analyze error messages and logs
3. Identify root cause (model config, API keys, parameters)
4. Implement fixes in agent spawning/configuration
5. Test agent spawning with corrected configuration
6. Resume high-priority failed agents

### Phase 3: Testing & Validation
1. Test on real mobile devices (iOS, Android)
2. Verify all functionality works on mobile
3. Ensure desktop functionality unchanged
4. Validate agent recovery successful
5. Document changes and any configuration updates

## Deliverables

1. **Updated Frontend Code**:
   - Modified App.jsx with responsive layout
   - Updated component files for mobile optimization
   - Custom CSS for responsive design (if needed)
   - Updated index.html with viewport meta tag

2. **Agent Recovery Documentation**:
   - Error analysis report
   - Root cause identification
   - Configuration fixes applied
   - Resume/restart procedures

3. **Testing Documentation**:
   - Mobile device testing results
   - Screenshots of responsive layout
   - Agent recovery test results

4. **Updated README**: Documentation of mobile support and any configuration changes

## Dependencies

- Existing Ensemble UI codebase
- Bootstrap 5.x responsive utilities
- React 18.x
- Backend API (for agent recovery)
- Access to ~/.ensemble/metrics.db for agent analysis

## Technology Stack

- **Frontend**: React 18.x, Bootstrap 5.x
- **Styling**: Bootstrap responsive utilities, custom CSS media queries
- **Build**: Vite
- **Testing**: Manual testing on mobile devices/emulators
- **Agent System**: Python-based agent orchestration system

## Notes

- The user request mentions "resume high priority stalled agents" - this suggests there are agents that are currently blocked/failed
- Database query shows multiple agents failed with BadRequestError, most recently development_manager and unit_test_lead
- This is likely a configuration issue (wrong model names, API parameters) rather than a code logic issue
- The mobile responsiveness work is straightforward, but agent recovery may require investigation into the agent spawning system
