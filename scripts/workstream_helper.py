#!/usr/bin/env python3
"""
Work Stream Helper

Structured, programmatic access to WORK_STREAM.md so agents never
have to manually parse markdown tables.

Public API
----------
- WorkStreamItem       – dataclass for a single item
- WorkStreamState      – dataclass holding all three sections
- parse_work_stream()  – parse file into WorkStreamState
- get_next_items()     – unblocked, unclaimed items (ready to work)
- claim_item()         – atomically add to CLAIMED
- complete_item()      – atomically move to COMPLETED
- add_backlog_item()   – append to BACKLOG
- get_blocked_items()  – items whose dependencies are not yet met
"""

from __future__ import annotations

import fcntl
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import IO

# ---------------------------------------------------------------------------
# Default path – override via parse_work_stream(path=...)
# ---------------------------------------------------------------------------
DEFAULT_WORK_STREAM_PATH = Path(__file__).parent.parent / "docs" / "reference" / "WORK_STREAM.md"

# Priority order (lower index = higher priority)
_PRIORITY_ORDER = ["P0", "P1", "P2", "P3", "P4"]


def _priority_key(p: str) -> int:
    """Return sort key for a priority string (unknown → appended at end)."""
    try:
        return _PRIORITY_ORDER.index(p)
    except ValueError:
        return len(_PRIORITY_ORDER)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class WorkStreamItem:
    """A single item from the work stream.

    Attributes
    ----------
    id:       Unique slug identifier (e.g. ``swarm-fix-macos-sampling``).
    title:    Human-readable description.
    source:   Origin document.
    priority: Priority string such as ``P1``.
    depends:  Raw dependency string; ``"-"`` or ``""`` means none.
    status:   One of ``"backlog"``, ``"claimed"``, ``"completed"``.
    agent:    Agent ID that claimed/completed this item (CLAIMED / COMPLETED only).
    timestamp: ISO-8601 string for when the item was claimed/completed.
    notes:    Free-form notes (COMPLETED only).
    """

    id: str
    title: str
    source: str = ""
    priority: str = "P2"
    depends: str = "-"
    status: str = "backlog"
    agent: str = ""
    timestamp: str = ""
    notes: str = ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def dependency_ids(self) -> list[str]:
        """Return a list of dependency IDs, empty when there are none."""
        raw = self.depends.strip()
        if not raw or raw in {"-", "—", "✅ Complete"}:
            return []
        return [d.strip() for d in raw.split(",") if d.strip()]

    def priority_key(self) -> int:
        """Integer sort key for this item's priority."""
        return _priority_key(self.priority)


@dataclass
class WorkStreamState:
    """Parsed representation of all three WORK_STREAM.md sections."""

    backlog: list[WorkStreamItem] = field(default_factory=list)
    claimed: list[WorkStreamItem] = field(default_factory=list)
    completed: list[WorkStreamItem] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def claimed_ids(self) -> set[str]:
        return {item.id for item in self.claimed}

    def completed_ids(self) -> set[str]:
        return {item.id for item in self.completed}

    def all_items(self) -> list[WorkStreamItem]:
        return self.backlog + self.claimed + self.completed

    def find_by_id(self, item_id: str) -> WorkStreamItem | None:
        for item in self.all_items():
            if item.id == item_id:
                return item
        return None


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_work_stream(
    path: Path | str | None = None,
) -> WorkStreamState:
    """Parse WORK_STREAM.md into a :class:`WorkStreamState`.

    Parameters
    ----------
    path:
        Optional path override.  Defaults to :data:`DEFAULT_WORK_STREAM_PATH`.

    Returns
    -------
    WorkStreamState
        Parsed state; empty lists when the file does not exist.
    """
    ws_path = Path(path) if path else DEFAULT_WORK_STREAM_PATH
    if not ws_path.exists():
        return WorkStreamState()

    content = ws_path.read_text(encoding="utf-8")
    return _parse_content(content)


