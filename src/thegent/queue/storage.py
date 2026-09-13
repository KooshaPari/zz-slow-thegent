"""Queue storage module (AUDIT-N+39 hardened).

In-memory legacy ``QueueStorage`` plus the ``PromptQueue`` class
which persists pending prompts under ``<storage_dir>/prompt_queue.jsonl``
so deferral injection has a stable on-disk format.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class QueueStorage:
    """Storage for queue."""

    def __init__(self) -> None:
        self._storage: dict = {}

    def push(self, queue: str, item: dict) -> None:
        if queue not in self._storage:
            self._storage[queue] = []
        self._storage[queue].append(item)

    def pop(self, queue: str) -> dict | None:
        if self._storage.get(queue):
            return self._storage[queue].pop(0)
        return None


__all__ = ["QueueStorage", "PromptQueue"]


class PromptQueue:
    """Persistent prompt queue.

    AUDIT-N+39 hardened to back the deferral injection contract used
    by ``test_defer_injection.py`` -- JSONL on disk under
    ``<storage_dir>/prompt_queue.jsonl`` with ``append`` /
    ``list_all`` / ``list_pending`` / ``get_pending_count`` surface.
    """

    def __init__(self, storage_dir: Path | str | None = None) -> None:
        if storage_dir is None:
            storage_dir = Path.cwd()
        self.storage_dir = Path(storage_dir)
        self.queue_file = self.storage_dir / "prompt_queue.jsonl"
        self._in_memory: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Legacy in-memory API (preserved for the stub callers in AUDIT-N+33)
    # ------------------------------------------------------------------

    def enqueue(self, prompt: dict) -> None:
        """Enqueue a prompt (in-memory)."""
        self._in_memory.append(prompt)

    def dequeue(self) -> dict | None:
        if self._in_memory:
            return self._in_memory.pop(0)
        return None

    def peek(self) -> dict | None:
        if self._in_memory:
            return self._in_memory[0]
        return None

    def size(self) -> int:
        return len(self._in_memory)

    # ------------------------------------------------------------------
    # AUDIT-N+39 persistent API
    # ------------------------------------------------------------------

    def _load(self) -> list[dict[str, Any]]:
        if not self.queue_file.exists():
            return []
        items: list[dict[str, Any]] = []
        try:
            with self.queue_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError:
            return []
        return items

    def _save(self, items: list[dict[str, Any]]) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            dir=self.storage_dir, prefix=".queue_", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                for item in items:
                    f.write(json.dumps(item) + "\n")
            os.replace(tmp, self.queue_file)
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(tmp)
            raise

    def append(
        self,
        prompt: str,
        *,
        project: str | None = None,
        agent: str | None = None,
        status: str = "pending",
        source: str = "manual",
    ) -> dict[str, Any]:
        """Append a prompt row to the persistent queue."""
        item: dict[str, Any] = {
            "id": uuid.uuid4().hex,
            "prompt": prompt,
            "status": status,
            "source": source,
            "created_at": datetime.now(UTC).isoformat(),
        }
        if project is not None:
            item["project"] = project
        if agent is not None:
            item["agent"] = agent
        items = self._load()
        items.append(item)
        self._save(items)
        return item

    def list_all(self) -> list[dict[str, Any]]:
        return list(self._load())

    def list_pending(self) -> list[dict[str, Any]]:
        return [item for item in self._load() if item.get("status") == "pending"]

    def get_pending_count(self) -> int:
        return len(self.list_pending())

    def clear(self) -> None:
        self._save([])
