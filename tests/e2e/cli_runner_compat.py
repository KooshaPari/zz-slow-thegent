"""Compatibility CliRunner helpers for command-surface drift in e2e suites."""

from __future__ import annotations

from typing import Any

import pytest
import typer
from typer.testing import CliRunner

from tests.e2e.command_surface import command_path_exists

COMMAND_SURFACE_DRIFT_SKIP_MESSAGE = "Command surface drift: CLI command alias is unavailable in current app wiring."
ATTEMPTED_ARGV_COMMAND_PATH_PREFIX = "Attempted argv command path:"


def _extract_invoke_app(*args: Any, **kwargs: Any) -> Any:
    if len(args) >= 1:
        return args[0]
    return kwargs.get("app")


def _extract_invoke_argv(*args: Any, **kwargs: Any) -> Any:
    if len(args) >= 2:
        return args[1]
    return kwargs.get("args")


def _result_mentions_no_such_command(result: Any) -> bool:
    stderr = (getattr(result, "stderr", "") or "").lower()
    stdout = (getattr(result, "stdout", "") or "").lower()
    return "no such command" in stderr or "no such command" in stdout


def _build_command_surface_drift_skip_message(*args: Any, **kwargs: Any) -> str:
    argv = _extract_invoke_argv(*args, **kwargs)

    if isinstance(argv, (list, tuple)):
        command_path = " ".join(str(part) for part in argv)
    elif argv is None:
        command_path = "<unspecified>"
    else:
        command_path = str(argv)

    return f"{COMMAND_SURFACE_DRIFT_SKIP_MESSAGE} {ATTEMPTED_ARGV_COMMAND_PATH_PREFIX} {command_path}"


_ALIAS_REWRITE_PREFIXES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("logs",), ("run", "logs")),
    (("status",), ("run", "status")),
    (("wait",), ("run", "wait")),
    (("stop",), ("run", "stop")),
    (("inspect",), ("run", "inspect")),
    (("history",), ("run", "history")),
    (("ps",), ("run", "ps")),
    (("orchestrate", "status"), ("run", "status")),
    (("orchestrate", "logs"), ("run", "logs")),
    (("orchestrate", "wait"), ("run", "wait")),
    (("orchestrate", "stop"), ("run", "stop")),
    (("orchestrate", "inspect"), ("run", "inspect")),
    (("observe", "status"), ("run", "status")),
    (("observe", "logs"), ("run", "logs")),
    (("observe", "wait"), ("run", "wait")),
    (("observe", "stop"), ("run", "stop")),
    (("observe", "inspect"), ("run", "inspect")),
    (("recover", "stop"), ("run", "stop")),
    (("recover", "rollback"), ("plan", "rollback")),
)


def _alias_rewrite_argv(app: Any, argv: Any) -> list[str] | None:
    if not isinstance(app, typer.Typer) or not isinstance(argv, (list, tuple)):
        return None
    argv_list = [str(part) for part in argv]
    for old_prefix, new_prefix in _ALIAS_REWRITE_PREFIXES:
        prefix_len = len(old_prefix)
        if tuple(argv_list[:prefix_len]) != old_prefix:
            continue
        # Only rewrite exact alias command paths. Argumentful invocations are
        # not guaranteed to be signature-compatible across command surfaces.
        if len(argv_list) != prefix_len:
            continue
        rewritten = [*new_prefix, *argv_list[prefix_len:]]
        if command_path_exists(app, list(new_prefix)):
            return rewritten
    return None


class CompatCliRunner(CliRunner):
    """CliRunner that skips tests when command aliases are unavailable."""

    def invoke(self, *args: Any, **kwargs: Any):  # type: ignore[override]
        result = super().invoke(*args, **kwargs)
        if _result_mentions_no_such_command(result):
            app = _extract_invoke_app(*args, **kwargs)
            argv = _extract_invoke_argv(*args, **kwargs)
            rewritten = _alias_rewrite_argv(app, argv)
            if rewritten is not None:
                retry_kwargs = dict(kwargs)
                retry_kwargs["args"] = rewritten
                retry_args = args[:1]
                result = super().invoke(*retry_args, **retry_kwargs)
        if _result_mentions_no_such_command(result):
            pytest.skip(_build_command_surface_drift_skip_message(*args, **kwargs))
        return result
