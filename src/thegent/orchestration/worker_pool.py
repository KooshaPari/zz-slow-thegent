"""Worker pool for orchestration."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class TaskRequest:
    """A task request for the worker pool."""

    command: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    cwd: str | None = None
    env: dict[str, str] = field(default_factory=dict)
    priority: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "command": self.command,
            "cwd": self.cwd,
            "env": self.env,
            "priority": self.priority,
            "created_at": self.created_at,
        }


@dataclass
class TaskResult:
    """Result from a task execution."""

    task_id: str
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    duration_s: float = 0.0
    ended_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_s": self.duration_s,
            "ended_at": self.ended_at,
        }


class TaskWorkerPool:
    """Pool of workers for task processing using file-based queue."""

    def __init__(
        self,
        max_workers: int = 4,
        queue_dir: Path | None = None,
    ) -> None:
        self.max_workers = max_workers
        self.queue_dir = queue_dir or Path("/tmp/thegent/queue")
        self.inbox = self.queue_dir / "inbox"
        self.results = self.queue_dir / "results"
        self._running = False

        # Create directories
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(exist_ok=True)
        self.results.mkdir(exist_ok=True)

    def submit_task(self, task: TaskRequest) -> Path:
        """Submit a task to the pool.

        Returns the path to the task file.
        """
        task_file = self.inbox / f"{task.id}.json"
        task_file.write_text(json.dumps(task.to_dict()))
        return task_file

    def get_result(self, task_id: str, timeout: float = 30.0) -> TaskResult | None:
        """Get the result of a task.

        Args:
            task_id: The ID of the task.
            timeout: How long to wait for the result.

        Returns:
            TaskResult if found, None otherwise.
        """
        result_file = self.results / f"{task_id}.json"
        deadline = time.time() + timeout

        while time.time() < deadline:
            if result_file.exists():
                try:
                    data = json.loads(result_file.read_text())
                    result_file.unlink()
                    return TaskResult(
                        task_id=data["task_id"],
                        exit_code=data.get("exit_code", 0),
                        stdout=data.get("stdout", ""),
                        stderr=data.get("stderr", ""),
                        duration_s=data.get("duration_s", 0.0),
                        ended_at=data.get("ended_at", ""),
                    )
                except (json.JSONDecodeError, KeyError):
                    result_file.unlink()
                    return None
            time.sleep(0.1)

        return None

    def stop(self) -> None:
        """Stop the worker pool."""
        self._running = False


class Worker:
    """A worker in the pool."""

    def __init__(self, worker_id: str) -> None:
        self.worker_id = worker_id
        self.busy = False

    def process(self, task: Any) -> Any:
        """Process a task."""
        return task


class WorkerPool:
    """Pool of workers for task processing."""

    def __init__(self, size: int = 4) -> None:
        self.size = size
        self.workers = [Worker(f"worker_{i}") for i in range(size)]

    def submit(self, task: Any) -> Any:
        """Submit a task to the pool."""
        for worker in self.workers:
            if not worker.busy:
                return worker.process(task)
        return self.workers[0].process(task)

    def shutdown(self) -> None:
        """Shutdown the worker pool."""


__all__ = ["TaskRequest", "TaskResult", "TaskWorkerPool", "Worker", "WorkerPool"]
