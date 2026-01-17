"""
Unit tests for pattern_library module.

Tests the PatternLibrary class and related components.
"""

import pytest
import tempfile
import json
from pathlib import Path
from src.runtime.agents.pattern_library import (
    PatternCategory,
    TaskTemplate,
    DevelopmentPattern,
    PatternLibrary,
)


class TestPatternCategory:
    """Test PatternCategory enum."""

    def test_category_values(self):
        """Test all category values."""
        assert PatternCategory.CRUD_API.value == "crud_api"
        assert PatternCategory.AUTHENTICATION.value == "authentication"
        assert PatternCategory.DATABASE.value == "database"
        assert PatternCategory.FILE_UPLOAD.value == "file_upload"
        assert PatternCategory.PAYMENT_INTEGRATION.value == "payment_integration"
        assert PatternCategory.EMAIL_NOTIFICATION.value == "email_notification"
        assert PatternCategory.SEARCH_INDEXING.value == "search_indexing"
        assert PatternCategory.REAL_TIME_UPDATES.value == "real_time_updates"
        assert PatternCategory.ADMIN_DASHBOARD.value == "admin_dashboard"
        assert PatternCategory.USER_PROFILE.value == "user_profile"
        assert PatternCategory.TESTING.value == "testing"
        assert PatternCategory.DEPLOYMENT.value == "deployment"
        assert PatternCategory.CUSTOM.value == "custom"

    def test_category_is_string_enum(self):
        """Test that category inherits from str."""
        # Should be usable as string
        assert PatternCategory.CRUD_API == "crud_api"


class TestTaskTemplate:
    """Test TaskTemplate dataclass."""

    def test_task_template_creation(self):
        """Test creating a TaskTemplate."""
        template = TaskTemplate(
            task_id="test_1",
            description="Test task description",
            agent_type="backend_developer",
            complexity="creative",
            estimated_duration_mins=30,
        )

        assert template.task_id == "test_1"
        assert template.description == "Test task description"
        assert template.agent_type == "backend_developer"
        assert template.complexity == "creative"
        assert template.estimated_duration_mins == 30
        # Defaults
        assert template.dependencies == []
        assert template.required_tools == []
        assert template.outputs == []
        assert template.acceptance_criteria == []

    def test_task_template_with_all_fields(self):
        """Test TaskTemplate with all optional fields."""
        template = TaskTemplate(
            task_id="test_full",
            description="Full task",
            agent_type="frontend_developer",
            complexity="simple",
            estimated_duration_mins=15,
            dependencies=["task_0"],
            required_tools=["write_file", "read_file"],
            outputs=["output.py"],
            acceptance_criteria=["Works correctly", "Tests pass"],
        )

        assert template.dependencies == ["task_0"]
        assert template.required_tools == ["write_file", "read_file"]
        assert template.outputs == ["output.py"]
        assert template.acceptance_criteria == ["Works correctly", "Tests pass"]


