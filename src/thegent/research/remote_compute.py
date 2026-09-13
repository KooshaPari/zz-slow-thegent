"""STUB MODULE - thegent.research.remote_compute

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

from typing import Any


class RemoteComputeClient:
    """Client for remote compute operations."""

    def __init__(self, endpoint: str = "") -> None:
        self.endpoint = endpoint

    def submit(self, task: dict[str, Any]) -> str:
        """Submit a task for remote execution."""
        return f"task_{id(task)}"

    def get_result(self, task_id: str) -> dict[str, Any] | None:
        """Get result of a remote task."""
        return None


__all__ = ["RemoteComputeClient"]
