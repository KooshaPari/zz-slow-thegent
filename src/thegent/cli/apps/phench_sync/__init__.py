"""phench_sync CLI app module."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import typer


def register_sync_commands(
    app: typer.Typer,
    **kwargs: Any,
) -> None:
    """Register sync commands with the given app."""


__all__ = ["register_sync_commands"]