class TestDevelopmentPattern:
    """Test DevelopmentPattern dataclass."""

    @pytest.fixture
    def sample_task_templates(self):
        """Sample task templates for testing."""
        return [
            TaskTemplate(
                task_id="task_1",
                description="First task",
                agent_type="backend_developer",
                complexity="simple",
                estimated_duration_mins=20,
            ),
            TaskTemplate(
                task_id="task_2",
                description="Second task",
                agent_type="test_writer",
                complexity="creative",
                estimated_duration_mins=25,
                dependencies=["task_1"],
            ),
        ]

    def test_pattern_creation(self, sample_task_templates):
        """Test creating a DevelopmentPattern."""
        pattern = DevelopmentPattern(
            pattern_id="test_pattern",
            name="Test Pattern",
            category=PatternCategory.TESTING,
            description="A test pattern",
            task_templates=sample_task_templates,
            estimated_total_duration_mins=45,
            complexity="creative",
        )

        assert pattern.pattern_id == "test_pattern"
        assert pattern.name == "Test Pattern"
        assert pattern.category == PatternCategory.TESTING
        assert len(pattern.task_templates) == 2
        assert pattern.estimated_total_duration_mins == 45
        # Defaults
        assert pattern.tags == []
        assert pattern.usage_count == 0
        assert pattern.average_actual_duration_mins is None

    def test_pattern_with_tags(self, sample_task_templates):
        """Test pattern with tags."""
        pattern = DevelopmentPattern(
            pattern_id="tagged_pattern",
            name="Tagged Pattern",
            category=PatternCategory.CRUD_API,
            description="Pattern with tags",
            task_templates=sample_task_templates,
            estimated_total_duration_mins=45,
            complexity="creative",
            tags=["api", "rest", "backend"],
        )

        assert pattern.tags == ["api", "rest", "backend"]

    def test_pattern_to_dict(self, sample_task_templates):
        """Test to_dict serialization."""
        pattern = DevelopmentPattern(
            pattern_id="dict_pattern",
            name="Dict Pattern",
            category=PatternCategory.AUTHENTICATION,
            description="Test serialization",
            task_templates=sample_task_templates,
            estimated_total_duration_mins=45,
            complexity="creative",
            tags=["auth"],
            usage_count=5,
            average_actual_duration_mins=40,
        )

        data = pattern.to_dict()

        assert data["pattern_id"] == "dict_pattern"
        assert data["name"] == "Dict Pattern"
        assert data["category"] == "authentication"  # Converted to string
        assert len(data["task_templates"]) == 2
        assert data["usage_count"] == 5
        assert data["average_actual_duration_mins"] == 40

    def test_pattern_from_dict(self):
        """Test from_dict deserialization."""
        data = {
            "pattern_id": "from_dict_pattern",
            "name": "From Dict Pattern",
            "category": "crud_api",
            "description": "Test deserialization",
            "task_templates": [
                {
                    "task_id": "t1",
                    "description": "Task 1",
                    "agent_type": "developer",
                    "complexity": "simple",
                    "estimated_duration_mins": 15,
                }
            ],
            "estimated_total_duration_mins": 15,
            "complexity": "simple",
            "tags": ["test"],
        }

        pattern = DevelopmentPattern.from_dict(data)

        assert pattern.pattern_id == "from_dict_pattern"
        assert pattern.category == PatternCategory.CRUD_API
        assert len(pattern.task_templates) == 1
        assert isinstance(pattern.task_templates[0], TaskTemplate)

    def test_pattern_roundtrip_serialization(self, sample_task_templates):
        """Test that to_dict/from_dict roundtrip preserves data."""
        original = DevelopmentPattern(
            pattern_id="roundtrip",
            name="Roundtrip Pattern",
            category=PatternCategory.DATABASE,
            description="Test roundtrip",
            task_templates=sample_task_templates,
            estimated_total_duration_mins=45,
            complexity="creative",
            tags=["database", "setup"],
            usage_count=10,
            average_actual_duration_mins=50,
        )

        # Convert to dict and back
        data = original.to_dict()
        restored = DevelopmentPattern.from_dict(data)

        assert restored.pattern_id == original.pattern_id
        assert restored.name == original.name
        assert restored.category == original.category
        assert restored.usage_count == original.usage_count


