"""Tests for the JSONL decision audit appender (Phase 3/4 hardening lane).

These tests pin the deterministic-replay contract: a frozen clock + the
appender must produce byte-identical JSONL output across runs, so SOTA
audit tooling can rely on stable hashes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from thegent.ux.cockpit import DecisionNotice, OperatorCockpit
from thegent.ux.decision_audit import (
    DEFAULT_TAIL_INTERVAL_S,
    DecisionAuditAppender,
    DecisionAuditTailer,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class _FrozenClock:
    """Frozen wall clock — returns the same value until ``advance()``."""

    def __init__(self, start: float = 1_700_000_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _make_notice(
    *,
    verdict: str = "deny",
    reason_code: str = "trust_boundary_violation",
    rule_id: str | None = "no-network",
    agent: str = "cursor",
    lane: str = "critical",
    evaluated_at: float = 0.0,
    reason: str = "sensitive prompt + low-trust agent",
) -> DecisionNotice:
    return DecisionNotice(
        verdict=verdict,
        reason_code=reason_code,
        rule_id=rule_id,
        agent=agent,
        lane=lane,
        evaluated_at=evaluated_at,
        reason=reason,
    )


# ---------------------------------------------------------------------------
# DecisionAuditAppender
# ---------------------------------------------------------------------------


class TestAppenderRejectsBadInput:
    def test_record_rejects_non_decision_notice(self, tmp_path: Path) -> None:
        appender = DecisionAuditAppender(audit_path=tmp_path / "decisions.jsonl")
        with pytest.raises(TypeError, match="DecisionNotice"):
            appender.record({"verdict": "deny"})  # type: ignore[arg-type]

    def test_record_many_aborts_on_bad_input(self, tmp_path: Path) -> None:
        appender = DecisionAuditAppender(audit_path=tmp_path / "decisions.jsonl")
        with pytest.raises(TypeError):
            appender.record_many(
                iter(
                    [
                        _make_notice(),
                        "not a notice",  # type: ignore[list-item]
                    ]
                )
            )
        # The file may or may not exist; if it does, the good record should
        # not have been flushed because the batch aborted.
        log = tmp_path / "decisions.jsonl"
        if log.exists():
            assert log.read_text(encoding="utf-8").strip() == ""


class TestAppenderPersistsShape:
    def test_record_persists_canonical_shape(self, tmp_path: Path) -> None:
        clock = _FrozenClock(start=10_000.0)
        appender = DecisionAuditAppender(audit_path=tmp_path / "decisions.jsonl", clock=clock)
        notice = _make_notice(evaluated_at=9_990.0)
        appender.record(notice)
        lines = (tmp_path / "decisions.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["event_type"] == "cockpit.decision.recorded"
        assert record["verdict"] == "deny"
        assert record["reason_code"] == "trust_boundary_violation"
        assert record["rule_id"] == "no-network"
        assert record["agent"] == "cursor"
        assert record["lane"] == "critical"
        assert record["evaluated_at"] == 9_990.0
        assert record["emitted_at"] == 10_000.0
        assert "sensitive prompt" in record["reason"]

    def test_record_many_returns_count(self, tmp_path: Path) -> None:
        appender = DecisionAuditAppender(audit_path=tmp_path / "decisions.jsonl")
        count = appender.record_many([_make_notice(rule_id=f"r{i}") for i in range(5)])
        assert count == 5
        log = tmp_path / "decisions.jsonl"
        assert len(log.read_text(encoding="utf-8").splitlines()) == 5


class TestAppenderDeterminism:
    def test_deterministic_with_frozen_clock(self, tmp_path: Path) -> None:
        clock = _FrozenClock(start=42.0)
        a = DecisionAuditAppender(audit_path=tmp_path / "a.jsonl", clock=clock)
        b = DecisionAuditAppender(audit_path=tmp_path / "b.jsonl", clock=clock)
        notice = _make_notice(evaluated_at=41.0, reason="deterministic")
        a.record(notice)
        b.record(notice)
        a_text = (tmp_path / "a.jsonl").read_text(encoding="utf-8")
        b_text = (tmp_path / "b.jsonl").read_text(encoding="utf-8")
        assert a_text == b_text
        assert a_text.endswith("\n")

    def test_clock_advance_changes_emitted_at(self, tmp_path: Path) -> None:
        clock = _FrozenClock(start=10.0)
        appender = DecisionAuditAppender(audit_path=tmp_path / "d.jsonl", clock=clock)
        appender.record(_make_notice(evaluated_at=5.0))
        clock.advance(7.0)
        appender.record(_make_notice(rule_id="r2", evaluated_at=6.0))
        lines = (tmp_path / "d.jsonl").read_text(encoding="utf-8").splitlines()
        rec1 = json.loads(lines[0])
        rec2 = json.loads(lines[1])
        assert rec1["emitted_at"] == 10.0
        assert rec2["emitted_at"] == 17.0


class TestAppenderTail:
    def test_tail_missing_file_returns_empty(self, tmp_path: Path) -> None:
        appender = DecisionAuditAppender(audit_path=tmp_path / "missing.jsonl")
        assert appender.tail_events() == []

    def test_tail_skips_malformed_lines(self, tmp_path: Path) -> None:
        log = tmp_path / "d.jsonl"
        log.write_text('{"event_type":"cockpit.decision.recorded","verdict":"allow"}\nNOT_JSON\n', encoding="utf-8")
        appender = DecisionAuditAppender(audit_path=log)
        events = appender.tail_events(n=10)
        assert len(events) == 1
        assert events[0]["verdict"] == "allow"

    def test_tail_returns_last_n(self, tmp_path: Path) -> None:
        appender = DecisionAuditAppender(audit_path=tmp_path / "d.jsonl")
        for i in range(10):
            appender.record(_make_notice(rule_id=f"r{i}"))
        events = appender.tail_events(n=3)
        assert len(events) == 3
        assert [e["rule_id"] for e in events] == ["r7", "r8", "r9"]


class TestAppenderSetClock:
    def test_set_clock_swaps_emitted_at_source(self, tmp_path: Path) -> None:
        appender = DecisionAuditAppender(audit_path=tmp_path / "d.jsonl")
        appender.set_clock(lambda: 999.0)
        appender.record(_make_notice())
        rec = json.loads((tmp_path / "d.jsonl").read_text(encoding="utf-8").splitlines()[0])
        assert rec["emitted_at"] == 999.0

    def test_audit_path_returns_expanded_path(self, tmp_path: Path) -> None:
        log = tmp_path / "d.jsonl"
        appender = DecisionAuditAppender(audit_path=log)
        assert appender.audit_path() == log


# ---------------------------------------------------------------------------
# DecisionAuditTailer
# ---------------------------------------------------------------------------


class TestTailerDrainsCockpit:
    def test_drain_once_appends_new_decisions(self, tmp_path: Path) -> None:
        clock = _FrozenClock(start=1.0)
        cockpit = OperatorCockpit(clock=clock)
        appender = DecisionAuditAppender(audit_path=tmp_path / "d.jsonl", clock=clock)
        tailer = DecisionAuditTailer(cockpit=cockpit, appender=appender)
        cockpit.record_decision(_make_notice(rule_id="r1"))
        cockpit.record_decision(_make_notice(rule_id="r2"))
        # advance the clock so ``emitted_at`` differs from ``evaluated_at`` defaults
        clock.advance(2.0)
        appended = tailer.drain_once()
        assert appended == 2
        events = appender.tail_events(n=10)
        assert [e["rule_id"] for e in events] == ["r1", "r2"]
        # second call is a no-op (no new decisions)
        assert tailer.drain_once() == 0

    def test_drain_once_first_call_persists_existing_buffer(self, tmp_path: Path) -> None:
        clock = _FrozenClock(start=5.0)
        cockpit = OperatorCockpit(clock=clock)
        appender = DecisionAuditAppender(audit_path=tmp_path / "d.jsonl", clock=clock)
        # Pre-populate the cockpit before attaching the tailer.
        cockpit.record_decision(_make_notice(rule_id="seed"))
        tailer = DecisionAuditTailer(cockpit=cockpit, appender=appender)
        assert tailer.drain_once() == 1
        log_lines = (tmp_path / "d.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(log_lines) == 1
        assert json.loads(log_lines[0])["rule_id"] == "seed"

    def test_max_batch_caps_single_drain(self, tmp_path: Path) -> None:
        clock = _FrozenClock(start=0.0)
        cockpit = OperatorCockpit(clock=clock)
        appender = DecisionAuditAppender(audit_path=tmp_path / "d.jsonl", clock=clock)
        tailer = DecisionAuditTailer(cockpit=cockpit, appender=appender, max_batch=2)
        for i in range(5):
            cockpit.record_decision(_make_notice(rule_id=f"r{i}"))
        # First drain: limited by max_batch
        assert tailer.drain_once() == 2
        # Second drain: also capped by max_batch
        assert tailer.drain_once() == 2
        # Third drain: picks up the final item
        assert tailer.drain_once() == 1
        # No new notices
        assert tailer.drain_once() == 0
        # All 5 events were eventually persisted
        assert len(appender.tail_events(n=10)) == 5

    def test_default_interval_is_one_second(self) -> None:
        # Default tail cadence mirrors OverrideExpiryMonitor (1s).
        assert DEFAULT_TAIL_INTERVAL_S == 1.0


class TestTailerLifecycle:
    def test_start_is_idempotent(self, tmp_path: Path) -> None:
        clock = _FrozenClock(start=0.0)
        cockpit = OperatorCockpit(clock=clock)
        appender = DecisionAuditAppender(audit_path=tmp_path / "d.jsonl", clock=clock)
        tailer = DecisionAuditTailer(
            cockpit=cockpit,
            appender=appender,
            interval_s=0.05,
        )
        tailer.start()
        try:
            cockpit.record_decision(_make_notice(rule_id="async"))
            # The tail thread drains within interval_s + scheduling jitter.
            import time as _time

            deadline = _time.time() + 1.0
            while _time.time() < deadline:
                if appender.tail_events():
                    break
                _time.sleep(0.05)
            events = appender.tail_events(n=5)
            assert any(e["rule_id"] == "async" for e in events)
        finally:
            tailer.stop(timeout_s=2.0)
        # restart should not raise
        tailer.start()
        tailer.stop(timeout_s=2.0)
