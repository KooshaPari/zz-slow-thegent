"""Tests for WL-175: Single-Writer Lock Discipline.

@pytest.mark.requirement("WL-175")
"""

from __future__ import annotations

from pathlib import Path

import orjson as json
import pytest

from thegent.integrations.writer_lock import SingleWriterLock

# ---------------------------------------------------------------------------
# Test: Lock Acquisition and Release
# ---------------------------------------------------------------------------


class TestLockAcquisition:
    """Test lock acquisition and release."""

    @pytest.mark.requirement("WL-175")
    def test_acquire_lock(self, tmp_path: Path) -> None:
        """Test acquiring a lock."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        assert lock.acquire("agent-001")
        assert lock.is_locked()

    @pytest.mark.requirement("WL-175")
    def test_acquire_lock_creates_file(self, tmp_path: Path) -> None:
        """Test that acquiring a lock creates the lockfile."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        lock.acquire("agent-001")
        assert lock_path.exists()

    @pytest.mark.requirement("WL-175")
    def test_acquire_lock_creates_parent_directory(self, tmp_path: Path) -> None:
        """Test that acquiring a lock creates parent directories."""
        lock_path = tmp_path / "subdir" / "another" / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        lock.acquire("agent-001")
        assert lock_path.exists()
        assert lock_path.parent.exists()

    @pytest.mark.requirement("WL-175")
    def test_lock_file_contains_owner_info(self, tmp_path: Path) -> None:
        """Test that lockfile contains owner and timestamp."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        lock.acquire("agent-001")

        data = json.loads(lock_path.read_text())
        assert data["owner"] == "agent-001"
        assert "acquired_at" in data

    @pytest.mark.requirement("WL-175")
    def test_release_lock(self, tmp_path: Path) -> None:
        """Test releasing a lock."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        lock.acquire("agent-001")
        assert lock.is_locked()

        lock.release("agent-001")
        assert not lock.is_locked()

    @pytest.mark.requirement("WL-175")
    def test_release_removes_file(self, tmp_path: Path) -> None:
        """Test that releasing a lock removes the lockfile."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        lock.acquire("agent-001")
        assert lock_path.exists()

        lock.release("agent-001")
        assert not lock_path.exists()

    @pytest.mark.requirement("WL-175")
    def test_release_by_wrong_owner_is_noop(self, tmp_path: Path) -> None:
        """Test that releasing with wrong owner ID is a no-op."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        lock.acquire("agent-001")
        assert lock.is_locked()

        # Try to release with different owner
        lock.release("agent-002")
        # Lock should still be held
        assert lock.is_locked()
        assert lock.get_owner() == "agent-001"


# ---------------------------------------------------------------------------
# Test: Lock Contention
# ---------------------------------------------------------------------------


class TestLockContention:
    """Test behavior when multiple agents contend for the lock."""

    @pytest.mark.requirement("WL-175")
    def test_cannot_acquire_if_held_by_other(self, tmp_path: Path) -> None:
        """Test that acquire fails if lock is held by another owner."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        assert lock.acquire("agent-001")
        assert not lock.acquire("agent-002")

    @pytest.mark.requirement("WL-175")
    def test_can_reacquire_own_lock(self, tmp_path: Path) -> None:
        """Test that owner can re-acquire their own lock."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        assert lock.acquire("agent-001")
        # Re-acquire should succeed (idempotent)
        assert lock.acquire("agent-001")

    @pytest.mark.requirement("WL-175")
    def test_multiple_lock_instances_same_file(self, tmp_path: Path) -> None:
        """Test multiple lock instances pointing to same file."""
        lock_path = tmp_path / "lock.json"
        lock1 = SingleWriterLock(lock_path=lock_path)
        lock2 = SingleWriterLock(lock_path=lock_path)

        assert lock1.acquire("agent-001")
        assert not lock2.acquire("agent-002")
        assert lock2.get_owner() == "agent-001"


# ---------------------------------------------------------------------------
# Test: Lock Status Queries
# ---------------------------------------------------------------------------