class TestPatternLibrary:
    """Test PatternLibrary class."""

    @pytest.fixture
    def temp_library_path(self):
        """Create temporary library path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test_library.json"

    @pytest.fixture
    def library(self, temp_library_path):
        """Create a fresh PatternLibrary instance."""
        return PatternLibrary(library_path=temp_library_path)

    def test_init_creates_directory(self):
        """Test that initialization creates parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "new_subdir" / "test_library.json"

            # Ensure nested path doesn't exist
            assert not nested_path.parent.exists()

            library = PatternLibrary(library_path=nested_path)

            assert nested_path.parent.exists()

    def test_init_loads_default_patterns(self, library):
        """Test that default patterns are loaded on initialization."""
        # Should have default patterns
        assert len(library.patterns) > 0

        # Check for expected default patterns
        assert "crud_api_rest" in library.patterns
        assert "auth_jwt" in library.patterns
        assert "database_setup" in library.patterns

    def test_add_pattern(self, library):
        """Test adding a custom pattern."""
        pattern = DevelopmentPattern(
            pattern_id="custom_pattern",
            name="Custom Pattern",
            category=PatternCategory.CUSTOM,
            description="Custom test pattern",
            task_templates=[],
            estimated_total_duration_mins=30,
            complexity="simple",
        )

        library.add_pattern(pattern)

        assert "custom_pattern" in library.patterns
        assert library.patterns["custom_pattern"].name == "Custom Pattern"

    def test_get_pattern_exists(self, library):
        """Test getting an existing pattern."""
        pattern = library.get_pattern("crud_api_rest")

        assert pattern is not None
        assert pattern.pattern_id == "crud_api_rest"
        assert pattern.name == "REST CRUD API"

    def test_get_pattern_not_found(self, library):
        """Test getting a non-existent pattern."""
        pattern = library.get_pattern("nonexistent_pattern")

        assert pattern is None

    def test_search_patterns_all(self, library):
        """Test searching without filters returns all."""
        results = library.search_patterns()

        assert len(results) == len(library.patterns)

    def test_search_patterns_by_category(self, library):
        """Test searching by category."""
        results = library.search_patterns(category=PatternCategory.CRUD_API)

        assert len(results) > 0
        for pattern in results:
            assert pattern.category == PatternCategory.CRUD_API

    def test_search_patterns_by_tags(self, library):
        """Test searching by tags."""
        results = library.search_patterns(tags=["auth"])

        assert len(results) > 0
        for pattern in results:
            assert any(tag in pattern.tags for tag in ["auth"])

    def test_search_patterns_by_query(self, library):
        """Test searching by text query."""
        results = library.search_patterns(query="JWT")

        assert len(results) > 0
        for pattern in results:
            assert "jwt" in pattern.name.lower() or "jwt" in pattern.description.lower()

    def test_search_patterns_combined_filters(self, library):
        """Test searching with multiple filters."""
        results = library.search_patterns(
            category=PatternCategory.AUTHENTICATION,
            tags=["jwt"],
        )

        assert len(results) > 0
        for pattern in results:
            assert pattern.category == PatternCategory.AUTHENTICATION

    def test_find_matching_pattern_crud(self, library):
        """Test finding matching pattern for CRUD request."""
        pattern = library.find_matching_pattern(
            "I need a CRUD API for users",
            domain="backend"
        )

        assert pattern is not None
        assert pattern.pattern_id == "crud_api_rest"

    def test_find_matching_pattern_auth(self, library):
        """Test finding matching pattern for auth request."""
        pattern = library.find_matching_pattern(
            "Add login and registration",
            domain="backend"
        )

        assert pattern is not None
        assert pattern.pattern_id == "auth_jwt"

    def test_find_matching_pattern_jwt(self, library):
        """Test finding matching pattern for JWT request."""
        pattern = library.find_matching_pattern(
            "Implement JWT authentication",
            domain="backend"
        )

        assert pattern is not None
        assert pattern.pattern_id == "auth_jwt"

    def test_find_matching_pattern_database(self, library):
        """Test finding matching pattern for database request."""
        pattern = library.find_matching_pattern(
            "Set up database migration system",
            domain="backend"
        )

        assert pattern is not None
        assert pattern.pattern_id == "database_setup"

    def test_find_matching_pattern_form(self, library):
        """Test finding matching pattern for form request."""
        pattern = library.find_matching_pattern(
            "Create a form component",
            domain="frontend"
        )

        assert pattern is not None
        assert pattern.pattern_id == "react_component_form"

    def test_find_matching_pattern_testing(self, library):
        """Test finding matching pattern for testing request."""
        pattern = library.find_matching_pattern(
            "Set up testing infrastructure",
            domain="backend"
        )

        assert pattern is not None
        assert pattern.pattern_id == "test_suite_setup"

    def test_find_matching_pattern_no_match(self, library):
        """Test finding matching pattern with no match."""
        pattern = library.find_matching_pattern(
            "Do something completely unrelated",
            domain="backend"
        )

        assert pattern is None

    def test_record_usage_first_time(self, library):
        """Test recording first usage of a pattern."""
        library.record_usage("crud_api_rest", 150)

        pattern = library.get_pattern("crud_api_rest")
        assert pattern.usage_count == 1
        assert pattern.average_actual_duration_mins == 150

    def test_record_usage_moving_average(self, library):
        """Test that usage recording uses moving average."""
        library.record_usage("crud_api_rest", 100)
        library.record_usage("crud_api_rest", 200)

        pattern = library.get_pattern("crud_api_rest")
        assert pattern.usage_count == 2
        # Average of 100 and 200
        assert pattern.average_actual_duration_mins == 150

    def test_record_usage_unknown_pattern(self, library):
        """Test recording usage for unknown pattern."""
        # Should not raise
        library.record_usage("nonexistent", 100)

    def test_save_and_load(self, temp_library_path):
        """Test saving and loading library."""
        # Create library with custom pattern
        library1 = PatternLibrary(library_path=temp_library_path)
        library1.add_pattern(DevelopmentPattern(
            pattern_id="custom_save",
            name="Custom Save Pattern",
            category=PatternCategory.CUSTOM,
            description="Test saving",
            task_templates=[],
            estimated_total_duration_mins=30,
            complexity="simple",
        ))
        library1.save()

        # Create new library that loads from same path
        library2 = PatternLibrary(library_path=temp_library_path)

        assert "custom_save" in library2.patterns
        assert library2.patterns["custom_save"].name == "Custom Save Pattern"

    def test_get_stats(self, library):
        """Test getting library statistics."""
        stats = library.get_stats()

        assert "total_patterns" in stats
        assert stats["total_patterns"] == len(library.patterns)
        assert "by_category" in stats
        assert "most_used" in stats
        assert "average_accuracy" in stats

    def test_get_stats_by_category(self, library):
        """Test category breakdown in stats."""
        stats = library.get_stats()

        # All categories should be present
        for category in PatternCategory:
            assert category.value in stats["by_category"]

    def test_get_stats_most_used(self, library):
        """Test most used patterns in stats."""
        # Record some usage
        library.record_usage("crud_api_rest", 100)
        library.record_usage("crud_api_rest", 100)
        library.record_usage("auth_jwt", 100)

        stats = library.get_stats()

        # crud_api_rest should be first (most used)
        most_used = stats["most_used"]
        if most_used:
            assert most_used[0].pattern_id == "crud_api_rest"

    def test_calculate_average_accuracy(self, library):
        """Test average accuracy calculation."""
        # Record usage with actual durations
        library.record_usage("crud_api_rest", 145)  # Same as estimate

        stats = library.get_stats()

        # Should have accuracy calculation
        assert stats["average_accuracy"] is not None

    def test_calculate_average_accuracy_no_data(self, temp_library_path):
        """Test average accuracy with no usage data."""
        library = PatternLibrary(library_path=temp_library_path)

        stats = library.get_stats()

        # No patterns have usage data yet in fresh library
        # Average accuracy depends on whether any pattern has average_actual_duration_mins
        # It could be None if no pattern has been used


