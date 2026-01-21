"""
Unit tests for event_bus module.

Tests the EventBus, Event, and EventSubscriber classes.
"""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock


class TestEventType:
    """Test EventType enum."""

    def test_event_type_values(self):
        """Test that all event types have expected values."""
        from src.runtime.agents.event_bus import EventType

        assert EventType.SESSION_CREATED.value == "session_created"
        assert EventType.SESSION_COMPLETED.value == "session_completed"
        assert EventType.AGENT_SPAWNED.value == "agent_spawned"
        assert EventType.AGENT_COMPLETED.value == "agent_completed"
        assert EventType.TOOL_EXECUTED.value == "tool_executed"
        assert EventType.FILE_WRITTEN.value == "file_written"
        assert EventType.GIT_COMMIT.value == "git_commit"
        assert EventType.COST_UPDATED.value == "cost_updated"
        assert EventType.QUESTION_ASKED.value == "question_asked"
        assert EventType.CUSTOM.value == "custom"


class TestEvent:
    """Test Event dataclass."""

    def test_event_creation(self):
        """Test creating an Event."""
        from src.runtime.agents.event_bus import Event

        event = Event(
            event_type="test_event",
            payload={"key": "value"},
            session_id="session-1",
            agent_id="agent-1"
        )

        assert event.event_type == "test_event"
        assert event.payload == {"key": "value"}
        assert event.session_id == "session-1"
        assert event.agent_id == "agent-1"
        assert event.timestamp is not None
        assert event.event_id is not None

    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        from src.runtime.agents.event_bus import Event

        event = Event(
            event_type="test_event",
            payload={"key": "value"},
            session_id="session-1",
            agent_id="agent-1"
        )

        result = event.to_dict()

        assert result["event_type"] == "test_event"
        assert result["payload"] == {"key": "value"}
        assert result["session_id"] == "session-1"
        assert result["agent_id"] == "agent-1"
        assert "timestamp" in result
        assert "event_id" in result

    def test_event_to_json(self):
        """Test converting event to JSON."""
        from src.runtime.agents.event_bus import Event
        import json

        event = Event(
            event_type="test_event",
            payload={"key": "value"},
            session_id="session-1"
        )

        json_str = event.to_json()
        parsed = json.loads(json_str)

        assert parsed["event_type"] == "test_event"
        assert parsed["payload"]["key"] == "value"


class TestEventSubscriber:
    """Test EventSubscriber class."""

    def test_subscriber_creation(self):
        """Test creating an EventSubscriber."""
        from src.runtime.agents.event_bus import EventSubscriber

        subscriber = EventSubscriber("test-subscriber")

        assert subscriber.subscriber_id == "test-subscriber"
        assert subscriber._active is True

    def test_receive_event(self):
        """Test receiving an event."""
        from src.runtime.agents.event_bus import EventSubscriber, Event

        subscriber = EventSubscriber("test-subscriber")
        event = Event(event_type="test", payload={})

        subscriber.receive(event)

        events = subscriber.get_events(timeout=0.1)
        assert len(events) == 1
        assert events[0].event_type == "test"

    def test_receive_when_closed(self):
        """Test receiving event when subscriber is closed."""
        from src.runtime.agents.event_bus import EventSubscriber, Event

        subscriber = EventSubscriber("test-subscriber")
        subscriber.close()

        event = Event(event_type="test", payload={})
        subscriber.receive(event)

        events = subscriber.get_events(timeout=0.1)
        assert len(events) == 0

    def test_get_events_multiple(self):
        """Test getting multiple events."""
        from src.runtime.agents.event_bus import EventSubscriber, Event

        subscriber = EventSubscriber("test-subscriber")

        for i in range(5):
            event = Event(event_type=f"test_{i}", payload={"index": i})
            subscriber.receive(event)

        events = subscriber.get_events(timeout=0.5, max_events=10)
        assert len(events) == 5

    def test_get_events_max_limit(self):
        """Test max_events limit."""
        from src.runtime.agents.event_bus import EventSubscriber, Event

        subscriber = EventSubscriber("test-subscriber")

        for i in range(10):
            event = Event(event_type=f"test_{i}", payload={})
            subscriber.receive(event)

        events = subscriber.get_events(timeout=0.5, max_events=3)
        assert len(events) == 3

    def test_close_subscriber(self):
        """Test closing subscriber."""
        from src.runtime.agents.event_bus import EventSubscriber

        subscriber = EventSubscriber("test-subscriber")
        assert subscriber._active is True

        subscriber.close()
        assert subscriber._active is False


