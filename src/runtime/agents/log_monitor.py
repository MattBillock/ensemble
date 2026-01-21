"""
Log Monitor Service - Detects runtime failures and surfaces them to users.

This service monitors for errors in the agent system and creates actionable
issues that can be presented to users for resolution.
"""

import logging
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    """Severity levels for detected issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueCategory(Enum):
    """Categories of detected issues."""
    AGENT_FAILURE = "agent_failure"
    API_ERROR = "api_error"
    RECOVERY_FAILURE = "recovery_failure"
    CONFIGURATION_ERROR = "configuration_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class DetectedIssue:
    """Represents a detected runtime issue."""
    id: str
    timestamp: str
    severity: IssueSeverity
    category: IssueCategory
    title: str
    description: str
    source_module: str
    agent_id: Optional[str] = None
    request_id: Optional[str] = None
    suggested_actions: List[str] = field(default_factory=list)
    raw_log: str = ""
    resolved: bool = False
    resolved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "severity": self.severity.value,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "source_module": self.source_module,
            "agent_id": self.agent_id,
            "request_id": self.request_id,
            "suggested_actions": self.suggested_actions,
            "raw_log": self.raw_log,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at
        }


class LogMonitorHandler(logging.Handler):
    """Custom logging handler that captures errors for monitoring."""

    def __init__(self, callback: Callable[[logging.LogRecord], None]):
        super().__init__()
        self.callback = callback
        self.setLevel(logging.WARNING)  # Capture warnings and above

    def emit(self, record: logging.LogRecord):
        try:
            self.callback(record)
        except Exception:
            pass  # Never fail the logging system


class LogMonitor:
    """
    Monitors logs for runtime failures and creates actionable issues.

    This service:
    - Installs a log handler to capture errors
    - Analyzes error patterns to categorize issues
    - Suggests remediation actions
    - Exposes issues via API for user review
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.issues: deque = deque(maxlen=500)  # Keep last 500 issues
        self.issue_counter = 0
        self._handlers_installed = False
        self._callbacks: List[Callable[[DetectedIssue], None]] = []

        # Patterns for categorizing issues
        self._error_patterns = [
            # Agent failures
            (r"Agent.*failed|Agent.*error|Agent retry failed", IssueCategory.AGENT_FAILURE),
            (r"Agent definition.*not found", IssueCategory.CONFIGURATION_ERROR),
            (r"Cannot.*agent.*no API key", IssueCategory.CONFIGURATION_ERROR),
            # API errors
            (r"API.*error|HTTP.*error|rate.?limit", IssueCategory.API_ERROR),
            (r"anthropic|claude.*error", IssueCategory.API_ERROR),
            # Recovery failures
            (r"recovery.*failed|Recovery.*error", IssueCategory.RECOVERY_FAILURE),
            # Timeouts
            (r"timeout|timed out", IssueCategory.TIMEOUT),
            # Resource issues
            (r"memory|out of.*resources|exhausted", IssueCategory.RESOURCE_EXHAUSTION),
        ]

        # Suggested actions for each category
        self._suggested_actions = {
            IssueCategory.AGENT_FAILURE: [
                "Review agent logs for detailed error information",
                "Check if the agent's input data is valid",
                "Try restarting the agent with the Retry button",
                "If persistent, check the agent definition file"
            ],
            IssueCategory.API_ERROR: [
                "Check your API key configuration",
                "Verify network connectivity",
                "Check Anthropic API status at status.anthropic.com",
                "If rate limited, wait a few minutes before retrying"
            ],
            IssueCategory.RECOVERY_FAILURE: [
                "Check the agent definition path is correct",
                "Verify the agent type exists in the codebase",
                "Try manual restart via the UI",
                "Check backend logs for detailed errors"
            ],
            IssueCategory.CONFIGURATION_ERROR: [
                "Verify the agent definition file exists",
                "Check the ANTHROPIC_API_KEY environment variable",
                "Review agent type spelling and path",
                "Restart the backend after configuration changes"
            ],
            IssueCategory.TIMEOUT: [
                "The operation took too long - consider retrying",
                "Check network connectivity",
                "If task is complex, try breaking it into smaller parts"
            ],
            IssueCategory.RESOURCE_EXHAUSTION: [
                "Clear completed/old data from the system",
                "Restart the backend to free up resources",
                "Check system memory usage"
            ],
            IssueCategory.UNKNOWN: [
                "Review the full error log for details",
                "Check backend logs for more context",
                "Try restarting the affected operation"
            ]
        }

    def install_handlers(self):
        """Install log handlers to capture errors."""
        if self._handlers_installed:
            return

        handler = LogMonitorHandler(self._process_log_record)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

        # Install on root logger and key module loggers
        logging.getLogger().addHandler(handler)
        for module in ['src.runtime.agents', 'src.field.ensemble_ui.backend']:
            logging.getLogger(module).addHandler(handler)

        self._handlers_installed = True
        logger.info("Log monitor handlers installed")

    def _process_log_record(self, record: logging.LogRecord):
        """Process a log record and potentially create an issue."""
        # Only process warnings and errors
        if record.levelno < logging.WARNING:
            return

        message = record.getMessage()

        # Categorize the issue
        category = self._categorize_error(message)

        # Determine severity
        if record.levelno >= logging.ERROR:
            severity = IssueSeverity.ERROR
        else:
            severity = IssueSeverity.WARNING

        # Extract agent_id if present
        agent_id = self._extract_agent_id(message)
        request_id = self._extract_request_id(message)

        # Create issue
        self.issue_counter += 1
        issue = DetectedIssue(
            id=f"issue_{self.issue_counter}_{int(time.time())}",
            timestamp=datetime.now().isoformat(),
            severity=severity,
            category=category,
            title=self._generate_title(category, message),
            description=message[:500],
            source_module=record.name,
            agent_id=agent_id,
            request_id=request_id,
            suggested_actions=self._suggested_actions.get(category, []),
            raw_log=f"{record.levelname}: {message}"
        )

        self.issues.append(issue)

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(issue)
            except Exception as e:
                logger.debug(f"Issue callback failed: {e}")

    def _categorize_error(self, message: str) -> IssueCategory:
        """Categorize an error message."""
        message_lower = message.lower()
        for pattern, category in self._error_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return category
        return IssueCategory.UNKNOWN

    def _extract_agent_id(self, message: str) -> Optional[str]:
        """Extract agent ID from message if present."""
        patterns = [
            r"agent[_\s]?(?:id)?[:\s]+([a-zA-Z0-9_\-]+)",
            r"for agent[:\s]+([a-zA-Z0-9_\-]+)",
            r"Agent ([a-zA-Z0-9_\-]+) ",
        ]
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_request_id(self, message: str) -> Optional[str]:
        """Extract request ID from message if present."""
        patterns = [
            r"request[_\s]?id[:\s]+([a-zA-Z0-9_\-]+)",
            r"req[_\s]?id[:\s]+([a-zA-Z0-9_\-]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _generate_title(self, category: IssueCategory, message: str) -> str:
        """Generate a user-friendly title for the issue."""
        titles = {
            IssueCategory.AGENT_FAILURE: "Agent Execution Failed",
            IssueCategory.API_ERROR: "API Communication Error",
            IssueCategory.RECOVERY_FAILURE: "Agent Recovery Failed",
            IssueCategory.CONFIGURATION_ERROR: "Configuration Error",
            IssueCategory.TIMEOUT: "Operation Timed Out",
            IssueCategory.RESOURCE_EXHAUSTION: "Resource Limit Reached",
            IssueCategory.UNKNOWN: "Runtime Error Detected",
        }
        return titles.get(category, "Error Detected")

    def get_issues(
        self,
        severity: Optional[IssueSeverity] = None,
        category: Optional[IssueCategory] = None,
        unresolved_only: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get detected issues with optional filtering."""
        issues = list(self.issues)

        # Filter
        if severity:
            issues = [i for i in issues if i.severity == severity]
        if category:
            issues = [i for i in issues if i.category == category]
        if unresolved_only:
            issues = [i for i in issues if not i.resolved]

        # Sort by timestamp (newest first)
        issues.sort(key=lambda x: x.timestamp, reverse=True)

        return [i.to_dict() for i in issues[:limit]]

    def resolve_issue(self, issue_id: str) -> bool:
        """Mark an issue as resolved."""
        for issue in self.issues:
            if issue.id == issue_id:
                issue.resolved = True
                issue.resolved_at = datetime.now().isoformat()
                return True
        return False

    def resolve_all(self) -> int:
        """Mark all issues as resolved."""
        count = 0
        for issue in self.issues:
            if not issue.resolved:
                issue.resolved = True
                issue.resolved_at = datetime.now().isoformat()
                count += 1
        return count

    def add_callback(self, callback: Callable[[DetectedIssue], None]):
        """Add a callback to be notified of new issues."""
        self._callbacks.append(callback)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of current issues."""
        issues = list(self.issues)
        unresolved = [i for i in issues if not i.resolved]

        by_severity = {}
        by_category = {}
        for issue in unresolved:
            sev = issue.severity.value
            cat = issue.category.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "total_issues": len(issues),
            "unresolved_count": len(unresolved),
            "by_severity": by_severity,
            "by_category": by_category,
            "oldest_unresolved": unresolved[-1].to_dict() if unresolved else None,
            "newest_unresolved": unresolved[0].to_dict() if unresolved else None,
        }


# Singleton accessor
_log_monitor: Optional[LogMonitor] = None


def get_log_monitor() -> LogMonitor:
    """Get the singleton LogMonitor instance."""
    global _log_monitor
    if _log_monitor is None:
        _log_monitor = LogMonitor()
    return _log_monitor


def init_log_monitor():
    """Initialize and install the log monitor."""
    monitor = get_log_monitor()
    monitor.install_handlers()
    return monitor