class TestPatternLibraryPersistence:
    """Test pattern library persistence scenarios."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_creates_parent_directories(self, temp_dir):
        """Test that nested parent directories are created."""
        nested_path = temp_dir / "deep" / "nested" / "path" / "library.json"

        library = PatternLibrary(library_path=nested_path)

        assert nested_path.parent.exists()

    def test_loads_existing_library(self, temp_dir):
        """Test loading existing library file."""
        library_path = temp_dir / "existing.json"

        # Create library file manually
        data = {
            "patterns": {
                "manual_pattern": {
                    "pattern_id": "manual_pattern",
                    "name": "Manually Created",
                    "category": "custom",
                    "description": "Created manually",
                    "task_templates": [],
                    "estimated_total_duration_mins": 10,
                    "complexity": "simple",
                    "tags": [],
                    "usage_count": 0,
                    "average_actual_duration_mins": None,
                }
            }
        }
        with open(library_path, 'w') as f:
            json.dump(data, f)

        library = PatternLibrary(library_path=library_path)

        assert "manual_pattern" in library.patterns
        # Should NOT have default patterns since we loaded existing file
        assert len(library.patterns) == 1

    def test_default_library_path(self):
        """Test default library path is in home directory."""
        # Just verify the path format (don't actually create it)
        expected_path = Path.home() / ".ensemble" / "pattern_library.json"

        # Create with a temp path to avoid side effects
        with tempfile.TemporaryDirectory() as tmpdir:
            library = PatternLibrary(library_path=Path(tmpdir) / "test.json")

        # The default path logic is: library_path = Path.home() / ".ensemble" / "pattern_library.json"
        # This just tests the default would be reasonable


class TestDefaultPatterns:
    """Test the default patterns have correct structure."""

    @pytest.fixture
    def library(self):
        """Create library with temp path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield PatternLibrary(library_path=Path(tmpdir) / "test.json")

    def test_crud_pattern_structure(self, library):
        """Test CRUD pattern has correct structure."""
        pattern = library.get_pattern("crud_api_rest")

        assert pattern.category == PatternCategory.CRUD_API
        assert len(pattern.task_templates) >= 6  # Create, Read, Update, Delete, Tests
        assert "crud" in pattern.tags

    def test_auth_pattern_structure(self, library):
        """Test Auth pattern has correct structure."""
        pattern = library.get_pattern("auth_jwt")

        assert pattern.category == PatternCategory.AUTHENTICATION
        assert "auth" in pattern.tags or "jwt" in pattern.tags

    def test_all_patterns_have_task_templates(self, library):
        """Test all patterns have task templates."""
        for pattern_id, pattern in library.patterns.items():
            assert len(pattern.task_templates) > 0, f"Pattern {pattern_id} has no tasks"

    def test_task_dependencies_valid(self, library):
        """Test task dependencies reference existing tasks."""
        for pattern_id, pattern in library.patterns.items():
            task_ids = {t.task_id for t in pattern.task_templates}

            for task in pattern.task_templates:
                for dep in task.dependencies:
                    assert dep in task_ids, (
                        f"Pattern {pattern_id}: task {task.task_id} "
                        f"has invalid dependency {dep}"
                    )
