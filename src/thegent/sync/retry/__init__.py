"""Stub module."""

from typing import Any


class RetryPolicy:
    """Retry policy for sync operations."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Check if operation should be retried."""
        return attempt < self.max_retries

    def get_delay(self, attempt: int) -> float:
        """Get delay before next retry."""
        import math

        return min(self.base_delay * (2**attempt), self.max_delay)


class OperationMode:
    """Operation mode for retries."""

    SYNC = "sync"
    ASYNC = "async"


operation_mode = OperationMode()


def should_retry(attempt: int, max_retries: int) -> bool:
    """Check if should retry."""
    return attempt < max_retries


__all__ = ["RetryPolicy", "OperationMode", "operation_mode", "should_retry"]
