"""Tests for GW-19: Sliding window rate limiter.

All tests tagged with @pytest.mark.requirement("FR-ROUTE-019").
"""

import threading
import time

import pytest

from thegent.utils.routing_impl.rate_limiter import (
    MultiKeyRateLimiter,
    RateLimitConfig,
    SlidingWindowRateLimiter,
    get_rate_limiter,
    make_provider_config,
    make_user_config,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _config(limit: int, window: float = 1.0, key: str = "test") -> RateLimitConfig:
    return RateLimitConfig(requests_per_window=limit, window_seconds=window, key=key)


# ---------------------------------------------------------------------------
# SlidingWindowRateLimiter tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ROUTE-019")
def test_allows_within_limit():
    """N requests within the limit must all be allowed."""
    limiter = SlidingWindowRateLimiter()
    cfg = _config(limit=5, key="allow-within")
    for i in range(5):
        result = limiter.allow(cfg)
        assert result.allowed, f"Request {i + 1} should be allowed"
    assert result.remaining == 0


@pytest.mark.requirement("FR-ROUTE-019")
def test_blocks_over_limit():
    """The (N+1)th request must be blocked."""
    limiter = SlidingWindowRateLimiter()
    cfg = _config(limit=3, key="block-over")
    for _ in range(3):
        limiter.allow(cfg)
    result = limiter.allow(cfg)
    assert not result.allowed
    assert result.remaining == 0


@pytest.mark.requirement("FR-ROUTE-019")
def test_sliding_window_allows_after_expiry():
    """After the window passes, old requests no longer count."""
    limiter = SlidingWindowRateLimiter()
    cfg = _config(limit=2, window=0.1, key="expiry")
    # Fill the window
    limiter.allow(cfg)
    limiter.allow(cfg)
    # Verify blocked
    assert not limiter.allow(cfg).allowed
    # Wait for window to expire
    time.sleep(0.15)
    # Now should be allowed again
    result = limiter.allow(cfg)
    assert result.allowed


@pytest.mark.requirement("FR-ROUTE-019")
def test_check_does_not_consume_slot():
    """check() must not consume a slot regardless of how many times called."""
    limiter = SlidingWindowRateLimiter()
    cfg = _config(limit=2, key="check-no-consume")
    for _ in range(10):
        result = limiter.check(cfg)
        assert result.allowed
    # After many checks, two allow() calls must still pass
    assert limiter.allow(cfg).allowed
    assert limiter.allow(cfg).allowed
    # Third allow() is over the limit
    assert not limiter.allow(cfg).allowed


@pytest.mark.requirement("FR-ROUTE-019")
def test_allow_consumes_slot():
    """allow() must consume a slot and decrement remaining."""
    limiter = SlidingWindowRateLimiter()
    cfg = _config(limit=3, key="consumes")
    r1 = limiter.allow(cfg)
    assert r1.allowed
    assert r1.remaining == 2
    r2 = limiter.allow(cfg)
    assert r2.remaining == 1
    r3 = limiter.allow(cfg)
    assert r3.remaining == 0
    assert limiter.get_current_count("consumes", 1.0) == 3


@pytest.mark.requirement("FR-ROUTE-019")
def test_reset_clears_count():
    """After reset(), all requests should be allowed again up to the limit."""
    limiter = SlidingWindowRateLimiter()
    cfg = _config(limit=2, key="reset-key")
    limiter.allow(cfg)
    limiter.allow(cfg)
    assert not limiter.allow(cfg).allowed
    limiter.reset("reset-key")
    assert limiter.allow(cfg).allowed
    assert limiter.allow(cfg).allowed


@pytest.mark.requirement("FR-ROUTE-019")
def test_get_current_count_reflects_window():
    """get_current_count returns requests within the active window."""
    limiter = SlidingWindowRateLimiter()
    cfg = _config(limit=10, window=0.1, key="count-key")
    limiter.allow(cfg)
    limiter.allow(cfg)
    assert limiter.get_current_count("count-key", 0.1) == 2
    time.sleep(0.15)
    assert limiter.get_current_count("count-key", 0.1) == 0


# ---------------------------------------------------------------------------
# MultiKeyRateLimiter tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ROUTE-019")
def test_multi_key_allows_when_all_pass():
    """allow_all passes when every limit allows the request."""
    limiter = SlidingWindowRateLimiter()
    multi = MultiKeyRateLimiter(limiter)
    configs = [
        _config(limit=5, key="mk-user"),
        _config(limit=10, key="mk-provider"),
    ]
    allowed, results = multi.allow_all(configs)
    assert allowed
    assert all(r.allowed for r in results)


@pytest.mark.requirement("FR-ROUTE-019")
def test_multi_key_blocks_when_any_fails():
    """allow_all blocks when at least one limit is exceeded."""
    limiter = SlidingWindowRateLimiter()
    multi = MultiKeyRateLimiter(limiter)

    tight_cfg = _config(limit=1, key="mk-tight")
    loose_cfg = _config(limit=10, key="mk-loose")

    # Exhaust the tight limit
    limiter.allow(tight_cfg)

    allowed, _ = multi.allow_all([tight_cfg, loose_cfg])
    assert not allowed


@pytest.mark.requirement("FR-ROUTE-019")
def test_multi_key_atomic_no_partial_consumption():
    """When one limit fails, no other limits are consumed."""
    limiter = SlidingWindowRateLimiter()
    multi = MultiKeyRateLimiter(limiter)

    passing_cfg = _config(limit=5, key="mk-atomic-pass")
    failing_cfg = _config(limit=1, key="mk-atomic-fail")

    # Exhaust the failing limit
    limiter.allow(failing_cfg)

    count_before = limiter.get_current_count("mk-atomic-pass", 1.0)
    allowed, _ = multi.allow_all([passing_cfg, failing_cfg])

    assert not allowed
    count_after = limiter.get_current_count("mk-atomic-pass", 1.0)
    assert count_after == count_before, "passing limit must not be consumed when another limit fails"


@pytest.mark.requirement("FR-ROUTE-019")
def test_concurrent_allows_respect_limit():
    """Thread-safety: concurrent allow() calls must not exceed the limit."""
    limiter = SlidingWindowRateLimiter()
    cfg = _config(limit=50, window=5.0, key="concurrent")
    results: list[bool] = []
    lock = threading.Lock()

    def worker():
        for _ in range(10):
            r = limiter.allow(cfg)
            with lock:
                results.append(r.allowed)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    allowed_count = sum(1 for r in results if r)
    assert allowed_count == 50, f"Exactly 50 requests should be allowed, got {allowed_count}"


# ---------------------------------------------------------------------------
# Convenience constructor tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ROUTE-019")
def test_make_provider_config():
    """make_provider_config builds a per-minute provider config."""
    cfg = make_provider_config("openai", 100)
    assert cfg.key == "provider:openai"
    assert cfg.requests_per_window == 100
    assert cfg.window_seconds == 60.0


@pytest.mark.requirement("FR-ROUTE-019")
def test_make_user_config():
    """make_user_config builds a per-minute user config."""
    cfg = make_user_config("alice", 20)
    assert cfg.key == "user:alice"
    assert cfg.requests_per_window == 20
    assert cfg.window_seconds == 60.0


@pytest.mark.requirement("FR-ROUTE-019")
def test_get_rate_limiter_singleton():
    """get_rate_limiter() returns the same instance on repeated calls."""
    a = get_rate_limiter()
    b = get_rate_limiter()
    assert a is b
