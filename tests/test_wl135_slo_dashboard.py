"""Tests for WL-135 SLO dashboard rendering.

# @trace WL-135 B90-W2-E1
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "render_slo_dashboard.py"
DASHBOARD = ROOT / ".quality" / "slo-dashboard.md"


def test_render_slo_dashboard_runs_without_error() -> None:
    """Script must exit 0 with no unhandled exception."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, f"Script failed:\nstdout={result.stdout}\nstderr={result.stderr}"


def test_slo_dashboard_file_exists() -> None:
    """Dashboard file must exist after running the script."""
    assert DASHBOARD.exists(), f"Expected {DASHBOARD} to exist after render"


def test_slo_dashboard_contains_table_headers() -> None:
    """Dashboard must contain expected markdown table headers."""
    content = DASHBOARD.read_text(encoding="utf-8")
    assert "| Metric | Value | Status | Threshold (Green) | Threshold (Red) |" in content
    assert "|--------|" in content


def test_slo_dashboard_contains_required_metrics() -> None:
    """Dashboard must list all required SLO metrics."""
    content = DASHBOARD.read_text(encoding="utf-8")
    required_metrics = [
        "Total Python LOC",
        "file_loc max",
        "p95 latency",
        "error rate",
        "trend health score",
    ]
    for metric in required_metrics:
        assert metric in content, f"Expected metric '{metric}' in dashboard"


def test_slo_dashboard_contains_breach_states() -> None:
    """Dashboard must include breach state definitions."""
    content = DASHBOARD.read_text(encoding="utf-8")
    assert "## Breach States" in content
    assert "CRITICAL" in content
    assert "HEALTHY" in content


def test_slo_dashboard_has_correct_heading() -> None:
    """Dashboard must start with LOC/SLO Dashboard heading."""
    content = DASHBOARD.read_text(encoding="utf-8")
    assert "# LOC/SLO Dashboard" in content
