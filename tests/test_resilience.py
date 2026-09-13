"""Tests for agent retry/resilience logic."""

import pytest

from thegent.agents.base import RunResult
from thegent.agents.resilience import (
    FailureKind,
    TransientAgentError,
    UsageLimitError,
    classify_failure,
    is_retryable,
    is_usage_limit,
    with_retry,
)


@pytest.mark.unit
class TestResilience:
    """Tests for agent retry/resilience logic."""

    def test_classify_usage_limit(self) -> None:
        # @trace FR-AGT-009
        assert classify_failure(RunResult(1, "", "quota exceeded")) == FailureKind.USAGE_LIMIT
        assert classify_failure(RunResult(1, "", "usage limit reached")) == FailureKind.USAGE_LIMIT
        assert classify_failure(RunResult(1, "", "monthly limit exceeded")) == FailureKind.USAGE_LIMIT

    def test_classify_rate_limit(self) -> None:
        # @trace FR-AGT-009
        assert classify_failure(RunResult(1, "", "429 Too Many Requests")) == FailureKind.RATE_LIMIT
        assert classify_failure(RunResult(1, "", "rate limit exceeded")) == FailureKind.RATE_LIMIT

    def test_classify_transient(self) -> None:
        # @trace FR-AGT-009
        assert classify_failure(RunResult(1, "", "502 Bad Gateway")) == FailureKind.TRANSIENT
        assert classify_failure(RunResult(1, "", "503 Service Unavailable")) == FailureKind.TRANSIENT

    def test_is_usage_limit(self) -> None:
        # @trace FR-AGT-009
        assert is_usage_limit(RunResult(1, "", "quota exceeded")) is True
        assert is_usage_limit(RunResult(1, "", "429 rate limit")) is False

    def test_is_retryable_rate_limit(self) -> None:
        # @trace FR-AGT-009
        assert is_retryable(RunResult(1, "", "429 Too Many Requests")) is True
        assert is_retryable(RunResult(1, "", "rate limit exceeded")) is True

    def test_is_retryable_not_usage_limit(self) -> None:
        # @trace FR-AGT-009
        assert is_retryable(RunResult(1, "", "quota exceeded")) is False

    def test_is_retryable_gateway(self) -> None:
        # @trace FR-AGT-009
        assert is_retryable(RunResult(1, "", "502 Bad Gateway")) is True
        assert is_retryable(RunResult(1, "", "503 Service Unavailable")) is True
        assert is_retryable(RunResult(1, "", "504 Gateway Timeout")) is True

    def test_is_retryable_success_not_retryable(self) -> None:
        # @trace FR-AGT-009
        assert is_retryable(RunResult(0, "ok", "")) is False

    def test_is_retryable_unknown_provider_not_retryable(self) -> None:
        # @trace FR-AGT-009
        # Config/routing errors are not retryable
        assert is_retryable(RunResult(1, "", "unknown provider for model")) is False

    def test_usage_limit_error_holds_result(self) -> None:
        # @trace FR-AGT-009
        r = RunResult(1, "", "quota exceeded")
        e = UsageLimitError(r, agent="glm")
        assert e.result is r
        assert e.agent == "glm"

    def test_transient_agent_error_holds_result(self) -> None:
        # @trace FR-AGT-009
        r = RunResult(1, "", "429 rate limit")
        e = TransientAgentError(r)
        assert e.result is r
        assert e.result.exit_code == 1

    def test_with_retry_retries_on_transient(self) -> None:
        # @trace FR-AGT-009
        attempts = [0]

        @with_retry(max_attempts=3, min_wait=0.01, max_wait=0.05)
        def flaky() -> str:
            attempts[0] += 1
            if attempts[0] < 2:
                raise TransientAgentError(RunResult(1, "", "429"))
            return "ok"

        assert flaky() == "ok"
        assert attempts[0] == 2

    def test_with_retry_returns_last_result_after_exhausted(self) -> None:
        # @trace FR-AGT-009
        @with_retry(max_attempts=2, min_wait=0.01, max_wait=0.05)
        def always_fail() -> str:
            raise TransientAgentError(RunResult(1, "", "429"))

        with pytest.raises(TransientAgentError) as exc_info:
            always_fail()
        assert exc_info.value.result.exit_code == 1
        assert "429" in exc_info.value.result.stderr
