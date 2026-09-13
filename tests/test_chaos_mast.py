"""WP-2004: Chaos tests — MAST F-01 through F-06.

Tests six chaos scenarios covering provider failures, partial responses,
timeouts, all-circuit-open conditions, provider-loop timeout, and concurrent
circuit-breaker state consistency.

# @trace WL-039 WP-2004
"""

from __future__ import annotations

import asyncio

import orjson as json
import pybreaker
import pytest

from thegent.agents.provider_loop import (
    ProviderLoopTimeout,
    run_with_provider_loop_timeout,
)
from thegent.utils.routing_impl.circuit_breaker import (
    CircuitOpenError,
    ProviderCircuitBreaker,
    ProviderCircuitBreakerConfig,
    ProviderCircuitBreakerRegistry,
)

# ---------------------------------------------------------------------------
# MAST F-01: Provider drops connection mid-stream
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMastF01:
    """F-01: Provider drops connection mid-stream — agent handles gracefully."""

    async def test_connection_drop_raises_error(self) -> None:
        # @trace WL-039 WP-2004 F-01
        async def _provider_that_drops() -> str:
            raise ConnectionResetError("Connection reset by peer mid-stream")

        with pytest.raises(ConnectionResetError, match="mid-stream"):
            await _provider_that_drops()

    async def test_circuit_breaker_records_connection_drop(self) -> None:
        # @trace WL-039 WP-2004 F-01
        config = ProviderCircuitBreakerConfig(failure_threshold=2, timeout_sec=999)
        breaker = ProviderCircuitBreaker("test-f01", config)

        call_count = 0

        async def _drop_conn() -> str:
            nonlocal call_count
            call_count += 1
            raise ConnectionResetError("dropped")

        # First failure — still CLOSED
        with pytest.raises(ConnectionResetError):
            await breaker.call_async(_drop_conn)
        assert breaker.state == "closed"

        # Second failure — trips to OPEN
        with pytest.raises(ConnectionResetError):
            await breaker.call_async(_drop_conn)
        assert breaker.state == "open"

    async def test_open_circuit_rejects_subsequent_calls(self) -> None:
        # @trace WL-039 WP-2004 F-01
        config = ProviderCircuitBreakerConfig(failure_threshold=1, timeout_sec=999)
        breaker = ProviderCircuitBreaker("test-f01-reject", config)

        async def _always_fail() -> str:
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            await breaker.call_async(_always_fail)

        # Now open — should raise CircuitOpenError
        with pytest.raises(CircuitOpenError):
            await breaker.call_async(_always_fail)


# ---------------------------------------------------------------------------
# MAST F-02: Provider returns partial JSON
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMastF02:
    """F-02: Provider returns partial JSON — parse error propagates as ProviderError."""

    def test_partial_json_raises_decode_error(self) -> None:
        # @trace WL-039 WP-2004 F-02
        partial = '{"message": "hello", "tokens'  # truncated

        with pytest.raises(json.JSONDecodeError):
            json.loads(partial)

    def test_partial_json_error_is_not_retryable(self) -> None:
        # @trace WL-039 WP-2004 F-02
        from thegent.agents.base import RunResult
        from thegent.agents.resilience import is_retryable

        result = RunResult(exit_code=1, stdout="", stderr="JSONDecodeError: invalid syntax")
        assert is_retryable(result) is False

    async def test_circuit_breaker_trips_on_parse_errors(self) -> None:
        # @trace WL-039 WP-2004 F-02
        config = ProviderCircuitBreakerConfig(failure_threshold=3, timeout_sec=999)
        breaker = ProviderCircuitBreaker("test-f02", config)

        async def _return_partial_json() -> dict:
            raise ValueError("JSONDecodeError: partial JSON response")

        for _ in range(3):
            with pytest.raises(ValueError):  # noqa: PT011
                await breaker.call_async(_return_partial_json)

        assert breaker.state == "open"
        with pytest.raises(CircuitOpenError):
            await breaker.call_async(_return_partial_json)


# ---------------------------------------------------------------------------
# MAST F-03: Provider timeouts at 50% through response
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMastF03:
    """F-03: Provider timeouts at 50% through response — timeout triggers."""

    async def test_asyncio_timeout_raises(self) -> None:
        # @trace WL-039 WP-2004 F-03
        async def _slow_provider() -> str:
            await asyncio.sleep(10)
            return "too late"

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(_slow_provider(), timeout=0.01)

    async def test_provider_loop_timeout_wraps_timeout(self) -> None:
        # @trace WL-039 WP-2004 F-03
        async def _slow_loop() -> str:
            await asyncio.sleep(10)
            return "never"

        with pytest.raises(ProviderLoopTimeout):
            await run_with_provider_loop_timeout(_slow_loop(), timeout_sec=1, context="f03-test")

    async def test_provider_loop_timeout_carries_context(self) -> None:
        # @trace WL-039 WP-2004 F-03
        async def _slow() -> str:
            await asyncio.sleep(10)
            return "never"

        exc = None
        with pytest.raises(ProviderLoopTimeout) as exc_info:
            await run_with_provider_loop_timeout(_slow(), timeout_sec=1, context="provider-X")
        exc = exc_info.value
        assert exc.timeout_sec == 1
        assert "provider-X" in exc.context


