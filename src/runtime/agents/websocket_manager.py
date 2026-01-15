"""
WebSocket Event Manager - Real-time event streaming for the Ensemble UI.

Provides centralized WebSocket management with:
- Event type filtering and subscriptions
- Broadcast to multiple clients
- Event buffering for reconnection
- Heartbeat and connection health monitoring
"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from collections import deque

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events that can be streamed via WebSocket."""
    # Agent lifecycle events
    AGENT_SPAWNED = "agent_spawned"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    AGENT_STALLED = "agent_stalled"
    AGENT_RECOVERED = "agent_recovered"

    # Activity events
    ITERATION_STARTED = "iteration_started"
    ITERATION_COMPLETED = "iteration_completed"
    TOOL_USE = "tool_use"

    # Question events
    QUESTION_ASKED = "question_asked"
    QUESTION_ANSWERED = "question_answered"

    # File events
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"

    # Recovery events
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETED = "recovery_completed"
    RECOVERY_FAILED = "recovery_failed"

    # System events
    STATUS_UPDATE = "status_update"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


@dataclass
class WebSocketClient:
    """Represents a connected WebSocket client."""
    websocket: Any  # FastAPI WebSocket object
    client_id: str
    subscriptions: Set[EventType] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    filters: Dict[str, Any] = field(default_factory=dict)  # e.g., {"request_id": "abc123"}

    def matches_event(self, event: Dict[str, Any]) -> bool:
        """Check if this client should receive this event."""
        # Check event type subscription
        event_type = event.get("type")
        if event_type:
            try:
                if EventType(event_type) not in self.subscriptions:
                    return False
            except ValueError:
                pass  # Unknown event type, let it through

        # Check filters
        for key, value in self.filters.items():
            if key in event.get("data", {}) and event["data"][key] != value:
                return False

        return True


