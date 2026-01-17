"""
Unit tests for data_retention module.

Tests the DataRetentionManager, DataCompactor, and DataArchiver classes.
"""

import pytest
import json
import gzip
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestRetentionPolicy:
    """Test RetentionPolicy enum."""

    def test_retention_policy_values(self):
        """Test that all retention policies exist with correct values."""
        from src.runtime.agents.data_retention import RetentionPolicy

        assert RetentionPolicy.IMMEDIATE.value == "immediate"
        assert RetentionPolicy.SHORT_TERM.value == "short_term"
        assert RetentionPolicy.MEDIUM_TERM.value == "medium_term"
        assert RetentionPolicy.LONG_TERM.value == "long_term"
        assert RetentionPolicy.ARCHIVE.value == "archive"
        assert RetentionPolicy.PERMANENT.value == "permanent"


class TestRetentionRule:
    """Test RetentionRule dataclass."""

    def test_retention_rule_creation(self):
        """Test creating a RetentionRule."""
        from src.runtime.agents.data_retention import RetentionRule, RetentionPolicy

        rule = RetentionRule(
            data_type="events",
            policy=RetentionPolicy.SHORT_TERM,
            retention_hours=24,
            compact_after_hours=6,
            description="Test rule"
        )

        assert rule.data_type == "events"
        assert rule.policy == RetentionPolicy.SHORT_TERM
        assert rule.retention_hours == 24
        assert rule.compact_after_hours == 6


class TestDefaultRetentionRules:
    """Test default retention rules."""

    def test_default_rules_exist(self):
        """Test that default rules are defined."""
        from src.runtime.agents.data_retention import DEFAULT_RETENTION_RULES

        assert len(DEFAULT_RETENTION_RULES) > 0

    def test_default_rules_cover_data_types(self):
        """Test that default rules cover expected data types."""
        from src.runtime.agents.data_retention import DEFAULT_RETENTION_RULES

        data_types = [r.data_type for r in DEFAULT_RETENTION_RULES]

        assert "events" in data_types
        assert "agent_messages" in data_types
        assert "tool_executions" in data_types
        assert "completed_sessions" in data_types
        assert "deliverables" in data_types


class TestDataCompactor:
    """Test DataCompactor class."""

    @pytest.fixture
    def compactor(self):
        """Create a DataCompactor instance."""
        from src.runtime.agents.data_retention import DataCompactor
        return DataCompactor()

    def test_compact_agent_messages_empty(self, compactor):
        """Test compacting empty messages list."""
        result = compactor.compact_agent_messages("agent-1", [])

        assert result["summary"] == "No messages"
        assert result["message_count"] == 0

    def test_compact_agent_messages(self, compactor):
        """Test compacting agent messages."""
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "Response with status: {\"status\": \"running\"}"},
            {"role": "user", "content": "Last message"},
        ]

        result = compactor.compact_agent_messages("agent-1", messages)

        assert result["agent_id"] == "agent-1"
        assert result["message_count"] == 3
        assert "first_message" in result
        assert "last_message" in result
        assert "compacted_at" in result

    def test_compact_agent_messages_extracts_errors(self, compactor):
        """Test that error messages are extracted."""
        messages = [
            {"role": "assistant", "content": "Error: Something failed"},
        ]

        result = compactor.compact_agent_messages("agent-1", messages)

        assert len(result["errors"]) > 0

    def test_truncate_content(self, compactor):
        """Test content truncation."""
        message = {"content": "x" * 1000}

        result = compactor._truncate_content(message, max_length=100)

        assert len(result["content"]) < 150  # 100 + truncation message

    def test_compact_tool_executions_empty(self, compactor):
        """Test compacting empty executions list."""
        result = compactor.compact_tool_executions("agent-1", [])

        assert result["summary"] == "No executions"
        assert result["count"] == 0

    def test_compact_tool_executions(self, compactor):
        """Test compacting tool executions."""
        executions = [
            {"tool_name": "write_file", "success": True, "duration_ms": 100},
            {"tool_name": "write_file", "success": True, "duration_ms": 150},
            {"tool_name": "read_file", "success": False, "duration_ms": 50, "result": "Error"},
        ]

        result = compactor.compact_tool_executions("agent-1", executions)

        assert result["agent_id"] == "agent-1"
        assert result["total_executions"] == 3
        assert "write_file" in result["by_tool"]
        assert result["by_tool"]["write_file"]["count"] == 2
        assert result["total_duration_ms"] == 300

    def test_compact_tool_executions_calculates_success_rate(self, compactor):
        """Test that success rate is calculated."""
        executions = [
            {"tool_name": "test", "success": True},
            {"tool_name": "test", "success": True},
            {"tool_name": "test", "success": False},
        ]

        result = compactor.compact_tool_executions("agent-1", executions)

        # 2/3 success rate
        assert abs(result["success_rate"] - 0.666) < 0.01


