"""Stub module."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "RemoteExecutor",
    "RemoteExecutorError",
    "RemoteResult",
    "RemoteTask",
    "_load_nodes_from_env",
    "_load_ssh_user_from_env",
]


def _load_ssh_user_from_env() -> str | None:
    """Load SSH username from environment variables.

    Returns:
        SSH username or None if not set.
    """
    import os

    return os.environ.get("SSH_USER") or os.environ.get("USER") or None


def _load_nodes_from_env() -> list[dict]:
    """Load compute nodes from environment variables.

    Returns:
        List of node configuration dictionaries.
    """
    import os

    nodes = []
    node_count = int(os.environ.get("REMOTE_NODE_COUNT", "0"))
    for i in range(node_count):
        node = {
            "id": os.environ.get(f"REMOTE_NODE_{i}_ID", f"node-{i}"),
            "url": os.environ.get(f"REMOTE_NODE_{i}_URL", "http://localhost:8080"),
            "capacity": float(os.environ.get(f"REMOTE_NODE_{i}_CAPACITY", "1.0")),
        }
        nodes.append(node)
    return nodes


@dataclass
class RemoteTask:
    """A task to be executed remotely."""

    id: str = ""
    name: str = ""
    payload: Any = None
    priority: int = 0
    timeout_seconds: float = 60.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "payload": self.payload,
            "priority": self.priority,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RemoteTask:
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            payload=data.get("payload"),
            priority=data.get("priority", 0),
            timeout_seconds=data.get("timeout_seconds", 60.0),
            metadata=data.get("metadata", {}),
        )


class RemoteExecutorError(Exception):
    """Error raised when remote execution fails."""

    def __init__(self, message: str, task_id: str = "") -> None:
        super().__init__(message)
        self.task_id = task_id


class RemoteExecutor:
    def __init__(self) -> None:
        self._tasks: dict = {}

    def execute(self, task: dict) -> dict:
        return {"status": "success", "task_id": task.get("id")}


@dataclass
class RemoteResult:
    """Result of a remote execution."""

    task_id: str = ""
    status: str = "pending"
    output: Any = None
    error: str = ""
    execution_time_ms: float = 0.0

    def is_success(self) -> bool:
        """Check if the result indicates success."""
        return self.status == "success"

    def is_error(self) -> bool:
        """Check if the result indicates an error."""
        return self.status == "error"
