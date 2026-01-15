"""
Data Retention Manager - Manages swarm data lifecycle, compaction, and archival.

Implements retention policies to prevent database bloat while maintaining
data needed for recovery, analytics, and debugging.
"""
import json
import logging
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RetentionPolicy(Enum):
    """Data retention policies."""
    IMMEDIATE = "immediate"      # Delete immediately when no longer needed
    SHORT_TERM = "short_term"    # Keep for hours (operational data)
    MEDIUM_TERM = "medium_term"  # Keep for days (debugging data)
    LONG_TERM = "long_term"      # Keep for weeks (analytics data)
    ARCHIVE = "archive"          # Compress and archive
    PERMANENT = "permanent"      # Never delete


@dataclass
class RetentionRule:
    """A rule for data retention."""
    data_type: str
    policy: RetentionPolicy
    retention_hours: int
    compact_after_hours: int
    archive_after_hours: Optional[int] = None
    description: str = ""


# Default retention rules
DEFAULT_RETENTION_RULES = [
    # Events - short lived, high volume
    RetentionRule(
        data_type="events",
        policy=RetentionPolicy.SHORT_TERM,
        retention_hours=24,
        compact_after_hours=6,
        description="Processed events can be cleaned quickly"
    ),

    # Agent messages - medium term for debugging
    RetentionRule(
        data_type="agent_messages",
        policy=RetentionPolicy.MEDIUM_TERM,
        retention_hours=168,  # 1 week
        compact_after_hours=48,
        archive_after_hours=336,  # 2 weeks -> archive
        description="Conversation history for debugging"
    ),

    # Tool executions - medium term
    RetentionRule(
        data_type="tool_executions",
        policy=RetentionPolicy.MEDIUM_TERM,
        retention_hours=168,
        compact_after_hours=72,
        description="Tool execution logs"
    ),

    # Completed sessions - long term for analytics
    RetentionRule(
        data_type="completed_sessions",
        policy=RetentionPolicy.LONG_TERM,
        retention_hours=720,  # 30 days
        compact_after_hours=168,
        archive_after_hours=1440,  # 60 days -> archive
        description="Completed session summaries"
    ),

    # Failed sessions - longer for debugging
    RetentionRule(
        data_type="failed_sessions",
        policy=RetentionPolicy.LONG_TERM,
        retention_hours=336,  # 2 weeks
        compact_after_hours=72,
        description="Failed sessions for root cause analysis"
    ),

    # Recovery queue - short term
    RetentionRule(
        data_type="recovery_queue",
        policy=RetentionPolicy.SHORT_TERM,
        retention_hours=48,
        compact_after_hours=24,
        description="Completed recovery tasks"
    ),

    # Deliverables - permanent (references to files/commits)
    RetentionRule(
        data_type="deliverables",
        policy=RetentionPolicy.PERMANENT,
        retention_hours=-1,  # Never delete
        compact_after_hours=-1,
        description="File and commit references"
    ),

    # Metrics summaries - long term
    RetentionRule(
        data_type="metrics_summaries",
        policy=RetentionPolicy.LONG_TERM,
        retention_hours=2160,  # 90 days
        compact_after_hours=720,
        archive_after_hours=4320,  # 180 days
        description="Aggregated performance metrics"
    ),
]


