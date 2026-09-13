"""Replay-based regression tests for governance spiral trend policy bands."""

from __future__ import annotations

import subprocess
from pathlib import Path

import orjson as json
import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _dispatcher_bin() -> Path:
    return _repo_root() / "hooks" / "hook-dispatcher" / "target" / "debug" / "hook-dispatcher"


@pytest.mark.unit
def test_spiral_trend_replay_manifest_invariants() -> None:
    dispatcher = _dispatcher_bin()
    assert dispatcher.exists(), f"Missing dispatcher binary: {dispatcher}"

    fixture_root = _repo_root() / "tests" / "fixtures" / "governance"
    replay_dir = fixture_root / "replay"
    manifest = json.loads((fixture_root / "spiral_trend_replay_manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] >= 1
    assert manifest["changelog"], "replay manifest changelog is required"

    for case in manifest["cases"]:
        metrics_file = replay_dir / case["file"]
        assert metrics_file.exists(), f"Missing replay fixture: {metrics_file}"

        proc = subprocess.run(
            [str(dispatcher), "governance", "spiral-trend", str(metrics_file), "--window", "50"],
            cwd=_repo_root(),
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(proc.stdout)

        assert set(payload.keys()) == {
            "source_file",
            "samples_total",
            "window_used",
            "breach_count",
            "breach_rate",
            "interrupt_count",
            "max_streak",
            "open_breach_streak",
            "mttr_proxy_cycles",
            "violations_delta",
            "stale_test_evidence_events",
            "stale_build_evidence_events",
            "stale_e2e_evidence_events",
            "pressure_score",
            "policy_band",
            "latest_status",
            "latest_severity",
            "latest_generated_at",
        }
        assert payload["samples_total"] >= 1
        assert payload["window_used"] == payload["samples_total"]
        assert payload["policy_band"] == case["expected_band"], (
            "spiral trend replay policy band drift detected. "
            "If intentional, bump schema_version and append changelog entry in "
            "tests/fixtures/governance/spiral_trend_replay_manifest.json."
        )
        assert case["min_pressure"] <= payload["pressure_score"] <= case["max_pressure"], (
            "spiral trend replay pressure range drift detected. "
            "If intentional, bump schema_version and append changelog entry in "
            "tests/fixtures/governance/spiral_trend_replay_manifest.json."
        )
        assert payload["latest_status"] == case["latest_status"], (
            "spiral trend replay latest_status drift detected. "
            "If intentional, bump schema_version and append changelog entry in "
            "tests/fixtures/governance/spiral_trend_replay_manifest.json."
        )
