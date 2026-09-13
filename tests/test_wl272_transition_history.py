# @trace WL-272 B90-W2-B1
"""Tests for the transition history log (WL-272).

Validates the append-only history log for status transitions with
JSONL persistence, time-range queries, and full replay capability.
"""

from __future__ import annotations

from datetime import datetime

import orjson as json
import pytest

from thegent.integrations.transition_history import (
    StatusTransition,
    TransitionHistoryLog,
)


@pytest.mark.requirement("WL-272")
def test_transition_dataclass_creation():
    """Test StatusTransition dataclass creation with all fields."""
    t = StatusTransition(
        wl_id="WL-100",
        from_status="OPEN",
        to_status="IN_PROGRESS",
        timestamp="2026-02-22T10:00:00",
        trigger="sync_cycle",
        cycle_id="cycle-001",
    )
    assert t.wl_id == "WL-100"
    assert t.from_status == "OPEN"
    assert t.to_status == "IN_PROGRESS"
    assert t.timestamp == "2026-02-22T10:00:00"
    assert t.trigger == "sync_cycle"
    assert t.cycle_id == "cycle-001"


@pytest.mark.requirement("WL-272")
def test_transition_dataclass_optional_cycle_id():
    """Test StatusTransition with optional cycle_id."""
    t = StatusTransition(
        wl_id="WL-101",
        from_status="OPEN",
        to_status="DONE",
        timestamp="2026-02-22T11:00:00",
        trigger="manual",
    )
    assert t.cycle_id is None


@pytest.mark.requirement("WL-272")
def test_append_single_transition(tmp_path):
    """Test appending a single transition to the log."""
    log_path = tmp_path / "transition_history.jsonl"
    log = TransitionHistoryLog(log_path)

    t = StatusTransition(
        wl_id="WL-200",
        from_status="OPEN",
        to_status="IN_PROGRESS",
        timestamp="2026-02-22T10:00:00",
        trigger="sync_cycle",
        cycle_id="cycle-001",
    )
    log.append(t)

    # Verify file was created and contains the record
    assert log_path.exists()
    with open(log_path) as f:
        lines = f.readlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["wl_id"] == "WL-200"
    assert data["to_status"] == "IN_PROGRESS"


@pytest.mark.requirement("WL-272")
def test_read_all_empty_log(tmp_path):
    """Test reading from a non-existent log returns empty list."""
    log_path = tmp_path / "nonexistent.jsonl"
    log = TransitionHistoryLog(log_path)

    result = log.read_all()
    assert result == []


@pytest.mark.requirement("WL-272")
def test_read_all_multiple_transitions(tmp_path):
    """Test reading multiple transitions from the log."""
    log_path = tmp_path / "transition_history.jsonl"
    log = TransitionHistoryLog(log_path)

    # Append multiple transitions
    transitions = [
        StatusTransition(
            wl_id="WL-300",
            from_status="OPEN",
            to_status="IN_PROGRESS",
            timestamp="2026-02-22T10:00:00",
            trigger="sync_cycle",
        ),
        StatusTransition(
            wl_id="WL-301",
            from_status="IN_PROGRESS",
            to_status="REVIEW",
            timestamp="2026-02-22T11:00:00",
            trigger="sync_cycle",
            cycle_id="cycle-002",
        ),
        StatusTransition(
            wl_id="WL-302",
            from_status="REVIEW",
            to_status="DONE",
            timestamp="2026-02-22T12:00:00",
            trigger="manual",
        ),
    ]

    for t in transitions:
        log.append(t)

    # Read all and verify
    result = log.read_all()
    assert len(result) == 3
    assert result[0].wl_id == "WL-300"
    assert result[1].wl_id == "WL-301"
    assert result[2].wl_id == "WL-302"


@pytest.mark.requirement("WL-272")
def test_read_since_time_range(tmp_path):
    """Test reading transitions since a specific datetime."""
    log_path = tmp_path / "transition_history.jsonl"
    log = TransitionHistoryLog(log_path)

    # Append transitions with different timestamps
    log.append(
        StatusTransition(
            wl_id="WL-400",
            from_status="OPEN",
            to_status="IN_PROGRESS",
            timestamp="2026-02-22T10:00:00",
            trigger="sync_cycle",
        )
    )
    log.append(
        StatusTransition(
            wl_id="WL-401",
            from_status="IN_PROGRESS",
            to_status="DONE",
            timestamp="2026-02-22T12:00:00",
            trigger="sync_cycle",
        )
    )
    log.append(
        StatusTransition(
            wl_id="WL-402",
            from_status="DONE",
            to_status="OPEN",
            timestamp="2026-02-22T14:00:00",
            trigger="manual",
        )
    )

    # Read since 11:00:00 - should get 2 transitions (at 12:00 and 14:00)
    cutoff = datetime.fromisoformat("2026-02-22T11:00:00")
    result = log.read_since(cutoff)

    assert len(result) == 2
    assert result[0].wl_id == "WL-401"
    assert result[1].wl_id == "WL-402"


@pytest.mark.requirement("WL-272")
def test_persistence_across_instances(tmp_path):
    """Test that data persists correctly across log instances."""
    log_path = tmp_path / "transition_history.jsonl"

    # Create first instance and append
    log1 = TransitionHistoryLog(log_path)
    log1.append(
        StatusTransition(
            wl_id="WL-500",
            from_status="OPEN",
            to_status="IN_PROGRESS",
            timestamp="2026-02-22T10:00:00",
            trigger="sync_cycle",
        )
    )

    # Create second instance and verify it can read the data
    log2 = TransitionHistoryLog(log_path)
    result = log2.read_all()

    assert len(result) == 1
    assert result[0].wl_id == "WL-500"
    assert result[0].to_status == "IN_PROGRESS"