class DataCompactor:
    """Compacts data by summarizing and removing details."""

    def compact_agent_messages(
        self,
        agent_id: str,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compact agent messages into a summary.

        Keeps:
        - First and last messages
        - Total message count
        - Key decisions/outputs
        - Error messages

        Removes:
        - Intermediate reasoning
        - Verbose tool outputs
        """
        if not messages:
            return {"summary": "No messages", "message_count": 0}

        summary = {
            "agent_id": agent_id,
            "message_count": len(messages),
            "first_message": self._truncate_content(messages[0]),
            "last_message": self._truncate_content(messages[-1]),
            "key_outputs": [],
            "errors": [],
            "compacted_at": datetime.now().isoformat()
        }

        # Extract key information
        for msg in messages:
            content = msg.get('content', '')
            if isinstance(content, str):
                # Look for JSON outputs
                if '"status"' in content:
                    try:
                        # Extract status blocks
                        import re
                        json_matches = re.findall(r'\{[^{}]*"status"[^{}]*\}', content)
                        for match in json_matches[:3]:  # Max 3
                            summary['key_outputs'].append(match[:500])
                    except:
                        pass

                # Look for errors
                if 'error' in content.lower() or 'failed' in content.lower():
                    summary['errors'].append(content[:200])

        return summary

    def _truncate_content(self, message: Dict[str, Any], max_length: int = 500) -> Dict[str, Any]:
        """Truncate message content."""
        result = dict(message)
        content = result.get('content', '')
        if isinstance(content, str) and len(content) > max_length:
            result['content'] = content[:max_length] + "...[truncated]"
        return result

    def compact_tool_executions(
        self,
        agent_id: str,
        executions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compact tool executions into summary statistics."""
        if not executions:
            return {"summary": "No executions", "count": 0}

        summary = {
            "agent_id": agent_id,
            "total_executions": len(executions),
            "by_tool": {},
            "success_rate": 0,
            "total_duration_ms": 0,
            "failed_tools": [],
            "compacted_at": datetime.now().isoformat()
        }

        for ex in executions:
            tool_name = ex.get('tool_name', 'unknown')
            success = ex.get('success', True)
            duration = ex.get('duration_ms', 0) or 0

            if tool_name not in summary['by_tool']:
                summary['by_tool'][tool_name] = {'count': 0, 'success': 0, 'failed': 0}

            summary['by_tool'][tool_name]['count'] += 1
            if success:
                summary['by_tool'][tool_name]['success'] += 1
            else:
                summary['by_tool'][tool_name]['failed'] += 1
                summary['failed_tools'].append({
                    'tool': tool_name,
                    'error': str(ex.get('result', {}))[:200]
                })

            summary['total_duration_ms'] += duration

        total = summary['total_executions']
        successes = sum(t['success'] for t in summary['by_tool'].values())
        summary['success_rate'] = successes / total if total > 0 else 0

        return summary


class DataArchiver:
    """Archives old data to compressed files."""

    def __init__(self, archive_dir: Optional[Path] = None):
        self.archive_dir = archive_dir or Path.home() / ".ensemble" / "archives"
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def archive_session(
        self,
        session_data: Dict[str, Any],
        agents_data: List[Dict[str, Any]],
        deliverables_data: List[Dict[str, Any]]
    ) -> Path:
        """Archive a complete session to a compressed file."""
        import gzip

        session_id = session_data.get('session_id', 'unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        archive_data = {
            "session": session_data,
            "agents": agents_data,
            "deliverables": deliverables_data,
            "archived_at": datetime.now().isoformat()
        }

        archive_path = self.archive_dir / f"session_{session_id}_{timestamp}.json.gz"

        with gzip.open(archive_path, 'wt', encoding='utf-8') as f:
            json.dump(archive_data, f, indent=2, default=str)

        logger.info(f"Archived session {session_id} to {archive_path}")
        return archive_path

    def list_archives(self, days: int = 30) -> List[Dict[str, Any]]:
        """List available archives."""
        archives = []
        cutoff = datetime.now() - timedelta(days=days)

        for archive_path in self.archive_dir.glob("*.json.gz"):
            stat = archive_path.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime)

            if mtime > cutoff:
                archives.append({
                    "path": str(archive_path),
                    "name": archive_path.name,
                    "size_kb": stat.st_size / 1024,
                    "created": mtime.isoformat()
                })

        return sorted(archives, key=lambda x: x['created'], reverse=True)

    def restore_session(self, archive_path: Path) -> Dict[str, Any]:
        """Restore a session from archive."""
        import gzip

        with gzip.open(archive_path, 'rt', encoding='utf-8') as f:
            return json.load(f)

    def archive_session_by_id(self, session_id: str) -> Dict[str, Any]:
        """Archive a session by its ID (for API use)."""
        from .swarm_state import get_swarm_state

        swarm_state = get_swarm_state()

        # Get session data
        session = swarm_state.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        if session.get("status") == "running":
            return {"success": False, "error": "Cannot archive running session"}

        # Get agents
        agents = swarm_state.get_session_agents(session_id)

        # Get deliverables
        deliverables = swarm_state.get_session_deliverables(session_id)

        try:
            archive_path = self.archive_session(session, agents, deliverables)

            # Delete from database after successful archive
            with swarm_state._get_connection() as conn:
                conn.execute("DELETE FROM agent_messages WHERE agent_id IN (SELECT agent_id FROM agents WHERE session_id = ?)", (session_id,))
                conn.execute("DELETE FROM tool_executions WHERE agent_id IN (SELECT agent_id FROM agents WHERE session_id = ?)", (session_id,))
                conn.execute("DELETE FROM agents WHERE session_id = ?", (session_id,))
                conn.execute("DELETE FROM swarm_sessions WHERE session_id = ?", (session_id,))
                conn.commit()

            return {
                "success": True,
                "session_id": session_id,
                "archive_path": str(archive_path),
                "agents_archived": len(agents),
                "deliverables_preserved": len(deliverables)
            }
        except Exception as e:
            logger.error(f"Failed to archive session {session_id}: {e}")
            return {"success": False, "error": str(e)}


