"""Tests for `thegent git worktree governance` structured lifecycle commands and help discoverability."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from thegent.cli.apps.main import app as main_app
from thegent.cli.commands.cli_git import app

runner = CliRunner()


def _assert_refresh_argv(argv: list[str]) -> None:
    assert argv[1] == "refresh"
    assert argv[2] == "fix-mcp-timeout"
    options = dict(zip(argv[3::2], argv[4::2], strict=False))
    assert options == {
        "--remote": "origin",
        "--ref": "origin/canary",
        "--strategy": "rebase",
    }


def _assert_migrate_argv(argv: list[str]) -> None:
    assert argv[1] == "migrate-legacy"
    assert argv[2].endswith("legacy-cache")
    assert argv[3:6] == ["infra", "m", "migrate-cache"]
    assert argv[6] == "blocked"


def test_git_worktree_governance_new_invokes_script(tmp_path: Path) -> None:
    """`thegent git worktree governance new` shells out to the governance script."""
    script = tmp_path / "scripts" / "worktree_governance.sh"
    script.parent.mkdir(parents=True)
    script.write_text("#!/usr/bin/env sh\n", encoding="utf-8")

    completed = MagicMock(returncode=0, stdout="created\n", stderr="")
    with (
        patch(
            "thegent.cli.commands.cli_git_worktree_governance._script_path",
            return_value=script,
        ),
        patch(
            "thegent.cli.commands.cli_git_worktree_governance.subprocess.run",
            return_value=completed,
        ) as mock_run,
    ):
        result = runner.invoke(
            app,
            [
                "worktree",
                "governance",
                "new",
                "backend",
                "m",
                "fix-mcp-timeout",
                "main",
                "--root",
                str(tmp_path),
            ],
        )

    assert result.exit_code == 0
    assert "created" in result.output
    mock_run.assert_called_once()
    assert mock_run.call_args.args[0][0] == str(script)
    assert mock_run.call_args.args[0][1:] == [
        "new",
        "backend",
        "m",
        "fix-mcp-timeout",
        "main",
    ]


def test_git_worktree_governance_prune_dry_run_invokes_script(tmp_path: Path) -> None:
    """`thegent git worktree governance prune --dry-run` passes the dry-run flag."""
    script = tmp_path / "scripts" / "worktree_governance.sh"
    script.parent.mkdir(parents=True)
    script.write_text("#!/usr/bin/env sh\n", encoding="utf-8")

    completed = MagicMock(returncode=0, stdout="[DRY-RUN]\n", stderr="")
    with (
        patch(
            "thegent.cli.commands.cli_git_worktree_governance._script_path",
            return_value=script,
        ),
        patch(
            "thegent.cli.commands.cli_git_worktree_governance.subprocess.run",
            return_value=completed,
        ) as mock_run,
    ):
        result = runner.invoke(
            app,
            ["worktree", "governance", "prune", "--dry-run", "--root", str(tmp_path)],
        )

    assert result.exit_code == 0
    assert "[DRY-RUN]" in result.output
    mock_run.assert_called_once()
    assert mock_run.call_args.args[0][1:] == ["prune", "--dry-run"]


@pytest.mark.parametrize(
    ("invoke_app", "invoke_args"),
    [
        (
            app,
            [
                "worktree",
                "governance",
                "refresh",
                "fix-mcp-timeout",
                "--remote",
                "origin",
                "--ref",
                "origin/canary",
                "--strategy",
                "rebase",
                "--root",
                "{root}",
            ],
        ),
        (
            main_app,
            [
                "worktree",
                "refresh",
                "fix-mcp-timeout",
                "--remote",
                "origin",
                "--ref",
                "origin/canary",
                "--strategy",
                "rebase",
                "--root",
                "{root}",
            ],
        ),
    ],
)
def test_worktree_governance_refresh_invokes_script(
    tmp_path: Path,
    invoke_app: object,
    invoke_args: list[str],
) -> None:
    """`thegent worktree refresh` and nested git refresh both forward refresh controls."""
    script = tmp_path / "scripts" / "worktree_governance.sh"
    script.parent.mkdir(parents=True)
    script.write_text("#!/usr/bin/env sh\n", encoding="utf-8")

    completed = MagicMock(returncode=0, stdout="[OK] refreshed worktree\n", stderr="")
    with (
        patch(
            "thegent.cli.commands.cli_git_worktree_governance._script_path",
            return_value=script,
        ),
        patch(
            "thegent.cli.commands.cli_git_worktree_governance.subprocess.run",
            return_value=completed,
        ) as mock_run,
    ):
        result = runner.invoke(
            invoke_app, [part.format(root=tmp_path) for part in invoke_args]
        )

    assert result.exit_code == 0
    assert "[OK] refreshed worktree" in result.output
    mock_run.assert_called_once()
    argv = mock_run.call_args.args[0]
    assert argv[0] == str(script)
    _assert_refresh_argv(argv)


@pytest.mark.parametrize(
    ("invoke_app", "invoke_args"),
    [
        (
            app,
            [
                "worktree",
                "governance",
                "migrate-legacy",
                "{legacy}",
                "infra",
                "m",
                "migrate-cache",
                "blocked",
                "--root",
                "{root}",
            ],
        ),
        (
            main_app,
            [
                "worktree",
                "migrate-legacy",
                "{legacy}",
                "infra",
                "m",
                "migrate-cache",
                "blocked",
                "--root",
                "{root}",
            ],
        ),
    ],
)
def test_worktree_governance_migrate_legacy_invokes_script(
    tmp_path: Path,
    invoke_app: object,
    invoke_args: list[str],
) -> None:
    """`thegent worktree migrate-legacy` and nested git migrate both forward migration controls."""
    script = tmp_path / "scripts" / "worktree_governance.sh"
    script.parent.mkdir(parents=True)
    script.write_text("#!/usr/bin/env sh\n", encoding="utf-8")
    legacy_path = tmp_path / "legacy-cache"
    legacy_path.mkdir()

    completed = MagicMock(
        returncode=0, stdout="[OK] migrated legacy worktree\n", stderr=""
    )
    with (
        patch(
            "thegent.cli.commands.cli_git_worktree_governance._script_path",
            return_value=script,
        ),
        patch(
            "thegent.cli.commands.cli_git_worktree_governance.subprocess.run",
            return_value=completed,
        ) as mock_run,
    ):
        result = runner.invoke(
            invoke_app,
            [part.format(root=tmp_path, legacy=legacy_path) for part in invoke_args],
        )

    assert result.exit_code == 0
    assert "[OK] migrated legacy worktree" in result.output
    mock_run.assert_called_once()
    argv = mock_run.call_args.args[0]
    assert argv[0] == str(script)
    _assert_migrate_argv(argv)


def test_root_worktree_new_invokes_script(tmp_path: Path) -> None:
    """`thegent worktree new` shells out to the governance script."""
    script = tmp_path / "scripts" / "worktree_governance.sh"
    script.parent.mkdir(parents=True)
    script.write_text("#!/usr/bin/env sh\n", encoding="utf-8")

    completed = MagicMock(returncode=0, stdout="created\n", stderr="")
    with (
        patch(
            "thegent.cli.commands.cli_git_worktree_governance._script_path",
            return_value=script,
        ),
        patch(
            "thegent.cli.commands.cli_git_worktree_governance.subprocess.run",
            return_value=completed,
        ) as mock_run,
    ):
        result = runner.invoke(
            main_app,
            [
                "worktree",
                "new",
                "backend",
                "m",
                "fix-mcp-timeout",
                "main",
                "--root",
                str(tmp_path),
            ],
        )

    assert result.exit_code == 0
    assert "created" in result.output
    mock_run.assert_called_once()
    assert mock_run.call_args.args[0][1:] == [
        "new",
        "backend",
        "m",
        "fix-mcp-timeout",
        "main",
    ]


def test_root_worktree_check_preserves_root_path_with_spaces(tmp_path: Path) -> None:
    """`thegent worktree governance check` forwards a sanitized root path intact."""
    root = tmp_path / "repo with spaces" / "nested"
    root.mkdir(parents=True)
    script = root / "scripts" / "worktree_governance.sh"
    script.parent.mkdir(parents=True)
    script.write_text("#!/usr/bin/env sh\n", encoding="utf-8")

    completed = MagicMock(
        returncode=0, stdout="[OK] worktree governance check passed\n", stderr=""
    )
    with (
        patch(
            "thegent.cli.commands.cli_git_worktree_governance._script_path",
            return_value=script,
        ),
        patch(
            "thegent.cli.commands.cli_git_worktree_governance.subprocess.run",
            return_value=completed,
        ) as mock_run,
    ):
        result = runner.invoke(
            app, ["worktree", "governance", "check", "--root", str(root)]
        )

    assert result.exit_code == 0
    assert "[OK] worktree governance check passed" in result.output
    mock_run.assert_called_once()
    assert mock_run.call_args.kwargs["cwd"] == root
    assert mock_run.call_args.args[0][0] == str(script)


def test_root_worktree_check_fails_when_repo_root_lookup_fails() -> None:
    """`thegent worktree check` should surface a failing `git rev-parse`."""
    completed = MagicMock(
        returncode=1, stdout="", stderr="fatal: not a git repository\n"
    )
    with patch(
        "thegent.cli.commands.cli_git_worktree_governance.subprocess.run",
        return_value=completed,
    ):
        result = runner.invoke(main_app, ["worktree", "check"])

    assert result.exit_code == 1


def test_git_worktree_governance_new_propagates_script_failure(tmp_path: Path) -> None:
    """`thegent git worktree governance new` should propagate a non-zero script exit."""
    script = tmp_path / "scripts" / "worktree_governance.sh"
    script.parent.mkdir(parents=True)
    script.write_text("#!/usr/bin/env sh\n", encoding="utf-8")

    completed = MagicMock(returncode=7, stdout="", stderr="boom\n")
    with (
        patch(
            "thegent.cli.commands.cli_git_worktree_governance._script_path",
            return_value=script,
        ),
        patch(
            "thegent.cli.commands.cli_git_worktree_governance.subprocess.run",
            return_value=completed,
        ),
    ):
        result = runner.invoke(
            app,
            [
                "worktree",
                "governance",
                "new",
                "backend",
                "m",
                "fix-mcp-timeout",
                "main",
                "--root",
                str(tmp_path),
            ],
        )

    assert result.exit_code == 7
    assert "boom" in result.output


def test_root_worktree_check_missing_script_fails_loudly(tmp_path: Path) -> None:
    """`thegent worktree check` should surface a missing governance script."""
    script_root = tmp_path / "repo"
    script_root.mkdir()

    with patch(
        "thegent.cli.commands.cli_git_worktree_governance._script_path",
        side_effect=FileNotFoundError("missing worktree governance script"),
    ):
        result = runner.invoke(
            main_app, ["worktree", "check", "--root", str(script_root)]
        )

    assert result.exit_code != 0
    assert "missing worktree governance script" in str(result.exception)
