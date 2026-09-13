"""Tests for thegent.integrations.checkpoint_resume — Rolling checkpoint resume.

@trace WL-284
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from thegent.integrations.checkpoint_resume import Checkpoint, CheckpointStore


class TestCheckpoint:
    """Test Checkpoint dataclass."""

    @pytest.mark.requirement("WL-284")
    def test_checkpoint_creation(self) -> None:
        """Can create a Checkpoint with required fields."""
        created_at = datetime.now(UTC)
        checkpoint = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=created_at,
        )

        assert checkpoint.checkpoint_id == "cp-001"
        assert checkpoint.cycle_id == "cycle-1"
        assert checkpoint.last_processed_idx == 100
        assert checkpoint.total_items == 1000
        assert checkpoint.created_at == created_at


class TestCheckpointStoreSave:
    """Test CheckpointStore.save operations. @trace WL-284"""

    @pytest.mark.requirement("WL-284")
    def test_save_creates_directory(self, tmp_path: Path) -> None:
        """save creates the store directory if it doesn't exist."""
        store_dir = tmp_path / "nonexistent" / "path"
        checkpoint = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=datetime.now(UTC),
        )

        CheckpointStore.save(checkpoint, store_dir)

        assert store_dir.exists()

    @pytest.mark.requirement("WL-284")
    def test_save_writes_json_file(self, tmp_path: Path) -> None:
        """save writes checkpoint as JSON file."""
        checkpoint = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        )

        path = CheckpointStore.save(checkpoint, tmp_path)

        assert path.exists()
        assert path.suffix == ".json"
        assert path.name == "cp-001.json"

    @pytest.mark.requirement("WL-284")
    def test_save_returns_path(self, tmp_path: Path) -> None:
        """save returns path to the saved file."""
        checkpoint = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=datetime.now(UTC),
        )

        result = CheckpointStore.save(checkpoint, tmp_path)

        assert isinstance(result, Path)
        assert result.exists()

    @pytest.mark.requirement("WL-284")
    def test_save_json_content(self, tmp_path: Path) -> None:
        """save writes valid JSON with checkpoint data."""
        import json

        checkpoint = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        )

        CheckpointStore.save(checkpoint, tmp_path)

        with open(tmp_path / "cp-001.json") as f:
            data = json.load(f)

        assert data["checkpoint_id"] == "cp-001"
        assert data["cycle_id"] == "cycle-1"
        assert data["last_processed_idx"] == 100
        assert data["total_items"] == 1000


class TestCheckpointStoreLoad:
    """Test CheckpointStore.load operations. @trace WL-284"""

    @pytest.mark.requirement("WL-284")
    def test_load_existing_checkpoint(self, tmp_path: Path) -> None:
        """load retrieves a saved checkpoint."""
        original = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        )

        CheckpointStore.save(original, tmp_path)
        loaded = CheckpointStore.load("cp-001", tmp_path)

        assert loaded.checkpoint_id == "cp-001"
        assert loaded.cycle_id == "cycle-1"
        assert loaded.last_processed_idx == 100
        assert loaded.total_items == 1000

    @pytest.mark.requirement("WL-284")
    def test_load_preserves_datetime(self, tmp_path: Path) -> None:
        """load preserves datetime precision."""
        original_dt = datetime(2024, 1, 1, 12, 30, 45, 123456, tzinfo=UTC)
        original = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=original_dt,
        )

        CheckpointStore.save(original, tmp_path)
        loaded = CheckpointStore.load("cp-001", tmp_path)

        assert loaded.created_at == original_dt

    @pytest.mark.requirement("WL-284")
    def test_load_nonexistent_raises_error(self, tmp_path: Path) -> None:
        """load raises FileNotFoundError for missing checkpoint."""
        with pytest.raises(FileNotFoundError):
            CheckpointStore.load("nonexistent", tmp_path)

    @pytest.mark.requirement("WL-284")
    def test_load_multiple_checkpoints(self, tmp_path: Path) -> None:
        """load can retrieve specific checkpoint from multiple saved."""
        cp1 = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=datetime.now(UTC),
        )
        cp2 = Checkpoint(
            checkpoint_id="cp-002",
            cycle_id="cycle-1",
            last_processed_idx=200,
            total_items=1000,
            created_at=datetime.now(UTC),
        )

        CheckpointStore.save(cp1, tmp_path)
        CheckpointStore.save(cp2, tmp_path)

        loaded = CheckpointStore.load("cp-002", tmp_path)

        assert loaded.checkpoint_id == "cp-002"
        assert loaded.last_processed_idx == 200


