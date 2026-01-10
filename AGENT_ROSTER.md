# Ensemble Agent Roster

Complete hierarchy and role definitions for all agents in the Ensemble system.

## Hierarchy Overview

```
Executive Director (defines project)
    ↓
Program Coordinator (breaks into milestones)
    ↓
Caption Heads (break milestones into domain tasks)
    ├── Brass Caption Head (code writing)
    ├── Percussion Caption Head (testing)
    ├── Guard Caption Head (visual/styling/UX)
    └── Pit Caption Head (infrastructure)
    ↓
Drum Major (coordinates task execution across sections)
    ↓
Section Techs (supervise, determine completion, cross-section collaboration)
    ↓
Section Leaders (do work OR instantiate performers)
    ↓
Performers (optional - help when needed)
```

---

## Level 1: Strategic Leadership

### Executive Director
**Status:** Future
**Purpose:** Defines what the project is - the ultimate authority with long-term vision
**Responsibilities:**
- Understands user's high-level goals
- Determines project scope and vision
- Hands off to Program Coordinator for execution planning

### Program Coordinator
**Status:** ✅ Implemented (`leadership/program_coordinator.md`)
**Purpose:** Selects, designs, and drives implementation of the show concept
**Responsibilities:**
- Takes Executive Director's vision
- Analyzes problem description
- Creates structured requirements document
- Breaks project into milestones
- Hands milestones to Caption Heads

---

## Level 2: Domain Coordination (Caption Heads)

### Brass Caption Head
**Status:** Future
**Purpose:** Coordinates all code writing across the project
**Responsibilities:**
- Receives milestones from Program Coordinator
- Breaks down into code writing tasks
- Coordinates with other caption heads
- Assigns tasks to appropriate brass techs
- Reports completion status

### Percussion Caption Head
**Status:** Future
**Purpose:** Coordinates all testing across the project
**Responsibilities:**
- Receives milestones from Program Coordinator
- Breaks down into testing tasks
- Ensures proper test coverage
- Assigns tasks to appropriate percussion techs
- Reports completion status

### Guard Caption Head
**Status:** Future
**Purpose:** Coordinates all visual, styling, and UX work
**Responsibilities:**
- Receives milestones from Program Coordinator
- Breaks down into visual/UX tasks
- Ensures cohesive visual design
- Assigns tasks to appropriate guard techs
- Reports completion status

### Pit Caption Head
**Status:** Future
**Purpose:** Coordinates all infrastructure and deployment work
**Responsibilities:**
- Receives milestones from Program Coordinator
- Breaks down into infrastructure tasks
- Ensures proper deployment strategy
- Assigns tasks to appropriate pit techs
- Reports completion status

---

## Level 2.5: Architecture & Design

### Designer
**Status:** ✅ Implemented (`leadership/designer.md`)
**Purpose:** Designs the show formations and execution strategy
**Responsibilities:**
- Takes requirements from Program Coordinator
- Creates architecture proposal
- Proposes tech stack with justifications
- Defines system structure and component breakdown
- Requires user approval before implementation

---

## Level 3: Task Management

### Drum Major
**Status:** ✅ Implemented (`leadership/drum_major.md`)
**Purpose:** Directs and coordinates the ensemble through rehearsal
**Responsibilities:**
- Manages tempo, attitude, and execution
- Coordinates task execution one at a time
- Works with all section techs
- Implements Test-Driven Development (TDD) workflow
- Manages Red-Green-Refactor cycle
- Decides which sections are needed for each task
- Coordinates with Visual Tech for refactoring

---

## Level 4: Section Supervision

### Brass Section Techs
**Purpose:** Supervise code writing, determine completion, cross-section collaboration
**Domain Expertise:** Each tech has deep knowledge of their specific coding domain

#### Trumpet Tech
**Status:** Future
**Domain:** Frontend development (React, JavaScript/TypeScript, UI components)
**Supervises:** Trumpet (frontend code writer)
**Responsibilities:**
- Supervises frontend code writing
- Determines when frontend code is complete
- Coordinates with Guard techs for styling integration
- Reports to Brass Caption Head

