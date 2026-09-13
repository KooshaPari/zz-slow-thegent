"""Tests for ShadowAuditGit with secret scrubbing.

WBS: wp-71002-shadow-git
FR Traceability: FR-VER-003 (shadow audit log with secret scrubbing)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from thegent.audit.shadow_audit_git import AuditEntry, ShadowAuditGit
from thegent.registry.project_registry import ProjectRegistry

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_audit.db"


@pytest.fixture
def registry(db_path: Path) -> ProjectRegistry:
    return ProjectRegistry(db_path=db_path)


@pytest.fixture
def shadow(db_path: Path) -> ShadowAuditGit:
    return ShadowAuditGit(db_path=db_path)


@pytest.fixture
def project_id(registry: ProjectRegistry) -> str:
    project = registry.register_project(name="test-proj", path="/tmp/test")
    return project.id


# ---------------------------------------------------------------------------
# AuditEntry model tests
# ---------------------------------------------------------------------------


class TestAuditEntry:
    def test_create_entry(self) -> None:
        entry = AuditEntry(
            project_id="proj-1",
            sha="abc123",
            message="test commit",
            diff="--- a/file\n+++ b/file",
        )
        assert entry.project_id == "proj-1"
        assert entry.sha == "abc123"
        assert entry.id is not None
        assert entry.created_at is not None

    def test_entry_auto_id(self) -> None:
        e1 = AuditEntry(project_id="p", sha="a", message="m", diff="d")
        e2 = AuditEntry(project_id="p", sha="a", message="m", diff="d")
        assert e1.id != e2.id


# ---------------------------------------------------------------------------
# record_commit tests
# ---------------------------------------------------------------------------


class TestRecordCommit:
    def test_record_commit_basic(self, shadow: ShadowAuditGit, project_id: str) -> None:
        entry = shadow.record_commit(
            project_id=project_id,
            sha="deadbeef",
            message="Add feature X",
            diff="--- a/main.py\n+++ b/main.py\n+print('hello')",
        )
        assert entry.sha == "deadbeef"
        assert entry.message == "Add feature X"
        assert "print('hello')" in entry.diff

    def test_record_commit_scrubs_openai_key(self, shadow: ShadowAuditGit, project_id: str) -> None:
        diff_with_secret = "OPENAI_API_KEY=sk-1234567890abcdef1234567890abcdef1234567890abcdef12"
        entry = shadow.record_commit(
            project_id=project_id,
            sha="abc",
            message="config change",
            diff=diff_with_secret,
        )
        assert "sk-1234567890" not in entry.diff
        assert "<REDACTED" in entry.diff

    def test_record_commit_scrubs_aws_key(self, shadow: ShadowAuditGit, project_id: str) -> None:
        diff_with_secret = "+AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
        entry = shadow.record_commit(
            project_id=project_id,
            sha="def",
            message="aws config",
            diff=diff_with_secret,
        )
        assert "AKIAIOSFODNN7EXAMPLE" not in entry.diff
        assert "<REDACTED" in entry.diff

    def test_record_commit_scrubs_github_pat(self, shadow: ShadowAuditGit, project_id: str) -> None:
        diff_with_secret = "+token = ghp_ABCDEFghijklmnopqrstuvwxyz0123456789"
        entry = shadow.record_commit(
            project_id=project_id,
            sha="ghi",
            message="token leak",
            diff=diff_with_secret,
        )
        assert "ghp_ABCDEFghijklmnopqrstuvwxyz0123456789" not in entry.diff
        assert "<REDACTED" in entry.diff

    def test_record_commit_preserves_clean_diff(self, shadow: ShadowAuditGit, project_id: str) -> None:
        clean_diff = "+def hello():\n+    return 'world'"
        entry = shadow.record_commit(
            project_id=project_id,
            sha="jkl",
            message="clean code",
            diff=clean_diff,
        )
        assert entry.diff == clean_diff

    def test_record_commit_scrubs_message_too(self, shadow: ShadowAuditGit, project_id: str) -> None:
        entry = shadow.record_commit(
            project_id=project_id,
            sha="mno",
            message="Update key to sk-1234567890abcdef1234567890abcdef1234567890abcdef12",
            diff="no secrets here",
        )
        assert "sk-1234567890" not in entry.message
        assert "<REDACTED" in entry.message


# ---------------------------------------------------------------------------
# get_audit_log tests
# ---------------------------------------------------------------------------


class TestGetAuditLog:
    def test_get_audit_log_empty(self, shadow: ShadowAuditGit, project_id: str) -> None:
        entries = shadow.get_audit_log(project_id)
        assert entries == []

    def test_get_audit_log_multiple(self, shadow: ShadowAuditGit, project_id: str) -> None:
        shadow.record_commit(project_id=project_id, sha="a1", message="first", diff="d1")
        shadow.record_commit(project_id=project_id, sha="a2", message="second", diff="d2")
        shadow.record_commit(project_id=project_id, sha="a3", message="third", diff="d3")
        entries = shadow.get_audit_log(project_id)
        assert len(entries) == 3
        assert entries[0].sha == "a1"
        assert entries[2].sha == "a3"

    def test_get_audit_log_with_limit(self, shadow: ShadowAuditGit, project_id: str) -> None:
        for i in range(10):
            shadow.record_commit(project_id=project_id, sha=f"sha-{i}", message=f"msg {i}", diff=f"d{i}")
        entries = shadow.get_audit_log(project_id, limit=3)
        assert len(entries) == 3

    def test_get_audit_log_isolated_by_project(self, shadow: ShadowAuditGit, db_path: Path) -> None:
        reg = ProjectRegistry(db_path=db_path)
        p1 = reg.register_project(name="proj-a", path="/a")
        p2 = reg.register_project(name="proj-b", path="/b")
        shadow.record_commit(project_id=p1.id, sha="s1", message="m1", diff="d1")
        shadow.record_commit(project_id=p2.id, sha="s2", message="m2", diff="d2")
        assert len(shadow.get_audit_log(p1.id)) == 1
        assert len(shadow.get_audit_log(p2.id)) == 1


# ---------------------------------------------------------------------------
# export_audit tests
# ---------------------------------------------------------------------------


class TestExportAudit:
    def test_export_audit_json(self, shadow: ShadowAuditGit, project_id: str, tmp_path: Path) -> None:
        shadow.record_commit(project_id=project_id, sha="x1", message="exp msg", diff="exp diff")
        out_path = tmp_path / "audit_export.json"
        shadow.export_audit(project_id, out_path)
        assert out_path.exists()
        import json

        data = json.loads(out_path.read_text())
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["sha"] == "x1"

    def test_export_audit_empty(self, shadow: ShadowAuditGit, project_id: str, tmp_path: Path) -> None:
        out_path = tmp_path / "empty_export.json"
        shadow.export_audit(project_id, out_path)
        import json

        data = json.loads(out_path.read_text())
        assert data == []


# ---------------------------------------------------------------------------
# Persistence tests
# ---------------------------------------------------------------------------


class TestShadowPersistence:
    def test_entries_persist_across_instances(self, db_path: Path) -> None:
        reg = ProjectRegistry(db_path=db_path)
        proj = reg.register_project(name="persist", path="/persist")

        s1 = ShadowAuditGit(db_path=db_path)
        s1.record_commit(
            project_id=proj.id,
            sha="persist-sha",
            message="persist msg",
            diff="persist diff",
        )

        s2 = ShadowAuditGit(db_path=db_path)
        entries = s2.get_audit_log(proj.id)
        assert len(entries) == 1
        assert entries[0].sha == "persist-sha"
