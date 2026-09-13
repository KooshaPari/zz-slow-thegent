"""Tests for audit CLI commands (log/diff).

WBS: wp-71004-audit-cli
FR Traceability: FR-VER-005 (audit log and diff CLI)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from thegent.audit.shadow_audit_git import ShadowAuditGit
from thegent.commands.audit_commands import app
from thegent.registry.project_registry import ProjectRegistry

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_audit_cli.db"


@pytest.fixture
def registry(db_path: Path) -> ProjectRegistry:
    return ProjectRegistry(db_path=db_path)


@pytest.fixture
def shadow(db_path: Path) -> ShadowAuditGit:
    return ShadowAuditGit(db_path=db_path)


@pytest.fixture
def project_with_entries(registry: ProjectRegistry, shadow: ShadowAuditGit) -> str:
    """Create a project with some audit entries and return its name."""
    proj = registry.register_project(name="test-audit-proj", path="/tmp/audit-test")
    shadow.record_commit(project_id=proj.id, sha="abc123", message="First commit", diff="diff1")
    shadow.record_commit(project_id=proj.id, sha="def456", message="Second commit", diff="diff2")
    shadow.record_commit(project_id=proj.id, sha="ghi789", message="Third commit", diff="diff3")
    return proj.name


@pytest.fixture
def _patch_deps(db_path: Path, registry: ProjectRegistry, shadow: ShadowAuditGit):
    """Patch the module-level factory functions."""
    with (
        patch("thegent.commands.audit_commands._get_registry", return_value=registry),
        patch("thegent.commands.audit_commands._get_shadow", return_value=shadow),
    ):
        yield


# ---------------------------------------------------------------------------
# Log command tests
# ---------------------------------------------------------------------------


class TestAuditLog:
    def test_log_empty(self, _patch_deps, registry: ProjectRegistry) -> None:
        registry.register_project(name="empty-proj", path="/empty")
        result = runner.invoke(app, ["log", "--project", "empty-proj"])
        assert result.exit_code == 0
        assert "No audit entries" in result.output

    def test_log_with_entries(self, _patch_deps, project_with_entries: str) -> None:
        result = runner.invoke(app, ["log", "--project", project_with_entries])
        assert result.exit_code == 0
        assert "abc123" in result.output
        assert "def456" in result.output

    def test_log_with_limit(self, _patch_deps, project_with_entries: str) -> None:
        result = runner.invoke(app, ["log", "--project", project_with_entries, "--limit", "2"])
        assert result.exit_code == 0
        assert "abc123" in result.output
        # With limit 2, should have at most 2 entries shown
        assert "ghi789" not in result.output

    def test_log_unknown_project(self, _patch_deps) -> None:
        result = runner.invoke(app, ["log", "--project", "nonexistent"])
        assert result.exit_code == 1

    def test_log_no_project_flag(self, _patch_deps) -> None:
        result = runner.invoke(app, ["log"])
        # Should show usage error or require --project
        assert result.exit_code != 0 or "Missing" in result.output or "required" in result.output.lower()


# ---------------------------------------------------------------------------
# Diff command tests
# ---------------------------------------------------------------------------


class TestAuditDiff:
    def test_diff_two_shas(self, _patch_deps, project_with_entries: str) -> None:
        result = runner.invoke(app, ["diff", "abc123", "def456", "--project", project_with_entries])
        assert result.exit_code == 0
        # Should show diff content from both entries
        assert "abc123" in result.output or "diff1" in result.output

    def test_diff_unknown_sha(self, _patch_deps, project_with_entries: str) -> None:
        result = runner.invoke(app, ["diff", "unknown1", "unknown2", "--project", project_with_entries])
        assert result.exit_code == 1

    def test_diff_unknown_project(self, _patch_deps) -> None:
        result = runner.invoke(app, ["diff", "sha1", "sha2", "--project", "nonexistent"])
        assert result.exit_code == 1

    def test_diff_shows_both_entries(self, _patch_deps, project_with_entries: str) -> None:
        result = runner.invoke(app, ["diff", "abc123", "ghi789", "--project", project_with_entries])
        assert result.exit_code == 0
        assert "Entry 1" in result.output
        assert "Entry 2" in result.output

    def test_diff_one_sha_missing(self, _patch_deps, project_with_entries: str) -> None:
        result = runner.invoke(app, ["diff", "abc123", "missing_sha", "--project", project_with_entries])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()
