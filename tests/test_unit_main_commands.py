"""Unit tests for top-level CLI routing in ``thegent.main``.

These tests validate current (apps-based) command wiring rather than the pre-2026
flat command surface.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from thegent.main import app

runner = CliRunner()


@pytest.mark.unit
def test_root_help_exits_zero() -> None:
    """Root app help renders successfully."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


@pytest.mark.unit
@pytest.mark.parametrize("subcommand", ["run", "plan", "sync", "audit", "team", "sys"])
def test_primary_subcommand_help_exits_zero(subcommand: str) -> None:
    """Primary apps-based subcommands are registered and routable."""
    result = runner.invoke(app, [subcommand, "--help"])
    assert result.exit_code == 0


@pytest.mark.unit
@patch("thegent.cli.apps.run.run_agent")
def test_top_level_do_routes_to_run_agent(mock_run_agent: MagicMock) -> None:
    """`thegent do` delegates to run-app quick execution."""
    result = runner.invoke(app, ["do", "hello world"])
    assert result.exit_code == 0
    mock_run_agent.assert_called_once_with(prompt="hello world")


@pytest.mark.unit
@patch("thegent.cli.commands.cli.resume_cmd")
def test_top_level_resume_routes_to_resume_cmd(mock_resume_cmd: MagicMock) -> None:
    """`thegent resume` shortcut delegates to canonical resume command."""
    result = runner.invoke(app, ["resume", "sess-1"])
    assert result.exit_code == 0
    mock_resume_cmd.assert_called_once_with(session_id="sess-1", prompt=None)


@pytest.mark.unit
@patch("thegent.cli.commands.cli.resume_cmd")
def test_top_level_resume_with_skill_forwards_skills(
    mock_resume_cmd: MagicMock,
) -> None:
    """`thegent resume --skill` forwards skill list to resume command."""
    result = runner.invoke(app, ["resume", "sess-2", "--skill", "openai-docs", "--skill", "playwright"])
    assert result.exit_code == 0
    mock_resume_cmd.assert_called_once_with(session_id="sess-2", prompt=None, skills=["openai-docs", "playwright"])


@pytest.mark.unit
@patch("thegent.doctor.run_doctor")
def test_top_level_doctor_routes_to_run_doctor(mock_run_doctor: MagicMock) -> None:
    """`thegent doctor` delegates to doctor implementation."""
    mock_run_doctor.return_value = True
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    mock_run_doctor.assert_called_once_with(fix=False, dry_run=False)


@pytest.mark.unit
@patch("thegent.doctor.run_doctor")
def test_top_level_doctor_failure_propagates_exit_code(
    mock_run_doctor: MagicMock,
) -> None:
    """Failure from run_doctor exits non-zero."""
    mock_run_doctor.return_value = False
    result = runner.invoke(app, ["doctor", "--fix", "--dry-run"])
    assert result.exit_code == 1
    mock_run_doctor.assert_called_once_with(fix=True, dry_run=True)


@pytest.mark.unit
@patch("thegent.cli.apps.run.run_ps")
def test_top_level_ps_routes_to_run_ps(mock_run_ps: MagicMock) -> None:
    """`thegent ps` shortcut delegates to run-app session listing."""
    result = runner.invoke(app, ["ps", "--format", "json"])
    assert result.exit_code == 0
    mock_run_ps.assert_called_once_with(
        all_sessions=False,
        owner=None,
        format="json",
        include_contract=False,
    )


@pytest.mark.unit
def test_run_group_help_exits_zero() -> None:
    """`thegent run` group is present and exposes help."""
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0


@pytest.mark.unit
def test_plan_group_help_exits_zero() -> None:
    """`thegent plan` group is present and exposes help."""
    result = runner.invoke(app, ["plan", "--help"])
    assert result.exit_code == 0
