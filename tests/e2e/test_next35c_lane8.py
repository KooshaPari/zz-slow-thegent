"""Next-35c lane 8: project and setup project help coverage."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

from tests.e2e.cli_runner_compat import CompatCliRunner

sys.modules.setdefault("thegent_git", MagicMock())
from thegent.main import app

runner = CompatCliRunner()


@pytest.mark.e2e
def test_project_show_help_exits_zero() -> None:
    result = runner.invoke(app, ["project", "show", "--help"])
    assert result.exit_code == 0
    assert "show" in result.stdout


@pytest.mark.e2e
def test_sys_setup_project_brownfield_help_exits_zero() -> None:
    result = runner.invoke(app, ["sys", "setup", "project", "brownfield", "--help"])
    assert result.exit_code == 0
    assert "brownfield" in result.stdout


@pytest.mark.e2e
def test_sys_setup_project_greenfield_help_exits_zero() -> None:
    result = runner.invoke(app, ["sys", "setup", "project", "greenfield", "--help"])
    assert result.exit_code == 0
    assert "greenfield" in result.stdout


@pytest.mark.e2e
def test_sys_setup_project_init_help_exits_zero() -> None:
    result = runner.invoke(app, ["sys", "setup", "project", "init", "--help"])
    assert result.exit_code == 0
    assert "init" in result.stdout


@pytest.mark.e2e
def test_sys_setup_project_scaffold_profiles_help_exits_zero() -> None:
    result = runner.invoke(app, ["sys", "setup", "project", "scaffold-profiles", "--help"])
    assert result.exit_code == 0
    assert "scaffold-profiles" in result.stdout
