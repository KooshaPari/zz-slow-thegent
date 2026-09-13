"""Tests for WL-131 migration baseline benchmark.

Verifies that the benchmark runs correctly, produces a valid result dict,
and that per-call latency is within an acceptable range.

# @trace WL-131 B90-W2-F3
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

import orjson as json
import pytest

ROOT = Path(__file__).resolve().parents[1]
BASELINE_JSON = ROOT / "benchmarks" / "baseline-wl131-parse-model-suffix.json"

# Maximum acceptable per-call latency in microseconds.
# 1000 us = 1 ms; any Python function should complete well under this.
MAX_ACCEPTABLE_PER_CALL_US = 1000.0


class TestWl131BenchmarkFile:
    """benchmarks/wl131_migration_baseline.py must exist and be importable."""

    # @trace WL-131 B90-W2-F3

    def test_benchmark_module_exists(self) -> None:
        """benchmarks/wl131_migration_baseline.py must exist."""
        benchmark_file = ROOT / "benchmarks" / "wl131_migration_baseline.py"
        assert benchmark_file.exists(), f"Missing benchmark file: {benchmark_file}"

    def test_baseline_json_exists(self) -> None:
        """benchmarks/baseline-wl131-parse-model-suffix.json must exist."""
        assert BASELINE_JSON.exists(), f"Missing baseline JSON: {BASELINE_JSON}"

    def test_baseline_json_is_valid(self) -> None:
        """baseline JSON must parse and contain required keys."""
        data = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
        assert "n" in data, "baseline JSON must have 'n' key"
        assert "elapsed_s" in data, "baseline JSON must have 'elapsed_s' key"
        assert "per_call_us" in data, "baseline JSON must have 'per_call_us' key"

    def test_baseline_json_per_call_within_range(self) -> None:
        """Recorded per_call_us must be within acceptable range (<= 1000 us)."""
        data = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
        per_call = data["per_call_us"]
        assert per_call <= MAX_ACCEPTABLE_PER_CALL_US, (
            f"Baseline per_call_us={per_call:.4f} exceeds {MAX_ACCEPTABLE_PER_CALL_US} us. "
            "This may indicate a performance regression in the Python implementation. "
            "Investigate before promoting to Rust migration."
        )

    def test_baseline_json_n_positive(self) -> None:
        """Recorded n (total calls) must be a positive integer."""
        data = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
        assert data["n"] > 0, "baseline JSON 'n' must be positive"


class TestWl131BenchmarkExecution:
    """The benchmark function must execute and return a valid result dict."""

    # @trace WL-131 B90-W2-F3

    def test_benchmark_runs_and_produces_result(self) -> None:
        """benchmark_parse_model_suffix must return a result with expected keys."""
        # Add benchmarks/ to path so we can import the module
        benchmarks_dir = str(ROOT / "benchmarks")
        if benchmarks_dir not in sys.path:
            sys.path.insert(0, benchmarks_dir)

        spec = importlib.util.spec_from_file_location(
            "wl131_migration_baseline",
            ROOT / "benchmarks" / "wl131_migration_baseline.py",
        )
        if spec is None or spec.loader is None:
            pytest.fail("Cannot load wl131_migration_baseline.py")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        result = module.benchmark_parse_model_suffix()

        assert isinstance(result, dict), "benchmark must return a dict"
        assert "n" in result, "result must have 'n' key"
        assert "elapsed_s" in result, "result must have 'elapsed_s' key"
        assert "per_call_us" in result, "result must have 'per_call_us' key"

    def test_benchmark_per_call_within_range(self) -> None:
        """Live benchmark per_call_us must be <= MAX_ACCEPTABLE_PER_CALL_US."""
        benchmarks_dir = str(ROOT / "benchmarks")
        if benchmarks_dir not in sys.path:
            sys.path.insert(0, benchmarks_dir)

        spec = importlib.util.spec_from_file_location(
            "wl131_migration_baseline_live",
            ROOT / "benchmarks" / "wl131_migration_baseline.py",
        )
        if spec is None or spec.loader is None:
            pytest.fail("Cannot load wl131_migration_baseline.py")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        result = module.benchmark_parse_model_suffix()
        per_call = result["per_call_us"]

        assert per_call <= MAX_ACCEPTABLE_PER_CALL_US, (
            f"Live benchmark per_call_us={per_call:.4f} us exceeds "
            f"{MAX_ACCEPTABLE_PER_CALL_US} us — potential performance regression "
            "in parse_model_suffix. Flag for WL-131 Rust migration team."
        )
