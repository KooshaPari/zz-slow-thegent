"""WBS Phase 2 Reliability — combined test suite (WL-039).

Covers:
- WP-2001: ProviderCircuitBreaker and ProviderCircuitBreakerRegistry
- WP-2003: ProviderLoopTimeout / run_with_provider_loop_timeout
- Integration: breaker + loop timeout interaction

# @trace WL-039 WP-2001 WP-2003
"""

from __future__ import annotations

import asyncio
import threading

import pytest

from thegent.agents.provider_loop import (
    PROVIDER_LOOP_TIMEOUT_SEC,
    ProviderLoopTimeout,
    run_with_provider_loop_timeout,
)
from thegent.utils.routing_impl.circuit_breaker import (
    CircuitOpenError,
    ProviderCircuitBreaker,
    ProviderCircuitBreakerConfig,
    ProviderCircuitBreakerRegistry,
)

# ===========================================================================
# WP-2001: ProviderCircuitBreaker unit tests
# ===========================================================================


@pytest.mark.unit
class TestProviderCircuitBreakerConfig:
    """ProviderCircuitBreakerConfig defaults and custom values."""

    def test_default_config(self) -> None:
        # @trace WL-039 WP-2001
        cfg = ProviderCircuitBreakerConfig()
        assert cfg.failure_threshold == 5
        assert cfg.success_threshold == 2
        assert cfg.timeout_sec == 60.0
        assert cfg.half_open_max_calls == 3

    def test_custom_config(self) -> None:
        # @trace WL-039 WP-2001
        cfg = ProviderCircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=1,
            timeout_sec=30.0,
            half_open_max_calls=2,
        )
        assert cfg.failure_threshold == 3
        assert cfg.success_threshold == 1
        assert cfg.timeout_sec == 30.0
        assert cfg.half_open_max_calls == 2


@pytest.mark.unit
class TestProviderCircuitBreakerState:
    """State machine: CLOSED -> OPEN -> (HALF_OPEN) -> CLOSED."""

    def test_initial_state_is_closed(self) -> None:
        # @trace WL-039 WP-2001
        breaker = ProviderCircuitBreaker("test-init")
        assert breaker.state == "closed"

    def test_fail_counter_starts_at_zero(self) -> None:
        # @trace WL-039 WP-2001
        breaker = ProviderCircuitBreaker("test-counter")
        assert breaker.fail_counter == 0

    async def test_trip_to_open_after_threshold(self) -> None:
        # @trace WL-039 WP-2001
        config = ProviderCircuitBreakerConfig(failure_threshold=3, timeout_sec=999)
        breaker = ProviderCircuitBreaker("trip-test", config)

        async def _fail() -> None:
            raise RuntimeError("provider error")

        for i in range(3):
            with pytest.raises(RuntimeError):
                await breaker.call_async(_fail)
            if i < 2:
                assert breaker.state == "closed"

        assert breaker.state == "open"

    async def test_open_raises_circuit_open_error(self) -> None:
        # @trace WL-039 WP-2001
        config = ProviderCircuitBreakerConfig(failure_threshold=1, timeout_sec=999)
        breaker = ProviderCircuitBreaker("open-reject", config)

        async def _fail() -> None:
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            await breaker.call_async(_fail)

        # Must raise CircuitOpenError, NOT RuntimeError
        with pytest.raises(CircuitOpenError):
            await breaker.call_async(_fail)

    async def test_reset_closes_open_breaker(self) -> None:
        # @trace WL-039 WP-2001
        config = ProviderCircuitBreakerConfig(failure_threshold=1, timeout_sec=999)
        breaker = ProviderCircuitBreaker("reset-test", config)

        async def _fail() -> None:
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            await breaker.call_async(_fail)

        assert breaker.state == "open"
        breaker.reset()
        assert breaker.state == "closed"

    async def test_successful_call_on_closed_breaker(self) -> None:
        # @trace WL-039 WP-2001
        breaker = ProviderCircuitBreaker("success-test")

        async def _succeed() -> str:
            return "ok"

        result = await breaker.call_async(_succeed)
        assert result == "ok"
        assert breaker.state == "closed"

    def test_sync_call_success(self) -> None:
        # @trace WL-039 WP-2001
        breaker = ProviderCircuitBreaker("sync-success")
        result = breaker.call(lambda: "sync-ok")
        assert result == "sync-ok"

    def test_sync_call_open_raises_circuit_open_error(self) -> None:
        # @trace WL-039 WP-2001
        # With failure_threshold=2: first call raises original exc, second trips→CircuitOpenError
        config = ProviderCircuitBreakerConfig(failure_threshold=2, timeout_sec=999)
        breaker = ProviderCircuitBreaker("sync-open", config)

        def _fail() -> None:
            raise RuntimeError("sync fail")

        # First call: original RuntimeError (breaker still CLOSED after)
        with pytest.raises(RuntimeError):
            breaker.call(_fail)

        # Second call: pybreaker trips on this one → CircuitOpenError
        with pytest.raises(CircuitOpenError):
            breaker.call(_fail)

        # Third call: already OPEN → CircuitOpenError
        with pytest.raises(CircuitOpenError):
            breaker.call(_fail)

    def test_repr_contains_provider_and_state(self) -> None:
        # @trace WL-039 WP-2001
        breaker = ProviderCircuitBreaker("repr-test")
        r = repr(breaker)
        assert "repr-test" in r
        assert "closed" in r


