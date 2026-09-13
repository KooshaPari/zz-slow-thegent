"""Tests for token bucket rate limiting (swarm-token-bucket).

@trace FR-ORC-TB-001 -- TokenBucketConfig: capacity/refill_rate/initial_tokens validation.
@trace FR-ORC-TB-002 -- TokenBucket.consume: non-blocking consumption.
@trace FR-ORC-TB-003 -- TokenBucket exhaustion: returns False when insufficient tokens.
@trace FR-ORC-TB-004 -- TokenBucket.refill: time-based and manual refill.
@trace FR-ORC-TB-005 -- TokenBucket.consume_blocking: blocks until tokens available.
@trace FR-ORC-TB-006 -- TokenBucket.consume_blocking: timeout returns False.
@trace FR-ORC-TB-007 -- TokenBucket.try_consume: returns (success, wait_time_s).
@trace FR-ORC-TB-008 -- TokenBucket.available: reflects current token count.
@trace FR-ORC-TB-009 -- Thread safety: concurrent consumers do not over-consume.
@trace FR-ORC-TB-010 -- RateLimitedSwarmRunner: wraps callable with token gating.
@trace FR-ORC-TB-011 -- RateLimitedSwarmRunner.configure_from_env: env var config.
"""

from __future__ import annotations

import os
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from thegent.orchestration.resource.token_bucket import (
    RateLimitedSwarmRunner,
    TokenBucket,
    TokenBucketConfig,
)

# ---------------------------------------------------------------------------
# TokenBucketConfig tests
# ---------------------------------------------------------------------------


class TestTokenBucketConfig:
    """Unit tests for TokenBucketConfig validation. @trace FR-ORC-TB-001"""

    def test_valid_config(self) -> None:  # @trace FR-ORC-TB-001
        cfg = TokenBucketConfig(capacity=10.0, refill_rate=2.0)
        assert cfg.capacity == 10.0
        assert cfg.refill_rate == 2.0
        assert cfg.initial_tokens is None

    def test_initial_tokens_set(self) -> None:  # @trace FR-ORC-TB-001
        cfg = TokenBucketConfig(capacity=10.0, refill_rate=2.0, initial_tokens=5.0)
        assert cfg.initial_tokens == 5.0

    def test_zero_capacity_raises(self) -> None:  # @trace FR-ORC-TB-001
        with pytest.raises(ValueError, match="capacity must be > 0"):
            TokenBucketConfig(capacity=0.0, refill_rate=1.0)

    def test_negative_capacity_raises(self) -> None:  # @trace FR-ORC-TB-001
        with pytest.raises(ValueError, match="capacity must be > 0"):
            TokenBucketConfig(capacity=-5.0, refill_rate=1.0)

    def test_negative_refill_rate_raises(self) -> None:  # @trace FR-ORC-TB-001
        with pytest.raises(ValueError, match="refill_rate must be >= 0"):
            TokenBucketConfig(capacity=10.0, refill_rate=-1.0)

    def test_zero_refill_rate_allowed(self) -> None:  # @trace FR-ORC-TB-001
        cfg = TokenBucketConfig(capacity=10.0, refill_rate=0.0)
        assert cfg.refill_rate == 0.0

    def test_negative_initial_tokens_raises(self) -> None:  # @trace FR-ORC-TB-001
        with pytest.raises(ValueError, match="initial_tokens must be >= 0"):
            TokenBucketConfig(capacity=10.0, refill_rate=1.0, initial_tokens=-1.0)


# ---------------------------------------------------------------------------
# TokenBucket.available tests
# ---------------------------------------------------------------------------


