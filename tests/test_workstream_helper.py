#!/usr/bin/env python3
"""
Unit tests for scripts/workstream_helper.py

All tests use temp files for full isolation; no production WORK_STREAM.md
is ever touched.

Traces to: FR-DX-001 (work-stream automation)
"""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

# ---------------------------------------------------------------------------
# Import workstream_helper from scripts/ without mutating sys.path permanently.
# Using importlib.util lets the type checker treat this as a plain module load.
# Skipped at module level if the script has been removed (tracked follow-up).
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
_HELPER_PATH = _SCRIPTS_DIR / "workstream_helper.py"

if not _HELPER_PATH.exists():
    pytest.skip(
        f"script not present (tracked follow-up): {_HELPER_PATH.name}",
        allow_module_level=True,
    )

_spec = importlib.util.spec_from_file_location("workstream_helper", _HELPER_PATH)
assert _spec is not None
assert _spec.loader is not None
_wsh: ModuleType = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("workstream_helper", _wsh)
_spec.loader.exec_module(_wsh)

WorkStreamItem = _wsh.WorkStreamItem
WorkStreamState = _wsh.WorkStreamState
parse_work_stream = _wsh.parse_work_stream
get_next_items = _wsh.get_next_items
get_blocked_items = _wsh.get_blocked_items
claim_item = _wsh.claim_item
complete_item = _wsh.complete_item
add_backlog_item = _wsh.add_backlog_item

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_MINIMAL_MD = textwrap.dedent(
    """\
    # Unified Work Stream — Canonical

    ## BACKLOG (not started)

    | ID | Title | Source | Priority | Depends |
    |----|-------|--------|----------|---------|
    | task-alpha | Do alpha | source-a.md | P1 | - |
    | task-beta  | Do beta  | source-b.md | P2 | task-alpha |
    | task-gamma | Do gamma | source-c.md | P3 | - |

    ---

    ## CLAIMED (in progress — do not pick)

    | ID | Agent | Started | Notes |
    |----|-------|---------|-------|
    | task-delta | agent-1 | 2026-01-01T00:00:00Z |  |

    ## COMPLETED (this session / recent)
    | ID | Agent | Completed | Notes |
    |----|-------|-----------|-------|
    | task-zeta | agent-0 | 2026-01-01 | Done |
    """
)

_EMPTY_SECTIONS_MD = textwrap.dedent(
    """\
    # Work Stream

    ## BACKLOG (not started)

    | ID | Title | Source | Priority | Depends |
    |----|-------|--------|----------|---------|

    ---

    ## CLAIMED (in progress — do not pick)

    | ID | Agent | Started | Notes |
    |----|-------|---------|-------|

    ## COMPLETED (this session / recent)
    | ID | Agent | Completed | Notes |
    |----|-------|-----------|-------|
    """
)


@pytest.fixture
def ws_file(tmp_path: Path) -> Path:
    """Write minimal markdown and return the path."""
    p = tmp_path / "WORK_STREAM.md"
    p.write_text(_MINIMAL_MD, encoding="utf-8")
    return p


