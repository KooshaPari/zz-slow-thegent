"""Governance checks for smoke suite runner usage."""

from __future__ import annotations

import ast
from pathlib import Path

SMOKE_TEST_PATH = Path(__file__).with_name("test_cli_surface_smoke.py")


def _parse() -> ast.Module:
    return ast.parse(SMOKE_TEST_PATH.read_text(encoding="utf-8"), filename=str(SMOKE_TEST_PATH))


def test_smoke_suite_imports_compat_cli_runner() -> None:
    module = _parse()
    has_compat_import = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "tests.e2e.cli_runner_compat"
        and any(alias.name == "CompatCliRunner" for alias in node.names)
        for node in ast.walk(module)
    )
    assert has_compat_import


def test_smoke_suite_does_not_import_bare_cli_runner() -> None:
    module = _parse()
    has_bare_import = any(
        isinstance(node, ast.ImportFrom)
        and node.module in {"typer.testing", "click.testing"}
        and any(alias.name == "CliRunner" for alias in node.names)
        for node in ast.walk(module)
    )
    assert not has_bare_import
