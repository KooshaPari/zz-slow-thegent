"""Tests for workstream_ops module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from thegent.utils.workstream_ops import WorkStreamOps


class TestWorkStreamOps:
    """Tests for WorkStreamOps."""

    @pytest.fixture
    def work_stream_file(self, tmp_path: Path) -> Path:
        """Create a mock WORK_STREAM.md file."""
        ws_path = tmp_path / "WORK_STREAM.md"
        content = """# WORK_STREAM.md

## BACKLOG

| ID | Title | Source | Priority | Depends |
|----|-------|--------|----------|---------|
| WS-001 | First item | Plan A | P0 | - |
| WS-002 | Second item | Plan B | P1 | WS-001 |
| ~~WS-003~~ | Completed item | Plan A | P2 | - |

## CLAIMED

| ID | Agent | Claimed At |
|----|-------|------------|
| WS-004 | Agent-1 | 2026-02-20T10:00:00Z |

## COMPLETED

| ID | Agent | Completed At |
|----|-------|--------------|
| WS-005 | Agent-2 | 2026-02-20T11:00:00Z |
"""
        ws_path.write_text(content)
        return ws_path

    def test_read_backlog(self, work_stream_file: Path) -> None:
        """Test reading backlog items."""
        ops = WorkStreamOps(base_dir=work_stream_file.parent)
        ops.work_stream_path = work_stream_file

        items = ops.read_backlog()
        assert len(items) == 2
        assert items[0]["id"] == "WS-001"
        assert items[0]["title"] == "First item"
        assert items[1]["id"] == "WS-002"
        assert items[1]["priority"] == "P1"

    def test_claim_item(self, work_stream_file: Path) -> None:
        """Test claiming an item."""
        ops = WorkStreamOps(base_dir=work_stream_file.parent)
        ops.work_stream_path = work_stream_file

        success = ops.claim_item("WS-006", "Test-Agent")
        assert success

        content = work_stream_file.read_text()
        assert "## CLAIMED" in content
        assert "| WS-006 | Test-Agent |" in content

    def test_complete_item(self, work_stream_file: Path) -> None:
        """Test completing an item."""
        ops = WorkStreamOps(base_dir=work_stream_file.parent)
        ops.work_stream_path = work_stream_file

        success = ops.complete_item("WS-001", "Test-Agent")
        assert success

        content = work_stream_file.read_text()
        # Item should be struck through in backlog
        assert "~~WS-001~~" in content
        # Item should be in completed section
        assert "## COMPLETED" in content
        assert "| WS-001 | Test-Agent |" in content

    def test_get_progress(self, work_stream_file: Path) -> None:
        """Test progress calculation."""
        ops = WorkStreamOps(base_dir=work_stream_file.parent)
        ops.work_stream_path = work_stream_file

        progress = ops.get_progress()
        assert progress["total"] == 3  # WS-001, WS-002, WS-003
        assert progress["completed"] == 1  # WS-003 is already completed
        assert progress["backlog"] == 2  # WS-001, WS-002

    def test_claim_item_returns_false_when_lock_contention(self, work_stream_file: Path) -> None:
        """Return false when the file lock cannot be acquired."""
        ops = WorkStreamOps(base_dir=work_stream_file.parent)
        ops.work_stream_path = work_stream_file

        with patch(
            "thegent.utils.workstream_ops._locked_file_access", side_effect=BlockingIOError(11, "resource unavailable")
        ):
            success = ops.claim_item("WS-006", "Test-Agent")

        assert success is False
        assert "| WS-006 | Test-Agent |" not in work_stream_file.read_text()

    def test_complete_item_returns_false_when_lock_contention(self, work_stream_file: Path) -> None:
        """Return false when complete cannot acquire write lock."""
        ops = WorkStreamOps(base_dir=work_stream_file.parent)
        ops.work_stream_path = work_stream_file

        with patch(
            "thegent.utils.workstream_ops._locked_file_access", side_effect=BlockingIOError(11, "resource unavailable")
        ):
            success = ops.complete_item("WS-001", "Test-Agent")

        assert success is False
        content = work_stream_file.read_text()
        assert "| WS-001 | Test-Agent |" not in content

    def test_find_work_stream_fallback(self, tmp_path: Path) -> None:
        """Test fallback location for find_work_stream."""
        ops = WorkStreamOps(base_dir=tmp_path)
        expected = tmp_path / "docs" / "reference" / "WORK_STREAM.md"
        assert ops.work_stream_path == expected

    @pytest.mark.requirement("WL-224")
    def test_lint_schema(self, tmp_path: Path) -> None:
        """Validate schema linting includes missing required sections."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """# Unified Work Stream

### [WL-1] Missing Sections
**Status:** BACKLOG
""",
            encoding="utf-8",
        )
        ops = WorkStreamOps(base_dir=tmp_path)
        ops.work_stream_path = work_stream

        errors = ops.lint_schema()
        assert any("missing required section" in error for error in errors)

    @pytest.mark.requirement("WL-225")
    def test_sort_and_normalize(self, tmp_path: Path) -> None:
        """Normalize and sort WL sections into canonical order."""
        work_stream = tmp_path / "WORK_STREAM.md"
        work_stream.write_text(
            """### [WL-20] Second
**Status:** BACKLOG

### [WL-10] First
**Status:** BACKLOG
""",
            encoding="utf-8",
        )
        ops = WorkStreamOps(base_dir=tmp_path)
        ops.work_stream_path = work_stream

        normalized = ops.sort_and_normalize()
        assert normalized.find("WL-10") < normalized.find("WL-20")