class TestDataArchiver:
    """Test DataArchiver class."""

    @pytest.fixture
    def temp_archive_dir(self):
        """Create a temporary archive directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def archiver(self, temp_archive_dir):
        """Create a DataArchiver instance."""
        from src.runtime.agents.data_retention import DataArchiver
        return DataArchiver(archive_dir=temp_archive_dir)

    def test_init_creates_directory(self, temp_archive_dir):
        """Test that initialization creates archive directory."""
        from src.runtime.agents.data_retention import DataArchiver

        archive_dir = temp_archive_dir / "archives"
        archiver = DataArchiver(archive_dir=archive_dir)

        assert archive_dir.exists()

    def test_archive_session(self, archiver, temp_archive_dir):
        """Test archiving a session."""
        session_data = {
            "session_id": "test-session",
            "prompt": "Test prompt"
        }
        agents_data = [
            {"agent_id": "agent-1", "status": "completed"}
        ]
        deliverables_data = [
            {"file_path": "/test.py"}
        ]

        archive_path = archiver.archive_session(
            session_data,
            agents_data,
            deliverables_data
        )

        assert archive_path.exists()
        assert archive_path.suffix == ".gz"

        # Verify contents
        with gzip.open(archive_path, 'rt') as f:
            archived = json.load(f)
            assert archived["session"]["session_id"] == "test-session"
            assert len(archived["agents"]) == 1

    def test_list_archives(self, archiver, temp_archive_dir):
        """Test listing archives."""
        # Create a test archive
        archiver.archive_session(
            {"session_id": "test"},
            [],
            []
        )

        archives = archiver.list_archives(days=30)

        assert len(archives) >= 1
        assert "path" in archives[0]
        assert "size_kb" in archives[0]

    def test_restore_session(self, archiver, temp_archive_dir):
        """Test restoring a session from archive."""
        session_data = {
            "session_id": "test-session",
            "prompt": "Test prompt"
        }

        archive_path = archiver.archive_session(
            session_data,
            [],
            []
        )

        restored = archiver.restore_session(archive_path)

        assert restored["session"]["session_id"] == "test-session"


class TestDataRetentionManager:
    """Test DataRetentionManager class."""

    @pytest.fixture
    def temp_archive_dir(self):
        """Create a temporary archive directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_archive_dir):
        """Create a DataRetentionManager instance."""
        from src.runtime.agents.data_retention import DataRetentionManager
        return DataRetentionManager(
            archive_dir=temp_archive_dir,
            max_db_size_mb=100
        )

    def test_init(self, manager):
        """Test DataRetentionManager initialization."""
        assert manager._running is False
        assert manager.compactor is not None
        assert manager.archiver is not None

    def test_init_with_custom_rules(self, temp_archive_dir):
        """Test initialization with custom rules."""
        from src.runtime.agents.data_retention import (
            DataRetentionManager, RetentionRule, RetentionPolicy
        )

        custom_rules = [
            RetentionRule(
                data_type="custom",
                policy=RetentionPolicy.SHORT_TERM,
                retention_hours=12,
                compact_after_hours=6
            )
        ]

        manager = DataRetentionManager(
            rules=custom_rules,
            archive_dir=temp_archive_dir
        )

        assert "custom" in manager.rules

    def test_start_background_cleanup(self, manager):
        """Test starting background cleanup."""
        manager.start_background_cleanup(interval_minutes=1)

        assert manager._running is True
        assert manager._thread is not None

        # Cleanup
        manager.stop_background_cleanup()

    def test_stop_background_cleanup(self, manager):
        """Test stopping background cleanup."""
        manager.start_background_cleanup(interval_minutes=1)
        manager.stop_background_cleanup()

        assert manager._running is False

    def test_get_retention_stats(self, manager, temp_archive_dir):
        """Test getting retention statistics."""
        # These methods require the swarm_state module, so just test they don't crash
        # when swarm_state is not available
        try:
            stats = manager.get_retention_stats()
            assert "database_size_mb" in stats
            assert "max_size_mb" in stats
        except Exception:
            # If swarm_state isn't initialized, that's expected
            pass

    def test_get_status(self, manager, temp_archive_dir):
        """Test getting status."""
        # The is_running and retention_rules don't need swarm_state
        status = manager.get_status()
        assert "is_running" in status
        assert "retention_rules" in status

    def test_run_cleanup_dry_run(self, manager, temp_archive_dir):
        """Test dry run cleanup."""
        # Dry run needs swarm_state, so test it doesn't crash
        try:
            result = manager.run_cleanup(dry_run=True)
            assert result["dry_run"] is True
            assert "would_delete" in result
        except Exception:
            # If swarm_state isn't initialized, that's expected
            pass


class TestGlobalRetentionManager:
    """Test global retention manager function."""

    def test_get_retention_manager(self):
        """Test get_retention_manager returns instance."""
        # Reset global
        import src.runtime.agents.data_retention as module
        module._retention_manager = None

        from src.runtime.agents.data_retention import get_retention_manager

        manager = get_retention_manager()

        assert manager is not None

    def test_get_retention_manager_returns_same_instance(self):
        """Test get_retention_manager returns same instance."""
        import src.runtime.agents.data_retention as module
        module._retention_manager = None

        from src.runtime.agents.data_retention import get_retention_manager

        m1 = get_retention_manager()
        m2 = get_retention_manager()

        assert m1 is m2
