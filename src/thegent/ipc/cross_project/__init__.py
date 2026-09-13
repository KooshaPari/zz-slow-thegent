"""Stub module."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class IpcMessage:
    """IPC message for cross-project communication."""

    id: str = ""
    sender: str = ""
    recipient: str = ""
    payload: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


BROADCAST_ADDR = "255.255.255.255"


class CrossProjectIPC:
    """IPC for cross-project communication."""

    def __init__(self) -> None:
        self.connected: bool = False


class CrossProjectIpc:
    """IPC for cross-project communication."""

    def __init__(self) -> None:
        self.connected: bool = False

    def send(self, message: dict) -> bool:
        """Send a message."""
        return True

    def receive(self) -> dict | None:
        """Receive a message."""
        return None


class CrossProjectIpcServer:
    """Server for cross-project IPC."""

    def __init__(self, port: int = 0) -> None:
        self.port = port
        self._running = False

    def start(self) -> None:
        """Start the server."""
        self._running = True

    def stop(self) -> None:
        """Stop the server."""
        self._running = False


__all__ = [
    "BROADCAST_ADDR",
    "CrossProjectIPC",
    "CrossProjectIpc",
    "CrossProjectIpcServer",
    "_inbox_name",
]


def _inbox_name(project_id: str, entity_id: str) -> str:
    """Generate an inbox name for a project entity.

    Args:
        project_id: The project ID.
        entity_id: The entity ID within the project.

    Returns:
        Inbox name string.
    """
    return f"inbox:{project_id}:{entity_id}"
