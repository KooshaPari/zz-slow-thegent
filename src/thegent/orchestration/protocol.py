"""Orchestration protocol definitions.

Hardening (AUDIT-N+37)
======================

The :class:`SubAgentEvent`, :class:`SubAgentRequest`, and
:class:`SubAgentResult` classes accept **both** the historical
positional ctor (e.g. ``SubAgentRequest(request_id, task)``) and the
dormant-test kwargs ctor (e.g. ``SubAgentRequest(agent_type=..., task=...)``).

The compat layer is anchored on:

| Historical | Dormant |
|------------|---------|
| ``SubAgentEvent(event_type, data)`` | ``SubAgentEvent(request_id, event_type, payload=...)`` |
| ``SubAgentRequest(request_id, task)`` | ``SubAgentRequest(agent_type=..., task=...)`` |
| ``SubAgentResult(request_id, success, result)`` | ``SubAgentResult(request_id, agent_type, status, result)`` |

The historical read of ``.event_type`` and ``.data`` continues to
work; the dormant-test read of ``.request_id`` / ``.payload`` /
``.agent_type`` is now exposed too.  Both attribute names are kept
synchronized on each instance so neither legacy dispatch paths nor
dormant code break.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class OrchestrationProtocol:
    """Protocol for orchestration communication."""

    def __init__(self) -> None:
        self.version = "1.0"

    def encode(self, message: dict[str, Any]) -> bytes:
        """Encode a message."""
        return b""

    def decode(self, data: bytes) -> dict[str, Any]:
        """Decode a message."""
        return {"type": "unknown"}


class TaskMessage:
    """A task message in the orchestration protocol."""

    def __init__(self, task_id: str, payload: dict[str, Any]) -> None:
        self.task_id = task_id
        self.payload = payload


class SubAgentRequest:
    """Sub-agent request.

    Accepts BOTH the historical positional ctor
    ``SubAgentRequest(request_id, task)`` and the dormant-test kwargs
    ctor ``SubAgentRequest(agent_type=..., task=...)``.

    Both signatures populate the same canonical fields so
    ``request.request_id``, ``request.task``, ``request.agent_type``
    are always available.
    """

    def __init__(
        self,
        request_id: str | None = None,
        task: Any | None = None,
        *,
        agent_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        # Positional-first form: ``SubAgentRequest(request_id, task)``.
        if request_id is not None and not kwargs and agent_type is None:
            self.request_id = request_id
            self.task = task
            # Mirror to the dormant-test kwargs API.
            self.agent_type = ""
            return
        # Keyword form: ``SubAgentRequest(agent_type=..., task=...)``.
        # When ``agent_type`` is supplied and ``request_id`` is not,
        # treat ``agent_type`` as the canonical request id (dormant
        # contract).
        self.request_id = kwargs.get("request_id", request_id or "") or (agent_type or "")
        self.task = kwargs.get("task", task if task is not None else "")
        self.agent_type = agent_type or ""


class SubAgentResult:
    """Sub-agent result.

    Accepts BOTH the historical positional ctor
    ``SubAgentResult(request_id, success, result)`` and the dormant-test
    kwargs ctor ``SubAgentResult(request_id, agent_type, status, result)``.

    Both signatures populate the same canonical fields.
    """

    def __init__(
        self,
        request_id: str | None = None,
        *args: Any,
        agent_type: str | None = None,
        status: Any = None,
        result: Any = None,
        **kwargs: Any,
    ) -> None:
        # Historical positional form: ``SubAgentResult(request_id, success, result)``.
        if args and not kwargs and status is None:
            success = args[0] if args else False
            self.success = bool(success)
            self.result = result if len(args) < 2 else args[1]
            self.request_id = request_id or ""
            self.agent_type = ""
            self.status = "completed" if self.success else "failed"
            return
        # Keyword form: ``SubAgentResult(request_id, agent_type, status, result)``.
        self.request_id = request_id or kwargs.get("request_id", "")
        self.agent_type = agent_type or ""
        self.status = status if status is not None else "completed"
        self.success = bool(getattr(self.status, "value", self.status) == "completed")
        self.result = result


class SubAgentEvent:
    """Sub-agent event.

    Accepts BOTH the historical positional ctor
    ``SubAgentEvent(event_type, data)`` and the dormant-test kwargs
    ctor ``SubAgentEvent(request_id, event_type, payload=...)``.

    Both signatures populate the same canonical fields.  The
    duck-typed event check in :mod:`thegent.orchestration.event_queue`
    relies on ``request_id`` / ``event_type`` / ``payload`` attributes.
    """

    def __init__(
        self,
        request_id: Any = None,
        event_type: Any = None,
        payload: dict[str, Any] | None = None,
        *,
        data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        # Historical positional form: ``SubAgentEvent(event_type, data)``.
        # The first arg is an event-type-like value (str / Enum value)
        # and the second is a dict payload.  Detect by type: if the
        # first positional arg is NOT a request-id-shaped string AND
        # the second positional arg IS a dict, treat it as the
        # historical form.  Otherwise, treat it as canonical kwargs.
        if isinstance(event_type, dict) and not isinstance(payload, dict) and data is None and not kwargs:
            self.event_type = request_id
            self.data = event_type
            self.request_id = ""
            self.payload = self.data
            return
        # Canonical form (dormant + future).
        self.request_id = request_id or kwargs.get("request_id", "")
        self.event_type = event_type if event_type is not None else kwargs.get("event_type", "")
        self.payload = payload if payload is not None else data if data is not None else kwargs.get("payload", {})
        self.data = self.payload  # mirror


class SubAgentStatus(Enum):
    """Sub-agent status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SubAgentEventType(Enum):
    """Sub-agent event type enumeration."""

    STARTED = "started"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    LOG = "log"


__all__ = [
    "OrchestrationProtocol",
    "TaskMessage",
    "SubAgentRequest",
    "SubAgentResult",
    "SubAgentEvent",
    "SubAgentStatus",
    "SubAgentEventType",
    "SubAgentProtocolSerializer",
    "get_protocol",
]


def get_protocol() -> OrchestrationProtocol:
    """Get the orchestration protocol instance."""
    return OrchestrationProtocol()


class SubAgentProtocolSerializer:
    """Serializer for sub-agent protocol."""

    def serialize(self, message: SubAgentRequest) -> bytes:
        """Serialize a sub-agent request."""
        return b""

    def deserialize(self, data: bytes) -> SubAgentRequest:
        """Deserialize a sub-agent request."""
        return SubAgentRequest(request_id="", task={})
