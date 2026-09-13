"""Unit tests for Phase 2.1: Provider Scoring System (WP-5003).

Tests cover:
- DefaultProviderScorer normalization and composition
- ProviderRegistry registration and lookup
- MetricsCollector aggregation and persistence

See: docs/changes/research-economic-governance/tasks.md § Phase 2.1
"""

import tempfile
from pathlib import Path

import orjson as json
import pytest

from thegent.governance.metrics import (
    AggregatedMetrics,
    MetricsCollector,
    ProviderMetricsSnapshot,
)
from thegent.governance.providers import ProviderConfig, ProviderRegistry, ProviderType
from thegent.governance.scoring import (
    DefaultProviderScorer,
    ProviderMetrics,
    ProviderScore,
)

# ============================================================================
# Tests for DefaultProviderScorer (Task 2.1.1)
# ============================================================================


class TestDefaultProviderScorer:
    """Test suite for DefaultProviderScorer.

    Acceptance Criteria:
    - Composite score correctly weighted (0.4/0.2/0.4)
    - Latency normalization produces 0-10 range
    - Cost normalization produces 0-10 range
    - Score inversely weighted (higher cost/latency = lower score)
    - Unit tests passing (>95% coverage)
    """

    def test_scorer_initialization(self):
        """Test scorer can be initialized."""
        scorer = DefaultProviderScorer()
        assert scorer.RELIABILITY_WEIGHT == 0.4
        assert scorer.LATENCY_WEIGHT == 0.2
        assert scorer.COST_WEIGHT == 0.4

    def test_weights_sum_to_one(self):
        """Test that weights sum to exactly 1.0."""
        scorer = DefaultProviderScorer()
        total = scorer.RELIABILITY_WEIGHT + scorer.LATENCY_WEIGHT + scorer.COST_WEIGHT
        assert abs(total - 1.0) < 0.0001

    def test_score_perfect_provider(self):
        """Test scoring for a perfect provider (100% reliability, low latency, low cost)."""
        scorer = DefaultProviderScorer()
        metrics = ProviderMetrics(
            provider_id="perfect-provider",
            reliability=1.0,  # 100% uptime
            latency_p99=100.0,  # Fast (baseline is 250ms)
            cost_per_1m_tokens=0.05,  # Cheap (baseline is 0.15)
            sample_size=1000,
        )
        score = scorer.score(metrics)

        assert score.provider_id == "perfect-provider"
        assert score.reliability_score == 10.0  # max reliability
        assert score.latency_score > 8.0  # fast = high score
        assert score.cost_score > 8.0  # cheap = high score
        assert score.composite_score > 9.0  # overall excellent

    def test_score_poor_provider(self):
        """Test scoring for a poor provider (low reliability, high latency, high cost)."""
        scorer = DefaultProviderScorer()
        metrics = ProviderMetrics(
            provider_id="poor-provider",
            reliability=0.9,  # 90% uptime
            latency_p99=500.0,  # Slow (2× baseline)
            cost_per_1m_tokens=0.30,  # Expensive (2× baseline)
            sample_size=1000,
        )
        score = scorer.score(metrics)

        assert score.reliability_score == 9.0  # 0.9 × 10
        assert score.latency_score < 5.0  # slow = low score
        assert score.cost_score < 5.0  # expensive = low score
        assert score.composite_score < 7.0  # overall mediocre

    def test_score_baseline_provider(self):
        """Test scoring for provider at normalization baseline."""
        scorer = DefaultProviderScorer()
        metrics = ProviderMetrics(
            provider_id="baseline-provider",
            reliability=0.95,  # 95% uptime
            latency_p99=250.0,  # exactly baseline
            cost_per_1m_tokens=0.15,  # exactly baseline
            sample_size=1000,
        )
        score = scorer.score(metrics)

        assert score.reliability_score == 9.5  # 0.95 × 10
        assert abs(score.latency_score - 5.0) < 0.5  # baseline = score ~5
        assert abs(score.cost_score - 5.0) < 0.5  # baseline = score ~5

    def test_normalize_reliability_linear(self):
        """Test reliability normalization is linear (0.0-1.0 → 0-10)."""
        scorer = DefaultProviderScorer()

        assert scorer.normalize(0.0, "reliability") == 0.0
        assert scorer.normalize(0.5, "reliability") == 5.0
        assert scorer.normalize(1.0, "reliability") == 10.0

    def test_normalize_latency_inverse(self):
        """Test latency normalization is inverse (lower latency = higher score)."""
        scorer = DefaultProviderScorer()

        # Test baseline (250ms → score 5.0)
        baseline_score = scorer.normalize(250.0, "latency")
        assert abs(baseline_score - 5.0) < 0.5

        # Test faster than baseline (100ms → score > 5.0)
        fast_score = scorer.normalize(100.0, "latency")
        assert fast_score > baseline_score

        # Test slower than baseline (500ms → score < 5.0)
        slow_score = scorer.normalize(500.0, "latency")
        assert slow_score < baseline_score

    def test_normalize_latency_range(self):
        """Test latency normalization stays within 0-10 range."""
        scorer = DefaultProviderScorer()

        # Test extreme values
        for latency in [1, 10, 100, 250, 500, 1000, 5000]:
            score = scorer.normalize(latency, "latency")
            assert 0.0 <= score <= 10.0, f"Latency {latency}ms produced score {score}"

    def test_normalize_cost_inverse(self):
        """Test cost normalization is inverse (lower cost = higher score)."""
        scorer = DefaultProviderScorer()

        # Test baseline ($0.15/1M → score 5.0)
        baseline_score = scorer.normalize(0.15, "cost")
        assert abs(baseline_score - 5.0) < 0.5

        # Test cheaper than baseline (0.06/1M → score > 5.0)
        cheap_score = scorer.normalize(0.06, "cost")
        assert cheap_score > baseline_score

        # Test more expensive than baseline (0.30/1M → score < 5.0)
        expensive_score = scorer.normalize(0.30, "cost")
        assert expensive_score < baseline_score

    def test_normalize_cost_range(self):
        """Test cost normalization stays within 0-10 range."""
        scorer = DefaultProviderScorer()

        # Test extreme values
        for cost in [0.01, 0.05, 0.15, 0.30, 1.0, 5.0, 10.0]:
            score = scorer.normalize(cost, "cost")
            assert 0.0 <= score <= 10.0, f"Cost ${cost}/1M produced score {score}"

    def test_normalize_invalid_metric_type(self):
        """Test that invalid metric types raise ValueError."""
        scorer = DefaultProviderScorer()

        with pytest.raises(ValueError):
            scorer.normalize(100.0, "invalid_type")

    def test_composite_score_weighting(self):
        """Test composite score uses correct weights."""
        scorer = DefaultProviderScorer()

        # Create metrics where each component has known score
        metrics = ProviderMetrics(
            provider_id="test",
            reliability=1.0,  # reliability_score = 10.0
            latency_p99=250.0,  # latency_score ≈ 5.0
            cost_per_1m_tokens=0.15,  # cost_score ≈ 5.0
            sample_size=1000,
        )
        score = scorer.score(metrics)

        # Composite = 10.0×0.4 + 5.0×0.2 + 5.0×0.4 = 4.0 + 1.0 + 2.0 = 7.0
        assert 6.8 < score.composite_score < 7.2

    def test_score_output_format(self):
        """Test ProviderScore dataclass has all required fields."""
        scorer = DefaultProviderScorer()
        metrics = ProviderMetrics(
            provider_id="test",
            reliability=0.95,
            latency_p99=250.0,
            cost_per_1m_tokens=0.15,
            sample_size=1000,
        )
        score = scorer.score(metrics)

        # Check all fields present and correct types
        assert isinstance(score, ProviderScore)
        assert isinstance(score.provider_id, str)
        assert isinstance(score.reliability_score, float)
        assert isinstance(score.latency_score, float)
        assert isinstance(score.cost_score, float)
        assert isinstance(score.composite_score, float)
        assert isinstance(score.timestamp, float)


