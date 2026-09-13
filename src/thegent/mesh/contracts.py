"""Typed contracts for mesh command sharing.

The contracts describe the existing mesh adapters; they do not own persistence.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class CommandKey:
    """Stable identity for one normalized command execution request."""

    value: str
    algorithm: str = "sha256"

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("command key cannot be empty")

    @classmethod
    def from_request(
        cls,
        command: str,
        cwd: Path,
        env: Mapping[str, str],
        execution_profile: str,
        *,
        allowlisted_env: set[str] | frozenset[str] | None = None,
    ) -> CommandKey:
        """Hash only explicitly allowlisted environment names."""
        allowed = allowlisted_env or frozenset()
        canonical = {
            "command": command,
            "cwd": str(cwd.resolve()),
            "env": {name: env[name] for name in sorted(allowed) if name in env},
            "profile": execution_profile,
        }
        payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        return cls(hashlib.sha256(payload).hexdigest())


@dataclass(frozen=True, slots=True)
class AcquireLockCommand:
    key: CommandKey
    owner_id: str
    ttl_seconds: int = 3600
    result_path: str | None = None

    def __post_init__(self) -> None:
        if not self.owner_id or self.ttl_seconds <= 0:
            raise ValueError("owner_id and positive ttl_seconds are required")


@dataclass(frozen=True, slots=True)
class ReleaseLockCommand:
    key: CommandKey
    owner_id: str


@dataclass(frozen=True, slots=True)
class EnqueueTaskCommand:
    payload: Mapping[str, Any]
    priority: int = 5
    owner_id: str | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.priority <= 9:
            raise ValueError("priority must be between 0 and 9")


class MergeStrategy(StrEnum):
    AUTO = "auto"
    OURS = "ours"
    THEIRS = "theirs"
    MANUAL = "manual"


@dataclass(frozen=True, slots=True)
class MergeCommand:
    base: str
    ours: str
    theirs: str
    strategy: MergeStrategy = MergeStrategy.AUTO


@dataclass(frozen=True, slots=True)
class GetLockQuery:
    key: CommandKey


@dataclass(frozen=True, slots=True)
class ListLocksQuery:
    include_expired: bool = False


@dataclass(frozen=True, slots=True)
class GetQueueDepthQuery:
    priority: int | None = None

    def __post_init__(self) -> None:
        if self.priority is not None and not 0 <= self.priority <= 9:
            raise ValueError("priority must be between 0 and 9")


@dataclass(frozen=True, slots=True)
class GetMergeCandidatesQuery:
    base_branch: str | None = None
    min_conflicts: int = 0

    def __post_init__(self) -> None:
        if self.min_conflicts < 0:
            raise ValueError("min_conflicts cannot be negative")


class EventType(StrEnum):
    LOCK_ACQUIRED = "lock.acquired"
    LOCK_RELEASED = "lock.released"
    LOCK_EXPIRED = "lock.expired"
    TASK_ENQUEUED = "task.enqueued"
    TASK_CLAIMED = "task.claimed"
    TASK_ACKED = "task.acked"
    TASK_NACKED = "task.nacked"
    TASK_RECLAIMED = "task.reclaimed"
    MERGE_PREDICTED = "merge.predicted"
    MERGE_COMPLETED = "merge.completed"


@dataclass(frozen=True, slots=True)
class MeshEvent:
    event_type: EventType
    actor_id: str
    correlation_id: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid4().hex)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class QueuePort(Protocol):
    def enqueue(self, task: Mapping[str, Any], priority: int = 5) -> str: ...

    def dequeue(self, owner: str | None = None) -> dict[str, Any] | None: ...

    def ack(self, task_id: str) -> None: ...

    def nack(self, task_id: str) -> None: ...

    def list_pending(self) -> list[dict[str, Any]]: ...

    def reclaim_owner(self, owner: str) -> int: ...
