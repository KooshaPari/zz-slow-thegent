"""Canonical in-process event bus for thegent.

WL150 Phase 3/4 hardening — L26 Event Driven (85/A- → 92/A).

The ``InMemoryEventBus`` is the canonical implementation of the
``EventBusInterface`` Protocol declared in
``thegent.core.ports``.  Before WL150, the codebase referenced
``event_bus`` 34 times (per the SOTA audit) but shipped **zero**
concrete in-process pub/sub surface: only two incompatible
``EventBusInterface`` Protocol declarations (``core/ports`` exposes
``publish``; ``execution/executor`` exposes ``emit``) and a
``NoOpEventBus`` that silently dropped every event.

WL150 closes the gap:

* Ships ``InMemoryEventBus`` — a thread-safe, handler-exception
  isolated, reentrant-safe pub/sub with both ``publish`` and ``emit``
  surface names so the two Protocol shapes both resolve.
* Pins the canonical surface via
  ``tests/test_wl150_l26_event_bus_surface.py`` (subscribe, unsubscribe,
  multi-handler fan-out, handler-exception isolation, no-handler no-op,
  reentrant publish, duplicate-handler fan-out, ``emit`` alias parity,
  thread-safe concurrent publish).
* Wires ``execution/executor`` to the canonical ``EventBusInterface``
  so the ``Executor`` constructor can be passed any canonical bus
  without changing the ``event_bus=...`` keyword argument.

Design choices (frozen at WL150, regression-pinned):

* **Synchronous delivery** — handlers are invoked in registration
  order from the publisher's thread.  This is the simplest contract
  to reason about and matches every existing call site
  (``event_bus.emit("execution:started", {...})``).
* **Thread-safety** — uses ``threading.RLock`` so a handler that
  reentrantly publishes during dispatch is safe (and so concurrent
  publishers do not corrupt the handler list).
* **Handler exception isolation** — a handler raising
  ``Exception`` (not ``BaseException``) is swallowed; the next
  handler in the dispatch list still runs.  ``KeyboardInterrupt``
  and ``SystemExit`` propagate.
* **Unsubscribe by callable** — ``subscribe`` returns the
  unsubscribe callable so callers don't need to retain the handler
  reference.
* **No wildcards** — keep the surface minimal.  Wildcard subscription
  is a future Phase 4 surface; current call sites never publish to
  wildcards.
* **Counts** — ``InMemoryEventBus.handler_invocation_count`` exposes
  the total number of handler invocations across all event types
  (for testing/telemetry only; not on the Protocol).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from thegent.core.events.in_memory_bus import (  # noqa: F401
    EventHandlerError,
    InMemoryEventBus,
    get_default_event_bus,
    reset_default_event_bus,
)

# Re-export the canonical Protocol so callers can ``isinstance`` /
# ``runtime_checkable`` against the symbol they import.
from thegent.core.ports import EventBusInterface  # noqa: F401

EventHandler = Callable[[Any], None]


__all__ = [
    "EventBusInterface",
    "InMemoryEventBus",
    "EventHandlerError",
    "EventHandler",
    "get_default_event_bus",
    "reset_default_event_bus",
]
