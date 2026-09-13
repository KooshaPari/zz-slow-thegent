"""Unit tests for BacklogManager and BacklogItem models.

Traces to: FR-GOV-001 (governance backlog management)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import orjson as json

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from thegent.governance.backlog import (
    BacklogItem,
    BacklogManager,
    BacklogStatus,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def session_dir(tmp_path: Path) -> Path:
    """Return a temporary session directory for backlog storage.

    Traces to: FR-GOV-001
    """
    return tmp_path / "session_001"


@pytest.fixture
def backlog(session_dir: Path) -> BacklogManager:
    """Return a BacklogManager instance with a temporary session dir.

    Traces to: FR-GOV-001
    """
    return BacklogManager(session_dir)


# ---------------------------------------------------------------------------
# BacklogItem Model Tests
# ---------------------------------------------------------------------------


def test_backlog_item_model_fields() -> None:
    """BacklogItem accepts valid data and generates defaults.

    Traces to: FR-GOV-001
    """
    item = BacklogItem(
        finding_id="FIND-001",
        dimension="test_coverage",
        severity=8.5,
        description="Coverage below target",
    )
    assert item.item_id is not None
    assert item.finding_id == "FIND-001"
    assert item.dimension == "test_coverage"
    assert item.severity == 8.5
    assert item.description == "Coverage below target"
    assert item.attempts == 0
    assert item.status == BacklogStatus.PENDING
    assert item.created_at is not None
    assert item.deferred_reason is None


def test_backlog_item_custom_item_id() -> None:
    """BacklogItem accepts custom item_id.

    Traces to: FR-GOV-001
    """
    item = BacklogItem(
        item_id="custom-id-123",
        finding_id="FIND-002",
        dimension="lint_violations",
        severity=5.0,
        description="Too many lint violations",
    )
    assert item.item_id == "custom-id-123"


def test_backlog_item_all_fields_populated() -> None:
    """BacklogItem can have all optional fields populated.

    Traces to: FR-GOV-001
    """
    item = BacklogItem(
        finding_id="FIND-003",
        dimension="complexity",
        severity=5.0,
        description="High complexity",
        attempts=3,
        last_attempted_at="2026-01-15T10:30:00Z",
        status=BacklogStatus.IN_PROGRESS,
        deferred_reason="Waiting for resources",
    )
    assert item.attempts == 3
    assert item.last_attempted_at == "2026-01-15T10:30:00Z"
    assert item.status == BacklogStatus.IN_PROGRESS
    assert item.deferred_reason == "Waiting for resources"


def test_backlog_status_enum_values() -> None:
    """BacklogStatus enum members have expected string values.

    Traces to: FR-GOV-001
    """
    assert BacklogStatus.PENDING == "pending"
    assert BacklogStatus.IN_PROGRESS == "in_progress"
    assert BacklogStatus.RESOLVED == "resolved"
    assert BacklogStatus.DEFERRED == "deferred"


# ---------------------------------------------------------------------------
# BacklogManager Initialization
# ---------------------------------------------------------------------------


def test_backlog_manager_initialization(backlog: BacklogManager) -> None:
    """BacklogManager initializes and creates directory structure.

    Traces to: FR-GOV-001
    """
    assert backlog.session_dir.name == "session_001"
    assert backlog.backlog_path.parent.exists()
    assert backlog.backlog_path.parent.name == "agileplus"


def test_backlog_path_property(backlog: BacklogManager) -> None:
    """backlog_path property returns correct path.

    Traces to: FR-GOV-001
    """
    expected = backlog.session_dir / "agileplus" / "backlog.jsonl"
    assert backlog.backlog_path == expected


def test_empty_backlog_file_creation(backlog: BacklogManager) -> None:
    """BacklogManager creates backlog.jsonl on first write.

    Traces to: FR-GOV-001
    """
    # File doesn't exist yet
    assert not backlog.backlog_path.exists()
    # Add an item triggers file creation
    backlog.add("FIND-001", "test_coverage", 7.0, "Coverage issue")
    assert backlog.backlog_path.exists()


# ---------------------------------------------------------------------------
# add() Method Tests
# ---------------------------------------------------------------------------


def test_add_single_item(backlog: BacklogManager) -> None:
    """add() creates a new pending backlog item.

    Traces to: FR-GOV-001
    """
    item = backlog.add(
        finding_id="FIND-101",
        dimension="test_coverage",
        severity=8.0,
        description="Coverage below 80%",
    )
    assert item.finding_id == "FIND-101"
    assert item.dimension == "test_coverage"
    assert item.severity == 8.0
    assert item.status == BacklogStatus.PENDING
    assert item.attempts == 0


def test_add_multiple_items(backlog: BacklogManager) -> None:
    """add() appends items to the JSONL file.

    Traces to: FR-GOV-001
    """
    backlog.add("FIND-102", "lint_violations", 5.0, "Too many violations")
    backlog.add("FIND-103", "complexity_index", 3.0, "High complexity")
    items = backlog.get_all()
    assert len(items) == 2
    assert items[0].finding_id == "FIND-102"
    assert items[1].finding_id == "FIND-103"


def test_add_item_persists_to_file(backlog: BacklogManager) -> None:
    """add() writes item to JSONL file.

    Traces to: FR-GOV-001
    """
    backlog.add("FIND-104", "security_findings", 9.0, "Security issue")
    # Read raw JSONL
    lines = backlog.backlog_path.read_text().strip().split("\n")
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["finding_id"] == "FIND-104"


# ---------------------------------------------------------------------------
# get_pending() Method Tests
# ---------------------------------------------------------------------------


def test_get_pending_empty(backlog: BacklogManager) -> None:
    """get_pending() returns empty list when no items exist.

    Traces to: FR-GOV-001
    """
    assert backlog.get_pending() == []


def test_get_pending_returns_only_pending(backlog: BacklogManager) -> None:
    """get_pending() filters out resolved and deferred items.

    Traces to: FR-GOV-001
    """
    item1 = backlog.add("FIND-201", "test_coverage", 8.0, "Issue 1")
    item2 = backlog.add("FIND-202", "lint_violations", 6.0, "Issue 2")
    backlog.add("FIND-203", "complexity", 7.0, "Issue 3")
    # Resolve one, defer another
    backlog.resolve(item1.item_id)
    backlog.defer(item2.item_id, "Low priority")
    pending = backlog.get_pending()
    assert len(pending) == 1
    assert pending[0].finding_id == "FIND-203"


def test_get_pending_sorted_by_severity_desc(backlog: BacklogManager) -> None:
    """get_pending() sorts by severity descending, then attempts ascending.

    Traces to: FR-GOV-001
    """
    backlog.add("FIND-204", "dimension1", 3.0, "Low severity")
    backlog.add("FIND-205", "dimension2", 8.0, "High severity")
    backlog.add("FIND-206", "dimension3", 5.0, "Medium severity")
    pending = backlog.get_pending()
    assert len(pending) == 3
    assert pending[0].finding_id == "FIND-205"  # 8.0
    assert pending[1].finding_id == "FIND-206"  # 5.0
    assert pending[2].finding_id == "FIND-204"  # 3.0


def test_get_pending_sorted_by_attempts_when_same_severity(backlog: BacklogManager) -> None:
    """get_pending() sorts by attempts ascending when severity is equal.

    Traces to: FR-GOV-001
    """
    item1 = backlog.add("FIND-207", "dimension1", 5.0, "First")
    _ = backlog.add("FIND-208", "dimension2", 5.0, "Second")
    # Increment attempt on first item
    backlog.increment_attempt(item1.item_id)
    pending = backlog.get_pending()
    assert pending[0].finding_id == "FIND-208"  # Fewer attempts
    assert pending[1].finding_id == "FIND-207"  # More attempts


# ---------------------------------------------------------------------------
# update_status() Method Tests
# ---------------------------------------------------------------------------


def test_update_status_pending_to_in_progress(backlog: BacklogManager) -> None:
    """update_status() changes status from PENDING to IN_PROGRESS.

    Traces to: FR-GOV-001
    """
    item = backlog.add("FIND-301", "test_coverage", 7.0, "Issue")
    backlog.update_status(item.item_id, BacklogStatus.IN_PROGRESS)
    # Reload from file
    items = backlog.get_all()
    assert items[0].status == BacklogStatus.IN_PROGRESS


def test_update_status_with_deferred_reason(backlog: BacklogManager) -> None:
    """update_status() stores deferred reason when provided.

    Traces to: FR-GOV-001
    """
    item = backlog.add("FIND-302", "lint_violations", 5.0, "Issue")
    backlog.update_status(item.item_id, BacklogStatus.DEFERRED, reason="Low priority")
    items = backlog.get_all()
    assert items[0].status == BacklogStatus.DEFERRED
    assert items[0].deferred_reason == "Low priority"


def test_update_status_invalid_item_raises(backlog: BacklogManager) -> None:
    """update_status() raises ValueError for non-existent item_id.

    Traces to: FR-GOV-001
    """
    with pytest.raises(ValueError, match="not found"):
        backlog.update_status("nonexistent-id", BacklogStatus.RESOLVED)


# ---------------------------------------------------------------------------
# increment_attempt() Method Tests
# ---------------------------------------------------------------------------


def test_increment_attempt_increments_counter(backlog: BacklogManager) -> None:
    """increment_attempt() increments attempts and updates timestamp.

    Traces to: FR-GOV-001
    """
    item = backlog.add("FIND-401", "test_coverage", 7.0, "Issue")
    assert item.attempts == 0
    backlog.increment_attempt(item.item_id)
    items = backlog.get_all()
    assert items[0].attempts == 1
    assert items[0].last_attempted_at is not None


def test_increment_attempt_multiple_times(backlog: BacklogManager) -> None:
    """increment_attempt() can be called multiple times.

    Traces to: FR-GOV-001
    """
    item = backlog.add("FIND-402", "lint_violations", 5.0, "Issue")
    backlog.increment_attempt(item.item_id)
    backlog.increment_attempt(item.item_id)
    backlog.increment_attempt(item.item_id)
    items = backlog.get_all()
    assert items[0].attempts == 3


def test_increment_attempt_invalid_item_raises(backlog: BacklogManager) -> None:
    """increment_attempt() raises ValueError for non-existent item_id.

    Traces to: FR-GOV-001
    """
    with pytest.raises(ValueError, match="not found"):
        backlog.increment_attempt("nonexistent-id")


# ---------------------------------------------------------------------------
# resolve() Method Tests
# ---------------------------------------------------------------------------


def test_resolve_changes_status_to_resolved(backlog: BacklogManager) -> None:
    """resolve() marks item as RESOLVED.

    Traces to: FR-GOV-001
    """
    item = backlog.add("FIND-501", "test_coverage", 7.0, "Issue")
    backlog.resolve(item.item_id)
    items = backlog.get_all()
    assert items[0].status == BacklogStatus.RESOLVED


def test_resolve_removes_from_pending(backlog: BacklogManager) -> None:
    """resolve() removes item from get_pending() results.

    Traces to: FR-GOV-001
    """
    item = backlog.add("FIND-502", "lint_violations", 5.0, "Issue")
    assert len(backlog.get_pending()) == 1
    backlog.resolve(item.item_id)
    assert backlog.get_pending() == []


def test_resolve_invalid_item_raises(backlog: BacklogManager) -> None:
    """resolve() raises ValueError for non-existent item_id.

    Traces to: FR-GOV-001
    """
    with pytest.raises(ValueError, match="not found"):
        backlog.resolve("nonexistent-id")


# ---------------------------------------------------------------------------
# defer() Method Tests
# ---------------------------------------------------------------------------


def test_defer_changes_status_to_deferred(backlog: BacklogManager) -> None:
    """defer() marks item as DEFERRED with reason.

    Traces to: FR-GOV-001
    """
    item = backlog.add("FIND-601", "test_coverage", 7.0, "Issue")
    backlog.defer(item.item_id, "Resource constraints")
    items = backlog.get_all()
    assert items[0].status == BacklogStatus.DEFERRED
    assert items[0].deferred_reason == "Resource constraints"


def test_defer_removes_from_pending(backlog: BacklogManager) -> None:
    """defer() removes item from get_pending() results.

    Traces to: FR-GOV-001
    """
    item = backlog.add("FIND-602", "complexity", 4.0, "Issue")
    assert len(backlog.get_pending()) == 1
    backlog.defer(item.item_id, "Backlog full")
    assert backlog.get_pending() == []


def test_defer_invalid_item_raises(backlog: BacklogManager) -> None:
    """defer() raises ValueError for non-existent item_id.

    Traces to: FR-GOV-001
    """
    with pytest.raises(ValueError, match="not found"):
        backlog.defer("nonexistent-id", "Any reason")


# ---------------------------------------------------------------------------
# get_all() Method Tests
# ---------------------------------------------------------------------------


def test_get_all_empty(backlog: BacklogManager) -> None:
    """get_all() returns empty list when no items exist.

    Traces to: FR-GOV-001
    """
    assert backlog.get_all() == []


def test_get_all_returns_all_items(backlog: BacklogManager) -> None:
    """get_all() returns all items regardless of status.

    Traces to: FR-GOV-001
    """
    item1 = backlog.add("FIND-701", "test_coverage", 8.0, "Issue 1")
    item2 = backlog.add("FIND-702", "lint_violations", 6.0, "Issue 2")
    backlog.resolve(item1.item_id)
    backlog.defer(item2.item_id, "Deferred")
    all_items = backlog.get_all()
    assert len(all_items) == 2
    statuses = {item.status for item in all_items}
    assert statuses == {BacklogStatus.RESOLVED, BacklogStatus.DEFERRED}


def test_get_all_preserves_audit_trail(backlog: BacklogManager) -> None:
    """get_all() includes resolved items for audit trail.

    Traces to: FR-GOV-001
    """
    item = backlog.add("FIND-703", "security", 9.0, "Critical issue")
    backlog.resolve(item.item_id)
    items = backlog.get_all()
    assert len(items) == 1
    assert items[0].status == BacklogStatus.RESOLVED


# ---------------------------------------------------------------------------
# Edge Cases and Integration Tests
# ---------------------------------------------------------------------------


def test_full_lifecycle(backlog: BacklogManager) -> None:
    """Test complete lifecycle: add -> increment -> resolve.

    Traces to: FR-GOV-001
    """
    # Add item
    item = backlog.add("FIND-801", "test_coverage", 7.0, "Coverage issue")
    item_id = item.item_id

    # Item is pending
    pending = backlog.get_pending()
    assert len(pending) == 1

    # Increment attempts
    backlog.increment_attempt(item_id)
    backlog.increment_attempt(item_id)

    # Resolve
    backlog.resolve(item_id)

    # No longer pending, but in all items
    assert backlog.get_pending() == []
    all_items = backlog.get_all()
    assert len(all_items) == 1
    assert all_items[0].status == BacklogStatus.RESOLVED
    assert all_items[0].attempts == 2


def test_multiple_items_mixed_statuses(backlog: BacklogManager) -> None:
    """Test multiple items with mixed statuses.

    Traces to: FR-GOV-001
    """
    # Add 4 items
    item1 = backlog.add("FIND-901", "dim1", 9.0, "High")
    item2 = backlog.add("FIND-902", "dim2", 7.0, "Med")
    _ = backlog.add("FIND-903", "dim3", 5.0, "Low")
    _ = backlog.add("FIND-904", "dim4", 8.0, "High2")

    # Resolve 1, defer 1, leave 2 pending
    backlog.resolve(item1.item_id)
    backlog.defer(item2.item_id, "Deferred")

    # get_pending returns only the 2 pending items, sorted by severity
    pending = backlog.get_pending()
    assert len(pending) == 2
    assert pending[0].finding_id == "FIND-904"  # 8.0
    assert pending[1].finding_id == "FIND-903"  # 5.0

    # get_all returns all 4
    all_items = backlog.get_all()
    assert len(all_items) == 4


def test_timestamp_updated_on_increment(backlog: BacklogManager) -> None:
    """increment_attempt() updates last_attempted_at timestamp.

    Traces to: FR-GOV-001
    """
    item = backlog.add("FIND-A01", "test_coverage", 7.0, "Issue")
    assert item.last_attempted_at is None
    backlog.increment_attempt(item.item_id)
    items = backlog.get_all()
    assert items[0].last_attempted_at is not None


def test_backlog_item_id_uniqueness(backlog: BacklogManager) -> None:
    """Each backlog item gets a unique item_id.

    Traces to: FR-GOV-001
    """
    items = []
    for i in range(5):
        item = backlog.add(f"FIND-{i}", "dim", 5.0, f"Issue {i}")
        items.append(item)
    ids = [item.item_id for item in items]
    assert len(ids) == len(set(ids))


def test_jsonl_file_format(backlog: BacklogManager) -> None:
    """Backlog stores items as valid JSONL (one JSON object per line).

    Traces to: FR-GOV-001
    """
    backlog.add("FIND-B01", "test_coverage", 8.0, "Issue 1")
    backlog.add("FIND-B02", "lint_violations", 6.0, "Issue 2")

    content = backlog.backlog_path.read_text()
    lines = [line for line in content.strip().split("\n") if line]

    assert len(lines) == 2
    for line in lines:
        # Each line must be valid JSON
        data = json.loads(line)
        assert "item_id" in data
        assert "finding_id" in data
        assert "status" in data