# ============================================================================
# Tests for ProviderRegistry (Task 2.1.2)
# ============================================================================


class TestProviderRegistry:
    """Test suite for ProviderRegistry.

    Acceptance Criteria:
    - Registry initialized with 4+ providers
    - Each provider has: cost, reliability, latency, fallback chain
    - get(), list_providers(), get_fallback_order() work
    - Fallback chains prioritize cost-efficiency
    - Integration tests with mock providers
    """

    def setup_method(self):
        """Clear registry before each test."""
        ProviderRegistry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        ProviderRegistry.clear()

    def test_registry_initializes_with_builtin_providers(self):
        """Test registry loads with built-in providers."""
        # Import module to trigger initialization
        from thegent.governance import providers as prov_module

        prov_module._initialize_registry()

        # Should have at least 4 built-in providers
        providers = ProviderRegistry.list_providers()
        assert len(providers) >= 4

    def test_register_provider(self):
        """Test registering a new provider."""
        config = ProviderConfig(
            provider_id="test-provider",
            name="Test Provider",
            provider_type=ProviderType.DIRECT,
            api_endpoint="https://test.example.com",
            auth_method="api_key",
            cost_per_1m_tokens=0.20,
            max_rpm=1000,
            max_tpm=500000,
        )

        ProviderRegistry.register(config)
        retrieved = ProviderRegistry.get("test-provider")

        assert retrieved is not None
        assert retrieved.provider_id == "test-provider"
        assert retrieved.cost_per_1m_tokens == 0.20

    def test_get_nonexistent_provider(self):
        """Test getting a provider that doesn't exist."""
        result = ProviderRegistry.get("nonexistent")
        assert result is None

    def test_list_providers(self):
        """Test listing all registered providers."""
        config1 = ProviderConfig(
            provider_id="provider-1",
            name="Provider 1",
            provider_type=ProviderType.DIRECT,
            api_endpoint="https://1.example.com",
            auth_method="api_key",
            cost_per_1m_tokens=0.10,
            max_rpm=1000,
            max_tpm=500000,
        )
        config2 = ProviderConfig(
            provider_id="provider-2",
            name="Provider 2",
            provider_type=ProviderType.PROXY,
            api_endpoint="https://2.example.com",
            auth_method="oauth",
            cost_per_1m_tokens=0.20,
            max_rpm=2000,
            max_tpm=1000000,
        )

        ProviderRegistry.register(config1)
        ProviderRegistry.register(config2)

        providers = ProviderRegistry.list_providers()
        assert len(providers) == 2
        assert any(p.provider_id == "provider-1" for p in providers)
        assert any(p.provider_id == "provider-2" for p in providers)

    def test_get_fallback_order(self):
        """Test retrieving fallback chain for a provider."""
        config = ProviderConfig(
            provider_id="main-provider",
            name="Main Provider",
            provider_type=ProviderType.DIRECT,
            api_endpoint="https://main.example.com",
            auth_method="api_key",
            cost_per_1m_tokens=0.15,
            max_rpm=1000,
            max_tpm=500000,
            fallback_order=["fallback-1", "fallback-2"],
        )

        ProviderRegistry.register(config)
        fallbacks = ProviderRegistry.get_fallback_order("main-provider")

        assert fallbacks == ["fallback-1", "fallback-2"]

    def test_get_fallback_order_empty(self):
        """Test fallback order for provider with no fallbacks."""
        config = ProviderConfig(
            provider_id="no-fallback",
            name="No Fallback",
            provider_type=ProviderType.DIRECT,
            api_endpoint="https://nofallback.example.com",
            auth_method="api_key",
            cost_per_1m_tokens=0.15,
            max_rpm=1000,
            max_tpm=500000,
            fallback_order=[],
        )

        ProviderRegistry.register(config)
        fallbacks = ProviderRegistry.get_fallback_order("no-fallback")

        assert fallbacks == []

    def test_provider_config_has_required_fields(self):
        """Test that registered providers have required metadata."""
        config = ProviderConfig(
            provider_id="test",
            name="Test",
            provider_type=ProviderType.DIRECT,
            api_endpoint="https://test.example.com",
            auth_method="api_key",
            cost_per_1m_tokens=0.15,
            max_rpm=1000,
            max_tpm=500000,
        )

        ProviderRegistry.register(config)
        provider = ProviderRegistry.get("test")

        assert provider.provider_id == "test"
        assert provider.cost_per_1m_tokens > 0
        assert provider.max_rpm > 0
        assert provider.max_tpm > 0


