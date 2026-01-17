# Backend Tasks - Milestone 1: Core Theming Infrastructure

## Overview
Establish the foundation for the theming system with basic theme switching capabilities. This milestone focuses on the backend infrastructure needed to support theme persistence, validation, and API access.

## Tech Stack (per Architecture)
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Validation**: Pydantic models
- **Testing**: pytest with coverage

---

## Task Group 1: Database Foundation

### Task 1.1: Database Connection Setup
**Description**: Configure PostgreSQL database connection with SQLAlchemy async support and connection pooling.

**Acceptance Criteria**:
- [ ] SQLAlchemy async engine configured
- [ ] Connection pooling enabled with reasonable defaults (min=5, max=20)
- [ ] Database URL configurable via environment variables
- [ ] Health check endpoint for database connectivity
- [ ] Connection error handling with retry logic

**Dependencies**: None (foundational)

**Complexity**: Simple

**Files to Create**:
- `backend/app/core/database.py`
- `backend/app/core/config.py`

---

### Task 1.2: Theme Database Model
**Description**: Create SQLAlchemy model for Theme entity with all required fields per the data model specification.

**Acceptance Criteria**:
- [ ] Theme model with fields: id (UUID), name, description, colors (JSONB), typography (JSONB), spacing (JSONB), borders (JSONB)
- [ ] Timestamps: created_at, updated_at
- [ ] is_system flag to distinguish pre-built themes from custom themes
- [ ] user_id foreign key for custom themes (nullable for system themes)
- [ ] Proper indexes on frequently queried fields (user_id, is_system, name)

**Dependencies**: Task 1.1

**Complexity**: Simple

**Files to Create**:
- `backend/app/models/theme.py`
- `backend/app/models/__init__.py`

---

### Task 1.3: Database Migrations Setup
**Description**: Configure Alembic for database migrations and create initial migration for Theme table.

**Acceptance Criteria**:
- [ ] Alembic configured with async SQLAlchemy support
- [ ] Initial migration creates themes table
- [ ] Migration includes all indexes
- [ ] Rollback capability tested
- [ ] Migration scripts work with empty database

**Dependencies**: Task 1.2

**Complexity**: Simple

