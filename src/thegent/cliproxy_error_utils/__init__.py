"""CLIProxy error utilities.

This module provides error handling utilities for the CLIProxy adapter,
including error message constants, retry logic, and custom exception classes.
"""

from __future__ import annotations

from typing import Any

# Error message constants
_ERROR_MESSAGES: dict[str, str] = {
    "insufficient_credits": "Insufficient credits to process this request.",
    "rate_limited": "Rate limit exceeded. Please retry later.",
    "server_error": "Internal server error. Please try again.",
    "timeout": "Request timed out.",
    "invalid_request": "Invalid request parameters.",
    "unauthorized": "Unauthorized. Please check your credentials.",
    "not_found": "Resource not found.",
    "service_unavailable": "Service is currently unavailable.",
}

_RETRY_MAX_ATTEMPTS: int = 3


class _RetryableStreamError(Exception):
    """Error raised when a stream operation should be retried."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class InsufficientCreditsError(Exception):
    """Error raised when there are insufficient credits for an operation."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or _ERROR_MESSAGES.get("insufficient_credits", "Insufficient credits."))


def _make_error_body(error: Exception, status_code: int | None = None) -> dict[str, Any]:
    """Create a standardized error response body.

    Args:
        error: The exception that occurred.
        status_code: Optional HTTP status code.

    Returns:
        Error body dictionary.
    """
    error_type = type(error).__name__
    message = str(error) or _ERROR_MESSAGES.get("server_error", "An error occurred.")

    body: dict[str, Any] = {
        "error": {
            "type": error_type,
            "message": message,
        }
    }

    if status_code is not None:
        body["error"]["status_code"] = status_code

    return body


def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable.

    Args:
        error: The exception to check.

    Returns:
        True if the error should trigger a retry.
    """
    if isinstance(error, _RetryableStreamError):
        return True

    error_messages = (
        _ERROR_MESSAGES.get("timeout", ""),
        _ERROR_MESSAGES.get("rate_limited", ""),
        _ERROR_MESSAGES.get("server_error", ""),
        _ERROR_MESSAGES.get("service_unavailable", ""),
    )

    return any(msg in str(error) for msg in error_messages)


def get_error_message(error_key: str) -> str:
    """Get an error message by key.

    Args:
        error_key: The error message key.

    Returns:
        The error message or a default message if not found.
    """
    return _ERROR_MESSAGES.get(error_key, "An unexpected error occurred.")


__all__ = [
    "_ERROR_MESSAGES",
    "_RETRY_MAX_ATTEMPTS",
    "_RetryableStreamError",
    "InsufficientCreditsError",
    "_make_error_body",
    "is_retryable_error",
    "get_error_message",
]
