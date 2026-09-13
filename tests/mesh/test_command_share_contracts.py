from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from thegent.mesh.contracts import (
    AcquireLockCommand,
    CommandKey,
    EventType,
    GetQueueDepthQuery,
    MeshEvent,
    QueuePort,
)


def test_command_key_is_stable_for_environment_order() -> None:
    first = CommandKey.from_request(
        "python -m worker",
        Path("/tmp/project"),
        {"B": "2", "A": "1", "SECRET": "do-not-hash"},
        "default",
        allowlisted_env={"A", "B"},
    )
    second = CommandKey.from_request(
        "python -m worker",
        Path("/tmp/project"),
        {"A": "1", "B": "2"},
        "default",
        allowlisted_env={"A", "B"},
    )

    assert first == second
    assert "do-not-hash" not in first.value


def test_command_key_changes_for_execution_context() -> None:
    base = CommandKey.from_request("echo hi", Path("/tmp/a"), {}, "default")
    changed = CommandKey.from_request("echo hi", Path("/tmp/b"), {}, "default")

    assert base != changed


def test_commands_are_immutable_and_queries_validate_priority() -> None:
    command = AcquireLockCommand(key=CommandKey("a"), owner_id="agent-1")
    with pytest.raises((AttributeError, TypeError)):
        command.owner_id = "agent-2"  # type: ignore[misc]

    assert GetQueueDepthQuery(priority=5).priority == 5
    with pytest.raises(ValueError):
        GetQueueDepthQuery(priority=10)


def test_mesh_event_has_correlation_and_utc_timestamp() -> None:
    event = MeshEvent(
        event_type=EventType.TASK_ENQUEUED,
        actor_id="agent-1",
        correlation_id="corr-1",
        payload={"task_id": "task-1"},
    )

    assert event.event_id
    assert event.occurred_at.tzinfo == UTC
    assert isinstance(event.occurred_at, datetime)
    assert event.payload == {"task_id": "task-1"}


def test_queue_port_exposes_existing_maildir_lifecycle() -> None:
    for method in (
        "enqueue",
        "dequeue",
        "ack",
        "nack",
        "list_pending",
        "reclaim_owner",
    ):
        assert hasattr(QueuePort, method)