def _parse_content(content: str) -> WorkStreamState:
    """Parse raw markdown content into WorkStreamState."""
    state = WorkStreamState()
    current_section: str | None = None

    for line in content.splitlines():
        stripped = line.strip()

        # Section headers
        if re.match(r"^##\s+BACKLOG", stripped):
            current_section = "backlog"
            continue
        if re.match(r"^##\s+CLAIMED", stripped):
            current_section = "claimed"
            continue
        if re.match(r"^##\s+COMPLETED", stripped):
            current_section = "completed"
            continue

        # Table rows only
        if not stripped.startswith("|") or current_section is None:
            continue

        # Skip header row and separator rows
        # split("|") on "| a | b |  | d |" produces ['', ' a ', ' b ', '  ', ' d ', '']
        # Strip each cell, then drop only the leading/trailing empty boundary
        # cells introduced by the outer pipes, preserving empty interior cells.
        raw_cols = [c.strip() for c in stripped.split("|")]
        # Drop first and last boundary empties only
        if raw_cols and raw_cols[0] == "":
            raw_cols = raw_cols[1:]
        if raw_cols and raw_cols[-1] == "":
            raw_cols = raw_cols[:-1]
        cols = raw_cols

        if not cols:
            continue
        if cols[0].upper() in {"ID", "----", "---"}:
            continue
        if all(re.match(r"^-+$", c) for c in cols):
            continue

        item = _parse_row(cols, current_section)
        if item is None:
            continue

        if current_section == "backlog":
            state.backlog.append(item)
        elif current_section == "claimed":
            state.claimed.append(item)
        elif current_section == "completed":
            state.completed.append(item)

    return state


def _parse_row(cols: list[str], section: str) -> WorkStreamItem | None:
    """Convert parsed table columns into a WorkStreamItem."""
    if not cols or not cols[0]:
        return None

    item_id = cols[0]

    if section == "backlog":
        # | ID | Title | Source | Priority | Depends |
        return WorkStreamItem(
            id=item_id,
            title=cols[1] if len(cols) > 1 else "",
            source=cols[2] if len(cols) > 2 else "",
            priority=cols[3] if len(cols) > 3 else "P2",
            depends=cols[4] if len(cols) > 4 else "-",
            status="backlog",
        )

    if section == "claimed":
        # | ID | Agent | Started | Notes |
        return WorkStreamItem(
            id=item_id,
            title="",
            agent=cols[1] if len(cols) > 1 else "",
            timestamp=cols[2] if len(cols) > 2 else "",
            notes=cols[3] if len(cols) > 3 else "",
            status="claimed",
        )

    if section == "completed":
        # | ID | Agent | Completed | Notes |
        return WorkStreamItem(
            id=item_id,
            title="",
            agent=cols[1] if len(cols) > 1 else "",
            timestamp=cols[2] if len(cols) > 2 else "",
            notes=cols[3] if len(cols) > 3 else "",
            status="completed",
        )

    return None


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


def get_next_items(
    n: int = 5,
    min_priority: str = "P2",
    path: Path | str | None = None,
) -> list[WorkStreamItem]:
    """Return up to *n* unblocked, unclaimed backlog items.

    Items are sorted by priority (P0 first) then by their position in the
    file so that the order is stable.

    Parameters
    ----------
    n:
        Maximum number of items to return.
    min_priority:
        Include items with this priority or higher.  ``"P2"`` includes P0,
        P1, and P2 but excludes P3 and P4.
    path:
        Optional path override.

    Returns
    -------
    list[WorkStreamItem]
        Ready-to-work items sorted by priority.
    """
    state = parse_work_stream(path)
    claimed_ids = state.claimed_ids()
    completed_ids = state.completed_ids()
    max_pri_key = _priority_key(min_priority)

    ready: list[WorkStreamItem] = []
    for item in state.backlog:
        if item.id in claimed_ids:
            continue
        if item.priority_key() > max_pri_key:
            continue
        dep_ids = item.dependency_ids()
        if dep_ids and not all(d in completed_ids for d in dep_ids):
            continue
        ready.append(item)

    ready.sort(key=lambda x: x.priority_key())
    return ready[:n]


