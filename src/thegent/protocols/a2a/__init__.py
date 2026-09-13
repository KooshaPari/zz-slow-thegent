"""A2A protocol support for agent-to-agent communication."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

VALID_MESSAGE_TYPES = {"request", "response", "error", "event"}


@dataclass
class A2AMessage:
    """A2A message for agent-to-agent communication."""

    source_agent: str
    target_agent: str
    message_type: str  # "request", "response", "error", "event"
    payload: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    correlation_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def a2a_message_from_dict(data: dict[str, Any]) -> A2AMessage:
    """Create an A2AMessage from a dictionary."""
    if not data.get("source_agent"):
        raise ValueError("source_agent is required")
    return A2AMessage(
        id=data.get("id", str(uuid.uuid4())),
        source_agent=data["source_agent"],
        target_agent=data.get("target_agent", ""),
        message_type=data.get("message_type", "request"),
        payload=data.get("payload", {}),
        timestamp=data.get("timestamp", time.time()),
        correlation_id=data.get("correlation_id", ""),
        metadata=data.get("metadata", {}),
    )


def a2a_message_to_dict(message: A2AMessage) -> dict[str, Any]:
    """Convert an A2AMessage to a dictionary."""
    return {
        "id": message.id,
        "source_agent": message.source_agent,
        "target_agent": message.target_agent,
        "message_type": message.message_type,
        "payload": message.payload,
        "timestamp": message.timestamp,
        "correlation_id": message.correlation_id,
        "metadata": message.metadata,
    }


def validate_a2a_message(msg: A2AMessage) -> list[str]:
    """Validate an A2A message and return list of errors."""
    errors = []
    if not msg.source_agent:
        errors.append("source_agent is required and cannot be empty")
    if msg.message_type not in VALID_MESSAGE_TYPES:
        errors.append(
            f"message_type must be one of {VALID_MESSAGE_TYPES}, got: {msg.message_type}"
        )
    return errors


def create_response(
    request: A2AMessage,
    source_agent: str,
    payload: dict[str, Any] | None = None,
    error: str = "",
) -> A2AMessage:
    """Create a response message for a request."""
    msg_type = "error" if error else "response"
    return A2AMessage(
        source_agent=source_agent,
        target_agent=request.source_agent,
        message_type=msg_type,
        payload=payload or {"error": error} if error else {},
        correlation_id=request.id,
    )


class A2ARouter:
    """Router for A2A messages."""

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[A2AMessage], A2AMessage | None]] = {}

    def register(
        self,
        agent_id: str,
        handler: Callable[[A2AMessage], A2AMessage | None],
    ) -> None:
        """Register a handler for an agent."""
        self._handlers[agent_id] = handler

    def unregister(self, agent_id: str) -> None:
        """Unregister a handler for an agent."""
        self._handlers.pop(agent_id, None)

    def list_agents(self) -> list[str]:
        """List registered agents."""
        return list(self._handlers.keys())

    def route(self, msg: A2AMessage) -> list[A2AMessage]:
        """Route a message to the appropriate handler."""
        handler = self._handlers.get(msg.target_agent)
        if handler is None:
            return []
        result = handler(msg)
        if result is None:
            return []
        return [result]


__all__ = [
    "A2AMessage",
    "A2ARouter",
    "a2a_message_from_dict",
    "a2a_message_to_dict",
    "create_response",
    "validate_a2a_message",
]
