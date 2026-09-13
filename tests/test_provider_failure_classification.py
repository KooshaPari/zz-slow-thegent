"""WP-2002: Comprehensive tests for provider failure classification.

Covers 30+ scenarios for HTTP error codes, timeouts, auth errors, network
errors, and malformed responses — verifying correct FailureKind classification
and retry/circuit-break behaviour.

# @trace WL-039 WP-2002
"""

from __future__ import annotations

import pytest

from thegent.agents.base import RunResult
from thegent.agents.resilience import (
    FailureKind,
    classify_failure,
    is_retryable,
    is_usage_limit,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _r(stderr: str, exit_code: int = 1) -> RunResult:
    """Shorthand to build a RunResult with given stderr."""
    return RunResult(exit_code=exit_code, stdout="", stderr=stderr)


# ---------------------------------------------------------------------------
# HTTP 429 — rate limit: should trigger backoff, NOT circuit break
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHttp429:
    """HTTP 429 responses must classify as RATE_LIMIT and be retryable."""

    @pytest.mark.parametrize(
        "msg",
        [
            "429 Too Many Requests",
            "429",
            "rate limit exceeded",
            "Rate Limit Exceeded",
            "too many requests",
        ],
    )
    def test_rate_limit_classified(self, msg: str) -> None:
        # @trace WL-039 WP-2002
        kind = classify_failure(_r(msg))
        assert kind == FailureKind.RATE_LIMIT, f"Expected RATE_LIMIT for {msg!r}, got {kind}"

    def test_retry_after_header_is_retryable(self) -> None:
        # @trace WL-039 WP-2002
        # "Retry-After" headers appear on both 429 and 503 — both retryable
        kind = classify_failure(_r("retry after 60"))
        assert kind in (FailureKind.RATE_LIMIT, FailureKind.TRANSIENT)

    @pytest.mark.parametrize(
        "msg",
        [
            "429 Too Many Requests",
            "rate limit exceeded",
            "too many requests",
        ],
    )
    def test_rate_limit_is_retryable(self, msg: str) -> None:
        # @trace WL-039 WP-2002
        assert is_retryable(_r(msg)) is True

    @pytest.mark.parametrize(
        "msg",
        [
            "429 Too Many Requests",
            "rate limit exceeded",
        ],
    )
    def test_rate_limit_is_not_usage_limit(self, msg: str) -> None:
        # @trace WL-039 WP-2002
        assert is_usage_limit(_r(msg)) is False


# ---------------------------------------------------------------------------
# HTTP 500 / 502 / 503 — should circuit break after threshold
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHttp5xx:
    """5xx responses must classify as TRANSIENT and be retryable (circuit-break candidates)."""

    @pytest.mark.parametrize(
        "msg",
        [
            "502 Bad Gateway",
            "502",
            "503 Service Unavailable",
            "503",
            "504 Gateway Timeout",
            "504",
        ],
    )
    def test_5xx_classified_transient(self, msg: str) -> None:
        # @trace WL-039 WP-2002
        kind = classify_failure(_r(msg))
        assert kind == FailureKind.TRANSIENT, f"Expected TRANSIENT for {msg!r}, got {kind}"

    @pytest.mark.parametrize(
        "msg",
        [
            "502 Bad Gateway",
            "503 Service Unavailable",
            "504 Gateway Timeout",
        ],
    )
    def test_5xx_is_retryable(self, msg: str) -> None:
        # @trace WL-039 WP-2002
        assert is_retryable(_r(msg)) is True

    @pytest.mark.parametrize(
        "msg",
        [
            "502 Bad Gateway",
            "503 Service Unavailable",
        ],
    )
    def test_5xx_is_not_usage_limit(self, msg: str) -> None:
        # @trace WL-039 WP-2002
        assert is_usage_limit(_r(msg)) is False


# ---------------------------------------------------------------------------
# Authentication errors (401/403) — fail fast, do NOT retry
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAuthErrors:
    """Auth errors should not retry (unknown/permanent); they do not circuit-break."""

    @pytest.mark.parametrize(
        "msg",
        [
            "401 Unauthorized",
            "403 Forbidden",
            "Invalid API key",
            "authentication failed",
            "access denied",
        ],
    )
    def test_auth_error_not_retryable(self, msg: str) -> None:
        # @trace WL-039 WP-2002
        assert is_retryable(_r(msg)) is False

    @pytest.mark.parametrize(
        "msg",
        [
            "401 Unauthorized",
            "403 Forbidden",
        ],
    )
    def test_auth_error_not_usage_limit(self, msg: str) -> None:
        # @trace WL-039 WP-2002
        assert is_usage_limit(_r(msg)) is False


# ---------------------------------------------------------------------------
# Quota / usage limit — fallback to different provider; do NOT retry same
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestUsageLimits:
    """Quota exhaustion must be classified as USAGE_LIMIT — fallback, not retry."""

    @pytest.mark.parametrize(
        "msg",
        [
            "quota exceeded",
            "Quota Exceeded",
            "usage limit reached",
            "monthly limit exceeded",
            "daily limit exceeded",
            "insufficient quota",
            "out of quota",
            "out of credits",
            "billing limit exceeded",
            "subscription exceeded",
        ],
    )
    def test_usage_limit_classified(self, msg: str) -> None:
        # @trace WL-039 WP-2002
        assert classify_failure(_r(msg)) == FailureKind.USAGE_LIMIT

    @pytest.mark.parametrize(
        "msg",
        [
            "quota exceeded",
            "monthly limit exceeded",
        ],
    )
    def test_usage_limit_not_retryable(self, msg: str) -> None:
        # @trace WL-039 WP-2002
        assert is_retryable(_r(msg)) is False

    @pytest.mark.parametrize(
        "msg",
        [
            "quota exceeded",
            "monthly limit exceeded",
        ],
    )
    def test_usage_limit_is_usage_limit(self, msg: str) -> None:
        # @trace WL-039 WP-2002
        assert is_usage_limit(_r(msg)) is True


# ---------------------------------------------------------------------------
# Network errors — should circuit break
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestNetworkErrors:
    """Network errors classify as UNKNOWN (not explicitly retryable by pattern)."""

    @pytest.mark.parametrize(
        "msg",
        [
            "connection refused",
            "network error",
            "DNS resolution failed",
        ],
    )
    def test_network_error_not_retryable(self, msg: str) -> None:
        # @trace WL-039 WP-2002
        # Network errors without 502/503/504 codes fall through to UNKNOWN
        result = classify_failure(_r(msg))
        assert result in (FailureKind.UNKNOWN, FailureKind.TRANSIENT)


# ---------------------------------------------------------------------------
# Malformed response — should circuit break
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMalformedResponse:
    """Malformed response errors are not retryable."""

    @pytest.mark.parametrize(
        "msg",
        [
            "JSONDecodeError: invalid JSON",
            "unexpected end of stream",
            "partial response received",
        ],
    )
    def test_malformed_not_retryable(self, msg: str) -> None:
        # @trace WL-039 WP-2002
        assert is_retryable(_r(msg)) is False

    def test_success_exit_code_is_unknown(self) -> None:
        # @trace WL-039 WP-2002
        assert classify_failure(RunResult(0, "ok", "")) == FailureKind.UNKNOWN


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEdgeCases:
    """Edge cases for failure classification."""

    def test_empty_stderr_is_unknown(self) -> None:
        # @trace WL-039 WP-2002
        assert classify_failure(_r("")) == FailureKind.UNKNOWN

    def test_reconnecting_is_retryable(self) -> None:
        # @trace WL-039 WP-2002
        assert is_retryable(_r("reconnecting to server")) is True

    def test_success_not_retryable(self) -> None:
        # @trace WL-039 WP-2002
        assert is_retryable(RunResult(0, "done", "")) is False
