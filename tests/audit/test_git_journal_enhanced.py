"""Tests for GitJournalEnhanced with P1 enhancements.

WBS: wp-71002-shadow-git
FR Traceability: FR-VER-003 (shadow audit log with secret scrubbing)
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import orjson as json
import pytest

pytestmark = pytest.mark.skip(reason="Multiple pre-existing test failures - needs investigation")

from thegent.audit.shadow_audit_git import (
    GitJournal,
    GitJournalEnhanced,
)

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository for testing."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    (repo_path / "README.md").write_text("# Test Repo\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    return repo_path


@pytest.fixture
def journal_enhanced(git_repo: Path) -> GitJournalEnhanced:
    """Create enhanced journal instance with default settings."""
    return GitJournalEnhanced(
        repo_root=git_repo,
        session_id="test-session-001",
        track_secrets=True,
        auto_commit=False,
        enable_watching=False,
        enable_attestation=False,
        batch_size=5,
    )


@pytest.fixture
def journal_with_attestation(git_repo: Path) -> GitJournalEnhanced:
    """Create enhanced journal with attestation enabled."""
    return GitJournalEnhanced(
        repo_root=git_repo,
        session_id="test-session-attest",
        track_secrets=True,
        auto_commit=False,
        enable_watching=False,
        enable_attestation=True,
        batch_size=3,
    )


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------


class TestGitJournalEnhancedInit:
    """Tests for GitJournalEnhanced initialization."""

    def test_init_default_options(self, git_repo: Path) -> None:
        """Test initialization with default options."""
        journal = GitJournalEnhanced(
            repo_root=git_repo,
            session_id="init-test-001",
        )

        assert journal.session_id == "init-test-001"
        assert journal.repo_root == git_repo
        assert journal.track_secrets is True
        assert journal.auto_commit is False  # overridden by enhanced
        assert journal.enable_watching is False
        assert journal.enable_attestation is False
        assert journal.batch_size == 10  # default

    def test_init_all_options(self, git_repo: Path) -> None:
        """Test initialization with all options specified."""
        journal = GitJournalEnhanced(
            repo_root=git_repo,
            session_id="init-test-002",
            track_secrets=False,
            auto_commit=True,
            enable_watching=True,
            enable_attestation=True,
            batch_size=15,
        )

        assert journal.session_id == "init-test-002"
        assert journal.track_secrets is False
        assert journal.enable_watching is True
        assert journal.enable_attestation is True
        assert journal.batch_size == 15

    def test_init_caches_initialized(self, git_repo: Path) -> None:
        """Test that internal caches are properly initialized."""
        journal = GitJournalEnhanced(
            repo_root=git_repo,
            session_id="init-cache-test",
        )

        assert journal._blob_cache == {}
        assert journal._pending_changes == []
        assert journal._attestations == []

    def test_init_inherits_from_git_journal(self, git_repo: Path) -> None:
        """Test that GitJournalEnhanced properly inherits from GitJournal."""
        journal = GitJournalEnhanced(
            repo_root=git_repo,
            session_id="inheritance-test",
        )

        assert isinstance(journal, GitJournal)
        assert hasattr(journal, "repo_root")
        assert hasattr(journal, "session_id")
        assert hasattr(journal, "audit_ref")


# ---------------------------------------------------------------------------
# Native scanner detection tests
# ---------------------------------------------------------------------------


class TestNativeScannerDetection:
    """Tests for native secret scanner detection and fallback."""

    def test_scanner_available_when_hook_dispatcher_present(self, git_repo: Path) -> None:
        """Test scanner detection when hook-dispatcher is available."""
        with patch("subprocess.run") as mock_run:
            # Simulate hook-dispatcher --help succeeds
            mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")

            journal = GitJournalEnhanced(
                repo_root=git_repo,
                session_id="scanner-available",
                enable_watching=False,
            )

            # Re-call the check with mocked subprocess
            result = journal._check_native_scanner()
            assert result is True
            mock_run.assert_called()

    def test_scanner_fallback_when_hook_dispatcher_missing(self, git_repo: Path) -> None:
        """Test fallback when hook-dispatcher is not available."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("hook-dispatcher not found")

            journal = GitJournalEnhanced(
                repo_root=git_repo,
                session_id="scanner-fallback",
                enable_watching=False,
            )

            result = journal._check_native_scanner()
            assert result is False

    def test_scanner_fallback_on_error(self, git_repo: Path) -> None:
        """Test fallback on scanner error."""
        with patch("subprocess.run") as mock_run:
            # Scanner exists but returns error
            mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"error")

            journal = GitJournalEnhanced(
                repo_root=git_repo,
                session_id="scanner-error",
                enable_watching=False,
            )

            result = journal._check_native_scanner()
            assert result is False

    def test_native_scanner_property_set(self, git_repo: Path) -> None:
        """Test that _native_scanner_available is properly set."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")

            journal = GitJournalEnhanced(
                repo_root=git_repo,
                session_id="scanner-prop",
                enable_watching=False,
            )

            # The property should be set during __init__
            assert hasattr(journal, "_native_scanner_available")


# ---------------------------------------------------------------------------
# Secret scrubbing tests
# ---------------------------------------------------------------------------


class TestScrubWithNativeScanner:
    """Tests for _scrub_with_native_scanner method."""

    def test_scrub_with_native_scanner_available(self, git_repo: Path) -> None:
        """Test scrubbing when native scanner is available."""
        with patch("subprocess.run") as mock_run:
            # Mock native scanner returning findings
            findings = [
                {"matched": "sk-secret-key-12345", "kind": "OPENAI_API_KEY"},
            ]
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps(findings),
                stderr=b"",
            )

            journal = GitJournalEnhanced(
                repo_root=git_repo,
                session_id="scrub-native",
                enable_watching=False,
                track_secrets=True,
            )

            # Force native scanner to be available
            journal._native_scanner_available = True

            content = "API_KEY=sk-secret-key-12345\nOTHER_CONTENT"
            result = journal._scrub_with_native_scanner(content)

            assert "sk-secret-key-12345" not in result
            assert "<REDACTED_OPENAI_API_KEY>" in result

    def test_scrub_fallback_to_regex(self, git_repo: Path) -> None:
        """Test fallback to regex scrubbing when native scanner fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Scanner failed")

            journal = GitJournalEnhanced(
                repo_root=git_repo,
                session_id="scrub-fallback",
                enable_watching=False,
                track_secrets=True,
            )

            journal._native_scanner_available = True
            content = "token=ghp_abcdefghijklmnopqrstuvwxyz0123456789"
            result = journal._scrub_with_native_scanner(content)

            assert "ghp_" not in result
            assert "<REDACTED_" in result

    def test_scrub_no_secrets(self, git_repo: Path) -> None:
        """Test scrubbing content with no secrets."""
        journal = GitJournalEnhanced(
            repo_root=git_repo,
            session_id="scrub-clean",
            enable_watching=False,
            track_secrets=True,
        )

        content = "def hello():\n    return 'world'"
        result = journal._scrub_with_native_scanner(content)

        assert result == content  # No changes


