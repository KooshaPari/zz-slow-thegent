"""Unit tests for E2E command-surface helpers."""

from __future__ import annotations

from typing import cast

import pytest
import typer

from tests.e2e.command_surface import command_path_exists


@pytest.fixture
def sample_app() -> typer.Typer:
    app = typer.Typer()
    plan_app = typer.Typer()
    reports_app = typer.Typer()

    @app.command("run")
    def run_cmd() -> None:
        pass

    @plan_app.command("status")
    def status_cmd() -> None:
        pass

    @reports_app.command("daily")
    def daily_cmd() -> None:
        pass

    plan_app.add_typer(reports_app, name="reports")
    app.add_typer(plan_app, name="plan")
    return app


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ([], True),
        ((), True),
        (["run"], True),
        (("run",), True),
        (["plan", "status"], True),
        (("plan", "status"), True),
        (["plan", "status", "extra"], False),
        (["plan", "missing"], False),
        (["missing"], False),
        (["run", "missing"], False),
    ],
)
def test_command_path_exists(sample_app: typer.Typer, path: tuple[str, ...] | list[str], expected: bool) -> None:
    assert command_path_exists(sample_app, path) is expected


def test_command_path_exists_non_group_intermediate_segment(sample_app: typer.Typer) -> None:
    assert command_path_exists(sample_app, ["run", "extra"]) is False


def test_command_path_exists_deep_nested_group_path(sample_app: typer.Typer) -> None:
    assert command_path_exists(sample_app, ["plan", "reports", "daily"]) is True


def test_command_path_exists_non_string_segment_returns_false(
    sample_app: typer.Typer,
) -> None:
    path = cast("list[str]", ["plan", 1])
    assert command_path_exists(sample_app, path) is False
