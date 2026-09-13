"""Exact-set equality contracts for governance registry and README bundle."""

from __future__ import annotations

import re
from pathlib import Path

from tests.e2e.test_split_hygiene import (
    REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND,
    REQUIRED_E2E_GOVERNANCE_FILES,
)

README_PATH = Path(__file__).with_name("README.md")
REPO_ROOT = README_PATH.parents[2]


def _bundle_paths_from_constant() -> set[str]:
    return {
        token
        for token in REQUIRED_E2E_GOVERNANCE_BUNDLE_COMMAND.split()
        if token.startswith("tests/") and token.endswith(".py")
    }


def _bundle_paths_from_readme() -> set[str]:
    text = README_PATH.read_text(encoding="utf-8")
    match = re.search(r"Full e2e governance unit bundle \(direct\).*?`([^`]+)`", text)
    assert match, "README missing full governance bundle row"
    return {token for token in match.group(1).split() if token.startswith("tests/") and token.endswith(".py")}


def _required_registry_paths() -> set[str]:
    return {
        str(path.relative_to(REPO_ROOT))
        for path in REQUIRED_E2E_GOVERNANCE_FILES
        if path.name != "cli_runner_compat.py"
    }


def test_constant_bundle_paths_equal_registry_set() -> None:
    constant_paths = _bundle_paths_from_constant()
    registry_paths = _required_registry_paths()
    assert constant_paths == registry_paths


def test_readme_bundle_paths_equal_constant_bundle_set() -> None:
    readme_paths = _bundle_paths_from_readme()
    constant_paths = _bundle_paths_from_constant()
    assert readme_paths == constant_paths