#### Horn Tech
**Status:** Future
**Domain:** Component architecture (reusable components, component libraries)
**Supervises:** Horn (component code writer)
**Responsibilities:**
- Supervises component development
- Determines when components are complete
- Ensures component reusability
- Reports to Brass Caption Head

#### Baritone Tech
**Status:** Future
**Domain:** Backend development (Python, business logic, data processing)
**Supervises:** Baritone (backend code writer)
**Responsibilities:**
- Supervises backend code writing
- Determines when backend code is complete
- Coordinates with Pit techs for database integration
- Reports to Brass Caption Head

#### Tuba Tech
**Status:** Future
**Domain:** API development (REST APIs, endpoints, API contracts)
**Supervises:** Tuba (API code writer)
**Responsibilities:**
- Supervises API development
- Determines when APIs are complete
- Coordinates with Trumpet tech for frontend integration
- Reports to Brass Caption Head

### Percussion Section Techs
**Purpose:** Supervise testing, determine completion, cross-section collaboration
**Domain Expertise:** Each tech has deep knowledge of their specific testing domain

#### Snare Tech
**Status:** Future
**Domain:** Unit testing (pytest, test design, mocking, TDD red phase)
**Supervises:** Snare (unit test writer)
**Responsibilities:**
- Supervises unit test writing
- Determines when tests are complete
- Ensures proper test coverage
- Reports to Percussion Caption Head

#### Tenor Tech
**Status:** Future
**Domain:** Integration testing (API testing, component integration, mocked responses)
**Supervises:** Tenor (integration test writer)
**Responsibilities:**
- Supervises integration test writing
- Determines when integration tests are complete
- Coordinates across sections for integration scenarios
- Reports to Percussion Caption Head

#### Bass Tech
**Status:** Future
**Domain:** Performance testing (load testing, benchmarking, scalability)
**Supervises:** Bass (performance test writer)
**Responsibilities:**
- Supervises performance test writing
- Determines when performance tests are complete
- Ensures scalability requirements are met
- Reports to Percussion Caption Head

#### Cymbal Tech
**Status:** Future
**Domain:** Test validation (test running, results verification, CI integration)
**Supervises:** Cymbal (test validator)
**Responsibilities:**
- Supervises test execution
- Validates test results
- Ensures tests pass before code is accepted
- Reports to Percussion Caption Head

### Guard Section Techs
**Purpose:** Supervise visual/styling/UX work, determine completion
**Domain Expertise:** Each tech has deep knowledge of their visual domain

#### Flag Tech
**Status:** Future
**Domain:** Styling (CSS, design systems, responsive design)
**Supervises:** Flag (stylesheet writer)
**Responsibilities:**
- Supervises stylesheet development
- Determines when styles are complete
- Ensures design consistency
- Reports to Guard Caption Head

#### Rifle Tech
**Status:** Future
**Domain:** Component styling (styled components, CSS-in-JS)
**Supervises:** Rifle (component styling)
**Responsibilities:**
- Supervises component-level styling
- Determines when component styles are complete
- Coordinates with Horn tech for component integration
- Reports to Guard Caption Head

#### Saber Tech
**Status:** Future
**Domain:** Animation (CSS animations, transitions, motion design)
**Supervises:** Saber (animation agent)
**Responsibilities:**
- Supervises animation development
- Determines when animations are complete
- Ensures smooth user experience
- Reports to Guard Caption Head

#### Dance Tech
**Status:** Future
**Domain:** UX/Interaction design (user flows, interactions, accessibility)
**Supervises:** Dance (UX/interaction designer)
**Responsibilities:**
- Supervises UX design work
- Determines when interactions are complete
- Ensures accessibility standards
- Reports to Guard Caption Head

### Pit Section Techs
**Purpose:** Supervise infrastructure work, determine completion
**Domain Expertise:** Each tech has deep knowledge of their infrastructure domain

