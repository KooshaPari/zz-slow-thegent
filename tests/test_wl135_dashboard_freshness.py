"""Tests for WL-135: Dashboard data freshness and retention.

Validates that the LOC/SLO metrics collector and dashboard renderer exist,
produce correct output shapes, and that the freshness validator script is
functional.

# @trace WL-135 B90-W3-C3
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
COLLECT_SCRIPT = ROOT / "scripts" / "collect_loc_metrics.py"
RENDER_SCRIPT = ROOT / "scripts" / "render_slo_dashboard.py"
FRESHNESS_SCRIPT = ROOT / "scripts" / "check_dashboard_freshness.py"


# @trace WL-135 B90-W3-C3
def test_collect_loc_metrics_script_exists() -> None:
    """scripts/collect_loc_metrics.py must exist."""
    assert COLLECT_SCRIPT.exists(), f"collect_loc_metrics.py not found at {COLLECT_SCRIPT}."


# @trace WL-135 B90-W3-C3
def test_render_slo_dashboard_script_exists() -> None:
    """scripts/render_slo_dashboard.py must exist (created in Wave-2)."""
    assert RENDER_SCRIPT.exists(), f"render_slo_dashboard.py not found at {RENDER_SCRIPT}."


# @trace WL-135 B90-W3-C3
def test_check_dashboard_freshness_script_exists() -> None:
    """scripts/check_dashboard_freshness.py must exist (created in Wave-3 C3)."""
    assert FRESHNESS_SCRIPT.exists(), f"check_dashboard_freshness.py not found at {FRESHNESS_SCRIPT}."


def _load_collect_metrics_module():
    """Dynamically load collect_loc_metrics.py as a module."""
    spec = importlib.util.spec_from_file_location("collect_loc_metrics", COLLECT_SCRIPT)
    assert spec is not None, "Could not create module spec for collect_loc_metrics.py"
    assert spec.loader is not None, "Module spec has no loader"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# @trace WL-135 B90-W3-C3
def test_collect_metrics_returns_dict_with_timestamp() -> None:
    """collect_metrics() must return a dict containing a 'timestamp' key."""
    mod = _load_collect_metrics_module()
    result = mod.collect_metrics()
    assert isinstance(result, dict), f"collect_metrics() returned {type(result).__name__}, expected dict."
    assert "timestamp" in result, "collect_metrics() result is missing 'timestamp' key."


# @trace WL-135 B90-W3-C3
def test_collect_metrics_timestamp_is_iso_format() -> None:
    """The timestamp returned by collect_metrics() must be in ISO 8601 format."""
    mod = _load_collect_metrics_module()
    result = mod.collect_metrics()
    ts = result["timestamp"]
    assert isinstance(ts, str), f"timestamp is {type(ts).__name__}, expected str."
    # ISO 8601 UTC pattern: YYYY-MM-DDTHH:MM:SS.ffffff+HH:MM or ending with Z
    iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    assert re.match(iso_pattern, ts), f"timestamp '{ts}' does not match ISO 8601 format."


# @trace WL-135 B90-W3-C3
def test_collect_metrics_total_loc_is_positive_integer() -> None:
    """collect_metrics() must return a 'total_loc' key with a positive integer value."""
    mod = _load_collect_metrics_module()
    result = mod.collect_metrics()
    assert "total_loc" in result, "collect_metrics() result is missing 'total_loc' key."
    total_loc = result["total_loc"]
    assert isinstance(total_loc, int), f"total_loc is {type(total_loc).__name__}, expected int."
    assert total_loc > 0, f"total_loc is {total_loc}, expected a positive integer."
