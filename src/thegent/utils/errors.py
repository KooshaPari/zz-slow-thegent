"""Error handling utilities for thegent.

Common error handling patterns and custom exceptions.
"""

from __future__ import annotations

import logging
import traceback
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ThegentError(Exception):
    """Base exception for thegent."""


class ConfigurationError(ThegentError):
    """Configuration-related errors."""


class NetworkError(ThegentError):
    """Network-related errors."""


class AuthenticationError(ThegentError):
    """Authentication errors."""


class TimeoutError(ThegentError):
    """Timeout errors."""


class ValidationError(ThegentError):
    """Validation errors."""


class NotFoundError(ThegentError):
    """Resource not found errors."""


class RateLimitError(ThegentError):
    """Rate limiting errors."""


def handle_error(
    error: Exception,
    context: str = "",
    reraise: bool = True,
    log_level: str = "error",
) -> None:
    """Handle an error with consistent logging.

    Args:
        error: The exception that occurred
        context: Additional context about where the error occurred
        reraise: Whether to re-raise the exception after handling
        log_level: Logging level (debug, info, warning, error, critical)
    """
    msg = f"{context}: {error}" if context else str(error)
    getattr(logger, log_level.lower())(msg)
    logger.debug(traceback.format_exc())

    if reraise:
        raise error


def safe_execute[T](
    func: Callable[..., T],
    *args: Any,
    default: T | None = None,
    log_errors: bool = True,
    **kwargs: Any,
) -> T | None:
    """Execute a function safely, returning default on error.

    Args:
        func: Function to execute
        *args: Positional arguments for func
        default: Default value to return on error
        log_errors: Whether to log errors
        **kwargs: Keyword arguments for func

    Returns:
        Result of func or default on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error("safe_execute failed: %s", e)
        return default


def suppress_errors[T](
    default: T | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that suppresses errors and returns default.

    Args:
        default: Default value to return on error

    Example:
        @suppress_errors(default=[])
        def get_items():
            raise ValueError("test")
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception:
                return default  # type: ignore

        return wrapper

    return decorator


def wrap_errors(
    new_exception: type[Exception],
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that wraps errors in a new exception type.

    Args:
        new_exception: Exception type to wrap with

    Example:
        @wrap_errors(NetworkError)
        def fetch_url(url: str) -> str:
            raise ValueError("invalid")
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                raise new_exception(str(e)) from e

        return wrapper

    return decorator


class ErrorContext:
    """Context manager for error handling."""

    def __init__(
        self,
        context: str,
        reraise: bool = True,
        log_level: str = "error",
    ):
        self.context = context
        self.reraise = reraise
        self.log_level = log_level
        self.error: Exception | None = None

    def __enter__(self) -> ErrorContext:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if exc_val is not None:
            self.error = exc_val
            handle_error(exc_val, self.context, self.reraise, self.log_level)
        return self.reraise  # Suppress if reraise=False
