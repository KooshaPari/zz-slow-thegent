from __future__ import annotations

import typer

from tests.e2e.cli_runner_compat import (
    ATTEMPTED_ARGV_COMMAND_PATH_PREFIX,
    COMMAND_SURFACE_DRIFT_SKIP_MESSAGE,
    _alias_rewrite_argv,
    _build_command_surface_drift_skip_message,
)


def test_build_command_surface_drift_skip_message_with_tuple_argv() -> None:
    message = _build_command_surface_drift_skip_message(None, ("logs", "x"))

    assert message == (f"{COMMAND_SURFACE_DRIFT_SKIP_MESSAGE} {ATTEMPTED_ARGV_COMMAND_PATH_PREFIX} logs x")


def test_build_command_surface_drift_skip_message_with_none_argv() -> None:
    message = _build_command_surface_drift_skip_message(None, None)

    assert message == (f"{COMMAND_SURFACE_DRIFT_SKIP_MESSAGE} {ATTEMPTED_ARGV_COMMAND_PATH_PREFIX} <unspecified>")


def test_build_command_surface_drift_skip_message_with_scalar_string_argv() -> None:
    message = _build_command_surface_drift_skip_message(None, "logs")

    assert message == (f"{COMMAND_SURFACE_DRIFT_SKIP_MESSAGE} {ATTEMPTED_ARGV_COMMAND_PATH_PREFIX} logs")


def test_alias_rewrite_argv_returns_none_when_app_is_not_typer() -> None:
    assert _alias_rewrite_argv(object(), ["logs"]) is None


def test_alias_rewrite_argv_returns_none_when_argv_is_not_list_or_tuple() -> None:
    app = typer.Typer()

    assert _alias_rewrite_argv(app, "logs") is None


def test_alias_rewrite_argv_returns_none_for_argumentful_alias() -> None:
    app = typer.Typer()

    assert _alias_rewrite_argv(app, ["logs", "x"]) is None


def test_alias_rewrite_argv_returns_none_when_target_command_path_missing() -> None:
    app = typer.Typer()
    run_app = typer.Typer()

    @run_app.command("status")
    def run_status() -> None:
        return None

    app.add_typer(run_app, name="run")

    assert _alias_rewrite_argv(app, ["logs"]) is None


def test_alias_rewrite_argv_returns_rewritten_list_for_exact_alias_when_target_exists() -> None:
    app = typer.Typer()
    run_app = typer.Typer()

    @run_app.command("logs")
    def run_logs() -> None:
        return None

    app.add_typer(run_app, name="run")

    assert _alias_rewrite_argv(app, ["logs"]) == ["run", "logs"]
