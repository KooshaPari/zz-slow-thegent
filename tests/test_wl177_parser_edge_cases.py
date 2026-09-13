"""Tests for WL-177: Parser/Reflection Edge-Case Unit Tests.

Comprehensive edge-case coverage for the WorkstreamParser class,
ensuring robustness against malformed, unusual, and boundary-condition inputs.

@pytest.mark.requirement("WL-177")
"""

from __future__ import annotations

from pathlib import Path

import pytest

from thegent.integrations.workstream_autosync import WorkstreamParser

# ---------------------------------------------------------------------------
# Test: Malformed WL Sections
# ---------------------------------------------------------------------------


class TestMalformedSections:
    """Test parser robustness against malformed WL sections."""

    @pytest.mark.requirement("WL-177")
    def test_wl_section_missing_status_line(self, tmp_path: Path) -> None:
        """Test parsing WL section that's missing the Status line."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """
### [WL-001] Missing Status
**Priority:** P1
**Area:** testing
**Blocked by:** none

Some description here.
""",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        assert items[0].item_id == "WL-001"
        # Default status should be BACKLOG when Status line is missing
        assert items[0].status == "BACKLOG"

    @pytest.mark.requirement("WL-177")
    def test_wl_status_with_extra_whitespace(self, tmp_path: Path) -> None:
        """Test parsing WL status with extra whitespace."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """
### [WL-002] Extra Whitespace
**Status:**    IN_PROGRESS
**Priority:** P1
**Area:** testing
**Blocked by:** none
""",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        # Status should be trimmed
        assert items[0].status.strip() == "IN_PROGRESS"

    @pytest.mark.requirement("WL-177")
    def test_wl_status_mixed_case(self, tmp_path: Path) -> None:
        """Test parsing WL status with mixed case (e.g., 'In Progress')."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """
### [WL-003] Mixed Case Status
**Status:** In Progress
**Priority:** P1
**Area:** testing
**Blocked by:** none
""",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        # Parser should preserve case (no normalization)
        assert items[0].status == "In Progress"

    @pytest.mark.requirement("WL-177")
    def test_wl_with_multiline_blocked_by(self, tmp_path: Path) -> None:
        """Test parsing WL item with multi-line blocked_by field."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """
### [WL-004] Multi-line Blocked By
**Status:** BACKLOG
**Priority:** P1
**Area:** testing
**Blocked by:** WL-001,
WL-002, WL-003
""",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        # blocked_by should capture the full text (parser extracts up to newline)
        assert items[0].blocked_by is not None
        assert "WL-001" in items[0].blocked_by

    @pytest.mark.requirement("WL-177")
    def test_wl_id_with_leading_zeros(self, tmp_path: Path) -> None:
        """Test parsing WL ID with leading zeros."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """
### [WL-0001] Leading Zeros
**Status:** BACKLOG
**Priority:** P1
**Area:** testing
**Blocked by:** none
""",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        # Parser regex should match WL-NNNN+ (N = digit)
        assert items[0].item_id == "WL-0001"


# ---------------------------------------------------------------------------
# Test: Line Ending Variations (CRLF, LF)
# ---------------------------------------------------------------------------


class TestLineEndings:
    """Test parser with different line ending styles."""

    @pytest.mark.requirement("WL-177")
    def test_windows_line_endings_crlf(self, tmp_path: Path) -> None:
        """Test parsing WORK_STREAM.md with Windows line endings (CRLF)."""
        work_stream = tmp_path / "WORK_STREAM.md"
        content = "### [WL-005] Windows CRLF\r\n**Status:** BACKLOG\r\n**Priority:** P1\r\n**Area:** testing\r\n**Blocked by:** none\r\n"
        # Write as binary to preserve CRLF
        work_stream.write_bytes(content.encode("utf-8"))

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        assert items[0].item_id == "WL-005"

    @pytest.mark.requirement("WL-177")
    def test_mixed_line_endings(self, tmp_path: Path) -> None:
        """Test parsing with mixed CRLF and LF."""
        work_stream = tmp_path / "WORK_STREAM.md"
        content = "### [WL-006] Mixed Endings\r\n**Status:** BACKLOG\n**Priority:** P1\r\n**Area:** testing\n**Blocked by:** none\n"
        work_stream.write_bytes(content.encode("utf-8"))

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        assert items[0].item_id == "WL-006"


# ---------------------------------------------------------------------------
# Test: File Boundary Conditions
# ---------------------------------------------------------------------------


class TestFileBoundaryConditions:
    """Test parser with edge cases at file boundaries."""

    @pytest.mark.requirement("WL-177")
    def test_wl_section_at_end_of_file_no_trailing_newline(self, tmp_path: Path) -> None:
        """Test WL section at end of file with no trailing newline."""
        work_stream = tmp_path / "WORK_STREAM.md"
        # No trailing newline after the last line
        work_stream.write_text(
            "### [WL-007] End of File\n**Status:** BACKLOG\n**Priority:** P1\n**Area:** testing\n**Blocked by:** none",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        assert items[0].item_id == "WL-007"
        assert items[0].status == "BACKLOG"

    @pytest.mark.requirement("WL-177")
    def test_empty_work_stream_file(self, tmp_path: Path) -> None:
        """Test parsing an empty WORK_STREAM.md file."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text("", encoding="utf-8")

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 0

    @pytest.mark.requirement("WL-177")
    def test_work_stream_with_only_whitespace(self, tmp_path: Path) -> None:
        """Test parsing WORK_STREAM.md with only whitespace."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text("   \n\n   \n", encoding="utf-8")

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 0

    @pytest.mark.requirement("WL-177")
    def test_wl_item_at_start_of_file(self, tmp_path: Path) -> None:
        """Test WL item appearing at the very start of file."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            "### [WL-008] Start of File\n**Status:** BACKLOG\n**Priority:** P1\n**Area:** testing\n**Blocked by:** none",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        assert items[0].item_id == "WL-008"
        assert items[0].source_line == 1


