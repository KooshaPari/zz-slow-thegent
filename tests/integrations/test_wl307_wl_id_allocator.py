"""Tests for thegent.integrations.wl_id_allocator — WL ID reservation allocator.

@trace WL-307
"""

from __future__ import annotations

import pytest

from thegent.integrations.wl_id_allocator import WLIdAllocator, WLRange


class TestWLRange:
    """Test WLRange dataclass. @trace WL-307"""

    @pytest.mark.requirement("WL-307")
    def test_create_wl_range(self) -> None:
        """Can create a WLRange with all fields."""
        wl_range = WLRange(start=1, end=100, label="Phase 1", reserved_by="alice")

        assert wl_range.start == 1
        assert wl_range.end == 100
        assert wl_range.label == "Phase 1"
        assert wl_range.reserved_by == "alice"

    @pytest.mark.requirement("WL-307")
    def test_wl_range_single_id(self) -> None:
        """Can create WLRange for single ID."""
        wl_range = WLRange(start=42, end=42, label="Single", reserved_by="bob")
        assert wl_range.start == wl_range.end


class TestWLIdAllocator:
    """Test WLIdAllocator operations. @trace WL-307"""

    @pytest.fixture
    def allocator(self) -> WLIdAllocator:
        """Provide a WLIdAllocator instance."""
        return WLIdAllocator()

    @pytest.mark.requirement("WL-307")
    def test_reserve_range(self, allocator: WLIdAllocator) -> None:
        """Can reserve a range of WL IDs."""
        wl_range = allocator.reserve_range(1, 100, "Phase 1", "alice")

        assert wl_range.start == 1
        assert wl_range.end == 100
        assert wl_range.label == "Phase 1"
        assert wl_range.reserved_by == "alice"

    @pytest.mark.requirement("WL-307")
    def test_reserve_single_id(self, allocator: WLIdAllocator) -> None:
        """Can reserve a single WL ID."""
        wl_range = allocator.reserve_range(42, 42, "Special", "bob")

        assert wl_range.start == 42
        assert wl_range.end == 42

    @pytest.mark.requirement("WL-307")
    def test_reserve_range_start_greater_than_end_raises_error(
        self, allocator: WLIdAllocator
    ) -> None:
        """Reserving with start > end raises ValueError."""
        with pytest.raises(ValueError, match=r"start.*must be.*end"):
            allocator.reserve_range(100, 1, "Bad", "alice")

    @pytest.mark.requirement("WL-307")
    def test_reserve_overlapping_range_raises_error(
        self, allocator: WLIdAllocator
    ) -> None:
        """Reserving overlapping range raises ValueError."""
        allocator.reserve_range(1, 100, "Phase 1", "alice")

        with pytest.raises(ValueError, match=r"overlaps"):
            allocator.reserve_range(50, 150, "Phase 2", "bob")

    @pytest.mark.requirement("WL-307")
    def test_reserve_adjacent_ranges_allowed(self, allocator: WLIdAllocator) -> None:
        """Adjacent ranges (non-overlapping) are allowed."""
        allocator.reserve_range(1, 100, "Phase 1", "alice")
        wl_range2 = allocator.reserve_range(101, 200, "Phase 2", "bob")

        assert wl_range2.start == 101

    @pytest.mark.requirement("WL-307")
    def test_next_available_empty(self, allocator: WLIdAllocator) -> None:
        """next_available from empty allocator returns 1."""
        result = allocator.next_available()
        assert result == 1

    @pytest.mark.requirement("WL-307")
    def test_next_available_after_zero(self, allocator: WLIdAllocator) -> None:
        """next_available(after=0) returns 1."""
        result = allocator.next_available(after=0)
        assert result == 1

    @pytest.mark.requirement("WL-307")
    def test_next_available_with_reservations(self, allocator: WLIdAllocator) -> None:
        """next_available skips reserved ranges."""
        allocator.reserve_range(1, 100, "Phase 1", "alice")

        result = allocator.next_available()
        assert result == 101

    @pytest.mark.requirement("WL-307")
    def test_next_available_after_reserved(self, allocator: WLIdAllocator) -> None:
        """next_available respects after parameter."""
        allocator.reserve_range(1, 100, "Phase 1", "alice")

        result = allocator.next_available(after=200)
        assert result == 201

    @pytest.mark.requirement("WL-307")
    def test_next_available_with_gap(self, allocator: WLIdAllocator) -> None:
        """next_available finds gaps in reservations."""
        allocator.reserve_range(1, 50, "Phase 1", "alice")
        allocator.reserve_range(100, 200, "Phase 2", "bob")

        result = allocator.next_available()
        # Should return 51 (first available after first reservation)
        assert result == 51

    @pytest.mark.requirement("WL-307")
    def test_is_reserved_empty(self, allocator: WLIdAllocator) -> None:
        """is_reserved returns False for empty allocator."""
        assert allocator.is_reserved(42) is False

    @pytest.mark.requirement("WL-307")
    def test_is_reserved_within_range(self, allocator: WLIdAllocator) -> None:
        """is_reserved returns True for IDs within reserved range."""
        allocator.reserve_range(1, 100, "Phase 1", "alice")

        assert allocator.is_reserved(1) is True
        assert allocator.is_reserved(50) is True
        assert allocator.is_reserved(100) is True

    @pytest.mark.requirement("WL-307")
    def test_is_reserved_outside_range(self, allocator: WLIdAllocator) -> None:
        """is_reserved returns False for IDs outside reserved range."""
        allocator.reserve_range(1, 100, "Phase 1", "alice")

        assert allocator.is_reserved(0) is False
        assert allocator.is_reserved(101) is False

    @pytest.mark.requirement("WL-307")
    def test_list_ranges_empty(self, allocator: WLIdAllocator) -> None:
        """list_ranges returns empty list for empty allocator."""
        result = allocator.list_ranges()
        assert result == []

    @pytest.mark.requirement("WL-307")
    def test_list_ranges_single(self, allocator: WLIdAllocator) -> None:
        """list_ranges returns single range."""
        allocator.reserve_range(1, 100, "Phase 1", "alice")
        result = allocator.list_ranges()

        assert len(result) == 1
        assert result[0].start == 1

    @pytest.mark.requirement("WL-307")
    def test_list_ranges_sorted(self, allocator: WLIdAllocator) -> None:
        """list_ranges returns ranges sorted by start ID."""
        allocator.reserve_range(200, 300, "Phase 2", "bob")
        allocator.reserve_range(1, 100, "Phase 1", "alice")
        allocator.reserve_range(400, 500, "Phase 3", "charlie")

        result = allocator.list_ranges()

        assert len(result) == 3
        assert result[0].start == 1
        assert result[1].start == 200
        assert result[2].start == 400

    @pytest.mark.requirement("WL-307")
    def test_check_overlap_empty(self, allocator: WLIdAllocator) -> None:
        """check_overlap returns False for empty allocator."""
        assert allocator.check_overlap(1, 100) is False

    @pytest.mark.requirement("WL-307")
    def test_check_overlap_no_overlap(self, allocator: WLIdAllocator) -> None:
        """check_overlap returns False for non-overlapping range."""
        allocator.reserve_range(1, 100, "Phase 1", "alice")

        assert allocator.check_overlap(101, 200) is False
        assert allocator.check_overlap(200, 300) is False

    @pytest.mark.requirement("WL-307")
    def test_check_overlap_complete_overlap(self, allocator: WLIdAllocator) -> None:
        """check_overlap returns True for complete overlap."""
        allocator.reserve_range(1, 100, "Phase 1", "alice")

        assert allocator.check_overlap(1, 100) is True

    @pytest.mark.requirement("WL-307")
    def test_check_overlap_partial_overlap_start(
        self, allocator: WLIdAllocator
    ) -> None:
        """check_overlap returns True for overlap at start."""
        allocator.reserve_range(100, 200, "Phase 1", "alice")

        assert allocator.check_overlap(50, 150) is True

    @pytest.mark.requirement("WL-307")
    def test_check_overlap_partial_overlap_end(self, allocator: WLIdAllocator) -> None:
        """check_overlap returns True for overlap at end."""
        allocator.reserve_range(100, 200, "Phase 1", "alice")

        assert allocator.check_overlap(150, 250) is True

    @pytest.mark.requirement("WL-307")
    def test_check_overlap_contained_in_existing(
        self, allocator: WLIdAllocator
    ) -> None:
        """check_overlap returns True for range contained in existing."""
        allocator.reserve_range(1, 200, "Phase 1", "alice")

        assert allocator.check_overlap(50, 150) is True

    @pytest.mark.requirement("WL-307")
    def test_check_overlap_contains_existing(self, allocator: WLIdAllocator) -> None:
        """check_overlap returns True for range containing existing."""
        allocator.reserve_range(100, 150, "Phase 1", "alice")

        assert allocator.check_overlap(1, 200) is True

    @pytest.mark.requirement("WL-307")
    def test_workflow_sequential_allocation(self, allocator: WLIdAllocator) -> None:
        """Typical workflow: reserve phase ranges sequentially."""
        allocator.reserve_range(1, 100, "Phase 1", "alice")
        allocator.reserve_range(101, 200, "Phase 2", "bob")
        allocator.reserve_range(201, 300, "Phase 3", "charlie")

        # Check all are recognized as reserved
        assert allocator.is_reserved(50) is True
        assert allocator.is_reserved(150) is True
        assert allocator.is_reserved(250) is True

        # Find next available
        assert allocator.next_available() == 301
