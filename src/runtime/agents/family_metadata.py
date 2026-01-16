"""
Family Metadata - Tracks metadata for agent family groupings.

This module provides the FamilyMetadata class for managing metadata about
groups of related agents (families) including member tracking and metrics.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class FamilyMetadata:
    """
    Tracks metadata for a family of agents.

    A family represents a group of related agents working together on a task.
    This class tracks the family name, creation time, member agents, and
    aggregate metrics for the family.
    """

    def __init__(self, family_name: str):
        """
        Initialize a new FamilyMetadata instance.

        Args:
            family_name: The name of the family
        """
        self.family_name = family_name
        self.creation_timestamp = datetime.now()
        self.members: List[str] = []
        self.metrics: Dict[str, Any] = {}

    def add_member(self, agent_id: Optional[str]) -> None:
        """
        Add an agent member to the family.

        Args:
            agent_id: The ID of the agent to add
        """
        self.members.append(agent_id)

    def get_members(self) -> List[str]:
        """
        Get the list of family members.

        Returns:
            List of agent IDs in this family
        """
        return self.members

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Update family metrics with new values.

        Existing metrics are updated with new values, and new metrics are added.
        Unchanged metrics remain.

        Args:
            metrics: Dictionary of metrics to update/add
        """
        self.metrics.update(metrics)

    def get_family_info(self) -> Dict[str, Any]:
        """
        Get complete family information as a dictionary.

        Returns:
            Dictionary containing:
            - family_name: Name of the family
            - creation_timestamp: When the family was created
            - members: List of agent IDs
            - metrics: Dictionary of family metrics
        """
        return {
            "family_name": self.family_name,
            "creation_timestamp": self.creation_timestamp,
            "members": self.members,
            "metrics": self.metrics,
        }
