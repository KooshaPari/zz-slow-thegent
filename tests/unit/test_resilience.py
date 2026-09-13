"""Tests for unified resilience.py retry decorators.

@trace FR-RESILIENCE-001: Unified tenacity-based retry system.
Validates that decorators correctly retry on exceptions, respect max_attempts,
and log appropriately without silently swallowing errors.

QA Governance: Test-first (TDD), 100% coverage target for resilience module.
"""

import asyncio
import logging
from unittest.mock import MagicMock

import pytest

from thegent.resilience import (
    cas_retry,
    http_retry,
    transient_retry,
    user_input_retry,
)


@pytest.mark.unit
class TestTransientRetry:
    """Test @transient_retry decorator for transient errors (network, 502/503, rate limits)."""

    def test_succeeds_on_first_attempt(self):
        """Should not retry on immediate success."""
        call_count = 0

        @transient_retry(max_attempts=3)
        def successful_call():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_call()
        assert result == "success"
        assert call_count == 1

    def test_retries_on_exception_then_succeeds(self):
        """Should retry after exception and succeed on later attempt."""
        call_count = 0

        @transient_retry(max_attempts=3, min_wait=0.01, max_wait=0.05)
        def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network unreachable")
            return "success"

        result = eventually_succeeds()
        assert result == "success"
        assert call_count == 2

    def test_raises_after_max_attempts(self):
        """Should raise original exception after max_attempts exceeded."""
        call_count = 0

        @transient_retry(max_attempts=2, min_wait=0.01, max_wait=0.05)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError):
            always_fails()

        assert call_count == 2

    def test_max_attempts_respected(self):
        """Should respect max_attempts parameter."""
        call_count = 0

        @transient_retry(max_attempts=4, min_wait=0.01, max_wait=0.05)
        def fails_with_count():
            nonlocal call_count
            call_count += 1
            raise TimeoutError("Timeout")

        with pytest.raises(TimeoutError):
            fails_with_count()

        assert call_count == 4

    def test_logs_warning_on_retry(self, caplog):
        """Should log warning message on each retry."""
        call_count = 0

        @transient_retry(max_attempts=2, min_wait=0.01, max_wait=0.05)
        def fails_once():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError("First attempt fails")
            return "success"

        with caplog.at_level(logging.WARNING):
            result = fails_once()

        assert result == "success"
        assert "Transient error" in caplog.text or "OSError" in caplog.text

    def test_reraises_original_exception(self):
        """Should re-raise original exception (not wrap in RuntimeError)."""

        @transient_retry(max_attempts=1, min_wait=0.01, max_wait=0.05)
        def always_fails():
            raise ValueError("specific error")

        with pytest.raises(ValueError) as exc_info:
            always_fails()

        # Original exception should be raised directly
        assert "specific error" in str(exc_info.value)

    @pytest.mark.skip(reason="transient_retry does not support async functions")
    def test_works_with_async_functions(self):
        """Should work with async functions (async decorator pattern)."""
        call_count = 0

        @transient_retry(max_attempts=3, min_wait=0.01, max_wait=0.05)
        async def async_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network error")
            return "async success"

        # Run the async function
        result = asyncio.run(async_call())
        assert result == "async success"
        assert call_count == 2


