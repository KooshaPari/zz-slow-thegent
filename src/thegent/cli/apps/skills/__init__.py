"""Skills CLI module."""

from __future__ import annotations

from typing import Any

__all__ = ["skills_list", "skills_select", "skills_show"]


async def skills_list() -> list[str]:
    """List available skills."""
    return []


async def skills_select(skill_name: str) -> dict[str, Any]:
    """Select a skill."""
    return {"name": skill_name, "selected": True}


async def skills_show(skill_name: str) -> dict[str, Any]:
    """Show skill details."""
    return {"name": skill_name, "description": ""}
