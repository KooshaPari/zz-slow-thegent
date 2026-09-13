"""WL150 — L26 Event Driven Lane.

Tests for the canonical InMemoryEventBus surface shipped at WL150. The
bus unifies the two previously inconsistent ``EventBusInterface``
Protocols (legacy ``subscribe(...) -> None`` shape vs the executor's
``subscribe(...) -> Callable[[], None]`` shape) and provides:

* ``subscribe(event_type, handler)`` returning an idempotent unsubscriber
* ``publish(event_type, data)`` synchronous fan-out
* ``emit(event_type, data)`` deprecated alias for ``publish``
* handler exception isolation (default non-strict)
* strict mode that re-raises via ``EventHandlerError``
* ``unsubscribe_all(event_type)`` for hand-resetting a topic
* introspection counters: ``publish_count``, ``handler_invocation_count``,
  ``subscriber_count(event_type)``, ``subscribed_event_types()``
* thread-safe subscribe/publish/unsubscribe

These tests are part of the Phase 3/4 hardening effort and lock in
the public API contract used by ``thegent.execution.executor``,
``thegent.ux.cockpit_bridge``, and downstream callers.
"""

from __future__ import annotations

import threading

import pytest

from thegent.core.events import (
    EventHandlerError,
    InMemoryEventBus,
    get_default_event_bus,
    reset_default_event_bus,
)
from thegent.core.ports import EventBusInterface
from thegent.execution.executor import EventBusInterface as ExecutorEventBusInterface
from thegent.execution.executor import Executor

# ---------------------------------------------------------------------------
# Protocol identity / canonical parity
# ---------------------------------------------------------------------------


def test_canonical_protocol_is_unified() -> None:
    """The executor's EventBusInterface must be the canonical one."""
    assert ExecutorEventBusInterface is EventBusInterface


def test_in_memory_event_bus_satisfies_canonical_protocol() -> None:
    bus = InMemoryEventBus()
    assert isinstance(bus, EventBusInterface)
    # The runtime checkable protocol requires both publish + emit + subscribe.
    assert callable(bus.publish)
    assert callable(bus.emit)
    assert callable(bus.subscribe)


# ---------------------------------------------------------------------------
# subscribe / publish / unsubscribe
# ---------------------------------------------------------------------------


def test_subscribe_returns_idempotent_unsubscriber() -> None:
    bus = InMemoryEventBus()
    fired: list[str] = []
    unsub = bus.subscribe("e", lambda d: fired.append(d))

    bus.publish("e", "a")
    assert fired == ["a"]

    # Unsubscribe stops further deliveries.
    unsub()
    bus.publish("e", "b")
    assert fired == ["a"]

    # Unsubscriber is idempotent.
    unsub()
    unsub()
    assert bus.subscriber_count("e") == 0


def test_publish_fans_out_to_multiple_handlers_in_order() -> None:
    bus = InMemoryEventBus()
    log: list[str] = []
    bus.subscribe("e", lambda d: log.append(f"a:{d}"))
    bus.subscribe("e", lambda d: log.append(f"b:{d}"))
    bus.subscribe("e", lambda d: log.append(f"c:{d}"))

    bus.publish("e", 1)
    assert log == ["a:1", "b:1", "c:1"]


def test_publish_with_no_subscribers_is_a_no_op() -> None:
    bus = InMemoryEventBus()
    bus.publish("nobody-home", {"x": 1})  # must not raise
    assert bus.publish_count == 1


def test_emit_is_an_alias_for_publish() -> None:
    bus = InMemoryEventBus()
    fired: list[object] = []
    bus.subscribe("e", lambda d: fired.append(d))

    bus.emit("e", "via-emit")
    bus.publish("e", "via-publish")

    assert fired == ["via-emit", "via-publish"]


# ---------------------------------------------------------------------------
# Handler exception isolation
# ---------------------------------------------------------------------------


def test_handler_exceptions_do_not_block_other_handlers() -> None:
    bus = InMemoryEventBus()
    survived: list[object] = []

    def bad(_: object) -> None:
        raise ValueError("boom")

    bus.subscribe("e", bad)
    bus.subscribe("e", lambda d: survived.append(d))

    bus.publish("e", "payload")
    assert survived == ["payload"]
    assert bus.handler_invocation_count == 2


def test_strict_mode_re_raises_as_event_handler_error() -> None:
    bus = InMemoryEventBus(strict=True)

    def bad(_: object) -> None:
        raise RuntimeError("strict boom")

    bus.subscribe("e", bad)
    with pytest.raises(EventHandlerError) as excinfo:
        bus.publish("e", "data")
    assert isinstance(excinfo.value.__cause__, RuntimeError)
    assert "strict boom" in str(excinfo.value.__cause__)


