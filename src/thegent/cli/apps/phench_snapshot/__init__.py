"""Stub module for phench_snapshot CLI commands."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def register_snapshot_commands(
    app: Any,
    create_target_snapshot_fn: Callable[..., Any] | None = None,
    list_target_snapshots_fn: Callable[..., Any] | None = None,
    show_target_snapshot_fn: Callable[..., Any] | None = None,
    **kwargs: Any,
) -> None:
    """Register snapshot-related CLI commands."""


__all__ = ["register_snapshot_commands"]
