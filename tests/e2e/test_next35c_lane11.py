"""Next-35c lane 11: scaffold help coverage."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

from tests.e2e.cli_runner_compat import CompatCliRunner

sys.modules.setdefault("thegent_git", MagicMock())
from thegent.main import app

runner = CompatCliRunner()


@pytest.mark.e2e
def test_project_scaffold_ag_dd_help_exits_zero() -> None:
    result = runner.invoke(app, ["scaffold", "ag-dd", "--help"])
    assert result.exit_code == 0


@pytest.mark.e2e
def test_project_scaffold_none_help_exits_zero() -> None:
    result = runner.invoke(app, ["scaffold", "none", "--help"])
    assert result.exit_code == 0


@pytest.mark.e2e
def test_project_scaffold_profiles_help_exits_zero() -> None:
    result = runner.invoke(app, ["project", "scaffold-profiles", "--help"])
    assert result.exit_code == 0
