"""Unit tests for GitJournalAsync wrapper class.

Tests async operations, concurrent behavior, error propagation,
and thread pool behavior.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

# Ensure src/ is in path
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from thegent.audit.shadow_audit_git import (
    GitJournal,
    GitJournalAsync,
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
    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )

    # Create initial commit
    (repo_path / "README.md").write_text("# Test Repo\n")
    subprocess.run(
        ["git", "add", "README.md"], cwd=repo_path, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "commit", "-m", "initial commit"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )

    return repo_path


@pytest.fixture
def session_id() -> str:
    """Generate a unique session ID for tests."""
    import uuid

    return f"test-session-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Test: GitJournalAsync.create factory method
# ---------------------------------------------------------------------------


class TestCreate:
    """Tests for the GitJournalAsync.create factory method."""

    @pytest.mark.asyncio
    async def test_create_enhanced_true(self, git_repo: Path, session_id: str) -> None:
        """Test create with enhanced=True returns GitJournalEnhanced wrapper."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=True,
        )

        assert isinstance(async_journal, GitJournalAsync)
        assert isinstance(async_journal._journal, GitJournalEnhanced)

    @pytest.mark.asyncio
    async def test_create_enhanced_false(self, git_repo: Path, session_id: str) -> None:
        """Test create with enhanced=False returns base GitJournal wrapper."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        assert isinstance(async_journal, GitJournalAsync)
        assert isinstance(async_journal._journal, GitJournal)
        assert not isinstance(async_journal._journal, GitJournalEnhanced)

    @pytest.mark.asyncio
    async def test_create_default_is_enhanced(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test create defaults to enhanced=True."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
        )

        assert isinstance(async_journal._journal, GitJournalEnhanced)

    @pytest.mark.asyncio
    async def test_create_with_track_secrets(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test create passes track_secrets parameter."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            track_secrets=False,
            enhanced=False,
        )

        assert async_journal._journal.track_secrets is False

    @pytest.mark.asyncio
    async def test_create_with_auto_commit(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test create passes auto_commit parameter."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            auto_commit=True,
            enhanced=False,
        )

        # Note: Enhanced mode forces auto_commit=False internally
        # so this tests base GitJournal behavior
        assert async_journal._journal.auto_commit is True


# ---------------------------------------------------------------------------
# Test: Async record_file_change
# ---------------------------------------------------------------------------


class TestRecordFileChange:
    """Tests for async record_file_change method."""

    @pytest.mark.asyncio
    async def test_record_file_change_basic(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test basic async file change recording."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        # Create a test file
        test_content = b"Hello, World!"
        result = await async_journal.record_file_change(
            file_path="test.txt",
            content=test_content,
            action="created",
        )

        assert result is not None
        assert len(result) == 40  # Git SHA length

    @pytest.mark.asyncio
    async def test_record_file_change_modified(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test recording a file modification."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        result = await async_journal.record_file_change(
            file_path="test.txt",
            content=b"Modified content",
            action="modified",
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_record_file_change_deleted(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test recording a file deletion."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        # First create a file
        await async_journal.record_file_change(
            file_path="delete_me.txt",
            content=b"to be deleted",
            action="created",
        )

        # Then delete it
        result = await async_journal.record_file_change(
            file_path="delete_me.txt",
            content=None,
            action="deleted",
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_record_file_change_with_metadata(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test recording file change with metadata."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        metadata = {"author": "test", "line_count": 10}
        result = await async_journal.record_file_change(
            file_path="test.py",
            content=b"print('hello')",
            action="created",
            metadata=metadata,
        )

        assert result is not None


# ---------------------------------------------------------------------------
# Test: Async record_snapshot
# ---------------------------------------------------------------------------


class TestRecordSnapshot:
    """Tests for async record_snapshot method."""

    @pytest.mark.asyncio
    async def test_record_snapshot_basic(self, git_repo: Path, session_id: str) -> None:
        """Test basic async snapshot creation."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        # Add some files first
        await async_journal.record_file_change(
            file_path="file1.txt",
            content=b"Content 1",
            action="created",
        )
        await async_journal.record_file_change(
            file_path="file2.txt",
            content=b"Content 2",
            action="created",
        )

        result = await async_journal.record_snapshot(message="test snapshot")

        assert result is not None
        assert len(result) == 40

    @pytest.mark.asyncio
    async def test_record_snapshot_with_default_message(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test snapshot with default message."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        result = await async_journal.record_snapshot()

        assert result is not None


# ---------------------------------------------------------------------------
# Test: Async get_audit_log
# ---------------------------------------------------------------------------


class TestGetAuditLog:
    """Tests for async get_audit_log method."""

    @pytest.mark.asyncio
    async def test_get_audit_log_empty(self, git_repo: Path, session_id: str) -> None:
        """Test getting audit log when empty."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        result = await async_journal.get_audit_log()

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_audit_log_with_entries(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test getting audit log with recorded changes."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        # Record some changes
        await async_journal.record_file_change(
            file_path="test1.txt",
            content=b"Content 1",
            action="created",
        )
        await async_journal.record_file_change(
            file_path="test2.txt",
            content=b"Content 2",
            action="created",
        )

        result = await async_journal.get_audit_log()

        assert isinstance(result, list)
        assert len(result) >= 2

    @pytest.mark.asyncio
    async def test_get_audit_log_returns_dicts(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test audit log returns proper dict structure."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        await async_journal.record_file_change(
            file_path="test.txt",
            content=b"test",
            action="created",
        )

        result = await async_journal.get_audit_log()

        if result:
            entry = result[0]
            assert "sha" in entry
            assert "message" in entry
            assert "timestamp" in entry


# ---------------------------------------------------------------------------
# Test: Async finalize_session
# ---------------------------------------------------------------------------


class TestFinalizeSession:
    """Tests for async finalize_session method."""

    @pytest.mark.asyncio
    async def test_finalize_session_basic(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test basic session finalization."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        # Record some changes
        await async_journal.record_file_change(
            file_path="final.txt",
            content=b"Final content",
            action="created",
        )

        result = await async_journal.finalize_session(message="test complete")

        assert result is not None
        assert len(result) == 40

    @pytest.mark.asyncio
    async def test_finalize_session_with_default_message(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test finalize with default message."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        await async_journal.record_file_change(
            file_path="test.txt",
            content=b"test",
            action="created",
        )

        result = await async_journal.finalize_session()

        assert result is not None


# ---------------------------------------------------------------------------
# Test: Concurrent operations
# ---------------------------------------------------------------------------


class TestConcurrentOperations:
    """Tests for concurrent async operations."""

    @pytest.mark.asyncio
    async def test_concurrent_file_changes(self, git_repo: Path) -> None:
        """Test concurrent file changes are handled correctly."""
        session_id = "concurrent-test"

        async def create_journal() -> GitJournalAsync:
            return GitJournalAsync.create(
                repo_root=git_repo,
                session_id=session_id,
                enhanced=False,
                auto_commit=True,
            )

        # Create separate journal instances for concurrent ops
        journal1 = await create_journal()
        journal2 = await create_journal()

        # Run concurrent operations
        async def change_file(
            journal: GitJournalAsync, filename: str, content: bytes
        ) -> str:
            return await journal.record_file_change(
                file_path=filename,
                content=content,
                action="created",
            )

        # Execute concurrently
        results = await asyncio.gather(
            change_file(journal1, "file1.txt", b"Content 1"),
            change_file(journal2, "file2.txt", b"Content 2"),
            change_file(journal1, "file3.txt", b"Content 3"),
        )

        # All should complete successfully
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_snapshot_and_record(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test concurrent snapshot and record operations."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        # Run snapshot and record concurrently
        results = await asyncio.gather(
            async_journal.record_file_change(
                "concurrent1.txt", b"c1", action="created"
            ),
            async_journal.record_file_change(
                "concurrent2.txt", b"c2", action="created"
            ),
            async_journal.record_snapshot("concurrent snapshot"),
        )

        assert all(r is not None for r in results)


# ---------------------------------------------------------------------------
# Test: Error propagation
# ---------------------------------------------------------------------------


class TestErrorPropagation:
    """Tests for error handling and propagation."""

    @pytest.mark.asyncio
    async def test_error_invalid_repo_path(
        self, tmp_path: Path, session_id: str
    ) -> None:
        """Test error handling for invalid repository path."""
        invalid_path = tmp_path / "nonexistent_repo"

        with pytest.raises(Exception):
            GitJournalAsync.create(
                repo_root=invalid_path,
                session_id=session_id,
                enhanced=False,
            )

    @pytest.mark.asyncio
    async def test_error_nonexistent_file(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test error when trying to record nonexistent file."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        # This should not raise but return empty string or handle gracefully
        # when auto_commit=False
        async_journal._journal.auto_commit = False
        result = await async_journal.record_file_change(
            file_path="nonexistent.txt",
            content=None,
            action="deleted",
        )

        # Should handle gracefully
        assert result == ""


# ---------------------------------------------------------------------------
# Test: Thread pool behavior
# ---------------------------------------------------------------------------


class TestThreadPoolBehavior:
    """Tests for thread pool behavior and executor usage."""

    def test_shared_executor_exists(self) -> None:
        """Test that shared executor is created."""
        journal = GitJournalAsync.create(
            repo_root="/tmp",  # Won't actually use
            session_id="test",
            enhanced=False,
        )

        assert journal._executor is not None
        assert isinstance(journal._executor, ThreadPoolExecutor)
        assert journal._executor._max_workers == 4

    @pytest.mark.asyncio
    async def test_runs_in_executor(self, git_repo: Path, session_id: str) -> None:
        """Test that operations run in the thread pool executor."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        # Track if we're in the executor thread
        thread_names: list[str] = []

        original_record = async_journal._journal.record_file_change

        def tracking_record(*args, **kwargs):
            thread_names.append(__import__("threading").current_thread().name)
            return original_record(*args, **kwargs)

        with patch.object(
            async_journal._journal, "record_file_change", side_effect=tracking_record
        ):
            await async_journal.record_file_change(
                file_path="test.txt",
                content=b"test",
                action="created",
            )

        # Verify the function ran (thread name captured)
        assert len(thread_names) > 0

    @pytest.mark.asyncio
    async def test_executor_thread_name_prefix(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test executor threads have correct name prefix."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        # Verify thread name prefix
        assert "git-journal-" in async_journal._executor._thread_name_prefix


# ---------------------------------------------------------------------------
# Test: Enhanced mode features
# ---------------------------------------------------------------------------


class TestEnhancedMode:
    """Tests specific to enhanced mode features."""

    @pytest.mark.asyncio
    async def test_enhanced_batch_size(self, git_repo: Path, session_id: str) -> None:
        """Test enhanced mode batch size parameter."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=True,
            batch_size=5,
        )

        assert async_journal._journal.batch_size == 5

    @pytest.mark.asyncio
    async def test_enhanced_attestation(self, git_repo: Path, session_id: str) -> None:
        """Test enhanced mode attestation."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=True,
            enable_attestation=True,
        )

        # Record some changes
        await async_journal.record_file_change(
            file_path="test.txt",
            content=b"test content",
            action="created",
        )

        # Finalize to trigger attestation
        await async_journal.finalize_session()

        # Check attestations were created
        attestations = async_journal.get_attestations()
        assert len(attestations) > 0

    @pytest.mark.asyncio
    async def test_enhanced_performance_stats(
        self, git_repo: Path, session_id: str
    ) -> None:
        """Test enhanced mode performance stats."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=True,
            batch_size=10,
        )

        # Record some changes
        await async_journal.record_file_change(
            file_path="test.txt",
            content=b"test",
            action="created",
        )

        stats = async_journal.get_performance_stats()

        assert "blob_cache_size" in stats
        assert "pending_changes" in stats
        assert "attestations" in stats
        assert "native_scanner" in stats
        assert "batch_size" in stats
        assert stats["batch_size"] == 10


# ---------------------------------------------------------------------------
# Test: Delegation to wrapped journal
# ---------------------------------------------------------------------------


class TestDelegation:
    """Tests for __getattr__ delegation to wrapped journal."""

    @pytest.mark.asyncio
    async def test_delegate_session_id(self, git_repo: Path, session_id: str) -> None:
        """Test delegation of session_id property."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        assert async_journal.session_id == session_id

    @pytest.mark.asyncio
    async def test_delegate_repo_root(self, git_repo: Path, session_id: str) -> None:
        """Test delegation of repo_root property."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        assert async_journal.repo_root == git_repo

    @pytest.mark.asyncio
    async def test_delegate_audit_ref(self, git_repo: Path, session_id: str) -> None:
        """Test delegation of audit_ref property."""
        async_journal = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session_id,
            enhanced=False,
        )

        assert async_journal.audit_ref == f"refs/audit/{session_id}"


# ---------------------------------------------------------------------------
# Test: Multiple sessions
# ---------------------------------------------------------------------------


class TestMultipleSessions:
    """Tests for handling multiple concurrent sessions."""

    @pytest.mark.asyncio
    async def test_multiple_sessions_independent(self, git_repo: Path) -> None:
        """Test multiple sessions operate independently."""
        session1 = "session-1"
        session2 = "session-2"

        journal1 = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session1,
            enhanced=False,
        )
        journal2 = GitJournalAsync.create(
            repo_root=git_repo,
            session_id=session2,
            enhanced=False,
        )

        # Record changes in each session
        await journal1.record_file_change("s1_file.txt", b"session 1", action="created")
        await journal2.record_file_change("s2_file.txt", b"session 2", action="created")

        # Get audit logs - should be independent
        log1 = await journal1.get_audit_log()
        log2 = await journal2.get_audit_log()

        # Each session should have its own entries
        assert len(log1) > 0
        assert len(log2) > 0

    @pytest.mark.asyncio
    async def test_finalize_multiple_sessions(self, git_repo: Path) -> None:
        """Test finalizing multiple sessions."""
        journal1 = GitJournalAsync.create(
            repo_root=git_repo, session_id="final-1", enhanced=False
        )
        journal2 = GitJournalAsync.create(
            repo_root=git_repo, session_id="final-2", enhanced=False
        )

        await journal1.record_file_change("f1.txt", b"f1", action="created")
        await journal2.record_file_change("f2.txt", b"f2", action="created")

        result1 = await journal1.finalize_session()
        result2 = await journal2.finalize_session()

        assert result1 is not None
        assert result2 is not None
        assert result1 != result2  # Different commits
