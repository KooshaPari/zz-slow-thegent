"""WL-332 tests for throttle telemetry in autosync cycle metrics."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from thegent.integrations.workstream_autosync import (
    SyncDirection,
    WorkstreamAutosyncConfig,
    WorkstreamAutosyncRunner,
    WorkstreamItem,
)


def _build_runner(tmp_path: Path) -> WorkstreamAutosyncRunner:
    config = WorkstreamAutosyncConfig(
        enabled=True,
        github_enabled=True,
        github_owner="example",
        github_project_number=1,
        github_direction=SyncDirection.WRITE_ONLY,
        standalone_mode=True,
        cycle_metrics_path=tmp_path / "cycle_metrics.jsonl",
        rate_limit_max_retries=2,
        rate_limit_initial_wait=0.2,
        rate_limit_max_wait=0.5,
        rate_limit_multiplier=2.0,
    )
    return WorkstreamAutosyncRunner(config)


def _read_cycle_metrics_record(path: Path) -> dict[str, object]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines
    return json.loads(lines[-1])


def test_wl332_cycle_metrics_include_throttle_fields_when_idle(tmp_path: Path) -> None:
    runner = _build_runner(tmp_path)
    started_at = datetime.now(UTC)
    completed_at = started_at + timedelta(seconds=1)

    runner._emit_cycle_metrics(
        started_at=started_at,
        completed_at=completed_at,
        item_count=0,
        status="success",
        no_op=True,
        no_op_reason="unit_test",
    )

    payload = _read_cycle_metrics_record(runner.config.cycle_metrics_path)

    assert "throttle_retry_attempts" in payload
    assert "throttle_wait_seconds" in payload
    assert payload["throttle_retry_attempts"] == 0
    assert payload["throttle_wait_seconds"] == 0.0


@pytest.mark.asyncio
async def test_wl332_cycle_metrics_capture_retry_wait_and_attempt_bounds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = _build_runner(tmp_path)
    items = [
        WorkstreamItem(
            item_id="WL-332",
            title="Throttle telemetry",
            status="IN PROGRESS",
            priority="P1",
            area="sync",
        )
    ]
    calls = {"count": 0}

    async def _flaky_sync(_: list[WorkstreamItem]) -> None:
        calls["count"] += 1
        if calls["count"] < 3:
            raise RuntimeError("HTTP 429 rate limit")

    async def _skip_sleep(_: float) -> None:
        return None

    monkeypatch.setattr("thegent.integrations.rate_limit_backoff.random.uniform", lambda _a, _b: 0.0)
    monkeypatch.setattr("thegent.integrations.workstream_autosync.asyncio.sleep", _skip_sleep)

    await runner._sync_in_partitions(
        connector="github",
        direction="write",
        items=items,
        sync_fn=_flaky_sync,
    )

    started_at = datetime.now(UTC)
    completed_at = started_at + timedelta(seconds=1)
    runner._emit_cycle_metrics(
        started_at=started_at,
        completed_at=completed_at,
        item_count=len(items),
        status="success",
        no_op=False,
        no_op_reason=None,
    )

    payload = _read_cycle_metrics_record(runner.config.cycle_metrics_path)

    assert payload["throttle_retry_attempts"] == 2
    assert payload["throttle_retry_attempts"] <= runner.config.rate_limit_max_retries
    assert payload["throttle_wait_seconds"] >= 0.0
    assert payload["throttle_wait_seconds"] <= (runner.config.rate_limit_max_wait * payload["throttle_retry_attempts"])