class WebSocketEventManager:
    """
    Manages WebSocket connections and event broadcasting.

    Features:
    - Multiple client connections with individual subscriptions
    - Event buffering for reconnection
    - Heartbeat monitoring
    - Event filtering by request_id, agent_id, etc.
    """

    def __init__(
        self,
        buffer_size: int = 100,
        heartbeat_interval: float = 30.0,
        client_timeout: float = 120.0
    ):
        self.clients: Dict[str, WebSocketClient] = {}
        self.event_buffer: deque = deque(maxlen=buffer_size)
        self.heartbeat_interval = heartbeat_interval
        self.client_timeout = client_timeout
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._client_counter = 0

        # Event callbacks for external integrations
        self._event_hooks: List[Callable] = []

    async def start(self):
        """Start the WebSocket manager background tasks."""
        if self._running:
            return

        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("WebSocket event manager started")

    async def stop(self):
        """Stop the WebSocket manager and close all connections."""
        self._running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Close all client connections
        for client in list(self.clients.values()):
            try:
                await client.websocket.close()
            except:
                pass

        self.clients.clear()
        logger.info("WebSocket event manager stopped")

    async def register_client(
        self,
        websocket: Any,
        subscriptions: Optional[Set[EventType]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a new WebSocket client.

        Returns the client_id for future reference.
        """
        async with self._lock:
            self._client_counter += 1
            client_id = f"ws_{self._client_counter}_{int(time.time())}"

            # Default to all event types if none specified
            if subscriptions is None:
                subscriptions = set(EventType)

            client = WebSocketClient(
                websocket=websocket,
                client_id=client_id,
                subscriptions=subscriptions,
                filters=filters or {}
            )

            self.clients[client_id] = client

        logger.info(f"WebSocket client registered: {client_id} with {len(subscriptions)} subscriptions")

        # Send any buffered events that match the client's subscriptions
        await self._send_buffered_events(client)

        return client_id

    async def unregister_client(self, client_id: str):
        """Unregister a WebSocket client."""
        async with self._lock:
            if client_id in self.clients:
                del self.clients[client_id]
                logger.info(f"WebSocket client unregistered: {client_id}")

    async def update_subscriptions(
        self,
        client_id: str,
        subscriptions: Set[EventType],
        filters: Optional[Dict[str, Any]] = None
    ):
        """Update a client's subscriptions and filters."""
        async with self._lock:
            if client_id in self.clients:
                self.clients[client_id].subscriptions = subscriptions
                if filters is not None:
                    self.clients[client_id].filters = filters
                logger.debug(f"Updated subscriptions for {client_id}")

    async def broadcast_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        buffer: bool = True
    ):
        """
        Broadcast an event to all subscribed clients.

        Args:
            event_type: Type of event being broadcast
            data: Event payload data
            buffer: Whether to add this event to the buffer for reconnecting clients
        """
        event = {
            "type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        # Add to buffer
        if buffer:
            self.event_buffer.append(event)

        # Call event hooks
        for hook in self._event_hooks:
            try:
                await hook(event)
            except Exception as e:
                logger.error(f"Event hook error: {e}")

        # Broadcast to matching clients
        disconnected_clients = []

        for client_id, client in list(self.clients.items()):
            if not client.matches_event(event):
                continue

            try:
                await client.websocket.send_json(event)
                client.last_activity = datetime.now()
            except Exception as e:
                logger.warning(f"Failed to send to client {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.unregister_client(client_id)

    async def send_to_client(
        self,
        client_id: str,
        event_type: EventType,
        data: Dict[str, Any]
    ) -> bool:
        """Send an event to a specific client."""
        if client_id not in self.clients:
            return False

        client = self.clients[client_id]
        event = {
            "type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        try:
            await client.websocket.send_json(event)
            client.last_activity = datetime.now()
            return True
        except Exception as e:
            logger.warning(f"Failed to send to client {client_id}: {e}")
            await self.unregister_client(client_id)
            return False

    async def _send_buffered_events(self, client: WebSocketClient):
        """Send relevant buffered events to a newly connected client."""
        matching_events = [
            event for event in self.event_buffer
            if client.matches_event(event)
        ]

        if matching_events:
            # Send as a batch
            try:
                await client.websocket.send_json({
                    "type": "buffered_events",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "events": matching_events,
                        "count": len(matching_events)
                    }
                })
                logger.debug(f"Sent {len(matching_events)} buffered events to {client.client_id}")
            except Exception as e:
                logger.warning(f"Failed to send buffered events: {e}")

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to keep connections alive."""
        while self._running:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                await self.broadcast_event(
                    EventType.HEARTBEAT,
                    {
                        "connected_clients": len(self.clients),
                        "buffer_size": len(self.event_buffer)
                    },
                    buffer=False
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")

    async def _cleanup_loop(self):
        """Periodically clean up stale connections."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute

                now = datetime.now()
                stale_clients = []

                for client_id, client in list(self.clients.items()):
                    if (now - client.last_activity).total_seconds() > self.client_timeout:
                        stale_clients.append(client_id)

                for client_id in stale_clients:
                    logger.info(f"Cleaning up stale client: {client_id}")
                    await self.unregister_client(client_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

    def add_event_hook(self, hook: Callable):
        """Add a callback that's called for every event."""
        self._event_hooks.append(hook)

    def remove_event_hook(self, hook: Callable):
        """Remove an event callback."""
        if hook in self._event_hooks:
            self._event_hooks.remove(hook)

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics."""
        return {
            "connected_clients": len(self.clients),
            "buffered_events": len(self.event_buffer),
            "is_running": self._running,
            "clients": [
                {
                    "client_id": client.client_id,
                    "connected_at": client.connected_at.isoformat(),
                    "last_activity": client.last_activity.isoformat(),
                    "subscriptions": [s.value for s in client.subscriptions],
                    "filters": client.filters
                }
                for client in self.clients.values()
            ]
        }


# Global WebSocket manager instance
_ws_manager: Optional[WebSocketEventManager] = None


def get_websocket_manager() -> WebSocketEventManager:
    """Get or create the global WebSocket manager."""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketEventManager()
    return _ws_manager


# Helper functions for common event broadcasts

async def emit_agent_spawned(
    agent_id: str,
    agent_name: str,
    agent_type: str,
    parent_id: Optional[str] = None,
    request_id: Optional[str] = None,
    **kwargs
):
    """Emit an agent_spawned event."""
    manager = get_websocket_manager()
    await manager.broadcast_event(EventType.AGENT_SPAWNED, {
        "agent_id": agent_id,
        "agent_name": agent_name,
        "agent_type": agent_type,
        "parent_id": parent_id,
        "request_id": request_id,
        **kwargs
    })


async def emit_agent_completed(
    agent_id: str,
    agent_name: str,
    result_status: str,
    duration_ms: Optional[int] = None,
    request_id: Optional[str] = None,
    **kwargs
):
    """Emit an agent_completed event."""
    manager = get_websocket_manager()
    await manager.broadcast_event(EventType.AGENT_COMPLETED, {
        "agent_id": agent_id,
        "agent_name": agent_name,
        "result_status": result_status,
        "duration_ms": duration_ms,
        "request_id": request_id,
        **kwargs
    })


async def emit_agent_failed(
    agent_id: str,
    agent_name: str,
    error_message: str,
    request_id: Optional[str] = None,
    **kwargs
):
    """Emit an agent_failed event."""
    manager = get_websocket_manager()
    await manager.broadcast_event(EventType.AGENT_FAILED, {
        "agent_id": agent_id,
        "agent_name": agent_name,
        "error_message": error_message,
        "request_id": request_id,
        **kwargs
    })


async def emit_tool_use(
    agent_id: str,
    tool_name: str,
    tool_input: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    **kwargs
):
    """Emit a tool_use event."""
    manager = get_websocket_manager()
    await manager.broadcast_event(EventType.TOOL_USE, {
        "agent_id": agent_id,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "request_id": request_id,
        **kwargs
    })


async def emit_question_asked(
    question_id: str,
    agent_id: str,
    question_text: str,
    options: Optional[List[str]] = None,
    request_id: Optional[str] = None,
    **kwargs
):
    """Emit a question_asked event."""
    manager = get_websocket_manager()
    await manager.broadcast_event(EventType.QUESTION_ASKED, {
        "question_id": question_id,
        "agent_id": agent_id,
        "question_text": question_text,
        "options": options,
        "request_id": request_id,
        **kwargs
    })


async def emit_file_created(
    file_path: str,
    agent_id: str,
    file_type: Optional[str] = None,
    request_id: Optional[str] = None,
    **kwargs
):
    """Emit a file_created event."""
    manager = get_websocket_manager()
    await manager.broadcast_event(EventType.FILE_CREATED, {
        "file_path": file_path,
        "agent_id": agent_id,
        "file_type": file_type,
        "request_id": request_id,
        **kwargs
    })


async def emit_status_update(
    status: str,
    details: Dict[str, Any],
    **kwargs
):
    """Emit a general status_update event."""
    manager = get_websocket_manager()
    await manager.broadcast_event(EventType.STATUS_UPDATE, {
        "status": status,
        "details": details,
        **kwargs
    })


async def emit_recovery_event(
    event_type: EventType,
    agent_id: str,
    strategy: str,
    request_id: Optional[str] = None,
    **kwargs
):
    """Emit a recovery-related event."""
    manager = get_websocket_manager()
    await manager.broadcast_event(event_type, {
        "agent_id": agent_id,
        "strategy": strategy,
        "request_id": request_id,
        **kwargs
    })