class TestLockStatusQueries:
    """Test lock status inspection methods."""

    @pytest.mark.requirement("WL-175")
    def test_is_locked_when_not_held(self, tmp_path: Path) -> None:
        """Test is_locked returns False when not held."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        assert not lock.is_locked()

    @pytest.mark.requirement("WL-175")
    def test_is_locked_when_held(self, tmp_path: Path) -> None:
        """Test is_locked returns True when held."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        lock.acquire("agent-001")
        assert lock.is_locked()

    @pytest.mark.requirement("WL-175")
    def test_get_owner_when_not_held(self, tmp_path: Path) -> None:
        """Test get_owner returns None when lock not held."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        assert lock.get_owner() is None

    @pytest.mark.requirement("WL-175")
    def test_get_owner_when_held(self, tmp_path: Path) -> None:
        """Test get_owner returns owner when lock held."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        lock.acquire("agent-001")
        assert lock.get_owner() == "agent-001"

    @pytest.mark.requirement("WL-175")
    def test_get_owner_after_release(self, tmp_path: Path) -> None:
        """Test get_owner returns None after release."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        lock.acquire("agent-001")
        assert lock.get_owner() == "agent-001"

        lock.release("agent-001")
        assert lock.get_owner() is None


# ---------------------------------------------------------------------------
# Test: Emergency Force Release
# ---------------------------------------------------------------------------


class TestForceRelease:
    """Test emergency force release."""

    @pytest.mark.requirement("WL-175")
    def test_force_release(self, tmp_path: Path) -> None:
        """Test force releasing a lock."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        lock.acquire("agent-001")
        assert lock.is_locked()

        # Force release (no owner check)
        lock.force_release()
        assert not lock.is_locked()

    @pytest.mark.requirement("WL-175")
    def test_force_release_when_not_locked(self, tmp_path: Path) -> None:
        """Test force release when lock is not held (no-op)."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        # Should not raise
        lock.force_release()
        assert not lock.is_locked()

    @pytest.mark.requirement("WL-175")
    def test_force_release_ignores_ownership(self, tmp_path: Path) -> None:
        """Test that force release ignores ownership."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        lock.acquire("agent-001")

        # Force release (even though we're "agent-002")
        lock.force_release()
        assert not lock.is_locked()


# ---------------------------------------------------------------------------
# Test: Edge Cases and Robustness
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.requirement("WL-175")
    def test_release_nonexistent_lock(self, tmp_path: Path) -> None:
        """Test releasing a lock that doesn't exist (no-op)."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        # Should not raise
        lock.release("agent-001")

    @pytest.mark.requirement("WL-175")
    def test_get_owner_with_corrupted_file(self, tmp_path: Path) -> None:
        """Test get_owner handles corrupted lockfile gracefully."""
        lock_path = tmp_path / "lock.json"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text("invalid json")

        lock = SingleWriterLock(lock_path=lock_path)
        # Should return None (corrupted file)
        assert lock.get_owner() is None

    @pytest.mark.requirement("WL-175")
    def test_acquire_with_empty_owner_id(self, tmp_path: Path) -> None:
        """Test acquiring lock with empty owner ID."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        # Should succeed (no validation of owner_id)
        assert lock.acquire("")

    @pytest.mark.requirement("WL-175")
    def test_default_lock_path(self) -> None:
        """Test that default lock path is docs/reference/autosync.lock."""
        lock = SingleWriterLock()
        assert lock.lock_path == Path("docs/reference/autosync.lock")

    @pytest.mark.requirement("WL-175")
    def test_multiple_sequential_acquisitions(self, tmp_path: Path) -> None:
        """Test acquiring and releasing lock multiple times."""
        lock_path = tmp_path / "lock.json"
        lock = SingleWriterLock(lock_path=lock_path)

        for i in range(3):
            assert lock.acquire(f"agent-{i:03d}")
            assert lock.is_locked()
            lock.release(f"agent-{i:03d}")
            assert not lock.is_locked()
