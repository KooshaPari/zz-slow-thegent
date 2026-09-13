"""CLI helper functions for process management and retry logic.

This module provides runtime helpers for CLI operations including
subprocess spawning, retry logic, and file operations.
"""

from __future__ import annotations

import errno
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

# EAGAIN/EWOULDBLOCK errno numbers for retry logic
_EAGAIN_ERRNOS = {errno.EAGAIN, errno.EWOULDBLOCK, errno.EINTR}


def retry_if_eagain(func: Any) -> Any:
    """Retry function if EAGAIN error occurs.

    Decorator that retries a function up to 3 times if an OSError
    with EAGAIN, EWOULDBLOCK, or EINTR errno is raised.

    Args:
        func: Function to wrap with retry logic.

    Returns:
        Wrapped function with retry behavior.
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except OSError as e:
                if e.errno in _EAGAIN_ERRNOS and attempt < max_retries - 1:
                    time.sleep(0.1 * (2**attempt))
                    continue
                raise
        return None

    return wrapper


def backoff_delay(attempt: int, base: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate exponential backoff delay.

    Args:
        attempt: Current retry attempt number (0-indexed).
        base: Base delay in seconds.
        max_delay: Maximum delay in seconds.

    Returns:
        Calculated delay in seconds.
    """
    return min(base * (2**attempt), max_delay)


def atomic_write(path: Path | str, content: str) -> None:
    """Atomically write content to a file.

    Uses a temporary file and atomic rename to ensure the file
    is either fully written or not modified at all.

    Args:
        path: Target file path.
        content: Content to write.
    """
    path_str = str(path)
    dir_path = str(Path(path_str).parent) or "."
    with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=dir_path) as f:
        f.write(content)
        temp_path = f.name
    os.rename(temp_path, path_str)


def spawn_with_eagain_retry(
    cmd: list[str], **kwargs: Any
) -> subprocess.CompletedProcess:
    """Spawn process with EAGAIN retry logic.

    Runs a subprocess with retry logic for EAGAIN errors,
    which can occur with file descriptors on certain systems.

    Args:
        cmd: Command and arguments to run.
        **kwargs: Additional arguments passed to subprocess.run.

    Returns:
        CompletedProcess instance with result.

    Raises:
        OSError: If a non-retryable error occurs.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return subprocess.run(cmd, **kwargs)
        except OSError as e:
            if e.errno in _EAGAIN_ERRNOS and attempt < max_retries - 1:
                time.sleep(0.1 * (2**attempt))
                continue
            raise
    return None


def is_pid_running(pid: int) -> bool:
    """Check whether a process with the given PID is still running.

    Uses ``os.kill(pid, 0)`` which sends no signal but checks whether
    the process exists and the caller has permission.

    Args:
        pid: Process ID to check.

    Returns:
        True if the process is running, False otherwise.
    """
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def resolve_safe_path(path: Path | str | None) -> Path | None:
    """Resolve and validate a path safely.

    Args:
        path: Path to resolve, or None.

    Returns:
        Resolved Path or None if path is None or doesn't exist.
    """
    if path is None:
        return None
    resolved = Path(path).expanduser().resolve()
    if resolved.exists():
        return resolved
    return None
