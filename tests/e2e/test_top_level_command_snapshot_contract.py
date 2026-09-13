"""Snapshot-style contract for stable top-level command names on the real app."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import click
from typer.main import get_command

sys.modules.setdefault("thegent_git", MagicMock())
from thegent.main import app

_REQUIRED_STABLE_TOP_LEVEL_COMMANDS: tuple[str, ...] = (
    "run",
    "plan",
    "list-agents",
    "session-contract-health-gate",
    "session-contract-health-report",
)

_STABLE_TOP_LEVEL_COMMANDS_SNAPSHOT: tuple[str, ...] = (
    "list-agents",
    "plan",
    "run",
    "session-contract-health-gate",
    "session-contract-health-report",
)


def _top_level_command_names() -> tuple[str, ...]:
    root = get_command(app)
    assert isinstance(root, click.Group)
    return tuple(root.commands.keys())


def test_required_stable_top_level_subset_exists_on_real_app() -> None:
    command_names = set(_top_level_command_names())
    missing = sorted(set(_REQUIRED_STABLE_TOP_LEVEL_COMMANDS) - command_names)

    assert not missing, f"Missing required stable top-level commands on real app: {missing!r}"


def test_stable_top_level_subset_snapshot_is_deterministic() -> None:
    command_names = set(_top_level_command_names())
    stable_subset = tuple(sorted(name for name in command_names if name in _REQUIRED_STABLE_TOP_LEVEL_COMMANDS))

    assert stable_subset == _STABLE_TOP_LEVEL_COMMANDS_SNAPSHOT
