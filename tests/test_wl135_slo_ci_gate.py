"""Tests for SLO CI gate script (WL-135 B90-W3-E1).

Verifies that scripts/check_slo_gate.py exists, is valid Python syntax,
and correctly exits 0 (no data / all green) or 1 (any red metric).
# @trace WL-135 B90-W3-E1
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import orjson as json

ROOT = Path(__file__).parent.parent
GATE_SCRIPT = ROOT / "scripts" / "check_slo_gate.py"
QUALITY_DIR = ROOT / ".quality"


def test_gate_script_exists() -> None:
    """check_slo_gate.py must exist in scripts/."""
    assert GATE_SCRIPT.exists(), f"Expected {GATE_SCRIPT} to exist"


def test_gate_script_valid_python() -> None:
    """check_slo_gate.py must be valid Python syntax."""
    source = GATE_SCRIPT.read_text(encoding="utf-8")
    # ast.parse raises SyntaxError on invalid syntax
    ast.parse(source)


def test_gate_exits_0_when_no_file(tmp_path: Path) -> None:
    """Gate exits 0 when no JSONL file is present."""
    result = subprocess.run(
        [sys.executable, str(GATE_SCRIPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Expected exit 0 with no JSONL file, got {result.returncode}. stderr: {result.stderr}"
    )


def test_gate_exits_0_when_file_empty(tmp_path: Path) -> None:
    """Gate exits 0 when JSONL file exists but is empty."""
    quality_dir = tmp_path / ".quality"
    quality_dir.mkdir()
    (quality_dir / "slo-metrics.jsonl").write_text("", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(GATE_SCRIPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Expected exit 0 with empty JSONL, got {result.returncode}. stderr: {result.stderr}"


def _all_green_record() -> dict:
    """Return a JSONL record where all metrics are within green thresholds."""
    return {
        "file_loc": 100.0,
        "function_loc_p95": 20.0,
        "impl_importers": 5.0,
        "cross_boundary_import_edges": 5.0,
        "cli_help_p95_ms": 100.0,
        "run_command_p95_ms": 200.0,
        "decomposition_checkpoint_pass_rate": 1.0,
        "timestamp": "2026-02-21T00:00:00+00:00",
        "source": "test",
    }


def _all_red_record() -> dict:
    """Return a JSONL record where all lower-is-better metrics exceed red thresholds."""
    return {
        "file_loc": 9999.0,
        "function_loc_p95": 9999.0,
        "impl_importers": 9999.0,
        "cross_boundary_import_edges": 9999.0,
        "cli_help_p95_ms": 9999.0,
        "run_command_p95_ms": 9999.0,
        "decomposition_checkpoint_pass_rate": 0.0,
        "timestamp": "2026-02-21T00:00:00+00:00",
        "source": "test",
    }


def test_gate_exits_0_when_all_green(tmp_path: Path) -> None:
    """Gate exits 0 when last JSONL record has all green metrics."""
    quality_dir = tmp_path / ".quality"
    quality_dir.mkdir()
    jsonl_path = quality_dir / "slo-metrics.jsonl"
    jsonl_path.write_text(json.dumps(_all_green_record().decode()) + "\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(GATE_SCRIPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Expected exit 0 with all-green metrics, got {result.returncode}. stderr: {result.stderr}"
    )


def test_gate_exits_1_when_all_red(tmp_path: Path) -> None:
    """Gate exits 1 when last JSONL record has red metrics."""
    quality_dir = tmp_path / ".quality"
    quality_dir.mkdir()
    jsonl_path = quality_dir / "slo-metrics.jsonl"
    jsonl_path.write_text(json.dumps(_all_red_record().decode()) + "\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(GATE_SCRIPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(ROOT / "src"),
        },
    )
    assert result.returncode == 1, (
        f"Expected exit 1 with all-red metrics, got {result.returncode}. stderr: {result.stderr}"
    )


def test_gate_uses_last_record_only(tmp_path: Path) -> None:
    """Gate evaluates only the last JSONL record; earlier red records do not fail gate."""
    quality_dir = tmp_path / ".quality"
    quality_dir.mkdir()
    jsonl_path = quality_dir / "slo-metrics.jsonl"
    # First record is all-red, last record is all-green
    content = json.dumps(_all_red_record().decode()) + "\n" + json.dumps(_all_green_record().decode()) + "\n"
    jsonl_path.write_text(content, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(GATE_SCRIPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(ROOT / "src"),
        },
    )
    assert result.returncode == 0, (
        f"Expected exit 0 when last record is green, got {result.returncode}. stderr: {result.stderr}"
    )
