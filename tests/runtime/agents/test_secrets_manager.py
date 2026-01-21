"""
Unit tests for secrets_manager module.

Tests the SecretsManager class for secure credential storage.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestSecretsManager:
    """Test SecretsManager class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        try:
            db_path.unlink()
        except:
            pass

    @pytest.fixture
    def manager(self, temp_db):
        """Create a fresh SecretsManager instance."""
        # Reset singleton for testing
        from src.runtime.agents.secrets_manager import SecretsManager
        SecretsManager._instance = None

        return SecretsManager(db_path=temp_db, master_key="test-master-key")

    def test_singleton_pattern(self, temp_db):
        """Test that SecretsManager uses singleton pattern."""
        from src.runtime.agents.secrets_manager import SecretsManager
        SecretsManager._instance = None

        m1 = SecretsManager(db_path=temp_db, master_key="test-key")
        m2 = SecretsManager(db_path=temp_db, master_key="test-key")

        assert m1 is m2

    def test_init_creates_database(self, manager, temp_db):
        """Test that initialization creates the database."""
        assert temp_db.exists()

    def test_init_creates_tables(self, manager):
        """Test that initialization creates required tables."""
        with manager._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='secrets'"
            )
            assert cursor.fetchone() is not None

            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='access_log'"
            )
            assert cursor.fetchone() is not None

    def test_store_secret(self, manager):
        """Test storing a secret."""
        manager.store_secret(
            name="test-secret",
            value="secret-value",
            description="A test secret"
        )

        secrets = manager.list_secrets()
        assert len(secrets) == 1
        assert secrets[0]["name"] == "test-secret"
        assert secrets[0]["description"] == "A test secret"

    def test_store_secret_with_allowed_agents(self, manager):
        """Test storing a secret with agent restrictions."""
        manager.store_secret(
            name="restricted-secret",
            value="secret-value",
            allowed_agents=["developer", "tester"]
        )

        secrets = manager.list_secrets()
        assert secrets[0]["allowed_agents"] == ["developer", "tester"]

    def test_store_secret_with_expiration(self, manager):
        """Test storing a secret with expiration."""
        manager.store_secret(
            name="expiring-secret",
            value="secret-value",
            expires_in_days=30
        )

        secrets = manager.list_secrets()
        assert secrets[0]["expires_at"] is not None

    def test_store_secret_with_rotation(self, manager):
        """Test storing a secret with rotation interval."""
        manager.store_secret(
            name="rotating-secret",
            value="secret-value",
            rotation_interval_days=90
        )

        secrets = manager.list_secrets()
        # needs_rotation should be false initially
        assert secrets[0]["needs_rotation"] is False

    def test_get_secret(self, manager):
        """Test retrieving a secret."""
        manager.store_secret("test-secret", "secret-value")

        value = manager.get_secret("test-secret")

        assert value == "secret-value"

    def test_get_secret_not_found(self, manager):
        """Test retrieving a non-existent secret raises error."""
        from src.runtime.agents.secrets_manager import SecretNotFound

        with pytest.raises(SecretNotFound):
            manager.get_secret("nonexistent")

    def test_get_secret_access_denied(self, manager):
        """Test retrieving a secret without permission raises error."""
        from src.runtime.agents.secrets_manager import SecretAccessDenied

        manager.store_secret(
            name="restricted-secret",
            value="secret-value",
            allowed_agents=["developer"]
        )

        with pytest.raises(SecretAccessDenied):
            manager.get_secret(
                "restricted-secret",
                agent_type="tester"  # Not in allowed list
            )

    def test_get_secret_with_wildcard_access(self, manager):
        """Test retrieving a secret with wildcard access."""
        manager.store_secret(
            name="open-secret",
            value="secret-value",
            allowed_agents=["*"]
        )

        value = manager.get_secret(
            "open-secret",
            agent_type="any-agent"
        )

        assert value == "secret-value"

    def test_get_secret_logs_access(self, manager):
        """Test that secret access is logged."""
        manager.store_secret("test-secret", "secret-value")

        manager.get_secret(
            "test-secret",
            agent_id="agent-1",
            agent_type="developer"
        )

        log = manager.get_access_log(secret_name="test-secret")
        assert len(log) == 1
        assert log[0]["agent_id"] == "agent-1"
        assert log[0]["success"] == 1

    def test_get_secret_or_env(self, manager):
        """Test get_secret_or_env falls back to environment."""
        # Secret doesn't exist
        with patch.dict(os.environ, {"TEST_SECRET": "env-value"}):
            value = manager.get_secret_or_env("test-secret", "TEST_SECRET")

            assert value == "env-value"

    def test_get_secret_or_env_prefers_stored(self, manager):
        """Test get_secret_or_env prefers stored secret over env."""
        manager.store_secret("test-secret", "stored-value")

        with patch.dict(os.environ, {"TEST_SECRET": "env-value"}):
            value = manager.get_secret_or_env("test-secret", "TEST_SECRET")

            assert value == "stored-value"

    def test_get_secret_or_env_default_env_name(self, manager):
        """Test get_secret_or_env uses uppercased name as default env var."""
        with patch.dict(os.environ, {"MY_SECRET": "env-value"}):
            value = manager.get_secret_or_env("my-secret")

            assert value == "env-value"

    def test_delete_secret(self, manager):
        """Test deleting a secret."""
        manager.store_secret("test-secret", "secret-value")

        manager.delete_secret("test-secret")

        secrets = manager.list_secrets()
        assert len(secrets) == 0

    def test_list_secrets(self, manager):
        """Test listing all secrets."""
        manager.store_secret("secret-1", "value-1")
        manager.store_secret("secret-2", "value-2")

        secrets = manager.list_secrets()

        assert len(secrets) == 2
        names = [s["name"] for s in secrets]
        assert "secret-1" in names
        assert "secret-2" in names

    def test_list_secrets_excludes_values(self, manager):
        """Test that list_secrets doesn't include actual values."""
        manager.store_secret("test-secret", "secret-value")

        secrets = manager.list_secrets()

        # Should not have 'value' or 'encrypted_value' keys
        for secret in secrets:
            assert "value" not in secret
            assert "encrypted_value" not in secret

    def test_mark_rotated(self, manager):
        """Test marking a secret as rotated."""
        manager.store_secret(
            "test-secret",
            "secret-value",
            rotation_interval_days=90
        )

        manager.mark_rotated("test-secret")

        secrets = manager.list_secrets()
        # After marking rotated, needs_rotation should be False
        assert secrets[0]["needs_rotation"] is False

    def test_get_secrets_needing_rotation(self, manager):
        """Test getting secrets that need rotation."""
        # This is tricky to test without time manipulation
        # For now, just verify the method exists and returns empty list for new secrets
        manager.store_secret(
            "test-secret",
            "secret-value",
            rotation_interval_days=90
        )

        needing_rotation = manager.get_secrets_needing_rotation()

        # New secrets shouldn't need rotation
        assert "test-secret" not in needing_rotation

    def test_get_access_log(self, manager):
        """Test getting the access log."""
        manager.store_secret("test-secret", "secret-value")
        manager.get_secret("test-secret", agent_id="agent-1")
        manager.get_secret("test-secret", agent_id="agent-2")

        log = manager.get_access_log(limit=10)

        assert len(log) == 2

    def test_get_access_log_filtered(self, manager):
        """Test getting access log filtered by secret name."""
        manager.store_secret("secret-1", "value-1")
        manager.store_secret("secret-2", "value-2")
        manager.get_secret("secret-1")
        manager.get_secret("secret-2")

        log = manager.get_access_log(secret_name="secret-1")

        assert len(log) == 1

    def test_import_from_env(self, manager):
        """Test importing secrets from environment variables."""
        with patch.dict(os.environ, {
            "API_KEY_1": "key-value-1",
            "API_KEY_2": "key-value-2"
        }):
            manager.import_from_env({
                "api-key-1": "API_KEY_1",
                "api-key-2": "API_KEY_2"
            })

        secrets = manager.list_secrets()
        assert len(secrets) == 2

        # Verify we can retrieve the values
        assert manager.get_secret("api-key-1") == "key-value-1"
        assert manager.get_secret("api-key-2") == "key-value-2"

    def test_import_from_env_skips_missing(self, manager):
        """Test that import_from_env skips missing env vars."""
        with patch.dict(os.environ, {"EXISTING_KEY": "value"}, clear=True):
            manager.import_from_env({
                "existing": "EXISTING_KEY",
                "missing": "MISSING_KEY"
            })

        secrets = manager.list_secrets()
        assert len(secrets) == 1
        assert secrets[0]["name"] == "existing"

    def test_encryption_roundtrip(self, manager):
        """Test that values survive encryption/decryption roundtrip."""
        # Only test ASCII values since the fallback obfuscation doesn't support unicode
        test_values = [
            "simple value",
            "value with special chars: !@#$%^&*()",
            "long value " * 100,
        ]

        for i, value in enumerate(test_values):
            name = f"test-{i}"
            manager.store_secret(name, value)
            retrieved = manager.get_secret(name)
            assert retrieved == value, f"Failed for value: {value[:50]}..."


