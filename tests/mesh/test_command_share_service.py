from pathlib import Path

import pytest

from thegent.mesh.command_share import CommandShareService
from thegent.mesh.contracts import CommandKey, MergeCommand


def test_service_shares_lock_queue_and_events(tmp_path: Path):
    service = CommandShareService(tmp_path / "mesh")
    key = CommandKey("abc")

    assert service.acquire_lock(key, "agent-a") is True
    assert service.acquire_lock(key, "agent-b") is False
    task_id = service.enqueue({"command": "echo hi"}, priority=2, owner_id="agent-a")
    assert service.dequeue("agent-a")["id"] == task_id
    service.ack(task_id)
    assert [event.event_type.value for event in service.events] == [
        "lock.acquired",
        "task.enqueued",
        "task.claimed",
        "task.acked",
    ]


def test_service_release_and_merge_delegate(tmp_path: Path, monkeypatch):
    service = CommandShareService(tmp_path / "mesh")
    key = CommandKey("abc")
    service.acquire_lock(key, "agent-a")
    assert service.release_lock(key, "agent-a") is True
    called = {}
    monkeypatch.setattr(service.merger, "merge", lambda *args, **kwargs: called.setdefault("args", args))
    result = service.merge(MergeCommand("base", "ours", "theirs"), "out")
    assert result == ("base", "ours", "theirs", "out")


def test_events_redact_secrets_and_bound_payload(tmp_path: Path):
    service = CommandShareService(tmp_path / "mesh")
    service.enqueue({"api_key": "secret", "nested": {"password": "pw", "ok": "x" * 500}})
    event = service.events[-1]
    assert event.payload["payload"]["api_key"] == "[REDACTED]"
    assert event.payload["payload"]["nested"]["password"] == "[REDACTED]"
    assert len(event.payload["payload"]["nested"]["ok"]) <= 256


def test_queue_restart_and_reclaim(tmp_path: Path):
    root = tmp_path / "mesh"
    first = CommandShareService(root)
    task_id = first.enqueue({"x": 1}, owner_id="agent")
    assert first.dequeue("agent")["id"] == task_id
    second = CommandShareService(root)
    assert second.queue.reclaim_owner("agent") == 1
    task = second.dequeue("agent")
    second.nack(task["id"], "agent")
    assert second.queue.list_pending()[0]["id"] == task_id


def test_result_path_confined_to_mesh_root(tmp_path: Path):
    service = CommandShareService(tmp_path / "mesh")
    assert service.confine_result_path("results/out.json").parent == tmp_path / "mesh" / "results"
    with pytest.raises(ValueError):
        service.confine_result_path("../escape")


def test_redacted_event_replay_retains_correlation(tmp_path: Path):
    service = CommandShareService(tmp_path / "mesh")
    service.enqueue({"token": "hidden", "message": "ok"})
    event = service.events[-1]
    replay = event.__class__(
        event.event_type,
        event.actor_id,
        event.correlation_id,
        payload=event.payload,
        event_id=event.event_id,
        occurred_at=event.occurred_at,
    )
    assert replay.correlation_id == event.correlation_id
    assert replay.payload["payload"]["token"] == "[REDACTED]"