**Files to Create**:
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/001_create_themes_table.py`

---

## Task Group 2: Pydantic Schemas & Validation

### Task 2.1: Theme Pydantic Schemas
**Description**: Create Pydantic models for theme data validation, serialization, and API request/response handling.

**Acceptance Criteria**:
- [ ] ColorScheme model with fields: primary, secondary, background, surface, text_primary, text_secondary, error, warning, success
- [ ] Typography model with fields: font_family, font_size_base, line_height, font_weights
- [ ] Spacing model with fields: base_unit, scale_factor
- [ ] Borders model with fields: radius, width
- [ ] ThemeCreate schema for POST requests
- [ ] ThemeUpdate schema for PUT/PATCH requests (all fields optional)
- [ ] ThemeResponse schema for API responses
- [ ] ThemeList schema for paginated list responses

**Dependencies**: None (can be developed in parallel with Task Group 1)

**Complexity**: Medium

**Files to Create**:
- `backend/app/schemas/theme.py`
- `backend/app/schemas/__init__.py`

---

### Task 2.2: Color Validation Service
**Description**: Implement color validation including hex format validation and WCAG contrast ratio checking.

**Acceptance Criteria**:
- [ ] Validate hex color format (3 or 6 character hex with optional #)
- [ ] Normalize colors to consistent format (#RRGGBB)
- [ ] Calculate contrast ratio between two colors
- [ ] Validate text/background combinations meet WCAG 2.1 AA (4.5:1 for normal text, 3:1 for large text)
- [ ] Return detailed validation errors with specific failing combinations
- [ ] Support batch validation of entire color scheme

**Dependencies**: Task 2.1

**Complexity**: Medium

**Files to Create**:
- `backend/app/services/color_validator.py`

---

### Task 2.3: Theme Validation Service
**Description**: Comprehensive theme validation service that validates all theme properties and ensures data integrity.

**Acceptance Criteria**:
- [ ] Validate all color values using color validation service
- [ ] Validate typography values (font_size_base > 0, line_height > 0)
- [ ] Validate spacing values (base_unit > 0, scale_factor > 0)
- [ ] Validate borders values (radius >= 0, width >= 0)
- [ ] Validate theme name (non-empty, max 100 chars, no XSS characters)
- [ ] Return aggregated validation result with all errors
- [ ] Provide accessibility score based on contrast ratios

**Dependencies**: Task 2.2

**Complexity**: Medium

**Files to Create**:
- `backend/app/services/theme_validator.py`

---

## Task Group 3: Theme Service Layer

### Task 3.1: Theme Repository
**Description**: Create data access layer for theme CRUD operations with proper async support.

**Acceptance Criteria**:
- [ ] get_by_id(theme_id) - returns theme or None
- [ ] get_all(user_id, include_system=True, skip, limit) - returns paginated themes
- [ ] create(theme_data) - creates and returns new theme
- [ ] update(theme_id, theme_data) - updates and returns theme
- [ ] delete(theme_id) - soft delete or hard delete theme
- [ ] exists(theme_id) - checks if theme exists
- [ ] get_by_name(name, user_id) - find theme by name for uniqueness check
- [ ] All methods use async/await pattern
- [ ] Proper error handling for database errors

**Dependencies**: Task 1.2, Task 2.1

**Complexity**: Medium

**Files to Create**:
- `backend/app/repositories/theme_repository.py`
- `backend/app/repositories/__init__.py`

---

### Task 3.2: Theme Service
**Description**: Business logic layer for theme operations including validation, authorization, and CRUD orchestration.

**Acceptance Criteria**:
- [ ] create_theme(user_id, theme_data) - validates and creates theme
- [ ] update_theme(user_id, theme_id, theme_data) - validates ownership and updates
- [ ] delete_theme(user_id, theme_id) - validates ownership and deletes
- [ ] get_theme(theme_id) - retrieves single theme
- [ ] list_themes(user_id, include_system, pagination) - lists accessible themes
- [ ] Enforce uniqueness of theme name per user
- [ ] Prevent modification/deletion of system themes
- [ ] Integrate validation service before create/update
- [ ] Raise appropriate exceptions (NotFoundError, ForbiddenError, ValidationError)

**Dependencies**: Task 3.1, Task 2.3

**Complexity**: Medium

**Files to Create**:
- `backend/app/services/theme_service.py`
- `backend/app/core/exceptions.py`

---

## Task Group 4: API Endpoints

### Task 4.1: Theme API Router
**Description**: Implement REST API endpoints for theme CRUD operations.

**Endpoints**:
- `GET /api/v1/themes` - List themes (paginated)
- `POST /api/v1/themes` - Create custom theme
- `GET /api/v1/themes/{theme_id}` - Get single theme
- `PUT /api/v1/themes/{theme_id}` - Update theme
- `DELETE /api/v1/themes/{theme_id}` - Delete theme

**Acceptance Criteria**:
- [ ] All endpoints implemented with proper HTTP methods
- [ ] Request validation using Pydantic schemas
- [ ] Response serialization using Pydantic schemas
- [ ] Proper HTTP status codes (200, 201, 204, 400, 404, 403, 422)
- [ ] Pagination support on list endpoint (page, page_size query params)
- [ ] Filter support on list endpoint (include_system query param)
- [ ] OpenAPI documentation with examples
- [ ] Dependency injection for service layer

**Dependencies**: Task 3.2

**Complexity**: Medium

**Files to Create**:
- `backend/app/api/v1/themes.py`
- `backend/app/api/v1/__init__.py`
- `backend/app/api/__init__.py`

---

### Task 4.2: API Error Handling
**Description**: Implement global exception handlers and error response formatting.

**Acceptance Criteria**:
- [ ] Global exception handler for application exceptions
- [ ] Consistent error response format: {error: {code, message, details}}
- [ ] Map domain exceptions to HTTP status codes
- [ ] ValidationError -> 422 with field-level details
- [ ] NotFoundError -> 404
- [ ] ForbiddenError -> 403
- [ ] Log errors appropriately (debug for client errors, error for server errors)
- [ ] Hide internal error details in production

**Dependencies**: Task 3.2 (needs exception types)

**Complexity**: Simple

**Files to Create**:
- `backend/app/api/error_handlers.py`

---

### Task 4.3: FastAPI Application Setup
**Description**: Configure FastAPI application with middleware, routers, and startup/shutdown events.

**Acceptance Criteria**:
- [ ] FastAPI app instance with metadata (title, version, description)
- [ ] CORS middleware configured (configurable origins)
- [ ] Include theme router at /api/v1/themes
- [ ] Database connection on startup
- [ ] Database cleanup on shutdown
- [ ] Health check endpoint at /health
- [ ] OpenAPI schema available at /docs

**Dependencies**: Task 4.1, Task 4.2, Task 1.1

**Complexity**: Simple

**Files to Create**:
- `backend/app/main.py`

---

## Task Group 5: Default Themes Seeding

### Task 5.1: Default Theme Definitions
**Description**: Define the three pre-built system themes: Light, Dark, and High Contrast.

**Acceptance Criteria**:
- [ ] Light theme with professional light color scheme
- [ ] Dark theme with professional dark color scheme  
- [ ] High Contrast theme meeting WCAG AAA contrast requirements
- [ ] All themes pass accessibility validation (4.5:1 contrast minimum)
- [ ] Themes stored as Python constants or JSON files
- [ ] Each theme has id, name, description, and all style properties

**Dependencies**: Task 2.1

**Complexity**: Simple

**Files to Create**:
- `backend/app/data/default_themes.py`

---

### Task 5.2: Database Seeder
**Description**: Create database seeder to initialize default themes on first run.

**Acceptance Criteria**:
- [ ] Seed default themes if they don't exist
- [ ] Don't duplicate themes on subsequent runs (idempotent)
- [ ] Can be run via CLI command or on app startup
- [ ] Log seeding operations
- [ ] Support --force flag to recreate default themes

**Dependencies**: Task 5.1, Task 3.1

**Complexity**: Simple

**Files to Create**:
- `backend/app/scripts/seed_themes.py`

---

## Task Dependency Graph

```
Task 1.1 (DB Connection)
    └── Task 1.2 (Theme Model)
            └── Task 1.3 (Migrations)
            └── Task 3.1 (Repository)
                    └── Task 3.2 (Service)
                            └── Task 4.1 (API Router)
                                    └── Task 4.3 (App Setup)

