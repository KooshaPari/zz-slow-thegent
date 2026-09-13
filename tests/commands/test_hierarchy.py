"""Tests for hierarchy CLI commands (milestone/sprint).

WBS: wp-71005-hierarchy-cli
FR Traceability: FR-VER-002 (milestone and sprint management)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from thegent.commands.hierarchy import app
from thegent.registry.project_registry import ProjectRegistry

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_hierarchy.db"


@pytest.fixture
def _patch_registry(db_path: Path):
    """Patch _get_registry to use a temp DB."""
    registry = ProjectRegistry(db_path=db_path)
    with patch("thegent.commands.hierarchy._get_registry", return_value=registry):
        yield registry


# ---------------------------------------------------------------------------
# Milestone tests
# ---------------------------------------------------------------------------


class TestMilestoneCreate:
    def test_create_milestone(self, _patch_registry: ProjectRegistry) -> None:
        result = runner.invoke(
            app,
            ["milestone", "create", "m-reliability", "--label", "Reliability Phase"],
        )
        assert result.exit_code == 0
        assert "m-reliability" in result.output

    def test_create_milestone_minimal(self, _patch_registry: ProjectRegistry) -> None:
        result = runner.invoke(app, ["milestone", "create", "m-perf"])
        assert result.exit_code == 0
        assert "m-perf" in result.output

    def test_create_duplicate_name(self, _patch_registry: ProjectRegistry) -> None:
        runner.invoke(app, ["milestone", "create", "m-dup"])
        result = runner.invoke(app, ["milestone", "create", "m-dup"])
        # Second creation should still succeed (different IDs)
        assert result.exit_code == 0


class TestMilestoneList:
    def test_list_empty(self, _patch_registry: ProjectRegistry) -> None:
        result = runner.invoke(app, ["milestone", "list"])
        assert result.exit_code == 0
        assert "No milestones" in result.output

    def test_list_with_milestones(self, _patch_registry: ProjectRegistry) -> None:
        runner.invoke(app, ["milestone", "create", "m-alpha"])
        runner.invoke(app, ["milestone", "create", "m-beta"])
        result = runner.invoke(app, ["milestone", "list"])
        assert result.exit_code == 0
        assert "m-alpha" in result.output
        assert "m-beta" in result.output


class TestMilestoneComplete:
    def test_complete_milestone(self, _patch_registry: ProjectRegistry) -> None:
        runner.invoke(app, ["milestone", "create", "m-done"])
        result = runner.invoke(app, ["milestone", "complete", "m-done"])
        assert result.exit_code == 0
        assert "completed" in result.output.lower() or "m-done" in result.output

    def test_complete_nonexistent(self, _patch_registry: ProjectRegistry) -> None:
        result = runner.invoke(app, ["milestone", "complete", "m-ghost"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Sprint tests
# ---------------------------------------------------------------------------


class TestSprintCreate:
    def test_create_sprint(self, _patch_registry: ProjectRegistry) -> None:
        result = runner.invoke(app, ["sprint", "create", "s-2026-W08", "--label", "Sprint Week 8"])
        assert result.exit_code == 0
        assert "s-2026-W08" in result.output

    def test_create_sprint_minimal(self, _patch_registry: ProjectRegistry) -> None:
        result = runner.invoke(app, ["sprint", "create", "s-2026-W09"])
        assert result.exit_code == 0


class TestSprintList:
    def test_list_empty(self, _patch_registry: ProjectRegistry) -> None:
        result = runner.invoke(app, ["sprint", "list"])
        assert result.exit_code == 0
        assert "No sprints" in result.output

    def test_list_with_sprints(self, _patch_registry: ProjectRegistry) -> None:
        runner.invoke(app, ["sprint", "create", "s-w1"])
        runner.invoke(app, ["sprint", "create", "s-w2"])
        result = runner.invoke(app, ["sprint", "list"])
        assert result.exit_code == 0
        assert "s-w1" in result.output
        assert "s-w2" in result.output


class TestSprintComplete:
    def test_complete_sprint(self, _patch_registry: ProjectRegistry) -> None:
        runner.invoke(app, ["sprint", "create", "s-done"])
        result = runner.invoke(app, ["sprint", "complete", "s-done"])
        assert result.exit_code == 0

    def test_complete_nonexistent(self, _patch_registry: ProjectRegistry) -> None:
        result = runner.invoke(app, ["sprint", "complete", "s-ghost"])
        assert result.exit_code == 1
