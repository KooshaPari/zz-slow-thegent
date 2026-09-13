"""Tests for WL-317: Drift Replay Tool.

@trace WL-317
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from thegent.integrations.drift_replay import DriftManifest, DriftReplayEngine


@pytest.mark.requirement("WL-317")
def test_drift_manifest_dataclass() -> None:
    """Test DriftManifest dataclass creation."""
    drifts = [{"field": "status", "from": "TODO", "to": "DONE"}]
    timestamp = datetime.now(UTC)

    manifest = DriftManifest(
        manifest_id="MAN-001",
        cycle_id="CYCLE-001",
        drifts=drifts,
        captured_at=timestamp,
    )
    assert manifest.manifest_id == "MAN-001"
    assert manifest.cycle_id == "CYCLE-001"
    assert manifest.drifts == drifts
    assert manifest.captured_at == timestamp


@pytest.mark.requirement("WL-317")
def test_drift_manifest_to_dict() -> None:
    """Test DriftManifest to_dict serialization."""
    drifts = [{"field": "status", "from": "TODO", "to": "DONE"}]
    timestamp = datetime(2025, 1, 15, 10, 30, 45, tzinfo=UTC)

    manifest = DriftManifest(
        manifest_id="MAN-001",
        cycle_id="CYCLE-001",
        drifts=drifts,
        captured_at=timestamp,
    )
    result = manifest.to_dict()
    assert result["manifest_id"] == "MAN-001"
    assert result["cycle_id"] == "CYCLE-001"
    assert result["drifts"] == drifts
    assert result["captured_at"] == "2025-01-15T10:30:45+00:00"


@pytest.mark.requirement("WL-317")
def test_drift_manifest_from_dict() -> None:
    """Test DriftManifest from_dict deserialization."""
    data = {
        "manifest_id": "MAN-001",
        "cycle_id": "CYCLE-001",
        "drifts": [{"field": "status", "from": "TODO", "to": "DONE"}],
        "captured_at": "2025-01-15T10:30:45+00:00",
    }

    manifest = DriftManifest.from_dict(data)
    assert manifest.manifest_id == "MAN-001"
    assert manifest.cycle_id == "CYCLE-001"
    assert len(manifest.drifts) == 1
    assert manifest.captured_at.year == 2025


@pytest.mark.requirement("WL-317")
def test_archive_manifest_success() -> None:
    """Test archiving a manifest to disk."""
    with TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir)

        manifest = DriftManifest(
            manifest_id="MAN-001",
            cycle_id="CYCLE-001",
            drifts=[{"field": "status", "from": "TODO", "to": "DONE"}],
            captured_at=datetime.now(UTC),
        )

        result_path = DriftReplayEngine.archive_manifest(manifest, archive_dir)
        assert result_path == archive_dir / "MAN-001.json"
        assert result_path.exists()


@pytest.mark.requirement("WL-317")
def test_archive_manifest_invalid_dir() -> None:
    """Test archive_manifest fails if dir doesn't exist."""
    nonexistent_dir = Path("/nonexistent")
    manifest = DriftManifest(
        manifest_id="MAN-001",
        cycle_id="CYCLE-001",
        drifts=[],
        captured_at=datetime.now(UTC),
    )

    with pytest.raises(ValueError, match="Archive directory does not exist"):
        DriftReplayEngine.archive_manifest(manifest, nonexistent_dir)


@pytest.mark.requirement("WL-317")
def test_load_manifest_success() -> None:
    """Test loading a manifest from archive."""
    with TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir)

        original_manifest = DriftManifest(
            manifest_id="MAN-001",
            cycle_id="CYCLE-001",
            drifts=[{"field": "status", "from": "TODO", "to": "DONE"}],
            captured_at=datetime.now(UTC),
        )
        DriftReplayEngine.archive_manifest(original_manifest, archive_dir)

        loaded_manifest = DriftReplayEngine.load_manifest("MAN-001", archive_dir)
        assert loaded_manifest.manifest_id == "MAN-001"
        assert loaded_manifest.cycle_id == "CYCLE-001"
        assert len(loaded_manifest.drifts) == 1


@pytest.mark.requirement("WL-317")
def test_load_manifest_not_found() -> None:
    """Test load_manifest fails if manifest doesn't exist."""
    with TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir)

        with pytest.raises(FileNotFoundError, match="Manifest not found"):
            DriftReplayEngine.load_manifest("NONEXISTENT", archive_dir)


@pytest.mark.requirement("WL-317")
def test_list_manifests_empty() -> None:
    """Test list_manifests on empty archive."""
    with TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir)
        result = DriftReplayEngine.list_manifests(archive_dir)
        assert result == []


@pytest.mark.requirement("WL-317")
def test_list_manifests_nonexistent_dir() -> None:
    """Test list_manifests with nonexistent directory."""
    nonexistent_dir = Path("/nonexistent")
    result = DriftReplayEngine.list_manifests(nonexistent_dir)
    assert result == []


@pytest.mark.requirement("WL-317")
def test_list_manifests_multiple() -> None:
    """Test list_manifests returns sorted list."""
    with TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir)

        for i in [3, 1, 2]:
            manifest = DriftManifest(
                manifest_id=f"MAN-{i:03d}",
                cycle_id=f"CYCLE-{i}",
                drifts=[],
                captured_at=datetime.now(UTC),
            )
            DriftReplayEngine.archive_manifest(manifest, archive_dir)

        result = DriftReplayEngine.list_manifests(archive_dir)
        assert result == ["MAN-001", "MAN-002", "MAN-003"]


@pytest.mark.requirement("WL-317")
def test_replay_returns_drifts() -> None:
    """Test replay returns drifts from manifest."""
    drifts = [
        {"field": "status", "from": "TODO", "to": "IN_PROGRESS"},
        {"field": "priority", "from": "P2", "to": "P1"},
    ]
    manifest = DriftManifest(
        manifest_id="MAN-001",
        cycle_id="CYCLE-001",
        drifts=drifts,
        captured_at=datetime.now(UTC),
    )

    result = DriftReplayEngine.replay(manifest)
    assert result == drifts
    assert len(result) == 2


@pytest.mark.requirement("WL-317")
def test_replay_deterministic() -> None:
    """Test replay is deterministic."""
    drifts = [
        {"field": "status", "from": "TODO", "to": "DONE"},
        {"field": "owner", "from": "alice", "to": "bob"},
    ]
    manifest = DriftManifest(
        manifest_id="MAN-001",
        cycle_id="CYCLE-001",
        drifts=drifts,
        captured_at=datetime.now(UTC),
    )

    result1 = DriftReplayEngine.replay(manifest)
    result2 = DriftReplayEngine.replay(manifest)
    assert result1 == result2


@pytest.mark.requirement("WL-317")
def test_roundtrip_manifest() -> None:
    """Test archive and load roundtrip."""
    with TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir)

        original = DriftManifest(
            manifest_id="MAN-001",
            cycle_id="CYCLE-001",
            drifts=[
                {"field": "status", "from": "TODO", "to": "DONE"},
                {"field": "priority", "from": "P2", "to": "P1"},
            ],
            captured_at=datetime(2025, 1, 15, 10, 30, 45, tzinfo=UTC),
        )

        DriftReplayEngine.archive_manifest(original, archive_dir)
        loaded = DriftReplayEngine.load_manifest("MAN-001", archive_dir)

        assert loaded.manifest_id == original.manifest_id
        assert loaded.cycle_id == original.cycle_id
        assert loaded.drifts == original.drifts
        assert loaded.captured_at == original.captured_at