class TestTokenBucketAvailable:
    """Tests for available(). @trace FR-ORC-TB-008"""

    def test_initial_available_equals_capacity(self) -> None:  # @trace FR-ORC-TB-008
        bucket = TokenBucket(TokenBucketConfig(capacity=10.0, refill_rate=1.0))
        assert bucket.available() == pytest.approx(10.0, abs=0.01)

    def test_initial_tokens_override(self) -> None:  # @trace FR-ORC-TB-008
        bucket = TokenBucket(
            TokenBucketConfig(capacity=10.0, refill_rate=1.0, initial_tokens=3.0)
        )
        assert bucket.available() == pytest.approx(3.0, abs=0.01)

    def test_available_decreases_after_consume(self) -> None:  # @trace FR-ORC-TB-008
        bucket = TokenBucket(TokenBucketConfig(capacity=10.0, refill_rate=0.0))
        bucket.consume(3.0)
        assert bucket.available() == pytest.approx(7.0, abs=0.01)


# ---------------------------------------------------------------------------
# TokenBucket.consume tests
# ---------------------------------------------------------------------------


class TestTokenBucketConsume:
    """Tests for non-blocking consume(). @trace FR-ORC-TB-002, FR-ORC-TB-003"""

    def test_successful_consume(self) -> None:  # @trace FR-ORC-TB-002
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=0.0))
        assert bucket.consume(1.0) is True

    def test_consume_fractional(self) -> None:  # @trace FR-ORC-TB-002
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=0.0))
        assert bucket.consume(0.5) is True
        assert bucket.available() == pytest.approx(4.5, abs=0.01)

    def test_exhausted_bucket_returns_false(self) -> None:  # @trace FR-ORC-TB-003
        bucket = TokenBucket(
            TokenBucketConfig(capacity=2.0, refill_rate=0.0, initial_tokens=0.0)
        )
        assert bucket.consume(1.0) is False

    def test_partial_exhaustion_then_failure(self) -> None:  # @trace FR-ORC-TB-003
        bucket = TokenBucket(TokenBucketConfig(capacity=2.0, refill_rate=0.0))
        assert bucket.consume(2.0) is True
        assert bucket.consume(1.0) is False

    def test_consume_invalid_zero_raises(self) -> None:  # @trace FR-ORC-TB-002
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=1.0))
        with pytest.raises(ValueError, match="tokens must be > 0"):
            bucket.consume(0.0)

    def test_consume_invalid_negative_raises(self) -> None:  # @trace FR-ORC-TB-002
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=1.0))
        with pytest.raises(ValueError, match="tokens must be > 0"):
            bucket.consume(-1.0)


# ---------------------------------------------------------------------------
# TokenBucket.refill tests
# ---------------------------------------------------------------------------


class TestTokenBucketRefill:
    """Tests for manual and time-based refill. @trace FR-ORC-TB-004"""

    def test_manual_refill_adds_tokens(self) -> None:  # @trace FR-ORC-TB-004
        bucket = TokenBucket(
            TokenBucketConfig(capacity=10.0, refill_rate=0.0, initial_tokens=0.0)
        )
        bucket.refill(5.0)
        assert bucket.available() == pytest.approx(5.0, abs=0.01)

    def test_manual_refill_capped_at_capacity(self) -> None:  # @trace FR-ORC-TB-004
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=0.0))
        bucket.refill(100.0)
        assert bucket.available() == pytest.approx(5.0, abs=0.01)

    def test_manual_refill_negative_raises(self) -> None:  # @trace FR-ORC-TB-004
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=0.0))
        with pytest.raises(ValueError, match="tokens must be >= 0"):
            bucket.refill(-1.0)

    def test_time_based_refill_via_none(self) -> None:  # @trace FR-ORC-TB-004
        """Calling refill(None) applies time-based refill."""
        bucket = TokenBucket(
            TokenBucketConfig(capacity=10.0, refill_rate=100.0, initial_tokens=0.0)
        )
        time.sleep(0.05)  # 50 ms -> ~5 tokens at 100/s
        bucket.refill()  # explicit time-based refill
        assert bucket.available() > 0.0

    def test_time_based_refill_auto_on_consume(self) -> None:  # @trace FR-ORC-TB-004
        """consume() applies time-based refill before checking availability."""
        bucket = TokenBucket(
            TokenBucketConfig(capacity=5.0, refill_rate=100.0, initial_tokens=0.0)
        )
        time.sleep(0.06)  # ~6 tokens generated; capped at 5
        assert bucket.consume(1.0) is True


