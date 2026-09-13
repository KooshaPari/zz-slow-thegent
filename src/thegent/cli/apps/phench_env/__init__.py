"""CLI phench_env module.

This module provides CLI phench environment configuration.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def register_env_commands(
    app: object,
    run_env_doctor_for_target_fn: Callable[..., Any] | None = None,
    set_env_profile_fn: Callable[..., Any] | None = None,
    get_env_profile_fn: Callable[..., Any] | None = None,
    **kwargs: Any,
) -> None:
    """Register environment commands with the CLI app.

    Args:
        app: The CLI application to register commands with.
    """


__all__ = ["register_env_commands"]
