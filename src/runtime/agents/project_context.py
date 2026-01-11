"""
Project context management module.

This module provides dataclasses and utilities for managing project-level
context, including notes, decisions, and observations.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


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
            category=data["category"],
            related_task_id=data["related_task_id"]
        )
