"""Tests for Pattern Library."""
import pytest
import json
from pathlib import Path
import tempfile

from src.runtime.agents.pattern_library import (
    PatternLibrary,
    DevelopmentPattern,
    TaskTemplate,
    PatternCategory
)


class TestPatternLibrary:
    """Test pattern library functionality."""

    def test_initialize_default_patterns(self, tmp_path):
        """Test that default patterns are initialized."""
        library_path = tmp_path / "patterns.json"
        library = PatternLibrary(library_path=library_path)

        assert len(library.patterns) > 0
        assert "crud_api_rest" in library.patterns
        assert "auth_jwt" in library.patterns
        assert library_path.exists()

    def test_get_pattern(self, tmp_path):
        """Test getting a pattern by ID."""
        library = PatternLibrary(library_path=tmp_path / "patterns.json")

        pattern = library.get_pattern("crud_api_rest")

        assert pattern is not None
        assert pattern.pattern_id == "crud_api_rest"
        assert pattern.name == "REST CRUD API"
        assert pattern.category == PatternCategory.CRUD_API
        assert len(pattern.task_templates) > 0

    def test_search_patterns_by_category(self, tmp_path):
        """Test searching patterns by category."""
        library = PatternLibrary(library_path=tmp_path / "patterns.json")

        results = library.search_patterns(category=PatternCategory.AUTHENTICATION)

        assert len(results) > 0
        assert all(p.category == PatternCategory.AUTHENTICATION for p in results)

    def test_search_patterns_by_tags(self, tmp_path):
        """Test searching patterns by tags."""
        library = PatternLibrary(library_path=tmp_path / "patterns.json")

        results = library.search_patterns(tags=["api"])

        assert len(results) > 0
        assert all("api" in p.tags for p in results)

    def test_search_patterns_by_query(self, tmp_path):
        """Test searching patterns by text query."""
        library = PatternLibrary(library_path=tmp_path / "patterns.json")

        results = library.search_patterns(query="authentication")

        assert len(results) > 0
        assert any("auth" in p.name.lower() or "auth" in p.description.lower() for p in results)

    def test_find_matching_pattern_crud(self, tmp_path):
        """Test finding CRUD pattern from request."""
        library = PatternLibrary(library_path=tmp_path / "patterns.json")

        pattern = library.find_matching_pattern(
            request="Build a CRUD API for blog posts",
            domain="backend"
        )

        assert pattern is not None
        assert pattern.pattern_id == "crud_api_rest"

    def test_find_matching_pattern_auth(self, tmp_path):
        """Test finding auth pattern from request."""
        library = PatternLibrary(library_path=tmp_path / "patterns.json")

        pattern = library.find_matching_pattern(
            request="Add JWT authentication and login",
            domain="backend"
        )

        assert pattern is not None
        assert pattern.pattern_id == "auth_jwt"

    def test_add_custom_pattern(self, tmp_path):
        """Test adding a custom pattern."""
        library = PatternLibrary(library_path=tmp_path / "patterns.json")

        custom_pattern = DevelopmentPattern(
            pattern_id="custom_pattern",
            name="Custom Pattern",
            category=PatternCategory.CUSTOM,
            description="A custom test pattern",
            task_templates=[
                TaskTemplate(
                    task_id="custom_1",
                    description="Custom task",
                    agent_type="backend_developer",
                    complexity="simple",
                    estimated_duration_mins=10
                )
            ],
            estimated_total_duration_mins=10,
            complexity="simple",
            tags=["custom", "test"]
        )

        library.add_pattern(custom_pattern)

        retrieved = library.get_pattern("custom_pattern")
        assert retrieved is not None
        assert retrieved.name == "Custom Pattern"

    def test_record_usage(self, tmp_path):
        """Test recording pattern usage."""
        library = PatternLibrary(library_path=tmp_path / "patterns.json")

        pattern_id = "crud_api_rest"
        initial_count = library.patterns[pattern_id].usage_count

        library.record_usage(pattern_id, actual_duration_mins=150)

        pattern = library.get_pattern(pattern_id)
        assert pattern.usage_count == initial_count + 1
        assert pattern.average_actual_duration_mins == 150

        # Record another usage
        library.record_usage(pattern_id, actual_duration_mins=140)

        pattern = library.get_pattern(pattern_id)
        assert pattern.usage_count == initial_count + 2
        assert pattern.average_actual_duration_mins == 145  # Average of 150 and 140

    def test_save_and_load(self, tmp_path):
        """Test saving and loading pattern library."""
        library_path = tmp_path / "patterns.json"

        # Create library and add custom pattern
        library1 = PatternLibrary(library_path=library_path)
        initial_count = len(library1.patterns)

        custom_pattern = DevelopmentPattern(
            pattern_id="save_test",
            name="Save Test",
            category=PatternCategory.CUSTOM,
            description="Test pattern",
            task_templates=[],
            estimated_total_duration_mins=10,
            complexity="simple"
        )

        library1.add_pattern(custom_pattern)
        library1.save()

        # Load into new library instance
        library2 = PatternLibrary(library_path=library_path)

        assert len(library2.patterns) == initial_count + 1
        assert "save_test" in library2.patterns
        assert library2.get_pattern("save_test").name == "Save Test"

    def test_pattern_serialization(self):
        """Test pattern to_dict and from_dict."""
        pattern = DevelopmentPattern(
            pattern_id="test_pattern",
            name="Test Pattern",
            category=PatternCategory.TESTING,
            description="Test description",
            task_templates=[
                TaskTemplate(
                    task_id="task_1",
                    description="Test task",
                    agent_type="test_writer",
                    complexity="simple",
                    estimated_duration_mins=15,
                    dependencies=["task_0"],
                    outputs=["test.py"]
                )
            ],
            estimated_total_duration_mins=15,
            complexity="simple",
            tags=["test"],
            usage_count=5,
            average_actual_duration_mins=20
        )

        # Convert to dict
        pattern_dict = pattern.to_dict()

        assert pattern_dict["pattern_id"] == "test_pattern"
        assert pattern_dict["category"] == "testing"
        assert len(pattern_dict["task_templates"]) == 1

        # Convert back to pattern
        restored_pattern = DevelopmentPattern.from_dict(pattern_dict)

        assert restored_pattern.pattern_id == pattern.pattern_id
        assert restored_pattern.category == pattern.category
        assert len(restored_pattern.task_templates) == 1
        assert restored_pattern.usage_count == 5

    def test_get_stats(self, tmp_path):
        """Test getting library statistics."""
        library = PatternLibrary(library_path=tmp_path / "patterns.json")

        # Record some usage
        library.record_usage("crud_api_rest", 140)
        library.record_usage("auth_jwt", 120)

        stats = library.get_stats()

        assert "total_patterns" in stats
        assert "by_category" in stats
        assert "most_used" in stats
        assert stats["total_patterns"] > 0
        assert len(stats["most_used"]) <= 5

    def test_pattern_templates_structure(self, tmp_path):
        """Test that pattern templates have correct structure."""
        library = PatternLibrary(library_path=tmp_path / "patterns.json")

        crud_pattern = library.get_pattern("crud_api_rest")

        # Check all templates have required fields
        for template in crud_pattern.task_templates:
            assert template.task_id
            assert template.description
            assert template.agent_type
            assert template.complexity
            assert template.estimated_duration_mins > 0

    def test_crud_pattern_has_dependencies(self, tmp_path):
        """Test that CRUD pattern has proper task dependencies."""
        library = PatternLibrary(library_path=tmp_path / "patterns.json")

        crud_pattern = library.get_pattern("crud_api_rest")

        # First task should have no dependencies
        first_task = next(t for t in crud_pattern.task_templates if t.task_id == "crud_1")
        assert len(first_task.dependencies) == 0

        # Later tasks should have dependencies
        later_tasks = [t for t in crud_pattern.task_templates if t.task_id != "crud_1"]
        assert any(len(t.dependencies) > 0 for t in later_tasks)

    def test_find_no_matching_pattern(self, tmp_path):
        """Test that no pattern matches when request is unrelated."""
        library = PatternLibrary(library_path=tmp_path / "patterns.json")

        pattern = library.find_matching_pattern(
            request="Deploy to production using Kubernetes",
            domain="devops"
        )

        # Should return None if no pattern matches
        # (deployment pattern not in default set)
        assert pattern is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
