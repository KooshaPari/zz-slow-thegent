"""In-memory queue adapter for task queue operations."""


from ..domain.entities import QueuePriority, TaskQueueItem


class InMemoryQueueAdapter:
    """In-memory implementation of QueuePort for testing and local use."""

    def __init__(self) -> None:
        self._queue: list[TaskQueueItem] = []

    def enqueue(self, item: TaskQueueItem) -> TaskQueueItem:
        """Add item to queue."""
        self._queue.append(item)
        # Sort by priority
        self._queue.sort(key=lambda x: (
            0 if x.priority == QueuePriority.CRITICAL else
            1 if x.priority == QueuePriority.HIGH else
            2 if x.priority == QueuePriority.NORMAL else 3
        ))
        return item

    def dequeue(self) -> TaskQueueItem | None:
        """Remove and return next item."""
        if not self._queue:
            return None
        item = self._queue.pop(0)
        item.status = "dequeued"
        return item

    def peek(self) -> TaskQueueItem | None:
        """View next item without removing."""
        if not self._queue:
            return None
        return self._queue[0]

    def length(self) -> int:
        """Get queue length."""
        return len(self._queue)

    def clear(self) -> None:
        """Clear the queue."""
        self._queue.clear()

    def list_all(self) -> list[TaskQueueItem]:
        """List all queued items."""
        return list(self._queue)


__all__ = ["InMemoryQueueAdapter"]
