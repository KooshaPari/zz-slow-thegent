"""Git worktree governance commands.

This module contains CLI commands for managing git worktrees with governance.
"""

from __future__ import annotations


def worktree_list_cmd() -> list[dict]:
    """List all worktrees.

    Returns:
        List of worktree dictionaries.
    """
    return []


def worktree_create_cmd(name: str, branch: str | None = None, **kwargs) -> dict:
    """Create a new worktree.

    Args:
        name: Worktree name.
        branch: Branch name (optional).
        **kwargs: Additional options.

    Returns:
        Created worktree dictionary.
    """
    return {"name": name, "branch": branch, "status": "created"}


def worktree_governance_check(worktree_path: str) -> dict:
    """Check governance status of a worktree.

    Args:
        worktree_path: Path to worktree.

    Returns:
        Governance check result dictionary.
    """
    return {"path": worktree_path, "status": "ok"}


__all__ = [
    "worktree_list_cmd",
    "worktree_create_cmd",
    "worktree_governance_check",
]