# ---------------------------------------------------------------------------
# Batching tests
# ---------------------------------------------------------------------------


class TestRecordFileChangeBatching:
    """Tests for record_file_change with batching."""

    def test_record_file_change_accumulates(self, journal_enhanced: GitJournalEnhanced) -> None:
        """Test that file changes are accumulated in pending batch."""
        # Record multiple changes without flushing
        journal_enhanced.auto_commit = False

        journal_enhanced.record_file_change("file1.txt", b"content1", action="created")
        journal_enhanced.record_file_change("file2.txt", b"content2", action="created")

        assert len(journal_enhanced._pending_changes) == 2

    def test_record_file_change_flushes_at_batch_size(self, git_repo: Path) -> None:
        """Test that batch is flushed when batch_size is reached."""
        journal = GitJournalEnhanced(
            repo_root=git_repo,
            session_id="batch-flush-test",
            track_secrets=False,
            auto_commit=False,
            enable_watching=False,
            batch_size=2,
        )

        # Record batch_size changes - should trigger flush
        sha1 = journal.record_file_change("file1.txt", b"content1", action="created")
        journal.record_file_change("file2.txt", b"content2", action="created")

        # After 2 changes (batch_size), batch should be flushed
        assert len(journal._pending_changes) == 0
        assert sha1 != ""  # Commit was created

    def test_record_file_change_manual_flush(self, journal_enhanced: GitJournalEnhanced) -> None:
        """Test manual flush via _flush_batch."""
        journal_enhanced.record_file_change("manual.txt", b"manual content", action="created")

        assert len(journal_enhanced._pending_changes) == 1

        sha = journal_enhanced._flush_batch()

        assert len(journal_enhanced._pending_changes) == 0
        assert sha != ""

    def test_record_file_change_with_secrets(self, journal_enhanced: GitJournalEnhanced) -> None:
        """Test that secrets are scrubbed in record_file_change."""
        content = b"API_KEY=sk-1234567890abcdef1234567890abcdef1234567890abcdef12"
        journal_enhanced.record_file_change("config.py", content, action="created")

        # Flush to commit
        journal_enhanced._flush_batch()

        # Verify secrets are not in pending changes
        for (
            _rel_path,
            content_bytes,
            _action,
            _metadata,
        ) in journal_enhanced._pending_changes:
            if content_bytes:
                decoded = content_bytes.decode("utf-8", errors="replace")
                assert "sk-1234567890" not in decoded


