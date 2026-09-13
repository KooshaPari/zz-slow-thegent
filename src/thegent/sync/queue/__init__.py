"""Stub module."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ConflictQueueStore:
    """Store for conflict queue entries."""

    name: str = ""

    def enqueue(self, entry: dict[str, Any]) -> None:
        """Enqueue a conflict entry."""

    def dequeue(self) -> dict[str, Any] | None:
        """Dequeue a conflict entry."""
        return None


__all__ = ["ConflictQueueStore"]
