from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from thegent.observability.observability_v2 import AdvancedMetrics, MeshCLI


def test_advanced_metrics_aggregate_by_agent_and_command(tmp_path: Path) -> None:
    metrics_file = tmp_path / "metrics.jsonl"
    metrics = AdvancedMetrics(metrics_file)

    metrics.record("agent-a", "build", duration=10.0, success=True)
    metrics.record("agent-a", "build", duration=30.0, success=False)
    metrics.record("agent-b", "test", duration=50.0, success=True)

    summary = metrics.aggregate()
    assert summary["total_count"] == 3
    assert summary["success_count"] == 2
    assert summary["error_count"] == 1
    assert summary["duration_ms"]["max"] == 50.0
    assert summary["duration_ms"]["p95"] == 30.0

    group = summary["by_agent_command"]["agent-a:build"]
    assert group["count"] == 2
    assert group["success_count"] == 1
    assert group["error_count"] == 1
    assert group["duration_ms"]["mean"] == 20.0


def test_advanced_metrics_aggregate_rejects_invalid_jsonl(tmp_path: Path) -> None:
    metrics_file = tmp_path / "metrics.jsonl"
    metrics_file.write_text("{bad-json}\n", encoding="utf-8")
    metrics = AdvancedMetrics(metrics_file)

    with pytest.raises(ValueError, match="invalid JSONL metrics entry"):
        metrics.aggregate()


def test_mesh_cli_status_handles_missing_agents_dir(tmp_path: Path) -> None:
    status = MeshCLI.status(tmp_path)
    assert status["total_agents"] == 0
    assert status["alive_agents"] == 0
    assert status["agents"] == []


def test_mesh_cli_status_parses_manifests(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir(parents=True)
    manifest = agents_dir / "agent-123.yaml"
    manifest.write_text("pid: 123\ntype: codex\n", encoding="utf-8")

    class _Proc:
        def __init__(self, _pid: int) -> None:
            return None

        def is_running(self) -> bool:
            return True

    monkeypatch.setitem(sys.modules, "psutil", SimpleNamespace(Process=_Proc))
    status = MeshCLI.status(tmp_path)

    assert status["total_agents"] == 1
    assert status["alive_agents"] == 1
    assert status["agents"][0]["type"] == "codex"
    assert status["agents"][0]["status"] == "running"


def test_mesh_cli_tasks_counts_maildir_buckets(tmp_path: Path) -> None:
    queue_root = tmp_path / "queue"
    (queue_root / "new").mkdir(parents=True)
    (queue_root / "cur").mkdir(parents=True)
    (queue_root / "tmp").mkdir(parents=True)
    (queue_root / "new" / "a.task").write_text("{}", encoding="utf-8")
    (queue_root / "cur" / "b.task").write_text("{}", encoding="utf-8")
    (queue_root / "tmp" / "c.task").write_text("{}", encoding="utf-8")

    tasks = MeshCLI.tasks(tmp_path)
    assert tasks["pending_count"] == 1
    assert tasks["inflight_count"] == 1
    assert tasks["failed_count"] == 1
    assert tasks["pending_ids"] == ["a.task"]
    assert tasks["inflight_ids"] == ["b.task"]
    assert tasks["failed_ids"] == ["c.task"]
