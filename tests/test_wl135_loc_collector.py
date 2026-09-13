"""Tests for WL-135 LOC/complexity collector.

Verifies that:
1. collect_loc_metrics.py runs without error.
2. .quality/loc-metrics.json is valid JSON after run.
3. Output has required fields: timestamp, total_loc, by_module.

# @trace WL-135 B90-W2-C4
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import orjson as json

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "collect_loc_metrics.py"
OUTPUT_PATH = ROOT / ".quality" / "loc-metrics.json"


def _import_collect_module():
    """Dynamically import scripts/collect_loc_metrics.py."""
    spec = importlib.util.spec_from_file_location("collect_loc_metrics", SCRIPT)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


class TestLocCollectorScript:
    """collect_loc_metrics.py must exist and be importable."""

    # @trace WL-135 B90-W2-C4

    def test_script_exists(self) -> None:
        """scripts/collect_loc_metrics.py must exist."""
        assert SCRIPT.exists(), f"Script not found: {SCRIPT}"

    def test_script_is_valid_python(self) -> None:
        """collect_loc_metrics.py must parse without syntax errors."""
        source = SCRIPT.read_text()
        compile(source, str(SCRIPT), "exec")  # raises SyntaxError on failure


class TestLocCollectorOutput:
    """Running the collector must produce valid JSON with required fields."""

    # @trace WL-135 B90-W2-C4

    def test_collect_metrics_runs_without_error(self) -> None:
        """collect_metrics() must run and return a dict without raising."""
        mod = _import_collect_module()
        result = mod.collect_metrics()
        assert isinstance(result, dict), "collect_metrics() must return a dict"

    def test_output_has_timestamp(self) -> None:
        """Collector output must include 'timestamp' field."""
        mod = _import_collect_module()
        result = mod.collect_metrics()
        assert "timestamp" in result, "Missing 'timestamp' in collector output"
        assert isinstance(result["timestamp"], str)

    def test_output_has_total_loc(self) -> None:
        """Collector output must include 'total_loc' field with integer value."""
        mod = _import_collect_module()
        result = mod.collect_metrics()
        assert "total_loc" in result, "Missing 'total_loc' in collector output"
        assert isinstance(result["total_loc"], int)
        assert result["total_loc"] > 0, "total_loc must be > 0 for a non-empty codebase"

    def test_output_has_by_module(self) -> None:
        """Collector output must include 'by_module' dict."""
        mod = _import_collect_module()
        result = mod.collect_metrics()
        assert "by_module" in result, "Missing 'by_module' in collector output"
        assert isinstance(result["by_module"], dict)
        assert len(result["by_module"]) > 0, "by_module must not be empty"

    def test_output_has_top5_largest_files(self) -> None:
        """Collector output must include 'top5_largest_files' list."""
        mod = _import_collect_module()
        result = mod.collect_metrics()
        assert "top5_largest_files" in result, "Missing 'top5_largest_files' in collector output"
        assert isinstance(result["top5_largest_files"], list)

    def test_output_json_is_serializable(self) -> None:
        """collect_metrics() output must be JSON-serializable."""
        mod = _import_collect_module()
        result = mod.collect_metrics()
        serialized = json.dumps(result).decode()
        reparsed = json.loads(serialized)
        assert reparsed["total_loc"] == result["total_loc"]


class TestLocMetricsJsonFile:
    """After running main(), .quality/loc-metrics.json must be valid JSON."""

    # @trace WL-135 B90-W2-C4

    def test_output_file_written_by_main(self) -> None:
        """Running main() must write OUTPUT_PATH with valid JSON."""
        mod = _import_collect_module()
        # Run main() — will write to .quality/loc-metrics.json
        rc = mod.main()
        assert rc == 0, f"main() returned non-zero exit code: {rc}"
        assert OUTPUT_PATH.exists(), f"Output file not written: {OUTPUT_PATH}"
        data = json.loads(OUTPUT_PATH.read_text())
        assert "timestamp" in data
        assert "total_loc" in data
        assert "by_module" in data