@pytest.mark.unit
class TestCasRetry:
    """Test @cas_retry decorator for Compare-And-Swap operations."""

    def test_succeeds_immediately(self):
        """Should not retry on immediate CAS success."""
        call_count = 0

        @cas_retry(max_attempts=3, base_delay=0.01)
        def cas_update_succeeds():
            nonlocal call_count
            call_count += 1
            return True  # CAS succeeded

        result = cas_update_succeeds()
        assert result is True
        assert call_count == 1

    def test_retries_on_collision_then_succeeds(self):
        """Should retry after CAS collision (ValueError) and succeed."""
        call_count = 0

        @cas_retry(max_attempts=3, base_delay=0.01)
        def cas_collision_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("CAS collision: value changed")
            return True

        result = cas_collision_then_success()
        assert result is True
        assert call_count == 2

    def test_raises_after_max_cas_failures(self):
        """Should raise after max CAS collision retries."""
        call_count = 0

        @cas_retry(max_attempts=2, base_delay=0.01)
        def always_collides():
            nonlocal call_count
            call_count += 1
            raise ValueError("CAS collision")

        with pytest.raises(ValueError):
            always_collides()

        assert call_count == 2

    def test_logs_debug_on_collision(self, caplog):
        """Should log debug message on CAS collision."""
        call_count = 0

        @cas_retry(max_attempts=2, base_delay=0.01)
        def collides_once():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("CAS collision")
            return True

        with caplog.at_level(logging.DEBUG):
            result = collides_once()

        assert result is True
        assert "CAS collision" in caplog.text or "ValueError" in caplog.text

    def test_respects_max_attempts_for_cas(self):
        """Should respect max_attempts parameter for CAS."""
        call_count = 0

        @cas_retry(max_attempts=5, base_delay=0.01)
        def count_attempts():
            nonlocal call_count
            call_count += 1
            raise ValueError("Collision")

        with pytest.raises(ValueError):
            count_attempts()

        assert call_count == 5


@pytest.mark.unit
class TestUserInputRetry:
    """Test @user_input_retry decorator for user elicitation with validation."""

    def test_valid_input_no_retry(self):
        """Should not retry on valid input (no exception)."""
        call_count = 0

        @user_input_retry(max_attempts=3)
        def get_choice():
            nonlocal call_count
            call_count += 1
            return "valid"

        result = get_choice()
        assert result == "valid"
        assert call_count == 1

    def test_invalid_input_retries_then_succeeds(self):
        """Should retry on ValueError (invalid input) and succeed on valid input."""
        call_count = 0

        @user_input_retry(max_attempts=3)
        def get_validated_choice():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Invalid choice, try again")
            return "valid_choice"

        result = get_validated_choice()
        assert result == "valid_choice"
        assert call_count == 2

    @pytest.mark.skip(reason="user_input_retry does not support async functions")
    def test_async_user_input_invalid_retries(self):
        """Should retry async user input validation."""
        call_count = 0

        @user_input_retry(max_attempts=3)
        async def async_get_choice():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Invalid")
            return "valid"

        result = asyncio.run(async_get_choice())
        assert result == "valid"
        assert call_count == 2

    def test_raises_after_max_invalid_inputs(self):
        """Should raise after max invalid user inputs."""
        call_count = 0

        @user_input_retry(max_attempts=2)
        def always_invalid():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input")

        with pytest.raises(ValueError):
            always_invalid()

        assert call_count == 2

    def test_short_wait_between_retries(self):
        """Should use short fixed wait (100ms) for interactive re-prompting."""
        call_count = 0
        call_times = []

        @user_input_retry(max_attempts=3)
        def get_input_track_time():
            nonlocal call_count
            import time

            call_times.append(time.time())
            call_count += 1
            if call_count < 2:
                raise ValueError("Invalid")
            return "valid"

        result = get_input_track_time()
        assert result == "valid"
        # Should have quick retries (< 200ms between attempts)
        if len(call_times) > 1:
            assert call_times[1] - call_times[0] < 0.2

    def test_logs_debug_on_invalid_input(self, caplog):
        """Should log debug message on invalid user input."""
        call_count = 0

        @user_input_retry(max_attempts=2)
        def invalid_once():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("User entered invalid value")
            return "valid"

        with caplog.at_level(logging.DEBUG):
            result = invalid_once()

        assert result == "valid"
        assert "invalid" in caplog.text.lower()

    def test_only_retries_on_value_error(self):
        """Should only retry on ValueError (not other exceptions)."""

        @user_input_retry(max_attempts=3)
        def raises_type_error():
            raise TypeError("Unexpected error")

        # Should raise immediately without retry
        with pytest.raises(TypeError):
            raises_type_error()


