"""Tests for WL-163: GitHub Pull Reflection Audit Trail.

# @trace WL-163
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import orjson as json
import pytest

from thegent.integrations.gh_pull_audit import (
    PullReflectionAuditEntry,
    PullReflectionAuditLog,
)


@pytest.mark.requirement("WL-163")
def test_pull_reflection_audit_entry_creation() -> None:
    """Test creating a PullReflectionAuditEntry."""
    entry = PullReflectionAuditEntry(
        wl_id="WL-001",
        cycle_id="cycle-2026-02-22-001",
        connector="github",
        before_status="open",
        after_status="closed",
        timestamp=datetime.now(UTC).isoformat(),
        sync_note="Synced from GitHub",
    )

    assert entry.wl_id == "WL-001"
    assert entry.cycle_id == "cycle-2026-02-22-001"
    assert entry.connector == "github"
    assert entry.before_status == "open"
    assert entry.after_status == "closed"
    assert entry.sync_note == "Synced from GitHub"


@pytest.mark.requirement("WL-163")
def test_pull_reflection_audit_entry_to_dict() -> None:
    """Test converting PullReflectionAuditEntry to dictionary."""
    now = datetime.now(UTC).isoformat()
    entry = PullReflectionAuditEntry(
        wl_id="WL-002",
        cycle_id="cycle-123",
        connector="linear",
        before_status="todo",
        after_status="in_progress",
        timestamp=now,
        sync_note="Priority updated",
    )

    entry_dict = entry.to_dict()

    assert entry_dict["wl_id"] == "WL-002"
    assert entry_dict["cycle_id"] == "cycle-123"
    assert entry_dict["connector"] == "linear"
    assert entry_dict["before_status"] == "todo"
    assert entry_dict["after_status"] == "in_progress"
    assert entry_dict["timestamp"] == now
    assert entry_dict["sync_note"] == "Priority updated"


@pytest.mark.requirement("WL-163")
def test_pull_reflection_audit_entry_to_json_line() -> None:
    """Test converting PullReflectionAuditEntry to JSONL format."""
    now = datetime.now(UTC).isoformat()
    entry = PullReflectionAuditEntry(
        wl_id="WL-003",
        cycle_id="cycle-456",
        connector="github",
        before_status="draft",
        after_status="ready_for_review",
        timestamp=now,
    )

    json_line = entry.to_json_line()

    # Should be valid JSON on a single line
    parsed = json.loads(json_line)
    assert parsed["wl_id"] == "WL-003"
    assert parsed["cycle_id"] == "cycle-456"
    assert "\n" not in json_line


@pytest.mark.requirement("WL-163")
def test_pull_reflection_audit_log_append_and_read_all(tmp_path: Path) -> None:
    """Test appending entries and reading all from audit log."""
    log_path = tmp_path / "audit.jsonl"
    log = PullReflectionAuditLog(log_path)

    # Create and append entries
    entry1 = PullReflectionAuditEntry(
        wl_id="WL-001",
        cycle_id="cycle-1",
        connector="github",
        before_status="open",
        after_status="closed",
        timestamp=datetime.now(UTC).isoformat(),
    )
    entry2 = PullReflectionAuditEntry(
        wl_id="WL-002",
        cycle_id="cycle-1",
        connector="linear",
        before_status="todo",
        after_status="done",
        timestamp=datetime.now(UTC).isoformat(),
    )

    log.append(entry1)
    log.append(entry2)

    # Read all entries
    all_entries = log.read_all()

    assert len(all_entries) == 2
    assert all_entries[0].wl_id == "WL-001"
    assert all_entries[1].wl_id == "WL-002"
    assert all_entries[0].connector == "github"
    assert all_entries[1].connector == "linear"


@pytest.mark.requirement("WL-163")
def test_pull_reflection_audit_log_read_by_cycle(tmp_path: Path) -> None:
    """Test reading audit entries filtered by cycle ID."""
    log_path = tmp_path / "audit.jsonl"
    log = PullReflectionAuditLog(log_path)

    # Create entries for multiple cycles
    entry1 = PullReflectionAuditEntry(
        wl_id="WL-001",
        cycle_id="cycle-1",
        connector="github",
        before_status="open",
        after_status="closed",
        timestamp=datetime.now(UTC).isoformat(),
    )
    entry2 = PullReflectionAuditEntry(
        wl_id="WL-002",
        cycle_id="cycle-2",
        connector="linear",
        before_status="todo",
        after_status="done",
        timestamp=datetime.now(UTC).isoformat(),
    )
    entry3 = PullReflectionAuditEntry(
        wl_id="WL-003",
        cycle_id="cycle-1",
        connector="github",
        before_status="draft",
        after_status="ready",
        timestamp=datetime.now(UTC).isoformat(),
    )

    log.append(entry1)
    log.append(entry2)
    log.append(entry3)

    # Read entries for cycle-1
    cycle1_entries = log.read_by_cycle("cycle-1")

    assert len(cycle1_entries) == 2
    assert all(e.cycle_id == "cycle-1" for e in cycle1_entries)
    assert cycle1_entries[0].wl_id == "WL-001"
    assert cycle1_entries[1].wl_id == "WL-003"

    # Read entries for cycle-2
    cycle2_entries = log.read_by_cycle("cycle-2")

    assert len(cycle2_entries) == 1
    assert cycle2_entries[0].wl_id == "WL-002"


@pytest.mark.requirement("WL-163")
def test_pull_reflection_audit_log_read_all_empty(tmp_path: Path) -> None:
    """Test reading from non-existent log file returns empty list."""
    log_path = tmp_path / "nonexistent.jsonl"
    log = PullReflectionAuditLog(log_path)

    all_entries = log.read_all()

    assert all_entries == []


@pytest.mark.requirement("WL-163")
def test_pull_reflection_audit_log_clear(tmp_path: Path) -> None:
    """Test clearing the audit log."""
    log_path = tmp_path / "audit.jsonl"
    log = PullReflectionAuditLog(log_path)

    # Add an entry
    entry = PullReflectionAuditEntry(
        wl_id="WL-001",
        cycle_id="cycle-1",
        connector="github",
        before_status="open",
        after_status="closed",
        timestamp=datetime.now(UTC).isoformat(),
    )
    log.append(entry)

    # Verify it was added
    assert len(log.read_all()) == 1
    assert log_path.exists()

    # Clear the log
    log.clear()

    # Verify it's empty
    assert len(log.read_all()) == 0
    assert not log_path.exists()
