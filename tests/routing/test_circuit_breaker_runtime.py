"""GW-13: Per-deployment circuit breaker integration tests.

Tests verify that the circuit breaker helpers correctly filter LiteLLM
model_list entries and integrate with the LiteLLM router.

# @trace FR-ROUTE-013
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.circuit_breaker import (
    CircuitOpenError,
    ProviderCircuitBreakerConfig,
    ProviderCircuitBreakerRegistry,
    get_healthy_deployments,
    record_deployment_failure,
    record_deployment_success,
    with_circuit_breaker,
)
from thegent.utils.routing_impl.litellm_router import get_circuit_breaker_status

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_registry():
    """Reset the global circuit breaker registry before each test."""
    ProviderCircuitBreakerRegistry.reset_instance()
    yield
    ProviderCircuitBreakerRegistry.reset_instance()


def _make_model_list() -> list[dict]:
    """Return a minimal LiteLLM model_list with two providers."""
    return [
        {
            "model_name": "gpt-4o",
            "litellm_params": {"model": "openai/gpt-4o", "api_key": "dummy"},
        },
        {
            "model_name": "claude-opus-4.6",
            "litellm_params": {
                "model": "anthropic/claude-opus-4.6",
                "api_key": "dummy",
            },
        },
        {
            "model_name": "gemini-3-flash",
            "litellm_params": {"model": "gemini/gemini-3-flash", "api_key": "dummy"},
        },
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ROUTE-013")
class TestGetHealthyDeployments:
    """Tests for get_healthy_deployments."""

    def test_get_healthy_deployments_removes_open_circuits(self) -> None:
        """Open-circuit providers are excluded from the returned model list."""
        registry = ProviderCircuitBreakerRegistry.get_instance()
        # Configure with failure_threshold=1 so a single failure opens the circuit
        config = ProviderCircuitBreakerConfig(failure_threshold=1, timeout_sec=3600)
        breaker = registry.register("openai", config)
        breaker.record_failure()  # Trips to OPEN immediately (threshold=1)

        assert breaker.state == "open"

        model_list = _make_model_list()
        healthy = get_healthy_deployments(model_list, registry=registry)

        model_names = [e["model_name"] for e in healthy]
        assert "gpt-4o" not in model_names, "openai deployment must be excluded when circuit is OPEN"
        assert "claude-opus-4.6" in model_names
        assert "gemini-3-flash" in model_names

    def test_get_healthy_deployments_falls_back_when_all_open(self) -> None:
        """When all providers are open, the full list is returned (prefer degraded over outage)."""
        registry = ProviderCircuitBreakerRegistry.get_instance()
        config = ProviderCircuitBreakerConfig(failure_threshold=1, timeout_sec=3600)

        for provider in ("openai", "anthropic", "gemini"):
            breaker = registry.register(provider, config)
            breaker.record_failure()
            assert breaker.state == "open"

        model_list = _make_model_list()
        result = get_healthy_deployments(model_list, registry=registry)

        assert result == model_list, "Full list must be returned when all circuits are open"

    def test_get_healthy_deployments_no_open_circuits_returns_full_list(self) -> None:
        """When no circuits are open, the full list is returned unchanged."""
        model_list = _make_model_list()
        registry = ProviderCircuitBreakerRegistry.get_instance()
        result = get_healthy_deployments(model_list, registry=registry)
        assert result == model_list


@pytest.mark.requirement("FR-ROUTE-013")
class TestRecordDeploymentFailure:
    """Tests for record_deployment_failure."""

    def test_record_failure_opens_circuit_after_threshold(self) -> None:
        """After failure_threshold failures the circuit breaker opens."""
        registry = ProviderCircuitBreakerRegistry.get_instance()
        config = ProviderCircuitBreakerConfig(failure_threshold=3, timeout_sec=3600)
        registry.register("openai", config)

        error = RuntimeError("provider error")
        for _ in range(3):
            record_deployment_failure("openai", error, registry=registry)

        breaker = registry.get("openai")
        assert breaker.state == "open", "Circuit must be open after threshold failures"

    def test_record_failure_increments_counter(self) -> None:
        """Each call to record_deployment_failure increments the fail counter."""
        registry = ProviderCircuitBreakerRegistry.get_instance()
        config = ProviderCircuitBreakerConfig(failure_threshold=10, timeout_sec=3600)
        registry.register("anthropic", config)

        breaker = registry.get("anthropic")
        initial_count = breaker.fail_counter
        record_deployment_failure("anthropic", ValueError("err"), registry=registry)
        assert breaker.fail_counter == initial_count + 1


@pytest.mark.requirement("FR-ROUTE-013")
class TestRecordDeploymentSuccess:
    """Tests for record_deployment_success."""

    def test_record_success_updates_state(self) -> None:
        """record_deployment_success executes without error and closes the breaker."""
        registry = ProviderCircuitBreakerRegistry.get_instance()
        record_deployment_success("openai", registry=registry)
        breaker = registry.get("openai")
        # After a success on a new (closed) breaker it remains closed
        assert breaker.state == "closed"

    def test_record_success_closes_half_open_breaker(self) -> None:
        """A success recorded on a breaker in CLOSED state keeps it closed (no-op)."""
        registry = ProviderCircuitBreakerRegistry.get_instance()
        config = ProviderCircuitBreakerConfig(failure_threshold=5, timeout_sec=3600)
        breaker = registry.register("gemini", config)
        assert breaker.state == "closed"
        record_deployment_success("gemini", registry=registry)
        assert breaker.state == "closed"


@pytest.mark.requirement("FR-ROUTE-013")
class TestWithCircuitBreaker:
    """Tests for with_circuit_breaker."""

    def test_with_circuit_breaker_executes_func(self) -> None:
        """with_circuit_breaker returns the function's return value when circuit is closed."""
        registry = ProviderCircuitBreakerRegistry.get_instance()

        result = with_circuit_breaker("openai", lambda x: x * 2, 21, registry=registry)
        assert result == 42

    def test_with_circuit_breaker_raises_when_open(self) -> None:
        """CircuitOpenError is raised immediately when the circuit is already OPEN."""
        registry = ProviderCircuitBreakerRegistry.get_instance()
        config = ProviderCircuitBreakerConfig(failure_threshold=1, timeout_sec=3600)
        breaker = registry.register("openai", config)
        breaker.record_failure()
        assert breaker.state == "open"

        with pytest.raises(CircuitOpenError):
            with_circuit_breaker("openai", lambda: "should_not_run", registry=registry)

    def test_with_circuit_breaker_records_failure_on_exception(self) -> None:
        """Exceptions from the wrapped function are re-raised and the failure is recorded."""
        registry = ProviderCircuitBreakerRegistry.get_instance()
        config = ProviderCircuitBreakerConfig(failure_threshold=5, timeout_sec=3600)
        registry.register("anthropic", config)
        breaker = registry.get("anthropic")

        def _failing() -> None:
            raise ValueError("simulated provider error")

        with pytest.raises(ValueError, match="simulated provider error"):
            with_circuit_breaker("anthropic", _failing, registry=registry)

        assert breaker.fail_counter == 1


