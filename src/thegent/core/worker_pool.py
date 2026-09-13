"""Core worker pool implementation."""
from __future__ import annotations

from typing import Any


class Worker:
    """A worker."""

    def __init__(self, worker_id: str) -> None:
        self.worker_id = worker_id
        self.busy = False


class WorkerPool:
    """Pool of workers."""

    def __init__(self, size: int = 4) -> None:
        self.size = size
        self.workers = [Worker(f"worker_{i}") for i in range(size)]

    def get_worker(self) -> Worker | None:
        """Get an available worker."""
        for w in self.workers:
            if not w.busy:
                return w
        return self.workers[0] if self.workers else None

    def release(self, worker: Worker) -> None:
        """Release a worker back to the pool."""
        worker.busy = False


class PersistentWorkerPool(WorkerPool):
    """Worker pool that persists across tasks."""

    def __init__(self, size: int = 4) -> None:
        super().__init__(size)
        self._task_count: int = 0

    def submit(self, task: dict[str, Any]) -> dict[str, Any]:
        """Submit a persistent task."""
        self._task_count += 1
        return {"task_id": self._task_count, "status": "submitted"}


class AgentTask:
    """Agent task representation."""

    def __init__(self, task_id: str, agent_id: str, payload: dict[str, Any]) -> None:
        self.task_id = task_id
        self.agent_id = agent_id
        self.payload = payload

    def to_dict(self) -> dict[str, Any]:
        return {"task_id": self.task_id, "agent_id": self.agent_id, "payload": self.payload}


class AgentResult:
    """Result of an agent operation."""

    def __init__(self, agent_id: str, success: bool, result: Any | None = None) -> None:
        self.agent_id = agent_id
        self.success = success
        self.result = result

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "success": self.success,
            "result": self.result,
        }


__all__ = ["Worker", "WorkerPool", "AgentResult", "AgentTask", "PersistentWorkerPool", "get_worker_pool"]


def get_worker_pool() -> WorkerPool:
    """Get the global worker pool instance."""
    return WorkerPool()
