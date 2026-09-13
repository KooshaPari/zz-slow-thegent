"""Tests for thegent.integrations.reflection_rollback — Work stream snapshot and rollback.

@trace WL-185
"""

from __future__ import annotations

from pathlib import Path

import pytest

from thegent.integrations.reflection_rollback import (
    ReflectionRollbackManager,
    RollbackSnapshot,
)


class TestRollbackSnapshot:
    """Test RollbackSnapshot dataclass. @trace WL-185"""

    @pytest.mark.requirement("WL-185")
    def test_create_snapshot(self) -> None:
        """Can create a RollbackSnapshot with all fields."""
        snapshot = RollbackSnapshot(
            snapshot_id="snap123",
            timestamp="2026-02-22T12:00:00+00:00",
            work_stream_content="# Work Stream\ntest content",
            cycle_id="cycle-456",
        )

        assert snapshot.snapshot_id == "snap123"
        assert snapshot.timestamp == "2026-02-22T12:00:00+00:00"
        assert snapshot.work_stream_content == "# Work Stream\ntest content"
        assert snapshot.cycle_id == "cycle-456"

    @pytest.mark.requirement("WL-185")
    def test_snapshot_parses_timestamp(self) -> None:
        """RollbackSnapshot parses timestamp into datetime."""
        snapshot = RollbackSnapshot(
            snapshot_id="snap123",
            timestamp="2026-02-22T12:00:00+00:00",
            work_stream_content="content",
            cycle_id="cycle",
        )

        # Should not raise; _created_at is set
        assert snapshot._created_at is not None


class TestReflectionRollbackManager:
    """Test ReflectionRollbackManager operations. @trace WL-185"""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> ReflectionRollbackManager:
        """Provide a RollbackManager with tmp snapshots dir."""
        return ReflectionRollbackManager(snapshots_dir=tmp_path / "snapshots")

    @pytest.fixture
    def work_stream_file(self, tmp_path: Path) -> Path:
        """Create a temporary work stream file."""
        ws = tmp_path / "WORK_STREAM.md"
        ws.write_text("# Work Stream\n\n## P0 Items\n\nSome content", encoding="utf-8")
        return ws

    @pytest.mark.requirement("WL-185")
    def test_take_snapshot(
        self, manager: ReflectionRollbackManager, work_stream_file: Path
    ) -> None:
        """Can take a snapshot of work stream content."""
        snapshot = manager.take_snapshot(work_stream_file)

        assert snapshot.snapshot_id
        assert snapshot.timestamp
        assert (
            snapshot.work_stream_content
            == "# Work Stream\n\n## P0 Items\n\nSome content"
        )
        assert len(snapshot.snapshot_id) == 8  # UUID truncated to 8 chars

    @pytest.mark.requirement("WL-185")
    def test_take_snapshot_with_cycle_id(
        self, manager: ReflectionRollbackManager, work_stream_file: Path
    ) -> None:
        """Caller-provided cycle_id is persisted in snapshot metadata."""
        snapshot = manager.take_snapshot(work_stream_file, cycle_id="cycle-xyz")

        assert snapshot.cycle_id == "cycle-xyz"

    @pytest.mark.requirement("WL-185")
    def test_take_snapshot_file_not_found(
        self, manager: ReflectionRollbackManager
    ) -> None:
        """take_snapshot raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            manager.take_snapshot(Path("/nonexistent/WORK_STREAM.md"))

    @pytest.mark.requirement("WL-185")
    def test_take_snapshot_persists_to_disk(
        self, manager: ReflectionRollbackManager, work_stream_file: Path
    ) -> None:
        """Snapshots are persisted to disk."""
        snapshot = manager.take_snapshot(work_stream_file)
        snapshot_file = manager._snapshots_dir / f"{snapshot.snapshot_id}.json"

        assert snapshot_file.exists()

    @pytest.mark.requirement("WL-185")
    def test_list_snapshots_empty(self, manager: ReflectionRollbackManager) -> None:
        """list_snapshots returns empty list when none exist."""
        result = manager.list_snapshots()
        assert result == []

    @pytest.mark.requirement("WL-185")
    def test_list_snapshots_multiple(
        self, manager: ReflectionRollbackManager, work_stream_file: Path
    ) -> None:
        """list_snapshots returns all snapshots, sorted by timestamp (newest first)."""
        # Take first snapshot
        snap1 = manager.take_snapshot(work_stream_file)

        # Modify and take second snapshot
        work_stream_file.write_text(
            "# Work Stream\n\nUpdated content", encoding="utf-8"
        )
        snap2 = manager.take_snapshot(work_stream_file)

        snapshots = manager.list_snapshots()
        assert len(snapshots) == 2
        # Newest first
        assert snapshots[0].snapshot_id == snap2.snapshot_id
        assert snapshots[1].snapshot_id == snap1.snapshot_id

    @pytest.mark.requirement("WL-185")
    def test_rollback_to(
        self, manager: ReflectionRollbackManager, work_stream_file: Path, tmp_path: Path
    ) -> None:
        """Can restore work stream from a snapshot."""
        # Take initial snapshot
        original_content = "# Original content"
        work_stream_file.write_text(original_content, encoding="utf-8")
        snapshot = manager.take_snapshot(work_stream_file)

        # Modify file
        work_stream_file.write_text("# Modified content", encoding="utf-8")
        assert work_stream_file.read_text(encoding="utf-8") == "# Modified content"

        # Rollback
        manager.rollback_to(snapshot.snapshot_id, work_stream_file)
        assert work_stream_file.read_text(encoding="utf-8") == original_content

    @pytest.mark.requirement("WL-185")
    def test_rollback_to_not_found(
        self, manager: ReflectionRollbackManager, tmp_path: Path
    ) -> None:
        """rollback_to raises FileNotFoundError for missing snapshot."""
        ws = tmp_path / "WORK_STREAM.md"
        ws.write_text("content", encoding="utf-8")

        with pytest.raises(FileNotFoundError):
            manager.rollback_to("nonexistent", ws)

    @pytest.mark.requirement("WL-185")
    def test_cleanup_old_snapshots(
        self, manager: ReflectionRollbackManager, work_stream_file: Path
    ) -> None:
        """cleanup_old_snapshots keeps only N most recent."""
        # Create 7 snapshots
        snapshots = []
        for i in range(7):
            work_stream_file.write_text(f"# Content {i}", encoding="utf-8")
            snapshots.append(manager.take_snapshot(work_stream_file))

        # Clean up, keeping last 5
        manager.cleanup_old_snapshots(keep_last_n=5)

        remaining = manager.list_snapshots()
        assert len(remaining) == 5
        # Newest 5 should remain
        remaining_ids = {snap.snapshot_id for snap in remaining}
        kept_ids = {snap.snapshot_id for snap in snapshots[-5:]}
        assert remaining_ids == kept_ids
