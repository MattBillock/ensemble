"""
Unit tests for log_monitor module.
"""

import pytest
import logging
from datetime import datetime
from src.runtime.agents.log_monitor import (
    IssueSeverity,
    IssueCategory,
    DetectedIssue,
    LogMonitorHandler,
    LogMonitor,
)


class TestIssueSeverity:
    """Test IssueSeverity enum."""

    def test_severity_values(self):
        """Test severity enum values."""
        assert IssueSeverity.INFO.value == "info"
        assert IssueSeverity.WARNING.value == "warning"
        assert IssueSeverity.ERROR.value == "error"
        assert IssueSeverity.CRITICAL.value == "critical"


class TestIssueCategory:
    """Test IssueCategory enum."""

    def test_category_values(self):
        """Test category enum values."""
        assert IssueCategory.AGENT_FAILURE.value == "agent_failure"
        assert IssueCategory.API_ERROR.value == "api_error"
        assert IssueCategory.RECOVERY_FAILURE.value == "recovery_failure"
        assert IssueCategory.CONFIGURATION_ERROR.value == "configuration_error"
        assert IssueCategory.RESOURCE_EXHAUSTION.value == "resource_exhaustion"
        assert IssueCategory.TIMEOUT.value == "timeout"
        assert IssueCategory.UNKNOWN.value == "unknown"


class TestDetectedIssue:
    """Test DetectedIssue dataclass."""

    def test_create_issue(self):
        """Test creating a detected issue."""
        issue = DetectedIssue(
            id="test-123",
            timestamp="2026-01-17T12:00:00",
            severity=IssueSeverity.ERROR,
            category=IssueCategory.AGENT_FAILURE,
            title="Test Issue",
            description="Test description",
            source_module="test_module"
        )

        assert issue.id == "test-123"
        assert issue.severity == IssueSeverity.ERROR
        assert issue.category == IssueCategory.AGENT_FAILURE
        assert issue.resolved is False

    def test_issue_with_optional_fields(self):
        """Test issue with optional fields."""
        issue = DetectedIssue(
            id="test-456",
            timestamp="2026-01-17T12:00:00",
            severity=IssueSeverity.WARNING,
            category=IssueCategory.TIMEOUT,
            title="Timeout Issue",
            description="Agent timed out",
            source_module="runtime",
            agent_id="agent-123",
            request_id="req-456",
            suggested_actions=["Retry", "Check configuration"],
            raw_log="ERROR: timeout occurred"
        )

        assert issue.agent_id == "agent-123"
        assert issue.request_id == "req-456"
        assert len(issue.suggested_actions) == 2

    def test_to_dict(self):
        """Test converting issue to dictionary."""
        issue = DetectedIssue(
            id="test-789",
            timestamp="2026-01-17T12:00:00",
            severity=IssueSeverity.CRITICAL,
            category=IssueCategory.API_ERROR,
            title="API Failure",
            description="API call failed",
            source_module="api_module"
        )

        result = issue.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == "test-789"
        assert result["severity"] == "critical"
        assert result["category"] == "api_error"
        assert result["resolved"] is False


class TestLogMonitorHandler:
    """Test LogMonitorHandler."""

    def test_handler_calls_callback(self):
        """Test that handler calls callback with log record."""
        captured_records = []

        def callback(record):
            captured_records.append(record)

        handler = LogMonitorHandler(callback)
        handler.setLevel(logging.ERROR)

        logger = logging.getLogger("test_handler")
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)

        logger.error("Test error message")

        assert len(captured_records) == 1
        assert captured_records[0].message == "Test error message"

        logger.removeHandler(handler)


