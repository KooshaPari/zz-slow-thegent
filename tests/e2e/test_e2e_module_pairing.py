"""Governance checks ensuring e2e utility modules have test coverage imports."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
E2E_DIR = REPO_ROOT / "tests" / "e2e"
UTILITY_MODULES = {
    "tests.e2e.cli_assertions": E2E_DIR / "cli_assertions.py",
    "tests.e2e.cli_runner_compat": E2E_DIR / "cli_runner_compat.py",
    "tests.e2e.command_surface": E2E_DIR / "command_surface.py",
}
TEST_FILES = sorted(E2E_DIR.glob("test_*.py"))


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imports_module(path: Path, module_name: str) -> bool:
    module = _parse(path)
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom) and node.module == module_name:
            return True
        if isinstance(node, ast.Import):
            if any(alias.name == module_name for alias in node.names):
                return True
    return False


def test_e2e_utility_modules_exist() -> None:
    for module_path in UTILITY_MODULES.values():
        assert module_path.exists(), f"missing e2e utility module: {module_path}"


def test_each_e2e_utility_module_has_at_least_one_importing_test() -> None:
    assert TEST_FILES, f"no e2e test files found under {E2E_DIR}"

    for module_name in UTILITY_MODULES:
        importing_tests = [path for path in TEST_FILES if _imports_module(path, module_name)]
        assert importing_tests, f"No tests import {module_name}; add at least one test_*.py that imports it."


def test_each_utility_module_has_a_dedicated_test_file() -> None:
    expected_test_files = {
        "tests.e2e.cli_assertions": E2E_DIR / "test_cli_assertions.py",
        "tests.e2e.cli_runner_compat": E2E_DIR / "test_cli_runner_compat.py",
        "tests.e2e.command_surface": E2E_DIR / "test_command_surface.py",
    }
    for module_name, expected_test_path in expected_test_files.items():
        assert expected_test_path.exists(), f"Missing dedicated test file for {module_name}: {expected_test_path}"
        assert _imports_module(expected_test_path, module_name), f"{expected_test_path} must import {module_name}"
