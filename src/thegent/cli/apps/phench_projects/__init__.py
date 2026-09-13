"""phench_projects CLI app module."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import typer


def register_projects_run(
    app: typer.Typer,
    list_targets_fn: Callable[..., Any] | None = None,
    list_modules_fn: Callable[..., Any] | None = None,
    load_target_lock_fn: Callable[..., Any] | None = None,
    target_timeline_fn: Callable[..., Any] | None = None,
    target_status_fn: Callable[..., Any] | None = None,
    lock_target_fn: Callable[..., Any] | None = None,
    materialize_target_fn: Callable[..., Any] | None = None,
    run_target_fn: Callable[..., Any] | None = None,
    build_matrix_fn: Callable[..., Any] | None = None,
    audit_shared_modules_fn: Callable[..., Any] | None = None,
) -> None:
    """Register projects run commands with the given app."""


__all__ = ["register_projects_run"]
