"""Pattern Library for Common Development Tasks.

Stores reusable patterns for common development scenarios like CRUD APIs,
authentication, testing, etc. Used by the decomposition engine to improve
task breakdown accuracy and speed.
"""
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# Pattern Models
# ============================================================================

class PatternCategory(str, Enum):
    """Categories of development patterns."""
    CRUD_API = "crud_api"
    AUTHENTICATION = "authentication"
    DATABASE = "database"
    FILE_UPLOAD = "file_upload"
    PAYMENT_INTEGRATION = "payment_integration"
    EMAIL_NOTIFICATION = "email_notification"
    SEARCH_INDEXING = "search_indexing"
    REAL_TIME_UPDATES = "real_time_updates"
    ADMIN_DASHBOARD = "admin_dashboard"
    USER_PROFILE = "user_profile"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    CUSTOM = "custom"


@dataclass
class TaskTemplate:
    """Template for a common task."""
    task_id: str
    description: str
    agent_type: str
    complexity: str  # simple, creative, strategic
    estimated_duration_mins: int
    dependencies: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)


@dataclass
class DevelopmentPattern:
    """A reusable development pattern."""
    pattern_id: str
    name: str
    category: PatternCategory
    description: str
    task_templates: List[TaskTemplate]
    estimated_total_duration_mins: int
    complexity: str
    tags: List[str] = field(default_factory=list)
    usage_count: int = 0
    average_actual_duration_mins: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['category'] = self.category.value if isinstance(self.category, PatternCategory) else self.category
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DevelopmentPattern':
        """Create from dictionary."""
        # Convert category string back to enum
        if 'category' in data and isinstance(data['category'], str):
            data['category'] = PatternCategory(data['category'])

        # Convert task templates
        if 'task_templates' in data:
            data['task_templates'] = [
                TaskTemplate(**task) if isinstance(task, dict) else task
                for task in data['task_templates']
            ]

        return cls(**data)


# ============================================================================
# Pattern Library
# ============================================================================

