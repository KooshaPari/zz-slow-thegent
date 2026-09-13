"""Application commands - CQRS command handlers."""

from dataclasses import dataclass

from ..domain.entities import MergeStrategy, QueuePriority


@dataclass
class AcquireLockCommand:
    """Command to acquire a lock on a command."""
    cmd_hash: str
    pid: int
    output_path: str | None = None
    timeout_seconds: int = 3600


@dataclass
class ReleaseLockCommand:
    """Command to release a lock."""
    cmd_hash: str
    pid: int


@dataclass
class EnqueueTaskCommand:
    """Command to enqueue a task."""
    command: str
    priority: QueuePriority = QueuePriority.NORMAL
    cwd: str | None = None
    env: dict[str, str] | None = None
    timeout_seconds: int = 3600


@dataclass
class MergeCommand:
    """Command to perform a merge operation."""
    base_commit: str
    theirs_commit: str
    ours_commit: str
    strategy: MergeStrategy = MergeStrategy.AUTO