@pytest.fixture
def empty_ws_file(tmp_path: Path) -> Path:
    """Work stream with empty sections."""
    p = tmp_path / "WORK_STREAM.md"
    p.write_text(_EMPTY_SECTIONS_MD, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# WorkStreamItem dataclass
# ---------------------------------------------------------------------------


class TestWorkStreamItem:
    """Tests for WorkStreamItem dataclass."""

    def test_defaults(self):
        """Trace to: FR-DX-001 — item has sensible defaults."""
        item = WorkStreamItem(id="x", title="X")
        assert item.source == ""
        assert item.priority == "P2"
        assert item.depends == "-"
        assert item.status == "backlog"
        assert item.agent == ""
        assert item.timestamp == ""
        assert item.notes == ""

    def test_dependency_ids_dash(self):
        """'-' means no dependencies."""
        item = WorkStreamItem(id="x", title="X", depends="-")
        assert item.dependency_ids() == []

    def test_dependency_ids_empty(self):
        """Empty string means no dependencies."""
        item = WorkStreamItem(id="x", title="X", depends="")
        assert item.dependency_ids() == []

    def test_dependency_ids_single(self):
        """Single dependency."""
        item = WorkStreamItem(id="x", title="X", depends="task-alpha")
        assert item.dependency_ids() == ["task-alpha"]

    def test_dependency_ids_multiple(self):
        """Comma-separated dependencies."""
        item = WorkStreamItem(id="x", title="X", depends="a, b, c")
        assert item.dependency_ids() == ["a", "b", "c"]

    def test_dependency_ids_completed_marker(self):
        """Unicode completed marker means no blocking dependencies."""
        item = WorkStreamItem(id="x", title="X", depends="\u2705 Complete")
        assert item.dependency_ids() == []

    def test_priority_key_order(self):
        """P0 < P1 < P2 < P3 < P4."""
        keys = [WorkStreamItem(id="x", title="X", priority=p).priority_key() for p in ["P0", "P1", "P2", "P3", "P4"]]
        assert keys == sorted(keys)

    def test_priority_key_unknown(self):
        """Unknown priority sorts to end."""
        item = WorkStreamItem(id="x", title="X", priority="PX")
        assert item.priority_key() > WorkStreamItem(id="y", title="Y", priority="P4").priority_key()


# ---------------------------------------------------------------------------
# WorkStreamState helpers
# ---------------------------------------------------------------------------


class TestWorkStreamState:
    """Tests for WorkStreamState dataclass."""

    def test_claimed_ids(self):
        state = WorkStreamState(claimed=[WorkStreamItem(id="a", title="A", status="claimed")])
        assert "a" in state.claimed_ids()

    def test_completed_ids(self):
        state = WorkStreamState(completed=[WorkStreamItem(id="b", title="B", status="completed")])
        assert "b" in state.completed_ids()

    def test_all_items(self):
        state = WorkStreamState(
            backlog=[WorkStreamItem(id="a", title="A")],
            claimed=[WorkStreamItem(id="b", title="B", status="claimed")],
            completed=[WorkStreamItem(id="c", title="C", status="completed")],
        )
        ids = [i.id for i in state.all_items()]
        assert ids == ["a", "b", "c"]

    def test_find_by_id_found(self):
        state = WorkStreamState(backlog=[WorkStreamItem(id="found", title="Found")])
        assert state.find_by_id("found") is not None

    def test_find_by_id_missing(self):
        state = WorkStreamState()
        assert state.find_by_id("nope") is None


# ---------------------------------------------------------------------------
# parse_work_stream
# ---------------------------------------------------------------------------


class TestParseWorkStream:
    """Tests for parse_work_stream()."""

    def test_missing_file_returns_empty(self, tmp_path: Path):
        """Non-existent file -> empty state."""
        result = parse_work_stream(tmp_path / "missing.md")
        assert isinstance(result, WorkStreamState)
        assert result.backlog == []
        assert result.claimed == []
        assert result.completed == []

    def test_parses_backlog_count(self, ws_file: Path):
        state = parse_work_stream(ws_file)
        assert len(state.backlog) == 3

    def test_parses_claimed_count(self, ws_file: Path):
        state = parse_work_stream(ws_file)
        assert len(state.claimed) == 1

    def test_parses_completed_count(self, ws_file: Path):
        state = parse_work_stream(ws_file)
        assert len(state.completed) == 1

    def test_backlog_item_fields(self, ws_file: Path):
        state = parse_work_stream(ws_file)
        alpha = next(i for i in state.backlog if i.id == "task-alpha")
        assert alpha.title == "Do alpha"
        assert alpha.source == "source-a.md"
        assert alpha.priority == "P1"
        assert alpha.depends == "-"
        assert alpha.status == "backlog"

    def test_claimed_item_fields(self, ws_file: Path):
        state = parse_work_stream(ws_file)
        delta = state.claimed[0]
        assert delta.id == "task-delta"
        assert delta.agent == "agent-1"
        assert delta.status == "claimed"

    def test_completed_item_fields(self, ws_file: Path):
        state = parse_work_stream(ws_file)
        zeta = state.completed[0]
        assert zeta.id == "task-zeta"
        assert zeta.notes == "Done"

    def test_empty_sections(self, empty_ws_file: Path):
        state = parse_work_stream(empty_ws_file)
        assert state.backlog == []
        assert state.claimed == []
        assert state.completed == []


# ---------------------------------------------------------------------------
# get_next_items
# ---------------------------------------------------------------------------


class TestGetNextItems:
    """Tests for get_next_items()."""

    def test_returns_unclaimed_only(self, ws_file: Path):
        """task-delta is claimed; must not appear in results."""
        items = get_next_items(n=10, min_priority="P4", path=ws_file)
        ids = [i.id for i in items]
        assert "task-delta" not in ids

    def test_respects_min_priority(self, ws_file: Path):
        """With min_priority='P2', P3 items are excluded."""
        items = get_next_items(n=10, min_priority="P2", path=ws_file)
        for item in items:
            assert item.priority_key() <= 2  # P0, P1, P2 only

    def test_dependency_blocking(self, ws_file: Path):
        """task-beta depends on task-alpha which is not completed -> blocked."""
        items = get_next_items(n=10, min_priority="P4", path=ws_file)
        ids = [i.id for i in items]
        assert "task-beta" not in ids

    def test_n_limit(self, ws_file: Path):
        items = get_next_items(n=1, min_priority="P4", path=ws_file)
        assert len(items) <= 1

    def test_sorted_by_priority(self, ws_file: Path):
        """Results must be sorted highest-priority-first."""
        items = get_next_items(n=10, min_priority="P4", path=ws_file)
        keys = [i.priority_key() for i in items]
        assert keys == sorted(keys)

    def test_empty_backlog_returns_empty(self, empty_ws_file: Path):
        items = get_next_items(path=empty_ws_file)
        assert items == []

    def test_dependency_satisfied_when_completed(self, tmp_path: Path):
        """task-beta becomes ready once task-alpha is in COMPLETED."""
        md = textwrap.dedent(
            """\
            ## BACKLOG (not started)

            | ID | Title | Source | Priority | Depends |
            |----|-------|--------|----------|---------|
            | task-beta | Do beta | src.md | P1 | task-alpha |

            ## CLAIMED (in progress — do not pick)

            | ID | Agent | Started | Notes |
            |----|-------|---------|-------|

            ## COMPLETED (this session / recent)
            | ID | Agent | Completed | Notes |
            |----|-------|-----------|-------|
            | task-alpha | agent-0 | 2026-01-01 | done |
            """
        )
        p = tmp_path / "WS.md"
        p.write_text(md, encoding="utf-8")
        items = get_next_items(n=5, path=p)
        assert any(i.id == "task-beta" for i in items)


# ---------------------------------------------------------------------------
# get_blocked_items
# ---------------------------------------------------------------------------


class TestGetBlockedItems:
    """Tests for get_blocked_items()."""

    def test_returns_blocked_item(self, ws_file: Path):
        """task-beta depends on task-alpha (not completed) -> blocked."""
        blocked = get_blocked_items(path=ws_file)
        ids = [i.id for i in blocked]
        assert "task-beta" in ids

    def test_no_deps_not_blocked(self, ws_file: Path):
        """task-alpha has no deps -> not blocked."""
        blocked = get_blocked_items(path=ws_file)
        ids = [i.id for i in blocked]
        assert "task-alpha" not in ids

    def test_empty_backlog_no_blocked(self, empty_ws_file: Path):
        assert get_blocked_items(path=empty_ws_file) == []


# ---------------------------------------------------------------------------
# claim_item
# ---------------------------------------------------------------------------


class TestClaimItem:
    """Tests for claim_item()."""

    def test_claim_existing_item(self, ws_file: Path):
        result = claim_item("task-alpha", "test-agent", path=ws_file)
        assert result is True

    def test_claim_appears_in_claimed(self, ws_file: Path):
        claim_item("task-alpha", "test-agent", path=ws_file)
        state = parse_work_stream(ws_file)
        ids = [i.id for i in state.claimed]
        assert "task-alpha" in ids

    def test_claim_nonexistent_item(self, ws_file: Path):
        result = claim_item("no-such-item", "agent-x", path=ws_file)
        assert result is False

    def test_claim_already_claimed_item(self, ws_file: Path):
        """task-delta is already claimed -> return False."""
        result = claim_item("task-delta", "agent-2", path=ws_file)
        assert result is False

    def test_claim_missing_file(self, tmp_path: Path):
        result = claim_item("x", "a", path=tmp_path / "missing.md")
        assert result is False

    def test_claim_idempotent_check(self, ws_file: Path):
        """Claiming again after first claim returns False."""
        claim_item("task-alpha", "agent-1", path=ws_file)
        second = claim_item("task-alpha", "agent-2", path=ws_file)
        assert second is False


# ---------------------------------------------------------------------------
# complete_item
# ---------------------------------------------------------------------------


class TestCompleteItem:
    """Tests for complete_item()."""

    def test_complete_claimed_item(self, ws_file: Path):
        result = complete_item("task-delta", "agent-1", notes="finished", path=ws_file)
        assert result is True

    def test_complete_appears_in_completed(self, ws_file: Path):
        complete_item("task-delta", "agent-1", path=ws_file)
        state = parse_work_stream(ws_file)
        ids = [i.id for i in state.completed]
        assert "task-delta" in ids

    def test_complete_removes_from_claimed(self, ws_file: Path):
        complete_item("task-delta", "agent-1", path=ws_file)
        state = parse_work_stream(ws_file)
        ids = [i.id for i in state.claimed]
        assert "task-delta" not in ids

    def test_complete_backlog_item_directly(self, ws_file: Path):
        """Items in backlog (not claimed) can also be completed directly."""
        result = complete_item("task-alpha", "agent-x", path=ws_file)
        assert result is True
        state = parse_work_stream(ws_file)
        assert any(i.id == "task-alpha" for i in state.completed)

    def test_complete_nonexistent_item(self, ws_file: Path):
        result = complete_item("ghost", "agent", path=ws_file)
        assert result is False

    def test_complete_missing_file(self, tmp_path: Path):
        result = complete_item("x", "a", path=tmp_path / "missing.md")
        assert result is False

    def test_complete_notes_stored(self, ws_file: Path):
        complete_item("task-delta", "agent-1", notes="great success", path=ws_file)
        raw = ws_file.read_text()
        assert "great success" in raw


# ---------------------------------------------------------------------------
# add_backlog_item
# ---------------------------------------------------------------------------


class TestAddBacklogItem:
    """Tests for add_backlog_item()."""

    def test_add_new_item(self, ws_file: Path):
        new_item = WorkStreamItem(id="task-new", title="New Task", priority="P2")
        result = add_backlog_item(new_item, path=ws_file)
        assert result is True

    def test_added_item_appears_in_backlog(self, ws_file: Path):
        new_item = WorkStreamItem(id="task-new", title="New Task", priority="P2")
        add_backlog_item(new_item, path=ws_file)
        state = parse_work_stream(ws_file)
        ids = [i.id for i in state.backlog]
        assert "task-new" in ids

    def test_duplicate_item_rejected(self, ws_file: Path):
        """Adding an item that already exists returns False."""
        dup = WorkStreamItem(id="task-alpha", title="Dup", priority="P1")
        result = add_backlog_item(dup, path=ws_file)
        assert result is False

    def test_add_to_missing_file(self, tmp_path: Path):
        item = WorkStreamItem(id="x", title="X")
        result = add_backlog_item(item, path=tmp_path / "missing.md")
        assert result is False

    def test_add_preserves_existing_items(self, ws_file: Path):
        new_item = WorkStreamItem(id="task-new", title="New", priority="P1")
        add_backlog_item(new_item, path=ws_file)
        state = parse_work_stream(ws_file)
        existing_ids = {i.id for i in state.backlog}
        assert "task-alpha" in existing_ids
        assert "task-beta" in existing_ids
        assert "task-gamma" in existing_ids

    def test_add_item_with_dependency(self, ws_file: Path):
        new_item = WorkStreamItem(id="task-dep", title="Dep Task", priority="P2", depends="task-alpha")
        add_backlog_item(new_item, path=ws_file)
        state = parse_work_stream(ws_file)
        added = next(i for i in state.backlog if i.id == "task-dep")
        assert added.dependency_ids() == ["task-alpha"]