class TestCheckpointStoreLatest:
    """Test CheckpointStore.latest operations. @trace WL-284"""

    @pytest.mark.requirement("WL-284")
    def test_latest_returns_most_recent(self, tmp_path: Path) -> None:
        """latest returns most recent checkpoint by created_at."""
        cp1 = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
        )
        cp2 = Checkpoint(
            checkpoint_id="cp-002",
            cycle_id="cycle-1",
            last_processed_idx=200,
            total_items=1000,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        )

        CheckpointStore.save(cp1, tmp_path)
        CheckpointStore.save(cp2, tmp_path)

        latest = CheckpointStore.latest("cycle-1", tmp_path)

        assert latest is not None
        assert latest.checkpoint_id == "cp-002"

    @pytest.mark.requirement("WL-284")
    def test_latest_filters_by_cycle(self, tmp_path: Path) -> None:
        """latest only considers checkpoints for specified cycle."""
        cp1 = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=datetime.now(UTC),
        )
        cp2 = Checkpoint(
            checkpoint_id="cp-002",
            cycle_id="cycle-2",
            last_processed_idx=200,
            total_items=1000,
            created_at=datetime.now(UTC),
        )

        CheckpointStore.save(cp1, tmp_path)
        CheckpointStore.save(cp2, tmp_path)

        latest = CheckpointStore.latest("cycle-1", tmp_path)

        assert latest is not None
        assert latest.cycle_id == "cycle-1"

    @pytest.mark.requirement("WL-284")
    def test_latest_none_for_empty(self, tmp_path: Path) -> None:
        """latest returns None when no checkpoints exist for cycle."""
        result = CheckpointStore.latest("nonexistent", tmp_path)
        assert result is None

    @pytest.mark.requirement("WL-284")
    def test_latest_none_for_missing_directory(self, tmp_path: Path) -> None:
        """latest returns None when store directory doesn't exist."""
        nonexistent = tmp_path / "nonexistent"
        result = CheckpointStore.latest("cycle-1", nonexistent)
        assert result is None

    @pytest.mark.requirement("WL-284")
    def test_latest_single_checkpoint(self, tmp_path: Path) -> None:
        """latest returns the only checkpoint for cycle."""
        cp = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=datetime.now(UTC),
        )

        CheckpointStore.save(cp, tmp_path)
        latest = CheckpointStore.latest("cycle-1", tmp_path)

        assert latest is not None
        assert latest.checkpoint_id == "cp-001"


class TestCheckpointStoreDelete:
    """Test CheckpointStore.delete operations. @trace WL-284"""

    @pytest.mark.requirement("WL-284")
    def test_delete_removes_checkpoint(self, tmp_path: Path) -> None:
        """delete removes checkpoint file from store."""
        checkpoint = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=datetime.now(UTC),
        )

        CheckpointStore.save(checkpoint, tmp_path)
        CheckpointStore.delete("cp-001", tmp_path)

        assert not (tmp_path / "cp-001.json").exists()

    @pytest.mark.requirement("WL-284")
    def test_delete_nonexistent_safe(self, tmp_path: Path) -> None:
        """delete does not raise error for nonexistent checkpoint."""
        # Should not raise
        CheckpointStore.delete("nonexistent", tmp_path)

    @pytest.mark.requirement("WL-284")
    def test_delete_only_specified(self, tmp_path: Path) -> None:
        """delete only removes specified checkpoint."""
        cp1 = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=datetime.now(UTC),
        )
        cp2 = Checkpoint(
            checkpoint_id="cp-002",
            cycle_id="cycle-1",
            last_processed_idx=200,
            total_items=1000,
            created_at=datetime.now(UTC),
        )

        CheckpointStore.save(cp1, tmp_path)
        CheckpointStore.save(cp2, tmp_path)
        CheckpointStore.delete("cp-001", tmp_path)

        assert not (tmp_path / "cp-001.json").exists()
        assert (tmp_path / "cp-002.json").exists()


