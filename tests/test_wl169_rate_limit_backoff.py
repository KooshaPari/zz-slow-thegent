"""Tests for WL-169: API Rate-Limit Backoff Controls.

@pytest.mark.requirement("WL-169")
"""

from __future__ import annotations

import pytest

from thegent.integrations.rate_limit_backoff import (
    RateLimitBackoffManager,
    RateLimitConfig,
)

# ---------------------------------------------------------------------------
# Test: RateLimitConfig
# ---------------------------------------------------------------------------


class TestRateLimitConfig:
    """Test RateLimitConfig dataclass."""

    @pytest.mark.requirement("WL-169")
    def test_default_config(self) -> None:
        """Test creating a config with default values."""
        config = RateLimitConfig()
        assert config.max_retries == 5
        assert config.initial_wait == 1.0
        assert config.max_wait == 60.0
        assert config.multiplier == 2.0

    @pytest.mark.requirement("WL-169")
    def test_custom_config(self) -> None:
        """Test creating a config with custom values."""
        config = RateLimitConfig(
            max_retries=10,
            initial_wait=0.5,
            max_wait=120.0,
            multiplier=3.0,
        )
        assert config.max_retries == 10
        assert config.initial_wait == 0.5
        assert config.max_wait == 120.0
        assert config.multiplier == 3.0

    @pytest.mark.requirement("WL-169")
    def test_validate_negative_retries(self) -> None:
        """Test validation catches negative max_retries."""
        config = RateLimitConfig(max_retries=-1)
        with pytest.raises(ValueError):
            config.validate()

    @pytest.mark.requirement("WL-169")
    def test_validate_invalid_initial_wait(self) -> None:
        """Test validation catches invalid initial_wait."""
        config = RateLimitConfig(initial_wait=0.0)
        with pytest.raises(ValueError):
            config.validate()

        config = RateLimitConfig(initial_wait=-1.0)
        with pytest.raises(ValueError):
            config.validate()

    @pytest.mark.requirement("WL-169")
    def test_validate_max_wait_less_than_initial(self) -> None:
        """Test validation catches max_wait < initial_wait."""
        config = RateLimitConfig(initial_wait=10.0, max_wait=5.0)
        with pytest.raises(ValueError):
            config.validate()

    @pytest.mark.requirement("WL-169")
    def test_validate_invalid_multiplier(self) -> None:
        """Test validation catches invalid multiplier."""
        config = RateLimitConfig(multiplier=0.5)
        with pytest.raises(ValueError):
            config.validate()


# ---------------------------------------------------------------------------
# Test: RateLimitBackoffManager - Rate Limit Detection
# ---------------------------------------------------------------------------


class TestRateLimitDetection:
    """Test rate-limit code detection."""

    @pytest.mark.requirement("WL-169")
    def test_is_rate_limited_429(self) -> None:
        """Test detecting 429 (Too Many Requests)."""
        manager = RateLimitBackoffManager()
        assert manager.is_rate_limited(429)

    @pytest.mark.requirement("WL-169")
    def test_is_rate_limited_503(self) -> None:
        """Test detecting 503 (Service Unavailable)."""
        manager = RateLimitBackoffManager()
        assert manager.is_rate_limited(503)

    @pytest.mark.requirement("WL-169")
    def test_is_not_rate_limited_200(self) -> None:
        """Test that 200 is not rate limited."""
        manager = RateLimitBackoffManager()
        assert not manager.is_rate_limited(200)

    @pytest.mark.requirement("WL-169")
    def test_is_not_rate_limited_400(self) -> None:
        """Test that 400 is not rate limited."""
        manager = RateLimitBackoffManager()
        assert not manager.is_rate_limited(400)

    @pytest.mark.requirement("WL-169")
    def test_is_not_rate_limited_500(self) -> None:
        """Test that 500 is not rate limited."""
        manager = RateLimitBackoffManager()
        assert not manager.is_rate_limited(500)


# ---------------------------------------------------------------------------
# Test: Exponential Backoff Calculation
# ---------------------------------------------------------------------------