class TestAsyncEventSubscriber:
    """Test AsyncEventSubscriber class."""

    def test_async_subscriber_creation(self):
        """Test creating an AsyncEventSubscriber."""
        from src.runtime.agents.event_bus import AsyncEventSubscriber

        subscriber = AsyncEventSubscriber("test-async")

        assert subscriber.subscriber_id == "test-async"
        assert subscriber._active is True

    def test_async_receive_event(self):
        """Test receiving event in async subscriber."""
        from src.runtime.agents.event_bus import AsyncEventSubscriber, Event

        subscriber = AsyncEventSubscriber("test-async")
        event = Event(event_type="test", payload={})

        subscriber.receive(event)

        # Check the async queue has the event
        assert not subscriber._async_queue.empty()

    def test_async_receive_when_closed(self):
        """Test receiving event when async subscriber is closed."""
        from src.runtime.agents.event_bus import AsyncEventSubscriber, Event

        subscriber = AsyncEventSubscriber("test-async")
        subscriber.close()

        event = Event(event_type="test", payload={})
        subscriber.receive(event)

        assert subscriber._async_queue.empty()


class TestEventBusSingleton:
    """Test EventBus singleton pattern."""

    def test_singleton_same_instance(self):
        """Test EventBus returns same instance."""
        from src.runtime.agents.event_bus import EventBus

        # Reset singleton for test
        EventBus._instance = None

        bus1 = EventBus()
        bus2 = EventBus()

        assert bus1 is bus2


