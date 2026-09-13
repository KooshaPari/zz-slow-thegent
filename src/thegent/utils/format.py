"""Formatting utilities for thegent.

Common formatting functions for consistent output across the codebase.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def format_timestamp(ts: datetime | float | int, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a timestamp to string.

    Args:
        ts: datetime object or Unix timestamp
        fmt: strftime format string
    """
    if isinstance(ts, (int, float)):
        ts = datetime.fromtimestamp(ts, tz=UTC)
    return ts.strftime(fmt)


def format_duration(seconds: float) -> str:
    """Format seconds to human-readable duration.

    Args:
        seconds: Duration in seconds
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


def format_bytes(size: int) -> str:
    """Format bytes to human-readable size.

    Args:
        size: Size in bytes
    """
    size_value = float(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_value < 1024:
            return f"{size_value:.1f}{unit}"
        size_value /= 1024
    return f"{size_value:.1f}PB"


def format_number(n: int) -> str:
    """Format number with thousands separator.

    Args:
        n: Number to format
    """
    return f"{n:,}"


def format_percent(value: float, decimals: int = 1) -> str:
    """Format float as percentage.

    Args:
        value: Value between 0 and 1 (or 0 and 100)
        decimals: Number of decimal places
    """
    if value <= 1:
        value *= 100
    return f"{value:.{decimals}f}%"


def format_list(items: list[Any], max_items: int = 5, sep: str = ", ") -> str:
    """Format list with ellipsis if too long.

    Args:
        items: List of items
        max_items: Maximum items to show
        sep: Separator between items
    """
    if len(items) <= max_items:
        return sep.join(str(i) for i in items)
    shown = sep.join(str(i) for i in items[:max_items])
    remaining = len(items) - max_items
    return f"{shown}... +{remaining} more"


def truncate(s: str, max_len: int = 50, suffix: str = "...") -> str:
    """Truncate string to max length.

    Args:
        s: String to truncate
        max_len: Maximum length
        suffix: Suffix to add if truncated
    """
    if len(s) <= max_len:
        return s
    return s[: max_len - len(suffix)] + suffix


def format_bool(value: bool, true: str = "Yes", false: str = "No") -> str:
    """Format boolean as string.

    Args:
        value: Boolean value
        true: String for True
        false: String for False
    """
    return true if value else false


def format_table_row(columns: list[str], widths: list[int]) -> str:
    """Format a table row with fixed column widths.

    Args:
        columns: Column values
        widths: Column widths
    """
    parts = []
    for col, width in zip(columns, widths, strict=False):
        parts.append(str(col)[:width].ljust(width))
    return " | ".join(parts)
