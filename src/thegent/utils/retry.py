"""Common retry utilities for thegent.

Provides retry decorators and helpers with exponential backoff.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
P = ParamSpec("P")


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator that retries a function with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        exceptions: Tuple of exceptions to catch and retry
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = min(base_delay * (exponential_base**attempt), max_delay)
                        logger.warning(
                            "Retry %d/%d for %s after %.1fs: %s", attempt + 1, max_attempts, func.__name__, delay, e
                        )
                        time.sleep(delay)
            raise last_exception  # type: ignore

        return wrapper

    return decorator


def async_retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Async decorator that retries a function with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        exceptions: Tuple of exceptions to catch and retry
    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = min(base_delay * (exponential_base**attempt), max_delay)
                        logger.warning(
                            "Async retry %d/%d for %s after %.1fs: %s",
                            attempt + 1,
                            max_attempts,
                            func.__name__,
                            delay,
                            e,
                        )
                        await asyncio.sleep(delay)
            raise last_exception  # type: ignore

        return wrapper

    return decorator


def is_retryable_error(error: Exception) -> bool:
    """Determine if an error is retryable (network, timeout, etc.)."""
    error_name = type(error).__name__.lower()
    retryable_names = (
        "timeout",
        "connection",
        "network",
        "temporary",
        "unavailable",
        "too_many_requests",
        "rate_limit",
        "429",
        "500",
        "502",
        "503",
        "504",
    )
    return any(name in error_name for name in retryable_names)


class RetryContext:
    """Context manager for retry operations."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        on_retry: Callable[[int, Exception], None] | None = None,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.on_retry = on_retry
        self.attempt = 0
        self.last_error: Exception | None = None

    async def __aenter__(self) -> RetryContext:
        self.attempt += 1
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if exc_val is not None:
            self.last_error = exc_val
            if self.attempt < self.max_attempts and is_retryable_error(exc_val):
                delay = self.base_delay * (2 ** (self.attempt - 1))
                if self.on_retry:
                    self.on_retry(self.attempt, exc_val)
                logger.info("Retrying after %.1fs (attempt %d)", delay, self.attempt)
                await asyncio.sleep(delay)
                return True  # Suppress exception, will retry
        return False  # Don't suppress
