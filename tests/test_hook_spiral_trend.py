"""Integration tests for hook-dispatcher spiral trend reporting."""

from __future__ import annotations

import subprocess
from pathlib import Path

import orjson as json
import pytest


def _dispatcher_bin() -> Path:
    root = Path(__file__).resolve().parents[1]
    return root / "hooks" / "hook-dispatcher" / "target" / "debug" / "hook-dispatcher"


@pytest.mark.unit
def test_spiral_trend_command_reports_metrics(tmp_path: Path) -> None:
    dispatcher = _dispatcher_bin()
    assert dispatcher.exists(), f"Missing dispatcher binary: {dispatcher}"

    metrics = tmp_path / "regression-spiral-metrics.jsonl"
    metrics.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "generated_at": "2026-02-20T01:00:00Z",
                        "session_id": "s1",
                        "status": "warning",
                        "severity": "warning",
                        "reason": "violations=1",
                        "violations": 1,
                        "streak": 1,
                        "interrupt": False,
                        "metrics": {
                            "failed": 2,
                            "stale_test_evidence": 1,
                            "stale_build_evidence": 0,
                            "stale_e2e_evidence": 0,
                        },
                    }
                ).decode(),
                json.dumps(
                    {
                        "generated_at": "2026-02-20T01:10:00Z",
                        "session_id": "s1",
                        "status": "critical_interrupt",
                        "severity": "critical",
                        "reason": "streak=2 >= trigger=2",
                        "violations": 2,
                        "streak": 2,
                        "interrupt": True,
                        "metrics": {
                            "failed": 4,
                            "stale_test_evidence": 0,
                            "stale_build_evidence": 1,
                            "stale_e2e_evidence": 0,
                        },
                    }
                ).decode(),
                json.dumps(
                    {
                        "generated_at": "2026-02-20T01:20:00Z",
                        "session_id": "s1",
                        "status": "healthy",
                        "severity": "info",
                        "reason": "no_violations",
                        "violations": 0,
                        "streak": 0,
                        "interrupt": False,
                        "metrics": {
                            "failed": 0,
                            "stale_test_evidence": 0,
                            "stale_build_evidence": 0,
                            "stale_e2e_evidence": 1,
                        },
                    }
                ).decode(),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [str(dispatcher), "governance", "spiral-trend", str(metrics), "--window", "3"],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["samples_total"] == 3
    assert payload["window_used"] == 3
    assert payload["breach_count"] == 2
    assert payload["interrupt_count"] == 1
    assert payload["max_streak"] == 2
    assert payload["stale_test_evidence_events"] == 1
    assert payload["stale_build_evidence_events"] == 1
    assert payload["stale_e2e_evidence_events"] == 1
    assert payload["pressure_score"] == pytest.approx(0.5)
    assert payload["policy_band"] == "yellow"
    assert payload["latest_status"] == "healthy"


@pytest.mark.unit
def test_spiral_trend_command_handles_missing_file(tmp_path: Path) -> None:
    dispatcher = _dispatcher_bin()
    assert dispatcher.exists(), f"Missing dispatcher binary: {dispatcher}"

    proc = subprocess.run(
        [str(dispatcher), "governance", "spiral-trend", str(tmp_path / "missing.jsonl")],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["samples_total"] == 0
    assert payload["window_used"] == 0
    assert payload["breach_rate"] == 0.0
    assert payload["stale_test_evidence_events"] == 0
    assert payload["stale_build_evidence_events"] == 0
    assert payload["stale_e2e_evidence_events"] == 0
    assert payload["pressure_score"] == 0.0
    assert payload["policy_band"] == "green"