# ---------------------------------------------------------------------------
# TokenBucket.try_consume tests
# ---------------------------------------------------------------------------


class TestTokenBucketTryConsume:
    """Tests for try_consume(). @trace FR-ORC-TB-007"""

    def test_try_consume_success(self) -> None:  # @trace FR-ORC-TB-007
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=0.0))
        success, wait = bucket.try_consume(1.0)
        assert success is True
        assert wait == 0.0

    def test_try_consume_failure_returns_wait_time(
        self,
    ) -> None:  # @trace FR-ORC-TB-007
        bucket = TokenBucket(
            TokenBucketConfig(capacity=10.0, refill_rate=2.0, initial_tokens=0.0)
        )
        success, wait = bucket.try_consume(4.0)
        assert success is False
        assert wait == pytest.approx(2.0, abs=0.01)  # 4 tokens / 2 per sec

    def test_try_consume_no_refill_wait_zero(self) -> None:  # @trace FR-ORC-TB-007
        """When refill_rate=0, wait_time is 0.0 (bucket won't auto-refill)."""
        bucket = TokenBucket(
            TokenBucketConfig(capacity=5.0, refill_rate=0.0, initial_tokens=0.0)
        )
        success, wait = bucket.try_consume(1.0)
        assert success is False
        assert wait == 0.0

    def test_try_consume_invalid_zero_raises(self) -> None:  # @trace FR-ORC-TB-007
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=1.0))
        with pytest.raises(ValueError, match="tokens must be > 0"):
            bucket.try_consume(0.0)


# ---------------------------------------------------------------------------
# TokenBucket.consume_blocking tests
# ---------------------------------------------------------------------------


class TestTokenBucketConsumeBlocking:
    """Tests for blocking consume with timeout. @trace FR-ORC-TB-005, FR-ORC-TB-006"""

    def test_blocking_consume_immediate_success(self) -> None:  # @trace FR-ORC-TB-005
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=0.0))
        assert bucket.consume_blocking(1.0) is True

    def test_blocking_consume_waits_for_refill(self) -> None:  # @trace FR-ORC-TB-005
        """Blocking consume waits until refill provides enough tokens."""
        bucket = TokenBucket(
            TokenBucketConfig(capacity=5.0, refill_rate=50.0, initial_tokens=0.0)
        )
        start = time.monotonic()
        result = bucket.consume_blocking(tokens=1.0, timeout_s=1.0)
        elapsed = time.monotonic() - start
        assert result is True
        assert elapsed < 1.0  # should have been fast

    def test_blocking_consume_timeout_returns_false(
        self,
    ) -> None:  # @trace FR-ORC-TB-006
        bucket = TokenBucket(
            TokenBucketConfig(capacity=5.0, refill_rate=0.0, initial_tokens=0.0)
        )
        start = time.monotonic()
        result = bucket.consume_blocking(tokens=1.0, timeout_s=0.1)
        elapsed = time.monotonic() - start
        assert result is False
        assert elapsed >= 0.08  # waited approx the timeout

    def test_blocking_consume_zero_timeout_no_tokens(
        self,
    ) -> None:  # @trace FR-ORC-TB-006
        bucket = TokenBucket(
            TokenBucketConfig(capacity=5.0, refill_rate=0.0, initial_tokens=0.0)
        )
        assert bucket.consume_blocking(tokens=1.0, timeout_s=0.0) is False

    def test_blocking_consume_zero_timeout_has_tokens(
        self,
    ) -> None:  # @trace FR-ORC-TB-005
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=0.0))
        assert bucket.consume_blocking(tokens=1.0, timeout_s=0.0) is True

    def test_blocking_consume_exceeds_capacity_fails(
        self,
    ) -> None:  # @trace FR-ORC-TB-006
        """Requesting more tokens than capacity can never succeed."""
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=100.0))
        assert bucket.consume_blocking(tokens=10.0, timeout_s=0.5) is False

    def test_blocking_consume_negative_tokens_raises(
        self,
    ) -> None:  # @trace FR-ORC-TB-005
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=1.0))
        with pytest.raises(ValueError, match="tokens must be > 0"):
            bucket.consume_blocking(tokens=-1.0)

    def test_blocking_consume_negative_timeout_raises(
        self,
    ) -> None:  # @trace FR-ORC-TB-006
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=1.0))
        with pytest.raises(ValueError, match="timeout_s must be >= 0"):
            bucket.consume_blocking(tokens=1.0, timeout_s=-1.0)

    def test_blocking_consume_wakes_on_manual_refill(
        self,
    ) -> None:  # @trace FR-ORC-TB-005
        """A blocking consumer unblocks when another thread manually refills."""
        bucket = TokenBucket(
            TokenBucketConfig(capacity=5.0, refill_rate=0.0, initial_tokens=0.0)
        )
        results: list[bool] = []

        def consumer() -> None:
            results.append(bucket.consume_blocking(tokens=1.0, timeout_s=2.0))

        t = threading.Thread(target=consumer)
        t.start()
        time.sleep(0.05)  # let consumer block
        bucket.refill(2.0)
        t.join(timeout=1.0)
        assert results == [True]