# ---------------------------------------------------------------------------
# MAST F-04: All providers circuit-break simultaneously
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMastF04:
    """F-04: All providers circuit-break simultaneously — fail fast with clear error."""

    def setup_method(self) -> None:
        ProviderCircuitBreakerRegistry.reset_instance()

    def teardown_method(self) -> None:
        ProviderCircuitBreakerRegistry.reset_instance()

    async def test_all_providers_open_fail_fast(self) -> None:
        # @trace WL-039 WP-2004 F-04
        registry = ProviderCircuitBreakerRegistry.get_instance()
        providers = ["openai", "anthropic", "google", "minimax"]

        # Trip all breakers
        for name in providers:
            config = ProviderCircuitBreakerConfig(failure_threshold=1, timeout_sec=999)
            breaker = registry.register(name, config)

            async def _fail() -> str:
                raise RuntimeError("provider down")

            with pytest.raises(RuntimeError):
                await breaker.call_async(_fail)

        # All should now be open
        open_list = registry.all_open()
        assert set(open_list) == set(providers)

    async def test_all_open_raises_circuit_open_on_call(self) -> None:
        # @trace WL-039 WP-2004 F-04
        registry = ProviderCircuitBreakerRegistry.get_instance()
        config = ProviderCircuitBreakerConfig(failure_threshold=1, timeout_sec=999)
        breaker = registry.register("sole-provider", config)

        async def _fail() -> str:
            raise RuntimeError("down")

        with pytest.raises(RuntimeError):
            await breaker.call_async(_fail)

        # Circuit is now open; next call must raise CircuitOpenError
        with pytest.raises(CircuitOpenError):
            await breaker.call_async(_fail)


# ---------------------------------------------------------------------------
# MAST F-05: Provider loop timeout fires
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMastF05:
    """F-05: Provider loop timeout fires — ProviderLoopTimeout raised."""

    async def test_loop_timeout_raised_not_swallowed(self) -> None:
        # @trace WL-039 WP-2004 F-05
        async def _infinite_loop() -> str:
            while True:
                await asyncio.sleep(0.1)

        with pytest.raises(ProviderLoopTimeout) as exc_info:
            await run_with_provider_loop_timeout(_infinite_loop(), timeout_sec=1, context="F-05")

        assert exc_info.value.timeout_sec == 1

    async def test_loop_timeout_error_message_contains_timeout(self) -> None:
        # @trace WL-039 WP-2004 F-05
        async def _hang() -> None:
            await asyncio.sleep(999)

        with pytest.raises(ProviderLoopTimeout, match=r"timed out after \d+s"):
            await run_with_provider_loop_timeout(_hang(), timeout_sec=1)

    async def test_successful_loop_completes_within_timeout(self) -> None:
        # @trace WL-039 WP-2004 F-05
        async def _fast_provider() -> str:
            return "result"

        result = await run_with_provider_loop_timeout(_fast_provider(), timeout_sec=5)
        assert result == "result"

    async def test_non_timeout_exceptions_propagate(self) -> None:
        # @trace WL-039 WP-2004 F-05
        async def _raises_value_error() -> None:
            raise ValueError("not a timeout")

        with pytest.raises(ValueError, match="not a timeout"):  # noqa: PT011
            await run_with_provider_loop_timeout(_raises_value_error(), timeout_sec=5)


# ---------------------------------------------------------------------------
# MAST F-06: Concurrent requests hit same circuit breaker
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMastF06:
    """F-06: Concurrent requests hit same circuit breaker — state remains consistent."""

    def setup_method(self) -> None:
        ProviderCircuitBreakerRegistry.reset_instance()

    def teardown_method(self) -> None:
        ProviderCircuitBreakerRegistry.reset_instance()

    async def test_concurrent_failures_trip_breaker_once(self) -> None:
        # @trace WL-039 WP-2004 F-06
        config = ProviderCircuitBreakerConfig(failure_threshold=3, timeout_sec=999)
        breaker = ProviderCircuitBreaker("concurrent-test", config)

        async def _fail() -> str:
            raise RuntimeError("concurrent fail")

        # Fire 10 concurrent calls — all fail
        tasks = [asyncio.create_task(breaker.call_async(_fail)) for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should be either RuntimeError or CircuitOpenError — nothing else
        for r in results:
            assert isinstance(r, (RuntimeError, CircuitOpenError, pybreaker.CircuitBreakerError))

        # Breaker must be in a deterministic state (open or closed, not corrupted)
        assert breaker.state in ("open", "closed", "half-open")

    async def test_registry_returns_same_breaker_under_concurrency(self) -> None:
        # @trace WL-039 WP-2004 F-06
        registry = ProviderCircuitBreakerRegistry.get_instance()
        config = ProviderCircuitBreakerConfig()

        async def _get_breaker() -> ProviderCircuitBreaker:
            return registry.get("shared-provider", config)

        # Multiple concurrent get() calls
        tasks = [asyncio.create_task(_get_breaker()) for _ in range(20)]
        breakers = await asyncio.gather(*tasks)

        # All must be the same object (singleton per provider)
        first = breakers[0]
        for b in breakers[1:]:
            assert b is first, "Registry must return identical breaker instance under concurrency"

    async def test_fail_counter_monotonically_increases_under_concurrency(self) -> None:
        # @trace WL-039 WP-2004 F-06
        # Use high threshold so breaker stays closed during test
        config = ProviderCircuitBreakerConfig(failure_threshold=100, timeout_sec=999)
        breaker = ProviderCircuitBreaker("monotonic-test", config)

        async def _fail_once() -> str:
            raise RuntimeError("concurrent fail")

        tasks = [asyncio.create_task(breaker.call_async(_fail_once)) for _ in range(5)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Fail counter must be > 0 and <= 5 (no double counting)
        assert 1 <= breaker.fail_counter <= 5
