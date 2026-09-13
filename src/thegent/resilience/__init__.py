"""Resilience decorators for retrying operations.

Provides unified retry decorators using tenacity:
- transient_retry: for transient errors (network, 502/503, rate limits)
- cas_retry: for Compare-And-Swap operations with ValueError collision detection
- http_retry: for HTTP calls with status-code-based retry
- user_input_retry: for user input validation
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterable

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
)

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def transient_retry(
    max_attempts: int = 3,
    min_wait: float = 0.1,
    max_wait: float = 10.0,
) -> Callable[[F], F]:
    """Retry decorator for transient errors (network, 502/503, rate limits).

    Retries on common transient exceptions like ConnectionError, TimeoutError,
    OSError, and HTTP 502/503/504 errors.

    Args:
        max_attempts: Maximum number of retry attempts.
        min_wait: Minimum wait time between retries in seconds.
        max_wait: Maximum wait time between retries in seconds.

    Returns:
        A decorator that wraps functions with transient error retry logic.
    """
    # Transient exception types to retry on
    transient_exceptions = (
        ConnectionError,
        TimeoutError,
        OSError,
        IOError,
    )

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except transient_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        wait_time = min(min_wait * (2 ** (attempt - 1)), max_wait)
                        logger.warning(
                            "Transient error on attempt %d/%d: %s. Retrying in %.2fs...",
                            attempt,
                            max_attempts,
                            e,
                            wait_time,
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            "Max retry attempts (%d) reached for transient error: %s",
                            max_attempts,
                            e,
                        )
                        raise
                except Exception:
                    # Re-raise non-transient exceptions immediately
                    raise

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry loop exited unexpectedly")

        return wrapper  # type: ignore[return-value]

    return decorator


def cas_retry(
    max_attempts: int = 3,
    base_delay: float = 0.1,
) -> Callable[[F], F]:
    """Retry decorator for Compare-And-Swap operations.

    Retries when a ValueError with "collision" message is raised,
    indicating the CAS operation failed due to concurrent modification.

    Args:
        max_attempts: Maximum number of retry attempts.
        base_delay: Base delay between retries in seconds (doubles each attempt).

    Returns:
        A decorator that wraps functions with CAS retry logic.
    """

    def _is_cas_collision(exc: Exception) -> bool:
        """Check if exception indicates a CAS collision."""
        if isinstance(exc, ValueError):
            msg = str(exc).lower()
            return "collision" in msg or "changed" in msg or "conflict" in msg
        return False

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except ValueError as e:
                    if _is_cas_collision(e):
                        last_exception = e
                        if attempt < max_attempts:
                            delay = base_delay * (2 ** (attempt - 1))
                            logger.debug(
                                "CAS collision on attempt %d/%d: %s. Retrying in %.2fs...",
                                attempt,
                                max_attempts,
                                e,
                                delay,
                            )
                            time.sleep(delay)
                        else:
                            logger.error(
                                "Max CAS retry attempts (%d) reached for collision: %s",
                                max_attempts,
                                e,
                            )
                            raise
                    else:
                        raise
                except Exception:
                    raise

            if last_exception:
                raise last_exception
            raise RuntimeError("CAS retry loop exited unexpectedly")

        return wrapper  # type: ignore[return-value]

    return decorator


def http_retry(
    max_attempts: int = 3,
    status_codes: Iterable[int] = (429, 502, 503, 504),
) -> Callable[[F], F]:
    """Retry decorator for HTTP calls with status-code-based retry.

    Retries on specified HTTP status codes (default: 429, 502, 503, 504)
    and network timeout exceptions.

    Args:
        max_attempts: Maximum number of retry attempts.
        status_codes: Iterable of HTTP status codes that should trigger a retry.

    Returns:
        A decorator that wraps functions with HTTP retry logic.
    """
    retry_codes = set(status_codes)

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(1, max_attempts + 1):
                result = fn(*args, **kwargs)

                # Check if result is a dict with status code
                if isinstance(result, dict):
                    status = result.get("status")
                    if status in retry_codes:
                        if attempt < max_attempts:
                            logger.warning(
                                "HTTP status %s on attempt %d/%d. Retrying...",
                                status,
                                attempt,
                                max_attempts,
                            )
                            time.sleep(attempt * 0.5)
                            continue
                        # Return the result (will be last attempt's result)
                        return result

                return result

            return result  # type: ignore[return-value]

        return wrapper  # type: ignore[return-value]

    return decorator


def user_input_retry(
    max_attempts: int = 3,
) -> Callable[[F], F]:
    """Retry decorator for user elicitation with validation.

    Retries on ValueError exceptions, assuming they indicate invalid
    user input that should be re-prompted.

    Args:
        max_attempts: Maximum number of retry attempts.

    Returns:
        A decorator that wraps functions with user input retry logic.
    """

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except ValueError as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.debug(
                            "Invalid user input on attempt %d/%d: %s. Reprompting...",
                            attempt,
                            max_attempts,
                            e,
                        )
                        # Short wait for interactive re-prompting
                        time.sleep(0.1)
                    else:
                        logger.error(
                            "Max user input retry attempts (%d) reached: %s",
                            max_attempts,
                            e,
                        )
                        raise
                except Exception:
                    # Re-raise non-ValueError exceptions immediately
                    raise

            if last_exception:
                raise last_exception
            raise RuntimeError("User input retry loop exited unexpectedly")

        return wrapper  # type: ignore[return-value]

    return decorator


__all__ = [
    "transient_retry",
    "cas_retry",
    "http_retry",
    "user_input_retry",
]
