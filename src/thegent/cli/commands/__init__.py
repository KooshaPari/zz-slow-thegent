"""thegent.cli.commands - CLI commands package.

This package contains the CLI command implementations extracted from the
main CLI module.
"""

from __future__ import annotations

import getpass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import typer

if TYPE_CHECKING:
    from thegent.config import ThegentSettings

# Re-export command modules
# Re-export domain command submodules (WL-124)
from thegent.cli.commands import (
    _cli_shared,
    cli,
    cli_dag,
    cli_git_identity,
    cli_git_worktree_governance,
    governance_cmds,
    impl,
    infra_cmds,
    model_cmds,
    plan_cmds,
    run_cmds,
    session_cmds,
    session_owner_helpers,
    team_cmds,
    work_stream_impl,
)

# Re-export commonly used items
from thegent.cli.commands.model_cmds import model_cmds_list

__all__ = [
    "impl",
    "cli",
    "cli_dag",
    "run_cmds",
    "session_cmds",
    "governance_cmds",
    "plan_cmds",
    "team_cmds",
    "infra_cmds",
    "model_cmds",
    "_cli_shared",
    "cli_git_worktree_governance",
    "cli_git_identity",
    "work_stream_impl",
    "model_cmds_list",
    "session_owner_helpers",
]
