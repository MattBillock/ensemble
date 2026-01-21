"""
Unit tests for websocket_manager module.

Tests the WebSocketEventManager class for real-time event streaming.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime


class TestEventType:
    """Test EventType enum."""

    def test_event_types_exist(self):
        """Test that all expected event types exist."""
        from src.runtime.agents.websocket_manager import EventType

        # Agent lifecycle events
        assert EventType.AGENT_SPAWNED.value == "agent_spawned"
        assert EventType.AGENT_COMPLETED.value == "agent_completed"
        assert EventType.AGENT_FAILED.value == "agent_failed"
        assert EventType.AGENT_STALLED.value == "agent_stalled"
        assert EventType.AGENT_RECOVERED.value == "agent_recovered"

        # Activity events
        assert EventType.ITERATION_STARTED.value == "iteration_started"
        assert EventType.ITERATION_COMPLETED.value == "iteration_completed"
        assert EventType.TOOL_USE.value == "tool_use"

        # Question events
        assert EventType.QUESTION_ASKED.value == "question_asked"
        assert EventType.QUESTION_ANSWERED.value == "question_answered"

        # File events
        assert EventType.FILE_CREATED.value == "file_created"
        assert EventType.FILE_MODIFIED.value == "file_modified"

        # System events
        assert EventType.HEARTBEAT.value == "heartbeat"
        assert EventType.ERROR.value == "error"


class TestWebSocketClient:
    """Test WebSocketClient dataclass."""

    def test_client_creation(self):
        """Test creating a WebSocketClient."""
        from src.runtime.agents.websocket_manager import WebSocketClient, EventType

        mock_ws = MagicMock()
        client = WebSocketClient(
            websocket=mock_ws,
            client_id="test-client"
        )

        assert client.client_id == "test-client"
        assert client.subscriptions == set()
        assert client.filters == {}

    def test_client_with_subscriptions(self):
        """Test creating a client with subscriptions."""
        from src.runtime.agents.websocket_manager import WebSocketClient, EventType

        mock_ws = MagicMock()
        client = WebSocketClient(
            websocket=mock_ws,
            client_id="test-client",
            subscriptions={EventType.AGENT_SPAWNED, EventType.AGENT_COMPLETED}
        )

        assert EventType.AGENT_SPAWNED in client.subscriptions
        assert EventType.AGENT_COMPLETED in client.subscriptions

    def test_client_with_filters(self):
        """Test creating a client with filters."""
        from src.runtime.agents.websocket_manager import WebSocketClient

        mock_ws = MagicMock()
        client = WebSocketClient(
            websocket=mock_ws,
            client_id="test-client",
            filters={"request_id": "req-123"}
        )

        assert client.filters["request_id"] == "req-123"

    def test_matches_event_by_type(self):
        """Test client event matching by type."""
        from src.runtime.agents.websocket_manager import WebSocketClient, EventType

        mock_ws = MagicMock()
        client = WebSocketClient(
            websocket=mock_ws,
            client_id="test-client",
            subscriptions={EventType.AGENT_SPAWNED}
        )

        matching_event = {"type": "agent_spawned", "data": {}}
        non_matching_event = {"type": "agent_failed", "data": {}}

        assert client.matches_event(matching_event) is True
        assert client.matches_event(non_matching_event) is False

    def test_matches_event_by_filter(self):
        """Test client event matching by filter."""
        from src.runtime.agents.websocket_manager import WebSocketClient, EventType

        mock_ws = MagicMock()
        client = WebSocketClient(
            websocket=mock_ws,
            client_id="test-client",
            subscriptions={EventType.AGENT_SPAWNED},
            filters={"request_id": "req-123"}
        )

        matching_event = {
            "type": "agent_spawned",
            "data": {"request_id": "req-123"}
        }
        non_matching_event = {
            "type": "agent_spawned",
            "data": {"request_id": "req-456"}
        }

        assert client.matches_event(matching_event) is True
        assert client.matches_event(non_matching_event) is False


class TestWebSocketEventManager:
    """Test WebSocketEventManager class."""

    @pytest.fixture
    def manager(self):
        """Create a WebSocketEventManager instance."""
        from src.runtime.agents.websocket_manager import WebSocketEventManager
        return WebSocketEventManager(
            buffer_size=10,
            heartbeat_interval=5.0,
            client_timeout=60.0
        )

    def test_init(self, manager):
        """Test WebSocketEventManager initialization."""
        assert manager.clients == {}
        assert len(manager.event_buffer) == 0
        assert manager._running is False

    @pytest.mark.asyncio
    async def test_start(self, manager):
        """Test starting the WebSocket manager."""
        await manager.start()

        assert manager._running is True
        assert manager._heartbeat_task is not None
        assert manager._cleanup_task is not None

        # Cleanup
        await manager.stop()

    @pytest.mark.asyncio
    async def test_stop(self, manager):
        """Test stopping the WebSocket manager."""
        await manager.start()
        await manager.stop()

        assert manager._running is False
        assert len(manager.clients) == 0

    @pytest.mark.asyncio
    async def test_register_client(self, manager):
        """Test registering a WebSocket client."""
        mock_ws = AsyncMock()

        client_id = await manager.register_client(mock_ws)

        assert client_id is not None
        assert client_id in manager.clients
        assert manager.clients[client_id].websocket == mock_ws

    @pytest.mark.asyncio
    async def test_register_client_with_subscriptions(self, manager):
        """Test registering a client with specific subscriptions."""
        from src.runtime.agents.websocket_manager import EventType

        mock_ws = AsyncMock()

        client_id = await manager.register_client(
            mock_ws,
            subscriptions={EventType.AGENT_SPAWNED}
        )

        client = manager.clients[client_id]
        assert EventType.AGENT_SPAWNED in client.subscriptions

    @pytest.mark.asyncio
    async def test_register_client_with_filters(self, manager):
        """Test registering a client with filters."""
        mock_ws = AsyncMock()

        client_id = await manager.register_client(
            mock_ws,
            filters={"request_id": "req-123"}
        )

        client = manager.clients[client_id]
        assert client.filters["request_id"] == "req-123"

    @pytest.mark.asyncio
    async def test_unregister_client(self, manager):
        """Test unregistering a WebSocket client."""
        mock_ws = AsyncMock()
        client_id = await manager.register_client(mock_ws)

        await manager.unregister_client(client_id)

        assert client_id not in manager.clients

    @pytest.mark.asyncio
    async def test_update_subscriptions(self, manager):
        """Test updating client subscriptions."""
        from src.runtime.agents.websocket_manager import EventType

        mock_ws = AsyncMock()
        client_id = await manager.register_client(mock_ws)

        await manager.update_subscriptions(
            client_id,
            subscriptions={EventType.AGENT_FAILED},
            filters={"agent_id": "agent-1"}
        )

        client = manager.clients[client_id]
        assert EventType.AGENT_FAILED in client.subscriptions
        assert client.filters["agent_id"] == "agent-1"

    @pytest.mark.asyncio
    async def test_broadcast_event(self, manager):
        """Test broadcasting an event to clients."""
        from src.runtime.agents.websocket_manager import EventType

        mock_ws = AsyncMock()
        await manager.register_client(
            mock_ws,
            subscriptions={EventType.AGENT_SPAWNED}
        )

        await manager.broadcast_event(
            EventType.AGENT_SPAWNED,
            {"agent_id": "test-agent"}
        )

        # Check event was sent
        mock_ws.send_json.assert_called_once()
        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "agent_spawned"
        assert call_args["data"]["agent_id"] == "test-agent"

    @pytest.mark.asyncio
    async def test_broadcast_event_buffers(self, manager):
        """Test that events are buffered."""
        from src.runtime.agents.websocket_manager import EventType

        await manager.broadcast_event(
            EventType.AGENT_SPAWNED,
            {"agent_id": "test-agent"},
            buffer=True
        )

        assert len(manager.event_buffer) == 1
        assert manager.event_buffer[0]["type"] == "agent_spawned"

    @pytest.mark.asyncio
    async def test_broadcast_event_no_buffer(self, manager):
        """Test that events can skip buffering."""
        from src.runtime.agents.websocket_manager import EventType

        await manager.broadcast_event(
            EventType.HEARTBEAT,
            {},
            buffer=False
        )

        assert len(manager.event_buffer) == 0

    @pytest.mark.asyncio
    async def test_broadcast_event_filters_clients(self, manager):
        """Test that events are filtered by client subscriptions."""
        from src.runtime.agents.websocket_manager import EventType

        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        await manager.register_client(
            mock_ws1,
            subscriptions={EventType.AGENT_SPAWNED}
        )
        await manager.register_client(
            mock_ws2,
            subscriptions={EventType.AGENT_FAILED}
        )

        await manager.broadcast_event(
            EventType.AGENT_SPAWNED,
            {"agent_id": "test-agent"}
        )

        mock_ws1.send_json.assert_called_once()
        mock_ws2.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_event_handles_disconnected_client(self, manager):
        """Test that disconnected clients are cleaned up."""
        from src.runtime.agents.websocket_manager import EventType

        mock_ws = AsyncMock()
        mock_ws.send_json.side_effect = Exception("Connection closed")

        client_id = await manager.register_client(
            mock_ws,
            subscriptions={EventType.AGENT_SPAWNED}
        )

        await manager.broadcast_event(
            EventType.AGENT_SPAWNED,
            {"agent_id": "test-agent"}
        )

        assert client_id not in manager.clients

    @pytest.mark.asyncio
    async def test_send_to_client(self, manager):
        """Test sending event to a specific client."""
        from src.runtime.agents.websocket_manager import EventType

        mock_ws = AsyncMock()
        client_id = await manager.register_client(mock_ws)

        result = await manager.send_to_client(
            client_id,
            EventType.STATUS_UPDATE,
            {"status": "test"}
        )

        assert result is True
        mock_ws.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_client_not_found(self, manager):
        """Test sending to non-existent client returns False."""
        from src.runtime.agents.websocket_manager import EventType

        result = await manager.send_to_client(
            "nonexistent",
            EventType.STATUS_UPDATE,
            {}
        )

        assert result is False

    def test_add_event_hook(self, manager):
        """Test adding an event hook."""
        def test_hook(event):
            pass

        manager.add_event_hook(test_hook)

        assert test_hook in manager._event_hooks

    def test_remove_event_hook(self, manager):
        """Test removing an event hook."""
        def test_hook(event):
            pass

        manager.add_event_hook(test_hook)
        manager.remove_event_hook(test_hook)

        assert test_hook not in manager._event_hooks

    @pytest.mark.asyncio
    async def test_event_hooks_called(self, manager):
        """Test that event hooks are called on broadcast."""
        from src.runtime.agents.websocket_manager import EventType

        hook_called = []

        async def test_hook(event):
            hook_called.append(event)

        manager.add_event_hook(test_hook)

        await manager.broadcast_event(
            EventType.AGENT_SPAWNED,
            {"agent_id": "test"}
        )

        assert len(hook_called) == 1
        assert hook_called[0]["type"] == "agent_spawned"

    def test_get_stats(self, manager):
        """Test getting manager statistics."""
        stats = manager.get_stats()

        assert "connected_clients" in stats
        assert "buffered_events" in stats
        assert "is_running" in stats
        assert "clients" in stats


class TestGlobalManager:
    """Test global WebSocket manager functions."""

    def test_get_websocket_manager(self):
        """Test get_websocket_manager returns instance."""
        # Reset global
        import src.runtime.agents.websocket_manager as module
        module._ws_manager = None

        from src.runtime.agents.websocket_manager import get_websocket_manager

        manager = get_websocket_manager()

        assert manager is not None

    def test_get_websocket_manager_returns_same_instance(self):
        """Test get_websocket_manager returns same instance."""
        import src.runtime.agents.websocket_manager as module
        module._ws_manager = None

        from src.runtime.agents.websocket_manager import get_websocket_manager

        m1 = get_websocket_manager()
        m2 = get_websocket_manager()

        assert m1 is m2


class TestHelperFunctions:
    """Test helper emit functions."""

    @pytest.mark.asyncio
    async def test_emit_agent_spawned(self):
        """Test emit_agent_spawned helper."""
        import src.runtime.agents.websocket_manager as module
        module._ws_manager = None

        from src.runtime.agents.websocket_manager import (
            emit_agent_spawned,
            get_websocket_manager
        )

        manager = get_websocket_manager()
        mock_ws = AsyncMock()
        await manager.register_client(mock_ws)

        await emit_agent_spawned(
            agent_id="agent-1",
            agent_name="Test Agent",
            agent_type="developer",
            parent_id="parent-1",
            request_id="req-1"
        )

        mock_ws.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_emit_agent_completed(self):
        """Test emit_agent_completed helper."""
        import src.runtime.agents.websocket_manager as module
        module._ws_manager = None

        from src.runtime.agents.websocket_manager import (
            emit_agent_completed,
            get_websocket_manager
        )

        manager = get_websocket_manager()
        mock_ws = AsyncMock()
        await manager.register_client(mock_ws)

        await emit_agent_completed(
            agent_id="agent-1",
            agent_name="Test Agent",
            result_status="success",
            duration_ms=1000
        )

        mock_ws.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_emit_agent_failed(self):
        """Test emit_agent_failed helper."""
        import src.runtime.agents.websocket_manager as module
        module._ws_manager = None

        from src.runtime.agents.websocket_manager import (
            emit_agent_failed,
            get_websocket_manager
        )

        manager = get_websocket_manager()
        mock_ws = AsyncMock()
        await manager.register_client(mock_ws)

        await emit_agent_failed(
            agent_id="agent-1",
            agent_name="Test Agent",
            error_message="Something went wrong"
        )

        mock_ws.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_emit_tool_use(self):
        """Test emit_tool_use helper."""
        import src.runtime.agents.websocket_manager as module
        module._ws_manager = None

        from src.runtime.agents.websocket_manager import (
            emit_tool_use,
            get_websocket_manager
        )

        manager = get_websocket_manager()
        mock_ws = AsyncMock()
        await manager.register_client(mock_ws)

        await emit_tool_use(
            agent_id="agent-1",
            tool_name="write_file",
            tool_input={"path": "/test.py"}
        )

        mock_ws.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_emit_status_update(self):
        """Test emit_status_update helper."""
        import src.runtime.agents.websocket_manager as module
        module._ws_manager = None

        from src.runtime.agents.websocket_manager import (
            emit_status_update,
            get_websocket_manager
        )

        manager = get_websocket_manager()
        mock_ws = AsyncMock()
        await manager.register_client(mock_ws)

        await emit_status_update(
            status="active",
            details={"agents_running": 5}
        )

        mock_ws.send_json.assert_called()
