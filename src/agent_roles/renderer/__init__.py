"""Stub module."""

from __future__ import annotations

from typing import Any


class RoleRenderer:
    """Renders agent roles."""

    def render(self, role: str) -> str:
        """Render a role to string."""
        return f"<role:{role}>"


__all__ = ["RoleRenderer"]
