"""
Unit tests for ProjectNote dataclass.

This module contains comprehensive tests for the ProjectNote dataclass
including field validation, serialization, and deserialization.
"""

import pytest
from datetime import datetime
from src.runtime.agents.project_context import ProjectNote


class TestProjectNote:
    """Test suite for ProjectNote dataclass."""

    def test_create_project_note_with_all_fields(self):
        """
        Test creating a ProjectNote with all fields populated including related_task_id.
        
        Verifies that:
        - All fields are correctly assigned
        - related_task_id is properly stored when provided
        - All attributes are accessible
        """
        # Arrange
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        content = "Project kickoff meeting completed"
        category = "milestone"
        related_task_id = "TASK-123"
        
        # Act
        note = ProjectNote(
            timestamp=timestamp,
            content=content,
            category=category,
            related_task_id=related_task_id
        )
        
        # Assert
        assert note.timestamp == timestamp, "Timestamp should match the provided value"
        assert note.content == content, "Content should match the provided value"
        assert note.category == category, "Category should match the provided value"
        assert note.related_task_id == related_task_id, "Related task ID should match the provided value"

    def test_create_project_note_with_optional_none(self):
        """
        Test creating a ProjectNote with related_task_id as None.
        
        Verifies that:
        - ProjectNote can be created without related_task_id
        - related_task_id defaults to or accepts None
        - Other required fields are properly set
        """
        # Arrange
        timestamp = datetime(2024, 1, 15, 14, 45, 0)
        content = "General observation about project progress"
        category = "observation"
        
        # Act
        note = ProjectNote(
            timestamp=timestamp,
            content=content,
            category=category,
            related_task_id=None
        )
        
        # Assert
        assert note.timestamp == timestamp, "Timestamp should match the provided value"
        assert note.content == content, "Content should match the provided value"
        assert note.category == category, "Category should match the provided value"
        assert note.related_task_id is None, "Related task ID should be None"

    def test_to_dict_serialization(self):
        """
        Test to_dict() serializes correctly with ISO 8601 timestamp format.
        
        Verifies that:
        - to_dict() returns a dictionary
        - timestamp is converted to ISO 8601 string format (e.g., '2024-01-15T10:30:00')
        - All other fields are properly serialized
        - Dictionary contains all expected keys
        """
        # Arrange
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        content = "Critical decision made"
        category = "decision"
        related_task_id = "TASK-456"
        
        note = ProjectNote(
            timestamp=timestamp,
            content=content,
            category=category,
            related_task_id=related_task_id
        )
        
        # Act
        result = note.to_dict()
        
        # Assert
        assert isinstance(result, dict), "to_dict() should return a dictionary"
        assert result["timestamp"] == "2024-01-15T10:30:00", "Timestamp should be in ISO 8601 format"
        assert result["content"] == content, "Content should be serialized correctly"
        assert result["category"] == category, "Category should be serialized correctly"
        assert result["related_task_id"] == related_task_id, "Related task ID should be serialized correctly"
        assert len(result) == 4, "Dictionary should contain exactly 4 keys"

    def test_from_dict_deserialization(self):
        """
        Test from_dict() deserializes correctly from a dictionary.
        
        Verifies that:
        - from_dict() is a class method
        - Dictionary with ISO 8601 timestamp string is correctly deserialized
        - All fields are properly converted to their respective types
        - Resulting ProjectNote instance has correct attribute values
        """
        # Arrange
        data = {
            "timestamp": "2024-01-15T16:20:00",
            "content": "Blocker identified in authentication module",
            "category": "blocker",
            "related_task_id": "TASK-789"
        }
        
        # Act
        note = ProjectNote.from_dict(data)
        
        # Assert
        assert isinstance(note, ProjectNote), "from_dict() should return a ProjectNote instance"
        assert note.timestamp == datetime(2024, 1, 15, 16, 20, 0), "Timestamp should be deserialized to datetime object"
        assert note.content == data["content"], "Content should be deserialized correctly"
        assert note.category == data["category"], "Category should be deserialized correctly"
        assert note.related_task_id == data["related_task_id"], "Related task ID should be deserialized correctly"

    def test_round_trip_serialization(self):
        """
        Test that ProjectNote -> to_dict() -> from_dict() -> to_dict() produces identical results.
        
        Verifies that:
        - Serialization and deserialization are inverse operations
        - No data is lost in the round-trip conversion
        - The final dictionary matches the intermediate dictionary
        - This ensures data integrity through save/load cycles
        """
        # Arrange
        original_timestamp = datetime(2024, 1, 15, 9, 15, 30)
        original_note = ProjectNote(
            timestamp=original_timestamp,
            content="General note for testing round-trip",
            category="general",
            related_task_id="TASK-999"
        )
        
        # Act
        first_dict = original_note.to_dict()
        reconstructed_note = ProjectNote.from_dict(first_dict)
        second_dict = reconstructed_note.to_dict()
        
        # Assert
        assert first_dict == second_dict, "Round-trip serialization should produce identical dictionaries"
        assert first_dict["timestamp"] == "2024-01-15T09:15:30", "Timestamp should maintain ISO 8601 format"
        assert first_dict["content"] == second_dict["content"], "Content should be preserved"
        assert first_dict["category"] == second_dict["category"], "Category should be preserved"
        assert first_dict["related_task_id"] == second_dict["related_task_id"], "Related task ID should be preserved"
        
        # Additional verification: reconstructed note should have same values as original
        assert reconstructed_note.timestamp == original_timestamp, "Reconstructed timestamp should match original"
        assert reconstructed_note.content == original_note.content, "Reconstructed content should match original"
        assert reconstructed_note.category == original_note.category, "Reconstructed category should match original"
        assert reconstructed_note.related_task_id == original_note.related_task_id, "Reconstructed related_task_id should match original"
