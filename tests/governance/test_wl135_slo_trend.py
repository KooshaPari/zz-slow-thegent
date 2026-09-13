"""Tests for WL-135 SLO trend serialization (B90-W2-F4).

Verifies load_trend, serialize_trend, and window filtering behavior.

# @trace WL-135 B90-W2-F4
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from thegent.governance.slo_metrics import SloMetric
from thegent.governance.slo_trend import SloTrend, load_trend, serialize_trend


def _make_metric(timestamp: datetime, source: str = "test") -> SloMetric:
    """Build a minimal valid SloMetric for a given timestamp."""
    return SloMetric(
        file_loc=1000.0,
        function_loc_p95=50.0,
        impl_importers=10.0,
        cross_boundary_import_edges=5.0,
        cli_help_p95_ms=120.0,
        run_command_p95_ms=300.0,
        decomposition_checkpoint_pass_rate=1.0,
        timestamp=timestamp.isoformat(),
        source=source,
    )


def _write_jsonl(path: Path, metrics: list[SloMetric]) -> None:
    """Write a list of SloMetric records as JSONL to path."""
    import json
    from dataclasses import asdict

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for m in metrics:
            fh.write(json.dumps(asdict(m), sort_keys=True) + "\n")


class TestLoadTrend:
    """load_trend must read JSONL and filter by window_days."""

    # @trace WL-135 B90-W2-F4

    def test_load_trend_basic(self, tmp_path: Path) -> None:
        """load_trend returns SloTrend with all 3 records when all are within window."""
        now = datetime.now(UTC)
        metrics = [
            _make_metric(now - timedelta(days=1), source="run-a"),
            _make_metric(now - timedelta(days=3), source="run-b"),
            _make_metric(now - timedelta(days=5), source="run-c"),
        ]
        jsonl_path = tmp_path / "slo-metrics.jsonl"
        _write_jsonl(jsonl_path, metrics)

        trend = load_trend(jsonl_path, window_days=7)

        assert isinstance(trend, SloTrend)
        assert len(trend.metrics) == 3
        assert trend.window_days == 7

    def test_load_trend_window_filters_old_records(self, tmp_path: Path) -> None:
        """load_trend drops records older than window_days."""
        now = datetime.now(UTC)
        metrics = [
            _make_metric(now - timedelta(days=1), source="recent"),
            _make_metric(now - timedelta(days=10), source="old"),
            _make_metric(now - timedelta(days=20), source="very-old"),
        ]
        jsonl_path = tmp_path / "slo-metrics.jsonl"
        _write_jsonl(jsonl_path, metrics)

        trend = load_trend(jsonl_path, window_days=7)

        assert len(trend.metrics) == 1
        assert trend.metrics[0].source == "recent"

    def test_load_trend_empty_window(self, tmp_path: Path) -> None:
        """load_trend returns empty metrics list when all records are outside window."""
        now = datetime.now(UTC)
        metrics = [
            _make_metric(now - timedelta(days=30), source="ancient"),
        ]
        jsonl_path = tmp_path / "slo-metrics.jsonl"
        _write_jsonl(jsonl_path, metrics)

        trend = load_trend(jsonl_path, window_days=7)

        assert trend.metrics == []
        assert trend.window_days == 7

    def test_load_trend_missing_file_raises(self, tmp_path: Path) -> None:
        """load_trend raises FileNotFoundError if JSONL file does not exist."""
        missing = tmp_path / "nonexistent.jsonl"
        with pytest.raises(FileNotFoundError, match="not found"):
            load_trend(missing, window_days=7)

    def test_load_trend_malformed_json_raises(self, tmp_path: Path) -> None:
        """load_trend raises ValueError on malformed JSONL lines."""
        jsonl_path = tmp_path / "bad.jsonl"
        jsonl_path.write_text("not json at all\n", encoding="utf-8")
        with pytest.raises(ValueError, match="invalid JSON"):
            load_trend(jsonl_path, window_days=7)

    def test_load_trend_missing_fields_raises(self, tmp_path: Path) -> None:
        """load_trend raises ValueError when a record is missing required fields."""
        jsonl_path = tmp_path / "incomplete.jsonl"
        # Write a record with only some fields
        jsonl_path.write_text(
            json.dumps({"file_loc": 100.0, "timestamp": datetime.now(UTC).isoformat()}) + "\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="missing fields"):
            load_trend(jsonl_path, window_days=7)


class TestSerializeTrend:
    """serialize_trend must produce valid, deterministic JSON."""

    # @trace WL-135 B90-W2-F4

    def test_serialize_produces_valid_json(self) -> None:
        """serialize_trend output must parse as valid JSON."""
        now = datetime.now(UTC)
        trend = SloTrend(
            metrics=[_make_metric(now, source="test-a")],
            window_days=7,
            generated_at=now.isoformat(),
        )
        serialized = serialize_trend(trend)
        parsed = json.loads(serialized)
        assert isinstance(parsed, dict)

    def test_serialize_contains_required_keys(self) -> None:
        """serialize_trend JSON must contain window_days, generated_at, metrics."""
        now = datetime.now(UTC)
        trend = SloTrend(
            metrics=[_make_metric(now, source="test-b")],
            window_days=14,
            generated_at=now.isoformat(),
        )
        parsed = json.loads(serialize_trend(trend))
        assert "window_days" in parsed
        assert "generated_at" in parsed
        assert "metrics" in parsed
        assert parsed["window_days"] == 14

    def test_serialize_metrics_list_length(self) -> None:
        """serialize_trend metrics list length must match input trend.metrics."""
        now = datetime.now(UTC)
        records = [_make_metric(now - timedelta(hours=i)) for i in range(3)]
        trend = SloTrend(metrics=records, window_days=7, generated_at=now.isoformat())
        parsed = json.loads(serialize_trend(trend))
        assert len(parsed["metrics"]) == 3

    def test_serialize_empty_trend(self) -> None:
        """serialize_trend handles empty metrics list without error."""
        now = datetime.now(UTC)
        trend = SloTrend(metrics=[], window_days=7, generated_at=now.isoformat())
        parsed = json.loads(serialize_trend(trend))
        assert parsed["metrics"] == []

    def test_roundtrip_via_jsonl(self, tmp_path: Path) -> None:
        """load_trend -> serialize_trend roundtrip must preserve metric count."""
        now = datetime.now(UTC)
        original = [
            _make_metric(now - timedelta(hours=1), source="snap-1"),
            _make_metric(now - timedelta(hours=2), source="snap-2"),
        ]
        jsonl_path = tmp_path / "slo.jsonl"
        _write_jsonl(jsonl_path, original)

        trend = load_trend(jsonl_path, window_days=7)
        serialized = serialize_trend(trend)
        parsed = json.loads(serialized)

        assert len(parsed["metrics"]) == 2