class TestEventBus:
    """Test EventBus class."""

    @pytest.fixture
    def event_bus(self):
        """Create a fresh EventBus for testing."""
        from src.runtime.agents.event_bus import EventBus

        # Reset singleton
        EventBus._instance = None
        bus = EventBus()
        bus._persist_events = False  # Disable persistence for tests
        yield bus
        # Cleanup subscribers
        for sub_id in list(bus._subscribers.keys()):
            bus.unsubscribe(sub_id)

    def test_subscribe(self, event_bus):
        """Test subscribing to events."""
        subscriber = event_bus.subscribe("test-sub")

        assert subscriber is not None
        assert subscriber.subscriber_id == "test-sub"
        assert "test-sub" in event_bus._subscribers

    def test_subscribe_with_event_types(self, event_bus):
        """Test subscribing with specific event types."""
        subscriber = event_bus.subscribe(
            "test-sub",
            event_types=["agent_spawned", "agent_completed"]
        )

        assert "agent_spawned" in subscriber.subscribed_types
        assert "agent_completed" in subscriber.subscribed_types

    def test_subscribe_existing_returns_same(self, event_bus):
        """Test subscribing with same ID returns existing subscriber."""
        sub1 = event_bus.subscribe("test-sub")
        sub2 = event_bus.subscribe("test-sub")

        assert sub1 is sub2

    def test_subscribe_async_mode(self, event_bus):
        """Test subscribing in async mode."""
        from src.runtime.agents.event_bus import AsyncEventSubscriber

        subscriber = event_bus.subscribe("test-async", async_mode=True)

        assert isinstance(subscriber, AsyncEventSubscriber)

    def test_unsubscribe(self, event_bus):
        """Test unsubscribing."""
        event_bus.subscribe("test-sub")
        assert "test-sub" in event_bus._subscribers

        event_bus.unsubscribe("test-sub")
        assert "test-sub" not in event_bus._subscribers

    def test_unsubscribe_nonexistent(self, event_bus):
        """Test unsubscribing nonexistent subscriber."""
        # Should not raise
        event_bus.unsubscribe("nonexistent")

    def test_register_callback(self, event_bus):
        """Test registering callbacks."""
        callback = MagicMock()
        event_bus.register_callback("test_event", callback)

        assert callback in event_bus._callbacks["test_event"]

    def test_publish_basic(self, event_bus):
        """Test publishing an event."""
        event = event_bus.publish(
            "test_event",
            {"key": "value"},
            session_id="session-1",
            agent_id="agent-1"
        )

        assert event.event_type == "test_event"
        assert event.payload == {"key": "value"}
        assert event.session_id == "session-1"

    def test_publish_delivers_to_subscriber(self, event_bus):
        """Test that published events are delivered to subscribers."""
        subscriber = event_bus.subscribe("test-sub", event_types=["test_event"])

        event_bus.publish("test_event", {"key": "value"})

        events = subscriber.get_events(timeout=0.5)
        assert len(events) == 1
        assert events[0].event_type == "test_event"

    def test_publish_callback_executed(self, event_bus):
        """Test that callbacks are executed on publish."""
        callback = MagicMock()
        event_bus.register_callback("test_event", callback)

        event_bus.publish("test_event", {"key": "value"})

        callback.assert_called_once()

    def test_publish_without_persist(self, event_bus):
        """Test publishing without persisting."""
        # Just verify it doesn't crash with persist=False
        event = event_bus.publish("test_event", {}, persist=False)
        assert event is not None

    def test_publish_agent_spawned(self, event_bus):
        """Test publish_agent_spawned helper."""
        subscriber = event_bus.subscribe("test-sub", event_types=["agent_spawned"])

        event_bus.publish_agent_spawned(
            session_id="session-1",
            agent_id="agent-1",
            agent_type="developer",
            agent_name="Test Agent"
        )

        events = subscriber.get_events(timeout=0.2)
        assert len(events) == 1
        assert events[0].payload["agent_type"] == "developer"

    def test_publish_agent_iteration(self, event_bus):
        """Test publish_agent_iteration helper."""
        subscriber = event_bus.subscribe("test-sub", event_types=["agent_iteration"])

        event_bus.publish_agent_iteration(
            session_id="session-1",
            agent_id="agent-1",
            iteration=5,
            max_iterations=10,
            tokens_used=1000
        )

        events = subscriber.get_events(timeout=0.2)
        assert len(events) == 1
        assert events[0].payload["iteration"] == 5

    def test_publish_agent_completed(self, event_bus):
        """Test publish_agent_completed helper."""
        subscriber = event_bus.subscribe("test-sub", event_types=["agent_completed"])

        event_bus.publish_agent_completed(
            session_id="session-1",
            agent_id="agent-1",
            result_summary="Completed successfully",
            tokens_used=500,
            cost=0.01
        )

        events = subscriber.get_events(timeout=0.2)
        assert len(events) == 1
        assert events[0].payload["result_summary"] == "Completed successfully"

    def test_publish_agent_failed(self, event_bus):
        """Test publish_agent_failed helper."""
        subscriber = event_bus.subscribe("test-sub", event_types=["agent_failed"])

        event_bus.publish_agent_failed(
            session_id="session-1",
            agent_id="agent-1",
            error="Something went wrong"
        )

        events = subscriber.get_events(timeout=0.2)
        assert len(events) == 1
        assert events[0].payload["error"] == "Something went wrong"

    def test_publish_tool_executed(self, event_bus):
        """Test publish_tool_executed helper."""
        subscriber = event_bus.subscribe("test-sub", event_types=["tool_executed"])

        event_bus.publish_tool_executed(
            session_id="session-1",
            agent_id="agent-1",
            tool_name="write_file",
            success=True,
            duration_ms=100
        )

        events = subscriber.get_events(timeout=0.2)
        assert len(events) == 1
        assert events[0].payload["tool_name"] == "write_file"

    def test_publish_file_written(self, event_bus):
        """Test publish_file_written helper."""
        subscriber = event_bus.subscribe("test-sub", event_types=["file_written"])

        event_bus.publish_file_written(
            session_id="session-1",
            agent_id="agent-1",
            file_path="/test/file.py",
            was_overwrite=True
        )

        events = subscriber.get_events(timeout=0.2)
        assert len(events) == 1
        assert events[0].payload["file_path"] == "/test/file.py"

    def test_publish_git_commit(self, event_bus):
        """Test publish_git_commit helper."""
        subscriber = event_bus.subscribe("test-sub", event_types=["git_commit"])

        event_bus.publish_git_commit(
            session_id="session-1",
            agent_id="agent-1",
            commit_hash="abc123",
            message="Fix bug",
            files=["file1.py", "file2.py"]
        )

        events = subscriber.get_events(timeout=0.2)
        assert len(events) == 1
        assert events[0].payload["commit_hash"] == "abc123"

    def test_publish_cost_updated(self, event_bus):
        """Test publish_cost_updated helper."""
        subscriber = event_bus.subscribe("test-sub", event_types=["cost_updated"])

        event_bus.publish_cost_updated(
            session_id="session-1",
            agent_id="agent-1",
            tokens=1000,
            cost=0.01,
            cumulative_cost=0.05
        )

        events = subscriber.get_events(timeout=0.2)
        assert len(events) == 1
        assert events[0].payload["tokens"] == 1000

    def test_get_recent_events_error_handling(self, event_bus):
        """Test getting recent events when error occurs."""
        # This tests the error handling path in get_recent_events
        # The import inside the method will fail since swarm_state isn't initialized
        events = event_bus.get_recent_events()
        # Should return empty list on error
        assert isinstance(events, list)


