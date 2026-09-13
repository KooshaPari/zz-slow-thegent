"""CLI helpers for thegent.

Common CLI utilities for output formatting, user interaction, and progress tracking.
"""

from __future__ import annotations

import sys
from typing import Any


def print_error(msg: str) -> None:
    """Print error to stderr."""


def print_warning(msg: str) -> None:
    """Print warning to stdout."""


def print_success(msg: str) -> None:
    """Print success message to stdout."""


def print_info(msg: str) -> None:
    """Print info message to stdout."""


def confirm(prompt: str, default: bool = False) -> bool:
    """Ask for confirmation."""
    suffix = " [Y/n]" if default else "[y/N]"
    response = input(f"{prompt}{suffix}: ").strip().lower()
    if not response:
        return default
    return response in ("y", "yes")


def progress_bar(current: int, total: int, width: int = 40) -> str:
    """Create a progress bar string."""
    percent = 0.0 if total == 0 else current / total
    filled = int(width * percent)
    bar = "=" * filled + "-" * (width - filled)
    return f"[{bar}] {int(percent * 100)}%"


def format_bytes(num_bytes: int) -> str:
    """Format bytes into human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"
