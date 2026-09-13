"""phench_run CLI app module."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import typer


def register_run_commands(
    app: typer.Typer,
    run_target_fn: Callable[..., Any] | None = None,
    target_status_fn: Callable[..., Any] | None = None,
    list_targets_fn: Callable[..., Any] | None = None,
    build_project_execution_matrix_fn: Callable[..., Any] | None = None,
    **kwargs: Any,
) -> None:
    """Register run commands with the given app."""


__all__ = ["register_run_commands"]