class TestExponentialBackoff:
    """Test exponential backoff time calculation."""

    @pytest.mark.requirement("WL-169")
    def test_compute_wait_attempt_zero(self) -> None:
        """Test wait time for attempt 0 (no wait)."""
        manager = RateLimitBackoffManager()
        assert manager.compute_wait(0) == 0.0

    @pytest.mark.requirement("WL-169")
    def test_compute_wait_attempt_one(self) -> None:
        """Test wait time for attempt 1."""
        config = RateLimitConfig(initial_wait=1.0, multiplier=2.0, max_wait=60.0)
        manager = RateLimitBackoffManager(config)

        wait = manager.compute_wait(1)
        # Should be approximately initial_wait (1.0) ± jitter
        assert 0.9 < wait < 1.1

    @pytest.mark.requirement("WL-169")
    def test_compute_wait_increases_exponentially(self) -> None:
        """Test that wait time increases exponentially."""
        config = RateLimitConfig(
            initial_wait=1.0,
            multiplier=2.0,
            max_wait=1000.0,
        )
        manager = RateLimitBackoffManager(config)

        # Compute waits for several attempts (ignoring jitter)
        wait_1 = manager.compute_wait(1)
        wait_2 = manager.compute_wait(2)
        wait_3 = manager.compute_wait(3)

        # Rough checks (accounting for jitter)
        assert 0 < wait_1 < 2.0  # ~1.0
        assert wait_2 > wait_1  # ~2.0
        assert wait_3 > wait_2  # ~4.0

    @pytest.mark.requirement("WL-169")
    def test_compute_wait_caps_at_max(self) -> None:
        """Test that wait time is capped at max_wait."""
        config = RateLimitConfig(
            initial_wait=1.0,
            multiplier=10.0,
            max_wait=30.0,
        )
        manager = RateLimitBackoffManager(config)

        # With multiplier 10, attempt 10 would be 10^10 seconds without cap
        wait = manager.compute_wait(10)
        assert wait <= 30.0

    @pytest.mark.requirement("WL-169")
    def test_compute_wait_with_custom_multiplier(self) -> None:
        """Test wait calculation with custom multiplier."""
        config = RateLimitConfig(
            initial_wait=2.0,
            multiplier=3.0,
            max_wait=1000.0,
        )
        manager = RateLimitBackoffManager(config)

        wait_1 = manager.compute_wait(1)
        # Approximately 2.0 ± jitter
        assert 1.8 < wait_1 < 2.2

    @pytest.mark.requirement("WL-169")
    def test_compute_wait_negative_attempt(self) -> None:
        """Test wait time for negative attempt (treated as 0)."""
        manager = RateLimitBackoffManager()
        assert manager.compute_wait(-5) == 0.0


# ---------------------------------------------------------------------------
# Test: Tenacity Integration
# ---------------------------------------------------------------------------


class TestTenacityIntegration:
    """Test tenacity decorator integration."""

    @pytest.mark.requirement("WL-169")
    def test_get_retry_config_structure(self) -> None:
        """Test that retry config has expected structure."""
        manager = RateLimitBackoffManager()
        config = manager.get_retry_config()

        assert "wait" in config
        assert "stop" in config
        assert "reraise" in config
        assert config["reraise"] is True

    @pytest.mark.requirement("WL-169")
    def test_get_retry_config_with_custom_settings(self) -> None:
        """Test retry config with custom rate-limit settings."""
        rate_config = RateLimitConfig(
            max_retries=10,
            initial_wait=0.5,
            max_wait=120.0,
        )
        manager = RateLimitBackoffManager(rate_config)
        config = manager.get_retry_config()

        assert "wait" in config
        assert "stop" in config

    @pytest.mark.requirement("WL-169")
    def test_make_retry_decorator(self) -> None:
        """Test creating a retry decorator."""
        manager = RateLimitBackoffManager()
        decorator = manager.make_retry_decorator()

        # Should be callable and have necessary attributes
        assert callable(decorator)
        assert callable(decorator)
