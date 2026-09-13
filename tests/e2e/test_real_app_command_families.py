"""Real-app smoke contracts for stable command families."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

from tests.e2e.command_surface import command_path_exists

sys.modules.setdefault("thegent_git", MagicMock())
from thegent.main import app

_REQUIRED_ROOT_COMMANDS: tuple[str, ...] = (
    "run",
    "plan",
    "list-agents",
    "session-contract-health-gate",
    "session-contract-health-report",
)

_APPROVED_STABLE_TOP_LEVEL_COMMANDS: tuple[str, ...] = _REQUIRED_ROOT_COMMANDS


def test_required_root_command_paths_exist_on_real_app() -> None:
    missing = [command_name for command_name in _REQUIRED_ROOT_COMMANDS if not command_path_exists(app, [command_name])]
    assert not missing, f"Missing required stable root commands on real app: {sorted(missing)!r}"


def test_run_and_plan_resolve_as_top_level_paths_on_real_app() -> None:
    assert command_path_exists(app, ["run"])
    assert command_path_exists(app, ["plan"])


def test_at_least_five_approved_stable_top_level_commands_exist() -> None:
    stable_count = sum(
        1 for command_name in _APPROVED_STABLE_TOP_LEVEL_COMMANDS if command_path_exists(app, [command_name])
    )
    assert stable_count >= 5, f"Expected at least 5 approved stable top-level command paths; found {stable_count}"
