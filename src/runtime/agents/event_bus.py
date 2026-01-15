"""
Event Bus - Real-time inter-agent communication and UI broadcasting.

Provides pub/sub mechanism for agents to communicate with each other
and for the UI to receive real-time updates.
"""
import asyncio
import json
import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from queue import Queue, Empty
from typing import Any, Callable, Dict, List, Optional, Set
from weakref import WeakSet

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Standard event types for the swarm."""
    # Session events
    SESSION_CREATED = "session_created"
    SESSION_COMPLETED = "session_completed"
    SESSION_FAILED = "session_failed"
    SESSION_TITLE_UPDATED = "session_title_updated"

    # Agent lifecycle events
    AGENT_SPAWNED = "agent_spawned"
    AGENT_STARTED = "agent_started"
    AGENT_ITERATION = "agent_iteration"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    AGENT_STALLED = "agent_stalled"
    AGENT_RECOVERED = "agent_recovered"

    # Tool events
    TOOL_EXECUTED = "tool_executed"
    FILE_WRITTEN = "file_written"
    FILE_READ = "file_read"
    COMMAND_EXECUTED = "command_executed"

    # Git events
    GIT_COMMIT = "git_commit"
    GIT_BRANCH_CREATED = "git_branch_created"
    GIT_BRANCH_MERGED = "git_branch_merged"

    # Deliverable events
    DELIVERABLE_CREATED = "deliverable_created"

    # Cost events
    COST_UPDATED = "cost_updated"
    BUDGET_WARNING = "budget_warning"
    BUDGET_EXCEEDED = "budget_exceeded"

    # Recovery events
    RECOVERY_QUEUED = "recovery_queued"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETED = "recovery_completed"
    RECOVERY_FAILED = "recovery_failed"

    # Question events (for user interaction)
    QUESTION_ASKED = "question_asked"
    QUESTION_ANSWERED = "question_answered"

    # Custom/generic
    CUSTOM = "custom"


@dataclass
class Event:
    """An event in the event bus."""
    event_type: str
    payload: Dict[str, Any]
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    event_id: int = field(default_factory=lambda: int(time.time() * 1000000))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class EventSubscriber:
    """Base class for event subscribers."""

    def __init__(self, subscriber_id: str):
        self.subscriber_id = subscriber_id
        self.subscribed_types: Set[str] = set()
        self._queue: Queue = Queue(maxsize=1000)
        self._active = True

    def receive(self, event: Event):
        """Receive an event (called by EventBus)."""
        if not self._active:
            return

        try:
            self._queue.put_nowait(event)
        except Exception:
            # Queue full, drop oldest
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(event)
            except Empty:
                pass

    def get_events(self, timeout: float = 0.1, max_events: int = 100) -> List[Event]:
        """Get pending events for this subscriber."""
        events = []
        deadline = time.time() + timeout

        while len(events) < max_events and time.time() < deadline:
            try:
                event = self._queue.get(timeout=min(0.01, deadline - time.time()))
                events.append(event)
            except Empty:
                break

        return events

    def close(self):
        """Close this subscriber."""
        self._active = False


class AsyncEventSubscriber(EventSubscriber):
    """Async-compatible event subscriber."""

    def __init__(self, subscriber_id: str):
        super().__init__(subscriber_id)
        self._async_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)

    def receive(self, event: Event):
        """Receive an event (thread-safe for async)."""
        if not self._active:
            return

        try:
            self._async_queue.put_nowait(event)
        except asyncio.QueueFull:
            # Queue full, drop oldest
            try:
                self._async_queue.get_nowait()
                self._async_queue.put_nowait(event)
            except asyncio.QueueEmpty:
                pass

    async def get_events_async(self, timeout: float = 0.1, max_events: int = 100) -> List[Event]:
        """Get pending events asynchronously."""
        events = []
        deadline = time.time() + timeout

        while len(events) < max_events and time.time() < deadline:
            try:
                event = await asyncio.wait_for(
                    self._async_queue.get(),
                    timeout=min(0.01, deadline - time.time())
                )
                events.append(event)
            except asyncio.TimeoutError:
                break

        return events


class EventBus:
    """
    Central event bus for inter-agent communication and UI updates.

    Features:
    - Pub/sub pattern for decoupled communication
    - Type-based filtering
    - Session/agent-based filtering
    - Persistent event log (via SwarmStateManager)
    - Thread-safe operation
    """

    _instance: Optional["EventBus"] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._subscribers: Dict[str, EventSubscriber] = {}
        self._type_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # event_type -> subscriber_ids
        self._session_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # session_id -> subscriber_ids
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)  # event_type -> callbacks
        self._lock = threading.RLock()
        self._event_counter = 0
        self._persist_events = True  # Whether to persist to SwarmStateManager

        self._initialized = True
        logger.info("EventBus initialized")

    def subscribe(
        self,
        subscriber_id: str,
        event_types: Optional[List[str]] = None,
        session_ids: Optional[List[str]] = None,
        async_mode: bool = False
    ) -> EventSubscriber:
        """
        Subscribe to events.

        Args:
            subscriber_id: Unique identifier for this subscriber
            event_types: List of event types to subscribe to (None = all)
            session_ids: List of session IDs to filter by (None = all)
            async_mode: Whether to use async-compatible subscriber

        Returns:
            EventSubscriber instance for receiving events
        """
        with self._lock:
            if subscriber_id in self._subscribers:
                # Return existing subscriber
                return self._subscribers[subscriber_id]

            subscriber = AsyncEventSubscriber(subscriber_id) if async_mode else EventSubscriber(subscriber_id)

            if event_types:
                subscriber.subscribed_types = set(event_types)
                for et in event_types:
                    self._type_subscriptions[et].add(subscriber_id)
            else:
                # Subscribe to all
                subscriber.subscribed_types = set(["*"])
                self._type_subscriptions["*"].add(subscriber_id)

            if session_ids:
                for sid in session_ids:
                    self._session_subscriptions[sid].add(subscriber_id)

            self._subscribers[subscriber_id] = subscriber

        logger.debug(f"Subscriber {subscriber_id} registered for {event_types or 'all'} events")
        return subscriber

    def unsubscribe(self, subscriber_id: str):
        """Unsubscribe from events."""
        with self._lock:
            if subscriber_id in self._subscribers:
                subscriber = self._subscribers[subscriber_id]
                subscriber.close()

                # Remove from type subscriptions
                for et in list(self._type_subscriptions.keys()):
                    self._type_subscriptions[et].discard(subscriber_id)

                # Remove from session subscriptions
                for sid in list(self._session_subscriptions.keys()):
                    self._session_subscriptions[sid].discard(subscriber_id)

                del self._subscribers[subscriber_id]

        logger.debug(f"Subscriber {subscriber_id} unregistered")

    def register_callback(self, event_type: str, callback: Callable[[Event], None]):
        """Register a callback for an event type."""
        with self._lock:
            self._callbacks[event_type].append(callback)

    def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        persist: bool = True
    ) -> Event:
        """
        Publish an event to all subscribers.

        Args:
            event_type: Type of event (use EventType enum values)
            payload: Event data
            session_id: Associated session ID
            agent_id: Associated agent ID
            persist: Whether to persist to database

        Returns:
            The published Event
        """
        with self._lock:
            self._event_counter += 1
            event = Event(
                event_type=event_type,
                payload=payload,
                session_id=session_id,
                agent_id=agent_id,
                event_id=self._event_counter
            )

            # Find matching subscribers
            matching_subscriber_ids: Set[str] = set()

            # Type-based matching
            matching_subscriber_ids.update(self._type_subscriptions.get(event_type, set()))
            matching_subscriber_ids.update(self._type_subscriptions.get("*", set()))

            # Session-based filtering
            if session_id:
                session_subs = self._session_subscriptions.get(session_id, set())
                if session_subs:
                    matching_subscriber_ids &= session_subs

            # Deliver to matching subscribers
            for sub_id in matching_subscriber_ids:
                if sub_id in self._subscribers:
                    self._subscribers[sub_id].receive(event)

            # Execute callbacks
            for callback in self._callbacks.get(event_type, []):
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Callback error for {event_type}: {e}")

            for callback in self._callbacks.get("*", []):
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Wildcard callback error: {e}")

        # Persist to database (outside lock)
        if persist and self._persist_events:
            try:
                from .swarm_state import get_swarm_state
                get_swarm_state().emit_event(event_type, session_id, agent_id, payload)
            except Exception as e:
                logger.warning(f"Failed to persist event: {e}")

        return event

    def publish_agent_spawned(
        self,
        session_id: str,
        agent_id: str,
        agent_type: str,
        agent_name: str,
        parent_agent_id: Optional[str] = None
    ):
        """Publish agent spawned event."""
        self.publish(
            EventType.AGENT_SPAWNED.value,
            {
                "agent_type": agent_type,
                "agent_name": agent_name,
                "parent_agent_id": parent_agent_id
            },
            session_id=session_id,
            agent_id=agent_id
        )

    def publish_agent_iteration(
        self,
        session_id: str,
        agent_id: str,
        iteration: int,
        max_iterations: int,
        tokens_used: int = 0
    ):
        """Publish agent iteration event."""
        self.publish(
            EventType.AGENT_ITERATION.value,
            {
                "iteration": iteration,
                "max_iterations": max_iterations,
                "tokens_used": tokens_used
            },
            session_id=session_id,
            agent_id=agent_id
        )

    def publish_agent_completed(
        self,
        session_id: str,
        agent_id: str,
        result_summary: Optional[str] = None,
        tokens_used: int = 0,
        cost: float = 0.0
    ):
        """Publish agent completed event."""
        self.publish(
            EventType.AGENT_COMPLETED.value,
            {
                "result_summary": result_summary,
                "tokens_used": tokens_used,
                "cost": cost
            },
            session_id=session_id,
            agent_id=agent_id
        )

    def publish_agent_failed(
        self,
        session_id: str,
        agent_id: str,
        error: str
    ):
        """Publish agent failed event."""
        self.publish(
            EventType.AGENT_FAILED.value,
            {"error": error},
            session_id=session_id,
            agent_id=agent_id
        )

    def publish_tool_executed(
        self,
        session_id: str,
        agent_id: str,
        tool_name: str,
        success: bool,
        duration_ms: Optional[int] = None
    ):
        """Publish tool executed event."""
        self.publish(
            EventType.TOOL_EXECUTED.value,
            {
                "tool_name": tool_name,
                "success": success,
                "duration_ms": duration_ms
            },
            session_id=session_id,
            agent_id=agent_id
        )

    def publish_file_written(
        self,
        session_id: str,
        agent_id: str,
        file_path: str,
        was_overwrite: bool = False
    ):
        """Publish file written event."""
        self.publish(
            EventType.FILE_WRITTEN.value,
            {
                "file_path": file_path,
                "was_overwrite": was_overwrite
            },
            session_id=session_id,
            agent_id=agent_id
        )

    def publish_git_commit(
        self,
        session_id: str,
        agent_id: str,
        commit_hash: str,
        message: str,
        files: List[str]
    ):
        """Publish git commit event."""
        self.publish(
            EventType.GIT_COMMIT.value,
            {
                "commit_hash": commit_hash,
                "message": message,
                "files": files
            },
            session_id=session_id,
            agent_id=agent_id
        )

    def publish_cost_updated(
        self,
        session_id: str,
        agent_id: str,
        tokens: int,
        cost: float,
        cumulative_cost: float
    ):
        """Publish cost updated event."""
        self.publish(
            EventType.COST_UPDATED.value,
            {
                "tokens": tokens,
                "cost": cost,
                "cumulative_cost": cumulative_cost
            },
            session_id=session_id,
            agent_id=agent_id
        )

    def get_recent_events(
        self,
        event_types: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        since_id: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent events from the persistent store."""
        try:
            from .swarm_state import get_swarm_state
            return get_swarm_state().subscribe_events(event_types, since_id, limit)
        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
            return []


# Singleton accessor
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
