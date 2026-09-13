"""Stub module."""

from __future__ import annotations

from enum import StrEnum


class FailureMode(StrEnum):
    """Failure modes for orchestration."""

    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    AUTH_FAILURE = "auth_failure"
    UNKNOWN = "unknown"
    RETRY = "retry"
    FALLBACK = "fallback"
    FAIL = "fail"
    CIRCUIT_BREAK = "circuit_break"


def classify_failure(message: str) -> FailureMode:
    """Classify a failure message and return the appropriate failure mode."""
    msg_lower = message.lower()
    if "timeout" in msg_lower or "timed out" in msg_lower:
        return FailureMode.TIMEOUT
    if "rate limit" in msg_lower or "429" in msg_lower:
        return FailureMode.RATE_LIMIT
    if "401" in msg_lower or "unauthorized" in msg_lower or "auth" in msg_lower:
        return FailureMode.AUTH_FAILURE
    return FailureMode.UNKNOWN


__all__ = ["FailureMode", "classify_failure"]
