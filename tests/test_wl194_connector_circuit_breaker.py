"""Tests for WL-194: Connector Circuit Breakers.

Verifies circuit breaker state transitions, failure tracking, and recovery behavior.

# @trace WL-194
"""

from __future__ import annotations

import pytest

from thegent.integrations.connector_circuit_breaker import (
    CircuitState,
    ConnectorCircuitBreaker,
)


@pytest.mark.requirement("WL-194")
class TestCircuitBreakerInitialization:
    """WL-194: Circuit breaker initialization."""

    def test_init_with_defaults(self):
        """Initialize circuit breaker with default parameters."""
        cb = ConnectorCircuitBreaker()

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.is_open() is False

    def test_init_with_custom_threshold(self):
        """Initialize with custom failure threshold."""
        cb = ConnectorCircuitBreaker(failure_threshold=10)

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_init_with_custom_timeout(self):
        """Initialize with custom recovery timeout."""
        cb = ConnectorCircuitBreaker(recovery_timeout_seconds=120.0)

        assert cb.state == CircuitState.CLOSED

    def test_init_invalid_threshold(self):
        """Reject invalid failure threshold."""
        with pytest.raises(ValueError, match="failure_threshold must be > 0"):
            ConnectorCircuitBreaker(failure_threshold=0)

        with pytest.raises(ValueError, match="failure_threshold must be > 0"):
            ConnectorCircuitBreaker(failure_threshold=-1)

    def test_init_invalid_timeout(self):
        """Reject negative recovery timeout."""
        with pytest.raises(ValueError, match="recovery_timeout_seconds must be >= 0"):
            ConnectorCircuitBreaker(recovery_timeout_seconds=-1.0)


@pytest.mark.requirement("WL-194")
class TestCircuitBreakerFailures:
    """WL-194: Failure recording and state transitions."""

    def test_record_single_failure_stays_closed(self):
        """Single failure does not open the circuit."""
        cb = ConnectorCircuitBreaker(failure_threshold=5)

        cb.record_failure()

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1

    def test_failure_count_increments(self):
        """Failure count increments with each call."""
        cb = ConnectorCircuitBreaker(failure_threshold=5)

        for i in range(1, 6):
            cb.record_failure()
            assert cb.failure_count == i

    def test_open_at_threshold(self):
        """Circuit opens when failure count reaches threshold."""
        cb = ConnectorCircuitBreaker(failure_threshold=3)

        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.is_open() is True

    def test_failures_after_open_stay_open(self):
        """Additional failures do not change state once open."""
        cb = ConnectorCircuitBreaker(failure_threshold=2)

        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3


@pytest.mark.requirement("WL-194")
class TestCircuitBreakerSuccess:
    """WL-194: Success recording and recovery."""

    def test_success_resets_closed_state(self):
        """Success resets failures when circuit is closed."""
        cb = ConnectorCircuitBreaker(failure_threshold=5)

        cb.record_failure()
        cb.record_failure()
        assert cb.failure_count == 2

        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    def test_success_on_closed_no_change(self):
        """Success on closed circuit resets failures to 0."""
        cb = ConnectorCircuitBreaker()

        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    def test_success_in_half_open_closes_circuit(self):
        """Success in half-open state transitions to closed."""
        cb = ConnectorCircuitBreaker(failure_threshold=2, recovery_timeout_seconds=0.01)

        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Trigger transition to half-open
        import time

        time.sleep(0.02)
        assert cb.is_open() is False  # Transitions to HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0


@pytest.mark.requirement("WL-194")
class TestCircuitBreakerRecovery:
    """WL-194: Recovery timeout and half-open state."""

    def test_recovery_timeout_transitions_to_half_open(self):
        """Circuit transitions to half-open after recovery timeout."""
        cb = ConnectorCircuitBreaker(failure_threshold=2, recovery_timeout_seconds=0.01)

        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.is_open() is True

        import time

        time.sleep(0.02)

        assert cb.is_open() is False  # is_open() triggers state check
        assert cb.state == CircuitState.HALF_OPEN

    def test_failure_in_half_open_returns_to_open(self):
        """Failure in half-open state returns circuit to open."""
        cb = ConnectorCircuitBreaker(failure_threshold=2, recovery_timeout_seconds=0.01)

        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        import time

        time.sleep(0.02)

        # Trigger half-open check
        cb.is_open()
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_zero_timeout_immediate_recovery(self):
        """Zero timeout allows immediate recovery attempt."""
        cb = ConnectorCircuitBreaker(failure_threshold=1, recovery_timeout_seconds=0.0)

        cb.record_failure()
        # Accessing state with zero timeout immediately transitions to HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN

        # is_open still returns True for HALF_OPEN
        assert cb.is_open() is True


@pytest.mark.requirement("WL-194")
class TestCircuitBreakerProperties:
    """WL-194: Property accessors and state queries."""

    def test_state_property_returns_current_state(self):
        """state property returns current CircuitState."""
        cb = ConnectorCircuitBreaker(failure_threshold=2)

        assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_failure_count_property(self):
        """failure_count property returns current count."""
        cb = ConnectorCircuitBreaker()

        assert cb.failure_count == 0

        cb.record_failure()
        cb.record_failure()
        assert cb.failure_count == 2

    def test_is_open_returns_boolean(self):
        """is_open() returns boolean."""
        cb = ConnectorCircuitBreaker(failure_threshold=1)

        assert cb.is_open() is False

        cb.record_failure()
        assert cb.is_open() is True

    def test_is_open_with_half_open_state(self):
        """is_open() transitions to HALF_OPEN when timeout expires."""
        cb = ConnectorCircuitBreaker(failure_threshold=1, recovery_timeout_seconds=0.01)

        cb.record_failure()
        assert cb.is_open() is True

        # Wait for timeout to expire
        import time

        time.sleep(0.02)

        # Trigger half-open by calling is_open()
        result = cb.is_open()
        assert result is False  # HALF_OPEN returns False from is_open()
        assert cb.state == CircuitState.HALF_OPEN
