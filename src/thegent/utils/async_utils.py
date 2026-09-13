"""Async utilities for thegent.

Common async patterns and helpers.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def run_in_thread[T](func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a blocking function in a thread pool.

    Args:
        func: Synchronous function to run
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Result of func
    """
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))


async def gather_with_limit[T](
    *tasks: Awaitable[T],
    limit: int = 10,
) -> list[T]:
    """Run tasks with concurrency limit.

    Args:
        *tasks: Awaitable tasks
        limit: Maximum concurrent tasks

    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(limit)

    async def bounded_task(task: Awaitable[T]) -> T:
        async with semaphore:
            return await task

    return await asyncio.gather(*(bounded_task(t) for t in tasks))


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for retrying async functions.

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch

    Example:
        @async_retry(max_attempts=3, delay=1.0)
        async def fetch(url: str) -> str:
            ...
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        wait = delay * (backoff**attempt)
                        logger.warning(
                            "Retry %d/%d for %s after %.1fs: %s", attempt + 1, max_attempts, func.__name__, wait, e
                        )
                        await asyncio.sleep(wait)
            raise last_error  # type: ignore

        return wrapper

    return decorator


async def wait_for_all[T](
    tasks: list[Awaitable[T]],
    timeout: float | None = None,
) -> list[T]:
    """Wait for all tasks to complete with timeout.

    Args:
        tasks: List of awaitable tasks
        timeout: Timeout in seconds

    Returns:
        List of results

    Raises:
        asyncio.TimeoutError: If timeout exceeded
    """
    return await asyncio.wait_for(
        asyncio.gather(*tasks, return_exceptions=False),
        timeout=timeout,
    )


class AsyncBatch:
    """Batch processor for async operations."""

    def __init__(self, batch_size: int = 10, delay: float = 0.1):
        self.batch_size = batch_size
        self.delay = delay
        self.queue: list[Awaitable[Any]] = []

    async def add(self, task: Awaitable[T]) -> T:
        """Add a task to the batch."""
        self.queue.append(task)
        if len(self.queue) >= self.batch_size:
            await self.flush()
        return await task

    async def flush(self) -> list[T]:
        """Process all queued tasks."""
        if not self.queue:
            return []
        results = await asyncio.gather(*self.queue, return_exceptions=True)
        self.queue.clear()
        return results  # type: ignore
