"""Tests for WL-195: Reflection decision event log.

# @trace WL-195
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import orjson as json
import pytest

from thegent.integrations.reflection_event_log import (
    ReflectionDecision,
    ReflectionEventLog,
)


class TestReflectionDecision:
    """Tests for ReflectionDecision dataclass."""

    @pytest.mark.requirement("WL-195")
    def test_reflection_decision_creation(self):
        """# @trace WL-195 — ReflectionDecision can be created with required fields."""
        now = datetime.now(UTC).isoformat()
        decision = ReflectionDecision(
            wl_id="WL-195",
            decision_type="apply",
            before_value="old",
            after_value="new",
            connector="github",
            timestamp=now,
            cycle_id="cycle-001",
        )
        assert decision.wl_id == "WL-195"
        assert decision.decision_type == "apply"
        assert decision.before_value == "old"
        assert decision.after_value == "new"
        assert decision.connector == "github"
        assert decision.timestamp == now
        assert decision.cycle_id == "cycle-001"

    @pytest.mark.requirement("WL-195")
    def test_reflection_decision_type_apply(self):
        """# @trace WL-195 — decision_type can be 'apply'."""
        now = datetime.now(UTC).isoformat()
        decision = ReflectionDecision(
            wl_id="WL-195",
            decision_type="apply",
            before_value=None,
            after_value="value",
            connector="test",
            timestamp=now,
            cycle_id="test",
        )
        assert decision.decision_type == "apply"

    @pytest.mark.requirement("WL-195")
    def test_reflection_decision_type_skip(self):
        """# @trace WL-195 — decision_type can be 'skip'."""
        now = datetime.now(UTC).isoformat()
        decision = ReflectionDecision(
            wl_id="WL-195",
            decision_type="skip",
            before_value="value",
            after_value="value",
            connector="test",
            timestamp=now,
            cycle_id="test",
        )
        assert decision.decision_type == "skip"

    @pytest.mark.requirement("WL-195")
    def test_reflection_decision_type_conflict(self):
        """# @trace WL-195 — decision_type can be 'conflict'."""
        now = datetime.now(UTC).isoformat()
        decision = ReflectionDecision(
            wl_id="WL-195",
            decision_type="conflict",
            before_value="value1",
            after_value="value2",
            connector="test",
            timestamp=now,
            cycle_id="test",
        )
        assert decision.decision_type == "conflict"


