"""Tests for WL-257: Historical Trend Reports.

Tests the trend reporting system for long-horizon analytics on drift/error/latency.

# @trace WL-257
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest


@pytest.mark.requirement("WL-257")
class TestTrendDataPoint:
    """Tests for TrendDataPoint dataclass."""

    def test_create_data_point(self):
        """# @trace WL-257 — TrendDataPoint can be created with required fields."""
        from thegent.integrations.historical_trends import TrendDataPoint

        now = datetime.now(UTC)
        point = TrendDataPoint(timestamp=now, metric="latency", value=100.5)

        assert point.timestamp == now
        assert point.metric == "latency"
        assert point.value == 100.5


@pytest.mark.requirement("WL-257")
class TestHistoricalTrendReport:
    """Tests for HistoricalTrendReport."""

    def test_init(self):
        """# @trace WL-257 — HistoricalTrendReport can be initialized."""
        from thegent.integrations.historical_trends import HistoricalTrendReport

        report = HistoricalTrendReport()
        assert report is not None

    def test_record_creates_data_point(self):
        """# @trace WL-257 — record returns a TrendDataPoint."""
        from thegent.integrations.historical_trends import HistoricalTrendReport

        report = HistoricalTrendReport()
        point = report.record("latency", 100.0)

        assert point.metric == "latency"
        assert point.value == 100.0
        assert point.timestamp is not None

    def test_record_multiple_metrics(self):
        """# @trace WL-257 — record can track multiple different metrics."""
        from thegent.integrations.historical_trends import HistoricalTrendReport

        report = HistoricalTrendReport()
        p1 = report.record("latency", 100.0)
        p2 = report.record("error_rate", 0.05)
        p3 = report.record("drift", 2)

        assert p1.metric == "latency"
        assert p2.metric == "error_rate"
        assert p3.metric == "drift"

    def test_get_series_returns_all_points_for_metric(self):
        """# @trace WL-257 — get_series returns all recorded points for a metric."""
        from thegent.integrations.historical_trends import HistoricalTrendReport

        report = HistoricalTrendReport()
        report.record("latency", 100.0)
        report.record("latency", 105.0)
        report.record("latency", 95.0)

        series = report.get_series("latency")
        assert len(series) == 3
        assert [p.value for p in series] == [100.0, 105.0, 95.0]

    def test_get_series_returns_empty_for_unknown_metric(self):
        """# @trace WL-257 — get_series returns empty list for unknown metric."""
        from thegent.integrations.historical_trends import HistoricalTrendReport

        report = HistoricalTrendReport()
        series = report.get_series("nonexistent")
        assert series == []

    def test_get_series_isolated_per_metric(self):
        """# @trace WL-257 — get_series returns only points for specified metric."""
        from thegent.integrations.historical_trends import HistoricalTrendReport

        report = HistoricalTrendReport()
        report.record("latency", 100.0)
        report.record("error_rate", 0.05)
        report.record("latency", 105.0)

        latency_series = report.get_series("latency")
        error_series = report.get_series("error_rate")

        assert len(latency_series) == 2
        assert len(error_series) == 1
        assert latency_series[0].metric == "latency"
        assert error_series[0].metric == "error_rate"

    def test_average_with_multiple_values(self):
        """# @trace WL-257 — average calculates correct mean."""
        from thegent.integrations.historical_trends import HistoricalTrendReport

        report = HistoricalTrendReport()
        report.record("latency", 100.0)
        report.record("latency", 200.0)
        report.record("latency", 300.0)

        avg = report.average("latency")
        assert avg == 200.0

    def test_average_with_single_value(self):
        """# @trace WL-257 — average returns single value as average."""
        from thegent.integrations.historical_trends import HistoricalTrendReport

        report = HistoricalTrendReport()
        report.record("latency", 42.0)

        avg = report.average("latency")
        assert avg == 42.0

    def test_average_with_no_data_returns_zero(self):
        """# @trace WL-257 — average returns 0.0 when no data exists."""
        from thegent.integrations.historical_trends import HistoricalTrendReport

        report = HistoricalTrendReport()
        avg = report.average("nonexistent")
        assert avg == 0.0

    def test_trend_up_when_last_greater_than_first(self):
        """# @trace WL-257 — trend returns 'up' when value increases."""
        from thegent.integrations.historical_trends import HistoricalTrendReport

        report = HistoricalTrendReport()
        report.record("latency", 100.0)
        report.record("latency", 150.0)
        report.record("latency", 200.0)

        trend = report.trend("latency")
        assert trend == "up"

    def test_trend_down_when_last_less_than_first(self):
        """# @trace WL-257 — trend returns 'down' when value decreases."""
        from thegent.integrations.historical_trends import HistoricalTrendReport

        report = HistoricalTrendReport()
        report.record("error_rate", 0.10)
        report.record("error_rate", 0.05)
        report.record("error_rate", 0.01)

        trend = report.trend("error_rate")
        assert trend == "down"

    def test_trend_stable_when_equal(self):
        """# @trace WL-257 — trend returns 'stable' when first equals last."""
        from thegent.integrations.historical_trends import HistoricalTrendReport

        report = HistoricalTrendReport()
        report.record("metric", 50.0)
        report.record("metric", 100.0)
        report.record("metric", 50.0)

        trend = report.trend("metric")
        assert trend == "stable"

    def test_trend_stable_with_single_point(self):
        """# @trace WL-257 — trend returns 'stable' with single data point."""
        from thegent.integrations.historical_trends import HistoricalTrendReport

        report = HistoricalTrendReport()
        report.record("latency", 100.0)

        trend = report.trend("latency")
        assert trend == "stable"

    def test_trend_stable_with_no_data(self):
        """# @trace WL-257 — trend returns 'stable' when metric has no data."""
        from thegent.integrations.historical_trends import HistoricalTrendReport

        report = HistoricalTrendReport()
        trend = report.trend("nonexistent")
        assert trend == "stable"

    def test_timestamps_recorded_with_utc_timezone(self):
        """# @trace WL-257 — recorded timestamps have UTC timezone."""
        from thegent.integrations.historical_trends import HistoricalTrendReport

        report = HistoricalTrendReport()
        point = report.record("latency", 100.0)

        assert point.timestamp.tzinfo == UTC