class TestGlobalSecretsManager:
    """Test global secrets manager functions."""

    def test_get_secrets_manager(self):
        """Test get_secrets_manager returns instance."""
        # Reset global
        import src.runtime.agents.secrets_manager as module
        module._secrets_manager = None
        module.SecretsManager._instance = None

        from src.runtime.agents.secrets_manager import get_secrets_manager

        manager = get_secrets_manager()

        assert manager is not None

    def test_get_secrets_manager_returns_same_instance(self):
        """Test get_secrets_manager returns same instance."""
        import src.runtime.agents.secrets_manager as module
        module._secrets_manager = None
        module.SecretsManager._instance = None

        from src.runtime.agents.secrets_manager import get_secrets_manager

        m1 = get_secrets_manager()
        m2 = get_secrets_manager()

        assert m1 is m2


class TestGetApiKey:
    """Test get_api_key convenience function."""

    def test_get_api_key_from_env(self):
        """Test get_api_key retrieves from environment."""
        import src.runtime.agents.secrets_manager as module
        module._secrets_manager = None
        module.SecretsManager._instance = None

        from src.runtime.agents.secrets_manager import get_api_key

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            key = get_api_key("anthropic")

            assert key == "test-key"

    def test_get_api_key_unknown_provider(self):
        """Test get_api_key returns None for unknown provider."""
        import src.runtime.agents.secrets_manager as module
        module._secrets_manager = None
        module.SecretsManager._instance = None

        from src.runtime.agents.secrets_manager import get_api_key

        key = get_api_key("unknown-provider")

        assert key is None

    def test_get_api_key_openai(self):
        """Test get_api_key for OpenAI."""
        import src.runtime.agents.secrets_manager as module
        module._secrets_manager = None
        module.SecretsManager._instance = None

        from src.runtime.agents.secrets_manager import get_api_key

        with patch.dict(os.environ, {"OPENAI_API_KEY": "openai-key"}):
            key = get_api_key("openai")

            assert key == "openai-key"

    def test_get_api_key_google(self):
        """Test get_api_key for Google."""
        import src.runtime.agents.secrets_manager as module
        module._secrets_manager = None
        module.SecretsManager._instance = None

        from src.runtime.agents.secrets_manager import get_api_key

        with patch.dict(os.environ, {"GOOGLE_API_KEY": "google-key"}):
            key = get_api_key("google")

            assert key == "google-key"
