"""Tests for distributed ShadowAuditGit with remote_host support.

Tests for the remote_host parameter which enables tracking file changes
from distributed worker nodes.

# @trace FR-VCS-001
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

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


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    """Create a sample file for testing."""
    file_path = tmp_path / "workdir" / "sample.txt"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("sample content")
    return file_path


@pytest.fixture
def secret_file(tmp_path: Path) -> Path:
    """Create a file with a secret for testing scrubbing."""
    file_path = tmp_path / "workdir" / "config.env"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("API_KEY=sk-abcdefghijklmnopqrstuvwxyz1234567890abcdefghijklmn")
    return file_path


@pytest.mark.requirement("FR-VCS-001")
class TestDistributedRemoteHost:
    """Tests for remote_host parameter in distributed scenarios."""

    def test_commit_with_remote_host_creates_subdirectory(
        self, initialized_audit: ShadowAuditGit, audit_dir: Path, sample_file: Path
    ) -> None:
        """Verify remote_host creates a subdirectory under snapshots."""
        initialized_audit.commit_transaction(
            episode_id="ep-dist-001",
            changed_files=[sample_file],
            message="remote commit",
            remote_host="worker-node-01",
        )

        # Check file is stored under remote_host subdirectory
        remote_snapshot = audit_dir / "snapshots" / "worker-node-01" / sample_file.name
        assert remote_snapshot.exists()
        assert remote_snapshot.read_text() == "sample content"

    def test_commit_without_remote_host_uses_base_snapshots(
        self, initialized_audit: ShadowAuditGit, audit_dir: Path, sample_file: Path
    ) -> None:
        """Verify commits without remote_host use base snapshots directory."""
        initialized_audit.commit_transaction(
            episode_id="ep-local-001",
            changed_files=[sample_file],
            message="local commit",
            remote_host=None,
        )

        # File should be directly in snapshots (not in a subdirectory)
        local_snapshot = audit_dir / "snapshots" / sample_file.name
        assert local_snapshot.exists()

    def test_commit_message_includes_remote_host(
        self, initialized_audit: ShadowAuditGit, audit_dir: Path, sample_file: Path
    ) -> None:
        """Verify remote_host is included in commit message."""
        initialized_audit.commit_transaction(
            episode_id="ep-msg-001",
            changed_files=[sample_file],
            message="test message",
            remote_host="worker-east-02",
        )

        result = subprocess.run(
            ["git", "log", "--format=%s"],
            cwd=audit_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "(worker-east-02)" in result.stdout
        assert "[ep-msg-001]" in result.stdout

    def test_multiple_remote_hosts_create_separate_directories(
        self, initialized_audit: ShadowAuditGit, audit_dir: Path, tmp_path: Path
    ) -> None:
        """Verify multiple remote hosts create separate snapshot directories."""
        for i, host in enumerate(["worker-a", "worker-b", "worker-c"]):
            file_path = tmp_path / f"workdir{i}" / "data.txt"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"data from {host}")

            initialized_audit.commit_transaction(
                episode_id=f"ep-multi-{i:03d}",
                changed_files=[file_path],
                message=f"commit from {host}",
                remote_host=host,
            )

        # Each remote host should have its own directory
        for host in ["worker-a", "worker-b", "worker-c"]:
            host_dir = audit_dir / "snapshots" / host
            assert host_dir.is_dir()
            assert (host_dir / "data.txt").exists()

    def test_same_filename_from_different_hosts(
        self, initialized_audit: ShadowAuditGit, audit_dir: Path, tmp_path: Path
    ) -> None:
        """Verify same filename from different hosts stored separately."""
        # Create files with same name from different hosts
        for host in ["host-1", "host-2"]:
            workdir = tmp_path / host / "workdir"
            workdir.mkdir(parents=True, exist_ok=True)
            file_path = workdir / "config.yaml"
            file_path.write_text(f"config for {host}")

            initialized_audit.commit_transaction(
                episode_id=f"ep-same-{host}",
                changed_files=[file_path],
                message=f"config from {host}",
                remote_host=host,
            )

        # Last write wins for the same filename in the same host dir
        host1_file = audit_dir / "snapshots" / "host-1" / "config.yaml"
        host2_file = audit_dir / "snapshots" / "host-2" / "config.yaml"
        assert host1_file.exists()
        assert host2_file.exists()

    def test_get_log_returns_remote_host_commits(self, initialized_audit: ShadowAuditGit, sample_file: Path) -> None:
        """Verify get_log returns commits from remote hosts."""
        initialized_audit.commit_transaction(
            episode_id="ep-log-remote-001",
            changed_files=[sample_file],
            message="remote log test",
            remote_host="log-test-host",
        )

        entries = initialized_audit.get_log(limit=10)
        assert len(entries) >= 1
        assert any("ep-log-remote-001" in e["message"] for e in entries)

    def test_get_log_filter_by_episode_with_remote(self, initialized_audit: ShadowAuditGit, tmp_path: Path) -> None:
        """Verify get_log can filter by episode_id for remote commits."""
        file1 = tmp_path / "w1" / "f.txt"
        file1.parent.mkdir(parents=True, exist_ok=True)
        file1.write_text("data1")

        file2 = tmp_path / "w2" / "f.txt"
        file2.parent.mkdir(parents=True, exist_ok=True)
        file2.write_text("data2")

        initialized_audit.commit_transaction(
            episode_id="ep-filter-remote",
            changed_files=[file1],
            message="filter target",
            remote_host="filter-host",
        )

        initialized_audit.commit_transaction(
            episode_id="ep-other-remote",
            changed_files=[file2],
            message="other",
            remote_host="other-host",
        )

        entries = initialized_audit.get_log(episode_id="ep-filter-remote")
        assert len(entries) >= 1
        assert all("ep-filter-remote" in e["message"] for e in entries)

    def test_get_diff_for_remote_commit(self, initialized_audit: ShadowAuditGit, sample_file: Path) -> None:
        """Verify get_diff works for commits from remote hosts."""
        initialized_audit.commit_transaction(
            episode_id="ep-diff-remote-001",
            changed_files=[sample_file],
            message="diff test remote",
            remote_host="diff-host",
        )

        entries = initialized_audit.get_log(episode_id="ep-diff-remote-001")
        assert len(entries) >= 1

        diff = initialized_audit.get_diff(entries[0]["hash"])
        assert isinstance(diff, str)
        assert "sample content" in diff


@pytest.mark.requirement("FR-VCS-001")
class TestDistributedSecretScrubbing:
    """Tests for secret scrubbing with remote_host."""

    def test_remote_host_scrubs_secrets(
        self, initialized_audit: ShadowAuditGit, audit_dir: Path, secret_file: Path
    ) -> None:
        """Verify secrets are scrubbed even with remote_host set."""
        initialized_audit.commit_transaction(
            episode_id="ep-secret-remote-001",
            changed_files=[secret_file],
            message="secret file from remote",
            remote_host="secure-worker",
        )

        copied = audit_dir / "snapshots" / "secure-worker" / secret_file.name
        content = copied.read_text()
        # Raw key should not appear
        assert "sk-abcdefghijklmnopqrstuvwxyz1234567890abcdefghijklmn" not in content

    def test_remote_host_preserves_non_secret_content(
        self, initialized_audit: ShadowAuditGit, audit_dir: Path, tmp_path: Path
    ) -> None:
        """Verify non-secret content is preserved with remote_host."""
        file_path = tmp_path / "workdir" / "config.yaml"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("name: myapp\nversion: 1.0.0\n")

        initialized_audit.commit_transaction(
            episode_id="ep-preserve-001",
            changed_files=[file_path],
            message="config from remote",
            remote_host="config-host",
        )

        copied = audit_dir / "snapshots" / "config-host" / file_path.name
        content = copied.read_text()
        assert "name: myapp" in content
        assert "version: 1.0.0" in content


@pytest.mark.requirement("FR-VCS-001")
class TestDistributedEdgeCases:
    """Edge cases for distributed shadow git."""

    def test_empty_changed_files_with_remote_host(self, initialized_audit: ShadowAuditGit) -> None:
        """Verify empty file list with remote_host doesn't error."""
        # Should not raise
        initialized_audit.commit_transaction(
            episode_id="ep-empty-remote",
            changed_files=[],
            message="empty commit",
            remote_host="empty-host",
        )

    def test_nonexistent_file_with_remote_host_raises(self, initialized_audit: ShadowAuditGit) -> None:
        """Verify nonexistent file with remote_host raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            initialized_audit.commit_transaction(
                episode_id="ep-nonexistent-remote",
                changed_files=[Path("/nonexistent/file.txt")],
                message="should fail",
                remote_host="fail-host",
            )

    def test_multiple_files_from_single_remote(
        self, initialized_audit: ShadowAuditGit, audit_dir: Path, tmp_path: Path
    ) -> None:
        """Verify multiple files from single remote host are tracked."""
        files = []
        for i in range(3):
            file_path = tmp_path / "workdir" / f"file{i}.txt"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"content {i}")
            files.append(file_path)

        initialized_audit.commit_transaction(
            episode_id="ep-multi-files-remote",
            changed_files=files,
            message="multiple files from remote",
            remote_host="batch-worker",
        )

        for i in range(3):
            snapshot = audit_dir / "snapshots" / "batch-worker" / f"file{i}.txt"
            assert snapshot.exists()

    def test_remote_host_with_special_characters(
        self, initialized_audit: ShadowAuditGit, audit_dir: Path, sample_file: Path
    ) -> None:
        """Verify remote host with dashes and dots works."""
        initialized_audit.commit_transaction(
            episode_id="ep-special-host",
            changed_files=[sample_file],
            message="special host test",
            remote_host="worker-node-01.us-east-1.prod",
        )

        snapshot = audit_dir / "snapshots" / "worker-node-01.us-east-1.prod" / sample_file.name
        assert snapshot.exists()

    def test_concurrent_remote_hosts(self, initialized_audit: ShadowAuditGit, audit_dir: Path, tmp_path: Path) -> None:
        """Verify concurrent commits from different hosts are tracked."""
        # Simulate concurrent commits by interleaving
        hosts = ["alpha", "beta", "gamma"]
        for i, host in enumerate(hosts):
            file_path = tmp_path / f"dir_{host}" / "data.txt"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"data from {host} iteration {i}")

            initialized_audit.commit_transaction(
                episode_id=f"ep-concurrent-{host}",
                changed_files=[file_path],
                message=f"concurrent commit {i}",
                remote_host=host,
            )

        # Verify all commits exist
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=audit_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        for host in hosts:
            assert f"({host})" in result.stdout


@pytest.mark.requirement("FR-VCS-001")
class TestDistributedMockScanning:
    """Tests using mocked secret scanning for isolation."""

    @patch("thegent.orchestration.state.audit_log.scan_secrets")
    def test_uses_scan_secrets_with_remote(
        self, mock_scan: MagicMock, initialized_audit: ShadowAuditGit, sample_file: Path
    ) -> None:
        """Verify scan_secrets is called for remote host commits."""
        mock_scan.return_value = []

        initialized_audit.commit_transaction(
            episode_id="ep-mock-scan",
            changed_files=[sample_file],
            message="mock scan test",
            remote_host="mock-host",
        )

        mock_scan.assert_called_once()
        call_arg = mock_scan.call_args[0][0]
        assert "sample content" in call_arg

    @patch("thegent.orchestration.state.audit_log.scan_secrets")
    def test_scan_secrets_finds_secrets_remote(
        self,
        mock_scan: MagicMock,
        initialized_audit: ShadowAuditGit,
        audit_dir: Path,
        tmp_path: Path,
    ) -> None:
        """Verify secrets found by scanner are redacted in remote commits."""
        from thegent.governance.native_secret_scan import SecretMatch

        # Mock finding a secret on line 1
        mock_scan.return_value = [SecretMatch(kind="test_secret", line=1, masked="TEST****")]

        file_path = tmp_path / "workdir" / "secret.txt"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("SECRET_KEY=supersecret123")

        initialized_audit.commit_transaction(
            episode_id="ep-found-secret",
            changed_files=[file_path],
            message="found secret",
            remote_host="secure-host",
        )

        # The file should be redacted
        copied = audit_dir / "snapshots" / "secure-host" / "secret.txt"
        content = copied.read_text()
        assert "[REDACTED]" in content
        assert "supersecret123" not in content
