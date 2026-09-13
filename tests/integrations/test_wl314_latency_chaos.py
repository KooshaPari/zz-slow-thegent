"""Tests for WL-314: Connector Latency Chaos Mode."""

from __future__ import annotations

import pytest

from thegent.integrations.latency_chaos import ChaosConfig, LatencyChaosInjector


class TestChaosConfig:
    """Tests for ChaosConfig dataclass."""

    @pytest.mark.requirement("WL-314")
    def test_defaults(self) -> None:
        """Test ChaosConfig defaults."""
        config = ChaosConfig()
        assert config.enabled is False
        assert config.min_delay_ms == 100.0
        assert config.max_delay_ms == 2000.0
        assert config.failure_rate == 0.0

    @pytest.mark.requirement("WL-314")
    def test_custom_values(self) -> None:
        """Test ChaosConfig with custom values."""
        config = ChaosConfig(
            enabled=True, min_delay_ms=50.0, max_delay_ms=500.0, failure_rate=0.25
        )
        assert config.enabled is True
        assert config.min_delay_ms == 50.0
        assert config.max_delay_ms == 500.0
        assert config.failure_rate == 0.25


class TestLatencyChaosInjector:
    """Tests for LatencyChaosInjector."""

    @pytest.mark.requirement("WL-314")
    def test_init(self) -> None:
        """Test injector initialization."""
        config = ChaosConfig(enabled=True)
        injector = LatencyChaosInjector(config)
        assert injector._config == config

    @pytest.mark.requirement("WL-314")
    def test_compute_delay_disabled(self) -> None:
        """Test compute_delay returns 0 when disabled."""
        config = ChaosConfig(enabled=False)
        injector = LatencyChaosInjector(config)
        delay = injector.compute_delay("test-connector")
        assert delay == 0.0

    @pytest.mark.requirement("WL-314")
    def test_compute_delay_within_range(self) -> None:
        """Test compute_delay returns value in configured range."""
        config = ChaosConfig(enabled=True, min_delay_ms=100.0, max_delay_ms=200.0)
        injector = LatencyChaosInjector(config)
        # Sample multiple times to check range
        for _ in range(20):
            delay = injector.compute_delay("test-connector")
            assert 100.0 <= delay <= 200.0

    @pytest.mark.requirement("WL-314")
    def test_compute_delay_seeded(self) -> None:
        """Test compute_delay is deterministic with seed."""
        config = ChaosConfig(enabled=True, min_delay_ms=100.0, max_delay_ms=200.0)
        injector1 = LatencyChaosInjector(config).with_seed(42)
        injector2 = LatencyChaosInjector(config).with_seed(42)

        delays1 = [injector1.compute_delay("test") for _ in range(5)]
        delays2 = [injector2.compute_delay("test") for _ in range(5)]
        assert delays1 == delays2

    @pytest.mark.requirement("WL-314")
    def test_should_fail_disabled(self) -> None:
        """Test should_fail returns False when disabled."""
        config = ChaosConfig(enabled=False, failure_rate=1.0)
        injector = LatencyChaosInjector(config)
        assert injector.should_fail("test-connector") is False

    @pytest.mark.requirement("WL-314")
    def test_should_fail_zero_rate(self) -> None:
        """Test should_fail returns False with 0 failure rate."""
        config = ChaosConfig(enabled=True, failure_rate=0.0)
        injector = LatencyChaosInjector(config)
        for _ in range(20):
            assert injector.should_fail("test-connector") is False

    @pytest.mark.requirement("WL-314")
    def test_should_fail_unity_rate(self) -> None:
        """Test should_fail returns True with 1.0 failure rate."""
        config = ChaosConfig(enabled=True, failure_rate=1.0)
        injector = LatencyChaosInjector(config)
        for _ in range(20):
            assert injector.should_fail("test-connector") is True

    @pytest.mark.requirement("WL-314")
    def test_should_fail_seeded(self) -> None:
        """Test should_fail is deterministic with seed."""
        config = ChaosConfig(enabled=True, failure_rate=0.5)
        injector1 = LatencyChaosInjector(config).with_seed(42)
        injector2 = LatencyChaosInjector(config).with_seed(42)

        failures1 = [injector1.should_fail("test") for _ in range(10)]
        failures2 = [injector2.should_fail("test") for _ in range(10)]
        assert failures1 == failures2

    @pytest.mark.requirement("WL-314")
    def test_inject_returns_tuple(self) -> None:
        """Test inject returns (delay, should_fail) tuple."""
        config = ChaosConfig(enabled=True)
        injector = LatencyChaosInjector(config)
        delay, should_fail = injector.inject("test-connector")
        assert isinstance(delay, float)
        assert isinstance(should_fail, bool)

    @pytest.mark.requirement("WL-314")
    def test_inject_disabled(self) -> None:
        """Test inject with chaos disabled."""
        config = ChaosConfig(enabled=False, failure_rate=1.0)
        injector = LatencyChaosInjector(config)
        delay, should_fail = injector.inject("test-connector")
        assert delay == 0.0
        assert should_fail is False

    @pytest.mark.requirement("WL-314")
    def test_with_seed_creates_new_instance(self) -> None:
        """Test with_seed creates a new injector instance."""
        config = ChaosConfig(enabled=True)
        injector1 = LatencyChaosInjector(config)
        injector2 = injector1.with_seed(42)
        assert injector1 is not injector2
        assert injector1._config == injector2._config

    @pytest.mark.requirement("WL-314")
    def test_with_seed_reproducibility(self) -> None:
        """Test with_seed enables reproducible chaos injection."""
        config = ChaosConfig(enabled=True, min_delay_ms=50.0, max_delay_ms=150.0)
        injector1 = LatencyChaosInjector(config).with_seed(123)
        injector2 = LatencyChaosInjector(config).with_seed(123)

        results1 = [injector1.inject("conn") for _ in range(5)]
        results2 = [injector2.inject("conn") for _ in range(5)]
        assert results1 == results2
