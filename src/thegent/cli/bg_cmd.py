"""thegent.cli.bg_cmd - CLI background command module.

This module provides the bg (background) command for thegent CLI.
"""

from __future__ import annotations

from typing import Any


def bg_cmd(
    model: str | None = None,
    prompt: str | None = None,
    cwd: str | None = None,
    remote: str | None = None,
    **kwargs: Any,
) -> int:
    """Execute the background command.

    Args:
        model: Model to use
        prompt: Prompt for the model
        cwd: Working directory
        remote: Remote execution target
        **kwargs: Additional arguments

    Returns:
        Exit code (0 for success)
    """
    # Stub implementation - actual logic would be in impl.py
    return 0
