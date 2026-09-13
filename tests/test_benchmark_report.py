from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import orjson as json

SCRIPT_PATH = Path("scripts/benchmark-report.py")


def _write_hyperfine(path: Path, command: str, mean: float, minimum: float, maximum: float, stddev: float) -> None:
    payload = {
        "results": [
            {
                "command": command,
                "mean": mean,
                "stddev": stddev,
                "min": minimum,
                "max": maximum,
                "times": [mean],
            }
        ]
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload).decode(), encoding="utf-8")


def _run_reporter(tmp_path: Path, baseline_dir: Path, current_dir: Path) -> tuple[Path, Path]:
    report_path = tmp_path / "report.md"
    summary_path = tmp_path / "summary.json"
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--baseline-dir",
            str(baseline_dir),
            "--current-dir",
            str(current_dir),
            "--report-path",
            str(report_path),
            "--summary-path",
            str(summary_path),
            "--title",
            "Rust Hook Benchmark Comparison",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return report_path, summary_path


def test_generates_speedup_report_from_hyperfine_json(tmp_path: Path) -> None:
    baseline_dir = tmp_path / "baseline"
    current_dir = tmp_path / "current"

    _write_hyperfine(
        baseline_dir / "tool_detection_bash.json",
        command="bash -c detect_tools",
        mean=0.060,
        minimum=0.055,
        maximum=0.070,
        stddev=0.004,
    )
    _write_hyperfine(
        current_dir / "tool_detection_rust.json",
        command="thegent-tool-detect --json",
        mean=0.010,
        minimum=0.009,
        maximum=0.012,
        stddev=0.001,
    )

    report_path, summary_path = _run_reporter(tmp_path, baseline_dir, current_dir)

    report = report_path.read_text(encoding="utf-8")
    assert "Rust Hook Benchmark Comparison" in report
    assert "tool_detection" in report
    assert "6.00x" in report

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["scenarios"][0]["scenario"] == "tool_detection"
    assert summary["scenarios"][0]["speedup"] == 6.0
    assert summary["mode_aggregates"]["cold"] is None
    assert summary["mode_aggregates"]["warm"] is None


def test_marks_speedup_na_when_current_result_missing(tmp_path: Path) -> None:
    baseline_dir = tmp_path / "baseline"
    current_dir = tmp_path / "current"

    _write_hyperfine(
        baseline_dir / "path_resolution_bash.json",
        command="bash -c resolve_path",
        mean=0.020,
        minimum=0.018,
        maximum=0.024,
        stddev=0.002,
    )

    report_path, summary_path = _run_reporter(tmp_path, baseline_dir, current_dir)

    report = report_path.read_text(encoding="utf-8")
    assert "path_resolution" in report
    assert "N/A" in report

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["scenarios"][0]["scenario"] == "path_resolution"
    assert summary["scenarios"][0]["speedup"] is None
    assert summary["mode_aggregates"]["cold"] is None
    assert summary["mode_aggregates"]["warm"] is None


def test_mode_aggregates_include_cold_and_warm(tmp_path: Path) -> None:
    baseline_dir = tmp_path / "baseline"
    current_dir = tmp_path / "current"

    _write_hyperfine(
        baseline_dir / "resolve_cold_bash.json",
        command="thegent-tool-detect --json",
        mean=0.100,
        minimum=0.095,
        maximum=0.110,
        stddev=0.002,
    )
    _write_hyperfine(
        current_dir / "resolve_cold_python.json",
        command="thegent-tool-detect --json",
        mean=0.050,
        minimum=0.048,
        maximum=0.052,
        stddev=0.001,
    )
    _write_hyperfine(
        baseline_dir / "search_warm_bash.json",
        command="thegent-search --json",
        mean=0.080,
        minimum=0.075,
        maximum=0.090,
        stddev=0.002,
    )
    _write_hyperfine(
        current_dir / "search_warm_python.json",
        command="thegent-search --json",
        mean=0.040,
        minimum=0.038,
        maximum=0.044,
        stddev=0.001,
    )

    _, summary_path = _run_reporter(tmp_path, baseline_dir, current_dir)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["mode_aggregates"]["cold"] is not None
    assert summary["mode_aggregates"]["warm"] is not None
    assert "baseline_mean_seconds" in summary["mode_aggregates"]["cold"]
    assert "baseline_mean_seconds" in summary["mode_aggregates"]["warm"]
