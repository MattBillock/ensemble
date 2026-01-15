"""
Project context management module.

This module provides dataclasses and utilities for managing project-level
context, including notes, decisions, observations, and task tracking.
Enables Executive Directors to maintain awareness about their active projects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid


@dataclass
class ProjectNote:
    """
    A dataclass representing a project note with timestamp and categorization.
    
    ProjectNote captures important project information such as decisions,
    observations, milestones, blockers, and general notes. Each note has a
    timestamp, content, category, and optional reference to a related task.
    
    Attributes:
        timestamp (datetime): The date and time when the note was created.
        content (str): The textual content of the note.
        category (str): The category of the note. Valid categories are:
            'decision', 'observation', 'milestone', 'blocker', 'general'.
        related_task_id (Optional[str]): Optional ID of a related task.
    """
    
    timestamp: datetime
    content: str
    category: str
    related_task_id: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the ProjectNote to a dictionary.
        
        Converts the ProjectNote instance to a dictionary representation
        with the timestamp serialized to ISO 8601 format string.
        
        Returns:
            Dict[str, Any]: A dictionary containing:
                - timestamp (str): ISO 8601 formatted timestamp string
                - content (str): The note content
                - category (str): The note category
                - related_task_id (Optional[str]): The related task ID or None
        
        Example:
            >>> note = ProjectNote(
            ...     timestamp=datetime(2024, 1, 15, 10, 30, 0),
            ...     content="Meeting completed",
            ...     category="milestone",
            ...     related_task_id="TASK-123"
            ... )
            >>> note.to_dict()
            {
                'timestamp': '2024-01-15T10:30:00',
                'content': 'Meeting completed',
                'category': 'milestone',
                'related_task_id': 'TASK-123'
            }
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
            "category": self.category,
            "related_task_id": self.related_task_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectNote":
        """
        Deserialize a ProjectNote from a dictionary.
        
        Creates a ProjectNote instance from a dictionary representation,
        converting the ISO 8601 timestamp string back to a datetime object.
        
        Args:
            data (Dict[str, Any]): A dictionary containing:
                - timestamp (str): ISO 8601 formatted timestamp string
                - content (str): The note content
                - category (str): The note category
                - related_task_id (Optional[str]): The related task ID or None
        
        Returns:
            ProjectNote: A new ProjectNote instance with the deserialized data.
        
        Raises:
            ValueError: If the timestamp string is not in valid ISO 8601 format.
            KeyError: If required fields are missing from the dictionary.
        
        Example:
            >>> data = {
            ...     'timestamp': '2024-01-15T10:30:00',
            ...     'content': 'Meeting completed',
            ...     'category': 'milestone',
            ...     'related_task_id': 'TASK-123'
            ... }
            >>> note = ProjectNote.from_dict(data)
            >>> note.timestamp
            datetime.datetime(2024, 1, 15, 10, 30)
        """
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            content=data["content"],
            category=data.get("category", "general"),
            related_task_id=data.get("related_task_id")
        )


@dataclass
class Task:
    """
    A tracked task within the project.

    Attributes:
        task_id (str): Unique identifier for the task (short UUID)
        description (str): Task description
        priority (str): Priority level - "high", "medium", or "low"
        status (str): Current status - "pending", "in_progress", "completed", or "blocked"
        created_at (datetime): When the task was created
        completed_at (Optional[datetime]): When the task was completed
        outcome (Optional[str]): Notes about how the task was completed
    """

    task_id: str
    description: str
    priority: str = "medium"
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    outcome: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize task to dictionary."""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "outcome": self.outcome,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Deserialize task from dictionary."""
        return cls(
            task_id=data["task_id"],
            description=data["description"],
            priority=data.get("priority", "medium"),
            status=data.get("status", "pending"),
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_at=(
                datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
            ),
            outcome=data.get("outcome"),
        )


@dataclass
class ProjectContext:
    """
    Encapsulates project awareness state for an Executive Director.

    Maintains project identity, proto-history notes, and task tracking.
    Provides methods for managing notes and tasks throughout the project lifecycle.

    Attributes:
        project_name (str): Descriptive project name
        project_description (str): Brief description of what's being built
        created_at (datetime): When the project started
        notes (List[ProjectNote]): Chronological notes/observations
        completed_tasks (List[Task]): Tasks that have been completed
        remaining_tasks (List[Task]): Tasks still to be done
    """

    project_name: str
    project_description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    notes: List[ProjectNote] = field(default_factory=list)
    completed_tasks: List[Task] = field(default_factory=list)
    remaining_tasks: List[Task] = field(default_factory=list)

    def add_note(
        self, content: str, category: str = "general", related_task_id: Optional[str] = None
    ) -> ProjectNote:
        """
        Add a new note to the project's proto-history.

        Args:
            content: The note content
            category: One of "decision", "observation", "milestone", "blocker", "general"
            related_task_id: Optional task ID this note relates to

        Returns:
            The created ProjectNote
        """
        note = ProjectNote(
            timestamp=datetime.now(),
            content=content,
            category=category,
            related_task_id=related_task_id,
        )
        self.notes.append(note)
        return note

    def add_task(self, description: str, priority: str = "medium") -> Task:
        """
        Add a new task to the remaining tasks list.

        Args:
            description: Task description
            priority: One of "high", "medium", "low"

        Returns:
            The created Task
        """
        task = Task(
            task_id=str(uuid.uuid4())[:8],
            description=description,
            priority=priority,
            status="pending",
            created_at=datetime.now(),
        )
        self.remaining_tasks.append(task)
        return task

    def mark_task_complete(self, task_id: str, outcome: Optional[str] = None) -> Optional[Task]:
        """
        Mark a task as completed and move it to completed_tasks.

        Args:
            task_id: The ID of the task to complete
            outcome: Optional notes about how the task was completed

        Returns:
            The completed Task, or None if not found
        """
        for i, task in enumerate(self.remaining_tasks):
            if task.task_id == task_id:
                task.status = "completed"
                task.completed_at = datetime.now()
                task.outcome = outcome
                self.completed_tasks.append(task)
                self.remaining_tasks.pop(i)
                return task
        return None

    def update_task_status(self, task_id: str, status: str) -> Optional[Task]:
        """
        Update the status of a task.

        Args:
            task_id: The ID of the task to update
            status: New status ("pending", "in_progress", "completed", "blocked")

        Returns:
            The updated Task, or None if not found
        """
        for task in self.remaining_tasks:
            if task.task_id == task_id:
                if status == "completed":
                    return self.mark_task_complete(task_id)
                task.status = status
                return task
        return None

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID from either remaining or completed tasks."""
        for task in self.remaining_tasks + self.completed_tasks:
            if task.task_id == task_id:
                return task
        return None

    def get_notes_by_category(self, category: str) -> List[ProjectNote]:
        """Get all notes of a specific category."""
        return [note for note in self.notes if note.category == category]

    def get_recent_notes(self, count: int = 5) -> List[ProjectNote]:
        """Get the most recent notes (newest first)."""
        return sorted(self.notes, key=lambda n: n.timestamp, reverse=True)[:count]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the project context."""
        return {
            "project_name": self.project_name,
            "project_description": self.project_description,
            "created_at": self.created_at.isoformat(),
            "total_notes": len(self.notes),
            "completed_tasks_count": len(self.completed_tasks),
            "remaining_tasks_count": len(self.remaining_tasks),
            "high_priority_remaining": sum(
                1 for t in self.remaining_tasks if t.priority == "high"
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize project context to dictionary."""
        return {
            "project_name": self.project_name,
            "project_description": self.project_description,
            "created_at": self.created_at.isoformat(),
            "notes": [note.to_dict() for note in self.notes],
            "completed_tasks": [task.to_dict() for task in self.completed_tasks],
            "remaining_tasks": [task.to_dict() for task in self.remaining_tasks],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectContext":
        """Deserialize project context from dictionary."""
        return cls(
            project_name=data["project_name"],
            project_description=data.get("project_description", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            notes=[ProjectNote.from_dict(n) for n in data.get("notes", [])],
            completed_tasks=[Task.from_dict(t) for t in data.get("completed_tasks", [])],
            remaining_tasks=[Task.from_dict(t) for t in data.get("remaining_tasks", [])],
        )

    @classmethod
    def create_from_vision(cls, user_vision: str) -> "ProjectContext":
        """
        Create a new ProjectContext from a user vision statement.

        Extracts a project name from the first sentence or uses a default.

        Args:
            user_vision: The user's problem description

        Returns:
            A new ProjectContext
        """
        first_sentence = user_vision.split(".")[0].strip()
        if len(first_sentence) > 60:
            project_name = first_sentence[:60] + "..."
        else:
            project_name = first_sentence if first_sentence else "Unnamed Project"

        return cls(
            project_name=project_name,
            project_description=user_vision[:500] if len(user_vision) > 500 else user_vision,
            created_at=datetime.now(),
        )
