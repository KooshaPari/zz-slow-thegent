"""Stub module."""

from dataclasses import dataclass
from typing import Any


@dataclass
class DeadLetterQueueEntry:
    """Entry in the dead letter queue."""

    id: str
    data: dict[str, Any]
    error: str


@dataclass
class RemoteWriteDeadLetterRecord:
    """Record for remote write dead letter queue."""

    record_id: str
    payload: dict[str, Any]
    status: str = "pending"


class RemoteWriteDeadLetterQueue:
    """Dead letter queue with remote write support."""

    def __init__(self) -> None:
        self.entries: list[DeadLetterQueueEntry] = []

    def enqueue(self, id: str, data: dict[str, Any], error: str) -> None:
        """Add entry to queue."""
        self.entries.append(DeadLetterQueueEntry(id=id, data=data, error=error))

    def dequeue(self) -> DeadLetterQueueEntry | None:
        """Remove and return next entry."""
        if self.entries:
            return self.entries.pop(0)
        return None


__all__ = [
    "DeadLetterQueueEntry",
    "RemoteWriteDeadLetterQueue",
    "RemoteWriteDeadLetterRecord",
    "DEFAULT_BOARD_DEAD_LETTER_BACKOFF_MULTIPLIER",
    "DEFAULT_BOARD_DEAD_LETTER_MAX_ATTEMPTS",
    "DEFAULT_BOARD_DEAD_LETTER_RETRY_DELAY_SECONDS",
    "compute_backoff_seconds",
]

DEFAULT_BOARD_DEAD_LETTER_BACKOFF_MULTIPLIER = 2.0
DEFAULT_BOARD_DEAD_LETTER_MAX_ATTEMPTS = 5
DEFAULT_BOARD_DEAD_LETTER_RETRY_DELAY_SECONDS = 5.0


def compute_backoff_seconds(
    attempt: int,
    base_delay: float = 1.0,
    multiplier: float = 2.0,
    max_delay: float = 60.0,
) -> float:
    """Compute exponential backoff seconds for retry attempts."""
    delay = base_delay * (multiplier**attempt)
    return min(delay, max_delay)
