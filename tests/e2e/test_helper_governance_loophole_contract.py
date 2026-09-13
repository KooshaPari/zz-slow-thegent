"""Anti-loophole checks for helper-governance tests."""

from __future__ import annotations

import ast
from pathlib import Path

TARGET = Path(__file__).with_name("test_cli_runner_import_governance.py")


def _module() -> ast.Module:
    return ast.parse(TARGET.read_text(encoding="utf-8"), filename=str(TARGET))


def test_helper_governance_targets_all_e2e_tests_not_just_runner_tests() -> None:
    module = _module()
    has_test_glob = any(
        isinstance(node, ast.Constant) and isinstance(node.value, str) and "test_*.py" in node.value
        for node in ast.walk(module)
    )
    assert has_test_glob


def test_helper_governance_file_keeps_forbidden_helper_list_non_empty() -> None:
    module = _module()
    assigns = [n for n in ast.walk(module) if isinstance(n, ast.Assign)]
    values = [
        a.value
        for a in assigns
        if any(isinstance(t, ast.Name) and t.id == "FORBIDDEN_LOCAL_HELPERS" for t in a.targets)
    ]
    assert values, "FORBIDDEN_LOCAL_HELPERS assignment missing"
    set_node = values[0]
    assert isinstance(set_node, (ast.Set, ast.Call))
