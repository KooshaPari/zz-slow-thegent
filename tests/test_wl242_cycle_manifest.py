"""Tests for immutable cycle manifests.

# @trace WL-242
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from thegent.integrations.cycle_manifest import (
    CycleManifest,
    CycleManifestStore,
)


@pytest.mark.requirement("WL-242")
class TestCycleManifest:
    """Test CycleManifest dataclass."""

    def test_cycle_manifest_creation(self) -> None:
        """Test creating a CycleManifest."""
        now = datetime.now(UTC)
        manifest = CycleManifest(cycle_id="cycle-1", created_at=now, items=("a", "b"))
        assert manifest.cycle_id == "cycle-1"
        assert manifest.created_at == now
        assert manifest.items == ("a", "b")

    def test_cycle_manifest_frozen(self) -> None:
        """Test that CycleManifest is immutable."""
        now = datetime.now(UTC)
        manifest = CycleManifest(cycle_id="cycle-1", created_at=now, items=("a",))
        with pytest.raises(Exception):  # FrozenInstanceError
            manifest.cycle_id = "cycle-2"

    def test_cycle_manifest_items_tuple(self) -> None:
        """Test that items are stored as tuple."""
        now = datetime.now(UTC)
        manifest = CycleManifest(
            cycle_id="cycle-1", created_at=now, items=("x", "y", "z")
        )
        assert isinstance(manifest.items, tuple)
        assert manifest.items == ("x", "y", "z")


@pytest.mark.requirement("WL-242")
class TestCycleManifestStore:
    """Test CycleManifestStore."""

    def test_create_manifest(self) -> None:
        """Test creating a new cycle manifest."""
        store = CycleManifestStore()
        before = datetime.now(UTC)
        manifest = store.create("cycle-1", ["item1", "item2"])
        after = datetime.now(UTC)
        assert manifest.cycle_id == "cycle-1"
        assert manifest.items == ("item1", "item2")
        assert before <= manifest.created_at <= after

    def test_get_manifest(self) -> None:
        """Test retrieving a cycle manifest."""
        store = CycleManifestStore()
        created = store.create("cycle-1", ["a", "b"])
        retrieved = store.get("cycle-1")
        assert retrieved.cycle_id == "cycle-1"
        assert retrieved.items == ("a", "b")
        assert retrieved == created

    def test_get_manifest_not_found(self) -> None:
        """Test getting non-existent manifest raises KeyError."""
        store = CycleManifestStore()
        with pytest.raises(KeyError):
            store.get("nonexistent")

    def test_list_cycles_empty(self) -> None:
        """Test listing cycles in empty store."""
        store = CycleManifestStore()
        cycles = store.list_cycles()
        assert cycles == []

    def test_list_cycles(self) -> None:
        """Test listing all cycle IDs."""
        store = CycleManifestStore()
        store.create("cycle-1", ["a"])
        store.create("cycle-2", ["b"])
        store.create("cycle-3", ["c"])
        cycles = store.list_cycles()
        assert len(cycles) == 3
        assert "cycle-1" in cycles
        assert "cycle-2" in cycles
        assert "cycle-3" in cycles

    def test_create_multiple_manifests(self) -> None:
        """Test creating multiple manifests."""
        store = CycleManifestStore()
        m1 = store.create("cycle-1", ["a", "b"])
        m2 = store.create("cycle-2", ["c", "d"])
        cycles = store.list_cycles()
        assert len(cycles) == 2
        assert m1.cycle_id == "cycle-1"
        assert m2.cycle_id == "cycle-2"

    def test_items_converted_to_tuple(self) -> None:
        """Test that list items are converted to tuple."""
        store = CycleManifestStore()
        manifest = store.create("cycle-1", ["x", "y", "z"])
        assert isinstance(manifest.items, tuple)
        assert manifest.items == ("x", "y", "z")

    def test_empty_items_list(self) -> None:
        """Test creating manifest with empty items list."""
        store = CycleManifestStore()
        manifest = store.create("cycle-empty", [])
        assert manifest.items == ()

    def test_get_error_message(self) -> None:
        """Test that KeyError has informative message."""
        store = CycleManifestStore()
        with pytest.raises(KeyError, match="not found"):
            store.get("nonexistent")

    def test_manifest_immutability_preserved(self) -> None:
        """Test that stored manifests remain immutable."""
        store = CycleManifestStore()
        store.create("cycle-1", ["a", "b"])
        retrieved = store.get("cycle-1")
        with pytest.raises(Exception):  # FrozenInstanceError
            retrieved.cycle_id = "modified"
