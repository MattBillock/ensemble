"""
Unit tests for task_watcher.py

Tests for the load_project_data function that loads project configuration
from JSON files in the ~/.ensemble/projects/ directory structure.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch
from scripts.monitoring.task_watcher import load_project_data


class TestLoadProjectData:
    """Test suite for load_project_data function."""

    def test_load_valid_project_data(self, tmp_path):
        """
        Test loading valid project data from a properly formatted JSON file.
        
        Verifies that:
        - Function returns a dictionary (not None)
        - Dictionary contains all expected keys: project_id, project_name, tasks
        - Values match the content from the JSON file
        """
        # Arrange
        project_id = "test_project_123"
        project_name = "Test Project"
        tasks = [
            {"id": "task1", "description": "First task", "status": "todo"},
            {"id": "task2", "description": "Second task", "status": "in_progress"}
        ]
        
        # Create project directory structure
        project_dir = tmp_path / project_id
        project_dir.mkdir(parents=True)
        
        # Create valid project.json
        project_data = {
            "project_id": project_id,
            "project_name": project_name,
            "tasks": tasks
        }
        project_file = project_dir / "project.json"
        project_file.write_text(json.dumps(project_data))
        
        # Act
        result = load_project_data(project_id, projects_dir=str(tmp_path))
        
        # Assert
        assert result is not None, "Expected dict, got None"
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert "project_id" in result, "Missing 'project_id' key"
        assert "project_name" in result, "Missing 'project_name' key"
        assert "tasks" in result, "Missing 'tasks' key"
        assert result["project_id"] == project_id, f"Expected project_id '{project_id}', got '{result['project_id']}'"
        assert result["project_name"] == project_name, f"Expected project_name '{project_name}', got '{result['project_name']}'"
        assert result["tasks"] == tasks, f"Tasks don't match: expected {tasks}, got {result['tasks']}"

    def test_load_missing_file(self, tmp_path):
        """
        Test loading project data when the project.json file doesn't exist.
        
        Verifies that:
        - Function returns None when file is missing
        - No exceptions are raised (graceful handling)
        """
        # Arrange
        project_id = "nonexistent_project"
        # Don't create any files - directory is empty
        
        # Act
        result = load_project_data(project_id, projects_dir=str(tmp_path))
        
        # Assert
        assert result is None, f"Expected None for missing file, got {result}"

    def test_load_invalid_json(self, tmp_path):
        """
        Test loading project data from a file with malformed JSON.
        
        Verifies that:
        - Function returns None when JSON is malformed
        - JSONDecodeError is handled gracefully (no exception raised)
        """
        # Arrange
        project_id = "malformed_project"
        
        # Create project directory structure
        project_dir = tmp_path / project_id
        project_dir.mkdir(parents=True)
        
        # Create file with invalid JSON content
        project_file = project_dir / "project.json"
        invalid_json = '{"project_id": "test", "project_name": "Test", "tasks": [invalid json content'
        project_file.write_text(invalid_json)
        
        # Act
        result = load_project_data(project_id, projects_dir=str(tmp_path))
        
        # Assert
        assert result is None, f"Expected None for malformed JSON, got {result}"

    def test_load_custom_dir(self, tmp_path):
        """
        Test loading project data from a custom directory instead of default.
        
        Verifies that:
        - projects_dir parameter overrides the default ~/.ensemble/projects/ location
        - Function loads data from the custom directory
        - Data is correctly parsed and returned
        """
        # Arrange
        project_id = "custom_dir_project"
        project_name = "Custom Directory Project"
        tasks = [{"id": "task_custom", "description": "Task in custom dir", "status": "completed"}]
        
        # Create custom directory structure
        custom_projects_dir = tmp_path / "custom_projects"
        custom_projects_dir.mkdir(parents=True)
        project_dir = custom_projects_dir / project_id
        project_dir.mkdir(parents=True)
        
        # Create project.json in custom location
        project_data = {
            "project_id": project_id,
            "project_name": project_name,
            "tasks": tasks
        }
        project_file = project_dir / "project.json"
        project_file.write_text(json.dumps(project_data))
        
        # Act
        result = load_project_data(project_id, projects_dir=str(custom_projects_dir))
        
        # Assert
        assert result is not None, "Expected dict from custom directory, got None"
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert result["project_id"] == project_id, f"Expected project_id '{project_id}', got '{result['project_id']}'"
        assert result["project_name"] == project_name, f"Expected project_name '{project_name}', got '{result['project_name']}'"
        assert result["tasks"] == tasks, f"Tasks don't match: expected {tasks}, got {result['tasks']}"

    def test_load_default_directory_expansion(self, tmp_path):
        """
        Test that default directory uses home directory expansion.
        
        Verifies that:
        - When projects_dir is None, function uses ~/.ensemble/projects/
        - Home directory is properly expanded
        - Function attempts to load from the correct default location
        """
        # Arrange
        project_id = "default_dir_project"
        project_name = "Default Dir Project"
        tasks = []
        
        # Create mock home directory structure
        mock_home = tmp_path / "mock_home"
        ensemble_dir = mock_home / ".ensemble" / "projects" / project_id
        ensemble_dir.mkdir(parents=True)
        
        # Create project.json in mock home directory
        project_data = {
            "project_id": project_id,
            "project_name": project_name,
            "tasks": tasks
        }
        project_file = ensemble_dir / "project.json"
        project_file.write_text(json.dumps(project_data))
        
        # Act - patch Path.home() to return our mock home directory
        with patch('pathlib.Path.home', return_value=mock_home):
            result = load_project_data(project_id, projects_dir=None)
        
        # Assert
        assert result is not None, "Expected dict from default directory, got None"
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert result["project_id"] == project_id, f"Expected project_id '{project_id}', got '{result['project_id']}'"
        assert result["project_name"] == project_name, f"Expected project_name '{project_name}', got '{result['project_name']}'"
        assert result["tasks"] == tasks, f"Tasks don't match: expected {tasks}, got {result['tasks']}"
