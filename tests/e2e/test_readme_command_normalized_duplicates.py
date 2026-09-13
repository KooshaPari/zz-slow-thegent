"""Governance test for normalized duplicate README command snippets."""

from __future__ import annotations

import re
import shlex
from collections import Counter
from pathlib import Path

README_PATH = Path(__file__).with_name("README.md")


def _readme_text() -> str:
    return README_PATH.read_text(encoding="utf-8")


def _backticked_pytest_or_task_snippets(text: str) -> list[str]:
    snippets = [snippet.strip() for snippet in re.findall(r"`([^`]+)`", text)]
    command_snippets: list[str] = []
    for snippet in snippets:
        tokens = shlex.split(snippet)
        if not tokens:
            continue
        if tokens[0] in {"pytest", "task"}:
            command_snippets.append(snippet)
    return command_snippets


def _normalize_whitespace(command: str) -> str:
    return " ".join(re.split(r"[\t ]+", command.strip()))


def test_no_normalized_duplicate_backticked_pytest_or_task_command_snippets() -> None:
    snippets = _backticked_pytest_or_task_snippets(_readme_text())
    assert snippets, "README should include at least one backticked pytest/task command snippet"

    normalized_commands = [_normalize_whitespace(snippet) for snippet in snippets]
    counts = Counter(normalized_commands)
    duplicates = [command for command, count in counts.items() if count > 1]

    assert not duplicates, (
        "README should not duplicate pytest/task snippets after whitespace normalization: " + "; ".join(duplicates)
    )