class PatternLibrary:
    """
    Library of reusable development patterns.

    Provides pre-built task decompositions for common scenarios.
    """

    def __init__(self, library_path: Optional[Path] = None):
        """
        Initialize pattern library.

        Args:
            library_path: Path to save/load pattern library
        """
        if library_path is None:
            library_path = Path.home() / ".ensemble" / "pattern_library.json"

        self.library_path = library_path
        self.library_path.parent.mkdir(parents=True, exist_ok=True)

        self.patterns: Dict[str, DevelopmentPattern] = {}
        self.logger = logging.getLogger(__name__)

        # Load existing patterns or initialize defaults
        if self.library_path.exists():
            self.load()
        else:
            self._initialize_default_patterns()
            self.save()

    def _initialize_default_patterns(self):
        """Initialize library with common development patterns."""
        self.logger.info("Initializing default development patterns")

        # CRUD API Pattern
        self.add_pattern(DevelopmentPattern(
            pattern_id="crud_api_rest",
            name="REST CRUD API",
            category=PatternCategory.CRUD_API,
            description="Standard REST API with Create, Read, Update, Delete operations",
            task_templates=[
                TaskTemplate(
                    task_id="crud_1",
                    description="Create database model with fields and relationships",
                    agent_type="backend_developer",
                    complexity="creative",
                    estimated_duration_mins=25,
                    dependencies=[],
                    required_tools=["write_file"],
                    outputs=["models.py"],
                    acceptance_criteria=["Model created", "Fields defined", "Relationships mapped"]
                ),
                TaskTemplate(
                    task_id="crud_2",
                    description="Implement GET endpoint with filtering and pagination",
                    agent_type="backend_developer",
                    complexity="creative",
                    estimated_duration_mins=30,
                    dependencies=["crud_1"],
                    required_tools=["write_file"],
                    outputs=["routes.py"],
                    acceptance_criteria=["GET endpoint works", "Filtering works", "Pagination works"]
                ),
                TaskTemplate(
                    task_id="crud_3",
                    description="Implement POST endpoint with validation",
                    agent_type="backend_developer",
                    complexity="creative",
                    estimated_duration_mins=25,
                    dependencies=["crud_1"],
                    required_tools=["write_file"],
                    outputs=["routes.py", "schemas.py"],
                    acceptance_criteria=["POST endpoint works", "Validation works", "Returns created resource"]
                ),
                TaskTemplate(
                    task_id="crud_4",
                    description="Implement PUT/PATCH endpoint for updates",
                    agent_type="backend_developer",
                    complexity="creative",
                    estimated_duration_mins=20,
                    dependencies=["crud_1", "crud_2"],
                    required_tools=["write_file"],
                    outputs=["routes.py"],
                    acceptance_criteria=["Update endpoint works", "Returns updated resource"]
                ),
                TaskTemplate(
                    task_id="crud_5",
                    description="Implement DELETE endpoint",
                    agent_type="backend_developer",
                    complexity="simple",
                    estimated_duration_mins=15,
                    dependencies=["crud_1", "crud_2"],
                    required_tools=["write_file"],
                    outputs=["routes.py"],
                    acceptance_criteria=["Delete endpoint works", "Returns 204 status"]
                ),
                TaskTemplate(
                    task_id="crud_6",
                    description="Write CRUD endpoint tests",
                    agent_type="test_writer",
                    complexity="creative",
                    estimated_duration_mins=30,
                    dependencies=["crud_2", "crud_3", "crud_4", "crud_5"],
                    required_tools=["write_file", "run_command"],
                    outputs=["test_crud.py"],
                    acceptance_criteria=["All CRUD operations tested", "Tests pass", "Coverage > 80%"]
                )
            ],
            estimated_total_duration_mins=145,
            complexity="creative",
            tags=["api", "crud", "rest", "backend"]
        ))

        # Authentication Pattern
        self.add_pattern(DevelopmentPattern(
            pattern_id="auth_jwt",
            name="JWT Authentication",
            category=PatternCategory.AUTHENTICATION,
            description="JWT-based authentication with login, register, token refresh",
            task_templates=[
                TaskTemplate(
                    task_id="auth_1",
                    description="Create User model with password hashing",
                    agent_type="backend_developer",
                    complexity="creative",
                    estimated_duration_mins=20,
                    dependencies=[],
                    outputs=["models.py"],
                    acceptance_criteria=["User model created", "Password hashing works"]
                ),
                TaskTemplate(
                    task_id="auth_2",
                    description="Implement registration endpoint",
                    agent_type="backend_developer",
                    complexity="creative",
                    estimated_duration_mins=25,
                    dependencies=["auth_1"],
                    outputs=["auth_routes.py"],
                    acceptance_criteria=["Registration works", "Validates email", "Hashes password"]
                ),
                TaskTemplate(
                    task_id="auth_3",
                    description="Implement login endpoint with JWT generation",
                    agent_type="backend_developer",
                    complexity="creative",
                    estimated_duration_mins=30,
                    dependencies=["auth_1"],
                    outputs=["auth_routes.py", "jwt_utils.py"],
                    acceptance_criteria=["Login works", "Returns JWT token", "Validates credentials"]
                ),
                TaskTemplate(
                    task_id="auth_4",
                    description="Create JWT verification middleware",
                    agent_type="backend_developer",
                    complexity="creative",
                    estimated_duration_mins=25,
                    dependencies=["auth_3"],
                    outputs=["middleware/auth.py"],
                    acceptance_criteria=["Middleware validates JWT", "Handles expired tokens", "Returns 401 on invalid"]
                ),
                TaskTemplate(
                    task_id="auth_5",
                    description="Write authentication tests",
                    agent_type="test_writer",
                    complexity="creative",
                    estimated_duration_mins=25,
                    dependencies=["auth_2", "auth_3", "auth_4"],
                    outputs=["test_auth.py"],
                    acceptance_criteria=["All auth flows tested", "Security edge cases covered"]
                )
            ],
            estimated_total_duration_mins=125,
            complexity="creative",
            tags=["auth", "jwt", "security", "backend"]
        ))

        # Database Migration Pattern
        self.add_pattern(DevelopmentPattern(
            pattern_id="database_setup",
            name="Database Setup with Migrations",
            category=PatternCategory.DATABASE,
            description="Set up database connection and migration system",
            task_templates=[
                TaskTemplate(
                    task_id="db_1",
                    description="Configure database connection and ORM",
                    agent_type="backend_developer",
                    complexity="creative",
                    estimated_duration_mins=20,
                    outputs=["database.py", "config.py"],
                    acceptance_criteria=["Database connects", "ORM configured"]
                ),
                TaskTemplate(
                    task_id="db_2",
                    description="Set up migration system (Alembic/Prisma)",
                    agent_type="backend_developer",
                    complexity="creative",
                    estimated_duration_mins=25,
                    dependencies=["db_1"],
                    outputs=["alembic.ini", "migrations/"],
                    acceptance_criteria=["Migrations work", "Can upgrade/downgrade"]
                ),
                TaskTemplate(
                    task_id="db_3",
                    description="Create initial database schema migration",
                    agent_type="backend_developer",
                    complexity="simple",
                    estimated_duration_mins=15,
                    dependencies=["db_2"],
                    outputs=["migrations/001_initial.py"],
                    acceptance_criteria=["Initial migration created", "Migration runs successfully"]
                )
            ],
            estimated_total_duration_mins=60,
            complexity="creative",
            tags=["database", "migrations", "setup", "backend"]
        ))

        # Frontend Component Pattern
        self.add_pattern(DevelopmentPattern(
            pattern_id="react_component_form",
            name="React Form Component",
            category=PatternCategory.USER_PROFILE,
            description="React form component with validation and state management",
            task_templates=[
                TaskTemplate(
                    task_id="form_1",
                    description="Create form component structure",
                    agent_type="frontend_developer",
                    complexity="creative",
                    estimated_duration_mins=20,
                    outputs=["components/Form.jsx"],
                    acceptance_criteria=["Component renders", "Form fields present"]
                ),
                TaskTemplate(
                    task_id="form_2",
                    description="Add form validation logic",
                    agent_type="frontend_developer",
                    complexity="creative",
                    estimated_duration_mins=25,
                    dependencies=["form_1"],
                    outputs=["components/Form.jsx", "utils/validation.js"],
                    acceptance_criteria=["Validation works", "Shows error messages"]
                ),
                TaskTemplate(
                    task_id="form_3",
                    description="Connect form to state management (Redux/Context)",
                    agent_type="frontend_developer",
                    complexity="creative",
                    estimated_duration_mins=20,
                    dependencies=["form_2"],
                    outputs=["components/Form.jsx", "store/formSlice.js"],
                    acceptance_criteria=["State updates on input", "Form submits correctly"]
                ),
                TaskTemplate(
                    task_id="form_4",
                    description="Write form component tests",
                    agent_type="test_writer",
                    complexity="creative",
                    estimated_duration_mins=20,
                    dependencies=["form_3"],
                    outputs=["components/Form.test.jsx"],
                    acceptance_criteria=["Render tests pass", "Validation tested", "Submit tested"]
                )
            ],
            estimated_total_duration_mins=85,
            complexity="creative",
            tags=["react", "form", "validation", "frontend"]
        ))

        # Testing Pattern
        self.add_pattern(DevelopmentPattern(
            pattern_id="test_suite_setup",
            name="Test Suite Setup",
            category=PatternCategory.TESTING,
            description="Set up testing infrastructure with unit and integration tests",
            task_templates=[
                TaskTemplate(
                    task_id="test_1",
                    description="Configure testing framework (pytest/jest)",
                    agent_type="test_writer",
                    complexity="simple",
                    estimated_duration_mins=15,
                    outputs=["pytest.ini", "setup_tests.py"],
                    acceptance_criteria=["Test framework configured", "Sample test runs"]
                ),
                TaskTemplate(
                    task_id="test_2",
                    description="Write unit tests for core functionality",
                    agent_type="test_writer",
                    complexity="creative",
                    estimated_duration_mins=35,
                    dependencies=["test_1"],
                    outputs=["tests/unit/"],
                    acceptance_criteria=["Unit tests written", "Coverage > 80%"]
                ),
                TaskTemplate(
                    task_id="test_3",
                    description="Write integration tests",
                    agent_type="integration_test_lead",
                    complexity="creative",
                    estimated_duration_mins=40,
                    dependencies=["test_1"],
                    outputs=["tests/integration/"],
                    acceptance_criteria=["Integration tests written", "API integration tested"]
                )
            ],
            estimated_total_duration_mins=90,
            complexity="creative",
            tags=["testing", "pytest", "jest", "quality"]
        ))

        self.logger.info(f"Initialized {len(self.patterns)} default patterns")

    def add_pattern(self, pattern: DevelopmentPattern):
        """Add a pattern to the library."""
        self.patterns[pattern.pattern_id] = pattern
        self.logger.debug(f"Added pattern: {pattern.name}")

    def get_pattern(self, pattern_id: str) -> Optional[DevelopmentPattern]:
        """Get a pattern by ID."""
        return self.patterns.get(pattern_id)

    def search_patterns(
        self,
        query: Optional[str] = None,
        category: Optional[PatternCategory] = None,
        tags: Optional[List[str]] = None
    ) -> List[DevelopmentPattern]:
        """
        Search for patterns.

        Args:
            query: Text search in name/description
            category: Filter by category
            tags: Filter by tags (any match)

        Returns:
            List of matching patterns
        """
        results = []

        for pattern in self.patterns.values():
            # Filter by category
            if category and pattern.category != category:
                continue

            # Filter by tags
            if tags and not any(tag in pattern.tags for tag in tags):
                continue

            # Filter by query
            if query:
                query_lower = query.lower()
                if (query_lower not in pattern.name.lower() and
                    query_lower not in pattern.description.lower()):
                    continue

            results.append(pattern)

        return results

    def find_matching_pattern(self, request: str, domain: str) -> Optional[DevelopmentPattern]:
        """
        Find the best matching pattern for a user request.

        Args:
            request: User's request text
            domain: Domain (backend, frontend, etc)

        Returns:
            Best matching pattern or None
        """
        request_lower = request.lower()

        # Check for explicit pattern keywords
        if "crud" in request_lower and domain == "backend":
            return self.get_pattern("crud_api_rest")

        if any(kw in request_lower for kw in ["auth", "login", "register", "jwt"]):
            return self.get_pattern("auth_jwt")

        if "database" in request_lower and "migration" in request_lower:
            return self.get_pattern("database_setup")

        if "form" in request_lower and domain == "frontend":
            return self.get_pattern("react_component_form")

        if any(kw in request_lower for kw in ["test", "testing", "pytest", "jest"]):
            return self.get_pattern("test_suite_setup")

        return None

    def record_usage(self, pattern_id: str, actual_duration_mins: int):
        """
        Record usage of a pattern to improve estimates.

        Args:
            pattern_id: Pattern that was used
            actual_duration_mins: Actual time it took
        """
        pattern = self.patterns.get(pattern_id)
        if not pattern:
            return

        pattern.usage_count += 1

        # Update average actual duration
        if pattern.average_actual_duration_mins is None:
            pattern.average_actual_duration_mins = actual_duration_mins
        else:
            # Moving average
            pattern.average_actual_duration_mins = int(
                (pattern.average_actual_duration_mins * (pattern.usage_count - 1) + actual_duration_mins) / pattern.usage_count
            )

        self.logger.info(f"Updated pattern {pattern_id} usage: count={pattern.usage_count}, avg_duration={pattern.average_actual_duration_mins}m")
        self.save()

    def save(self):
        """Save pattern library to disk."""
        data = {
            "patterns": {
                pid: pattern.to_dict()
                for pid, pattern in self.patterns.items()
            }
        }

        with open(self.library_path, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.debug(f"Saved pattern library to {self.library_path}")

    def load(self):
        """Load pattern library from disk."""
        with open(self.library_path, 'r') as f:
            data = json.load(f)

        self.patterns = {
            pid: DevelopmentPattern.from_dict(pattern_data)
            for pid, pattern_data in data.get("patterns", {}).items()
        }

        self.logger.info(f"Loaded {len(self.patterns)} patterns from {self.library_path}")

    def get_stats(self) -> Dict[str, Any]:
        """Get library statistics."""
        return {
            "total_patterns": len(self.patterns),
            "by_category": {
                category.value: len([p for p in self.patterns.values() if p.category == category])
                for category in PatternCategory
            },
            "most_used": sorted(
                self.patterns.values(),
                key=lambda p: p.usage_count,
                reverse=True
            )[:5],
            "average_accuracy": self._calculate_average_accuracy()
        }

    def _calculate_average_accuracy(self) -> Optional[float]:
        """Calculate average estimate accuracy across patterns."""
        accuracies = []

        for pattern in self.patterns.values():
            if pattern.average_actual_duration_mins is not None:
                estimated = pattern.estimated_total_duration_mins
                actual = pattern.average_actual_duration_mins
                accuracy = 1 - abs(estimated - actual) / estimated if estimated > 0 else 0
                accuracies.append(accuracy)

        return sum(accuracies) / len(accuracies) if accuracies else None