class TestCheckpointStoreListCheckpoints:
    """Test CheckpointStore.list_checkpoints operations. @trace WL-284"""

    @pytest.mark.requirement("WL-284")
    def test_list_checkpoints_empty(self, tmp_path: Path) -> None:
        """list_checkpoints returns empty list for empty store."""
        result = CheckpointStore.list_checkpoints("cycle-1", tmp_path)
        assert result == []

    @pytest.mark.requirement("WL-284")
    def test_list_checkpoints_single(self, tmp_path: Path) -> None:
        """list_checkpoints returns single checkpoint ID."""
        checkpoint = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=datetime.now(UTC),
        )

        CheckpointStore.save(checkpoint, tmp_path)
        result = CheckpointStore.list_checkpoints("cycle-1", tmp_path)

        assert result == ["cp-001"]

    @pytest.mark.requirement("WL-284")
    def test_list_checkpoints_multiple_sorted(self, tmp_path: Path) -> None:
        """list_checkpoints returns all checkpoints for cycle, sorted."""
        cp1 = Checkpoint(
            checkpoint_id="cp-003",
            cycle_id="cycle-1",
            last_processed_idx=300,
            total_items=1000,
            created_at=datetime.now(UTC),
        )
        cp2 = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=datetime.now(UTC),
        )
        cp3 = Checkpoint(
            checkpoint_id="cp-002",
            cycle_id="cycle-1",
            last_processed_idx=200,
            total_items=1000,
            created_at=datetime.now(UTC),
        )

        CheckpointStore.save(cp1, tmp_path)
        CheckpointStore.save(cp2, tmp_path)
        CheckpointStore.save(cp3, tmp_path)

        result = CheckpointStore.list_checkpoints("cycle-1", tmp_path)

        assert result == ["cp-001", "cp-002", "cp-003"]

    @pytest.mark.requirement("WL-284")
    def test_list_checkpoints_filters_by_cycle(self, tmp_path: Path) -> None:
        """list_checkpoints only returns checkpoints for specified cycle."""
        cp1 = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=datetime.now(UTC),
        )
        cp2 = Checkpoint(
            checkpoint_id="cp-002",
            cycle_id="cycle-2",
            last_processed_idx=200,
            total_items=1000,
            created_at=datetime.now(UTC),
        )

        CheckpointStore.save(cp1, tmp_path)
        CheckpointStore.save(cp2, tmp_path)

        result = CheckpointStore.list_checkpoints("cycle-1", tmp_path)

        assert result == ["cp-001"]

    @pytest.mark.requirement("WL-284")
    def test_list_checkpoints_missing_directory(self, tmp_path: Path) -> None:
        """list_checkpoints returns empty list for missing directory."""
        nonexistent = tmp_path / "nonexistent"
        result = CheckpointStore.list_checkpoints("cycle-1", nonexistent)
        assert result == []

    @pytest.mark.requirement("WL-284")
    def test_list_checkpoints_ignores_invalid_json(self, tmp_path: Path) -> None:
        """list_checkpoints skips invalid JSON files."""
        # Create an invalid JSON file
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json")

        # Create a valid checkpoint
        checkpoint = Checkpoint(
            checkpoint_id="cp-001",
            cycle_id="cycle-1",
            last_processed_idx=100,
            total_items=1000,
            created_at=datetime.now(UTC),
        )
        CheckpointStore.save(checkpoint, tmp_path)

        result = CheckpointStore.list_checkpoints("cycle-1", tmp_path)

        # Should only include the valid checkpoint
        assert result == ["cp-001"]