# ---------------------------------------------------------------------------
# Thread safety tests
# ---------------------------------------------------------------------------


class TestTokenBucketThreadSafety:
    """Thread safety: concurrent consumers never over-consume. @trace FR-ORC-TB-009"""

    def test_concurrent_consume_no_overdraft(self) -> None:  # @trace FR-ORC-TB-009
        capacity = 10.0
        bucket = TokenBucket(TokenBucketConfig(capacity=capacity, refill_rate=0.0))
        successes: list[bool] = []
        lock = threading.Lock()

        def worker() -> None:
            result = bucket.consume(1.0)
            with lock:
                successes.append(result)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total_consumed = sum(1 for s in successes if s)
        # No more than capacity tokens should have been consumed.
        assert total_consumed <= int(capacity)
        # Remaining tokens should be non-negative.
        assert bucket.available() >= 0.0

    def test_concurrent_blocking_consume(self) -> None:  # @trace FR-ORC-TB-009
        """Multiple threads block and each eventually consumes exactly one token."""
        n_threads = 5
        capacity = 2.0
        bucket = TokenBucket(
            TokenBucketConfig(capacity=capacity, refill_rate=100.0, initial_tokens=0.0)
        )
        results: list[bool] = []
        lock = threading.Lock()

        def worker() -> None:
            ok = bucket.consume_blocking(tokens=1.0, timeout_s=1.0)
            with lock:
                results.append(ok)

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=2.0)

        assert len(results) == n_threads
        assert all(results), "All threads should have eventually acquired a token"


# ---------------------------------------------------------------------------
# RateLimitedSwarmRunner tests
# ---------------------------------------------------------------------------


