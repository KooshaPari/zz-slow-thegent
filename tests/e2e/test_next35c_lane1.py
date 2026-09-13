"""Next-35c lane 1: command help E2E checks."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

from tests.e2e.cli_runner_compat import CompatCliRunner

sys.modules.setdefault("thegent_git", MagicMock())
from thegent.main import app

runner = CompatCliRunner()


@pytest.mark.e2e
def test_domain_map_help_exits_zero() -> None:
    result = runner.invoke(app, ["domain-map", "--help"])
    assert result.exit_code == 0


@pytest.mark.e2e
def test_enterprise_compliance_evidence_list_help_exits_zero() -> None:
    result = runner.invoke(app, ["enterprise", "compliance", "evidence", "list", "--help"])
    assert result.exit_code == 0


@pytest.mark.e2e
def test_enterprise_compliance_evidence_purge_help_exits_zero() -> None:
    result = runner.invoke(app, ["enterprise", "compliance", "evidence", "purge", "--help"])
    assert result.exit_code == 0


@pytest.mark.e2e
def test_git_help_exits_zero() -> None:
    result = runner.invoke(app, ["git", "--help"])
    assert result.exit_code == 0


@pytest.mark.e2e
def test_git_add_help_exits_zero() -> None:
    result = runner.invoke(app, ["git", "add", "--help"])
    assert result.exit_code == 0