class DataRetentionManager:
    """
    Manages data retention, compaction, and archival.

    Features:
    - Configurable retention policies per data type
    - Automatic compaction of old data
    - Archival of historical sessions
    - Size-based triggers
    - Scheduled cleanup
    """

    def __init__(
        self,
        rules: Optional[List[RetentionRule]] = None,
        archive_dir: Optional[Path] = None,
        max_db_size_mb: int = 500
    ):
        self.rules = {r.data_type: r for r in (rules or DEFAULT_RETENTION_RULES)}
        self.compactor = DataCompactor()
        self.archiver = DataArchiver(archive_dir)
        self.max_db_size_mb = max_db_size_mb
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start_background_cleanup(self, interval_minutes: int = 60):
        """Start background cleanup thread."""
        if self._running:
            return

        self._running = True

        def cleanup_loop():
            while self._running:
                try:
                    self.run_cleanup_cycle()
                except Exception as e:
                    logger.error(f"Cleanup cycle error: {e}")

                # Sleep in chunks for faster shutdown
                for _ in range(interval_minutes * 6):
                    if not self._running:
                        break
                    time.sleep(10)

        self._thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._thread.start()
        logger.info("Data retention manager started")

    def stop_background_cleanup(self):
        """Stop background cleanup."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=30)

    def run_cleanup_cycle(self):
        """Run a complete cleanup cycle."""
        logger.info("Starting data retention cleanup cycle")

        # 1. Check database size
        db_size_mb = self._get_db_size_mb()
        logger.info(f"Current database size: {db_size_mb:.2f} MB")

        # 2. Delete expired events
        deleted_events = self._cleanup_events()
        logger.info(f"Deleted {deleted_events} expired events")

        # 3. Compact old agent messages
        compacted_agents = self._compact_agent_messages()
        logger.info(f"Compacted messages for {compacted_agents} agents")

        # 4. Compact tool executions
        compacted_tools = self._compact_tool_executions()
        logger.info(f"Compacted tool executions for {compacted_tools} agents")

        # 5. Archive old completed sessions
        archived_sessions = self._archive_old_sessions()
        logger.info(f"Archived {archived_sessions} old sessions")

        # 6. Clean recovery queue
        cleaned_recovery = self._cleanup_recovery_queue()
        logger.info(f"Cleaned {cleaned_recovery} recovery entries")

        # 7. If still over size limit, force more aggressive cleanup
        db_size_mb = self._get_db_size_mb()
        if db_size_mb > self.max_db_size_mb:
            logger.warning(f"Database still over limit ({db_size_mb:.2f} MB), running aggressive cleanup")
            self._aggressive_cleanup()

        # 8. Vacuum database
        self._vacuum_database()

        logger.info("Data retention cleanup cycle completed")

    def _get_db_size_mb(self) -> float:
        """Get current database size in MB."""
        try:
            from .swarm_state import get_swarm_state
            db_path = get_swarm_state().db_path
            if db_path.exists():
                return db_path.stat().st_size / (1024 * 1024)
        except:
            pass
        return 0

    def _cleanup_events(self) -> int:
        """Delete old processed events."""
        rule = self.rules.get("events")
        if not rule:
            return 0

        from .swarm_state import get_swarm_state
        swarm_state = get_swarm_state()

        with swarm_state._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM events
                WHERE processed = 1
                AND timestamp < datetime('now', ?)
            """, (f'-{rule.retention_hours} hours',))
            deleted = cursor.rowcount
            conn.commit()

        return deleted

    def _compact_agent_messages(self) -> int:
        """Compact old agent messages."""
        rule = self.rules.get("agent_messages")
        if not rule:
            return 0

        from .swarm_state import get_swarm_state
        swarm_state = get_swarm_state()

        compacted_count = 0

        with swarm_state._get_connection() as conn:
            # Find agents with messages older than compact threshold
            rows = conn.execute("""
                SELECT DISTINCT agent_id
                FROM agent_messages
                WHERE timestamp < datetime('now', ?)
                AND agent_id NOT IN (
                    SELECT agent_id FROM agents WHERE status = 'running'
                )
            """, (f'-{rule.compact_after_hours} hours',)).fetchall()

            for row in rows:
                agent_id = row[0]

                # Get messages
                messages = conn.execute("""
                    SELECT * FROM agent_messages
                    WHERE agent_id = ?
                    ORDER BY iteration ASC
                """, (agent_id,)).fetchall()

                if len(messages) > 10:  # Only compact if significant
                    # Create summary
                    msg_dicts = [dict(m) for m in messages]
                    summary = self.compactor.compact_agent_messages(agent_id, msg_dicts)

                    # Delete original messages (keep first and last 2)
                    conn.execute("""
                        DELETE FROM agent_messages
                        WHERE agent_id = ?
                        AND id NOT IN (
                            SELECT id FROM agent_messages
                            WHERE agent_id = ?
                            ORDER BY iteration ASC
                            LIMIT 2
                        )
                        AND id NOT IN (
                            SELECT id FROM agent_messages
                            WHERE agent_id = ?
                            ORDER BY iteration DESC
                            LIMIT 2
                        )
                    """, (agent_id, agent_id, agent_id))

                    # Store summary as a special message
                    conn.execute("""
                        INSERT INTO agent_messages
                        (agent_id, iteration, role, content)
                        VALUES (?, -1, 'system', ?)
                    """, (agent_id, json.dumps({"compacted_summary": summary})))

                    compacted_count += 1

            conn.commit()

        return compacted_count

    def _compact_tool_executions(self) -> int:
        """Compact old tool executions into summaries."""
        rule = self.rules.get("tool_executions")
        if not rule:
            return 0

        from .swarm_state import get_swarm_state
        swarm_state = get_swarm_state()

        compacted_count = 0

        with swarm_state._get_connection() as conn:
            # Find agents with old tool executions
            rows = conn.execute("""
                SELECT DISTINCT agent_id
                FROM tool_executions
                WHERE timestamp < datetime('now', ?)
                AND agent_id NOT IN (
                    SELECT agent_id FROM agents WHERE status = 'running'
                )
            """, (f'-{rule.compact_after_hours} hours',)).fetchall()

            for row in rows:
                agent_id = row[0]

                # Get executions
                executions = conn.execute("""
                    SELECT * FROM tool_executions
                    WHERE agent_id = ?
                """, (agent_id,)).fetchall()

                if len(executions) > 20:  # Only compact if significant
                    ex_dicts = [dict(e) for e in executions]
                    summary = self.compactor.compact_tool_executions(agent_id, ex_dicts)

                    # Delete originals
                    conn.execute("""
                        DELETE FROM tool_executions
                        WHERE agent_id = ?
                    """, (agent_id,))

                    # Store summary
                    conn.execute("""
                        INSERT INTO tool_executions
                        (agent_id, tool_name, inputs, result, success)
                        VALUES (?, 'compacted_summary', '{}', ?, 1)
                    """, (agent_id, json.dumps(summary)))

                    compacted_count += 1

            conn.commit()

        return compacted_count

    def _archive_old_sessions(self) -> int:
        """Archive old completed sessions."""
        rule = self.rules.get("completed_sessions")
        if not rule or not rule.archive_after_hours:
            return 0

        from .swarm_state import get_swarm_state
        swarm_state = get_swarm_state()

        archived_count = 0

        with swarm_state._get_connection() as conn:
            # Find old completed sessions
            sessions = conn.execute("""
                SELECT * FROM swarm_sessions
                WHERE status = 'completed'
                AND completed_at < datetime('now', ?)
            """, (f'-{rule.archive_after_hours} hours',)).fetchall()

            for session in sessions:
                session_dict = dict(session)
                session_id = session_dict['session_id']

                # Get agents
                agents = conn.execute("""
                    SELECT * FROM agents WHERE session_id = ?
                """, (session_id,)).fetchall()
                agents_dicts = [dict(a) for a in agents]

                # Get deliverables
                deliverables = conn.execute("""
                    SELECT * FROM deliverables WHERE session_id = ?
                """, (session_id,)).fetchall()
                deliverables_dicts = [dict(d) for d in deliverables]

                # Archive
                try:
                    self.archiver.archive_session(
                        session_dict,
                        agents_dicts,
                        deliverables_dicts
                    )

                    # Delete from database (keep deliverables)
                    conn.execute("DELETE FROM agent_messages WHERE agent_id IN (SELECT agent_id FROM agents WHERE session_id = ?)", (session_id,))
                    conn.execute("DELETE FROM tool_executions WHERE agent_id IN (SELECT agent_id FROM agents WHERE session_id = ?)", (session_id,))
                    conn.execute("DELETE FROM agents WHERE session_id = ?", (session_id,))
                    conn.execute("DELETE FROM swarm_sessions WHERE session_id = ?", (session_id,))

                    archived_count += 1
                except Exception as e:
                    logger.error(f"Failed to archive session {session_id}: {e}")

            conn.commit()

        return archived_count

    def _cleanup_recovery_queue(self) -> int:
        """Clean up old recovery entries."""
        rule = self.rules.get("recovery_queue")
        if not rule:
            return 0

        from .swarm_state import get_swarm_state
        swarm_state = get_swarm_state()

        with swarm_state._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM recovery_queue
                WHERE status IN ('completed', 'failed', 'aborted')
                AND last_attempt < datetime('now', ?)
            """, (f'-{rule.retention_hours} hours',))
            deleted = cursor.rowcount
            conn.commit()

        return deleted

    def _aggressive_cleanup(self):
        """More aggressive cleanup when database is too large."""
        from .swarm_state import get_swarm_state
        swarm_state = get_swarm_state()

        with swarm_state._get_connection() as conn:
            # Delete all processed events
            conn.execute("DELETE FROM events WHERE processed = 1")

            # Delete messages for completed agents older than 3 days
            conn.execute("""
                DELETE FROM agent_messages
                WHERE agent_id IN (
                    SELECT agent_id FROM agents
                    WHERE status IN ('completed', 'failed')
                    AND completed_at < datetime('now', '-3 days')
                )
            """)

            # Delete tool executions older than 3 days
            conn.execute("""
                DELETE FROM tool_executions
                WHERE timestamp < datetime('now', '-3 days')
            """)

            conn.commit()

    def _vacuum_database(self):
        """Vacuum database to reclaim space."""
        try:
            from .swarm_state import get_swarm_state
            swarm_state = get_swarm_state()

            with swarm_state._get_connection() as conn:
                conn.execute("VACUUM")

        except Exception as e:
            logger.warning(f"Failed to vacuum database: {e}")

    def get_retention_stats(self) -> Dict[str, Any]:
        """Get current retention statistics."""
        from .swarm_state import get_swarm_state
        swarm_state = get_swarm_state()

        stats = {
            "database_size_mb": self._get_db_size_mb(),
            "max_size_mb": self.max_db_size_mb,
            "tables": {}
        }

        with swarm_state._get_connection() as conn:
            tables = [
                "swarm_sessions", "agents", "agent_messages",
                "tool_executions", "events", "deliverables", "recovery_queue"
            ]

            for table in tables:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                stats["tables"][table] = count

        stats["archives"] = len(self.archiver.list_archives())

        return stats

    def get_status(self) -> Dict[str, Any]:
        """Get current retention status (alias for API)."""
        stats = self.get_retention_stats()
        stats["is_running"] = self._running
        stats["retention_rules"] = {
            name: {
                "policy": rule.policy.value,
                "retention_hours": rule.retention_hours,
                "compact_after_hours": rule.compact_after_hours
            }
            for name, rule in self.rules.items()
        }
        return stats

    def run_cleanup(self, dry_run: bool = True) -> Dict[str, Any]:
        """Run cleanup with optional dry run mode."""
        if dry_run:
            # Dry run - just report what would be cleaned
            return self._estimate_cleanup()
        else:
            # Actually run cleanup
            self.run_cleanup_cycle()
            return {
                "executed": True,
                "new_stats": self.get_retention_stats()
            }

    def _estimate_cleanup(self) -> Dict[str, Any]:
        """Estimate what would be cleaned without actually cleaning."""
        from .swarm_state import get_swarm_state
        swarm_state = get_swarm_state()

        estimates = {
            "dry_run": True,
            "would_delete": {},
            "current_size_mb": self._get_db_size_mb()
        }

        with swarm_state._get_connection() as conn:
            # Estimate events to delete
            rule = self.rules.get("events")
            if rule:
                count = conn.execute("""
                    SELECT COUNT(*) FROM events
                    WHERE processed = 1
                    AND timestamp < datetime('now', ?)
                """, (f'-{rule.retention_hours} hours',)).fetchone()[0]
                estimates["would_delete"]["events"] = count

            # Estimate messages to compact
            rule = self.rules.get("agent_messages")
            if rule:
                count = conn.execute("""
                    SELECT COUNT(*) FROM agent_messages
                    WHERE timestamp < datetime('now', ?)
                    AND agent_id NOT IN (
                        SELECT agent_id FROM agents WHERE status = 'running'
                    )
                """, (f'-{rule.compact_after_hours} hours',)).fetchone()[0]
                estimates["would_delete"]["agent_messages"] = count

            # Estimate sessions to archive
            rule = self.rules.get("completed_sessions")
            if rule and rule.archive_after_hours:
                count = conn.execute("""
                    SELECT COUNT(*) FROM swarm_sessions
                    WHERE status = 'completed'
                    AND completed_at < datetime('now', ?)
                """, (f'-{rule.archive_after_hours} hours',)).fetchone()[0]
                estimates["would_delete"]["sessions_to_archive"] = count

        return estimates


# Global instance
_retention_manager: Optional[DataRetentionManager] = None


def get_retention_manager() -> DataRetentionManager:
    """Get the global data retention manager."""
    global _retention_manager
    if _retention_manager is None:
        _retention_manager = DataRetentionManager()
    return _retention_manager