#### Marimba Tech
**Status:** Future
**Domain:** Deployment (Docker, cloud platforms, deployment strategies)
**Supervises:** Marimba (deployment agent)
**Responsibilities:**
- Supervises deployment setup
- Determines when deployment is complete
- Ensures reliable deployments
- Reports to Pit Caption Head

#### Vibes Tech
**Status:** Future
**Domain:** CI/CD (GitHub Actions, automated pipelines, continuous integration)
**Supervises:** Vibes (CI/CD agent)
**Responsibilities:**
- Supervises CI/CD pipeline creation
- Determines when pipelines are complete
- Ensures automated testing and deployment
- Reports to Pit Caption Head

#### Synth Tech
**Status:** Future
**Domain:** Database (schema design, queries, data modeling, migrations)
**Supervises:** Synth (database agent)
**Responsibilities:**
- Supervises database work
- Determines when database setup is complete
- Coordinates with Baritone tech for backend integration
- Reports to Pit Caption Head

---

## Level 5: Section Leaders (Workers)

### Brass Section (Code Writers)

#### Trumpet
**Status:** Future
**Function:** Frontend code writer
**Responsibilities:**
- Writes frontend code (React components, pages, UI logic)
- Can instantiate Trumpet 1, 2, 3 performers if needed
- Supervised by Trumpet Tech

#### Horn
**Status:** Future
**Function:** Component code writer
**Responsibilities:**
- Writes reusable components and component libraries
- Can instantiate Horn 1, 2 performers if needed
- Supervised by Horn Tech

#### Baritone
**Status:** ✅ Implemented (`brass/baritone.md`)
**Function:** Backend code writer
**Responsibilities:**
- Writes backend Python code (business logic, data processing)
- Can instantiate Baritone 1, 2, 3 performers if needed
- Supervised by Baritone Tech

#### Tuba
**Status:** Future
**Function:** API code writer
**Responsibilities:**
- Writes API endpoints, request/response handling
- Can instantiate Tuba 1, 2 performers if needed
- Supervised by Tuba Tech

### Percussion Section (Test Writers)

#### Snare
**Status:** ✅ Implemented (`percussion/snare.md`)
**Function:** Unit test writer (TDD RED phase)
**Responsibilities:**
- Writes failing unit tests before code exists
- Defines requirements through tests
- Can instantiate additional snares if needed
- Supervised by Snare Tech

#### Tenor
**Status:** Future
**Function:** Integration test writer
**Responsibilities:**
- Writes integration tests (cross-component, API tests)
- Uses mocked external responses
- Can instantiate additional tenors if needed
- Supervised by Tenor Tech

#### Bass
**Status:** ✅ Implemented (`percussion/bass.md`)
**Function:** Performance test writer
**Responsibilities:**
- Writes load tests, benchmarks, scalability tests
- Validates performance requirements
- Tests response time, throughput, and scalability
- Can instantiate additional bass performers if needed
- Supervised by Bass Tech

#### Cymbal
**Status:** Future
**Function:** Test validator/runner
**Responsibilities:**
- Runs test suites
- Validates test results
- Ensures tests pass
- Supervised by Cymbal Tech

### Guard Section (Visual/Styling)

#### Flag
**Status:** Future
**Function:** Stylesheet writer
**Responsibilities:**
- Writes CSS, creates design systems
- Ensures responsive design
- Can instantiate additional flag performers if needed
- Supervised by Flag Tech

#### Rifle
**Status:** Future
**Function:** Component styling
**Responsibilities:**
- Styles individual components
- Implements styled-components or CSS-in-JS
- Can instantiate additional rifle performers if needed
- Supervised by Rifle Tech

#### Saber
**Status:** Future
**Function:** Animation agent
**Responsibilities:**
- Creates animations and transitions
- Implements motion design
- Can instantiate additional saber performers if needed
- Supervised by Saber Tech

#### Dance
**Status:** Future
**Function:** UX/interaction designer
**Responsibilities:**
- Designs user flows and interactions
- Ensures accessibility
- Can instantiate additional dancers if needed
- Supervised by Dance Tech

### Pit Section (Infrastructure)

