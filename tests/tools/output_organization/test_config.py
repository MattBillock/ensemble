"""
Unit tests for config.py module.

This test suite validates the output organization configuration including:
- CATEGORY_RULES: List of (regex_pattern, category_name) tuples
- OUTPUT_ROOT: Path object for output directory
- STANDARD_CATEGORIES: List of valid category names

Following TDD RED phase - tests written before implementation.
"""

import re
from pathlib import Path
import pytest

# Import the module under test
from src.runtime.output_organization import config


class TestModuleStructure:
    """Tests for verifying the basic structure of config module."""

    def test_category_rules_exists_and_is_list(self):
        """Test that CATEGORY_RULES exists and is a list."""
        # Arrange & Act
        category_rules = config.CATEGORY_RULES
        
        # Assert
        assert isinstance(category_rules, list), "CATEGORY_RULES should be a list"
        assert len(category_rules) > 0, "CATEGORY_RULES should not be empty"

    def test_category_rules_items_are_tuples(self):
        """Test that each item in CATEGORY_RULES is a tuple."""
        # Arrange
        category_rules = config.CATEGORY_RULES
        
        # Act & Assert
        for item in category_rules:
            assert isinstance(item, tuple), f"Each CATEGORY_RULES item should be a tuple, got {type(item)}"

    def test_category_rules_tuple_has_two_elements(self):
        """Test that each tuple in CATEGORY_RULES has exactly 2 elements."""
        # Arrange
        category_rules = config.CATEGORY_RULES
        
        # Act & Assert
        for item in category_rules:
            assert len(item) == 2, f"Each tuple should have 2 elements (pattern, category), got {len(item)}"

    def test_category_rules_first_element_is_compiled_regex(self):
        """Test that the first element of each tuple is a compiled regex pattern."""
        # Arrange
        category_rules = config.CATEGORY_RULES
        
        # Act & Assert
        for pattern, category in category_rules:
            assert isinstance(pattern, re.Pattern), f"First element should be compiled regex (re.Pattern), got {type(pattern)}"

    def test_category_rules_second_element_is_string(self):
        """Test that the second element of each tuple is a string."""
        # Arrange
        category_rules = config.CATEGORY_RULES
        
        # Act & Assert
        for pattern, category in category_rules:
            assert isinstance(category, str), f"Second element should be string, got {type(category)}"
            assert len(category) > 0, "Category name should not be empty"

    def test_output_root_exists_and_is_path(self):
        """Test that OUTPUT_ROOT exists and is a Path object."""
        # Arrange & Act
        output_root = config.OUTPUT_ROOT
        
        # Assert
        assert isinstance(output_root, Path), f"OUTPUT_ROOT should be a Path object, got {type(output_root)}"

    def test_output_root_points_to_correct_directory(self):
        """Test that OUTPUT_ROOT points to the correct directory path."""
        # Arrange
        expected_path = Path('/Users/mattbillock/Development/ai_exploration/ensemble/src/field/ensemble_ui/output/')
        
        # Act
        output_root = config.OUTPUT_ROOT
        
        # Assert
        assert output_root == expected_path, f"OUTPUT_ROOT should point to {expected_path}, got {output_root}"

    def test_standard_categories_exists_and_is_list(self):
        """Test that STANDARD_CATEGORIES exists and is a list."""
        # Arrange & Act
        standard_categories = config.STANDARD_CATEGORIES
        
        # Assert
        assert isinstance(standard_categories, list), "STANDARD_CATEGORIES should be a list"

    def test_standard_categories_has_eight_items(self):
        """Test that STANDARD_CATEGORIES contains exactly 8 categories."""
        # Arrange
        expected_count = 8
        
        # Act
        standard_categories = config.STANDARD_CATEGORIES
        
        # Assert
        assert len(standard_categories) == expected_count, f"STANDARD_CATEGORIES should have {expected_count} items, got {len(standard_categories)}"

    def test_standard_categories_contains_all_expected_categories(self):
        """Test that STANDARD_CATEGORIES contains all expected category names."""
        # Arrange
        expected_categories = {'requirements', 'architecture', 'milestones', 'tasks', 'reports', 'planning', 'guides', 'status'}
        
        # Act
        standard_categories = config.STANDARD_CATEGORIES
        
        # Assert
        assert set(standard_categories) == expected_categories, f"STANDARD_CATEGORIES should contain {expected_categories}, got {set(standard_categories)}"


