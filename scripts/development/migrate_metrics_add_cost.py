"""Migration script to add cost tracking fields to metrics database."""
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Add input_tokens, output_tokens, and estimated_cost columns to agent_executions table."""
    db_path = Path.home() / ".ensemble" / "metrics.db"

    if not db_path.exists():
        logger.error(f"Metrics database not found at {db_path}")
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(agent_executions)")
        columns = {row[1] for row in cursor.fetchall()}

        migrations_needed = []

        if "input_tokens" not in columns:
            migrations_needed.append("ALTER TABLE agent_executions ADD COLUMN input_tokens INTEGER")

        if "output_tokens" not in columns:
            migrations_needed.append("ALTER TABLE agent_executions ADD COLUMN output_tokens INTEGER")

        if "estimated_cost" not in columns:
            migrations_needed.append("ALTER TABLE agent_executions ADD COLUMN estimated_cost REAL")

        if not migrations_needed:
            logger.info("✓ All cost tracking columns already exist")
            return True

        # Run migrations
        for migration_sql in migrations_needed:
            logger.info(f"Running: {migration_sql}")
            cursor.execute(migration_sql)

        conn.commit()
        conn.close()

        logger.info(f"✓ Successfully added {len(migrations_needed)} columns to metrics database")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = migrate()
    exit(0 if success else 1)
