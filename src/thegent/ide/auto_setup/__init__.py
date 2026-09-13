"""Stub module."""

from typing import Any


def auto_setup_ghostty_shell_integration() -> dict[str, Any]:
    """Auto setup ghostty shell integration."""
    return {"configured": True, "shell": "bash"}


__all__ = ["auto_setup_ghostty_shell_integration"]
