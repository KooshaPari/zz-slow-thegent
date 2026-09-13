from __future__ import annotations

from pathlib import Path

from thegent.metrics.collector import MetricsCollector


def test_emit_slo_stub_pass_status() -> None:
    payload = MetricsCollector().emit_slo_stub("cli_help_p95_ms", 200.0, threshold=250.0)

    assert payload["emitter"] == "wl135-slo-stub"
    assert payload["metric_name"] == "cli_help_p95_ms"
    assert payload["status"] == "pass"
    assert payload["lane"] == "fast-lane"
    assert isinstance(payload["timestamp_unix"], float)


def test_emit_slo_stub_fail_and_unknown_statuses() -> None:
    collector = MetricsCollector()

    fail_payload = collector.emit_slo_stub("run_command_p95_ms", 900.0, threshold=800.0, lane="nightly-lane")
    unknown_payload = collector.emit_slo_stub("run_command_p95_ms", 900.0, threshold=None)

    assert fail_payload["status"] == "fail"
    assert fail_payload["lane"] == "nightly-lane"
    assert unknown_payload["status"] == "unknown"


def test_emit_slo_stub_pass_at_threshold_boundary() -> None:
    payload = MetricsCollector().emit_slo_stub("latency_p95_ms", 250.0, threshold=250.0)
    assert payload["status"] == "pass"


def test_emit_wl135_script_jsonl_append(tmp_path: Path) -> None:
    jsonl_path = tmp_path / "slo_stub.jsonl"

    import sys

    from scripts.emit_wl135_slo_stub import main as emit_main

    argv = sys.argv
    try:
        sys.argv = [
            "emit_wl135_slo_stub.py",
            "--metric",
            "cli_help_p95_ms",
            "--value",
            "210",
            "--threshold",
            "250",
            "--jsonl",
            str(jsonl_path),
        ]
        rc = emit_main()
    finally:
        sys.argv = argv

    assert rc == 0
    rows = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 1
    assert '"metric_name": "cli_help_p95_ms"' in rows[0]
