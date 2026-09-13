"""Stub module."""

from collections.abc import Callable
from typing import Any


def register_modules_commands(
    app: Any,
    audit_shared_modules_fn: Callable[..., Any] | None = None,
    list_modules_fn: Callable[..., Any] | None = None,
    sync_project_modules_from_repos_fn: Callable[..., Any] | None = None,
    audit_shared_modules_across_repos_fn: Callable[..., Any] | None = None,
    **kwargs: Any,
) -> None:
    """Register module-related commands."""


__all__ = ["register_modules_commands"]