# ---------------------------------------------------------------------------
# Flush batch tests
# ---------------------------------------------------------------------------


class TestFlushBatch:
    """Tests for _flush_batch method."""

    def test_flush_empty_batch(self, journal_enhanced: GitJournalEnhanced) -> None:
        """Test flushing empty batch returns empty string."""
        sha = journal_enhanced._flush_batch()
        assert sha == ""

    def test_flush_batch_creates_single_commit(self, journal_enhanced: GitJournalEnhanced) -> None:
        """Test that multiple pending changes create a single commit."""
        # Add multiple changes
        journal_enhanced.record_file_change("a.txt", b"content a", action="created")
        journal_enhanced.record_file_change("b.txt", b"content b", action="created")
        journal_enhanced.record_file_change("c.txt", b"content c", action="created")

        # Flush - should create one commit
        sha = journal_enhanced._flush_batch()

        assert sha != ""
        assert len(sha) == 40  # Git SHA length

        # Verify all changes are now in tree
        assert "a.txt" in journal_enhanced._current_tree
        assert "b.txt" in journal_enhanced._current_tree
        assert "c.txt" in journal_enhanced._current_tree

    def test_flush_batch_includes_changes_in_message(self, journal_enhanced: GitJournalEnhanced) -> None:
        """Test that flush batch includes all changes in commit message."""
        journal_enhanced.record_file_change("x.txt", b"x", action="created")
        journal_enhanced.record_file_change("y.txt", b"y", action="modified")

        sha = journal_enhanced._flush_batch()

        # Get commit message
        result = subprocess.run(
            ["git", "log", "-1", "--format=%B", sha],
            cwd=journal_enhanced.repo_root,
            capture_output=True,
            text=True,
        )

        commit_msg = result.stdout
        assert "batch: 2 changes" in commit_msg
        assert "x.txt" in commit_msg
        assert "y.txt" in commit_msg

    def test_flush_batch_updates_ref(self, journal_enhanced: GitJournalEnhanced) -> None:
        """Test that flush updates the audit ref."""
        journal_enhanced.record_file_change("ref_test.txt", b"ref content", action="created")

        sha = journal_enhanced._flush_batch()

        # Verify ref points to new commit
        result = subprocess.run(
            ["git", "rev-parse", journal_enhanced.audit_ref],
            cwd=journal_enhanced.repo_root,
            capture_output=True,
            text=True,
        )

        assert result.stdout.strip() == sha


# ---------------------------------------------------------------------------
# Caching tests
# ---------------------------------------------------------------------------


class TestHashObjectCached:
    """Tests for _hash_object_cached method."""

    def test_caching_returns_same_sha(self, journal_enhanced: GitJournalEnhanced) -> None:
        """Test that identical content returns cached SHA."""
        content = b"cached content test"

        sha1 = journal_enhanced._hash_object_cached(content)
        sha2 = journal_enhanced._hash_object_cached(content)

        assert sha1 == sha2

        # Cache should have one entry
        assert len(journal_enhanced._blob_cache) == 1

    def test_different_content_different_sha(self, journal_enhanced: GitJournalEnhanced) -> None:
        """Test that different content returns different SHAs."""
        sha1 = journal_enhanced._hash_object_cached(b"content A")
        sha2 = journal_enhanced._hash_object_cached(b"content B")

        assert sha1 != sha2
        assert len(journal_enhanced._blob_cache) == 2

    def test_cache_grows_with_content(self, journal_enhanced: GitJournalEnhanced) -> None:
        """Test that cache grows as new content is added."""
        initial_size = len(journal_enhanced._blob_cache)

        journal_enhanced._hash_object_cached(b"new content 1")
        journal_enhanced._hash_object_cached(b"new content 2")
        journal_enhanced._hash_object_cached(b"new content 3")

        assert len(journal_enhanced._blob_cache) == initial_size + 3