def get_blocked_items(
    path: Path | str | None = None,
) -> list[WorkStreamItem]:
    """Return backlog items whose dependencies have not yet been completed.

    Parameters
    ----------
    path:
        Optional path override.

    Returns
    -------
    list[WorkStreamItem]
        Blocked items.
    """
    state = parse_work_stream(path)
    completed_ids = state.completed_ids()

    blocked: list[WorkStreamItem] = []
    for item in state.backlog:
        dep_ids = item.dependency_ids()
        if dep_ids and not all(d in completed_ids for d in dep_ids):
            blocked.append(item)

    return blocked


# ---------------------------------------------------------------------------
# Mutation helpers (atomic via file locking)
# ---------------------------------------------------------------------------


def claim_item(
    item_id: str,
    agent_id: str,
    path: Path | str | None = None,
) -> bool:
    """Add *item_id* to the CLAIMED section atomically.

    Parameters
    ----------
    item_id:
        The ID of the backlog item to claim.
    agent_id:
        Unique agent identifier (e.g. ``"agent-1"``).
    path:
        Optional path override.

    Returns
    -------
    bool
        ``True`` on success; ``False`` when the item does not exist in the
        backlog, is already claimed, or the file cannot be written.
    """
    ws_path = Path(path) if path else DEFAULT_WORK_STREAM_PATH
    if not ws_path.exists():
        return False

    with _locked_open(ws_path) as fh:
        content = fh.read()
        state = _parse_content(content)

        # Validate: must exist in backlog and not already claimed/completed
        if not any(item.id == item_id for item in state.backlog):
            return False
        if item_id in state.claimed_ids():
            return False

        ts = datetime.now(tz=UTC).isoformat()
        new_row = f"| {item_id} | {agent_id} | {ts} |  |\n"
        content = _insert_into_claimed(content, new_row)

        fh.seek(0)
        fh.write(content)
        fh.truncate()

    return True


def complete_item(
    item_id: str,
    agent_id: str,
    notes: str = "",
    path: Path | str | None = None,
) -> bool:
    """Move *item_id* from CLAIMED (or BACKLOG) to COMPLETED atomically.

    Parameters
    ----------
    item_id:
        The ID of the item to complete.
    agent_id:
        Agent performing the completion.
    notes:
        Optional free-form notes appended to the COMPLETED row.
    path:
        Optional path override.

    Returns
    -------
    bool
        ``True`` on success; ``False`` when the item is not found or the
        file cannot be written.
    """
    ws_path = Path(path) if path else DEFAULT_WORK_STREAM_PATH
    if not ws_path.exists():
        return False

    with _locked_open(ws_path) as fh:
        content = fh.read()
        state = _parse_content(content)

        all_ids = {i.id for i in state.all_items()}
        if item_id not in all_ids:
            return False

        # Remove from backlog and claimed
        content = _remove_item_row(content, item_id)

        ts = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        safe_notes = notes.replace("|", " ") if notes else ""
        new_row = f"| {item_id} | {agent_id} | {ts} | {safe_notes} |\n"
        content = _insert_into_completed(content, new_row)

        fh.seek(0)
        fh.write(content)
        fh.truncate()

    return True


def add_backlog_item(
    item: WorkStreamItem,
    path: Path | str | None = None,
) -> bool:
    """Append *item* to the BACKLOG section.

    Parameters
    ----------
    item:
        The :class:`WorkStreamItem` to append.  Only ``id``, ``title``,
        ``source``, ``priority``, and ``depends`` are used.
    path:
        Optional path override.

    Returns
    -------
    bool
        ``True`` on success; ``False`` when the file does not exist or an
        item with the same ID already exists.
    """
    ws_path = Path(path) if path else DEFAULT_WORK_STREAM_PATH
    if not ws_path.exists():
        return False

    with _locked_open(ws_path) as fh:
        content = fh.read()
        state = _parse_content(content)

        if any(i.id == item.id for i in state.all_items()):
            return False  # duplicate

        depends = item.depends or "-"
        new_row = f"| {item.id} | {item.title} | {item.source} | {item.priority} | {depends} |\n"
        content = _insert_into_backlog(content, new_row)

        fh.seek(0)
        fh.write(content)
        fh.truncate()

    return True


