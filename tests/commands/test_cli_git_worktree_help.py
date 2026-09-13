"""Help examples and shortcut registration for worktree governance commands."""

from __future__ import annotations

from typer.testing import CliRunner

from thegent.cli.apps.main import app as main_app


def test_help_worktree_examples_are_registered() -> None:
    """`thegent help worktree` should expose structured governance examples.

    # @trace WL-040 WP-4004
    """
    from thegent.cli.help_examples import COMMAND_EXAMPLES

    assert "worktree" in COMMAND_EXAMPLES
    assert "thegent worktree migrate-legacy /tmp/legacy-cache infra m migrate-cache" in COMMAND_EXAMPLES["worktree"]
    assert "thegent worktree refresh <change-anchor> --remote origin --strategy merge" in COMMAND_EXAMPLES["worktree"]

    runner = CliRunner()
    result = runner.invoke(main_app, ["help", "worktree"])

    assert result.exit_code == 0
    assert "thegent worktree new" in result.output
    assert "thegent worktree migrate-legacy" in result.output
    assert "thegent worktree check" in result.output
    assert "thegent worktree refresh" in result.output


def test_help_git_examples_are_registered() -> None:
    """`thegent help git` should expose nested governance examples.

    # @trace WL-040 WP-4004
    """
    from thegent.cli.help_examples import COMMAND_EXAMPLES

    assert "git" in COMMAND_EXAMPLES
    assert (
        "thegent git worktree governance refresh <change-anchor> --remote origin --strategy merge"
        in COMMAND_EXAMPLES["git"]
    )
    assert (
        "thegent git worktree governance migrate-legacy /tmp/legacy-cache infra m migrate-cache"
        in COMMAND_EXAMPLES["git"]
    )

    runner = CliRunner()
    result = runner.invoke(main_app, ["help", "git"])

    assert result.exit_code == 0
    assert "thegent git worktree governance new" in result.output
    assert "thegent git worktree governance migrate-legacy" in result.output
    assert "thegent git worktree governance check" in result.output
    assert "thegent git worktree governance refresh" in result.output


def test_root_help_shortcut_block_matches_shortcuts() -> None:
    """The root help block should be derived from the canonical shortcut list.

    # @trace WL-040 WP-4004
    """
    from thegent.cli.help_examples import ROOT_HELP_SHORTCUT_BLOCK, ROOT_HELP_SHORTCUTS

    assert "\n".join(ROOT_HELP_SHORTCUTS) == ROOT_HELP_SHORTCUT_BLOCK
    assert "thegent help worktree" in ROOT_HELP_SHORTCUT_BLOCK
    assert "thegent help git" in ROOT_HELP_SHORTCUT_BLOCK