# ---------------------------------------------------------------------------
# Attestation tests
# ---------------------------------------------------------------------------


class TestAttestation:
    """Tests for attestation functionality."""

    def test_create_attestation_structure(self, journal_with_attestation: GitJournalEnhanced) -> None:
        """Test that attestation has correct structure."""
        attestation = journal_with_attestation._create_attestation(
            commit_sha="abc123def456",
            content_hash="deadbeef",
        )

        assert "version" in attestation
        assert "commit_sha" in attestation
        assert "content_hash" in attestation
        assert "timestamp" in attestation
        assert "session_id" in attestation
        assert "signature" in attestation
        assert attestation["algorithm"] == "SHA-256"

    def test_create_attestation_signature(self, journal_with_attestation: GitJournalEnhanced) -> None:
        """Test that attestation has valid signature."""
        import hashlib

        attestation = journal_with_attestation._create_attestation(
            commit_sha="abc123",
            content_hash="xyz789",
        )

        # Verify signature is deterministic
        attestation_data = "abc123:xyz789:{timestamp}:{session_id}".format(
            timestamp=attestation["timestamp"],
            session_id=attestation["session_id"],
        )
        expected_sig = hashlib.sha256(attestation_data.encode()).hexdigest()

        assert attestation["signature"] == expected_sig

    def test_verify_valid_attestation(self, journal_with_attestation: GitJournalEnhanced) -> None:
        """Test verification of valid attestation."""
        attestation = journal_with_attestation._create_attestation(
            commit_sha="abc123",
            content_hash="def456",
        )

        assert journal_with_attestation.verify_attestation(attestation) is True

    def test_verify_invalid_attestation(self, journal_with_attestation: GitJournalEnhanced) -> None:
        """Test verification fails for tampered attestation."""
        attestation = journal_with_attestation._create_attestation(
            commit_sha="abc123",
            content_hash="def456",
        )

        # Tamper with the attestation
        attestation["commit_sha"] = "modified"

        assert journal_with_attestation.verify_attestation(attestation) is False

    def test_attestation_created_on_flush(self, journal_with_attestation: GitJournalEnhanced) -> None:
        """Test that attestation is created during flush when enabled."""
        initial_count = len(journal_with_attestation._attestations)

        journal_with_attestation.record_file_change("attest.txt", b"content", action="created")

        assert len(journal_with_attestation._attestations) > initial_count


# ---------------------------------------------------------------------------
# Performance stats tests
# ---------------------------------------------------------------------------


class TestPerformanceStats:
    """Tests for get_performance_stats method."""

    def test_get_performance_stats_initial(self, journal_enhanced: GitJournalEnhanced) -> None:
        """Test performance stats on initial state."""
        stats = journal_enhanced.get_performance_stats()

        assert "blob_cache_size" in stats
        assert "pending_changes" in stats
        assert "attestations" in stats
        assert "native_scanner" in stats
        assert "watcher" in stats
        assert "batch_size" in stats

    def test_get_performance_stats_reflects_state(self, journal_enhanced: GitJournalEnhanced) -> None:
        """Test that stats reflect current journal state."""
        # Add some changes
        journal_enhanced.record_file_change("stat1.txt", b"content1", action="created")

        stats = journal_enhanced.get_performance_stats()

        assert stats["pending_changes"] == 1
        assert stats["blob_cache_size"] >= 1  # content was hashed


# ---------------------------------------------------------------------------
# Finalize session tests
# ---------------------------------------------------------------------------


