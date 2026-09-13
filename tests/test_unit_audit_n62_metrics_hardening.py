"""Unit tests for governance/metrics.py hardening (AUDIT-N+62 pass-46).

FR-GOV-MT-001..015 invariants asserting the contract surface of the
metrics module.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import ClassVar

import pytest

from thegent.governance.metrics import (
    AggregatedMetrics,
    ExecutionResult,
    MetricsCollector,
    ProviderMetricsSnapshot,
)


# ---------------------------------------------------------------------------
# FR-GOV-MT-001: ExecutionResult stores fields correctly
# ---------------------------------------------------------------------------
class TestFRGOVMT001:
    """ExecutionResult dataclass stores fields correctly."""

    def test_stores_all_fields(self) -> None:
        result = ExecutionResult(
            provider_id="openai",
            success=True,
            latency_ms=123.45,
            tokens_used=512,
            error=None,
            timestamp=999.0,
        )
        assert result.provider_id == "openai"
        assert result.success is True
        assert result.latency_ms == 123.45
        assert result.tokens_used == 512
        assert result.error is None
        assert result.timestamp == 999.0

    def test_stores_error_field(self) -> None:
        result = ExecutionResult(
            provider_id="anthropic",
            success=False,
            latency_ms=50.0,
            tokens_used=0,
            error="timeout",
            timestamp=1000.0,
        )
        assert result.error == "timeout"
        assert result.success is False


# ---------------------------------------------------------------------------
# FR-GOV-MT-002: ExecutionResult default timestamp is set on construction
# ---------------------------------------------------------------------------
class TestFRGOVMT002:
    """ExecutionResult default timestamp is set on construction."""

    def test_default_timestamp_set(self) -> None:
        before = time.time()
        result = ExecutionResult(
            provider_id="test",
            success=True,
            latency_ms=10.0,
        )
        after = time.time()
        assert before <= result.timestamp <= after


# ---------------------------------------------------------------------------
# FR-GOV-MT-003: ProviderMetricsSnapshot default values
# ---------------------------------------------------------------------------
class TestFRGOVMT003:
    """ProviderMetricsSnapshot default values are correct."""

    def test_defaults(self) -> None:
        snap = ProviderMetricsSnapshot(provider_id="test")
        assert snap.success is True
        assert snap.latency_ms == 0.0
        assert snap.tokens_used == 0


# ---------------------------------------------------------------------------
# FR-GOV-MT-004: AggregatedMetrics.reliability returns 0.95 when total_count is 0
# ---------------------------------------------------------------------------
class TestFRGOVMT004:
    """AggregatedMetrics.reliability returns 0.95 when total_count is 0."""

    def test_zero_count_returns_default(self) -> None:
        agg = AggregatedMetrics(provider_id="test")
        assert agg.reliability == 0.95


# ---------------------------------------------------------------------------
# FR-GOV-MT-005: AggregatedMetrics.reliability returns success_count/total_count
# ---------------------------------------------------------------------------
class TestFRGOVMT005:
    """AggregatedMetrics.reliability returns success_count/total_count > 0."""

    def test_reliability_ratio(self) -> None:
        agg = AggregatedMetrics(provider_id="test", success_count=8, total_count=10)
        assert agg.reliability == pytest.approx(0.8)

    def test_all_success(self) -> None:
        agg = AggregatedMetrics(provider_id="test", success_count=5, total_count=5)
        assert agg.reliability == 1.0


# ---------------------------------------------------------------------------
# FR-GOV-MT-006: AggregatedMetrics.latency_p99 returns 250.0 < 10 samples
# ---------------------------------------------------------------------------
class TestFRGOVMT006:
    """AggregatedMetrics.latency_p99 returns 250.0 when fewer than 10 samples."""

    def test_fewer_than_10_returns_baseline(self) -> None:
        agg = AggregatedMetrics(provider_id="test")
        agg.latency_samples.extend([10.0, 20.0, 30.0])
        assert agg.latency_p99 == 250.0

    def test_exactly_9_returns_baseline(self) -> None:
        agg = AggregatedMetrics(provider_id="test")
        agg.latency_samples.extend([float(i) for i in range(9)])
        assert agg.latency_p99 == 250.0


# ---------------------------------------------------------------------------
# FR-GOV-MT-007: AggregatedMetrics.latency_p99 correct with 10+ samples
# ---------------------------------------------------------------------------
class TestFRGOVMT007:
    """AggregatedMetrics.latency_p99 returns correct percentile with 10+ samples."""

    def test_p99_with_samples(self) -> None:
        agg = AggregatedMetrics(provider_id="test")
        # 10 samples: 1..10
        agg.latency_samples.extend([float(i) for i in range(1, 11)])
        sorted_samples = sorted(range(1, 11))
        idx = int(len(sorted_samples) * 0.99)
        assert agg.latency_p99 == float(sorted_samples[idx])


# ---------------------------------------------------------------------------
# FR-GOV-MT-008: AggregatedMetrics.latency_mean returns 250.0 with no samples
# ---------------------------------------------------------------------------
class TestFRGOVMT008:
    """AggregatedMetrics.latency_mean returns 250.0 when no samples."""

    def test_no_samples_returns_baseline(self) -> None:
        agg = AggregatedMetrics(provider_id="test")
        assert agg.latency_mean == 250.0


# ---------------------------------------------------------------------------
# FR-GOV-MT-009: AggregatedMetrics.latency_mean returns correct mean
# ---------------------------------------------------------------------------
class TestFRGOVMT009:
    """AggregatedMetrics.latency_mean returns correct mean with samples."""

    def test_correct_mean(self) -> None:
        agg = AggregatedMetrics(provider_id="test")
        agg.latency_samples.extend([100.0, 200.0, 300.0])
        assert agg.latency_mean == pytest.approx(200.0)


# ---------------------------------------------------------------------------
# FR-GOV-MT-010: MetricsCollector.__init__ creates storage_dir
# ---------------------------------------------------------------------------
class TestFRGOVMT010:
    """MetricsCollector.__init__ creates storage_dir when provided."""

    def test_creates_storage_dir(self, tmp_path: Path) -> None:
        storage = tmp_path / "metrics_data"
        assert not storage.exists()
        MetricsCollector(storage_dir=storage)
        assert storage.exists()
        assert storage.is_dir()


# ---------------------------------------------------------------------------
# FR-GOV-MT-011: MetricsCollector.record() initializes provider deques
# ---------------------------------------------------------------------------
class TestFRGOVMT011:
    """MetricsCollector.record() initializes provider deques on first record."""

    def test_first_record_initializes(self) -> None:
        collector = MetricsCollector()
        snap = ProviderMetricsSnapshot(provider_id="test-provider", latency_ms=50.0)
        collector.record(snap)
        assert "test-provider" in collector._snapshots
        assert "test-provider" in collector._aggregates
        assert len(collector._snapshots["test-provider"]) == 1


# ---------------------------------------------------------------------------
# FR-GOV-MT-012: MetricsCollector.get_metrics() returns None for unknown
# ---------------------------------------------------------------------------
class TestFRGOVMT012:
    """MetricsCollector.get_metrics() returns None for unknown provider."""

    def test_unknown_provider(self) -> None:
        collector = MetricsCollector()
        assert collector.get_metrics("nonexistent") is None


# ---------------------------------------------------------------------------
# FR-GOV-MT-013: MetricsCollector.reset_provider() clears snapshots/aggregates
# ---------------------------------------------------------------------------
class TestFRGOVMT013:
    """MetricsCollector.reset_provider() clears snapshots and aggregates."""

    def test_reset_clears_state(self) -> None:
        collector = MetricsCollector()
        snap = ProviderMetricsSnapshot(provider_id="p1", latency_ms=100.0, success=True)
        collector.record(snap)
        assert len(collector._snapshots["p1"]) == 1

        collector.reset_provider("p1")
        assert len(collector._snapshots["p1"]) == 0
        agg = collector._aggregates["p1"]
        assert agg.total_count == 0
        assert agg.success_count == 0


# ---------------------------------------------------------------------------
# FR-GOV-MT-014: MetricsCollector.get_query_latency_ms() returns 0.0
# ---------------------------------------------------------------------------
class TestFRGOVMT014:
    """MetricsCollector.get_query_latency_ms() returns 0.0 (SLO contract)."""

    def test_returns_zero(self) -> None:
        collector = MetricsCollector()
        assert collector.get_query_latency_ms() == 0.0


# ---------------------------------------------------------------------------
# FR-GOV-MT-015: __all__ exports exactly the expected names
# ---------------------------------------------------------------------------
class TestFRGOVMT015:
    """__all__ exports exactly the expected public surface."""

    EXPECTED: ClassVar[list[str]] = [
        "ExecutionResult",
        "AggregatedMetrics",
        "MetricsCollector",
        "ProviderMetricsCollector",
        "ProviderMetricsSnapshot",
        "get_metrics_collector",
        "initialize_metrics_collector",
    ]

    def test_all_exports(self) -> None:
        from thegent.governance import metrics as mod

        assert hasattr(mod, "__all__")
        assert sorted(mod.__all__) == sorted(self.EXPECTED)

    def test_all_names_are_importable(self) -> None:
        import thegent.governance.metrics as mod

        for name in self.EXPECTED:
            assert hasattr(mod, name), f"{name} not importable from metrics module"
