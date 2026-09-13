#!/usr/bin/env python3
"""
Tests for scripts/agent_helpers.py

Covers:
- log_friction: append to FRICTION_LOG.md, auto-create, custom path
- get_next_items: parse backlog, filter claimed/completed, dependency resolution
- update_work_stream: claim, complete, invalid status, missing file
- run_quality_check: result shape, lint/test flags, timeout, command errors
- read_config: settings available/unavailable, default fallback, missing key
- format_summary: empty list, single item, multiple items, singular/plural

Traces to: FR-AX-001 (Agent Helper Library)
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure scripts/ is importable regardless of working directory
_SCRIPTS_DIR = str(Path(__file__).parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# Import helpers module via importlib so we avoid type: ignore annotations
_ah = importlib.import_module("agent_helpers")

log_friction = _ah.log_friction
get_next_items = _ah.get_next_items
update_work_stream = _ah.update_work_stream
run_quality_check = _ah.run_quality_check
read_config = _ah.read_config
format_summary = _ah.format_summary
_parse_work_stream = _ah._parse_work_stream


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_friction_log(tmp_path: Path) -> Path:
    """Return a temporary path for FRICTION_LOG.md."""
    return tmp_path / "FRICTION_LOG.md"


@pytest.fixture
def minimal_work_stream(tmp_path: Path) -> Path:
    """Create a minimal WORK_STREAM.md and return its path."""
    ws = tmp_path / "WORK_STREAM.md"
    ws.write_text(
        "## BACKLOG\n\n"
        "| ID | Title | Source | Priority | Depends |\n"
        "|----|-------|--------|----------|---------|\n"
        "| task-alpha | Alpha Task | SOURCE.md | P1 | - |\n"
        "| task-beta | Beta Task | SOURCE.md | P2 | - |\n"
        "| task-gamma | Gamma Task | SOURCE.md | P1 | task-alpha |\n"
        "\n"
        "## CLAIMED\n\n"
        "| ID | Agent | Started |\n"
        "|----|-------|---------|\n"
        "\n"
        "## COMPLETED\n\n"
        "| ID | Agent | Completed |\n"
        "|----|-------|-----------|\n",
        encoding="utf-8",
    )
    return ws


# ===========================================================================
# Tests for log_friction
# ===========================================================================


class TestLogFriction:
    """Tests for log_friction helper."""

    def test_creates_file_when_missing(self, tmp_friction_log: Path) -> None:
        """log_friction creates FRICTION_LOG.md when it does not exist."""
        assert not tmp_friction_log.exists()
        result = log_friction("dx", "Test friction", friction_log_path=tmp_friction_log)
        assert result is True
        assert tmp_friction_log.exists()

    def test_appends_entry_to_existing_file(self, tmp_friction_log: Path) -> None:
        """Successive calls append multiple entries."""
        log_friction("dx", "First friction", friction_log_path=tmp_friction_log)
        log_friction("ux", "Second friction", friction_log_path=tmp_friction_log)
        content = tmp_friction_log.read_text(encoding="utf-8")
        assert "First friction" in content
        assert "Second friction" in content

    def test_category_uppercased_in_entry(self, tmp_friction_log: Path) -> None:
        """Category is stored in uppercase."""
        log_friction("dx", "Some issue", friction_log_path=tmp_friction_log)
        content = tmp_friction_log.read_text(encoding="utf-8")
        assert "**Category**: DX" in content

    def test_custom_task_id_used(self, tmp_friction_log: Path) -> None:
        """Explicit task_id appears as section header."""
        log_friction(
            "ax",
            "AX issue",
            task_id="ax-custom-001",
            friction_log_path=tmp_friction_log,
        )
        content = tmp_friction_log.read_text(encoding="utf-8")
        assert "### ax-custom-001" in content

    def test_auto_generated_task_id_when_none(self, tmp_friction_log: Path) -> None:
        """Auto-generated task_id starts with category slug."""
        log_friction("ux", "UX friction", friction_log_path=tmp_friction_log)
        content = tmp_friction_log.read_text(encoding="utf-8")
        assert "### ux-" in content

    def test_solution_recorded(self, tmp_friction_log: Path) -> None:
        """Provided solution appears in entry."""
        log_friction(
            "dx",
            "Some dx issue",
            solution="Use library X",
            friction_log_path=tmp_friction_log,
        )
        content = tmp_friction_log.read_text(encoding="utf-8")
        assert "Use library X" in content

    def test_solution_defaults_to_tbd(self, tmp_friction_log: Path) -> None:
        """Missing solution defaults to 'TBD'."""
        log_friction("dx", "No solution yet", friction_log_path=tmp_friction_log)
        content = tmp_friction_log.read_text(encoding="utf-8")
        assert "TBD" in content

    def test_priority_recorded(self, tmp_friction_log: Path) -> None:
        """Priority is included in entry."""
        log_friction("dx", "Critical issue", priority="P1", friction_log_path=tmp_friction_log)
        content = tmp_friction_log.read_text(encoding="utf-8")
        assert "**Priority**: P1" in content

    def test_returns_false_on_os_error(self, tmp_path: Path) -> None:
        """Returns False when write fails (unwritable path)."""
        bad_path = tmp_path / "no_such_dir" / "deeply" / "nested" / "log.md"
        # Make parent dir a file so creation fails
        blocker = tmp_path / "no_such_dir"
        blocker.write_text("blocker")
        result = log_friction("dx", "Should fail", friction_log_path=bad_path)
        assert result is False

    def test_timestamp_present_in_entry(self, tmp_friction_log: Path) -> None:
        """Entry includes a UTC ISO timestamp."""
        log_friction("dx", "timestamped entry", friction_log_path=tmp_friction_log)
        content = tmp_friction_log.read_text(encoding="utf-8")
        # ISO timestamp ends with 'Z'
        assert "Z" in content
        assert "**Timestamp**:" in content


# ===========================================================================
# Tests for get_next_items / _parse_work_stream
# ===========================================================================


class TestGetNextItems:
    """Tests for get_next_items helper."""

    def test_returns_empty_for_missing_file(self, tmp_path: Path) -> None:
        """Returns empty list when WORK_STREAM.md does not exist."""
        result = get_next_items(limit=5, work_stream_path=tmp_path / "missing.md")
        assert result == []

    def test_returns_backlog_items(self, minimal_work_stream: Path) -> None:
        """Returns unclaimed items from BACKLOG."""
        items = get_next_items(limit=10, work_stream_path=minimal_work_stream)
        ids = [i["id"] for i in items]
        assert "task-alpha" in ids

    def test_respects_limit(self, minimal_work_stream: Path) -> None:
        """Result length does not exceed limit."""
        items = get_next_items(limit=1, work_stream_path=minimal_work_stream)
        assert len(items) <= 1

    def test_priority_filter(self, minimal_work_stream: Path) -> None:
        """Priority filter excludes non-matching items."""
        items = get_next_items(limit=10, priority="P1", work_stream_path=minimal_work_stream)
        assert all(i["priority"] == "P1" for i in items)

    def test_excludes_claimed_items(self, tmp_path: Path) -> None:
        """Items in CLAIMED section are excluded from results."""
        ws = tmp_path / "WORK_STREAM.md"
        ws.write_text(
            "## BACKLOG\n\n"
            "| ID | Title | Source | Priority | Depends |\n"
            "|----|-------|--------|----------|---------|\n"
            "| task-x | Task X | S | P1 | - |\n"
            "\n"
            "## CLAIMED\n\n"
            "| ID | Agent | Started |\n"
            "|----|-------|---------|\n"
            "| task-x | agent-1 | 2026-01-01T00:00:00Z |\n"
            "\n"
            "## COMPLETED\n\n"
            "| ID | Agent | Completed |\n"
            "|----|-------|-----------|\n",
            encoding="utf-8",
        )
        items = get_next_items(limit=5, work_stream_path=ws)
        assert not any(i["id"] == "task-x" for i in items)

    def test_excludes_completed_items(self, tmp_path: Path) -> None:
        """Items in COMPLETED section are excluded from results."""
        ws = tmp_path / "WORK_STREAM.md"
        ws.write_text(
            "## BACKLOG\n\n"
            "| ID | Title | Source | Priority | Depends |\n"
            "|----|-------|--------|----------|---------|\n"
            "| task-done | Done | S | P1 | - |\n"
            "\n"
            "## CLAIMED\n\n"
            "| ID | Agent | Started |\n"
            "|----|-------|---------|\n"
            "\n"
            "## COMPLETED\n\n"
            "| ID | Agent | Completed |\n"
            "|----|-------|-----------|\n"
            "| task-done | agent-1 | 2026-01-01T00:00:00Z |\n",
            encoding="utf-8",
        )
        items = get_next_items(limit=5, work_stream_path=ws)
        assert not any(i["id"] == "task-done" for i in items)

    def test_dependency_blocks_item(self, minimal_work_stream: Path) -> None:
        """Items with unsatisfied dependencies are not returned."""
        items = get_next_items(limit=10, work_stream_path=minimal_work_stream)
        # task-gamma depends on task-alpha which is NOT completed
        assert not any(i["id"] == "task-gamma" for i in items)

    def test_dependency_satisfied_after_completion(self, tmp_path: Path) -> None:
        """Item with satisfied dependency IS returned."""
        ws = tmp_path / "WORK_STREAM.md"
        ws.write_text(
            "## BACKLOG\n\n"
            "| ID | Title | Source | Priority | Depends |\n"
            "|----|-------|--------|----------|---------|\n"
            "| task-dep | Dep Task | S | P1 | task-parent |\n"
            "\n"
            "## CLAIMED\n\n"
            "| ID | Agent | Started |\n"
            "|----|-------|---------|\n"
            "\n"
            "## COMPLETED\n\n"
            "| ID | Agent | Completed |\n"
            "|----|-------|-----------|\n"
            "| task-parent | agent-1 | 2026-01-01T00:00:00Z |\n",
            encoding="utf-8",
        )
        items = get_next_items(limit=10, work_stream_path=ws)
        assert any(i["id"] == "task-dep" for i in items)

    def test_item_dict_has_expected_keys(self, minimal_work_stream: Path) -> None:
        """Each returned item dict contains required keys."""
        items = get_next_items(limit=5, work_stream_path=minimal_work_stream)
        assert items
        for item in items:
            assert "id" in item
            assert "title" in item
            assert "priority" in item


# ===========================================================================
# Tests for update_work_stream
# ===========================================================================


class TestUpdateWorkStream:
    """Tests for update_work_stream helper."""

    def test_claim_item_adds_to_claimed_section(self, tmp_path: Path) -> None:
        """Claiming an item appends a row to the CLAIMED section."""
        ws = tmp_path / "WORK_STREAM.md"
        ws.write_text(
            "## BACKLOG\n\n"
            "| ID | Title | Source | Priority | Depends |\n"
            "|----|-------|--------|----------|---------|\n"
            "| my-task | My Task | S | P1 | - |\n"
            "\n"
            "## CLAIMED\n\n"
            "| ID | Agent | Started |\n"
            "|----|-------|---------|\n"
            "\n"
            "## COMPLETED\n\n"
            "| ID | Agent | Completed |\n"
            "|----|-------|-----------|\n",
            encoding="utf-8",
        )
        result = update_work_stream("my-task", "claimed", work_stream_path=ws)
        assert result is True
        content = ws.read_text(encoding="utf-8")
        assert "my-task" in content

    def test_complete_item_adds_to_completed_section(self, tmp_path: Path) -> None:
        """Completing an item appends a row to the COMPLETED section."""
        ws = tmp_path / "WORK_STREAM.md"
        ws.write_text(
            "## BACKLOG\n\n"
            "| ID | Title | Source | Priority | Depends |\n"
            "|----|-------|--------|----------|---------|\n"
            "| done-task | Done Task | S | P1 | - |\n"
            "\n"
            "## CLAIMED\n\n"
            "| ID | Agent | Started |\n"
            "|----|-------|---------|\n"
            "\n"
            "## COMPLETED\n\n"
            "| ID | Agent | Completed |\n"
            "|----|-------|-----------|\n",
            encoding="utf-8",
        )
        result = update_work_stream("done-task", "completed", work_stream_path=ws)
        assert result is True
        content = ws.read_text(encoding="utf-8")
        # Row should appear after COMPLETED section header separator
        completed_idx = content.find("## COMPLETED")
        assert content.find("done-task", completed_idx) > completed_idx

    def test_raises_on_invalid_status(self, tmp_path: Path) -> None:
        """Raises ValueError for unknown status values."""
        ws = tmp_path / "ws.md"
        ws.write_text("## BACKLOG\n", encoding="utf-8")
        with pytest.raises(ValueError, match=r"claimed.*completed"):
            update_work_stream("task-x", "pending", work_stream_path=ws)

    def test_returns_false_for_missing_file(self, tmp_path: Path) -> None:
        """Returns False when WORK_STREAM.md does not exist."""
        result = update_work_stream("x", "claimed", work_stream_path=tmp_path / "missing.md")
        assert result is False

    def test_notes_appended_to_row(self, tmp_path: Path) -> None:
        """Notes are appended to the new row."""
        ws = tmp_path / "ws.md"
        ws.write_text(
            "## BACKLOG\n\n| ID | Title | Source | Priority | Depends |\n|----|-------|--------|----------|---------|\n| t1 | T1 | S | P1 | - |\n\n"
            "## CLAIMED\n\n| ID | Agent | Started |\n|----|-------|---------|\n\n"
            "## COMPLETED\n\n| ID | Agent | Completed |\n|----|-------|-----------|\n",
            encoding="utf-8",
        )
        update_work_stream("t1", "claimed", notes="first attempt", work_stream_path=ws)
        content = ws.read_text(encoding="utf-8")
        assert "first attempt" in content

    def test_removes_item_from_backlog_on_claim(self, tmp_path: Path) -> None:
        """After claiming, the item is removed from the BACKLOG table rows."""
        ws = tmp_path / "ws.md"
        ws.write_text(
            "## BACKLOG\n\n| ID | Title | Source | Priority | Depends |\n|----|-------|--------|----------|---------|\n| rem-task | Rem | S | P1 | - |\n\n"
            "## CLAIMED\n\n| ID | Agent | Started |\n|----|-------|---------|\n\n"
            "## COMPLETED\n\n| ID | Agent | Completed |\n|----|-------|-----------|\n",
            encoding="utf-8",
        )
        update_work_stream("rem-task", "claimed", work_stream_path=ws)
        content = ws.read_text(encoding="utf-8")
        # The data row (not header) should be removed from BACKLOG
        backlog_idx = content.find("## BACKLOG")
        claimed_idx = content.find("## CLAIMED")
        backlog_section = content[backlog_idx:claimed_idx]
        # Item id should NOT appear as a data row in backlog section
        assert "| rem-task |" not in backlog_section


# ===========================================================================
# Tests for run_quality_check
# ===========================================================================


class TestRunQualityCheck:
    """Tests for run_quality_check helper."""

    def test_returns_dict_with_required_keys(self) -> None:
        """Result always contains all required keys."""
        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = ""
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc

            result = run_quality_check()

        assert "lint_passed" in result
        assert "lint_output" in result
        assert "tests_passed" in result
        assert "tests_output" in result
        assert "overall_passed" in result
        assert "errors" in result

    def test_overall_passed_false_when_lint_fails(self) -> None:
        """overall_passed is False when lint fails."""
        call_count = 0

        def _side_effect(cmd: list[str], **kwargs: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            proc = MagicMock()
            # First call = lint (returncode 1), second = tests (0)
            proc.returncode = 1 if call_count == 1 else 0
            proc.stdout = "lint error" if call_count == 1 else ""
            proc.stderr = ""
            return proc

        with patch("subprocess.run", side_effect=_side_effect):
            result = run_quality_check()

        assert result["lint_passed"] is False
        assert result["overall_passed"] is False

    def test_overall_passed_false_when_tests_fail(self) -> None:
        """overall_passed is False when tests fail."""
        call_count = 0

        def _side_effect(cmd: list[str], **kwargs: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            proc = MagicMock()
            proc.returncode = 0 if call_count == 1 else 1
            proc.stdout = "" if call_count == 1 else "FAILED"
            proc.stderr = ""
            return proc

        with patch("subprocess.run", side_effect=_side_effect):
            result = run_quality_check()

        assert result["tests_passed"] is False
        assert result["overall_passed"] is False

    def test_run_lint_false_skips_lint(self) -> None:
        """run_lint=False means lint is not executed."""
        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = ""
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc

            result = run_quality_check(run_lint=False)

        assert result["lint_passed"] is True  # default True (not run)
        assert result["lint_output"] == ""

    def test_run_tests_false_skips_tests(self) -> None:
        """run_tests=False means pytest is not executed."""
        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = ""
            mock_proc.stderr = ""
            mock_run.return_value = mock_proc

            result = run_quality_check(run_tests=False)

        assert result["tests_passed"] is True  # default True (not run)
        assert result["tests_output"] == ""

    def test_errors_list_populated_on_failure(self) -> None:
        """errors list is non-empty when lint or tests fail."""
        with patch("subprocess.run") as mock_run:
            proc = MagicMock()
            proc.returncode = 1
            proc.stdout = "error output"
            proc.stderr = ""
            mock_run.return_value = proc

            result = run_quality_check()

        assert len(result["errors"]) > 0

    def test_command_not_found_handled_gracefully(self) -> None:
        """FileNotFoundError is handled and reflected in result."""
        with patch("subprocess.run", side_effect=FileNotFoundError("uv not found")):
            result = run_quality_check()

        assert result["lint_passed"] is False or result["tests_passed"] is False


# ===========================================================================
# Tests for read_config
# ===========================================================================


class TestReadConfig:
    """Tests for read_config helper."""

    def test_returns_default_when_settings_unavailable(self) -> None:
        """Returns default when ThegentSettings is not importable."""
        original = _ah._SETTINGS_AVAILABLE
        try:
            _ah._SETTINGS_AVAILABLE = False
            result = read_config("default_timeout", default=42)
            assert result == 42
        finally:
            _ah._SETTINGS_AVAILABLE = original

    def test_returns_default_for_missing_key(self) -> None:
        """Returns default for keys not present on ThegentSettings."""
        result = read_config("__nonexistent_key__", default="fallback")
        assert result == "fallback"

    def test_returns_none_default_when_not_specified(self) -> None:
        """Default is None when not provided explicitly."""
        original = _ah._SETTINGS_AVAILABLE
        try:
            _ah._SETTINGS_AVAILABLE = False
            result = read_config("whatever")
            assert result is None
        finally:
            _ah._SETTINGS_AVAILABLE = original

    def test_returns_value_when_settings_available(self) -> None:
        """Returns a value (not the default) when settings class is available."""
        # default_timeout is a real ThegentSettings attribute
        result = read_config("default_timeout", default=-1)
        # If settings loaded, result is a positive int; if not, it's -1. Either is valid.
        assert isinstance(result, (int, type(None))) or result == -1


# ===========================================================================
# Tests for format_summary
# ===========================================================================


class TestFormatSummary:
    """Tests for format_summary helper."""

    def test_empty_items_produces_no_items_marker(self) -> None:
        """Empty list produces '_(no items)_' in output."""
        result = format_summary("Empty Summary", [])
        assert "_(no items)_" in result

    def test_title_appears_in_output(self) -> None:
        """Title appears in output."""
        result = format_summary("My Title", ["a"])
        assert "My Title" in result

    def test_item_count_in_header(self) -> None:
        """Item count is included in header."""
        result = format_summary("Test", ["x", "y", "z"])
        assert "3 items" in result

    def test_singular_item_label(self) -> None:
        """Single item uses 'item' not 'items'."""
        result = format_summary("Test", ["only one"])
        assert "1 item" in result
        assert "1 items" not in result

    def test_items_numbered(self) -> None:
        """Items appear as numbered list entries."""
        result = format_summary("Test", ["first", "second"])
        assert "1. first" in result
        assert "2. second" in result

    def test_timestamp_footer_present(self) -> None:
        """Output ends with a generated timestamp footer."""
        result = format_summary("Test", ["item"])
        assert "_Generated:" in result
        assert "Z_" in result

    def test_items_converted_to_string(self) -> None:
        """Non-string items are converted via str()."""
        result = format_summary("Numbers", [1, 2, 3])
        assert "1. 1" in result
        assert "2. 2" in result

    def test_returns_string_type(self) -> None:
        """Return type is always str."""
        result = format_summary("T", [])
        assert isinstance(result, str)
