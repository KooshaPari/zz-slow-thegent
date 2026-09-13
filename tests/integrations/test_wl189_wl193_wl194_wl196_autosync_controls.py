"""Integration tests for WL-189/WL-193/WL-194/WL-196 autosync controls."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from thegent.integrations.connector_mapping_cache import ConnectorMappingCache
from thegent.integrations.workstream_autosync import (
    SyncDirection,
    WorkstreamAutosyncConfig,
    WorkstreamAutosyncError,
    WorkstreamAutosyncRunner,
    WorkstreamItem,
    load_autosync_config_from_env,
)
from thegent.utils.routing_impl.circuit_breaker import ProviderCircuitBreakerRegistry


@pytest.fixture(autouse=True)
def _reset_breakers() -> None:
    ProviderCircuitBreakerRegistry.reset_instance()
    yield
    ProviderCircuitBreakerRegistry.reset_instance()


@pytest.fixture
def sample_workstream(tmp_path: Path) -> Path:
    path = tmp_path / "WORK_STREAM.md"
    path.write_text(
        """### [WL-189] Ignore candidate\n**Status:** BACKLOG\n**Priority:** P2\n**Area:** sync\n\n### [WL-196] Keep me\n**Status:** IN PROGRESS\n**Priority:** P1\n**Area:** observability\n""",
        encoding="utf-8",
    )
    return path


@pytest.mark.asyncio
@pytest.mark.requirement("WL-189")
async def test_wl_ignore_list_excludes_ids_from_sync(sample_workstream: Path) -> None:
    config = WorkstreamAutosyncConfig(
        enabled=True,
        github_enabled=True,
        github_owner="owner",
        github_project_number=1,
        github_direction=SyncDirection.WRITE_ONLY,
        work_stream_path=sample_workstream,
        wl_ignore_list=["WL-189"],
        standalone_mode=False,
    )
    runner = WorkstreamAutosyncRunner(config)

    captured_ids: list[str] = []

    async def capture(items: list[WorkstreamItem]) -> None:
        captured_ids.extend(item.item_id for item in items)

    runner._sync_to_github = capture  # type: ignore[method-assign]

    await runner._perform_sync_cycle()

    assert "WL-189" not in captured_ids
    assert "WL-196" in captured_ids
    assert runner.get_status()["ignored_wl_ids"] == ["WL-189"]


@pytest.mark.requirement("WL-189")
def test_wl_ignore_list_loads_from_env() -> None:
    env = {
        "THGENT_WORKSTREAM_AUTOSYNC_ENABLED": "true",
        "THGENT_GITHUB_ENABLED": "true",
        "THGENT_GITHUB_OWNER": "owner",
        "THGENT_GITHUB_PROJECT_NUMBER": "1",
        "THGENT_WORKSTREAM_WL_IGNORE_LIST": "WL-189,wl-196",
    }
    with pytest.MonkeyPatch.context() as mp:
        for key, value in env.items():
            mp.setenv(key, value)
        config = load_autosync_config_from_env()

    assert config.wl_ignore_list == ["WL-189", "WL-196"]


@pytest.mark.requirement("WL-191")
def test_orphan_report_uses_connector_mapping_cache(tmp_path: Path) -> None:
    cache_path = tmp_path / "connector_mapping_cache.json"
    cache = ConnectorMappingCache(cache_file=cache_path)
    cache.put("github", "WL-101", "remote_1")

    config = WorkstreamAutosyncConfig(
        connector_mapping_cache_path=cache_path,
        standalone_mode=True,
    )
    runner = WorkstreamAutosyncRunner(config)

    report = runner._compute_local_orphan_report(
        [
            WorkstreamItem("WL-101", "Mapped", "BACKLOG", "P1", "sync"),
            WorkstreamItem("WL-102", "Unmapped", "BACKLOG", "P1", "sync"),
        ]
    )

    assert report["mapped_remote_ids"] == ["WL-101"]
    assert report["local_orphan_ids"] == ["WL-102"]


@pytest.mark.asyncio
@pytest.mark.requirement("WL-193")
async def test_per_connector_timeout_enforced() -> None:
    config = WorkstreamAutosyncConfig(
        enabled=True,
        github_enabled=True,
        github_owner="owner",
        github_project_number=1,
        github_direction=SyncDirection.WRITE_ONLY,
        github_write_timeout_seconds=0.01,
        standalone_mode=False,
    )
    runner = WorkstreamAutosyncRunner(config)

    async def slow_sync(_items: list[WorkstreamItem]) -> None:
        await asyncio.sleep(0.1)

    with pytest.raises(WorkstreamAutosyncError, match="timed out"):
        await runner._sync_in_partitions(
            connector="github",
            direction="write",
            items=[WorkstreamItem("WL-193", "Timeout", "BACKLOG", "P2", "sync")],
            sync_fn=slow_sync,
        )


@pytest.mark.asyncio
@pytest.mark.requirement("WL-194")
async def test_connector_circuit_breaker_opens_after_repeated_failure() -> None:
    config = WorkstreamAutosyncConfig(
        enabled=True,
        github_enabled=True,
        github_owner="owner",
        github_project_number=1,
        github_direction=SyncDirection.WRITE_ONLY,
        connector_circuit_breaker_failure_threshold=1,
        connector_circuit_breaker_timeout_seconds=600.0,
        standalone_mode=False,
    )
    runner = WorkstreamAutosyncRunner(config)

    async def failing_sync(_items: list[WorkstreamItem]) -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await runner._sync_in_partitions(
            connector="github",
            direction="write",
            items=[WorkstreamItem("WL-194", "Breaker", "BACKLOG", "P1", "sync")],
            sync_fn=failing_sync,
        )

    with pytest.raises(WorkstreamAutosyncError, match="open connector circuit breaker"):
        await runner._sync_in_partitions(
            connector="github",
            direction="write",
            items=[WorkstreamItem("WL-194", "Breaker", "BACKLOG", "P1", "sync")],
            sync_fn=lambda _items: asyncio.sleep(0),
        )


@pytest.mark.asyncio
@pytest.mark.requirement("WL-196")
async def test_prometheus_metrics_export_written(sample_workstream: Path, tmp_path: Path) -> None:
    metrics_path = tmp_path / "autosync_metrics.prom"
    config = WorkstreamAutosyncConfig(
        enabled=True,
        github_enabled=True,
        github_owner="owner",
        github_project_number=1,
        github_direction=SyncDirection.WRITE_ONLY,
        work_stream_path=sample_workstream,
        autosync_prometheus_export_path=metrics_path,
        standalone_mode=False,
    )
    runner = WorkstreamAutosyncRunner(config)

    async def fast_sync(_items: list[WorkstreamItem]) -> None:
        return None

    runner._sync_to_github = fast_sync  # type: ignore[method-assign]

    await runner._perform_sync_cycle()

    text = metrics_path.read_text(encoding="utf-8")
    assert "thegent_autosync_cycles_total" in text
    assert 'thegent_autosync_cycle_outcomes_total{status="success"} 1' in text
    assert "thegent_autosync_cycle_duration_seconds_count" in text
    assert "thegent_autosync_connector_operations_total" in text
    assert "thegent_autosync_cycle_health" in text
