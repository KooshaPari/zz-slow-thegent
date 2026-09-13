"""Tests for WL-215: Cycle Performance Benchmark Harness.

# @trace WL-215
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

import pytest

from thegent.integrations.cycle_benchmark import CycleBenchmark, CycleBenchmarkHarness


class TestCycleBenchmark:
    """Tests for CycleBenchmark dataclass."""

    @pytest.mark.requirement("WL-215")
    def test_cycle_benchmark_creation(self):
        """# @trace WL-215 — CycleBenchmark can be created with required fields."""
        now = datetime.now(UTC)
        benchmark = CycleBenchmark(cycle_id="test_cycle", start_time=now)
        assert benchmark.cycle_id == "test_cycle"
        assert benchmark.start_time == now
        assert benchmark.end_time is None
        assert benchmark.item_count == 0

    @pytest.mark.requirement("WL-215")
    def test_cycle_benchmark_with_all_fields(self):
        """# @trace WL-215 — CycleBenchmark can be created with all fields."""
        now = datetime.now(UTC)
        end = datetime.now(UTC)
        benchmark = CycleBenchmark(
            cycle_id="test_cycle",
            start_time=now,
            end_time=end,
            item_count=100,
        )
        assert benchmark.cycle_id == "test_cycle"
        assert benchmark.start_time == now
        assert benchmark.end_time == end
        assert benchmark.item_count == 100


class TestCycleBenchmarkHarness:
    """Tests for CycleBenchmarkHarness class."""

    @pytest.mark.requirement("WL-215")
    def test_start_cycle(self):
        """# @trace WL-215 — start_cycle creates a benchmark and returns it."""
        harness = CycleBenchmarkHarness()
        before = datetime.now(UTC)
        benchmark = harness.start_cycle("cycle_1")
        after = datetime.now(UTC)

        assert benchmark.cycle_id == "cycle_1"
        assert before <= benchmark.start_time <= after
        assert benchmark.end_time is None
        assert benchmark.item_count == 0

    @pytest.mark.requirement("WL-215")
    def test_end_cycle(self):
        """# @trace WL-215 — end_cycle updates benchmark with end time and item count."""
        harness = CycleBenchmarkHarness()
        harness.start_cycle("cycle_1")
        before = datetime.now(UTC)
        benchmark = harness.end_cycle("cycle_1", item_count=50)
        after = datetime.now(UTC)

        assert benchmark.cycle_id == "cycle_1"
        assert before <= benchmark.end_time <= after
        assert benchmark.item_count == 50

    @pytest.mark.requirement("WL-215")
    def test_end_cycle_not_started(self):
        """# @trace WL-215 — end_cycle raises KeyError if cycle not started."""
        harness = CycleBenchmarkHarness()
        with pytest.raises(KeyError):
            harness.end_cycle("nonexistent", item_count=0)

    @pytest.mark.requirement("WL-215")
    def test_get_duration_seconds_with_ended_cycle(self):
        """# @trace WL-215 — get_duration_seconds returns duration in seconds."""
        harness = CycleBenchmarkHarness()
        harness.start_cycle("cycle_1")
        time.sleep(0.1)  # Sleep for 100ms
        harness.end_cycle("cycle_1", item_count=0)

        duration = harness.get_duration_seconds("cycle_1")
        assert duration >= 0.1
        assert duration < 1.0

    @pytest.mark.requirement("WL-215")
    def test_get_duration_seconds_not_ended(self):
        """# @trace WL-215 — get_duration_seconds returns 0 if cycle not ended."""
        harness = CycleBenchmarkHarness()
        harness.start_cycle("cycle_1")
        duration = harness.get_duration_seconds("cycle_1")
        assert duration == 0.0

    @pytest.mark.requirement("WL-215")
    def test_get_duration_seconds_not_started(self):
        """# @trace WL-215 — get_duration_seconds raises KeyError if cycle not started."""
        harness = CycleBenchmarkHarness()
        with pytest.raises(KeyError):
            harness.get_duration_seconds("nonexistent")

    @pytest.mark.requirement("WL-215")
    def test_all_benchmarks_empty(self):
        """# @trace WL-215 — all_benchmarks returns empty list initially."""
        harness = CycleBenchmarkHarness()
        benchmarks = harness.all_benchmarks()
        assert isinstance(benchmarks, list)
        assert len(benchmarks) == 0

    @pytest.mark.requirement("WL-215")
    def test_all_benchmarks_multiple(self):
        """# @trace WL-215 — all_benchmarks returns all recorded cycles."""
        harness = CycleBenchmarkHarness()
        harness.start_cycle("cycle_1")
        harness.start_cycle("cycle_2")
        harness.start_cycle("cycle_3")

        benchmarks = harness.all_benchmarks()
        assert len(benchmarks) == 3
        assert benchmarks[0].cycle_id == "cycle_1"
        assert benchmarks[1].cycle_id == "cycle_2"
        assert benchmarks[2].cycle_id == "cycle_3"

    @pytest.mark.requirement("WL-215")
    def test_multiple_cycles_independent(self):
        """# @trace WL-215 — multiple cycles can be tracked independently."""
        harness = CycleBenchmarkHarness()
        harness.start_cycle("cycle_a")
        harness.start_cycle("cycle_b")

        harness.end_cycle("cycle_a", item_count=10)
        harness.end_cycle("cycle_b", item_count=20)

        benchmarks = harness.all_benchmarks()
        assert benchmarks[0].item_count == 10
        assert benchmarks[1].item_count == 20
