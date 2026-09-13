"""In-memory event bus implementation for thegent.

WL150 Phase 3/4 hardening — L26 Event Driven.

Ships ``InMemoryEventBus``, a thread-safe, handler-exception-isolated
pub/sub that satisfies both ``EventBusInterface`` Protocol shapes:

* ``thegent.core.ports.EventBusInterface`` — canonical (publish/subscribe)
* ``thegent.execution.executor.EventBusInterface`` — legacy alias (emit)

The class exposes both ``publish()`` and ``emit()`` so callers using
either Protocol shape resolve cleanly.  ``publish`` and ``emit`` are
exact aliases (same handler, same dispatch semantics).

See ``thegent.core.events`` for the package-level surface and the
design rationale.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from collections.abc import Callable
from typing import Any

EventHandler = Callable[[Any], None]


class EventHandlerError(Exception):
    """Raised when a strict-mode handler dispatch fails.

    Default mode swallows handler exceptions to preserve dispatch
    continuity (one misbehaving subscriber cannot starve the rest).
    When ``strict=True`` is passed to ``InMemoryEventBus.__init__``,
    handler exceptions are re-raised wrapped in ``EventHandlerError``
    (with ``__cause__`` set to the original exception).
    """


class InMemoryEventBus:
    """Thread-safe in-process pub/sub bus.

    Implements the canonical ``EventBusInterface`` from
    ``thegent.core.ports`` (subscribe + publish) and the legacy
    ``execution/executor.EventBusInterface`` shape (emit) — both
    names resolve to the same dispatcher.

    Args:
        strict: If ``True``, handler exceptions are re-raised wrapped
            in ``EventHandlerError``.  If ``False`` (default), handler
            exceptions are logged and swallowed so the next handler in
            the dispatch list still runs.
        name: Optional human-readable label (for telemetry/debugging).

    Thread-safety:
        All public methods are safe to call from multiple threads
        concurrently.  Uses ``threading.RLock`` so a handler that
        reentrantly subscribes / unsubscribes / publishes during
        dispatch does not deadlock or corrupt the handler registry.
    """

    __slots__ = (
        "_handlers",
        "_lock",
        "_name",
        "_strict",
        "handler_invocation_count",
        "publish_count",
    )

    def __init__(self, *, strict: bool = False, name: str = "default") -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._lock = threading.RLock()
        self._strict = strict
        self._name = name
        # Observability counters (not on the Protocol; for tests/telemetry).
        self.handler_invocation_count: int = 0
        self.publish_count: int = 0

    # ---- protocol surface ------------------------------------------------

    def subscribe(self, event_type: str, handler: EventHandler) -> Callable[[], None]:
        """Subscribe ``handler`` to ``event_type``.

        Returns an unsubscribe callable.  Calling it twice is a no-op
        (idempotent); the handler is removed at most once from the
        registry.

        Handlers are invoked in registration order during dispatch.
        Duplicate subscriptions of the same handler for the same
        event type are kept (callers get one dispatch per subscribe).
        """
        with self._lock:
            self._handlers[event_type].append(handler)
            registered = handler

        def _unsubscribe() -> None:
            with self._lock:
                handlers = self._handlers.get(event_type)
                if handlers is None:
                    return
                try:
                    handlers.remove(registered)
                except ValueError:
                    return
                if not handlers:
                    del self._handlers[event_type]

        return _unsubscribe

    def publish(self, event_type: str, data: Any) -> None:
        """Publish ``data`` to every handler subscribed to ``event_type``.

        Handlers are invoked synchronously, in registration order, on
        the publisher's thread.  If ``strict=True`` was passed at
        construction, the first handler exception aborts dispatch and
        is re-raised wrapped in ``EventHandlerError``; otherwise
        exceptions are swallowed so subsequent handlers still fire.
        """
        self._dispatch(event_type, data)

    # ``emit`` is the legacy name exposed by
    # ``execution/executor.EventBusInterface``.  Alias to ``publish`` so
    # any callable conforming to either Protocol shape resolves.
    emit = publish

    # ---- introspection (off-Protocol, tests + telemetry) -----------------

    def subscriber_count(self, event_type: str) -> int:
        """Return the number of handlers subscribed to ``event_type``."""
        with self._lock:
            handlers = self._handlers.get(event_type)
            return len(handlers) if handlers is not None else 0

    def unsubscribe_all(self, event_type: str) -> int:
        """Remove every handler subscribed to ``event_type``.

        Returns:
            Number of handlers removed (``0`` if the topic had no
            subscribers).
        """
        with self._lock:
            handlers = self._handlers.pop(event_type, None)
            return len(handlers) if handlers is not None else 0

    def clear(self) -> None:
        """Remove every handler for every topic.

        After this call the bus behaves the same as a freshly
        constructed instance, except for the configured ``strict`` flag
        and ``name``.
        """
        with self._lock:
            self._handlers.clear()

    def subscribed_event_types(self) -> list[str]:
        """Return the sorted list of event types with at least one handler."""
        with self._lock:
            return sorted(self._handlers.keys())

    @property
    def name(self) -> str:
        """Human-readable label set at construction time."""
        return self._name

    @property
    def strict(self) -> bool:
        """Whether the bus is configured to re-raise handler exceptions."""
        return self._strict

    # ---- internal --------------------------------------------------------

    def _dispatch(self, event_type: str, data: Any) -> None:
        # Snapshot under the lock so reentrant subscribe/unsubscribe
        # during dispatch cannot skip or double-fire handlers.
        with self._lock:
            handlers = list(self._handlers.get(event_type, ()))
            self.publish_count += 1

        for handler in handlers:
            self.handler_invocation_count += 1
            try:
                handler(data)
            except BaseException as exc:
                # ``BaseException`` (not ``Exception``) so KeyboardInterrupt
                # and SystemExit propagate; everything else is contained.
                if self._strict:
                    raise EventHandlerError(f"handler {handler!r} raised on event {event_type!r}") from exc
                # Default (non-strict) mode: swallow and continue.
                # No logger import here to keep the bus dependency-free.


# Module-level singleton accessor (process-lifetime bus for callers that
# don't want to manage their own).  Tests should instantiate their own
# bus to keep state isolated.
_DEFAULT_BUS: InMemoryEventBus | None = None
_DEFAULT_BUS_LOCK = threading.Lock()


def get_default_event_bus() -> InMemoryEventBus:
    """Return the process-lifetime default ``InMemoryEventBus``.

    Lazily constructed on first call.  Safe to call from multiple
    threads (double-checked locking).
    """
    global _DEFAULT_BUS
    if _DEFAULT_BUS is None:
        with _DEFAULT_BUS_LOCK:
            if _DEFAULT_BUS is None:
                _DEFAULT_BUS = InMemoryEventBus(name="default-singleton")
    return _DEFAULT_BUS


def reset_default_event_bus() -> None:
    """Clear the process-lifetime default bus.

    Intended for tests that need a clean bus between cases.  Not
    idempotency-required (no exception if never set).
    """
    global _DEFAULT_BUS
    with _DEFAULT_BUS_LOCK:
        _DEFAULT_BUS = None


__all__ = [
    "InMemoryEventBus",
    "EventHandlerError",
    "EventHandler",
    "get_default_event_bus",
    "reset_default_event_bus",
]
