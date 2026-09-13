"""Contract checks for README governance bundle command ordering."""

from __future__ import annotations

import re
from pathlib import Path

README_PATH = Path(__file__).with_name("README.md")


def _readme_text() -> str:
    return README_PATH.read_text(encoding="utf-8")


def _full_bundle_command() -> str:
    text = _readme_text()
    match = re.search(r"Full e2e governance unit bundle \(direct\).*?`([^`]+)`", text)
    assert match, "README missing full governance bundle row"
    return match.group(1)


def test_full_bundle_starts_with_expected_prefix_sequence() -> None:
    command = _full_bundle_command()
    expected_prefix = (
        "pytest -q tests/e2e/test_cli_alias_rewrite_contract.py tests/e2e/test_cli_alias_rewrite_real_app.py"
    )
    assert command.startswith(expected_prefix)


def test_full_bundle_has_no_duplicate_test_paths() -> None:
    command = _full_bundle_command()
    paths = [token for token in command.split() if token.startswith("tests/") and token.endswith(".py")]
    assert paths
    assert len(paths) == len(set(paths)), "Full governance bundle has duplicate test paths"
