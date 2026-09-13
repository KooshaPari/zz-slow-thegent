"""Command sharing service composed from the durable mesh adapters."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
from uuid import uuid4

from .cache import Singleflight
from .contracts import (
    AcquireLockCommand,
    CommandKey,
    EnqueueTaskCommand,
    EventType,
    MergeCommand,
    MeshEvent,
    QueuePort,
    ReleaseLockCommand,
)
from .coordination import FileClaimsRegistry
from .smart_merge import SmartMerger
from .task_queue import MaildirQueue


class CommandShareService:
    """Application adapter; persistence remains owned by existing mesh ports."""

    def __init__(
        self,
        mesh_root: Path,
        *,
        merger: SmartMerger | None = None,
        queue: QueuePort | None = None,
    ) -> None:
        self.mesh_root = Path(mesh_root)
        self.mesh_root.mkdir(parents=True, exist_ok=True)
        self.claims = FileClaimsRegistry(self.mesh_root)
        self.queue = queue or MaildirQueue(self.mesh_root / "queue")
        self.merger = merger or SmartMerger()
        self.singleflight = Singleflight()
        self.events: list[MeshEvent] = []

    def _emit(self, event_type: EventType, actor_id: str, payload: dict[str, Any]) -> None:
        self.events.append(MeshEvent(event_type, actor_id, uuid4().hex, payload=self._redact(payload)))

    @classmethod
    def _redact(cls, value: Any, *, key: str = "") -> Any:
        if any(secret in key.lower() for secret in ("secret", "token", "password", "api_key", "apikey")):
            return "[REDACTED]"
        if isinstance(value, Mapping):
            return {str(k): cls._redact(v, key=str(k)) for k, v in value.items()}
        if isinstance(value, list):
            return [cls._redact(v) for v in value[:32]]
        if isinstance(value, str):
            return value[:256]
        return value

    def _claim_path(self, key: CommandKey) -> Path:
        return self.mesh_root / "command-claims" / key.value

    def acquire_lock(self, key: CommandKey, owner_id: str, ttl_seconds: int = 3600) -> bool:
        command = AcquireLockCommand(key, owner_id, ttl_seconds)
        acquired = self.singleflight.do(
            f"lock:{key.value}:{owner_id}",
            lambda: self.claims.acquire_lease(self._claim_path(command.key), command.owner_id, ttl=command.ttl_seconds),
        )
        if acquired:
            self._emit(EventType.LOCK_ACQUIRED, owner_id, {"key": key.value})
        return acquired

    def release_lock(self, key: CommandKey, owner_id: str) -> bool:
        command = ReleaseLockCommand(key, owner_id)
        released = self.claims.release_lease(self._claim_path(command.key), command.owner_id)
        if released:
            self._emit(EventType.LOCK_RELEASED, owner_id, {"key": key.value})
        return released

    def enqueue(self, payload: dict[str, Any], priority: int = 5, owner_id: str | None = None) -> str:
        command = EnqueueTaskCommand(payload, priority, owner_id)
        task_id = self.queue.enqueue(dict(command.payload), command.priority)
        self._emit(
            EventType.TASK_ENQUEUED,
            owner_id or "system",
            {"task_id": task_id, "payload": dict(command.payload)},
        )
        return task_id

    def confine_result_path(self, relative_path: str) -> Path:
        """Resolve a result path beneath the mesh root, rejecting traversal/symlinks."""
        candidate = (self.mesh_root / relative_path).resolve()
        root = self.mesh_root.resolve()
        if root not in candidate.parents and candidate != root:
            raise ValueError("result path escapes mesh root")
        current = self.mesh_root
        for part in Path(relative_path).parts:
            current /= part
            if current.is_symlink():
                raise ValueError("result path traverses symlink")
        return candidate

    def dequeue(self, owner_id: str | None = None) -> dict[str, Any] | None:
        task = self.queue.dequeue(owner_id)
        if task:
            self._emit(EventType.TASK_CLAIMED, owner_id or "system", {"task_id": task["id"]})
        return task

    def ack(self, task_id: str, actor_id: str = "system") -> None:
        self.queue.ack(task_id)
        self._emit(EventType.TASK_ACKED, actor_id, {"task_id": task_id})

    def nack(self, task_id: str, actor_id: str = "system") -> None:
        self.queue.nack(task_id)
        self._emit(EventType.TASK_NACKED, actor_id, {"task_id": task_id})

    def reclaim(self, owner_id: str) -> int:
        count = self.queue.reclaim_owner(owner_id)
        if count:
            self._emit(EventType.TASK_RECLAIMED, owner_id, {"count": count})
        return count

    def merge(self, command: MergeCommand, output: str, *, path_hint: str | None = None) -> Any:
        result = self.merger.merge(command.base, command.ours, command.theirs, output, path_hint=path_hint)
        self._emit(
            EventType.MERGE_COMPLETED,
            "system",
            {"success": getattr(result, "success", True)},
        )
        return result
