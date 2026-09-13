"""Tests for WL-185: Reflection Rollback Command.

# @trace WL-185
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from thegent.integrations.reflection_rollback import (
    ReflectionRollbackStore,
    RollbackEntry,
)


class TestRollbackEntry:
    """Tests for RollbackEntry dataclass."""

    @pytest.mark.requirement("WL-185")
    def test_rollback_entry_creation(self):
        """# @trace WL-185 — RollbackEntry can be created with required fields."""
        now = datetime.now(UTC)
        snapshot = {"key": "value"}
        entry = RollbackEntry(entry_id="entry_1", timestamp=now, snapshot=snapshot)
        assert entry.entry_id == "entry_1"
        assert entry.timestamp == now
        assert entry.snapshot == {"key": "value"}

    @pytest.mark.requirement("WL-185")
    def test_rollback_entry_snapshot_copy(self):
        """# @trace WL-185 — RollbackEntry stores snapshot as-is."""
        snapshot = {"data": {"nested": "value"}}
        entry = RollbackEntry(entry_id="test", timestamp=datetime.now(UTC), snapshot=snapshot)
        assert entry.snapshot == {"data": {"nested": "value"}}


class TestReflectionRollbackStore:
    """Tests for ReflectionRollbackStore class."""

    @pytest.mark.requirement("WL-185")
    def test_store_initialization(self):
        """# @trace WL-185 — ReflectionRollbackStore initializes empty."""
        store = ReflectionRollbackStore()
        assert store.list_entries() == []

    @pytest.mark.requirement("WL-185")
    def test_record_single_entry(self):
        """# @trace WL-185 — record creates a new entry."""
        store = ReflectionRollbackStore()
        before = datetime.now(UTC)
        snapshot = {"state": "initial"}
        entry = store.record("entry_1", snapshot)
        after = datetime.now(UTC)

        assert entry.entry_id == "entry_1"
        assert before <= entry.timestamp <= after
        assert entry.snapshot == {"state": "initial"}

    @pytest.mark.requirement("WL-185")
    def test_record_multiple_entries(self):
        """# @trace WL-185 — record can store multiple entries."""
        store = ReflectionRollbackStore()
        store.record("entry_1", {"state": "first"})
        store.record("entry_2", {"state": "second"})
        store.record("entry_3", {"state": "third"})

        entries = store.list_entries()
        assert len(entries) == 3

    @pytest.mark.requirement("WL-185")
    def test_rollback_to_existing_entry(self):
        """# @trace WL-185 — rollback_to returns snapshot of recorded entry."""
        store = ReflectionRollbackStore()
        original = {"key": "value", "count": 42}
        store.record("entry_1", original)

        snapshot = store.rollback_to("entry_1")
        assert snapshot == {"key": "value", "count": 42}

    @pytest.mark.requirement("WL-185")
    def test_rollback_to_nonexistent_entry(self):
        """# @trace WL-185 — rollback_to raises KeyError for nonexistent entry."""
        store = ReflectionRollbackStore()
        with pytest.raises(KeyError):
            store.rollback_to("nonexistent")

    @pytest.mark.requirement("WL-185")
    def test_rollback_snapshot_isolation(self):
        """# @trace WL-185 — rollback_to returns copy, not reference."""
        store = ReflectionRollbackStore()
        original = {"data": "original"}
        store.record("entry_1", original)

        snapshot = store.rollback_to("entry_1")
        snapshot["data"] = "modified"

        # Get again to verify original is unchanged
        snapshot2 = store.rollback_to("entry_1")
        assert snapshot2["data"] == "original"

    @pytest.mark.requirement("WL-185")
    def test_list_entries_empty(self):
        """# @trace WL-185 — list_entries returns empty list initially."""
        store = ReflectionRollbackStore()
        entries = store.list_entries()
        assert isinstance(entries, list)
        assert len(entries) == 0

    @pytest.mark.requirement("WL-185")
    def test_list_entries_all_recorded(self):
        """# @trace WL-185 — list_entries returns all recorded entries."""
        store = ReflectionRollbackStore()
        store.record("entry_a", {"value": 1})
        store.record("entry_b", {"value": 2})
        store.record("entry_c", {"value": 3})

        entries = store.list_entries()
        assert len(entries) == 3
        assert entries[0].entry_id == "entry_a"
        assert entries[1].entry_id == "entry_b"
        assert entries[2].entry_id == "entry_c"

    @pytest.mark.requirement("WL-185")
    def test_list_entries_order_preserved(self):
        """# @trace WL-185 — list_entries preserves insertion order."""
        store = ReflectionRollbackStore()
        ids = ["first", "second", "third", "fourth"]
        for id_ in ids:
            store.record(id_, {"id": id_})

        entries = store.list_entries()
        for i, id_ in enumerate(ids):
            assert entries[i].entry_id == id_

    @pytest.mark.requirement("WL-185")
    def test_record_overwrites_same_id(self):
        """# @trace WL-185 — recording with same id overwrites previous entry."""
        store = ReflectionRollbackStore()
        store.record("entry_1", {"version": 1})
        store.record("entry_1", {"version": 2})

        entries = store.list_entries()
        assert len(entries) == 1
        assert entries[0].snapshot["version"] == 2

    @pytest.mark.requirement("WL-185")
    def test_complex_snapshot_data(self):
        """# @trace WL-185 — record handles complex nested snapshot data."""
        store = ReflectionRollbackStore()
        snapshot = {
            "user": {"name": "Alice", "age": 30},
            "config": {"enabled": True, "level": 5},
            "tags": ["important", "verified"],
        }
        store.record("complex", snapshot)

        retrieved = store.rollback_to("complex")
        assert retrieved["user"]["name"] == "Alice"
        assert retrieved["config"]["level"] == 5
        assert len(retrieved["tags"]) == 2