class TestLogMonitor:
    """Test LogMonitor service."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton for each test."""
        # Save original state
        original_instance = LogMonitor._instance
        LogMonitor._instance = None

        yield

        # Restore original state
        LogMonitor._instance = original_instance

    def test_create_monitor(self):
        """Test creating a log monitor."""
        monitor = LogMonitor()

        assert monitor is not None
        assert len(monitor.get_issues()) == 0

    def test_singleton_pattern(self):
        """Test that LogMonitor is a singleton."""
        monitor1 = LogMonitor()
        monitor2 = LogMonitor()

        assert monitor1 is monitor2

    def test_get_issues_empty(self):
        """Test getting issues when none exist."""
        monitor = LogMonitor()

        issues = monitor.get_issues()

        assert isinstance(issues, list)
        assert len(issues) == 0

    def test_mark_issue_resolved(self):
        """Test marking an issue as resolved."""
        monitor = LogMonitor()

        # Create a mock issue
        issue = DetectedIssue(
            id="test-resolve",
            timestamp=datetime.now().isoformat(),
            severity=IssueSeverity.ERROR,
            category=IssueCategory.AGENT_FAILURE,
            title="Test Error",
            description="Test description",
            source_module="test"
        )

        # Add to monitor's issue list
        monitor.issues.append(issue)

        # Resolve it
        resolved = monitor.resolve_issue("test-resolve")

        assert resolved is True
        assert issue.resolved is True

    def test_mark_nonexistent_issue_resolved(self):
        """Test resolving a non-existent issue."""
        monitor = LogMonitor()

        resolved = monitor.resolve_issue("nonexistent-id")

        assert resolved is False

    def test_get_issues_by_severity(self):
        """Test filtering issues by severity."""
        monitor = LogMonitor()

        # Add issues with different severities
        error_issue = DetectedIssue(
            id="error-1",
            timestamp=datetime.now().isoformat(),
            severity=IssueSeverity.ERROR,
            category=IssueCategory.AGENT_FAILURE,
            title="Error",
            description="Error desc",
            source_module="test"
        )

        warning_issue = DetectedIssue(
            id="warning-1",
            timestamp=datetime.now().isoformat(),
            severity=IssueSeverity.WARNING,
            category=IssueCategory.TIMEOUT,
            title="Warning",
            description="Warning desc",
            source_module="test"
        )

        monitor.issues.append(error_issue)
        monitor.issues.append(warning_issue)

        error_issues = monitor.get_issues(severity=IssueSeverity.ERROR, unresolved_only=False)

        assert len(error_issues) == 1
        assert error_issues[0]["id"] == "error-1"

    def test_get_issues_by_category(self):
        """Test filtering issues by category."""
        monitor = LogMonitor()

        api_issue = DetectedIssue(
            id="api-1",
            timestamp=datetime.now().isoformat(),
            severity=IssueSeverity.ERROR,
            category=IssueCategory.API_ERROR,
            title="API Error",
            description="API error desc",
            source_module="api"
        )

        agent_issue = DetectedIssue(
            id="agent-1",
            timestamp=datetime.now().isoformat(),
            severity=IssueSeverity.ERROR,
            category=IssueCategory.AGENT_FAILURE,
            title="Agent Error",
            description="Agent error desc",
            source_module="runtime"
        )

        monitor.issues.append(api_issue)
        monitor.issues.append(agent_issue)

        api_issues = monitor.get_issues(category=IssueCategory.API_ERROR, unresolved_only=False)

        assert len(api_issues) == 1
        assert api_issues[0]["id"] == "api-1"

    def test_categorize_agent_failure(self):
        """Test categorizing agent failure messages."""
        monitor = LogMonitor()

        category = monitor._categorize_error("Agent TestAgent failed with error")

        assert category == IssueCategory.AGENT_FAILURE

    def test_categorize_api_error(self):
        """Test categorizing API error messages."""
        monitor = LogMonitor()

        category = monitor._categorize_error("API error: rate limit exceeded")

        assert category == IssueCategory.API_ERROR

    def test_categorize_timeout(self):
        """Test categorizing timeout messages."""
        monitor = LogMonitor()

        category = monitor._categorize_error("Operation timed out after 60s")

        assert category == IssueCategory.TIMEOUT

    def test_categorize_unknown(self):
        """Test categorizing unknown messages."""
        monitor = LogMonitor()

        category = monitor._categorize_error("Some random error message")

        assert category == IssueCategory.UNKNOWN

    def test_extract_agent_id(self):
        """Test extracting agent ID from message."""
        monitor = LogMonitor()

        agent_id = monitor._extract_agent_id("Error for agent: test-agent-123")

        assert agent_id == "test-agent-123"

    def test_extract_agent_id_none(self):
        """Test extracting agent ID when not present."""
        monitor = LogMonitor()

        # Use a message without any agent-related keywords
        agent_id = monitor._extract_agent_id("Database connection failed")

        assert agent_id is None

    def test_generate_title(self):
        """Test generating issue titles."""
        monitor = LogMonitor()

        title = monitor._generate_title(IssueCategory.AGENT_FAILURE, "some message")

        assert title == "Agent Execution Failed"

    def test_resolve_all(self):
        """Test resolving all issues."""
        monitor = LogMonitor()

        issue1 = DetectedIssue(
            id="issue-1",
            timestamp=datetime.now().isoformat(),
            severity=IssueSeverity.ERROR,
            category=IssueCategory.AGENT_FAILURE,
            title="Error 1",
            description="Error desc 1",
            source_module="test"
        )

        issue2 = DetectedIssue(
            id="issue-2",
            timestamp=datetime.now().isoformat(),
            severity=IssueSeverity.WARNING,
            category=IssueCategory.TIMEOUT,
            title="Warning 1",
            description="Warning desc 1",
            source_module="test"
        )

        monitor.issues.append(issue1)
        monitor.issues.append(issue2)

        count = monitor.resolve_all()

        assert count == 2
        assert issue1.resolved is True
        assert issue2.resolved is True
