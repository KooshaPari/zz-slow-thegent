"""Agent helpers - Helper functions for agent operations.

This module provides utility functions for logging friction points, managing
work streams, and other agent-related tasks.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

__all__ = [
    "log_friction",
    "get_next_items",
    "update_work_stream",
    "run_quality_check",
    "read_config",
    "format_summary",
]


# Default path for friction log
DEFAULT_FRICTION_LOG = Path(__file__).parent.parent / "docs" / "research" / "FRICTION_LOG.md"


def log_friction(
    category: str,
    description: str,
    impact: str = "medium",
    *,
    task_id: str | None = None,
    friction_type: str = "general",
    location: str = "unknown",
    solution: str = "",
    priority: str = "P2",
    friction_log_path: Path | None = None,
) -> bool:
    """Log a DX/UX/AX friction point to FRICTION_LOG.md.

    Args:
        category: The friction category - must be 'dx', 'ux', or 'ax'.
        description: What friction was observed.
        impact: Impact level - 'low', 'medium', or 'high'.
        task_id: Section header in log; auto-generated if omitted.
        friction_type: Sub-type label (e.g. 'verbosity', 'complexity').
        location: File, function, or pattern where friction occurs.
        solution: Proposed fix; defaults to empty string (TBD).
        priority: Priority - 'P1' (blocking) or 'P2' (improvement).
        friction_log_path: Override path for testing.

    Returns:
        True on success, False on write failure.
    """
    valid_categories = {"dx", "ux", "ax"}
    if category.lower() not in valid_categories:
        return False

    # Auto-generate task_id if not provided
    if task_id is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        task_id = f"{category.lower()}-friction-{timestamp}"

    # Default solution to TBD if empty
    if not solution:
        solution = "TBD"

    log_path = friction_log_path or DEFAULT_FRICTION_LOG
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create log entry
    entry_lines = [
        f"### {task_id}",
        "",
        f"- **Category**: {category.upper()}",
        f"- **Description**: {description}",
        f"- **Impact**: {impact}",
        f"- **Type**: {friction_type}",
        f"- **Location**: {location}",
        f"- **Solution**: {solution}",
        f"- **Priority**: {priority}",
        f"- **Logged**: {timestamp_str}",
        "",
    ]

    entry_content = "\n".join(entry_lines)

    try:
        # Ensure parent directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if log file exists
        if log_path.exists():
            existing_content = log_path.read_text()

            # Check if this task_id already exists
            if f"### {task_id}" in existing_content:
                # Update existing entry
                pattern = rf"(### {re.escape(task_id)}.*?)(?=\n### |\n## |\Z)"
                match = re.search(pattern, existing_content, re.DOTALL)
                if match:
                    existing_content = (
                        existing_content[: match.start()] + entry_content + existing_content[match.end() :]
                    )
                else:
                    existing_content += "\n" + entry_content
            else:
                # Append new entry
                existing_content += "\n" + entry_content
        else:
            # Create new log file with header
            header = """# Friction Log

Log of developer experience (DX), user experience (UX), and agent experience (AX) friction points.

## Instructions

- Use `log_friction()` from `scripts/agent_helpers.py` to add entries.
- Categories: `dx` (developer), `ux` (user), `ax` (agent/experience).
- Priority: `P1` (blocking), `P2` (improvement).

---

"""
            existing_content = header + entry_content

        log_path.write_text(existing_content)
        return True

    except OSError:
        return False


def get_next_items(
    limit: int = 5,
    workstream_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Return the next actionable unclaimed items from WORK_STREAM.md.

    Args:
        limit: Maximum number of items to return.
        workstream_path: Override path to workstream file.

    Returns:
        List of item dictionaries with 'id', 'title', and 'depends' keys.
    """
    # Stub implementation
    return []


def update_work_stream(
    item_id: str,
    status: str,
    workstream_path: Path | None = None,
) -> bool:
    """Update an item's status in WORK_STREAM.md.

    Args:
        item_id: The item ID to update.
        status: New status - 'claimed', 'completed', etc.
        workstream_path: Override path to workstream file.

    Returns:
        True on success, False otherwise.
    """
    # Stub implementation
    return True


def run_quality_check(
    lint: bool = True,
    test: bool = True,
    timeout: int = 300,
) -> dict[str, Any]:
    """Run quality checks (lint and/or tests).

    Args:
        lint: Whether to run lint checks.
        test: Whether to run tests.
        timeout: Timeout in seconds.

    Returns:
        Dictionary with 'success', 'lint', 'test', and 'errors' keys.
    """
    # Stub implementation
    return {"success": True, "lint": {}, "test": {}, "errors": []}


def read_config(
    key: str,
    config_path: Path | None = None,
    default: Any = None,
) -> Any:
    """Read a configuration value.

    Args:
        key: The configuration key to read.
        config_path: Override path to config file.
        default: Default value if key not found.

    Returns:
        The configuration value or default.
    """
    # Stub implementation
    return default


def format_summary(
    items: list[dict[str, Any]],
    show_details: bool = False,
) -> str:
    """Format a summary of items.

    Args:
        items: List of items to summarize.
        show_details: Whether to include detailed information.

    Returns:
        Formatted summary string.
    """
    if not items:
        return "No items."

    count = len(items)
    plural = "s" if count != 1 else ""
    summary = f"**{count} item{plural}**"

    if show_details:
        lines = [summary, ""]
        for item in items:
            lines.append(f"- {item.get('title', 'Untitled')}")
        return "\n".join(lines)

    return summary


# Private helpers (not exported in __all__ but used by tests)
def _parse_work_stream(content: str) -> list[dict[str, Any]]:
    """Parse workstream markdown content into structured items.

    Args:
        content: The markdown content of WORK_STREAM.md.

    Returns:
        List of item dictionaries.
    """
    # Stub implementation
    return []
