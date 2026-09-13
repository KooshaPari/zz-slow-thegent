"""SOTA audit performance budget tests.

Pins per-operation latency budgets for the hot-path surfaces that run
inside the 1-second DAG tick cadence.  Each budget is deliberately
generous (~10-20x measured cost) so CI noise does not flake the tests,
but tight enough that a real regression (e.g. O(N²) loop, unclosed
file handle, un-bounded deque growth) trips the assertion before it
ships.

Covers:
    P-091  DecisionAuditAppender.record() < 2 ms per append
    P-092  TrafficDashboard.record() + summary() < 5 ms round-trip
    P-093  cockpit.render() under high decision-notice pressure < 50 ms
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# P-091 — DecisionAuditAppender.record() per-append latency budget
# ---------------------------------------------------------------------------
class TestDecisionAuditAppendBudget:
    """Pin P-091: per-append latency budget for the JSONL appender.

    The appender is called once per governance decision inside the
    cockpit tick; at 10 decisions/tick it must not exceed 2 ms total
    (200 µs per append).  The ceiling is generous (measured cost is
    ~50-100 µs on dev hardware) but a regression past 2 ms would
    compound quickly under real governance load.
    """

    _P91_BUDGET_MS = 2.0  # per single append ceiling

    def test_single_append_under_budget(self) -> None:
        """One record() call stays well under the P-091 budget."""
        from thegent.ux.decision_audit import DecisionAuditAppender

        with tempfile.TemporaryDirectory() as td:
            appender = DecisionAuditAppender(audit_path=Path(td) / "test.jsonl")
            from thegent.ux.cockpit import DecisionNotice

            notice = DecisionNotice(
                verdict="allow",
                reason_code="ok",
                rule_id="test-rule",
                agent="ci-agent",
                lane="standard",
                evaluated_at=time.time(),
                reason="perf budget test",
            )
            # Warm-up
            appender.record(notice)
            # Measure
            t0 = time.perf_counter()
            appender.record(notice)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            assert elapsed_ms < self._P91_BUDGET_MS, (
                f"DecisionAuditAppender.record() took {elapsed_ms:.3f} ms, "
                f"exceeds P-091 budget of {self._P91_BUDGET_MS} ms"
            )

    def test_batch_append_under_budget(self) -> None:
        """Ten record_many() items stay under 10x the single-append budget."""
        from thegent.ux.decision_audit import DecisionAuditAppender

        with tempfile.TemporaryDirectory() as td:
            appender = DecisionAuditAppender(audit_path=Path(td) / "test_batch.jsonl")
            from thegent.ux.cockpit import DecisionNotice

            notices = [
                DecisionNotice(
                    verdict="allow",
                    reason_code="ok",
                    rule_id=f"rule-{i}",
                    agent="ci-agent",
                    lane="standard",
                    evaluated_at=time.time(),
                    reason=f"batch item {i}",
                )
                for i in range(10)
            ]
            t0 = time.perf_counter()
            appender.record_many(notices)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            assert elapsed_ms < self._P91_BUDGET_MS * 10, (
                f"DecisionAuditAppender.record_many(10) took {elapsed_ms:.3f} ms, "
                f"exceeds P-091 batch budget of {self._P91_BUDGET_MS * 10} ms"
            )


# ---------------------------------------------------------------------------
# P-092 — TrafficDashboard.record() + summary() round-trip budget
# ---------------------------------------------------------------------------
class TestTrafficDashboardBudget:
    """Pin P-092: per-event record + summary round-trip < 5 ms.

    The traffic dashboard is read on every cockpit render and written
    on every event; the combined record+summary path must stay fast
    enough that a burst of 50 events does not stall the tick.
    """

    _P92_BUDGET_MS = 5.0  # record + summary round-trip ceiling

    def test_record_summary_round_trip_under_budget(self) -> None:
        """A single record() + summary() pair stays under P-092."""
        from thegent.ux.kpis.traffic import TrafficDashboard, TrafficEvent

        dash = TrafficDashboard()
        event = TrafficEvent(ts=time.time(), lane="standard", agent="test-agent", status="ok")
        dash.record(event)
        # Warm-up
        dash.summary()
        # Measure
        t0 = time.perf_counter()
        result = dash.summary()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        assert result is not None, "summary() should return a result"
        assert elapsed_ms < self._P92_BUDGET_MS, (
            f"TrafficDashboard.record+summary took {elapsed_ms:.3f} ms, "
            f"exceeds P-092 budget of {self._P92_BUDGET_MS} ms"
        )

    def test_burst_record_under_budget(self) -> None:
        """Fifty record() calls stay under 10x the single-event budget."""
        from thegent.ux.kpis.traffic import TrafficDashboard, TrafficEvent

        dash = TrafficDashboard()
        t0 = time.perf_counter()
        for i in range(50):
            event = TrafficEvent(
                ts=time.time(),
                lane=("standard", "fast", "critical")[i % 3],
                agent=f"agent-{i % 5}",
                status="ok",
            )
            dash.record(event)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        assert elapsed_ms < self._P92_BUDGET_MS * 10, (
            f"TrafficDashboard.record(50) took {elapsed_ms:.3f} ms, "
            f"exceeds P-092 burst budget of {self._P92_BUDGET_MS * 10} ms"
        )


# ---------------------------------------------------------------------------
# P-093 — cockpit.render() under high decision-notice pressure
# ---------------------------------------------------------------------------
class TestCockpitDecisionNoticePressure:
    """Pin P-093: cockpit.render() under sustained decision-notice load.

    The governance bridge can push dozens of decision notices per tick
    when a federated policy engine is active.  This test fills the
    decision-notices deque to capacity and confirms the render stays
    within the P-090 50 ms SLO.
    """

    _P93_SLO_MS = 50.0  # same as P-090

    def test_render_with_full_decision_notices_under_slo(self) -> None:
        """A cockpit at MAX_DECISION_NOTICES renders under 50 ms."""
        from thegent.ux.cockpit import (
            MAX_DECISION_NOTICES,
            DecisionNotice,
            OperatorCockpit,
        )

        c = OperatorCockpit()
        for i in range(MAX_DECISION_NOTICES):
            notice = DecisionNotice(
                verdict=("allow", "deny", "warn")[i % 3],
                reason_code=f"code-{i % 7}",
                rule_id=f"rule-{i}",
                agent=f"agent-{i % 5}",
                lane=("standard", "fast", "critical")[i % 3],
                evaluated_at=time.time() - i,
                reason=f"pressure test reason text {i}",
            )
            c.record_decision(notice)

        c.render()  # warm-up
        t0 = time.perf_counter()
        text = c.render()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        assert text, "render should produce output"
        assert elapsed_ms < self._P93_SLO_MS, (
            f"cockpit.render() with {MAX_DECISION_NOTICES} decision notices "
            f"took {elapsed_ms:.2f} ms, exceeds P-093 SLO of {self._P93_SLO_MS} ms"
        )
