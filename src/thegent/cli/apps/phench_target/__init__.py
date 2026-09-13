"""phench_target CLI app module."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import typer


def register_target_commands(
    app: typer.Typer,
    init_target_fn: Callable[..., Any] | None = None,
    bootstrap_target_fn: Callable[..., Any] | None = None,
    import_repos_fn: Callable[..., Any] | None = None,
    add_repo_fn: Callable[..., Any] | None = None,
    set_repo_ref_fn: Callable[..., Any] | None = None,
    lock_target_fn: Callable[..., Any] | None = None,
    materialize_target_fn: Callable[..., Any] | None = None,
    add_module_to_target_fn: Callable[..., Any] | None = None,
    sync_target_fn: Callable[..., Any] | None = None,
    **kwargs: Any,
) -> None:
    """Register target commands with the given app."""


__all__ = ["register_target_commands"]
