"""Tests for thegent.integrations.pipeline_percentiles — Pipeline stage percentile tracking.

@trace WL-303
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from thegent.integrations.pipeline_percentiles import (
    PipelinePercentileTracker,
    StageTimer,
)


class TestStageTimer:
    """Test StageTimer dataclass. @trace WL-303"""

    @pytest.mark.requirement("WL-303")
    def test_create_stage_timer(self) -> None:
        """Can create a StageTimer with all fields."""
        now = datetime.now(UTC)
        timer = StageTimer(
            stage="validate",
            duration_ms=150.5,
            cycle_id="cycle-42",
            timestamp=now,
        )

        assert timer.stage == "validate"
        assert timer.duration_ms == 150.5
        assert timer.cycle_id == "cycle-42"
        assert timer.timestamp == now

    @pytest.mark.requirement("WL-303")
    def test_stage_timer_with_zero_duration(self) -> None:
        """StageTimer accepts zero duration."""
        timer = StageTimer(
            stage="noop",
            duration_ms=0.0,
            cycle_id="cycle-1",
            timestamp=datetime.now(UTC),
        )
        assert timer.duration_ms == 0.0


class TestPipelinePercentileTracker:
    """Test PipelinePercentileTracker operations. @trace WL-303"""

    @pytest.fixture
    def tracker(self) -> PipelinePercentileTracker:
        """Provide a PipelinePercentileTracker instance."""
        return PipelinePercentileTracker()

    @pytest.mark.requirement("WL-303")
    def test_record_single_stage(self, tracker: PipelinePercentileTracker) -> None:
        """Can record a single stage execution."""
        tracker.record("validate", 100.0, "cycle-1")
        assert tracker.all_stages() == ["validate"]

    @pytest.mark.requirement("WL-303")
    def test_record_multiple_executions_same_stage(self, tracker: PipelinePercentileTracker) -> None:
        """Can record multiple executions of the same stage."""
        tracker.record("validate", 100.0, "cycle-1")
        tracker.record("validate", 150.0, "cycle-2")
        tracker.record("validate", 120.0, "cycle-3")

        summary = tracker.summary("validate")
        assert summary["count"] == 3
        assert summary["stage"] == "validate"

    @pytest.mark.requirement("WL-303")
    def test_record_negative_duration_raises_error(self, tracker: PipelinePercentileTracker) -> None:
        """Recording negative duration raises ValueError."""
        with pytest.raises(ValueError, match="duration_ms must be non-negative"):
            tracker.record("validate", -1.0, "cycle-1")

    @pytest.mark.requirement("WL-303")
    def test_percentile_no_data(self, tracker: PipelinePercentileTracker) -> None:
        """Percentile returns None for stage with no data."""
        result = tracker.percentile("nonexistent", 50)
        assert result is None

    @pytest.mark.requirement("WL-303")
    def test_percentile_p50_single_value(self, tracker: PipelinePercentileTracker) -> None:
        """p50 of single value equals that value."""
        tracker.record("validate", 100.0, "cycle-1")
        result = tracker.percentile("validate", 50)
        assert result == 100.0

    @pytest.mark.requirement("WL-303")
    def test_percentile_p50_multiple_values(self, tracker: PipelinePercentileTracker) -> None:
        """p50 of multiple values is computed correctly."""
        # Record: 10, 20, 30, 40, 50
        for i, duration in enumerate([10, 20, 30, 40, 50]):
            tracker.record("process", float(duration), f"cycle-{i}")

        result = tracker.percentile("process", 50)
        assert result is not None
        # p50 should be around 30 (median)
        assert 25 <= result <= 35

    @pytest.mark.requirement("WL-303")
    def test_percentile_p95(self, tracker: PipelinePercentileTracker) -> None:
        """p95 is computed correctly."""
        # Record 100 values (1-100)
        for i in range(1, 101):
            tracker.record("compute", float(i), f"cycle-{i}")

        result = tracker.percentile("compute", 95)
        assert result is not None
        # p95 should be around 95
        assert 90 <= result <= 100

    @pytest.mark.requirement("WL-303")
    def test_percentile_p99(self, tracker: PipelinePercentileTracker) -> None:
        """p99 is computed correctly."""
        # Record 100 values (1-100)
        for i in range(1, 101):
            tracker.record("compute", float(i), f"cycle-{i}")

        result = tracker.percentile("compute", 99)
        assert result is not None
        # p99 should be around 99
        assert 95 <= result <= 100

    @pytest.mark.requirement("WL-303")
    def test_percentile_invalid_p_raises_error(self, tracker: PipelinePercentileTracker) -> None:
        """Invalid percentile values raise ValueError."""
        tracker.record("validate", 100.0, "cycle-1")

        with pytest.raises(ValueError, match="percentile must be in range"):
            tracker.percentile("validate", -1)

        with pytest.raises(ValueError, match="percentile must be in range"):
            tracker.percentile("validate", 101)

    @pytest.mark.requirement("WL-303")
    def test_summary_no_data(self, tracker: PipelinePercentileTracker) -> None:
        """Summary returns zeros and Nones for stage with no data."""
        summary = tracker.summary("nonexistent")

        assert summary["stage"] == "nonexistent"
        assert summary["count"] == 0
        assert summary["p50"] is None
        assert summary["p95"] is None
        assert summary["p99"] is None

    @pytest.mark.requirement("WL-303")
    def test_summary_with_data(self, tracker: PipelinePercentileTracker) -> None:
        """Summary includes all percentiles with data."""
        for i in range(1, 11):
            tracker.record("process", float(i * 10), f"cycle-{i}")

        summary = tracker.summary("process")

        assert summary["stage"] == "process"
        assert summary["count"] == 10
        assert summary["p50"] is not None
        assert summary["p95"] is not None
        assert summary["p99"] is not None

    @pytest.mark.requirement("WL-303")
    def test_all_stages_empty(self, tracker: PipelinePercentileTracker) -> None:
        """all_stages returns empty list for empty tracker."""
        result = tracker.all_stages()
        assert result == []

    @pytest.mark.requirement("WL-303")
    def test_all_stages_single(self, tracker: PipelinePercentileTracker) -> None:
        """all_stages returns single stage name."""
        tracker.record("validate", 100.0, "cycle-1")
        result = tracker.all_stages()
        assert result == ["validate"]

    @pytest.mark.requirement("WL-303")
    def test_all_stages_multiple_sorted(self, tracker: PipelinePercentileTracker) -> None:
        """all_stages returns sorted list of unique stages."""
        tracker.record("zebra", 100.0, "cycle-1")
        tracker.record("apple", 100.0, "cycle-2")
        tracker.record("zebra", 150.0, "cycle-3")
        tracker.record("beta", 120.0, "cycle-4")

        result = tracker.all_stages()
        assert result == ["apple", "beta", "zebra"]

    @pytest.mark.requirement("WL-303")
    def test_percentile_p0_and_p100(self, tracker: PipelinePercentileTracker) -> None:
        """p0 and p100 edge cases work correctly."""
        for i in range(1, 6):
            tracker.record("test", float(i * 10), f"cycle-{i}")

        # p0 should return min
        p0 = tracker.percentile("test", 0)
        assert p0 == 10.0

        # p100 should return max or close to it
        p100 = tracker.percentile("test", 100)
        assert p100 is not None
        assert p100 >= 40.0
