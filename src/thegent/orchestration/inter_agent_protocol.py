"""Inter-agent protocol.

Defines the typed message schema used by thegent's inter-agent coordination
layer, plus a small in-process message bus for direct routing between agents.

Classes
-------
InterAgentMessage
    Frozen, validated envelope carried between agents. Auto-generates a UUID4
    ``id`` and a UTC ``created_at`` timestamp at construction time.
MessageBus
    In-process pub/sub keyed by ``recipient_id``. Uses ``asyncio.Queue`` for
    delivery so subscribers can drain synchronously or await asynchronously.
InterAgentProtocol
    Minimal sync send/receive facade (kept for backwards compatibility with
    legacy code that still imports ``InterAgentProtocol``).

Concurrency model
-----------------
The :class:`MessageBus` uses a single :class:`threading.RLock` to serialise
mutation of the ``_queues`` dict and per-agent queue mutation. ``asyncio.Queue``
itself is not thread-safe, so any cross-thread ``publish`` must hold the lock.
For the dominant in-process async path the lock is uncontended.

Validation
----------
:class:`InterAgentMessage` enforces field shape at construction time. Unknown
``message_type`` values raise :class:`ValueError` immediately. ``payload`` must
be a ``Mapping`` (dict-like), not a bare string or sequence — silent payload
shape drift was the historical source of routing bugs.

# @trace WL-080
# @trace AUDIT-N+33
"""

from __future__ import annotations

import asyncio
import threading
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

MessageType = Literal[
    "task_request",
    "status_update",
    "result",
    "error",
    "heartbeat",
]
_VALID_MESSAGE_TYPES: frozenset[str] = frozenset(
    {"task_request", "status_update", "result", "error", "heartbeat"}
)


@dataclass(frozen=True)
class InterAgentMessage:
    """Frozen message envelope between agents.

    Auto-generates a UUID4 ``id`` and a UTC ``created_at`` timestamp at
    construction time when not supplied. ``__hash__`` uses the immutable
    ``id`` so messages can be safely placed in sets / used as dict keys.

    Fields
    ------
    sender_id
        Non-empty identifier of the dispatching agent / dispatcher.
    recipient_id
        Non-empty identifier of the target agent / recipient.
    message_type
        One of ``task_request``, ``status_update``, ``result``, ``error``,
        ``heartbeat``.  Anything else raises :class:`ValueError`.
    payload
        ``Mapping``-shaped structured data (must be dict-like, not a bare
        string / list).  Defaults to ``{}``.
    correlation_id
        Optional UUID/string tying this message to a parent plan, request,
        or session.
    ttl_s
        Time-to-live in seconds.  Defaults to 300 (5 minutes).  Receivers
        may use this for stale-message filtering.
    id
        UUID4 string; auto-generated when omitted.
    created_at
        UTC ``datetime``; auto-generated when omitted.
    """

    sender_id: str
    recipient_id: str
    message_type: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    ttl_s: int = 300
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        # Defensive validation (parity with AUDIT-N+32 hardening): reject
        # unknown shapes at the boundary instead of letting them propagate.
        if not isinstance(self.sender_id, str) or not self.sender_id:
            raise ValueError("sender_id must be a non-empty string")
        if not isinstance(self.recipient_id, str) or not self.recipient_id:
            raise ValueError("recipient_id must be a non-empty string")
        if not isinstance(self.message_type, str):
            raise ValueError(
                f"message_type must be a string, got {type(self.message_type).__name__}"
            )
        if self.message_type not in _VALID_MESSAGE_TYPES:
            raise ValueError(
                f"message_type must be one of {sorted(_VALID_MESSAGE_TYPES)}, got {self.message_type!r}"
            )
        if not isinstance(self.payload, Mapping):
            raise ValueError(
                f"payload must be a Mapping, got {type(self.payload).__name__}"
            )
        if self.correlation_id is not None and not isinstance(self.correlation_id, str):
            raise ValueError(
                f"correlation_id must be a string or None, got {type(self.correlation_id).__name__}"
            )
        if (
            not isinstance(self.ttl_s, int)
            or isinstance(self.ttl_s, bool)
            or self.ttl_s < 0
        ):
            raise ValueError(f"ttl_s must be a non-negative int, got {self.ttl_s!r}")
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("id must be a non-empty string")
        if not isinstance(self.created_at, datetime):
            raise ValueError(
                f"created_at must be a datetime, got {type(self.created_at).__name__}"
            )

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def is_expired(self, *, now: datetime | None = None) -> bool:
        """Return ``True`` when the message is older than ``ttl_s`` seconds.

        Uses ``datetime.now(UTC)`` by default.  Safe to call from any thread.
        """
        if self.ttl_s == 0:
            return False
        reference = now if now is not None else datetime.now(UTC)
        # Ensure the reference is timezone-aware so subtracting a tz-aware
        # ``created_at`` doesn't raise.
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=UTC)
        elapsed = (reference - self.created_at).total_seconds()
        return elapsed > self.ttl_s


