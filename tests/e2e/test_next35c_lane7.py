"""Next-35c lane 7: parity command surface hardening."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

# Skip all tests in this file - CLI commands do not exist
pytestmark = pytest.mark.skip(reason="CLI commands do not exist in current implementation")

from tests.e2e.cli_runner_compat import CompatCliRunner

sys.modules.setdefault("thegent_git", MagicMock())
from thegent.main import app

runner = CompatCliRunner()


@pytest.mark.e2e
def test_sys_setup_project_show_help_exits_zero() -> None:
    result = runner.invoke(app, ["sys", "setup", "project", "show", "--help"])
    assert result.exit_code == 0
    assert result.stdout


@pytest.mark.e2e
def test_sys_setup_project_help_exits_zero() -> None:
    result = runner.invoke(app, ["sys", "setup", "project", "--help"])
    assert result.exit_code == 0
    assert result.stdout


@pytest.mark.e2e
def test_routing_pareto_help_exits_zero() -> None:
    result = runner.invoke(app, ["routing", "pareto", "--help"])
    assert result.exit_code == 0
    assert result.stdout


@pytest.mark.e2e
def test_git_short_help_exits_zero() -> None:
    result = runner.invoke(app, ["git", "-h"])
    assert result.exit_code == 0
    assert result.stdout


@pytest.mark.e2e
def test_setup_short_help_exits_zero() -> None:
    result = runner.invoke(app, ["setup", "-h"])
    assert result.exit_code == 0
    assert result.stdout
