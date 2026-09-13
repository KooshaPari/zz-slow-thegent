"""Tests for WL-225: WL Sort/Normalize Command.

Verifies sorting, normalization, and deduplication of workstream records.

# @trace WL-225
"""

from __future__ import annotations

import pytest


@pytest.mark.requirement("WL-225")
class TestWLSortNormalizer:
    """WL-225: Sorting, normalization, and deduplication for workstream records."""

    def test_sort_by_id_ascending(self):
        """# @trace WL-225 — sort() sorts items by id in ascending order."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        items = [
            {"id": "WL-003", "title": "C"},
            {"id": "WL-001", "title": "A"},
            {"id": "WL-002", "title": "B"},
        ]
        sorted_items = normalizer.sort(items)

        assert sorted_items[0]["id"] == "WL-001"
        assert sorted_items[1]["id"] == "WL-002"
        assert sorted_items[2]["id"] == "WL-003"

    def test_sort_preserves_original_list(self):
        """# @trace WL-225 — sort() does not modify the original list."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        original = [
            {"id": "WL-003"},
            {"id": "WL-001"},
        ]
        sorted_items = normalizer.sort(original)

        assert original[0]["id"] == "WL-003"
        assert original[1]["id"] == "WL-001"
        assert sorted_items[0]["id"] == "WL-001"

    def test_sort_by_custom_key(self):
        """# @trace WL-225 — sort() sorts by custom key parameter."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        items = [
            {"id": "WL-001", "title": "Zebra"},
            {"id": "WL-002", "title": "Apple"},
            {"id": "WL-003", "title": "Mango"},
        ]
        sorted_items = normalizer.sort(items, key="title")

        assert sorted_items[0]["title"] == "Apple"
        assert sorted_items[1]["title"] == "Mango"
        assert sorted_items[2]["title"] == "Zebra"

    def test_sort_empty_list(self):
        """# @trace WL-225 — sort() handles empty list."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        sorted_items = normalizer.sort([])

        assert sorted_items == []

    def test_sort_single_item(self):
        """# @trace WL-225 — sort() handles single item list."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        items = [{"id": "WL-001"}]
        sorted_items = normalizer.sort(items)

        assert len(sorted_items) == 1
        assert sorted_items[0]["id"] == "WL-001"

    def test_normalize_ids_uppercase_string(self):
        """# @trace WL-225 — normalize_ids() converts id strings to uppercase."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        items = [
            {"id": "wl-001", "title": "Test"},
            {"id": "WL-002", "title": "Test2"},
        ]
        normalized = normalizer.normalize_ids(items)

        assert normalized[0]["id"] == "WL-001"
        assert normalized[1]["id"] == "WL-002"

    def test_normalize_ids_non_string_conversion(self):
        """# @trace WL-225 — normalize_ids() converts non-string ids to uppercase string."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        items = [{"id": 123, "title": "Test"}]
        normalized = normalizer.normalize_ids(items)

        assert normalized[0]["id"] == "123"
        assert isinstance(normalized[0]["id"], str)

    def test_normalize_ids_preserves_original(self):
        """# @trace WL-225 — normalize_ids() does not modify original list."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        items = [{"id": "wl-001"}]
        normalized = normalizer.normalize_ids(items)

        assert items[0]["id"] == "wl-001"
        assert normalized[0]["id"] == "WL-001"

    def test_normalize_ids_missing_id_field(self):
        """# @trace WL-225 — normalize_ids() handles missing id field."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        items = [{"title": "Test"}]
        normalized = normalizer.normalize_ids(items)

        assert "id" not in normalized[0]
        assert normalized[0]["title"] == "Test"

    def test_normalize_ids_preserves_other_fields(self):
        """# @trace WL-225 — normalize_ids() preserves other fields."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        items = [{"id": "wl-001", "title": "Test", "priority": "HIGH", "owner": "alice"}]
        normalized = normalizer.normalize_ids(items)

        assert normalized[0]["id"] == "WL-001"
        assert normalized[0]["title"] == "Test"
        assert normalized[0]["priority"] == "HIGH"
        assert normalized[0]["owner"] == "alice"

    def test_deduplicate_by_id_default(self):
        """# @trace WL-225 — deduplicate() removes duplicates by id."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        items = [
            {"id": "WL-001", "title": "Test1"},
            {"id": "WL-002", "title": "Test2"},
            {"id": "WL-001", "title": "Test1-Duplicate"},
        ]
        deduplicated = normalizer.deduplicate(items)

        assert len(deduplicated) == 2
        assert deduplicated[0]["id"] == "WL-001"
        assert deduplicated[1]["id"] == "WL-002"

    def test_deduplicate_keeps_first_occurrence(self):
        """# @trace WL-225 — deduplicate() keeps first occurrence."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        items = [
            {"id": "WL-001", "value": "first"},
            {"id": "WL-001", "value": "second"},
        ]
        deduplicated = normalizer.deduplicate(items)

        assert len(deduplicated) == 1
        assert deduplicated[0]["value"] == "first"

    def test_deduplicate_by_custom_key(self):
        """# @trace WL-225 — deduplicate() deduplicates by custom key."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        items = [
            {"id": "WL-001", "email": "alice@example.com"},
            {"id": "WL-002", "email": "bob@example.com"},
            {"id": "WL-003", "email": "alice@example.com"},
        ]
        deduplicated = normalizer.deduplicate(items, key="email")

        assert len(deduplicated) == 2
        assert deduplicated[0]["email"] == "alice@example.com"
        assert deduplicated[1]["email"] == "bob@example.com"

    def test_deduplicate_preserves_original(self):
        """# @trace WL-225 — deduplicate() does not modify original list."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        items = [
            {"id": "WL-001"},
            {"id": "WL-001"},
        ]
        deduplicated = normalizer.deduplicate(items)

        assert len(items) == 2
        assert len(deduplicated) == 1

    def test_deduplicate_empty_list(self):
        """# @trace WL-225 — deduplicate() handles empty list."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        deduplicated = normalizer.deduplicate([])

        assert deduplicated == []

    def test_deduplicate_no_duplicates(self):
        """# @trace WL-225 — deduplicate() returns all items if no duplicates."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        items = [
            {"id": "WL-001"},
            {"id": "WL-002"},
            {"id": "WL-003"},
        ]
        deduplicated = normalizer.deduplicate(items)

        assert len(deduplicated) == 3

    def test_deduplicate_with_none_values(self):
        """# @trace WL-225 — deduplicate() handles None values."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        items = [
            {"id": "WL-001"},
            {"id": None},
            {"id": "WL-002"},
            {"id": None},
        ]
        deduplicated = normalizer.deduplicate(items)

        assert len(deduplicated) == 3
        assert deduplicated[1]["id"] is None

    def test_sort_and_normalize_chaining(self):
        """# @trace WL-225 — sort(), normalize_ids() can be chained."""
        from thegent.integrations.wl_sort_normalize import WLSortNormalizer

        normalizer = WLSortNormalizer()
        items = [
            {"id": "wl-003", "title": "C"},
            {"id": "wl-001", "title": "A"},
            {"id": "wl-002", "title": "B"},
        ]

        result = normalizer.normalize_ids(items)
        result = normalizer.sort(result)

        assert result[0]["id"] == "WL-001"
        assert result[1]["id"] == "WL-002"
        assert result[2]["id"] == "WL-003"