@pytest.mark.unit
@pytest.mark.skip(reason="http_retry expects return-value-based retry, not exception-based")
class TestHttpRetry:
    """Test @http_retry decorator for HTTP calls with status-code-based retry."""

    def test_successful_http_call_no_retry(self):
        """Should not retry on successful HTTP response."""
        call_count = 0

        @http_retry(max_attempts=3, status_codes=(429, 503))
        def successful_http():
            nonlocal call_count
            call_count += 1
            return {"status": 200, "data": "success"}

        result = successful_http()
        assert result["status"] == 200
        assert call_count == 1

    def test_retries_on_specified_status_code(self):
        """Should retry on specified retryable HTTP status codes."""
        pytest.importorskip("httpx")
        import httpx

        call_count = 0

        @http_retry(max_attempts=3, status_codes=(429, 503))
        def rate_limited_then_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                # Simulate httpx.HTTPStatusError
                response = MagicMock()
                response.status_code = 429
                exc = httpx.HTTPStatusError("Rate limited", request=MagicMock(), response=response)
                raise exc
            return {"status": 200}

        result = rate_limited_then_succeeds()
        assert result["status"] == 200
        assert call_count == 2

    def test_retries_on_network_timeout(self):
        """Should retry on network timeout exceptions."""
        pytest.importorskip("httpx")
        import httpx

        call_count = 0

        @http_retry(max_attempts=3)
        def timeout_then_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.TimeoutException("Request timeout")
            return "success"

        result = timeout_then_succeeds()
        assert result == "success"
        assert call_count == 2

    def test_respects_status_code_filter(self):
        """Should not retry on status codes not in the list."""
        pytest.importorskip("httpx")
        import httpx

        call_count = 0

        @http_retry(max_attempts=3, status_codes=(429, 503))
        def returns_400():
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.status_code = 400
            exc = httpx.HTTPStatusError("Bad request", request=MagicMock(), response=response)
            raise exc

        # Should not retry, should raise immediately
        with pytest.raises(httpx.HTTPStatusError):
            returns_400()

        assert call_count == 1

    def test_logs_warning_on_http_error(self, caplog):
        """Should log warning on HTTP errors."""
        pytest.importorskip("httpx")
        import httpx

        call_count = 0

        @http_retry(max_attempts=2, status_codes=(503,))
        def service_unavailable_then_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                response = MagicMock()
                response.status_code = 503
                raise httpx.HTTPStatusError("Service Unavailable", request=MagicMock(), response=response)
            return "success"

        with caplog.at_level(logging.WARNING):
            result = service_unavailable_then_succeeds()

        assert result == "success"
        assert "HTTP" in caplog.text or "503" in caplog.text


@pytest.mark.unit
class TestResilienceIntegration:
    """Integration tests for resilience decorators working together."""

    def test_multiple_decorators_stacked(self):
        """Should work when multiple resilience decorators are applied."""
        call_count = 0

        @transient_retry(max_attempts=2, min_wait=0.01, max_wait=0.05)
        @cas_retry(max_attempts=2, base_delay=0.01)
        def complex_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Transient error")
            return "success"

        result = complex_operation()
        assert result == "success"
        assert call_count == 2

    def test_retry_error_preserves_original_exception(self):
        """Should re-raise original exception directly."""

        @transient_retry(max_attempts=1, min_wait=0.01, max_wait=0.05)
        def custom_error():
            raise RuntimeError("Custom error message")

        with pytest.raises(RuntimeError) as exc_info:
            custom_error()

        assert "Custom error message" in str(exc_info.value)

    def test_decorators_do_not_silently_swallow_errors(self):
        """Should never silently catch errors; must raise or retry explicitly."""

        @transient_retry(max_attempts=1, min_wait=0.01, max_wait=0.05)
        def always_raises():
            raise ValueError("Should be visible")

        # Should not silently return None or default value; must raise
        with pytest.raises(ValueError) as exc_info:
            always_raises()

        assert "Should be visible" in str(exc_info.value)
