"""Execute direct README e2e pytest snippets in collect-only mode."""

from __future__ import annotations

import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

README_PATH = Path(__file__).with_name("README.md")
REPO_ROOT = README_PATH.parents[2]


def _readme_text() -> str:
    return README_PATH.read_text(encoding="utf-8")


def _direct_readme_e2e_pytest_commands(text: str) -> list[list[str]]:
    commands: list[list[str]] = []
    for snippet in re.findall(r"`([^`]+)`", text):
        tokens = shlex.split(snippet)
        if len(tokens) < 3:
            continue
        if tokens[0] != "pytest" or tokens[1] != "-q":
            continue

        path_tokens = [token for token in tokens[2:] if token.startswith("tests/") and token.endswith(".py")]
        if not path_tokens:
            continue
        if any(not token.startswith("tests/e2e/") for token in path_tokens):
            continue

        allowed_tokens = {"pytest", "-q", *path_tokens}
        if any(token not in allowed_tokens for token in tokens):
            continue

        commands.append(tokens)

    return commands


@pytest.mark.parametrize("snippet_tokens", _direct_readme_e2e_pytest_commands(_readme_text()))
def test_readme_direct_e2e_pytest_commands_collect_only(snippet_tokens: list[str]) -> None:
    paths = snippet_tokens[2:]
    command = [sys.executable, "-m", "pytest", "-q", *paths, "--collect-only"]
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"README command failed in collect-only mode: {' '.join(snippet_tokens)}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_readme_has_direct_e2e_pytest_commands() -> None:
    commands = _direct_readme_e2e_pytest_commands(_readme_text())
    assert commands, "README should include at least one direct `pytest -q tests/e2e/...` snippet"
