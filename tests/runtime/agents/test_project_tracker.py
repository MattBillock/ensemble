"""
Unit tests for project_tracker module.

Tests the ProjectTracker class for project state management.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime


class TestTaskStatus:
    """Test TaskStatus enum."""

    def test_task_status_values(self):
        """Test that all task statuses exist with correct values."""
        from src.runtime.agents.project_tracker import TaskStatus

        assert TaskStatus.TODO.value == "todo"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.BLOCKED.value == "blocked"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestProjectTask:
    """Test ProjectTask dataclass."""

    def test_project_task_creation(self):
        """Test creating a ProjectTask."""
        from src.runtime.agents.project_tracker import ProjectTask, TaskStatus

        task = ProjectTask(
            task_id="task1",
            description="Test task",
            status=TaskStatus.TODO
        )

        assert task.task_id == "task1"
        assert task.description == "Test task"
        assert task.status == TaskStatus.TODO
        assert task.notes == []
        assert task.dependencies == []
        assert task.created_at is not None

    def test_project_task_with_all_fields(self):
        """Test creating a ProjectTask with all fields."""
        from src.runtime.agents.project_tracker import ProjectTask, TaskStatus

        task = ProjectTask(
            task_id="task1",
            description="Test task",
            status=TaskStatus.IN_PROGRESS,
            assigned_to="developer",
            created_at="2024-01-01T00:00:00",
            started_at="2024-01-02T00:00:00",
            completed_at=None,
            notes=["note1"],
            dependencies=["dep1"]
        )

        assert task.assigned_to == "developer"
        assert task.notes == ["note1"]
        assert task.dependencies == ["dep1"]

    def test_project_task_to_dict(self):
        """Test ProjectTask serialization to dict."""
        from src.runtime.agents.project_tracker import ProjectTask, TaskStatus

        task = ProjectTask(
            task_id="task1",
            description="Test task",
            status=TaskStatus.TODO
        )

        task_dict = task.to_dict()

        assert task_dict["task_id"] == "task1"
        assert task_dict["description"] == "Test task"
        assert task_dict["status"] == "todo"  # Should be string value


class TestProjectNote:
    """Test ProjectNote dataclass."""

    def test_project_note_creation(self):
        """Test creating a ProjectNote."""
        from src.runtime.agents.project_tracker import ProjectNote

        note = ProjectNote(
            timestamp="2024-01-01T00:00:00",
            author="test_author",
            note="Test note",
            category="general"
        )

        assert note.timestamp == "2024-01-01T00:00:00"
        assert note.author == "test_author"
        assert note.note == "Test note"
        assert note.category == "general"

    def test_project_note_to_dict(self):
        """Test ProjectNote serialization to dict."""
        from src.runtime.agents.project_tracker import ProjectNote

        note = ProjectNote(
            timestamp="2024-01-01T00:00:00",
            author="test_author",
            note="Test note"
        )

        note_dict = note.to_dict()

        assert note_dict["timestamp"] == "2024-01-01T00:00:00"
        assert note_dict["author"] == "test_author"
        assert note_dict["note"] == "Test note"


class TestProjectState:
    """Test ProjectState dataclass."""

    def test_project_state_creation(self):
        """Test creating a ProjectState."""
        from src.runtime.agents.project_tracker import ProjectState

        state = ProjectState(
            project_id="proj1",
            project_name="Test Project",
            description="A test project",
            status="active",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            tasks={},
            notes=[]
        )

        assert state.project_id == "proj1"
        assert state.project_name == "Test Project"
        assert state.status == "active"

    def test_project_state_to_dict(self):
        """Test ProjectState serialization to dict."""
        from src.runtime.agents.project_tracker import ProjectState, ProjectTask, TaskStatus

        state = ProjectState(
            project_id="proj1",
            project_name="Test Project",
            description="A test project",
            status="active",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            tasks={
                "task1": ProjectTask(
                    task_id="task1",
                    description="Test task",
                    status=TaskStatus.TODO
                )
            },
            notes=[]
        )

        state_dict = state.to_dict()

        assert state_dict["project_id"] == "proj1"
        assert "task1" in state_dict["tasks"]
        assert state_dict["tasks"]["task1"]["status"] == "todo"

    def test_project_state_from_dict(self):
        """Test ProjectState deserialization from dict."""
        from src.runtime.agents.project_tracker import ProjectState, TaskStatus

        data = {
            "project_id": "proj1",
            "project_name": "Test Project",
            "description": "A test project",
            "status": "active",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "tasks": {
                "task1": {
                    "task_id": "task1",
                    "description": "Test task",
                    "status": "todo",
                    "created_at": "2024-01-01T00:00:00"
                }
            },
            "notes": [
                {
                    "timestamp": "2024-01-01T00:00:00",
                    "author": "test",
                    "note": "Test note",
                    "category": "general"
                }
            ]
        }

        state = ProjectState.from_dict(data)

        assert state.project_id == "proj1"
        assert "task1" in state.tasks
        assert state.tasks["task1"].status == TaskStatus.TODO
        assert len(state.notes) == 1


class TestProjectTracker:
    """Test ProjectTracker class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def tracker(self, temp_dir):
        """Create a ProjectTracker with temp directory."""
        from src.runtime.agents.project_tracker import ProjectTracker
        return ProjectTracker(projects_dir=temp_dir)

    def test_init_creates_directory(self, temp_dir):
        """Test that initialization creates the projects directory."""
        from src.runtime.agents.project_tracker import ProjectTracker

        projects_dir = temp_dir / "projects"
        tracker = ProjectTracker(projects_dir=projects_dir)

        assert projects_dir.exists()

    def test_create_project(self, tracker):
        """Test creating a new project."""
        project = tracker.create_project(
            project_name="Test Project",
            description="A test project"
        )

        assert project.project_name == "Test Project"
        assert project.description == "A test project"
        assert project.status == "active"
        assert len(project.notes) == 1  # Initial creation note

    def test_create_project_with_options(self, tracker):
        """Test creating a project with all options."""
        project = tracker.create_project(
            project_name="Test Project",
            description="A test project",
            request_id="req123",
            budget_tier="full_firepower",
            output_directory="/tmp/output"
        )

        assert project.request_id == "req123"
        assert project.budget_tier == "full_firepower"
        assert project.output_directory == "/tmp/output"

    def test_get_project(self, tracker):
        """Test retrieving a project."""
        created = tracker.create_project(
            project_name="Test Project",
            description="A test project"
        )

        retrieved = tracker.get_project(created.project_id)

        assert retrieved is not None
        assert retrieved.project_id == created.project_id
        assert retrieved.project_name == "Test Project"

    def test_get_project_not_found(self, tracker):
        """Test retrieving a non-existent project."""
        result = tracker.get_project("nonexistent")

        assert result is None

    def test_get_project_from_cache(self, tracker):
        """Test that projects are cached."""
        project = tracker.create_project(
            project_name="Test Project",
            description="A test project"
        )

        # Clear the disk file
        (tracker.projects_dir / f"{project.project_id}.json").unlink()

        # Should still be retrievable from cache
        retrieved = tracker.get_project(project.project_id)
        assert retrieved is not None

    def test_update_project(self, tracker):
        """Test updating a project."""
        project = tracker.create_project(
            project_name="Test Project",
            description="A test project"
        )

        project.status = "completed"
        tracker.update_project(project)

        # Clear cache and reload
        tracker._cache.clear()
        retrieved = tracker.get_project(project.project_id)

        assert retrieved.status == "completed"

    def test_add_task(self, tracker):
        """Test adding a task to a project."""
        project = tracker.create_project(
            project_name="Test Project",
            description="A test project"
        )

        task_id = tracker.add_task(
            project_id=project.project_id,
            description="Test task",
            assigned_to="developer"
        )

        updated = tracker.get_project(project.project_id)
        assert task_id in updated.tasks
        assert updated.tasks[task_id].description == "Test task"
        assert updated.tasks[task_id].assigned_to == "developer"

    def test_add_task_with_dependencies(self, tracker):
        """Test adding a task with dependencies."""
        project = tracker.create_project(
            project_name="Test Project",
            description="A test project"
        )

        task1_id = tracker.add_task(project.project_id, "Task 1")
        task2_id = tracker.add_task(
            project.project_id,
            "Task 2",
            dependencies=[task1_id]
        )

        updated = tracker.get_project(project.project_id)
        assert updated.tasks[task2_id].dependencies == [task1_id]

    def test_add_task_project_not_found(self, tracker):
        """Test adding task to non-existent project raises error."""
        with pytest.raises(ValueError, match="Project not found"):
            tracker.add_task("nonexistent", "Test task")

    def test_update_task_status(self, tracker):
        """Test updating a task's status."""
        from src.runtime.agents.project_tracker import TaskStatus

        project = tracker.create_project(
            project_name="Test Project",
            description="A test project"
        )
        task_id = tracker.add_task(project.project_id, "Test task")

        tracker.update_task_status(
            project.project_id,
            task_id,
            TaskStatus.IN_PROGRESS
        )

        updated = tracker.get_project(project.project_id)
        assert updated.tasks[task_id].status == TaskStatus.IN_PROGRESS
        assert updated.tasks[task_id].started_at is not None

    def test_update_task_status_completed(self, tracker):
        """Test completing a task sets completed_at."""
        from src.runtime.agents.project_tracker import TaskStatus

        project = tracker.create_project(
            project_name="Test Project",
            description="A test project"
        )
        task_id = tracker.add_task(project.project_id, "Test task")

        tracker.update_task_status(project.project_id, task_id, TaskStatus.COMPLETED)

        updated = tracker.get_project(project.project_id)
        assert updated.tasks[task_id].completed_at is not None

    def test_update_task_status_with_note(self, tracker):
        """Test updating task status with a note."""
        from src.runtime.agents.project_tracker import TaskStatus

        project = tracker.create_project(
            project_name="Test Project",
            description="A test project"
        )
        task_id = tracker.add_task(project.project_id, "Test task")

        tracker.update_task_status(
            project.project_id,
            task_id,
            TaskStatus.COMPLETED,
            note="Task finished successfully"
        )

        updated = tracker.get_project(project.project_id)
        # Check that the note was added
        found_note = any(
            "Task finished successfully" in n.note
            for n in updated.notes
        )
        assert found_note

    def test_update_task_status_project_not_found(self, tracker):
        """Test updating task in non-existent project raises error."""
        from src.runtime.agents.project_tracker import TaskStatus

        with pytest.raises(ValueError, match="Project not found"):
            tracker.update_task_status("nonexistent", "task1", TaskStatus.COMPLETED)

    def test_update_task_status_task_not_found(self, tracker):
        """Test updating non-existent task raises error."""
        from src.runtime.agents.project_tracker import TaskStatus

        project = tracker.create_project(
            project_name="Test Project",
            description="A test project"
        )

        with pytest.raises(ValueError, match="Task not found"):
            tracker.update_task_status(project.project_id, "nonexistent", TaskStatus.COMPLETED)

    def test_add_note(self, tracker):
        """Test adding a note to a project."""
        project = tracker.create_project(
            project_name="Test Project",
            description="A test project"
        )

        tracker.add_note(
            project.project_id,
            "Test note",
            author="tester",
            category="milestone"
        )

        updated = tracker.get_project(project.project_id)
        found = any(
            n.note == "Test note" and n.author == "tester"
            for n in updated.notes
        )
        assert found

    def test_add_note_project_not_found(self, tracker):
        """Test adding note to non-existent project raises error."""
        with pytest.raises(ValueError, match="Project not found"):
            tracker.add_note("nonexistent", "Test note")

    def test_get_project_summary(self, tracker):
        """Test getting project summary."""
        from src.runtime.agents.project_tracker import TaskStatus

        project = tracker.create_project(
            project_name="Test Project",
            description="A test project"
        )
        tracker.add_task(project.project_id, "Task 1")
        task2_id = tracker.add_task(project.project_id, "Task 2")
        tracker.update_task_status(project.project_id, task2_id, TaskStatus.COMPLETED)

        summary = tracker.get_project_summary(project.project_id)

        assert summary["project_name"] == "Test Project"
        assert summary["task_counts"]["total"] == 2
        assert summary["task_counts"]["todo"] == 1
        assert summary["task_counts"]["completed"] == 1
        assert summary["completion_percentage"] == 50.0

    def test_get_project_summary_not_found(self, tracker):
        """Test getting summary for non-existent project."""
        summary = tracker.get_project_summary("nonexistent")

        assert "error" in summary

    def test_list_projects(self, tracker):
        """Test listing all projects."""
        tracker.create_project("Project 1", "Description 1")
        tracker.create_project("Project 2", "Description 2")

        projects = tracker.list_projects()

        assert len(projects) == 2

    def test_list_projects_filtered_by_status(self, tracker):
        """Test listing projects filtered by status."""
        project1 = tracker.create_project("Project 1", "Description 1")
        tracker.create_project("Project 2", "Description 2")

        # Complete project 1
        project1.status = "completed"
        tracker.update_project(project1)

        active_projects = tracker.list_projects(status="active")
        completed_projects = tracker.list_projects(status="completed")

        assert len(active_projects) == 1
        assert len(completed_projects) == 1

    def test_get_tasks_by_status(self, tracker):
        """Test getting tasks by status."""
        from src.runtime.agents.project_tracker import TaskStatus

        project = tracker.create_project("Test Project", "Description")
        tracker.add_task(project.project_id, "Task 1")
        task2_id = tracker.add_task(project.project_id, "Task 2")
        tracker.update_task_status(project.project_id, task2_id, TaskStatus.COMPLETED)

        todo_tasks = tracker.get_tasks_by_status(project.project_id, TaskStatus.TODO)
        completed_tasks = tracker.get_tasks_by_status(project.project_id, TaskStatus.COMPLETED)

        assert len(todo_tasks) == 1
        assert len(completed_tasks) == 1

    def test_get_tasks_by_status_project_not_found(self, tracker):
        """Test getting tasks from non-existent project returns empty list."""
        from src.runtime.agents.project_tracker import TaskStatus

        tasks = tracker.get_tasks_by_status("nonexistent", TaskStatus.TODO)

        assert tasks == []

    def test_get_next_tasks(self, tracker):
        """Test getting next available tasks."""
        from src.runtime.agents.project_tracker import TaskStatus

        project = tracker.create_project("Test Project", "Description")
        task1_id = tracker.add_task(project.project_id, "Task 1")
        tracker.add_task(project.project_id, "Task 2", dependencies=[task1_id])
        tracker.add_task(project.project_id, "Task 3")  # No dependencies

        next_tasks = tracker.get_next_tasks(project.project_id)

        # Should return Task 1 and Task 3 (no blocking dependencies)
        assert len(next_tasks) == 2
        descriptions = [t.description for t in next_tasks]
        assert "Task 1" in descriptions
        assert "Task 3" in descriptions

    def test_get_next_tasks_with_completed_dependencies(self, tracker):
        """Test getting next tasks after completing dependencies."""
        from src.runtime.agents.project_tracker import TaskStatus

        project = tracker.create_project("Test Project", "Description")
        task1_id = tracker.add_task(project.project_id, "Task 1")
        tracker.add_task(project.project_id, "Task 2", dependencies=[task1_id])

        # Before completing task 1
        next_tasks = tracker.get_next_tasks(project.project_id)
        assert len(next_tasks) == 1
        assert next_tasks[0].description == "Task 1"

        # After completing task 1
        tracker.update_task_status(project.project_id, task1_id, TaskStatus.COMPLETED)
        next_tasks = tracker.get_next_tasks(project.project_id)

        assert len(next_tasks) == 1
        assert next_tasks[0].description == "Task 2"

    def test_get_next_tasks_project_not_found(self, tracker):
        """Test getting next tasks from non-existent project."""
        tasks = tracker.get_next_tasks("nonexistent")

        assert tasks == []