Task 2.1 (Schemas) ─────────┬── Task 2.2 (Color Validation)
                            │       └── Task 2.3 (Theme Validation)
                            │               └── Task 3.2 (Service)
                            └── Task 3.1 (Repository)
                            └── Task 5.1 (Default Themes)
                                    └── Task 5.2 (Seeder)

Task 3.2 (Service) ─── Task 4.2 (Error Handling) ─── Task 4.3 (App Setup)
```

## Implementation Order (Critical Path)

### Phase 1: Foundation (Parallel)
1. **Task 1.1**: Database Connection Setup
2. **Task 2.1**: Theme Pydantic Schemas

### Phase 2: Data Layer (Sequential)
3. **Task 1.2**: Theme Database Model
4. **Task 1.3**: Database Migrations

### Phase 3: Validation (Sequential)
5. **Task 2.2**: Color Validation Service
6. **Task 2.3**: Theme Validation Service

### Phase 4: Business Logic (Sequential after Phase 2 & 3)
7. **Task 3.1**: Theme Repository
8. **Task 3.2**: Theme Service
9. **Task 4.2**: API Error Handling

### Phase 5: API Layer (Sequential)
10. **Task 4.1**: Theme API Router
11. **Task 4.3**: FastAPI Application Setup

### Phase 6: Seeding (After Phase 4)
12. **Task 5.1**: Default Theme Definitions
13. **Task 5.2**: Database Seeder

## Summary

| Task ID | Task Name | Complexity | Dependencies |
|---------|-----------|------------|--------------|
| 1.1 | Database Connection Setup | Simple | None |
| 1.2 | Theme Database Model | Simple | 1.1 |
| 1.3 | Database Migrations Setup | Simple | 1.2 |
| 2.1 | Theme Pydantic Schemas | Medium | None |
| 2.2 | Color Validation Service | Medium | 2.1 |
| 2.3 | Theme Validation Service | Medium | 2.2 |
| 3.1 | Theme Repository | Medium | 1.2, 2.1 |
| 3.2 | Theme Service | Medium | 3.1, 2.3 |
| 4.1 | Theme API Router | Medium | 3.2 |
| 4.2 | API Error Handling | Simple | 3.2 |
| 4.3 | FastAPI Application Setup | Simple | 4.1, 4.2, 1.1 |
| 5.1 | Default Theme Definitions | Simple | 2.1 |
| 5.2 | Database Seeder | Simple | 5.1, 3.1 |

**Total Tasks**: 13
**Simple**: 6 tasks
**Medium**: 7 tasks
**Complex**: 0 tasks
