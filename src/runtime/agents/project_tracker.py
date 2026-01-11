"""Project tracking system for Executive Director agents."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Status of a task."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass
class ProjectTask:
    """A task within a project."""
    task_id: str
    description: str
    status: TaskStatus
    assigned_to: Optional[str] = None  # Agent type or name
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    notes: List[str] = None
    dependencies: List[str] = None  # task_ids this depends on

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if self.notes is None:
            self.notes = []
        if self.dependencies is None:
            self.dependencies = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['status'] = self.status.value
        return result


@dataclass
class ProjectNote:
    """A note or history entry for the project."""
    timestamp: str
    author: str  # Agent ID or type
    note: str
    category: str = "general"  # general, decision, milestone, issue

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ProjectState:
    """Complete state of a project."""
    project_id: str
    project_name: str
    description: str
    status: str  # active, paused, completed, cancelled
    created_at: str
    updated_at: str

    # Task tracking
    tasks: Dict[str, ProjectTask]

    # History/notes
    notes: List[ProjectNote]

    # Metadata
    request_id: Optional[str] = None
    budget_tier: str = "balanced"
    output_directory: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "request_id": self.request_id,
            "budget_tier": self.budget_tier,
            "output_directory": self.output_directory,
            "tasks": {tid: task.to_dict() for tid, task in self.tasks.items()},
            "notes": [note.to_dict() for note in self.notes]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectState":
        """Create from dictionary."""
        tasks = {
            tid: ProjectTask(
                task_id=task_data["task_id"],
                description=task_data["description"],
                status=TaskStatus(task_data["status"]),
                assigned_to=task_data.get("assigned_to"),
                created_at=task_data["created_at"],
                started_at=task_data.get("started_at"),
                completed_at=task_data.get("completed_at"),
                notes=task_data.get("notes", []),
                dependencies=task_data.get("dependencies", [])
            )
            for tid, task_data in data.get("tasks", {}).items()
        }

        notes = [
            ProjectNote(
                timestamp=note_data["timestamp"],
                author=note_data["author"],
                note=note_data["note"],
                category=note_data.get("category", "general")
            )
            for note_data in data.get("notes", [])
        ]

        return cls(
            project_id=data["project_id"],
            project_name=data["project_name"],
            description=data["description"],
            status=data["status"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            tasks=tasks,
            notes=notes,
            request_id=data.get("request_id"),
            budget_tier=data.get("budget_tier", "balanced"),
            output_directory=data.get("output_directory")
        )


class ProjectTracker:
    """Tracks project state for Executive Director agents."""

    def __init__(self, projects_dir: Optional[Path] = None):
        """
        Initialize project tracker.

        Args:
            projects_dir: Directory to store project state files.
                         Defaults to ~/.ensemble/projects/
        """
        if projects_dir is None:
            projects_dir = Path.home() / ".ensemble" / "projects"

        self.projects_dir = Path(projects_dir)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache of active projects
        self._cache: Dict[str, ProjectState] = {}

    def create_project(
        self,
        project_name: str,
        description: str,
        request_id: Optional[str] = None,
        budget_tier: str = "balanced",
        output_directory: Optional[str] = None
    ) -> ProjectState:
        """
        Create a new project.

        Args:
            project_name: Descriptive name for the project
            description: Project description/vision
            request_id: Associated request ID
            budget_tier: Budget tier for the project
            output_directory: Where to create artifacts

        Returns:
            Created ProjectState
        """
        import uuid

        project_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        project = ProjectState(
            project_id=project_id,
            project_name=project_name,
            description=description,
            status="active",
            created_at=now,
            updated_at=now,
            tasks={},
            notes=[],
            request_id=request_id,
            budget_tier=budget_tier,
            output_directory=output_directory
        )

        # Add initial note
        project.notes.append(ProjectNote(
            timestamp=now,
            author="executive_director",
            note=f"Project '{project_name}' created",
            category="milestone"
        ))

        self._save_project(project)
        self._cache[project_id] = project

        logger.info(f"Created project: {project_name} (ID: {project_id})")

        return project

    def get_project(self, project_id: str) -> Optional[ProjectState]:
        """Get a project by ID."""
        # Check cache first
        if project_id in self._cache:
            return self._cache[project_id]

        # Load from disk
        project = self._load_project(project_id)
        if project:
            self._cache[project_id] = project

        return project

    def update_project(self, project: ProjectState) -> None:
        """Update a project's state."""
        project.updated_at = datetime.now().isoformat()
        self._save_project(project)
        self._cache[project.project_id] = project

    def add_task(
        self,
        project_id: str,
        description: str,
        assigned_to: Optional[str] = None,
        dependencies: Optional[List[str]] = None
    ) -> str:
        """
        Add a task to a project.

        Args:
            project_id: Project to add task to
            description: Task description
            assigned_to: Agent type or name
            dependencies: List of task IDs this depends on

        Returns:
            Created task ID
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        import uuid
        task_id = str(uuid.uuid4())[:8]

        task = ProjectTask(
            task_id=task_id,
            description=description,
            status=TaskStatus.TODO,
            assigned_to=assigned_to,
            dependencies=dependencies or []
        )

        project.tasks[task_id] = task
        project.notes.append(ProjectNote(
            timestamp=datetime.now().isoformat(),
            author="executive_director",
            note=f"Added task: {description}",
            category="general"
        ))

        self.update_project(project)

        logger.info(f"Added task to project {project_id}: {description}")

        return task_id

    def update_task_status(
        self,
        project_id: str,
        task_id: str,
        status: TaskStatus,
        note: Optional[str] = None
    ) -> None:
        """Update a task's status."""
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        if task_id not in project.tasks:
            raise ValueError(f"Task not found: {task_id}")

        task = project.tasks[task_id]
        old_status = task.status
        task.status = status

        now = datetime.now().isoformat()

        if status == TaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = now
        elif status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = now

        # Add note about status change
        status_note = f"Task '{task.description}' status: {old_status.value} → {status.value}"
        if note:
            status_note += f" - {note}"

        project.notes.append(ProjectNote(
            timestamp=now,
            author="executive_director",
            note=status_note,
            category="general"
        ))

        self.update_project(project)

        logger.info(f"Updated task {task_id} status: {old_status.value} → {status.value}")

    def add_note(
        self,
        project_id: str,
        note: str,
        author: str = "executive_director",
        category: str = "general"
    ) -> None:
        """Add a note to the project."""
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        project.notes.append(ProjectNote(
            timestamp=datetime.now().isoformat(),
            author=author,
            note=note,
            category=category
        ))

        self.update_project(project)

        logger.info(f"Added note to project {project_id}: {note}")

    def get_project_summary(self, project_id: str) -> Dict[str, Any]:
        """Get a summary of the project status."""
        project = self.get_project(project_id)
        if not project:
            return {"error": "Project not found"}

        task_counts = {
            "total": len(project.tasks),
            "todo": sum(1 for t in project.tasks.values() if t.status == TaskStatus.TODO),
            "in_progress": sum(1 for t in project.tasks.values() if t.status == TaskStatus.IN_PROGRESS),
            "completed": sum(1 for t in project.tasks.values() if t.status == TaskStatus.COMPLETED),
            "blocked": sum(1 for t in project.tasks.values() if t.status == TaskStatus.BLOCKED),
            "cancelled": sum(1 for t in project.tasks.values() if t.status == TaskStatus.CANCELLED)
        }

        # Calculate completion percentage
        completion_pct = 0.0
        if task_counts["total"] > 0:
            completion_pct = (task_counts["completed"] / task_counts["total"]) * 100

        # Get recent notes
        recent_notes = sorted(project.notes, key=lambda n: n.timestamp, reverse=True)[:10]

        return {
            "project_id": project.project_id,
            "project_name": project.project_name,
            "description": project.description,
            "status": project.status,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "task_counts": task_counts,
            "completion_percentage": completion_pct,
            "recent_notes": [n.to_dict() for n in recent_notes],
            "output_directory": project.output_directory
        }

    def list_projects(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all projects, optionally filtered by status."""
        projects = []

        for project_file in self.projects_dir.glob("*.json"):
            try:
                project = self._load_project(project_file.stem)
                if project and (status is None or project.status == status):
                    projects.append(self.get_project_summary(project.project_id))
            except Exception as e:
                logger.error(f"Error loading project {project_file}: {e}")

        # Sort by updated_at descending
        projects.sort(key=lambda p: p.get("updated_at", ""), reverse=True)

        return projects

    def _save_project(self, project: ProjectState) -> None:
        """Save project to disk."""
        project_file = self.projects_dir / f"{project.project_id}.json"

        with open(project_file, 'w') as f:
            json.dump(project.to_dict(), f, indent=2)

        logger.debug(f"Saved project {project.project_id} to {project_file}")

    def _load_project(self, project_id: str) -> Optional[ProjectState]:
        """Load project from disk."""
        project_file = self.projects_dir / f"{project_id}.json"

        if not project_file.exists():
            return None

        try:
            with open(project_file, 'r') as f:
                data = json.load(f)

            return ProjectState.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading project {project_id}: {e}")
            return None

    def get_tasks_by_status(
        self,
        project_id: str,
        status: TaskStatus
    ) -> List[ProjectTask]:
        """Get all tasks with a specific status."""
        project = self.get_project(project_id)
        if not project:
            return []

        return [
            task for task in project.tasks.values()
            if task.status == status
        ]

    def get_next_tasks(self, project_id: str) -> List[ProjectTask]:
        """
        Get next tasks that can be worked on (no blocking dependencies).

        Returns tasks that are:
        - Status TODO
        - All dependencies are COMPLETED
        """
        project = self.get_project(project_id)
        if not project:
            return []

        next_tasks = []

        for task in project.tasks.values():
            if task.status != TaskStatus.TODO:
                continue

            # Check if all dependencies are completed
            can_start = True
            for dep_id in task.dependencies:
                if dep_id not in project.tasks:
                    logger.warning(f"Task {task.task_id} depends on unknown task {dep_id}")
                    can_start = False
                    break

                if project.tasks[dep_id].status != TaskStatus.COMPLETED:
                    can_start = False
                    break

            if can_start:
                next_tasks.append(task)

        return next_tasks