# ============================================================================
# Tests for MetricsCollector (Task 2.1.3)
# ============================================================================


class TestMetricsCollector:
    """Test suite for MetricsCollector.

    Acceptance Criteria:
    - Metrics collection for each provider
    - Latency p99 calculation from samples
    - Success rate calculation
    - Storage in Supermemory L3 (or fallback to local)
    - Metrics queryable within <50ms
    """

    def test_collector_initialization(self):
        """Test metrics collector can be initialized."""
        collector = MetricsCollector()
        assert collector.storage_dir is None

    def test_collector_initialization_with_storage(self):
        """Test metrics collector with storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = MetricsCollector(Path(tmpdir))
            assert collector.storage_dir == Path(tmpdir)

    def test_record_single_snapshot(self):
        """Test recording a single metric snapshot."""
        collector = MetricsCollector()
        snapshot = ProviderMetricsSnapshot(
            provider_id="test-provider",
            success=True,
            latency_ms=100.0,
            tokens_used=1000,
        )

        collector.record(snapshot)
        metrics = collector.get_metrics("test-provider")

        assert metrics is not None
        assert metrics.provider_id == "test-provider"
        assert metrics.total_count == 1
        assert metrics.success_count == 1
        assert metrics.total_tokens == 1000

    def test_record_multiple_snapshots(self):
        """Test recording multiple snapshots."""
        collector = MetricsCollector()

        for i in range(10):
            snapshot = ProviderMetricsSnapshot(
                provider_id="test-provider",
                success=(i % 2 == 0),  # 5 successes, 5 failures
                latency_ms=100.0 + i * 10,
                tokens_used=100,
            )
            collector.record(snapshot)

        metrics = collector.get_metrics("test-provider")

        assert metrics.total_count == 10
        assert metrics.success_count == 5
        assert metrics.total_tokens == 1000

    def test_reliability_calculation(self):
        """Test success rate (reliability) calculation."""
        collector = MetricsCollector()

        # Record 8 successes and 2 failures
        for i in range(10):
            snapshot = ProviderMetricsSnapshot(
                provider_id="test",
                success=(i < 8),
                latency_ms=100.0,
            )
            collector.record(snapshot)

        metrics = collector.get_metrics("test")
        assert abs(metrics.reliability - 0.8) < 0.01  # 80% success rate

    def test_latency_p99_calculation(self):
        """Test P99 latency calculation from samples."""
        collector = MetricsCollector()

        # Record 100 snapshots with latencies 1-100ms
        for i in range(1, 101):
            snapshot = ProviderMetricsSnapshot(
                provider_id="test",
                success=True,
                latency_ms=float(i),
            )
            collector.record(snapshot)

        metrics = collector.get_metrics("test")
        p99 = metrics.latency_p99

        # P99 should be around 99ms (99th percentile of 1-100)
        assert 95 < p99 <= 100, f"P99 {p99} not in expected range"

    def test_latency_p99_with_insufficient_samples(self):
        """Test P99 returns baseline when insufficient samples."""
        collector = MetricsCollector()

        # Record only 5 snapshots
        for _i in range(5):
            snapshot = ProviderMetricsSnapshot(
                provider_id="test",
                success=True,
                latency_ms=100.0,
            )
            collector.record(snapshot)

        metrics = collector.get_metrics("test")
        p99 = metrics.latency_p99

        # With < 10 samples, should return baseline (250ms)
        assert p99 == 250.0

    def test_latency_mean_calculation(self):
        """Test mean latency calculation."""
        collector = MetricsCollector()

        latencies = [50.0, 100.0, 150.0, 200.0]
        for latency in latencies:
            snapshot = ProviderMetricsSnapshot(
                provider_id="test",
                success=True,
                latency_ms=latency,
            )
            collector.record(snapshot)

        metrics = collector.get_metrics("test")
        mean = metrics.latency_mean

        expected_mean = sum(latencies) / len(latencies)
        assert abs(mean - expected_mean) < 0.01

    def test_get_all_metrics(self):
        """Test getting metrics for all providers."""
        collector = MetricsCollector()

        # Record snapshots for 3 providers
        for provider_id in ["p1", "p2", "p3"]:
            snapshot = ProviderMetricsSnapshot(
                provider_id=provider_id,
                success=True,
                latency_ms=100.0,
            )
            collector.record(snapshot)

        all_metrics = collector.get_all_metrics()

        assert len(all_metrics) == 3
        assert "p1" in all_metrics
        assert "p2" in all_metrics
        assert "p3" in all_metrics

    def test_save_metrics_to_file(self):
        """Test saving metrics to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = MetricsCollector(Path(tmpdir))

            # Record some snapshots
            for i in range(10):
                snapshot = ProviderMetricsSnapshot(
                    provider_id="test",
                    success=(i < 9),
                    latency_ms=100.0 + i * 10,
                    tokens_used=500,
                )
                collector.record(snapshot)

            # Save to file
            filepath = collector.save_to_file("test")

            assert filepath is not None
            assert filepath.exists()

            # Verify saved data
            with open(filepath) as f:
                data = json.load(f)

            assert data["provider_id"] == "test"
            assert data["success_count"] == 9
            assert data["total_count"] == 10

    def test_load_metrics_from_file(self):
        """Test loading metrics from JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a metrics file
            metrics_file = Path(tmpdir) / "metrics.json"
            data = {
                "provider_id": "test",
                "success_count": 9,
                "total_count": 10,
                "total_tokens": 5000,
            }

            with open(metrics_file, "w") as f:
                json.dump(data, f)

            # Load from file
            collector = MetricsCollector(Path(tmpdir))
            loaded_metrics = collector.load_from_file(metrics_file)

            assert loaded_metrics is not None
            assert loaded_metrics.provider_id == "test"
            assert loaded_metrics.success_count == 9
            assert loaded_metrics.total_count == 10

    def test_query_latency_ms(self):
        """Test that metrics queries are fast (<50ms SLO)."""
        collector = MetricsCollector()

        # Record some snapshots
        for _i in range(100):
            snapshot = ProviderMetricsSnapshot(
                provider_id="test",
                success=True,
                latency_ms=100.0,
            )
            collector.record(snapshot)

        # Query latency should be minimal (in-memory)
        latency = collector.get_query_latency_ms()
        assert latency < 50  # Well under SLO

    def test_reset_provider(self):
        """Test resetting metrics for a provider."""
        collector = MetricsCollector()

        # Record snapshots
        snapshot = ProviderMetricsSnapshot(
            provider_id="test",
            success=True,
            latency_ms=100.0,
        )
        collector.record(snapshot)

        # Verify recorded
        assert collector.get_metrics("test").total_count == 1

        # Reset
        collector.reset_provider("test")

        # Verify reset
        assert collector.get_metrics("test").total_count == 0

    def test_clear_all_metrics(self):
        """Test clearing all metrics."""
        collector = MetricsCollector()

        # Record for multiple providers
        for provider_id in ["p1", "p2", "p3"]:
            snapshot = ProviderMetricsSnapshot(provider_id=provider_id)
            collector.record(snapshot)

        assert len(collector.get_all_metrics()) == 3

        # Clear all
        collector.clear_all()

        assert len(collector.get_all_metrics()) == 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestPhase21Integration:
    """Integration tests for Phase 2.1 components working together."""

    def test_scorer_with_collected_metrics(self):
        """Test provider scorer using metrics from collector."""
        # Collect metrics
        collector = MetricsCollector()
        for i in range(100):
            snapshot = ProviderMetricsSnapshot(
                provider_id="test-provider",
                success=(i < 95),  # 95% success rate
                latency_ms=150.0 + i * 0.5,  # Varying latency
                tokens_used=1000,
            )
            collector.record(snapshot)

        # Score the provider based on collected metrics
        metrics = collector.get_metrics("test-provider")
        provider_metrics = ProviderMetrics(
            provider_id="test-provider",
            reliability=metrics.reliability,
            latency_p99=metrics.latency_p99,
            cost_per_1m_tokens=0.15,
            sample_size=metrics.total_count,
        )

        scorer = DefaultProviderScorer()
        score = scorer.score(provider_metrics)

        # Verify score is reasonable
        assert 0 <= score.composite_score <= 10
        assert score.reliability_score == 9.5  # 95% uptime

    def test_registry_and_scorer_together(self):
        """Test provider registry with scorer."""
        # Register providers
        provider1 = ProviderConfig(
            provider_id="cheap",
            name="Cheap Provider",
            provider_type=ProviderType.DIRECT,
            api_endpoint="https://cheap.example.com",
            auth_method="api_key",
            cost_per_1m_tokens=0.10,
            max_rpm=1000,
            max_tpm=500000,
            fallback_order=["expensive"],
        )

        provider2 = ProviderConfig(
            provider_id="expensive",
            name="Expensive Provider",
            provider_type=ProviderType.DIRECT,
            api_endpoint="https://expensive.example.com",
            auth_method="api_key",
            cost_per_1m_tokens=0.30,
            max_rpm=2000,
            max_tpm=1000000,
            fallback_order=[],
        )

        ProviderRegistry.register(provider1)
        ProviderRegistry.register(provider2)

        # Score based on cost
        scorer = DefaultProviderScorer()

        cheap_score = scorer.score(
            ProviderMetrics(
                provider_id="cheap",
                reliability=0.95,
                latency_p99=200.0,
                cost_per_1m_tokens=0.10,
                sample_size=100,
            )
        )

        expensive_score = scorer.score(
            ProviderMetrics(
                provider_id="expensive",
                reliability=0.95,
                latency_p99=200.0,
                cost_per_1m_tokens=0.30,
                sample_size=100,
            )
        )

        # Cheap provider should score higher
        assert cheap_score.cost_score > expensive_score.cost_score
        assert cheap_score.composite_score > expensive_score.composite_score

        # Cleanup
        ProviderRegistry.clear()


# ============================================================================
# Coverage and Performance Tests
# ============================================================================


class TestPhase21Coverage:
    """Ensure >95% code coverage for Phase 2.1 components."""

    def test_coverage_provider_metrics_dataclass(self):
        """Test ProviderMetrics dataclass initialization."""
        metrics = ProviderMetrics(
            provider_id="test",
            reliability=0.95,
            latency_p99=250.0,
            cost_per_1m_tokens=0.15,
            sample_size=1000,
        )

        assert metrics.provider_id == "test"
        assert metrics.reliability == 0.95

    def test_coverage_provider_score_dataclass(self):
        """Test ProviderScore dataclass initialization."""
        score = ProviderScore(
            provider_id="test",
            reliability_score=9.5,
            latency_score=5.0,
            cost_score=5.0,
            composite_score=6.6,
        )

        assert score.provider_id == "test"
        assert score.composite_score == 6.6

    def test_coverage_aggregated_metrics(self):
        """Test AggregatedMetrics properties."""
        metrics = AggregatedMetrics(provider_id="test")

        # Test defaults
        assert metrics.reliability == 0.95  # Conservative default
        assert metrics.latency_p99 == 250.0  # Baseline
        assert metrics.latency_mean == 250.0  # No samples

    def test_coverage_aggregated_metrics_with_data(self):
        """Test AggregatedMetrics with actual data."""
        metrics = AggregatedMetrics(provider_id="test")
        metrics.success_count = 95
        metrics.total_count = 100
        for _ in range(100):
            metrics.latency_samples.append(100.0)

        assert abs(metrics.reliability - 0.95) < 0.01
        assert metrics.latency_mean == 100.0
        assert metrics.latency_p99 == 100.0