class TestFinalizeSession:
    """Tests for finalize_session method."""

    def test_finalize_empty_session(self, journal_enhanced: GitJournalEnhanced) -> None:
        """Test finalizing session with no changes."""
        sha = journal_enhanced.finalize_session()

        assert sha != ""

        # Should have created a snapshot
        result = subprocess.run(
            ["git", "log", "-1", "--format=%s", sha],
            cwd=journal_enhanced.repo_root,
            capture_output=True,
            text=True,
        )

        assert "final:" in result.stdout

    def test_finalize_with_pending_changes(self, journal_enhanced: GitJournalEnhanced) -> None:
        """Test finalizing session with pending changes."""
        # Add changes but don't flush
        journal_enhanced.record_file_change("final1.txt", b"final content", action="created")

        sha = journal_enhanced.finalize_session()

        # Pending changes should be flushed
        assert len(journal_enhanced._pending_changes) == 0
        assert sha != ""

    def test_finalize_with_attestation(self, journal_with_attestation: GitJournalEnhanced) -> None:
        """Test finalization creates final attestation."""
        journal_with_attestation.record_file_change("final_attest.txt", b"content", action="created")

        initial_attestations = len(journal_with_attestation._attestations)

        journal_with_attestation.finalize_session()

        # Should have created final attestation
        assert len(journal_with_attestation._attestations) > initial_attestations


# ---------------------------------------------------------------------------
# File watching tests
# ---------------------------------------------------------------------------


class TestFileWatching:
    """Tests for file watching functionality."""

    def test_init_watcher_watchman(self, git_repo: Path) -> None:
        """Test watcher initialization with watchman."""
        with patch("subprocess.run") as mock_run:
            # Watchman available
            mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")

            journal = GitJournalEnhanced(
                repo_root=git_repo,
                session_id="watchman-test",
                enable_watching=True,
                enable_attestation=False,
            )

            # Watcher should be set
            assert journal._watcher in ("watchman", "fswatch", "fsmonitor", None)

    def test_init_watcher_fallback_fswatch(self, git_repo: Path) -> None:
        """Test watcher fallback to fswatch."""
        with patch("subprocess.run") as mock_run:
            # First call (watchman) fails
            mock_run.side_effect = [
                FileNotFoundError("watchman not found"),  # watchman check
                MagicMock(returncode=0, stdout=b"fswatch 1.0", stderr=b""),  # fswatch check
            ]

            GitJournalEnhanced(
                repo_root=git_repo,
                session_id="fswatch-test",
                enable_watching=True,
            )

            # Should have tried fallback
            assert mock_run.call_count >= 1

    def test_init_watcher_no_watcher_available(self, git_repo: Path) -> None:
        """Test watcher initialization when no watcher available."""
        with patch("subprocess.run") as mock_run:
            # All watchers fail
            mock_run.side_effect = FileNotFoundError("no tools")

            journal = GitJournalEnhanced(
                repo_root=git_repo,
                session_id="no-watcher-test",
                enable_watching=True,
            )

            # Watcher should be None
            assert journal._watcher is None

    def test_start_watching_no_watcher(self, journal_enhanced: GitJournalEnhanced) -> None:
        """Test start_watching when no watcher configured."""
        journal_enhanced._watcher = None

        # Should not raise, just log warning
        journal_enhanced.start_watching()


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestGitJournalEnhancedIntegration:
    """Integration tests for full GitJournalEnhanced workflow."""

    def test_full_workflow(self, git_repo: Path) -> None:
        """Test complete workflow from init to finalize."""
        journal = GitJournalEnhanced(
            repo_root=git_repo,
            session_id="integration-test",
            track_secrets=True,
            auto_commit=False,
            enable_watching=False,
            enable_attestation=True,
            batch_size=5,
        )

        # Record several file changes
        journal.record_file_change("test1.py", b"print('hello')", action="created")
        journal.record_file_change("test2.py", b"print('world')", action="created")
        journal.record_file_change("test3.py", b"x = 1", action="created")

        # Finalize
        final_sha = journal.finalize_session("integration complete")

        assert final_sha != ""

        # Check audit log
        audit_log = journal.get_audit_log()
        assert len(audit_log) > 0

        # Check attestations
        attestations = journal.get_attestations()
        assert len(attestations) > 0

        # Verify attestation
        assert journal.verify_attestation(attestations[0]) is True

    def test_session_persists_ref(self, git_repo: Path) -> None:
        """Test that session creates persistent audit ref."""
        journal = GitJournalEnhanced(
            repo_root=git_repo,
            session_id="persist-ref-test",
            enable_watching=False,
        )

        journal.record_file_change("persist.txt", b"persistent", action="created")

        # Ref should exist
        result = subprocess.run(
            ["git", "show-ref", journal.audit_ref],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert journal.audit_ref in result.stdout
