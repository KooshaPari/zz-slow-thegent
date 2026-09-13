"""Tests for WL-135 B90-W3-A4 SLO pass/fail gate script.

Verifies:
- scripts/check_slo_gate.py exists and is valid Python
- Exits 0 when no JSONL file exists
- Exits 0 for an all-green metric JSONL
- Exits 1 for an all-red metric JSONL
- Taskfile.yml contains slo:check
"""
# @trace WL-135 B90-W3-A4

from __future__ import annotations

import subprocess
from pathlib import Path

import orjson as json

_ROOT = Path(__file__).parent.parent
_GATE_SCRIPT = _ROOT / "scripts" / "check_slo_gate.py"


def test_check_slo_gate_script_exists() -> None:
    """scripts/check_slo_gate.py must exist."""
    assert _GATE_SCRIPT.is_file(), f"check_slo_gate.py not found at {_GATE_SCRIPT}"


def test_check_slo_gate_is_valid_python() -> None:
    """scripts/check_slo_gate.py must be parseable as valid Python."""
    import ast

    source = _GATE_SCRIPT.read_text(encoding="utf-8")
    # Will raise SyntaxError if invalid Python
    ast.parse(source)


def test_slo_gate_exits_0_when_no_jsonl(tmp_path: Path) -> None:
    """check_slo_gate.py must exit 0 when .quality/slo-metrics.jsonl does not exist."""
    result = subprocess.run(
        ["uv", "run", "python", str(_GATE_SCRIPT)],
        capture_output=True,
        cwd=str(tmp_path),  # tmp_path has no .quality/ dir
    )
    assert result.returncode == 0, (
        f"Expected exit 0 for missing JSONL, got {result.returncode}\nstderr: {result.stderr.decode()}"
    )


def test_slo_gate_exits_0_for_all_green_metric(tmp_path: Path) -> None:
    """check_slo_gate.py must exit 0 for an all-green metric record."""
    quality_dir = tmp_path / ".quality"
    quality_dir.mkdir()
    jsonl_path = quality_dir / "slo-metrics.jsonl"

    green_record = {
        "file_loc": 100.0,  # green_max=1200
        "function_loc_p95": 20.0,  # green_max=80
        "impl_importers": 5.0,  # green_max=20
        "cross_boundary_import_edges": 3.0,  # green_max=25
        "cli_help_p95_ms": 100.0,  # green_max=250
        "run_command_p95_ms": 200.0,  # green_max=500
        "decomposition_checkpoint_pass_rate": 1.0,  # green_min=1.0
        "timestamp": "2026-02-21T00:00:00+00:00",
        "source": "test",
    }
    jsonl_path.write_text(json.dumps(green_record).decode() + "\n", encoding="utf-8")

    result = subprocess.run(
        ["uv", "run", "python", str(_GATE_SCRIPT)],
        capture_output=True,
        cwd=str(tmp_path),
    )
    assert result.returncode == 0, (
        f"Expected exit 0 for all-green metric, got {result.returncode}\nstderr: {result.stderr.decode()}"
    )


def test_slo_gate_exits_1_for_all_red_metric(tmp_path: Path) -> None:
    """check_slo_gate.py must exit 1 for an all-red metric record."""
    quality_dir = tmp_path / ".quality"
    quality_dir.mkdir()
    jsonl_path = quality_dir / "slo-metrics.jsonl"

    red_record = {
        "file_loc": 9999.0,  # red_min=1800 — red
        "function_loc_p95": 999.0,  # red_min=120 — red
        "impl_importers": 999.0,  # red_min=35 — red
        "cross_boundary_import_edges": 999.0,  # red_min=40 — red
        "cli_help_p95_ms": 9999.0,  # red_min=400 — red
        "run_command_p95_ms": 9999.0,  # red_min=800 — red
        "decomposition_checkpoint_pass_rate": 0.0,  # red_max=0.95 — red
        "timestamp": "2026-02-21T00:00:00+00:00",
        "source": "test",
    }
    jsonl_path.write_text(json.dumps(red_record).decode() + "\n", encoding="utf-8")

    result = subprocess.run(
        ["uv", "run", "python", str(_GATE_SCRIPT)],
        capture_output=True,
        cwd=str(tmp_path),
    )
    assert result.returncode == 1, (
        f"Expected exit 1 for all-red metric, got {result.returncode}\n"
        f"stdout: {result.stdout.decode()}\nstderr: {result.stderr.decode()}"
    )


def test_taskfile_contains_slo_check() -> None:
    """Taskfile.yml must define the slo:check task."""
    content = (_ROOT / "Taskfile.yml").read_text(encoding="utf-8")
    assert "slo:check" in content, "Taskfile.yml must contain the slo:check task"