class TestRegexPatternMatching:
    """Tests for verifying regex patterns correctly match expected filenames."""

    def test_requirements_pattern_matches_requirements_files(self):
        """Test that requirements pattern matches requirement-related markdown files."""
        # Arrange
        test_filenames = [
            'requirements.md',
            'project_requirements.md',
            'requirements_v2.md',
            'system_requirements.md',
            'requirements_doc.md'
        ]
        category_rules = config.CATEGORY_RULES
        requirements_pattern = None
        
        # Find the requirements pattern
        for pattern, category in category_rules:
            if category == 'requirements':
                requirements_pattern = pattern
                break
        
        assert requirements_pattern is not None, "No pattern found for 'requirements' category"
        
        # Act & Assert
        for filename in test_filenames:
            assert requirements_pattern.match(filename), f"Pattern should match {filename}"

    def test_architecture_pattern_matches_architecture_files(self):
        """Test that architecture pattern matches architecture-related markdown files."""
        # Arrange
        test_filenames = [
            'architecture.md',
            'system_architecture.md',
            'architecture_overview.md',
            'architecture_design.md'
        ]
        category_rules = config.CATEGORY_RULES
        architecture_pattern = None
        
        # Find the architecture pattern
        for pattern, category in category_rules:
            if category == 'architecture':
                architecture_pattern = pattern
                break
        
        assert architecture_pattern is not None, "No pattern found for 'architecture' category"
        
        # Act & Assert
        for filename in test_filenames:
            assert architecture_pattern.match(filename), f"Pattern should match {filename}"

    def test_milestones_pattern_matches_milestone_files(self):
        """Test that milestones pattern matches milestone-related markdown files."""
        # Arrange
        test_filenames = [
            'milestone.md',
            'project_milestone.md',
            'milestone_1.md',
            'milestone_report.md',
            'q1_milestone.md'
        ]
        category_rules = config.CATEGORY_RULES
        milestones_pattern = None
        
        # Find the milestones pattern
        for pattern, category in category_rules:
            if category == 'milestones':
                milestones_pattern = pattern
                break
        
        assert milestones_pattern is not None, "No pattern found for 'milestones' category"
        
        # Act & Assert
        for filename in test_filenames:
            assert milestones_pattern.match(filename), f"Pattern should match {filename}"

    def test_tasks_pattern_matches_task_files(self):
        """Test that tasks pattern matches task-related markdown files."""
        # Arrange
        test_filenames = [
            'backend_tasks.md',
            'backend.md',
            'frontend.md',
            'test_tasks.md',
            'api_tasks.md',
            'frontend_tasks.md',
            'dev_tasks.md'
        ]
        category_rules = config.CATEGORY_RULES
        tasks_pattern = None
        
        # Find the tasks pattern
        for pattern, category in category_rules:
            if category == 'tasks':
                tasks_pattern = pattern
                break
        
        assert tasks_pattern is not None, "No pattern found for 'tasks' category"
        
        # Act & Assert
        for filename in test_filenames:
            assert tasks_pattern.match(filename), f"Pattern should match {filename}"

    def test_reports_pattern_matches_report_files(self):
        """Test that reports pattern matches report-related markdown files."""
        # Arrange
        test_filenames = [
            'report.md',
            'weekly_report.md',
            'analysis.md',
            'audit.md',
            'assessment.md',
            'security_audit.md',
            'performance_analysis.md'
        ]
        category_rules = config.CATEGORY_RULES
        reports_pattern = None
        
        # Find the reports pattern
        for pattern, category in category_rules:
            if category == 'reports':
                reports_pattern = pattern
                break
        
        assert reports_pattern is not None, "No pattern found for 'reports' category"
        
        # Act & Assert
        for filename in test_filenames:
            assert reports_pattern.match(filename), f"Pattern should match {filename}"

    def test_planning_pattern_matches_planning_files(self):
        """Test that planning pattern matches planning-related markdown files."""
        # Arrange
        test_filenames = [
            'plan.md',
            'project_plan.md',
            'feasibility.md',
            'feasibility_study.md',
            'sprint_plan.md'
        ]
        category_rules = config.CATEGORY_RULES
        planning_pattern = None
        
        # Find the planning pattern
        for pattern, category in category_rules:
            if category == 'planning':
                planning_pattern = pattern
                break
        
        assert planning_pattern is not None, "No pattern found for 'planning' category"
        
        # Act & Assert
        for filename in test_filenames:
            assert planning_pattern.match(filename), f"Pattern should match {filename}"

    def test_guides_pattern_matches_guide_files(self):
        """Test that guides pattern matches guide-related markdown files."""
        # Arrange
        test_filenames = [
            'guide.md',
            'user_guide.md',
            'dictionary.md',
            'reference.md',
            'inventory.md',
            'api_reference.md',
            'style_guide.md'
        ]
        category_rules = config.CATEGORY_RULES
        guides_pattern = None
        
        # Find the guides pattern
        for pattern, category in category_rules:
            if category == 'guides':
                guides_pattern = pattern
                break
        
        assert guides_pattern is not None, "No pattern found for 'guides' category"
        
        # Act & Assert
        for filename in test_filenames:
            assert guides_pattern.match(filename), f"Pattern should match {filename}"

    def test_status_pattern_matches_status_files(self):
        """Test that status pattern matches status-related markdown files."""
        # Arrange
        test_filenames = [
            'status.md',
            'project_status.md',
            'implementation_status.md',
            'current_status.md'
        ]
        category_rules = config.CATEGORY_RULES
        status_pattern = None
        
        # Find the status pattern
        for pattern, category in category_rules:
            if category == 'status':
                status_pattern = pattern
                break
        
        assert status_pattern is not None, "No pattern found for 'status' category"
        
        # Act & Assert
        for filename in test_filenames:
            assert status_pattern.match(filename), f"Pattern should match {filename}"


class TestEdgeCases:
    """Tests for edge cases and negative scenarios."""

    def test_non_matching_filenames_dont_match(self):
        """Test that filenames not matching any pattern don't match."""
        # Arrange
        non_matching_filenames = [
            'random.md',
            'notes.md',
            'todo.md',
            'readme.md',
            'changelog.md'
        ]
        category_rules = config.CATEGORY_RULES
        
        # Act & Assert
        for filename in non_matching_filenames:
            matched = False
            for pattern, category in category_rules:
                if pattern.match(filename):
                    matched = True
                    break
            assert not matched, f"Filename {filename} should not match any pattern"

    def test_filenames_without_md_extension_dont_match(self):
        """Test that filenames without .md extension don't match patterns."""
        # Arrange
        non_md_filenames = [
            'requirements.txt',
            'architecture.pdf',
            'milestone',
            'report.docx',
            'plan.html'
        ]
        category_rules = config.CATEGORY_RULES
        
        # Act & Assert
        for filename in non_md_filenames:
            matched = False
            for pattern, category in category_rules:
                if pattern.match(filename):
                    matched = True
                    break
            assert not matched, f"Filename {filename} without .md extension should not match any pattern"