class TestReflectionEventLog:
    """Tests for ReflectionEventLog class."""

    @pytest.mark.requirement("WL-195")
    def test_event_log_initialization_with_default_path(self, tmp_path):
        """# @trace WL-195 — ReflectionEventLog initializes with default path."""
        # Use tmp_path to avoid creating files in project root
        log_path = tmp_path / "reflection_events.jsonl"
        event_log = ReflectionEventLog(log_path)
        assert event_log.log_path == log_path

    @pytest.mark.requirement("WL-195")
    def test_event_log_initialization_with_custom_path(self, tmp_path):
        """# @trace WL-195 — ReflectionEventLog accepts custom path."""
        custom_path = tmp_path / "custom" / "events.jsonl"
        event_log = ReflectionEventLog(custom_path)
        assert event_log.log_path == custom_path

    @pytest.mark.requirement("WL-195")
    def test_event_log_log_writes_to_file(self, tmp_path):
        """# @trace WL-195 — log() writes decision to file."""
        log_path = tmp_path / "events.jsonl"
        event_log = ReflectionEventLog(log_path)

        now = datetime.now(UTC).isoformat()
        decision = ReflectionDecision(
            wl_id="WL-195",
            decision_type="apply",
            before_value="old",
            after_value="new",
            connector="github",
            timestamp=now,
            cycle_id="cycle-001",
        )

        event_log.log(decision)

        # Verify file was created and contains the decision
        assert log_path.exists()
        with open(log_path) as f:
            line = f.readline().strip()
            data = json.loads(line)
            assert data["wl_id"] == "WL-195"
            assert data["decision_type"] == "apply"

    @pytest.mark.requirement("WL-195")
    def test_event_log_read_all(self, tmp_path):
        """# @trace WL-195 — read_all() returns all logged decisions."""
        log_path = tmp_path / "events.jsonl"
        event_log = ReflectionEventLog(log_path)

        now = datetime.now(UTC).isoformat()
        decisions = [
            ReflectionDecision(
                wl_id="WL-195",
                decision_type="apply",
                before_value="old1",
                after_value="new1",
                connector="github",
                timestamp=now,
                cycle_id="cycle-001",
            ),
            ReflectionDecision(
                wl_id="WL-195",
                decision_type="skip",
                before_value="old2",
                after_value="old2",
                connector="github",
                timestamp=now,
                cycle_id="cycle-001",
            ),
        ]

        for decision in decisions:
            event_log.log(decision)

        all_events = event_log.read_all()
        assert len(all_events) == 2
        assert all_events[0].decision_type == "apply"
        assert all_events[1].decision_type == "skip"

    @pytest.mark.requirement("WL-195")
    def test_event_log_read_by_type(self, tmp_path):
        """# @trace WL-195 — read_by_type() filters decisions by type."""
        log_path = tmp_path / "events.jsonl"
        event_log = ReflectionEventLog(log_path)

        now = datetime.now(UTC).isoformat()
        decisions = [
            ReflectionDecision(
                wl_id="WL-195",
                decision_type="apply",
                before_value="old1",
                after_value="new1",
                connector="github",
                timestamp=now,
                cycle_id="cycle-001",
            ),
            ReflectionDecision(
                wl_id="WL-195",
                decision_type="skip",
                before_value="old2",
                after_value="old2",
                connector="github",
                timestamp=now,
                cycle_id="cycle-001",
            ),
            ReflectionDecision(
                wl_id="WL-195",
                decision_type="apply",
                before_value="old3",
                after_value="new3",
                connector="github",
                timestamp=now,
                cycle_id="cycle-002",
            ),
        ]

        for decision in decisions:
            event_log.log(decision)

        apply_decisions = event_log.read_by_type("apply")
        assert len(apply_decisions) == 2
        assert all(d.decision_type == "apply" for d in apply_decisions)

        skip_decisions = event_log.read_by_type("skip")
        assert len(skip_decisions) == 1
        assert skip_decisions[0].decision_type == "skip"

    @pytest.mark.requirement("WL-195")
    def test_event_log_read_since(self, tmp_path):
        """# @trace WL-195 — read_since() filters decisions by datetime."""
        log_path = tmp_path / "events.jsonl"
        event_log = ReflectionEventLog(log_path)

        now = datetime.now(UTC)
        past = (now - timedelta(hours=1)).isoformat()
        recent = now.isoformat()
        future = (now + timedelta(hours=1)).isoformat()

        decisions = [
            ReflectionDecision(
                wl_id="WL-195",
                decision_type="apply",
                before_value="old1",
                after_value="new1",
                connector="github",
                timestamp=past,
                cycle_id="cycle-001",
            ),
            ReflectionDecision(
                wl_id="WL-195",
                decision_type="apply",
                before_value="old2",
                after_value="new2",
                connector="github",
                timestamp=recent,
                cycle_id="cycle-002",
            ),
            ReflectionDecision(
                wl_id="WL-195",
                decision_type="apply",
                before_value="old3",
                after_value="new3",
                connector="github",
                timestamp=future,
                cycle_id="cycle-003",
            ),
        ]

        for decision in decisions:
            event_log.log(decision)

        # Read decisions since now (should include recent and future)
        since_now = event_log.read_since(now)
        assert len(since_now) == 2

    @pytest.mark.requirement("WL-195")
    def test_event_log_loads_existing_events(self, tmp_path):
        """# @trace WL-195 — ReflectionEventLog loads existing events from file."""
        log_path = tmp_path / "events.jsonl"

        # First, create and populate the log
        event_log1 = ReflectionEventLog(log_path)
        now = datetime.now(UTC).isoformat()
        decision = ReflectionDecision(
            wl_id="WL-195",
            decision_type="apply",
            before_value="old",
            after_value="new",
            connector="github",
            timestamp=now,
            cycle_id="cycle-001",
        )
        event_log1.log(decision)

        # Create a new instance and verify it loads the existing event
        event_log2 = ReflectionEventLog(log_path)
        all_events = event_log2.read_all()
        assert len(all_events) == 1
        assert all_events[0].wl_id == "WL-195"

    @pytest.mark.requirement("WL-195")
    def test_event_log_read_empty_log(self, tmp_path):
        """# @trace WL-195 — read_all() returns empty list for new log file."""
        log_path = tmp_path / "empty.jsonl"
        event_log = ReflectionEventLog(log_path)
        all_events = event_log.read_all()
        assert all_events == []