#### Marimba
**Status:** Future
**Function:** Deployment agent
**Responsibilities:**
- Sets up deployment infrastructure
- Creates Docker containers, deployment configs
- Can instantiate additional marimba performers if needed
- Supervised by Marimba Tech

#### Vibes
**Status:** Future
**Function:** CI/CD agent
**Responsibilities:**
- Creates CI/CD pipelines
- Automates testing and deployment
- Can instantiate additional vibes performers if needed
- Supervised by Vibes Tech

#### Synth
**Status:** Future
**Function:** Database agent
**Responsibilities:**
- Designs database schema
- Writes migrations and queries
- Can instantiate additional synth performers if needed
- Supervised by Synth Tech

---

## Special Roles

### Visual Tech
**Status:** ✅ Implemented (`support/visual_tech.md`)
**Purpose:** Cleans spacing, alignment, and technique (refactoring)
**Responsibilities:**
- Refactors code without changing behavior (TDD REFACTOR phase)
- Works at direction of Drum Major
- Can spawn additional visual techs if needed
- Ensures code quality and maintainability
- Works during "visual rehearsal" phase

---

## Logistics & Support Staff

### Logistics Manager
**Status:** ✅ Implemented (`support/logistics_manager.md`)
**Role:** Coordinates transportation, equipment, and site surveying
**Purpose:** File exploration and codebase surveying - gets the ensemble oriented in new codebases
**Responsibilities:**
- Explores existing codebases
- Maps file structures and dependencies
- Identifies relevant code sections
- Surveys the "venue" before the show
- Provides context to other agents
- Handles navigation between different parts of the codebase

### Monitor
**Status:** Future
**Role:** Nurse (health checks)
**Purpose:** System health monitoring
**Responsibilities:**
- Monitors system performance
- Checks for errors and warnings
- Alerts when issues are detected

### Error Handler
**Status:** Future
**Role:** Physical therapist (fixes problems)
**Purpose:** Error recovery and problem resolution
**Responsibilities:**
- Handles runtime errors
- Provides recovery strategies
- Helps agents when they get stuck

### Logger
**Status:** Future
**Role:** Souvenir stand (records what happened)
**Purpose:** Event recording and documentation
**Responsibilities:**
- Logs agent activities
- Tracks decisions made
- Provides audit trail

---

## Level 6: Performers (Optional)

Performers are additional instances instantiated by section leaders when needed.

**Examples:**
- Trumpet 1, Trumpet 2, Trumpet 3 (help Trumpet with complex frontend work)
- Snare 1, Snare 2 (help Snare with extensive test writing)
- etc.

**Implementation:**
- Rookie performers: Simpler, more cautious implementations
- Veteran performers: More sophisticated, efficient implementations

---

## Current Implementation Status

**✅ Implemented:**
- Program Coordinator (requirements analysis)
- Designer (architecture design)
- Drum Major (TDD task orchestration)
- Snare (unit test writer)
- Baritone (backend code writer)
- Bass (performance test writer)
- Visual Tech (refactoring)
- Logistics Manager (codebase exploration and surveying)

**🚧 Next Priority:**
- Executive Director (project definition)
- Caption Heads (all four)
- Section Techs (starting with most critical domains)
- Frontend section leaders (Trumpet, Horn)

**📋 Future:**
- All remaining section leaders
- Performer instantiation system
- Logistics/support staff
- Rookie vs Veteran tiers

---

## Notes

1. **Tech-Written Tests:** Section techs can write the tests that section leaders (performers) write code to pass. This creates a clean TDD flow where techs define requirements via tests, and performers implement solutions.

2. **Section Tech Agents:** Each section tech is a separate agent with domain expertise. They supervise section leaders and determine when work is complete.

3. **Scalability:** Section leaders can instantiate additional performers when work is complex enough to require it.

4. **Reporting:** Section techs report completion to caption heads, who report to Program Coordinator/Executive Director.

5. **Rookie vs Veteran:** Future implementation will support tiered performers - rookies for simpler/cautious implementations, veterans for sophisticated/efficient work.
