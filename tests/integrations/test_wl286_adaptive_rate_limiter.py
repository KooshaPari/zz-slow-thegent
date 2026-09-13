"""Tests for thegent.integrations.adaptive_rate_limiter — Adaptive rate limiter.

@trace WL-286
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from thegent.integrations.adaptive_rate_limiter import (
    AdaptiveRateLimiter,
    RateLimitState,
)


class TestRateLimitState:
    """Test RateLimitState dataclass."""

    @pytest.mark.requirement("WL-286")
    def test_rate_limit_state_creation(self) -> None:
        """Can create a RateLimitState with required fields."""
        updated = datetime.now(UTC)
        state = RateLimitState(
            connector="github",
            requests_per_minute=60.0,
            last_updated=updated,
        )

        assert state.connector == "github"
        assert state.requests_per_minute == 60.0
        assert state.last_updated == updated


class TestAdaptiveRateLimiterInit:
    """Test AdaptiveRateLimiter initialization. @trace WL-286"""

    @pytest.mark.requirement("WL-286")
    def test_init_with_default(self) -> None:
        """AdaptiveRateLimiter initializes with default rpm."""
        limiter = AdaptiveRateLimiter()
        assert limiter._default_rpm == 60.0

    @pytest.mark.requirement("WL-286")
    def test_init_with_custom_default(self) -> None:
        """AdaptiveRateLimiter accepts custom default rpm."""
        limiter = AdaptiveRateLimiter(default_rpm=120.0)
        assert limiter._default_rpm == 120.0

    @pytest.mark.requirement("WL-286")
    def test_init_invalid_default_raises_error(self) -> None:
        """AdaptiveRateLimiter raises ValueError for invalid default."""
        with pytest.raises(ValueError, match=r"default_rpm must be >= 1.0"):
            AdaptiveRateLimiter(default_rpm=0.5)


class TestAdaptiveRateLimiterSetLimit:
    """Test AdaptiveRateLimiter.set_limit operations. @trace WL-286"""

    @pytest.fixture
    def limiter(self) -> AdaptiveRateLimiter:
        """Provide an AdaptiveRateLimiter instance."""
        return AdaptiveRateLimiter()

    @pytest.mark.requirement("WL-286")
    def test_set_limit(self, limiter: AdaptiveRateLimiter) -> None:
        """set_limit sets explicit limit for connector."""
        limiter.set_limit("github", 120.0)
        assert limiter.get_limit("github") == 120.0

    @pytest.mark.requirement("WL-286")
    def test_set_limit_overrides_default(self, limiter: AdaptiveRateLimiter) -> None:
        """set_limit overrides default for connector."""
        limiter.set_limit("github", 200.0)
        assert limiter.get_limit("github") == 200.0

    @pytest.mark.requirement("WL-286")
    def test_set_limit_invalid_raises_error(self, limiter: AdaptiveRateLimiter) -> None:
        """set_limit raises ValueError for rpm < 1.0."""
        with pytest.raises(ValueError, match=r"rpm must be >= 1.0"):
            limiter.set_limit("github", 0.5)

    @pytest.mark.requirement("WL-286")
    def test_set_limit_updates_last_updated(self, limiter: AdaptiveRateLimiter) -> None:
        """set_limit updates last_updated timestamp."""
        before = datetime.now(UTC)
        limiter.set_limit("github", 120.0)
        after = datetime.now(UTC)

        state = limiter.get_state("github")
        assert before <= state.last_updated <= after

    @pytest.mark.requirement("WL-286")
    def test_set_limit_minimum_value(self, limiter: AdaptiveRateLimiter) -> None:
        """set_limit accepts minimum value of 1.0."""
        limiter.set_limit("github", 1.0)
        assert limiter.get_limit("github") == 1.0


class TestAdaptiveRateLimiterGetLimit:
    """Test AdaptiveRateLimiter.get_limit operations. @trace WL-286"""

    @pytest.fixture
    def limiter(self) -> AdaptiveRateLimiter:
        """Provide an AdaptiveRateLimiter instance."""
        return AdaptiveRateLimiter(default_rpm=60.0)

    @pytest.mark.requirement("WL-286")
    def test_get_limit_default_for_unset(self, limiter: AdaptiveRateLimiter) -> None:
        """get_limit returns default for unset connector."""
        limit = limiter.get_limit("unknown")
        assert limit == 60.0

    @pytest.mark.requirement("WL-286")
    def test_get_limit_explicit_value(self, limiter: AdaptiveRateLimiter) -> None:
        """get_limit returns explicit value for set connector."""
        limiter.set_limit("github", 120.0)
        assert limiter.get_limit("github") == 120.0

    @pytest.mark.requirement("WL-286")
    def test_get_limit_multiple_connectors(self, limiter: AdaptiveRateLimiter) -> None:
        """get_limit returns correct value for each connector."""
        limiter.set_limit("github", 100.0)
        limiter.set_limit("linear", 200.0)

        assert limiter.get_limit("github") == 100.0
        assert limiter.get_limit("linear") == 200.0
        assert limiter.get_limit("unknown") == 60.0


class TestAdaptiveRateLimiterRecordThrottle:
    """Test AdaptiveRateLimiter.record_throttle operations. @trace WL-286"""

    @pytest.fixture
    def limiter(self) -> AdaptiveRateLimiter:
        """Provide an AdaptiveRateLimiter instance."""
        return AdaptiveRateLimiter(default_rpm=100.0)

    @pytest.mark.requirement("WL-286")
    def test_record_throttle_reduces_by_twenty_percent(self, limiter: AdaptiveRateLimiter) -> None:
        """record_throttle reduces limit by 20%."""
        limiter.set_limit("github", 100.0)
        limiter.record_throttle("github")

        assert limiter.get_limit("github") == 80.0

    @pytest.mark.requirement("WL-286")
    def test_record_throttle_multiple_times(self, limiter: AdaptiveRateLimiter) -> None:
        """record_throttle can be called multiple times."""
        limiter.set_limit("github", 100.0)
        limiter.record_throttle("github")
        limiter.record_throttle("github")

        # 100 * 0.8 * 0.8 = 64
        assert abs(limiter.get_limit("github") - 64.0) < 0.01

    @pytest.mark.requirement("WL-286")
    def test_record_throttle_respects_minimum(self, limiter: AdaptiveRateLimiter) -> None:
        """record_throttle never goes below 1.0."""
        limiter.set_limit("github", 1.5)
        limiter.record_throttle("github")

        # 1.5 * 0.8 = 1.2, which is still > 1.0
        assert abs(limiter.get_limit("github") - 1.2) < 0.01

    @pytest.mark.requirement("WL-286")
    def test_record_throttle_at_minimum_stays_at_minimum(self, limiter: AdaptiveRateLimiter) -> None:
        """record_throttle on minimum stays at 1.0."""
        limiter.set_limit("github", 1.0)
        limiter.record_throttle("github")

        assert limiter.get_limit("github") == 1.0

    @pytest.mark.requirement("WL-286")
    def test_record_throttle_uses_default_if_unset(self, limiter: AdaptiveRateLimiter) -> None:
        """record_throttle uses default limit if connector not set."""
        limiter.record_throttle("unknown")

        # 100 * 0.8 = 80
        assert limiter.get_limit("unknown") == 80.0

    @pytest.mark.requirement("WL-286")
    def test_record_throttle_updates_timestamp(self, limiter: AdaptiveRateLimiter) -> None:
        """record_throttle updates last_updated timestamp."""
        limiter.set_limit("github", 100.0)
        limiter.record_throttle("github")

        state = limiter.get_state("github")
        assert state.last_updated is not None


class TestAdaptiveRateLimiterRecordSuccess:
    """Test AdaptiveRateLimiter.record_success operations. @trace WL-286"""

    @pytest.fixture
    def limiter(self) -> AdaptiveRateLimiter:
        """Provide an AdaptiveRateLimiter instance."""
        return AdaptiveRateLimiter(default_rpm=100.0)

    @pytest.mark.requirement("WL-286")
    def test_record_success_increases_by_five_percent(self, limiter: AdaptiveRateLimiter) -> None:
        """record_success increases limit by 5%."""
        limiter.set_limit("github", 100.0)
        limiter.record_success("github")

        assert limiter.get_limit("github") == 105.0

    @pytest.mark.requirement("WL-286")
    def test_record_success_multiple_times(self, limiter: AdaptiveRateLimiter) -> None:
        """record_success can be called multiple times."""
        limiter.set_limit("github", 100.0)
        limiter.record_success("github")
        limiter.record_success("github")

        # 100 * 1.05 * 1.05 = 110.25
        assert abs(limiter.get_limit("github") - 110.25) < 0.01

    @pytest.mark.requirement("WL-286")
    def test_record_success_respects_maximum(self, limiter: AdaptiveRateLimiter) -> None:
        """record_success never exceeds 10x default."""
        limiter.set_limit("github", 950.0)
        limiter.record_success("github")

        # 950 * 1.05 = 997.5, which is still < 1000
        assert abs(limiter.get_limit("github") - 997.5) < 0.01

    @pytest.mark.requirement("WL-286")
    def test_record_success_at_maximum_stays_at_maximum(self, limiter: AdaptiveRateLimiter) -> None:
        """record_success at max stays at max."""
        limiter.set_limit("github", 1000.0)
        limiter.record_success("github")

        assert limiter.get_limit("github") == 1000.0

    @pytest.mark.requirement("WL-286")
    def test_record_success_uses_default_if_unset(self, limiter: AdaptiveRateLimiter) -> None:
        """record_success uses default if connector not set."""
        limiter.record_success("unknown")

        # 100 * 1.05 = 105
        assert limiter.get_limit("unknown") == 105.0

    @pytest.mark.requirement("WL-286")
    def test_record_success_updates_timestamp(self, limiter: AdaptiveRateLimiter) -> None:
        """record_success updates last_updated timestamp."""
        limiter.set_limit("github", 100.0)
        limiter.record_success("github")

        state = limiter.get_state("github")
        assert state.last_updated is not None


class TestAdaptiveRateLimiterGetState:
    """Test AdaptiveRateLimiter.get_state operations. @trace WL-286"""

    @pytest.fixture
    def limiter(self) -> AdaptiveRateLimiter:
        """Provide an AdaptiveRateLimiter instance."""
        return AdaptiveRateLimiter(default_rpm=60.0)

    @pytest.mark.requirement("WL-286")
    def test_get_state_unset_connector(self, limiter: AdaptiveRateLimiter) -> None:
        """get_state returns state with default for unset connector."""
        state = limiter.get_state("github")

        assert state.connector == "github"
        assert state.requests_per_minute == 60.0

    @pytest.mark.requirement("WL-286")
    def test_get_state_explicit_limit(self, limiter: AdaptiveRateLimiter) -> None:
        """get_state returns state with explicit limit."""
        limiter.set_limit("github", 120.0)
        state = limiter.get_state("github")

        assert state.connector == "github"
        assert state.requests_per_minute == 120.0

    @pytest.mark.requirement("WL-286")
    def test_get_state_after_throttle(self, limiter: AdaptiveRateLimiter) -> None:
        """get_state reflects throttle changes."""
        limiter.set_limit("github", 100.0)
        limiter.record_throttle("github")
        state = limiter.get_state("github")

        assert state.requests_per_minute == 80.0

    @pytest.mark.requirement("WL-286")
    def test_get_state_after_success(self, limiter: AdaptiveRateLimiter) -> None:
        """get_state reflects success changes."""
        limiter.set_limit("github", 100.0)
        limiter.record_success("github")
        state = limiter.get_state("github")

        assert state.requests_per_minute == 105.0

    @pytest.mark.requirement("WL-286")
    def test_get_state_multiple_connectors(self, limiter: AdaptiveRateLimiter) -> None:
        """get_state returns independent state for each connector."""
        limiter.set_limit("github", 100.0)
        limiter.set_limit("linear", 200.0)

        state_github = limiter.get_state("github")
        state_linear = limiter.get_state("linear")

        assert state_github.requests_per_minute == 100.0
        assert state_linear.requests_per_minute == 200.0

    @pytest.mark.requirement("WL-286")
    def test_adaptive_flow(self, limiter: AdaptiveRateLimiter) -> None:
        """Adaptive rate limiter adjusts limits based on events."""
        # Start at default
        assert limiter.get_limit("github") == 60.0

        # Success increases it
        limiter.record_success("github")
        assert abs(limiter.get_limit("github") - 63.0) < 0.01

        # Throttle decreases it
        limiter.record_throttle("github")
        assert abs(limiter.get_limit("github") - 50.4) < 0.01

        # Multiple successes ramp it up
        for _ in range(5):
            limiter.record_success("github")

        limit = limiter.get_limit("github")
        assert limit > 50.4  # Should have increased

    @pytest.mark.requirement("WL-286")
    def test_independent_connectors(self, limiter: AdaptiveRateLimiter) -> None:
        """Different connectors maintain independent limits."""
        limiter.set_limit("github", 100.0)
        limiter.set_limit("linear", 100.0)

        limiter.record_throttle("github")
        limiter.record_success("linear")

        assert limiter.get_limit("github") == 80.0
        assert limiter.get_limit("linear") == 105.0
