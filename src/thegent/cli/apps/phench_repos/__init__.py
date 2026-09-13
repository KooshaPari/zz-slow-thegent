"""Stub module for phench_repos CLI commands."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any


def register_repos_commands(
    app: Any,
    discover_repos_fn: Callable[..., Any] | None = None,
    **kwargs: Any,
) -> None:
    """Register repos-related CLI commands."""


__all__ = ["register_repos_commands"]
