"""Tests for WL-302 Compliance Evidence Snapshot Scheduler.

# @trace WL-302
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import orjson as json
import pytest

from thegent.integrations.compliance_snapshot import ComplianceSnapshotScheduler


class TestComplianceSnapshotSchedulerInit:
    """Tests for scheduler initialization."""

    def test_init_with_valid_config(self, tmp_path: Path) -> None:
        """Initialize scheduler with valid config."""
        scheduler = ComplianceSnapshotScheduler(tmp_path, schedule_interval_hours=24)
        assert scheduler.snapshot_dir == tmp_path
        assert scheduler.schedule_interval_hours == 24

    def test_init_creates_directory(self, tmp_path: Path) -> None:
        """Scheduler creates snapshot directory."""
        snap_dir = tmp_path / "snapshots"
        assert not snap_dir.exists()
        _scheduler = ComplianceSnapshotScheduler(snap_dir)
        assert snap_dir.exists()

    def test_init_with_string_path(self, tmp_path: Path) -> None:
        """Scheduler accepts string path."""
        snap_dir = str(tmp_path / "snapshots")
        scheduler = ComplianceSnapshotScheduler(snap_dir)
        assert isinstance(scheduler.snapshot_dir, Path)

    def test_init_with_zero_interval_raises(self, tmp_path: Path) -> None:
        """Zero interval raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            ComplianceSnapshotScheduler(tmp_path, schedule_interval_hours=0)

    def test_init_with_negative_interval_raises(self, tmp_path: Path) -> None:
        """Negative interval raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            ComplianceSnapshotScheduler(tmp_path, schedule_interval_hours=-1)

    @pytest.mark.requirement("WL-302")
    def test_init_default_interval(self, tmp_path: Path) -> None:
        """Default interval is 24 hours."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        assert scheduler.schedule_interval_hours == 24


class TestTakeSnapshot:
    """Tests for take_snapshot method."""

    def test_take_snapshot_writes_file(self, tmp_path: Path) -> None:
        """take_snapshot writes JSON file to disk."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        artifacts = [{"id": "a1", "type": "policy"}, {"id": "a2", "type": "audit"}]

        result_path = scheduler.take_snapshot(artifacts)

        assert result_path.exists()
        assert result_path.parent == tmp_path
        assert result_path.name.startswith("snapshot_")
        assert result_path.name.endswith(".json")

    def test_take_snapshot_content_structure(self, tmp_path: Path) -> None:
        """Snapshot file has correct structure."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        artifacts = [{"id": "a1"}]

        result_path = scheduler.take_snapshot(artifacts)

        with result_path.open() as f:
            data = json.load(f)

        assert "timestamp" in data
        assert "artifacts" in data
        assert "artifact_count" in data
        assert data["artifact_count"] == 1

    def test_take_snapshot_preserves_artifacts(self, tmp_path: Path) -> None:
        """Snapshot preserves artifact data."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        artifacts = [{"id": "a1", "name": "test"}, {"id": "a2", "status": "active"}]

        result_path = scheduler.take_snapshot(artifacts)

        with result_path.open() as f:
            data = json.load(f)

        assert data["artifacts"] == artifacts

    def test_take_snapshot_empty_list(self, tmp_path: Path) -> None:
        """Snapshot can handle empty artifact list."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        result_path = scheduler.take_snapshot([])

        with result_path.open() as f:
            data = json.load(f)

        assert data["artifact_count"] == 0
        assert data["artifacts"] == []

    def test_take_snapshot_invalid_artifacts_type(self, tmp_path: Path) -> None:
        """Non-list artifacts raises ValueError."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        with pytest.raises(ValueError, match="list"):
            scheduler.take_snapshot({"invalid": "dict"})

    def test_take_snapshot_non_dict_artifact(self, tmp_path: Path) -> None:
        """Non-dict artifact item raises ValueError."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        with pytest.raises(ValueError, match="dicts"):
            scheduler.take_snapshot([{"valid": "dict"}, "invalid_string"])

    def test_take_snapshot_unique_filenames(self, tmp_path: Path) -> None:
        """Multiple snapshots get unique filenames."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        path1 = scheduler.take_snapshot([{"id": "1"}])
        path2 = scheduler.take_snapshot([{"id": "2"}])

        assert path1.name != path2.name
        assert path1.exists() and path2.exists()

    @pytest.mark.requirement("WL-302")
    def test_take_snapshot_timestamp_format(self, tmp_path: Path) -> None:
        """Snapshot timestamp is valid ISO format."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        result_path = scheduler.take_snapshot([])

        with result_path.open() as f:
            data = json.load(f)

        ts_str = data["timestamp"]
        # Should parse as valid datetime
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        assert dt.tzinfo is not None


