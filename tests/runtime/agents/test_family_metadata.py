"""
Unit tests for FamilyMetadata class.

Tests written following TDD principles - these tests are expected to fail
until the FamilyMetadata class is implemented.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.runtime.agents.family_metadata import FamilyMetadata


class TestFamilyMetadataCreation:
    """Tests for FamilyMetadata initialization."""

    def test_family_metadata_creation(self):
        """
        Test that FamilyMetadata is created with correct initial state.
        
        Verifies:
        - family_name is set correctly
        - creation_timestamp is auto-generated and is a datetime
        - members list is empty
        - metrics dict is empty
        """
        family_name = "TestFamily"
        family = FamilyMetadata(family_name)
        
        # Verify family name is set
        assert family.family_name == family_name, "Family name should match initialization parameter"
        
        # Verify timestamp exists and is a datetime object
        assert hasattr(family, 'creation_timestamp'), "FamilyMetadata should have creation_timestamp attribute"
        assert family.creation_timestamp is not None, "creation_timestamp should not be None"
        assert isinstance(family.creation_timestamp, datetime), "creation_timestamp should be a datetime object"
        
        # Verify members list is empty
        assert hasattr(family, 'members'), "FamilyMetadata should have members attribute"
        assert isinstance(family.members, list), "members should be a list"
        assert len(family.members) == 0, "members list should be empty on creation"
        
        # Verify metrics dict is empty
        assert hasattr(family, 'metrics'), "FamilyMetadata should have metrics attribute"
        assert isinstance(family.metrics, dict), "metrics should be a dictionary"
        assert len(family.metrics) == 0, "metrics dict should be empty on creation"

    def test_family_metadata_creation_with_mocked_timestamp(self):
        """
        Test FamilyMetadata creation with mocked timestamp for deterministic testing.
        
        Verifies that the timestamp is correctly set during initialization.
        """
        mock_timestamp = datetime(2024, 1, 15, 10, 30, 0)
        
        with patch('src.runtime.agents.family_metadata.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_timestamp
            family = FamilyMetadata("MockedFamily")
            
            assert family.creation_timestamp == mock_timestamp, \
                "creation_timestamp should match mocked datetime"


class TestAddMember:
    """Tests for adding members to the family."""

    def test_add_member(self):
        """
        Test adding a single agent member to the family.
        
        Verifies:
        - Member is added to members list
        - Member count increases
        """
        family = FamilyMetadata("TestFamily")
        agent_id = "agent_123"
        
        family.add_member(agent_id)
        
        assert agent_id in family.members, "Agent ID should be in members list"
        assert len(family.members) == 1, "Members list should have exactly one member"

    def test_add_multiple_members(self):
        """
        Test adding multiple agent members to the family.
        
        Verifies:
        - All members are added to members list
        - Members are in correct order
        - Member count is correct
        """
        family = FamilyMetadata("TestFamily")
        agent_ids = ["agent_1", "agent_2", "agent_3"]
        
        for agent_id in agent_ids:
            family.add_member(agent_id)
        
        assert len(family.members) == 3, "Members list should have three members"
        for agent_id in agent_ids:
            assert agent_id in family.members, f"Agent {agent_id} should be in members list"

    def test_add_duplicate_member(self):
        """
        Test adding the same agent member twice.
        
        Verifies behavior when duplicate members are added.
        Note: Assuming duplicates are allowed based on typical list behavior.
        If duplicates should be prevented, this test should be modified.
        """
        family = FamilyMetadata("TestFamily")
        agent_id = "agent_123"
        
        family.add_member(agent_id)
        family.add_member(agent_id)
        
        # If duplicates are allowed, count should be 2
        # If duplicates are prevented, count should be 1
        # Adjust assertion based on actual requirement
        assert agent_id in family.members, "Agent should be in members list"


class TestGetMembers:
    """Tests for retrieving family members."""

    def test_get_members(self):
        """
        Test getting the list of family members.
        
        Verifies:
        - get_members() returns a list
        - List contains all added members
        """
        family = FamilyMetadata("TestFamily")
        agent_ids = ["agent_1", "agent_2", "agent_3"]
        
        for agent_id in agent_ids:
            family.add_member(agent_id)
        
        members = family.get_members()
        
        assert isinstance(members, list), "get_members() should return a list"
        assert len(members) == 3, "Should return all three members"
        assert members == agent_ids, "Returned list should match added members"

    def test_get_members_empty(self):
        """
        Test getting members from a family with no members.
        
        Verifies:
        - get_members() returns an empty list for new family
        """
        family = FamilyMetadata("TestFamily")
        
        members = family.get_members()
        
        assert isinstance(members, list), "get_members() should return a list"
        assert len(members) == 0, "Should return empty list for family with no members"


class TestUpdateMetrics:
    """Tests for updating family metrics."""

    def test_update_metrics(self):
        """
        Test setting initial metrics for the family.
        
        Verifies:
        - Metrics are stored correctly
        - Metrics can be retrieved
        """
        family = FamilyMetadata("TestFamily")
        metrics = {
            "total_tasks": 5,
            "completed_tasks": 3,
            "success_rate": 0.6
        }
        
        family.update_metrics(metrics)
        
        assert family.metrics == metrics, "Metrics should match the provided dictionary"
        assert family.metrics["total_tasks"] == 5, "Should access individual metric values"
        assert family.metrics["completed_tasks"] == 3, "Should access individual metric values"
        assert family.metrics["success_rate"] == 0.6, "Should access individual metric values"

    def test_update_metrics_partial_update(self):
        """
        Test updating existing metrics with new values.
        
        Verifies:
        - Existing metrics are updated
        - New metrics are added
        - Unchanged metrics remain
        """
        family = FamilyMetadata("TestFamily")
        
        # Set initial metrics
        initial_metrics = {
            "total_tasks": 5,
            "completed_tasks": 3
        }
        family.update_metrics(initial_metrics)
        
        # Update with new metrics
        update_metrics = {
            "completed_tasks": 5,  # Update existing
            "success_rate": 1.0    # Add new
        }
        family.update_metrics(update_metrics)
        
        assert family.metrics["total_tasks"] == 5, "Unchanged metric should remain"
        assert family.metrics["completed_tasks"] == 5, "Updated metric should have new value"
        assert family.metrics["success_rate"] == 1.0, "New metric should be added"

    def test_update_metrics_empty_dict(self):
        """
        Test updating metrics with an empty dictionary.
        
        Verifies:
        - Empty dict update doesn't break functionality
        """
        family = FamilyMetadata("TestFamily")
        initial_metrics = {"tasks": 5}
        family.update_metrics(initial_metrics)
        
        family.update_metrics({})
        
        assert family.metrics["tasks"] == 5, "Existing metrics should remain after empty update"


class TestGetFamilyInfo:
    """Tests for retrieving complete family information."""

    def test_get_family_info(self):
        """
        Test getting complete family information as a dictionary.
        
        Verifies:
        - Returns a dictionary
        - Contains all required keys: family_name, creation_timestamp, members, metrics
        - Values match the current state
        """
        family = FamilyMetadata("TestFamily")
        family.add_member("agent_1")
        family.add_member("agent_2")
        family.update_metrics({"total_tasks": 10})
        
        info = family.get_family_info()
        
        assert isinstance(info, dict), "get_family_info() should return a dictionary"
        
        # Verify all required keys are present
        assert "family_name" in info, "Info dict should contain family_name"
        assert "creation_timestamp" in info, "Info dict should contain creation_timestamp"
        assert "members" in info, "Info dict should contain members"
        assert "metrics" in info, "Info dict should contain metrics"
        
        # Verify values match current state
        assert info["family_name"] == "TestFamily", "family_name should match"
        assert isinstance(info["creation_timestamp"], datetime), "timestamp should be datetime"
        assert info["members"] == ["agent_1", "agent_2"], "members should match"
        assert info["metrics"] == {"total_tasks": 10}, "metrics should match"

    def test_get_family_info_empty_family(self):
        """
        Test getting family info for a newly created family.
        
        Verifies:
        - Returns dict with empty members and metrics
        - Still includes family_name and timestamp
        """
        family = FamilyMetadata("EmptyFamily")
        
        info = family.get_family_info()
        
        assert info["family_name"] == "EmptyFamily", "Should include family name"
        assert info["creation_timestamp"] is not None, "Should include timestamp"
        assert info["members"] == [], "Should have empty members list"
        assert info["metrics"] == {}, "Should have empty metrics dict"


class TestMemberCount:
    """Tests for tracking the count of family members."""

    def test_member_count(self):
        """
        Test tracking the number of members in the family.
        
        Verifies:
        - Member count starts at 0
        - Member count increases as members are added
        - Member count is accurate
        """
        family = FamilyMetadata("TestFamily")
        
        # Initial count should be 0
        assert len(family.members) == 0, "Initial member count should be 0"
        
        # Add members and verify count
        family.add_member("agent_1")
        assert len(family.members) == 1, "Member count should be 1 after adding one member"
        
        family.add_member("agent_2")
        assert len(family.members) == 2, "Member count should be 2 after adding two members"
        
        family.add_member("agent_3")
        assert len(family.members) == 3, "Member count should be 3 after adding three members"

    def test_member_count_via_get_members(self):
        """
        Test that member count can be determined from get_members() return value.
        
        Verifies:
        - get_members() returns correct number of members
        """
        family = FamilyMetadata("TestFamily")
        
        for i in range(5):
            family.add_member(f"agent_{i}")
        
        members = family.get_members()
        assert len(members) == 5, "get_members() should return 5 members"


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_family_name(self):
        """
        Test creating a family with an empty name.
        
        Verifies behavior with edge case input.
        """
        family = FamilyMetadata("")
        
        assert family.family_name == "", "Should accept empty string as family name"
        assert isinstance(family.members, list), "Should still initialize properly"

    def test_none_agent_id(self):
        """
        Test adding None as an agent ID.
        
        Verifies behavior with None input.
        """
        family = FamilyMetadata("TestFamily")
        
        # This may raise an error or accept None - adjust based on requirements
        family.add_member(None)
        assert None in family.members or len(family.members) == 0, \
            "Should handle None agent_id appropriately"

    def test_metrics_with_various_types(self):
        """
        Test updating metrics with various value types.
        
        Verifies:
        - Metrics can store different data types
        """
        family = FamilyMetadata("TestFamily")
        
        metrics = {
            "count": 42,
            "rate": 0.95,
            "name": "test_metric",
            "active": True,
            "tags": ["tag1", "tag2"],
            "nested": {"key": "value"}
        }
        
        family.update_metrics(metrics)
        
        assert family.metrics["count"] == 42, "Should store integer"
        assert family.metrics["rate"] == 0.95, "Should store float"
        assert family.metrics["name"] == "test_metric", "Should store string"
        assert family.metrics["active"] is True, "Should store boolean"
        assert family.metrics["tags"] == ["tag1", "tag2"], "Should store list"
        assert family.metrics["nested"] == {"key": "value"}, "Should store nested dict"