# ---------------------------------------------------------------------------
# Internal: file manipulation helpers
# ---------------------------------------------------------------------------


def _locked_open(path: Path):
    """Context manager: open *path* for read+write with an exclusive lock."""

    class _Ctx:
        def __init__(self, p: Path) -> None:
            self._p = p
            self._fh: IO[str] | None = None

        def __enter__(self) -> IO[str]:
            self._fh = open(self._p, "r+", encoding="utf-8")  # noqa: SIM115
            fcntl.flock(self._fh, fcntl.LOCK_EX)
            return self._fh

        def __exit__(self, *_: object) -> None:
            if self._fh:
                fcntl.flock(self._fh, fcntl.LOCK_UN)
                self._fh.close()

    return _Ctx(path)


# Section anchor patterns
_BACKLOG_ANCHOR = re.compile(r"(^## BACKLOG\b.*$)", re.MULTILINE)
_CLAIMED_ANCHOR = re.compile(r"(^## CLAIMED\b.*$)", re.MULTILINE)
_COMPLETED_ANCHOR = re.compile(r"(^## COMPLETED\b.*$)", re.MULTILINE)

# Match the last table row inside a section (used to find insertion point)
_TABLE_ROW = re.compile(r"^\|[^|].*\|[ \t]*$", re.MULTILINE)


def _find_section_table_end(content: str, section_pattern: re.Pattern) -> int:
    """Return the index just after the last table row in *section_pattern*'s block.

    If no table rows exist, return the position right after the section header
    line (so the new row is inserted as the first row).
    """
    m_section = section_pattern.search(content)
    if not m_section:
        return len(content)

    section_start = m_section.end()

    # Find the next section header to limit search scope
    next_section = re.search(r"^## ", content[section_start:], re.MULTILINE)
    section_end = section_start + next_section.start() if next_section else len(content)
    block = content[section_start:section_end]

    # Collect all table rows in this block
    rows = list(_TABLE_ROW.finditer(block))
    if rows:
        last_row = rows[-1]
        return section_start + last_row.end() + 1  # +1 to include the newline

    # No rows yet – insert right after the header line (skip blank line)
    return section_start + 1


def _insert_into_backlog(content: str, new_row: str) -> str:
    insert_at = _find_section_table_end(content, _BACKLOG_ANCHOR)
    return content[:insert_at] + new_row + content[insert_at:]


def _insert_into_claimed(content: str, new_row: str) -> str:
    insert_at = _find_section_table_end(content, _CLAIMED_ANCHOR)
    return content[:insert_at] + new_row + content[insert_at:]


def _insert_into_completed(content: str, new_row: str) -> str:
    insert_at = _find_section_table_end(content, _COMPLETED_ANCHOR)
    return content[:insert_at] + new_row + content[insert_at:]


def _remove_item_row(content: str, item_id: str) -> str:
    """Remove the table row whose first column is *item_id* (all occurrences)."""
    escaped = re.escape(item_id)
    pattern = re.compile(rf"^\| ?{escaped} ?\|[^\n]*\n?", re.MULTILINE)
    return pattern.sub("", content)


# ---------------------------------------------------------------------------
# CLI entry-point (convenience)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "next"

    if cmd == "next":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        items = get_next_items(n=n)
        print(json.dumps([vars(i) for i in items], indent=2))
    elif cmd == "blocked":
        items = get_blocked_items()
        print(json.dumps([vars(i) for i in items], indent=2))
    elif cmd == "parse":
        state = parse_work_stream()
        print(
            json.dumps(
                {
                    "backlog": len(state.backlog),
                    "claimed": len(state.claimed),
                    "completed": len(state.completed),
                }
            )
        )
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