class TestRateLimitedSwarmRunner:
    """Tests for RateLimitedSwarmRunner. @trace FR-ORC-TB-010"""

    def test_run_calls_function_and_returns_value(self) -> None:  # @trace FR-ORC-TB-010
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=0.0))
        runner = RateLimitedSwarmRunner(bucket=bucket)
        fn = MagicMock(return_value=42)
        result = runner.run(fn, "arg1", kw="val")
        fn.assert_called_once_with("arg1", kw="val")
        assert result == 42

    def test_run_consumes_one_token(self) -> None:  # @trace FR-ORC-TB-010
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=0.0))
        runner = RateLimitedSwarmRunner(bucket=bucket)
        runner.run(lambda: None)
        assert bucket.available() == pytest.approx(4.0, abs=0.01)

    def test_run_raises_timeout_error_when_exhausted(
        self,
    ) -> None:  # @trace FR-ORC-TB-010
        bucket = TokenBucket(
            TokenBucketConfig(capacity=1.0, refill_rate=0.0, initial_tokens=0.0)
        )
        runner = RateLimitedSwarmRunner(bucket=bucket, default_timeout_s=0.05)
        with pytest.raises(TimeoutError, match="Rate limit exceeded"):
            runner.run(lambda: None)

    def test_run_without_bucket_raises_runtime_error(
        self,
    ) -> None:  # @trace FR-ORC-TB-010
        runner = RateLimitedSwarmRunner()
        with pytest.raises(RuntimeError, match="no bucket configured"):
            runner.run(lambda: None)

    def test_run_timeout_override(self) -> None:  # @trace FR-ORC-TB-010
        """Explicit timeout_s=None means wait indefinitely (should succeed with tokens)."""
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=0.0))
        runner = RateLimitedSwarmRunner(bucket=bucket, default_timeout_s=0.0)
        # default is 0 but overriding with None; bucket has tokens so no wait needed
        result = runner.run(lambda: "ok", timeout_s=None)
        assert result == "ok"

    def test_run_forwards_args_and_kwargs(self) -> None:  # @trace FR-ORC-TB-010
        bucket = TokenBucket(TokenBucketConfig(capacity=5.0, refill_rate=0.0))
        runner = RateLimitedSwarmRunner(bucket=bucket)
        captured: dict = {}

        def fn(*args: object, **kwargs: object) -> None:
            captured["args"] = args
            captured["kwargs"] = kwargs

        runner.run(fn, 1, 2, x=3)
        assert captured["args"] == (1, 2)
        assert captured["kwargs"] == {"x": 3}


# ---------------------------------------------------------------------------
# RateLimitedSwarmRunner.configure_from_env tests
# ---------------------------------------------------------------------------


class TestRateLimitedSwarmRunnerEnvConfig:
    """Tests for configure_from_env(). @trace FR-ORC-TB-011"""

    def test_configure_from_env_defaults(self) -> None:  # @trace FR-ORC-TB-011
        runner = RateLimitedSwarmRunner()
        env = dict(os.environ.items())
        env.pop("THGENT_RATE_TOKENS_PER_SEC", None)
        env.pop("THGENT_RATE_BUCKET_SIZE", None)
        with patch.dict(os.environ, env, clear=True):
            runner.configure_from_env()
        assert runner._bucket is not None
        assert runner._bucket._config.refill_rate == pytest.approx(10.0)
        assert runner._bucket._config.capacity == pytest.approx(20.0)

    def test_configure_from_env_custom_values(self) -> None:  # @trace FR-ORC-TB-011
        runner = RateLimitedSwarmRunner()
        with patch.dict(
            os.environ,
            {
                "THGENT_RATE_TOKENS_PER_SEC": "5.0",
                "THGENT_RATE_BUCKET_SIZE": "50.0",
            },
        ):
            runner.configure_from_env()
        assert runner._bucket is not None
        assert runner._bucket._config.refill_rate == pytest.approx(5.0)
        assert runner._bucket._config.capacity == pytest.approx(50.0)

    def test_configure_from_env_returns_self(self) -> None:  # @trace FR-ORC-TB-011
        runner = RateLimitedSwarmRunner()
        result = runner.configure_from_env()
        assert result is runner

    def test_configure_from_env_enables_run(self) -> None:  # @trace FR-ORC-TB-011
        runner = RateLimitedSwarmRunner(default_timeout_s=1.0)
        with patch.dict(
            os.environ,
            {
                "THGENT_RATE_TOKENS_PER_SEC": "100.0",
                "THGENT_RATE_BUCKET_SIZE": "10.0",
            },
        ):
            runner.configure_from_env()
        result = runner.run(lambda: "done")
        assert result == "done"
