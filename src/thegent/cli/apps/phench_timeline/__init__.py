"""phench_timeline CLI app module."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import typer


def register_timeline_commands(
    app: typer.Typer,
    target_timeline_fn: Callable[..., Any] | None = None,
    **kwargs: Any,
) -> None:
    """Register timeline commands with the given app."""


__all__ = ["register_timeline_commands"]