# ===========================================================================
# WP-2001: ProviderCircuitBreakerRegistry unit tests
# ===========================================================================


@pytest.mark.unit
class TestProviderCircuitBreakerRegistry:
    """Registry lifecycle and singleton behaviour."""

    def setup_method(self) -> None:
        ProviderCircuitBreakerRegistry.reset_instance()

    def teardown_method(self) -> None:
        ProviderCircuitBreakerRegistry.reset_instance()

    def test_get_instance_singleton(self) -> None:
        # @trace WL-039 WP-2001
        a = ProviderCircuitBreakerRegistry.get_instance()
        b = ProviderCircuitBreakerRegistry.get_instance()
        assert a is b

    def test_get_creates_breaker_on_first_call(self) -> None:
        # @trace WL-039 WP-2001
        reg = ProviderCircuitBreakerRegistry.get_instance()
        breaker = reg.get("new-provider")
        assert breaker.provider == "new-provider"

    def test_get_returns_same_breaker(self) -> None:
        # @trace WL-039 WP-2001
        reg = ProviderCircuitBreakerRegistry.get_instance()
        b1 = reg.get("stable")
        b2 = reg.get("stable")
        assert b1 is b2

    def test_register_replaces_breaker(self) -> None:
        # @trace WL-039 WP-2001
        reg = ProviderCircuitBreakerRegistry.get_instance()
        b1 = reg.get("replace-me")
        new_cfg = ProviderCircuitBreakerConfig(failure_threshold=10)
        b2 = reg.register("replace-me", new_cfg)
        b3 = reg.get("replace-me")
        assert b2 is b3
        assert b1 is not b3

    def test_all_states_returns_dict(self) -> None:
        # @trace WL-039 WP-2001
        reg = ProviderCircuitBreakerRegistry.get_instance()
        reg.get("prov-a")
        reg.get("prov-b")
        states = reg.all_states()
        assert "prov-a" in states
        assert "prov-b" in states
        assert states["prov-a"] == "closed"

    def test_all_open_empty_when_all_closed(self) -> None:
        # @trace WL-039 WP-2001
        reg = ProviderCircuitBreakerRegistry.get_instance()
        reg.get("closed-prov")
        assert "closed-prov" not in reg.all_open()

    async def test_all_open_lists_tripped_providers(self) -> None:
        # @trace WL-039 WP-2001
        reg = ProviderCircuitBreakerRegistry.get_instance()
        config = ProviderCircuitBreakerConfig(failure_threshold=1, timeout_sec=999)
        breaker = reg.register("tripped", config)

        async def _fail() -> None:
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            await breaker.call_async(_fail)

        assert "tripped" in reg.all_open()

    def test_clear_removes_all_breakers(self) -> None:
        # @trace WL-039 WP-2001
        reg = ProviderCircuitBreakerRegistry.get_instance()
        reg.get("to-clear")
        reg.clear()
        assert reg.all_states() == {}

    def test_thread_safety_concurrent_get(self) -> None:
        # @trace WL-039 WP-2001
        reg = ProviderCircuitBreakerRegistry.get_instance()
        results: list[ProviderCircuitBreaker] = []
        lock = threading.Lock()

        def _get() -> None:
            b = reg.get("thread-safe-provider")
            with lock:
                results.append(b)

        threads = [threading.Thread(target=_get) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        first = results[0]
        for b in results[1:]:
            assert b is first


# ===========================================================================
# WP-2003: ProviderLoopTimeout unit tests
# ===========================================================================


@pytest.mark.unit
class TestProviderLoopTimeoutConstants:
    """PROVIDER_LOOP_TIMEOUT_SEC must default to 300."""

    def test_default_timeout(self) -> None:
        # @trace WL-039 WP-2003
        # Default env value is 300 unless overridden
        assert isinstance(PROVIDER_LOOP_TIMEOUT_SEC, int)
        assert PROVIDER_LOOP_TIMEOUT_SEC > 0


@pytest.mark.unit
class TestProviderLoopTimeoutException:
    """ProviderLoopTimeout carries timeout_sec and context."""

    def test_exception_attributes(self) -> None:
        # @trace WL-039 WP-2003
        exc = ProviderLoopTimeout(timeout_sec=300, context="test-provider")
        assert exc.timeout_sec == 300
        assert exc.context == "test-provider"

    def test_exception_message(self) -> None:
        # @trace WL-039 WP-2003
        exc = ProviderLoopTimeout(300)
        assert "300" in str(exc)

    def test_exception_with_context_in_message(self) -> None:
        # @trace WL-039 WP-2003
        exc = ProviderLoopTimeout(60, "my-provider")
        assert "my-provider" in str(exc)

    def test_exception_no_context(self) -> None:
        # @trace WL-039 WP-2003
        exc = ProviderLoopTimeout(30)
        assert exc.context == ""


@pytest.mark.unit
class TestRunWithProviderLoopTimeout:
    """run_with_provider_loop_timeout() function behaviour."""

    async def test_fast_coro_returns_value(self) -> None:
        # @trace WL-039 WP-2003
        async def _quick() -> int:
            return 42

        result = await run_with_provider_loop_timeout(_quick(), timeout_sec=5)
        assert result == 42

    async def test_slow_coro_raises_provider_loop_timeout(self) -> None:
        # @trace WL-039 WP-2003
        async def _slow() -> None:
            await asyncio.sleep(10)

        with pytest.raises(ProviderLoopTimeout):
            await run_with_provider_loop_timeout(_slow(), timeout_sec=1)

    async def test_timeout_error_not_swallowed(self) -> None:
        # @trace WL-039 WP-2003
        async def _hang() -> None:
            await asyncio.sleep(999)

        # Must raise ProviderLoopTimeout, NOT asyncio.TimeoutError
        with pytest.raises(ProviderLoopTimeout):
            await run_with_provider_loop_timeout(_hang(), timeout_sec=1)

    async def test_non_timeout_exception_propagates(self) -> None:
        # @trace WL-039 WP-2003
        async def _raises() -> None:
            raise KeyError("missing key")

        with pytest.raises(KeyError, match="missing key"):
            await run_with_provider_loop_timeout(_raises(), timeout_sec=5)

    async def test_uses_default_timeout_when_none_provided(self) -> None:
        # @trace WL-039 WP-2003
        async def _instant() -> str:
            return "done"

        result = await run_with_provider_loop_timeout(_instant())
        assert result == "done"

    async def test_context_appears_in_exception(self) -> None:
        # @trace WL-039 WP-2003
        async def _slow() -> None:
            await asyncio.sleep(10)

        with pytest.raises(ProviderLoopTimeout) as exc_info:
            await run_with_provider_loop_timeout(_slow(), timeout_sec=1, context="openai")
        assert "openai" in exc_info.value.context


# ===========================================================================
# Integration: circuit breaker + provider loop timeout
# ===========================================================================


@pytest.mark.unit
class TestCircuitBreakerAndLoopTimeout:
    """Integration tests combining circuit breaker open state with loop timeout."""

    def setup_method(self) -> None:
        ProviderCircuitBreakerRegistry.reset_instance()

    def teardown_method(self) -> None:
        ProviderCircuitBreakerRegistry.reset_instance()

    async def test_open_breaker_in_loop_raises_circuit_open_not_timeout(self) -> None:
        # @trace WL-039 WP-2001 WP-2003
        config = ProviderCircuitBreakerConfig(failure_threshold=1, timeout_sec=999)
        breaker = ProviderCircuitBreaker("integration-test", config)

        async def _fail() -> None:
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            await breaker.call_async(_fail)

        async def _loop_with_open_breaker() -> str:
            return await breaker.call_async(_fail)

        # Circuit is open; CircuitOpenError must bubble, not be masked as ProviderLoopTimeout
        with pytest.raises(CircuitOpenError):
            await run_with_provider_loop_timeout(_loop_with_open_breaker(), timeout_sec=5, context="integration")
