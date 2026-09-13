"""Tests for ShadowAuditGit (wp-71002).

# @trace FR-VCS-001
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from thegent.orchestration.state.audit_log import ShadowAuditGit


@pytest.fixture
def audit_dir(tmp_path: Path) -> Path:
    """Return a temporary directory for the shadow audit repo."""
    return tmp_path / "audit"


@pytest.fixture
def audit_git(audit_dir: Path) -> ShadowAuditGit:
    """Create a ShadowAuditGit instance with a temp audit dir."""
    return ShadowAuditGit(audit_path=audit_dir)


@pytest.fixture
def initialized_audit(audit_git: ShadowAuditGit) -> ShadowAuditGit:
    """Return a ShadowAuditGit that has been initialized."""
    audit_git.init_shadow_repo()
    return audit_git


@pytest.mark.requirement("FR-VCS-001")
class TestInitShadowRepo:
    def test_init_creates_git_repo(self, audit_git: ShadowAuditGit, audit_dir: Path) -> None:
        audit_git.init_shadow_repo()
        assert (audit_dir / ".git").is_dir()

    def test_init_idempotent(self, audit_git: ShadowAuditGit, audit_dir: Path) -> None:
        audit_git.init_shadow_repo()
        audit_git.init_shadow_repo()
        assert (audit_dir / ".git").is_dir()

    def test_init_creates_initial_commit(self, audit_git: ShadowAuditGit, audit_dir: Path) -> None:
        audit_git.init_shadow_repo()
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=audit_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "init" in result.stdout.lower()


@pytest.mark.requirement("FR-VCS-001")
class TestCommitTransaction:
    def test_commit_transaction_creates_commit(
        self, initialized_audit: ShadowAuditGit, audit_dir: Path, tmp_path: Path
    ) -> None:
        # Create a file to track
        test_file = tmp_path / "workdir" / "hello.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("hello world")

        initialized_audit.commit_transaction(
            episode_id="ep-001",
            changed_files=[test_file],
            message="test commit",
        )

        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=audit_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "ep-001" in result.stdout

    def test_commit_transaction_copies_files(
        self, initialized_audit: ShadowAuditGit, audit_dir: Path, tmp_path: Path
    ) -> None:
        test_file = tmp_path / "workdir" / "data.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("some data")

        initialized_audit.commit_transaction(
            episode_id="ep-002",
            changed_files=[test_file],
            message="track data",
        )

        # The file should exist in the audit repo
        copied = audit_dir / "snapshots" / test_file.name
        assert copied.exists()

    def test_commit_scrubs_secrets(self, initialized_audit: ShadowAuditGit, audit_dir: Path, tmp_path: Path) -> None:
        test_file = tmp_path / "workdir" / "config.env"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("OPENAI_KEY=sk-abcdefghijklmnopqrstuvwxyz1234567890abcdefghijklmn")

        initialized_audit.commit_transaction(
            episode_id="ep-003",
            changed_files=[test_file],
            message="track config",
        )

        copied = audit_dir / "snapshots" / test_file.name
        content = copied.read_text()
        # The raw key should NOT appear in the committed file
        assert "sk-abcdefghijklmnopqrstuvwxyz1234567890abcdefghijklmn" not in content

    def test_commit_empty_file_list(self, initialized_audit: ShadowAuditGit) -> None:
        # Committing with no files should not raise
        initialized_audit.commit_transaction(
            episode_id="ep-004",
            changed_files=[],
            message="empty commit",
        )

    def test_commit_nonexistent_file_raises(self, initialized_audit: ShadowAuditGit) -> None:
        with pytest.raises(FileNotFoundError):
            initialized_audit.commit_transaction(
                episode_id="ep-005",
                changed_files=[Path("/nonexistent/file.txt")],
                message="should fail",
            )


@pytest.mark.requirement("FR-VCS-001")
class TestGetLog:
    def test_get_log_returns_entries(self, initialized_audit: ShadowAuditGit, tmp_path: Path) -> None:
        test_file = tmp_path / "workdir" / "f.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("data")

        initialized_audit.commit_transaction(
            episode_id="ep-010",
            changed_files=[test_file],
            message="log test",
        )

        entries = initialized_audit.get_log(limit=10)
        assert len(entries) >= 1
        assert any("ep-010" in e["message"] for e in entries)

    def test_get_log_respects_limit(self, initialized_audit: ShadowAuditGit, tmp_path: Path) -> None:
        test_file = tmp_path / "workdir" / "f.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        for i in range(5):
            test_file.write_text(f"data-{i}")
            initialized_audit.commit_transaction(
                episode_id=f"ep-{i:03d}",
                changed_files=[test_file],
                message=f"commit {i}",
            )

        entries = initialized_audit.get_log(limit=3)
        assert len(entries) == 3

    def test_get_log_filter_episode(self, initialized_audit: ShadowAuditGit, tmp_path: Path) -> None:
        test_file = tmp_path / "workdir" / "f.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("a")

        initialized_audit.commit_transaction(
            episode_id="ep-filter-target",
            changed_files=[test_file],
            message="target",
        )
        test_file.write_text("b")
        initialized_audit.commit_transaction(
            episode_id="ep-other",
            changed_files=[test_file],
            message="other",
        )

        entries = initialized_audit.get_log(episode_id="ep-filter-target")
        assert len(entries) >= 1
        assert all("ep-filter-target" in e["message"] for e in entries)


@pytest.mark.requirement("FR-VCS-001")
class TestGetDiff:
    def test_get_diff_returns_content(self, initialized_audit: ShadowAuditGit, tmp_path: Path) -> None:
        test_file = tmp_path / "workdir" / "f.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("new content")

        initialized_audit.commit_transaction(
            episode_id="ep-diff-001",
            changed_files=[test_file],
            message="diff test",
        )

        entries = initialized_audit.get_log(episode_id="ep-diff-001")
        assert len(entries) >= 1
        diff = initialized_audit.get_diff(entries[0]["hash"])
        assert isinstance(diff, str)
        assert len(diff) > 0