class TestShouldRun:
    """Tests for should_run method."""

    def test_should_run_first_time(self, tmp_path: Path) -> None:
        """First run (last_run=None) returns True."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        assert scheduler.should_run(None) is True

    def test_should_run_within_interval(self, tmp_path: Path) -> None:
        """Within interval returns False."""
        scheduler = ComplianceSnapshotScheduler(tmp_path, schedule_interval_hours=24)
        last_run = datetime.now(UTC) - timedelta(hours=12)
        assert scheduler.should_run(last_run) is False

    def test_should_run_at_interval_boundary(self, tmp_path: Path) -> None:
        """Exactly at interval boundary returns True."""
        scheduler = ComplianceSnapshotScheduler(tmp_path, schedule_interval_hours=24)
        last_run = datetime.now(UTC) - timedelta(hours=24)
        assert scheduler.should_run(last_run) is True

    def test_should_run_past_interval(self, tmp_path: Path) -> None:
        """Past interval returns True."""
        scheduler = ComplianceSnapshotScheduler(tmp_path, schedule_interval_hours=24)
        last_run = datetime.now(UTC) - timedelta(hours=48)
        assert scheduler.should_run(last_run) is True

    def test_should_run_short_interval(self, tmp_path: Path) -> None:
        """Works with short intervals."""
        scheduler = ComplianceSnapshotScheduler(tmp_path, schedule_interval_hours=1)
        last_run = datetime.now(UTC) - timedelta(minutes=61)
        assert scheduler.should_run(last_run) is True

    @pytest.mark.requirement("WL-302")
    def test_should_run_uses_utc(self, tmp_path: Path) -> None:
        """should_run uses UTC timezone."""
        scheduler = ComplianceSnapshotScheduler(tmp_path, schedule_interval_hours=24)
        now_utc = datetime.now(UTC)
        last_run_utc = now_utc - timedelta(hours=25)
        assert scheduler.should_run(last_run_utc) is True


class TestListSnapshots:
    """Tests for list_snapshots method."""

    def test_list_snapshots_empty(self, tmp_path: Path) -> None:
        """Empty directory returns empty list."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        assert scheduler.list_snapshots() == []

    def test_list_snapshots_nonexistent_dir(self, tmp_path: Path) -> None:
        """Non-existent directory returns empty list."""
        snap_dir = tmp_path / "nonexistent"
        scheduler = ComplianceSnapshotScheduler(snap_dir)
        scheduler.snapshot_dir.rmdir()  # Remove created dir
        assert scheduler.list_snapshots() == []

    def test_list_snapshots_single(self, tmp_path: Path) -> None:
        """Single snapshot is listed."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        path = scheduler.take_snapshot([{"id": "1"}])
        snapshots = scheduler.list_snapshots()

        assert len(snapshots) == 1
        assert path in snapshots

    def test_list_snapshots_multiple(self, tmp_path: Path) -> None:
        """Multiple snapshots are listed in order."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        _path1 = scheduler.take_snapshot([{"id": "1"}])
        _path2 = scheduler.take_snapshot([{"id": "2"}])
        _path3 = scheduler.take_snapshot([{"id": "3"}])

        snapshots = scheduler.list_snapshots()
        assert len(snapshots) == 3

    def test_list_snapshots_sorted_order(self, tmp_path: Path) -> None:
        """Snapshots are returned in sorted order (oldest first)."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        paths = []
        for i in range(3):
            paths.append(scheduler.take_snapshot([{"id": str(i)}]))

        snapshots = scheduler.list_snapshots()
        assert snapshots == sorted(paths)

    def test_list_snapshots_ignores_other_files(self, tmp_path: Path) -> None:
        """Non-snapshot files are ignored."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        scheduler.take_snapshot([{"id": "1"}])
        (tmp_path / "other_file.txt").write_text("ignore")
        (tmp_path / "snapshot_broken.json").write_text("ignore")

        snapshots = scheduler.list_snapshots()
        assert len(snapshots) == 1

    @pytest.mark.requirement("WL-302")
    def test_list_snapshots_returns_paths(self, tmp_path: Path) -> None:
        """list_snapshots returns Path objects."""
        scheduler = ComplianceSnapshotScheduler(tmp_path)
        scheduler.take_snapshot([])
        snapshots = scheduler.list_snapshots()

        assert len(snapshots) > 0
        assert all(isinstance(p, Path) for p in snapshots)


# noqa: PT018
