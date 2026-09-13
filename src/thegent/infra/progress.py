"""Progress indicators and status updates for long-running operations.

This module provides utilities for displaying progress bars, spinners, and
status updates in a consistent, beautiful way.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

console = Console()


@contextmanager
def progress_context(
    description: str,
    total: int | None = None,
    show_eta: bool = True,
    show_speed: bool = False,
):
    """Context manager for progress tracking.

    Args:
        description: Description of the operation
        total: Total number of steps (None for indeterminate)
        show_eta: Show estimated time remaining
        show_speed: Show processing speed

    Example:
        >>> with progress_context("Processing files", total=100) as progress:
        ...     for i in range(100):
        ...         progress.update(1)
    """
    columns = [
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ]

    if show_eta:
        columns.append(TimeRemainingColumn())

    if show_speed:
        columns.append(TextColumn("[progress.speed]{task.speed:.2f}/s"))

    columns.append(TimeElapsedColumn())

    with Progress(*columns, console=console) as progress:
        _task = progress.add_task(description, total=total)
        yield progress


@contextmanager
def spinner_context(message: str):
    """Context manager for spinner display.

    Args:
        message: Message to display while spinning

    Example:
        >>> with spinner_context("Loading data..."):
        ...     time.sleep(2)
    """
    with console.status(f"[bold cyan]{message}[/bold cyan]", spinner="dots"):
        yield


@dataclass
class SpinnerThrottle:
    """Tracks the last Rich status update time to prevent visual flicker."""

    _last_update: float = 0.0
    _interval: float = 0.1

    def should_update(self) -> bool:
        """Return True if enough time has elapsed since the last update."""
        now = time.monotonic()
        if now - self._last_update >= self._interval:
            self._last_update = now
            return True
        return False


@contextmanager
def throttled_spinner(message: str, min_interval: float = 0.1):
    """Context manager that wraps spinner_context with rate-limiting.

    Only updates the Rich status display every ``min_interval`` seconds
    to prevent visual flicker on fast operations.  Yields a
    :class:`SpinnerThrottle` whose ``should_update()`` method gates
    re-rendering.

    Args:
        message: Message to display while spinning
        min_interval: Minimum seconds between display updates

    Example:
        >>> with throttled_spinner("Processing...", min_interval=0.2) as spin:
        ...     for item in fast_items():
        ...         if spin.should_update():
        ...             pass  # status auto-throttled
        ...         process(item)
    """
    throttle = SpinnerThrottle(_interval=min_interval)
    with console.status(f"[bold cyan]{message}[/bold cyan]", spinner="dots"):
        yield throttle


def print_status(message: str, status: str = "info") -> None:
    """Print a status message with appropriate styling.

    Args:
        message: Status message
        status: Status type (info, success, warning, error)

    Example:
        >>> print_status("Operation completed", "success")
    """
    icons = {
        "info": "[bold blue]ℹ[/bold blue]",
        "success": "[bold green]✓[/bold green]",
        "warning": "[bold yellow]⚠[/bold yellow]",
        "error": "[bold red]✗[/bold red]",
    }
    icon = icons.get(status, icons["info"])
    console.print(f"{icon} {message}")


def print_step(step: int, total: int, message: str) -> None:
    """Print a step indicator.

    Args:
        step: Current step number
        total: Total number of steps
        message: Step message

    Example:
        >>> print_step(1, 3, "Installing dependencies")
    """
    console.print(f"[bold cyan][{step}/{total}][/bold cyan] {message}")


def print_section(title: str) -> None:
    """Print a section header.

    Args:
        title: Section title

    Example:
        >>> print_section("Configuration")
    """
    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    console.print("[dim]" + "─" * len(title) + "[/dim]\n")


def measure_time(description: str):
    """Decorator to measure and display execution time.

    Args:
        description: Description of the operation

    Example:
        >>> @measure_time("Processing data")
        ... def process_data():
        ...     time.sleep(1)
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            with spinner_context(description):
                result = func(*args, **kwargs)
            elapsed = time.time() - start
            print_status(f"{description} completed in {elapsed:.2f}s", "success")
            return result

        return wrapper

    return decorator
