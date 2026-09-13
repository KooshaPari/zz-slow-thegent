"""Deterministic cross-runtime coordination contract fixture."""

import json

from .adapters.dedup import InMemoryLockAdapter
from .adapters.queue import InMemoryQueueAdapter
from .domain.entities import EditIntent, QueuePriority, TaskQueueItem
from .domain.value_objects import CommandHash


def run_contract() -> list[dict[str, object]]:
    """Exercise normalized lock, queue, and edit-intent behavior."""
    lock_adapter = InMemoryLockAdapter()
    command_hash = CommandHash("coordination-lock-queue-v1")
    records: list[dict[str, object]] = []

    acquired = lock_adapter.acquire(command_hash, 101)
    records.append({"case": "lock_acquire", "outcome": "locked", "owner": acquired.pid})

    try:
        lock_adapter.acquire(command_hash, 202)
    except ValueError as error:
        if str(error) != "already locked":
            raise
        records.append({"case": "lock_contention", "outcome": "already_locked", "owner": 101})
    else:
        raise AssertionError("a different PID must not acquire a held lock")

    lock_adapter.release(command_hash, 101)
    records.append({"case": "lock_release", "outcome": "unlocked"})

    reacquired = lock_adapter.acquire(command_hash, 202)
    records.append({"case": "lock_reacquire", "outcome": "locked", "owner": reacquired.pid})

    queue_adapter = InMemoryQueueAdapter()
    for command, priority in (
        ("low", QueuePriority.LOW),
        ("normal", QueuePriority.NORMAL),
        ("high", QueuePriority.HIGH),
        ("critical", QueuePriority.CRITICAL),
    ):
        queue_adapter.enqueue(TaskQueueItem(command=command, priority=priority))
    records.append(
        {
            "case": "priority_dequeue",
            "commands": [queue_adapter.dequeue().command for _ in range(4)],
        }
    )

    base = EditIntent(agent_id="agent-a", file_path="fixture.rs", start_line=10, end_line=20)
    disjoint = EditIntent(agent_id="agent-b", file_path="fixture.rs", start_line=30, end_line=40)
    overlap = EditIntent(agent_id="agent-c", file_path="fixture.rs", start_line=15, end_line=25)
    records.append({"case": "edit_disjoint", "conflict": base.conflicts_with(disjoint)})
    records.append({"case": "edit_overlap", "conflict": base.conflicts_with(overlap)})
    return records


def main() -> None:
    """Emit the stable contract as compact JSON Lines."""
    for record in run_contract():
        print(json.dumps(record, separators=(",", ":")))


if __name__ == "__main__":
    main()