@pytest.mark.requirement("FR-ROUTE-013")
class TestGetCircuitBreakerStatus:
    """Tests for get_circuit_breaker_status (in litellm_router)."""

    def test_get_circuit_breaker_status_returns_dict(self) -> None:
        """Returns a dict mapping provider name to a state string."""
        registry = ProviderCircuitBreakerRegistry.get_instance()
        # Register a couple of providers
        registry.get("openai")
        registry.get("anthropic")

        status = get_circuit_breaker_status()

        assert isinstance(status, dict), "Status must be a dict"
        for provider, state in status.items():
            assert isinstance(provider, str)
            assert isinstance(state, str)
            assert state in {"closed", "open", "half-open"}, f"Unexpected state {state!r} for provider {provider!r}"

    def test_get_circuit_breaker_status_reflects_open_state(self) -> None:
        """An open provider shows as 'open' in the status dict."""
        registry = ProviderCircuitBreakerRegistry.get_instance()
        config = ProviderCircuitBreakerConfig(failure_threshold=1, timeout_sec=3600)
        breaker = registry.register("openai", config)
        breaker.record_failure()
        assert breaker.state == "open"

        status = get_circuit_breaker_status()
        assert status.get("openai") == "open"

    def test_get_circuit_breaker_status_empty_when_no_providers(self) -> None:
        """Returns an empty dict when no providers have been registered."""
        status = get_circuit_breaker_status()
        assert status == {}