class TestGetEventBus:
    """Test get_event_bus function."""

    def test_get_event_bus_returns_instance(self):
        """Test get_event_bus returns EventBus instance."""
        import src.runtime.agents.event_bus as module
        module._event_bus = None
        module.EventBus._instance = None

        from src.runtime.agents.event_bus import get_event_bus

        bus = get_event_bus()

        assert bus is not None

    def test_get_event_bus_returns_same_instance(self):
        """Test get_event_bus returns same instance."""
        import src.runtime.agents.event_bus as module
        module._event_bus = None
        module.EventBus._instance = None

        from src.runtime.agents.event_bus import get_event_bus

        bus1 = get_event_bus()
        bus2 = get_event_bus()

        assert bus1 is bus2


class TestEventBusFiltering:
    """Test EventBus filtering behavior."""

    @pytest.fixture
    def event_bus(self):
        """Create a fresh EventBus for testing."""
        from src.runtime.agents.event_bus import EventBus

        EventBus._instance = None
        bus = EventBus()
        bus._persist_events = False  # Disable persistence for tests
        yield bus
        for sub_id in list(bus._subscribers.keys()):
            bus.unsubscribe(sub_id)

    def test_type_filtering(self, event_bus):
        """Test that subscribers only receive subscribed event types."""
        sub1 = event_bus.subscribe("sub1", event_types=["type_a"])
        sub2 = event_bus.subscribe("sub2", event_types=["type_b"])

        event_bus.publish("type_a", {"msg": "a"})
        event_bus.publish("type_b", {"msg": "b"})

        events1 = sub1.get_events(timeout=0.2)
        events2 = sub2.get_events(timeout=0.2)

        assert len(events1) == 1
        assert events1[0].event_type == "type_a"
        assert len(events2) == 1
        assert events2[0].event_type == "type_b"

    def test_wildcard_subscription(self, event_bus):
        """Test wildcard subscription receives all events."""
        subscriber = event_bus.subscribe("wildcard-sub")  # No event_types = all

        event_bus.publish("type_a", {})
        event_bus.publish("type_b", {})
        event_bus.publish("type_c", {})

        events = subscriber.get_events(timeout=0.5)
        assert len(events) == 3

    def test_wildcard_callback(self, event_bus):
        """Test wildcard callback receives all events."""
        callback = MagicMock()
        event_bus.register_callback("*", callback)

        event_bus.publish("type_a", {})
        event_bus.publish("type_b", {})

        assert callback.call_count == 2

    def test_session_filtering(self, event_bus):
        """Test session-based filtering with multiple session subscribers."""
        # Create two subscribers for different sessions
        sub1 = event_bus.subscribe(
            "session-sub-1",
            event_types=["test"],
            session_ids=["session-1"]
        )
        sub2 = event_bus.subscribe(
            "session-sub-2",
            event_types=["test"],
            session_ids=["session-2"]
        )

        event_bus.publish("test", {"msg": "for session 1"}, session_id="session-1")
        event_bus.publish("test", {"msg": "for session 2"}, session_id="session-2")

        events1 = sub1.get_events(timeout=0.2)
        events2 = sub2.get_events(timeout=0.2)

        # Each subscriber receives only their session's event
        assert len(events1) == 1
        assert events1[0].session_id == "session-1"
        assert len(events2) == 1
        assert events2[0].session_id == "session-2"
