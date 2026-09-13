"""Lane B coverage for WL-172, WL-173, WL-175, WL-176, WL-169 integration."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import orjson as json
import pytest
from typer.testing import CliRunner

from thegent.cli.apps.sync import app
from thegent.integrations.workstream_autosync import (
    WorkstreamAutosyncConfig,
    WorkstreamAutosyncRunner,
    WorkstreamItem,
)
from thegent.mcp.manage import mcp_down, mcp_up


def _autopilot_config(**overrides: Any) -> Any:
    base = {
        "enabled": True,
        "cycle_interval_seconds": 300,
        "dry_run": False,
        "bootstrap_required_fields": [],
        "bootstrap_mapping_cache_path": None,
        "bootstrap_connector": "github",
        "github_enabled": False,
        "github_owner": "",
        "github_project_number": 0,
        "linear_enabled": False,
        "linear_api_key": "",
        "linear_team_key": "",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.unit
@pytest.mark.requirement("WL-172")
def test_autopilot_doctor_reports_missing_core_enablement(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _autopilot_config(enabled=False)
    monkeypatch.setattr("thegent.integrations.workstream_autosync.load_autosync_config_from_env", lambda: config)

    result = CliRunner().invoke(app, ["autopilot", "doctor", "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "autosync_enabled" in payload["failed_checks"]


@pytest.mark.unit
@pytest.mark.requirement("WL-172")
def test_autopilot_doctor_reports_missing_required_mappings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mapping_cache = tmp_path / "mapping_cache.json"
    config = _autopilot_config(
        bootstrap_required_fields=["Status", "Priority"],
        bootstrap_mapping_cache_path=mapping_cache,
        bootstrap_connector="github",
        github_enabled=True,
        github_owner="kooshapari",
        github_project_number=1,
    )
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
    monkeypatch.setattr("thegent.integrations.workstream_autosync.load_autosync_config_from_env", lambda: config)

    result = CliRunner().invoke(app, ["autopilot", "doctor", "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "field_mappings" in payload["failed_checks"]


@pytest.mark.unit
@pytest.mark.requirement("WL-173")
def test_cycle_metrics_emitted_per_sync_cycle(tmp_path: Path) -> None:
    work_stream_path = tmp_path / "WORK_STREAM.md"
    work_stream_path.write_text(
        "### [WL-100] Sample\n**Status:** BACKLOG\n**Priority:** P1\n**Area:** sync\n",
        encoding="utf-8",
    )
    cycle_metrics_path = tmp_path / "cycle_metrics.jsonl"
    config = WorkstreamAutosyncConfig(
        enabled=True,
        github_enabled=False,
        linear_enabled=False,
        work_stream_path=work_stream_path,
        cycle_metrics_path=cycle_metrics_path,
        trend_file_path=tmp_path / "trend.jsonl",
        status_file_path=tmp_path / "status.json",
        cycle_manifest_path=tmp_path / "manifest.jsonl",
        failure_queue_path=tmp_path / "failures.json",
        checkpoint_file_path=tmp_path / "checkpoint.json",
    )
    runner = WorkstreamAutosyncRunner(config)

    asyncio.run(runner._perform_sync_cycle())

    assert cycle_metrics_path.exists()
    records = [json.loads(line) for line in cycle_metrics_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(records) == 1
    assert records[0]["status"] == "success"
    assert records[0]["item_count"] == 1


@pytest.mark.unit
@pytest.mark.requirement("WL-175")
def test_single_writer_lock_blocking_marks_cycle_failed(tmp_path: Path) -> None:
    work_stream_path = tmp_path / "WORK_STREAM.md"
    work_stream_path.write_text(
        "### [WL-101] Contended\n**Status:** BACKLOG\n**Priority:** P1\n**Area:** sync\n",
        encoding="utf-8",
    )
    lock_path = tmp_path / "autosync.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    config = WorkstreamAutosyncConfig(
        enabled=True,
        github_enabled=True,
        github_owner="kooshapari",
        github_project_number=1,
        work_stream_path=work_stream_path,
        writer_lock_enabled=True,
        writer_lock_path=lock_path,
        status_file_path=tmp_path / "status.json",
        cycle_metrics_path=tmp_path / "metrics.jsonl",
        trend_file_path=tmp_path / "trend.jsonl",
        cycle_manifest_path=tmp_path / "manifest.jsonl",
        failure_queue_path=tmp_path / "failures.json",
        checkpoint_file_path=tmp_path / "checkpoint.json",
    )
    holder = WorkstreamAutosyncRunner(config)
    contender = WorkstreamAutosyncRunner(config)
    assert holder._writer_lock.acquire("lane-b-holder")

    asyncio.run(contender._perform_sync_cycle())

    assert contender.last_error is not None
    assert "single-writer lock unavailable" in contender.last_error
    holder._writer_lock.release("lane-b-holder")


@pytest.mark.unit
@pytest.mark.requirement("WL-169")
def test_rate_limit_failures_trigger_bounded_backoff_retries(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config = WorkstreamAutosyncConfig(
        enabled=True,
        github_enabled=True,
        github_owner="kooshapari",
        github_project_number=1,
        rate_limit_max_retries=2,
        rate_limit_initial_wait=0.01,
        rate_limit_max_wait=0.01,
        rate_limit_multiplier=2.0,
        failure_queue_path=tmp_path / "failures.json",
        checkpoint_file_path=tmp_path / "checkpoint.json",
    )
    runner = WorkstreamAutosyncRunner(config)
    sleep_calls: list[float] = []

    async def _failing_sync(_items: list[WorkstreamItem]) -> None:
        raise RuntimeError("429 rate limit")

    async def _fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr("thegent.integrations.workstream_autosync.asyncio.sleep", _fake_sleep)
    item = WorkstreamItem(item_id="WL-102", title="R", status="BACKLOG", priority="P1", area="sync")

    asyncio.run(
        runner._sync_in_partitions(
            connector="github",
            direction="write",
            items=[item],
            sync_fn=_failing_sync,
        )
    )

    assert len(sleep_calls) == 2
    assert all(delay >= 0.0 for delay in sleep_calls)


@pytest.mark.unit
@pytest.mark.requirement("WL-176")
def test_mcp_up_skips_when_services_already_healthy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    compose_file = tmp_path / "process-compose.yaml"
    compose_file.write_text("version: '0.5'\n", encoding="utf-8")
    monkeypatch.setattr("thegent.mcp.manage._process_compose_path", lambda: compose_file)
    monkeypatch.setattr("thegent.mcp.manage.shutil.which", lambda _: "/usr/local/bin/process-compose")
    monkeypatch.setattr("thegent.mcp.manage._services_healthy", lambda _settings: True)
    called = {"ran": False}

    def _unexpected_run(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        called["ran"] = True
        raise AssertionError("run_subprocess_optimized should not be called when services are already healthy")

    monkeypatch.setattr("thegent.mcp.manage.run_subprocess_optimized", _unexpected_run)

    ok, message = mcp_up()

    assert ok is True
    assert "already healthy" in message.lower()
    assert called["ran"] is False


@pytest.mark.unit
@pytest.mark.requirement("WL-176")
def test_mcp_down_uses_explicit_compose_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    compose_file = tmp_path / "process-compose.yaml"
    compose_file.write_text("version: '0.5'\n", encoding="utf-8")
    monkeypatch.setattr("thegent.mcp.manage._process_compose_path", lambda: compose_file)
    monkeypatch.setattr("thegent.mcp.manage.shutil.which", lambda _: "/usr/local/bin/process-compose")
    captured: dict[str, Any] = {}

    def _run(args: list[str], **kwargs: Any) -> Any:
        captured["args"] = args
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("thegent.mcp.manage.run_subprocess_optimized", _run)

    ok, _message = mcp_down()

    assert ok is True
    assert "-f" in captured["args"]
    assert str(compose_file) in captured["args"]