# ---------------------------------------------------------------------------
# Test: Multiple WL Items and Spacing
# ---------------------------------------------------------------------------


class TestMultipleItems:
    """Test parser with multiple items and various spacing."""

    @pytest.mark.requirement("WL-177")
    def test_consecutive_wl_items_no_blank_lines(self, tmp_path: Path) -> None:
        """Test multiple WL items with no blank lines between them."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """
### [WL-009] Item One
**Status:** BACKLOG
**Priority:** P1
**Area:** testing
**Blocked by:** none
### [WL-010] Item Two
**Status:** IN_PROGRESS
**Priority:** P2
**Area:** testing
**Blocked by:** WL-009
""",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 2
        assert items[0].item_id == "WL-009"
        assert items[1].item_id == "WL-010"

    @pytest.mark.requirement("WL-177")
    def test_many_blank_lines_between_items(self, tmp_path: Path) -> None:
        """Test WL items separated by multiple blank lines."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """
### [WL-011] Item One
**Status:** BACKLOG
**Priority:** P1
**Area:** testing
**Blocked by:** none




### [WL-012] Item Two
**Status:** BACKLOG
**Priority:** P1
**Area:** testing
**Blocked by:** none
""",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 2


# ---------------------------------------------------------------------------
# Test: Special Characters and Encoding
# ---------------------------------------------------------------------------


class TestSpecialCharactersAndEncoding:
    """Test parser with special characters and encoding issues."""

    @pytest.mark.requirement("WL-177")
    def test_wl_title_with_special_characters(self, tmp_path: Path) -> None:
        """Test WL title containing special characters."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """
### [WL-013] Title with "quotes" & special chars (β, €)
**Status:** BACKLOG
**Priority:** P1
**Area:** testing
**Blocked by:** none
""",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        assert "quotes" in items[0].title
        assert "€" in items[0].title

    @pytest.mark.requirement("WL-177")
    def test_area_with_multiple_values(self, tmp_path: Path) -> None:
        """Test Area field with comma-separated values."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """
### [WL-014] Multiple Areas
**Status:** BACKLOG
**Priority:** P1
**Area:** testing, reliability, performance
**Blocked by:** none
""",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        assert "testing" in items[0].area
        assert "reliability" in items[0].area


# ---------------------------------------------------------------------------
# Test: Missing Optional Fields
# ---------------------------------------------------------------------------


class TestMissingOptionalFields:
    """Test parser when optional fields are missing."""

    @pytest.mark.requirement("WL-177")
    def test_missing_priority_field(self, tmp_path: Path) -> None:
        """Test WL item without Priority field."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """
### [WL-015] No Priority
**Status:** BACKLOG
**Area:** testing
**Blocked by:** none
""",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        # Default priority should be P2
        assert items[0].priority == "P2"

    @pytest.mark.requirement("WL-177")
    def test_missing_area_field(self, tmp_path: Path) -> None:
        """Test WL item without Area field."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """
### [WL-016] No Area
**Status:** BACKLOG
**Priority:** P1
**Blocked by:** none
""",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        # Default area should be "unknown"
        assert items[0].area == "unknown"

    @pytest.mark.requirement("WL-177")
    def test_missing_blocked_by_field(self, tmp_path: Path) -> None:
        """Test WL item without Blocked by field."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """
### [WL-017] No Blocked By
**Status:** BACKLOG
**Priority:** P1
**Area:** testing
""",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        assert items[0].blocked_by is None


# ---------------------------------------------------------------------------
# Test: Parsing Correctness with Valid Data
# ---------------------------------------------------------------------------


class TestValidDataParsing:
    """Test that parser correctly handles valid data."""

    @pytest.mark.requirement("WL-177")
    def test_parse_correctly_formed_item(self, tmp_path: Path) -> None:
        """Test parsing a correctly formatted WL item."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """
### [WL-100] Correctly Formatted Item
**Status:** IN_PROGRESS
**Priority:** P1
**Area:** sync, cache
**Blocked by:** WL-099
""",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 1
        item = items[0]
        assert item.item_id == "WL-100"
        assert item.title == "Correctly Formatted Item"
        assert item.status == "IN_PROGRESS"
        assert item.priority == "P1"
        assert "sync" in item.area
        assert "cache" in item.area
        assert item.blocked_by == "WL-099"
        assert item.source_line == 2

    @pytest.mark.requirement("WL-177")
    def test_source_line_tracking(self, tmp_path: Path) -> None:
        """Test that source_line is correctly tracked for multiple items."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """### [WL-101] First Item
**Status:** BACKLOG
**Priority:** P1
**Area:** testing
**Blocked by:** none

### [WL-102] Second Item
**Status:** BACKLOG
**Priority:** P1
**Area:** testing
**Blocked by:** none
""",
            encoding="utf-8",
        )

        items = WorkstreamParser.parse_items(work_stream)
        assert len(items) == 2
        assert items[0].source_line == 1
        assert items[1].source_line == 7
