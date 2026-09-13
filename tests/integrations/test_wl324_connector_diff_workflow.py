"""Integration tests for WL-324 connector diff workflow output wiring."""

from __future__ import annotations

import json

import pytest

from thegent.integrations.workstream_autosync import (
    WorkstreamAutosyncConfig,
    WorkstreamAutosyncRunner,
)


@pytest.mark.asyncio
@pytest.mark.requirement("WL-324")
async def test_connector_diff_workflow_output_includes_dry_run_artifact_path(tmp_path) -> None:
    """Cycle/status outputs expose connector diff workflow schema with dry-run artifact path."""
    work_stream_path = tmp_path / "WORK_STREAM.md"
    work_stream_path.write_text(
        "### [WL-324] Connector diff workflow\n**Status:** BACKLOG\n**Priority:** P2\n**Area:** sync\n",
        encoding="utf-8",
    )
    manifest_path = tmp_path / "cycle_manifest.jsonl"

    config = WorkstreamAutosyncConfig(
        enabled=True,
        github_enabled=False,
        linear_enabled=False,
        work_stream_path=work_stream_path,
        status_file_path=tmp_path / "autosync_status.json",
        cycle_manifest_path=manifest_path,
        cycle_metrics_path=tmp_path / "cycle_metrics.jsonl",
        trend_file_path=tmp_path / "trend.jsonl",
        failure_queue_path=tmp_path / "failure_queue.json",
        checkpoint_file_path=tmp_path / "checkpoint.json",
        change_digest_path=tmp_path / "change_digest.jsonl",
        incident_bundle_path=tmp_path / "incident_snapshots.jsonl",
        standalone_mode=True,
    )
    runner = WorkstreamAutosyncRunner(config)

    await runner._perform_sync_cycle()

    status = runner.get_status()
    assert status["connector_diff_workflow"] == {
        "dry_run_diff_artifact_path": "artifacts/workstream_autosync_dry_run_diff.txt"
    }

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8").splitlines()[-1])
    assert manifest_payload["outputs"]["connector_diff_workflow"] == {
        "dry_run_diff_artifact_path": "artifacts/workstream_autosync_dry_run_diff.txt"
    }