def test_non_strict_mode_silently_swallows_handler_errors() -> None:
    bus = InMemoryEventBus()
    bus.subscribe("e", lambda _: (_ for _ in ()).throw(KeyError("nope")))
    # No exception escapes.
    bus.publish("e", "data")
    assert bus.publish_count == 1


# ---------------------------------------------------------------------------
# Topic management
# ---------------------------------------------------------------------------


def test_unsubscribe_all_clears_a_topic() -> None:
    bus = InMemoryEventBus()
    bus.subscribe("e", lambda d: None)
    bus.subscribe("e", lambda d: None)
    bus.subscribe("other", lambda d: None)
    assert bus.subscriber_count("e") == 2

    removed = bus.unsubscribe_all("e")
    assert removed == 2
    assert bus.subscriber_count("e") == 0
    assert bus.subscriber_count("other") == 1


def test_clear_removes_every_topic() -> None:
    bus = InMemoryEventBus()
    bus.subscribe("a", lambda d: None)
    bus.subscribe("b", lambda d: None)
    bus.subscribe("c", lambda d: None)
    bus.clear()
    assert bus.subscribed_event_types() == []


def test_subscribed_event_types_reflects_active_subscriptions() -> None:
    bus = InMemoryEventBus()
    assert bus.subscribed_event_types() == []

    unsub = bus.subscribe("alpha", lambda d: None)
    assert bus.subscribed_event_types() == ["alpha"]

    bus.subscribe("beta", lambda d: None)
    assert set(bus.subscribed_event_types()) == {"alpha", "beta"}

    unsub()
    assert bus.subscribed_event_types() == ["beta"]


# ---------------------------------------------------------------------------
# Introspection counters
# ---------------------------------------------------------------------------


def test_publish_count_and_handler_invocation_count_increment() -> None:
    bus = InMemoryEventBus()
    bus.subscribe("a", lambda d: None)
    bus.subscribe("a", lambda d: None)
    bus.subscribe("b", lambda d: None)

    bus.publish("a", 1)
    bus.publish("a", 2)
    bus.publish("b", 3)

    assert bus.publish_count == 3
    assert bus.handler_invocation_count == 5  # 2 + 2 + 1


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------


def test_get_default_event_bus_returns_singleton() -> None:
    reset_default_event_bus()
    a = get_default_event_bus()
    b = get_default_event_bus()
    assert a is b
    reset_default_event_bus()
    c = get_default_event_bus()
    assert c is not a


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------


def test_concurrent_subscribe_and_publish_do_not_corrupt_state() -> None:
    bus = InMemoryEventBus()
    counter = []
    counter_lock = threading.Lock()

    def make_handler(label: str):
        def handler(_: object) -> None:
            with counter_lock:
                counter.append(label)

        return handler

    def worker(idx: int) -> None:
        bus.subscribe(f"evt_{idx}", make_handler(f"h{idx}"))
        for k in range(20):
            bus.publish(f"evt_{idx}", k)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # At least one delivery per worker happened; no deadlock, no exception.
    assert bus.publish_count >= 8 * 20
    assert bus.handler_invocation_count >= 8 * 20


# ---------------------------------------------------------------------------
# Real-world end-to-end via Executor
# ---------------------------------------------------------------------------


def test_executor_uses_canonical_event_bus_end_to_end() -> None:
    bus = InMemoryEventBus()
    fired: list[tuple[str, dict]] = []
    bus.subscribe("execution:started", lambda d: fired.append(("started", d)))
    bus.subscribe("execution:completed", lambda d: fired.append(("completed", d)))
    bus.subscribe("execution:failed", lambda d: fired.append(("failed", d)))

    ex = Executor(event_bus=bus)
    result = ex.run("t-150", {"task": "demo"})

    assert result.success
    types = [t for t, _ in fired]
    assert types == ["started", "completed"]
    assert fired[0][1] == {"task_id": "t-150"}
    assert fired[1][1] == {"task_id": "t-150", "success": True}


def test_executor_noop_event_bus_conforms_to_canonical_protocol() -> None:
    """The injected fallback NoOpEventBus used by Executor must satisfy
    the canonical EventBusInterface so it can stand in anywhere."""
    noop = Executor._noop_event_bus()
    assert isinstance(noop, EventBusInterface)
    # Calling either shape should be safe.
    noop.publish("e", "x")
    noop.emit("e", "x")
    assert callable(noop.subscribe("e", lambda d: None))
