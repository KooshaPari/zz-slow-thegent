"""AST governance checks for split e2e CLI test files."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPLIT_TEST_FILES = [
    REPO_ROOT / "tests" / "test_e2e_cli_core_a.py",
    REPO_ROOT / "tests" / "test_e2e_cli_core_b.py",
    REPO_ROOT / "tests" / "test_e2e_cli_aliases.py",
    REPO_ROOT / "tests" / "test_e2e_cli_overlays.py",
]
COMPAT_RUNNER_MODULE = "tests.e2e.cli_runner_compat"
FORBIDDEN_CLI_RUNNER_MODULES = {"click.testing", "typer.testing"}


def _parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _is_pytest_e2e_marker(decorator: ast.expr) -> bool:
    marker = decorator.func if isinstance(decorator, ast.Call) else decorator
    return (
        isinstance(marker, ast.Attribute)
        and marker.attr == "e2e"
        and isinstance(marker.value, ast.Attribute)
        and marker.value.attr == "mark"
        and isinstance(marker.value.value, ast.Name)
        and marker.value.value.id == "pytest"
    )


def _module_has_explicit_e2e_decorator(module: ast.Module) -> bool:
    for node in ast.walk(module):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and any(
            _is_pytest_e2e_marker(decorator) for decorator in node.decorator_list
        ):
            return True
    return False


def test_split_files_exist() -> None:
    for path in SPLIT_TEST_FILES:
        assert path.exists(), f"missing split e2e file: {path}"


def test_split_files_have_explicit_pytest_e2e_decorator() -> None:
    for path in SPLIT_TEST_FILES:
        module = _parse_module(path)
        assert _module_has_explicit_e2e_decorator(module), (
            f"{path} must contain at least one explicit @pytest.mark.e2e decorator"
        )


def test_split_files_do_not_directly_import_bare_cli_runner() -> None:
    for path in SPLIT_TEST_FILES:
        module = _parse_module(path)
        forbidden_imported_modules: set[str] = set()

        for node in ast.walk(module):
            if isinstance(node, ast.ImportFrom) and node.module in FORBIDDEN_CLI_RUNNER_MODULES:
                if any(alias.name == "CliRunner" for alias in node.names):
                    forbidden_imported_modules.add(node.module)

        assert not forbidden_imported_modules, (
            f"{path} directly imports CliRunner from disallowed modules: "
            + ", ".join(sorted(forbidden_imported_modules))
        )


def test_split_files_import_compat_cli_runner() -> None:
    for path in SPLIT_TEST_FILES:
        module = _parse_module(path)
        imports_compat = any(
            isinstance(node, ast.ImportFrom)
            and node.module == COMPAT_RUNNER_MODULE
            and any(alias.name == "CompatCliRunner" for alias in node.names)
            for node in ast.walk(module)
        )

        assert imports_compat, f"{path} must import CompatCliRunner from {COMPAT_RUNNER_MODULE}"