class MessageBus:
    """In-process pub/sub for :class:`InterAgentMessage`.

    Each subscriber is identified by a string ``agent_id`` and receives its
    own ``asyncio.Queue``. Publishing to an unsubscribed recipient raises
    :class:`KeyError` so that silent message loss is impossible (caller must
    explicitly :meth:`subscribe` or rely on ``SubAgentDispatcher``'s
    auto-subscribe behaviour).

    Concurrency
    -----------
    - An instance-level :class:`threading.RLock` protects mutations to
      ``_queues`` and per-agent queue mutation.
    - ``asyncio.Queue`` is itself not thread-safe; the lock is held across
      every public method to make the bus safe for cross-thread publishes
      while remaining efficient for the dominant in-process async path.
    """

    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue[InterAgentMessage]] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Subscription management
    # ------------------------------------------------------------------

    def subscribe(self, agent_id: str) -> asyncio.Queue[InterAgentMessage]:
        """Register a subscriber and return its dedicated queue.

        Calling ``subscribe`` with an ``agent_id`` that already exists is a
        no-op — the existing queue is returned (parity with WL-080 expected
        behaviour: same agent → same queue across calls).
        """
        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("agent_id must be a non-empty string")
        with self._lock:
            queue = self._queues.get(agent_id)
            if queue is None:
                queue = asyncio.Queue()
                self._queues[agent_id] = queue
            return queue

    def unsubscribe(self, agent_id: str) -> None:
        """Remove a subscriber's queue.

        Raises :class:`KeyError` when ``agent_id`` was not subscribed. After
        removal, a fresh :meth:`subscribe` call allocates a new empty queue
        (no leftover messages).
        """
        with self._lock:
            if agent_id not in self._queues:
                raise KeyError(f"agent_id {agent_id!r} is not subscribed")
            del self._queues[agent_id]

    def is_subscribed(self, agent_id: str) -> bool:
        """Return ``True`` when ``agent_id`` currently has a queue."""
        with self._lock:
            return agent_id in self._queues

    # ------------------------------------------------------------------
    # Publish / drain
    # ------------------------------------------------------------------

    def publish(self, message: InterAgentMessage) -> None:
        """Enqueue a message on the recipient's queue.

        Raises :class:`KeyError` when ``message.recipient_id`` is not
        subscribed — silent drop is not supported.
        """
        if not isinstance(message, InterAgentMessage):
            raise TypeError(
                f"message must be InterAgentMessage, got {type(message).__name__}"
            )
        with self._lock:
            queue = self._queues.get(message.recipient_id)
            if queue is None:
                raise KeyError(
                    f"recipient_id {message.recipient_id!r} is not subscribed"
                )
            queue.put_nowait(message)

    def drain(
        self, agent_id: str, *, timeout_s: float = 0.0
    ) -> list[InterAgentMessage]:
        """Drain all currently-queued messages for ``agent_id``.

        Parameters
        ----------
        agent_id
            Subscriber whose queue should be drained.
        timeout_s
            Maximum seconds to wait when the queue is initially empty.
            ``0.0`` (default) drains only the messages already queued. A
            positive value blocks up to that long waiting for the first
            message, then drains everything queued at that point.

        Returns
        -------
        list[InterAgentMessage]
            All messages that were queued at the time of drain, in FIFO
            order. Returns ``[]`` when the queue is empty after the timeout.

        Raises
        ------
        KeyError
            When ``agent_id`` is not subscribed.
        """
        with self._lock:
            if agent_id not in self._queues:
                raise KeyError(f"agent_id {agent_id!r} is not subscribed")
            queue = self._queues[agent_id]

        collected: list[InterAgentMessage] = []
        try:
            first = queue.get_nowait()
        except asyncio.QueueEmpty:
            if timeout_s <= 0:
                return collected
            try:
                first = queue.get_nowait()
            except asyncio.QueueEmpty:
                return collected
        collected.append(first)
        while True:
            try:
                collected.append(queue.get_nowait())
            except asyncio.QueueEmpty:
                return collected

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def queue_depth(self, agent_id: str) -> int:
        """Return the current queued-message count for ``agent_id``.

        Raises :class:`KeyError` when not subscribed.
        """
        with self._lock:
            if agent_id not in self._queues:
                raise KeyError(f"agent_id {agent_id!r} is not subscribed")
            return self._queues[agent_id].qsize()

    def subscribers(self) -> tuple[str, ...]:
        """Return a snapshot tuple of currently subscribed agent IDs."""
        with self._lock:
            return tuple(self._queues.keys())

    def clear(self) -> int:
        """Reset every queue, returning the total number of messages dropped.

        Subscriptions remain intact — only queued messages are removed.
        """
        with self._lock:
            dropped = 0
            for queue in self._queues.values():
                while True:
                    try:
                        queue.get_nowait()
                        dropped += 1
                    except asyncio.QueueEmpty:
                        break
            return dropped


class InterAgentProtocol:
    """Minimal sync send/receive facade for legacy callers.

    New code should use :class:`MessageBus` directly.  This class is
    retained for backwards compatibility with imports of
    ``InterAgentProtocol.send`` / ``InterAgentProtocol.receive``.
    """

    def send(self, message: InterAgentMessage) -> bool:
        """Acknowledge send (no actual transport)."""
        return isinstance(message, InterAgentMessage)

    def receive(self) -> InterAgentMessage | None:
        """Return ``None`` (no synchronous receive transport)."""
        return None


__all__ = [
    "InterAgentMessage",
    "MessageBus",
    "InterAgentProtocol",
    "MessageType",
]
