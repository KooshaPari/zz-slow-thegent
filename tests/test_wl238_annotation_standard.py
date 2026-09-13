"""Tests for WL-238: Remote→Local Annotation Standard.

Verifies annotation creation, retrieval, merging, and error handling for the
annotation standard interface.

# @trace WL-238
"""

from __future__ import annotations

import pytest

from thegent.integrations.annotation_standard import (
    AnnotationEntry,
    RemoteToLocalAnnotationStandard,
)


@pytest.mark.requirement("WL-238")
class TestAnnotationEntry:
    """WL-238: AnnotationEntry dataclass creation and properties."""

    def test_annotation_entry_creation_with_all_fields(self):
        """# @trace WL-238 — AnnotationEntry stores item_id, source, and annotations."""
        entry = AnnotationEntry(
            item_id="item-123",
            source="remote-system",
            annotations={"tag": "important", "status": "reviewed"},
        )

        assert entry.item_id == "item-123"
        assert entry.source == "remote-system"
        assert entry.annotations == {"tag": "important", "status": "reviewed"}

    def test_annotation_entry_default_empty_annotations(self):
        """# @trace WL-238 — AnnotationEntry with no annotations defaults to empty dict."""
        entry = AnnotationEntry(item_id="item-456", source="another-source")

        assert entry.item_id == "item-456"
        assert entry.source == "another-source"
        assert entry.annotations == {}


@pytest.mark.requirement("WL-238")
class TestRemoteToLocalAnnotationStandard:
    """WL-238: RemoteToLocalAnnotationStandard manages annotations."""

    def test_annotate_creates_new_entry(self):
        """# @trace WL-238 — annotate() creates a new AnnotationEntry."""
        store = RemoteToLocalAnnotationStandard()
        entry = store.annotate(
            "item-1", "source-a", {"label": "priority-high", "owner": "alice"}
        )

        assert entry.item_id == "item-1"
        assert entry.source == "source-a"
        assert entry.annotations == {"label": "priority-high", "owner": "alice"}

    def test_annotate_overwrites_existing_entry(self):
        """# @trace WL-238 — annotate() replaces existing annotations for same item."""
        store = RemoteToLocalAnnotationStandard()
        store.annotate("item-2", "source-a", {"v": "1"})
        entry = store.annotate("item-2", "source-b", {"v": "2", "new": "value"})

        assert entry.source == "source-b"
        assert entry.annotations == {"v": "2", "new": "value"}

    def test_get_retrieves_existing_entry(self):
        """# @trace WL-238 — get() returns the AnnotationEntry for a valid item_id."""
        store = RemoteToLocalAnnotationStandard()
        store.annotate("item-3", "source-x", {"key": "value"})
        entry = store.get("item-3")

        assert entry.item_id == "item-3"
        assert entry.source == "source-x"

    def test_get_raises_keyerror_for_missing_item(self):
        """# @trace WL-238 — get() raises KeyError for non-existent item_id."""
        store = RemoteToLocalAnnotationStandard()

        with pytest.raises(KeyError, match="No annotations found for item_id"):
            store.get("nonexistent")

    def test_get_annotation_returns_value_for_existing_key(self):
        """# @trace WL-238 — get_annotation() returns value for existing key."""
        store = RemoteToLocalAnnotationStandard()
        store.annotate("item-4", "source-y", {"title": "Test Item", "status": "active"})
        value = store.get_annotation("item-4", "title")

        assert value == "Test Item"

    def test_get_annotation_returns_none_for_missing_key(self):
        """# @trace WL-238 — get_annotation() returns None if key does not exist."""
        store = RemoteToLocalAnnotationStandard()
        store.annotate("item-5", "source-z", {"title": "Item"})
        value = store.get_annotation("item-5", "nonexistent_key")

        assert value is None

    def test_get_annotation_returns_none_for_missing_item(self):
        """# @trace WL-238 — get_annotation() returns None if item_id does not exist."""
        store = RemoteToLocalAnnotationStandard()
        value = store.get_annotation("missing-item", "any_key")

        assert value is None

    def test_merge_adds_new_keys_to_existing_entry(self):
        """# @trace WL-238 — merge() adds new annotation keys to existing entry."""
        store = RemoteToLocalAnnotationStandard()
        store.annotate("item-6", "source-a", {"existing": "value"})
        entry = store.merge("item-6", {"new_key": "new_value"})

        assert entry.annotations == {"existing": "value", "new_key": "new_value"}

    def test_merge_overwrites_existing_keys(self):
        """# @trace WL-238 — merge() overwrites existing keys with new values."""
        store = RemoteToLocalAnnotationStandard()
        store.annotate("item-7", "source-b", {"key1": "old", "key2": "unchanged"})
        entry = store.merge("item-7", {"key1": "new", "key3": "added"})

        assert entry.annotations == {
            "key1": "new",
            "key2": "unchanged",
            "key3": "added",
        }

    def test_merge_raises_keyerror_for_missing_item(self):
        """# @trace WL-238 — merge() raises KeyError if item_id does not exist."""
        store = RemoteToLocalAnnotationStandard()

        with pytest.raises(KeyError, match="No annotations found for item_id"):
            store.merge("missing-item", {"key": "value"})

    def test_merge_returns_updated_entry(self):
        """# @trace WL-238 — merge() returns the updated AnnotationEntry."""
        store = RemoteToLocalAnnotationStandard()
        store.annotate("item-8", "source-c", {"a": "1"})
        entry = store.merge("item-8", {"b": "2"})

        assert entry.item_id == "item-8"
        assert entry.source == "source-c"
        assert entry.annotations == {"a": "1", "b": "2"}

    def test_annotate_creates_copy_of_annotations_dict(self):
        """# @trace WL-238 — annotate() stores a copy of the annotations dict."""
        store = RemoteToLocalAnnotationStandard()
        original_dict = {"key": "value"}
        store.annotate("item-9", "source-d", original_dict)

        # Modify the original dict
        original_dict["key"] = "modified"

        # The stored entry should not be affected
        entry = store.get("item-9")
        assert entry.annotations["key"] == "value"

    def test_multiple_items_with_different_annotations(self):
        """# @trace WL-238 — store manages multiple items with different annotations."""
        store = RemoteToLocalAnnotationStandard()
        store.annotate("item-10", "source-e", {"type": "A"})
        store.annotate("item-11", "source-f", {"type": "B"})

        entry_10 = store.get("item-10")
        entry_11 = store.get("item-11")

        assert entry_10.annotations["type"] == "A"
        assert entry_11.annotations["type"] == "B"

    def test_merge_modifies_stored_entry_in_place(self):
        """# @trace WL-238 — merge() modifies the stored entry and reflects on next get()."""
        store = RemoteToLocalAnnotationStandard()
        store.annotate("item-12", "source-g", {"v": "1"})
        store.merge("item-12", {"v": "2"})

        entry = store.get("item-12")
        assert entry.annotations["v"] == "2"
