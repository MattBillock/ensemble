"""
Secrets Manager - Secure credential storage and access control.

Provides encrypted storage for API keys, credentials, and sensitive data
with audit logging and access control for agents.
"""
import base64
import hashlib
import json
import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SecretAccessDenied(Exception):
    """Raised when an agent doesn't have permission to access a secret."""
    pass


class SecretNotFound(Exception):
    """Raised when a requested secret doesn't exist."""
    pass


class SecretsManager:
    """
    Secure secrets management with encryption and access control.

    Features:
    - Encrypted storage using derived key
    - Agent-level access control
    - Audit logging of all access
    - Secret rotation tracking
    - Environment variable fallback
    """

    _instance: Optional["SecretsManager"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        db_path: Optional[Path] = None,
        master_key: Optional[str] = None
    ):
        if self._initialized:
            return

        self.db_path = db_path or Path.home() / ".ensemble" / "secrets.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Derive encryption key from master key or machine ID
        if master_key:
            self._key = self._derive_key(master_key)
        else:
            self._key = self._derive_key(self._get_machine_id())

        self._local = threading.local()
        self._init_database()
        self._initialized = True

        logger.info("SecretsManager initialized")

    def _get_machine_id(self) -> str:
        """Get a stable machine identifier for key derivation."""
        # Use combination of hostname and user
        import socket
        import getpass
        return f"{socket.gethostname()}:{getpass.getuser()}:ensemble"

    def _derive_key(self, master: str) -> bytes:
        """Derive encryption key from master secret."""
        # Simple key derivation (in production, use proper KDF like PBKDF2)
        return hashlib.sha256(master.encode()).digest()

    def _encrypt(self, plaintext: str) -> str:
        """Encrypt a string value."""
        try:
            from cryptography.fernet import Fernet
            # Derive Fernet key from our key
            fernet_key = base64.urlsafe_b64encode(self._key)
            f = Fernet(fernet_key)
            return f.encrypt(plaintext.encode()).decode()
        except ImportError:
            # Fallback: simple XOR obfuscation (NOT secure, just obscuring)
            logger.warning("cryptography package not installed, using basic obfuscation")
            return self._simple_obfuscate(plaintext)

    def _decrypt(self, ciphertext: str) -> str:
        """Decrypt a string value."""
        try:
            from cryptography.fernet import Fernet
            fernet_key = base64.urlsafe_b64encode(self._key)
            f = Fernet(fernet_key)
            return f.decrypt(ciphertext.encode()).decode()
        except ImportError:
            return self._simple_deobfuscate(ciphertext)

    def _simple_obfuscate(self, text: str) -> str:
        """Simple obfuscation fallback (NOT cryptographically secure)."""
        result = []
        for i, char in enumerate(text):
            result.append(chr(ord(char) ^ self._key[i % len(self._key)]))
        return base64.b64encode(''.join(result).encode('latin-1')).decode()

    def _simple_deobfuscate(self, text: str) -> str:
        """Reverse simple obfuscation."""
        decoded = base64.b64decode(text).decode('latin-1')
        result = []
        for i, char in enumerate(decoded):
            result.append(chr(ord(char) ^ self._key[i % len(self._key)]))
        return ''.join(result)

    @contextmanager
    def _get_connection(self):
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row

        try:
            yield self._local.connection
        except Exception as e:
            self._local.connection.rollback()
            raise e

    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS secrets (
                    name TEXT PRIMARY KEY,
                    encrypted_value TEXT NOT NULL,
                    description TEXT,
                    allowed_agents TEXT DEFAULT '["*"]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    rotation_interval_days INTEGER,
                    last_rotated TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    secret_name TEXT NOT NULL,
                    agent_id TEXT,
                    agent_type TEXT,
                    action TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    def store_secret(
        self,
        name: str,
        value: str,
        description: Optional[str] = None,
        allowed_agents: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
        rotation_interval_days: Optional[int] = None
    ):
        """
        Store a secret securely.

        Args:
            name: Unique name for the secret
            value: Secret value to store
            description: Optional description
            allowed_agents: List of agent types that can access this secret.
                           Use ["*"] for all agents (default).
                           Use specific types like ["executive_director", "api_developer"]
            expires_in_days: Optional expiration in days
            rotation_interval_days: How often secret should be rotated
        """
        encrypted = self._encrypt(value)
        allowed = json.dumps(allowed_agents or ["*"])

        expires_at = None
        if expires_in_days:
            expires_at = (datetime.now() + timedelta(days=expires_in_days)).isoformat()

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO secrets
                (name, encrypted_value, description, allowed_agents, expires_at,
                 rotation_interval_days, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (name, encrypted, description, allowed, expires_at, rotation_interval_days))
            conn.commit()

        logger.info(f"Stored secret: {name}")

    def get_secret(
        self,
        name: str,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None
    ) -> str:
        """
        Retrieve a secret with access control.

        Args:
            name: Name of the secret
            agent_id: ID of the requesting agent
            agent_type: Type of the requesting agent

        Returns:
            Decrypted secret value

        Raises:
            SecretNotFound: If secret doesn't exist
            SecretAccessDenied: If agent doesn't have permission
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM secrets WHERE name = ?",
                (name,)
            ).fetchone()

            if not row:
                self._log_access(name, agent_id, agent_type, "get", False)
                raise SecretNotFound(f"Secret not found: {name}")

            # Check expiration
            if row['expires_at']:
                expires = datetime.fromisoformat(row['expires_at'])
                if datetime.now() > expires:
                    self._log_access(name, agent_id, agent_type, "get", False)
                    raise SecretNotFound(f"Secret expired: {name}")

            # Check access control
            allowed = json.loads(row['allowed_agents'])
            if "*" not in allowed and agent_type not in allowed:
                self._log_access(name, agent_id, agent_type, "get", False)
                raise SecretAccessDenied(
                    f"Agent type '{agent_type}' not allowed to access secret '{name}'"
                )

            # Log successful access
            self._log_access(name, agent_id, agent_type, "get", True)

            return self._decrypt(row['encrypted_value'])

    def get_secret_or_env(
        self,
        name: str,
        env_var: Optional[str] = None,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Get secret from store or fallback to environment variable.

        Args:
            name: Secret name
            env_var: Environment variable to check (defaults to upper(name))
            agent_id: Requesting agent ID
            agent_type: Requesting agent type

        Returns:
            Secret value or None if not found
        """
        try:
            return self.get_secret(name, agent_id, agent_type)
        except (SecretNotFound, SecretAccessDenied):
            # Fallback to environment variable
            env_name = env_var or name.upper().replace("-", "_")
            return os.environ.get(env_name)

    def delete_secret(self, name: str):
        """Delete a secret."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM secrets WHERE name = ?", (name,))
            conn.commit()
        logger.info(f"Deleted secret: {name}")

    def list_secrets(self) -> List[Dict[str, Any]]:
        """List all secrets (without values)."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT name, description, allowed_agents, created_at,
                       updated_at, expires_at, rotation_interval_days, last_rotated
                FROM secrets
            """).fetchall()

            return [
                {
                    "name": row['name'],
                    "description": row['description'],
                    "allowed_agents": json.loads(row['allowed_agents']),
                    "created_at": row['created_at'],
                    "updated_at": row['updated_at'],
                    "expires_at": row['expires_at'],
                    "needs_rotation": self._needs_rotation(row)
                }
                for row in rows
            ]

    def _needs_rotation(self, row: sqlite3.Row) -> bool:
        """Check if a secret needs rotation."""
        if not row['rotation_interval_days']:
            return False

        last_rotated = row['last_rotated'] or row['created_at']
        if not last_rotated:
            return True

        last = datetime.fromisoformat(last_rotated)
        interval = timedelta(days=row['rotation_interval_days'])

        return datetime.now() > (last + interval)

    def mark_rotated(self, name: str):
        """Mark a secret as rotated."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE secrets
                SET last_rotated = CURRENT_TIMESTAMP
                WHERE name = ?
            """, (name,))
            conn.commit()

    def get_secrets_needing_rotation(self) -> List[str]:
        """Get list of secrets that need rotation."""
        secrets = self.list_secrets()
        return [s['name'] for s in secrets if s.get('needs_rotation')]

    def _log_access(
        self,
        secret_name: str,
        agent_id: Optional[str],
        agent_type: Optional[str],
        action: str,
        success: bool
    ):
        """Log secret access for auditing."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO access_log
                (secret_name, agent_id, agent_type, action, success)
                VALUES (?, ?, ?, ?, ?)
            """, (secret_name, agent_id, agent_type, action, 1 if success else 0))
            conn.commit()

    def get_access_log(
        self,
        secret_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get access audit log."""
        with self._get_connection() as conn:
            if secret_name:
                rows = conn.execute("""
                    SELECT * FROM access_log
                    WHERE secret_name = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (secret_name, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM access_log
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,)).fetchall()

            return [dict(row) for row in rows]

    def import_from_env(self, mappings: Dict[str, str]):
        """
        Import secrets from environment variables.

        Args:
            mappings: Dict of secret_name -> env_var_name
        """
        for secret_name, env_var in mappings.items():
            value = os.environ.get(env_var)
            if value:
                self.store_secret(
                    secret_name,
                    value,
                    description=f"Imported from {env_var}"
                )
                logger.info(f"Imported secret from {env_var}")


# Global instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get the global secrets manager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


# Convenience function for tools
def get_api_key(
    provider: str,
    agent_id: Optional[str] = None,
    agent_type: Optional[str] = None
) -> Optional[str]:
    """Get an API key for a provider."""
    manager = get_secrets_manager()

    # Map provider to secret/env names
    mappings = {
        "anthropic": ("anthropic_api_key", "ANTHROPIC_API_KEY"),
        "openai": ("openai_api_key", "OPENAI_API_KEY"),
        "google": ("google_api_key", "GOOGLE_API_KEY"),
    }

    if provider.lower() not in mappings:
        return None

    secret_name, env_var = mappings[provider.lower()]

    return manager.get_secret_or_env(
        secret_name,
        env_var,
        agent_id,
        agent_type
    )
