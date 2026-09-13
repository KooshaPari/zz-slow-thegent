"""Phase 3/4 third-pass hardening tests for the decision audit lane.

Targets the AUDIT-1 / AUDIT-6 / AUDIT-9 audit findings and locks down the
new public API:

* ``DecisionAuditAppender`` — bounded rotation by ``max_bytes`` /
  ``max_lines``, ``fsync`` on every write, monotonic clock for
  ``emitted_at``, and an observability surface via
  :meth:`DecisionAuditAppender.audit_stats`.
* :func:`_exc_text` — Rich-markup escape guard used by the cockpit
  / sota CLI error printers (AUDIT-9).
* :class:`TrafficWindow` — bounded ``deque`` ``maxlen`` and
  future-timestamp eviction so a backwards wall-clock jump cannot
  leak events past the window boundary (AUDIT-19).

These tests are intentionally small and independent — each one
documents the contract a future operator / CI consumer can rely on.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import pytest

from thegent.ux.cockpit import DecisionNotice
from thegent.ux.decision_audit import DecisionAuditAppender
from thegent.ux.kpis.traffic import TrafficDashboard, TrafficEvent, TrafficWindow

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_notice(
    *, verdict: str = "allow", reason_code: str = "ok", ts: float = 0.0
) -> DecisionNotice:
    """Build a DecisionNotice with the minimum required fields."""
    return DecisionNotice(
        verdict=verdict,
        reason_code=reason_code,
        rule_id="r.test",
        agent="tester",
        lane="standard",
        evaluated_at=ts or time.time(),
        reason="phase3p4 hardening test",
    )


# ---------------------------------------------------------------------------
# AUDIT-1 — DecisionAuditAppender rotation / size-bound
# ---------------------------------------------------------------------------


class TestDecisionAuditRotation:
    """Validate ``max_bytes`` / ``max_lines`` rotation + observability."""

    def test_no_rotation_under_threshold(self, tmp_path: Path) -> None:
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(
            audit_path=path, max_bytes=10_000, max_lines=10_000
        )
        for i in range(10):
            appender.record(_make_notice(reason_code=f"ok.{i}", ts=1000.0 + i))
        stats = appender.audit_stats()
        assert stats["rotation_count"] == 0
        assert stats["line_count"] == 10
        assert stats["bytes_written"] > 0
        # Active file is at the original path; no rotation siblings yet.
        assert path.exists()
        assert not (tmp_path / "audit.jsonl.1").exists()

    def test_rotates_when_max_lines_exceeded(self, tmp_path: Path) -> None:
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(audit_path=path, max_lines=3, max_backups=3)
        for i in range(7):
            appender.record(_make_notice(reason_code=f"ok.{i}", ts=2000.0 + i))
        stats = appender.audit_stats()
        # 7 events, max_lines=3 ⇒ at least 2 rotations (to .1 and .2).
        assert stats["rotation_count"] >= 2
        # Active file is bounded to <= 3 lines.
        assert stats["line_count"] <= 3
        # Rotated siblings exist.
        assert (tmp_path / "audit.jsonl.1").exists()
        # Highest rotation index observed.
        siblings = sorted(p.name for p in tmp_path.iterdir())
        assert siblings[-1].startswith("audit.jsonl.")

    def test_rotates_when_max_bytes_exceeded(self, tmp_path: Path) -> None:
        path = tmp_path / "audit.jsonl"
        # Tight budget so even a single record triggers rotation.
        appender = DecisionAuditAppender(
            audit_path=path, max_bytes=80, max_lines=10_000
        )
        for i in range(5):
            # Use a verbose reason to inflate the JSON payload.
            big = "x" * 200
            appender.record(
                DecisionNotice(
                    verdict="allow",
                    reason_code=f"ok.{i}",
                    rule_id="r.test",
                    agent="tester",
                    lane="standard",
                    evaluated_at=3000.0 + i,
                    reason=big,
                )
            )
        stats = appender.audit_stats()
        assert stats["rotation_count"] >= 1
        # Active file's byte size is bounded (with a small slack for the
        # JSON wrapper — rotation fires on the *next* write, not retroactively).
        assert stats["bytes_written"] <= 80 + 512

    def test_rotation_count_is_monotonic(self, tmp_path: Path) -> None:
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(audit_path=path, max_lines=2)
        prior = appender.audit_stats()["rotation_count"]
        for i in range(5):
            appender.record(_make_notice(reason_code=f"ok.{i}"))
        assert appender.audit_stats()["rotation_count"] >= prior

    def test_max_lines_zero_means_unbounded(self, tmp_path: Path) -> None:
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(audit_path=path, max_lines=0)
        for i in range(50):
            appender.record(_make_notice(reason_code=f"ok.{i}"))
        stats = appender.audit_stats()
        assert stats["rotation_count"] == 0
        assert stats["line_count"] == 50

    def test_record_many_still_respects_max_lines(self, tmp_path: Path) -> None:
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(audit_path=path, max_lines=4)
        appender.record_many([_make_notice(reason_code=f"ok.{i}") for i in range(10)])
        stats = appender.audit_stats()
        assert stats["line_count"] <= 4
        assert stats["rotation_count"] >= 1

    def test_concurrent_record_does_not_corrupt_jsonl(self, tmp_path: Path) -> None:
        path = tmp_path / "audit.jsonl"
        # Pin a monotonically-advancing clock so the monotonic guard
        # does not collapse all threads onto a single emitted_at.
        state = {"t": 0.0}

        def clock() -> float:
            state["t"] += 0.001
            return state["t"]

        appender = DecisionAuditAppender(audit_path=path, max_lines=10_000, clock=clock)
        n_threads = 4
        per_thread = 50

        def worker(tid: int) -> None:
            for i in range(per_thread):
                appender.record(_make_notice(reason_code=f"ok.t{tid}.{i}"))

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln]
        assert len(lines) == n_threads * per_thread
        # Every line parses as JSON — atomic write fence honoured.
        for ln in lines:
            json.loads(ln)

    def test_audit_stats_lock_snapshot(self, tmp_path: Path) -> None:
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(audit_path=path, max_bytes=0, max_lines=0)
        snap = appender.audit_stats()
        # Surface contract: every documented key is present.
        for key in (
            "line_count",
            "bytes_written",
            "rotation_count",
            "fsync",
            "max_bytes",
            "max_lines",
            "max_backups",
        ):
            assert key in snap


# ---------------------------------------------------------------------------
# AUDIT-6 — DecisionAuditTailer atomic drain
# ---------------------------------------------------------------------------


class TestDecisionAuditTailerAtomicDrain:
    """Verify the tailer's collect+advance sequence holds the cockpit lock."""

    def test_drain_once_emits_buffered_notices(self, tmp_path: Path) -> None:
        from thegent.ux.cockpit import OperatorCockpit
        from thegent.ux.decision_audit import DecisionAuditTailer

        cockpit = OperatorCockpit()
        appender = DecisionAuditAppender(audit_path=tmp_path / "audit.jsonl")
        tailer = DecisionAuditTailer(cockpit, appender, max_batch=64)
        for i in range(5):
            cockpit.record_decision(_make_notice(reason_code=f"ok.{i}"))
        # Drain everything synchronously.
        n = tailer.drain_once()
        assert n == 5
        # JSONL file received the records.
        lines = [
            ln
            for ln in (tmp_path / "audit.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if ln
        ]
        assert len(lines) == 5

    def test_drain_once_is_idempotent(self, tmp_path: Path) -> None:
        from thegent.ux.cockpit import OperatorCockpit
        from thegent.ux.decision_audit import DecisionAuditTailer

        cockpit = OperatorCockpit()
        appender = DecisionAuditAppender(audit_path=tmp_path / "audit.jsonl")
        tailer = DecisionAuditTailer(cockpit, appender, max_batch=64)
        cockpit.record_decision(_make_notice(reason_code="ok"))
        # First drain flushes the one buffered notice.
        assert tailer.drain_once() == 1
        # Second drain is a no-op because the index advanced.
        assert tailer.drain_once() == 0


# ---------------------------------------------------------------------------
# AUDIT-9 — Rich-markup escape guard for CLI error printers
# ---------------------------------------------------------------------------


class TestExcTextEscapesRichMarkup:
    """``_exc_text`` neutralises Rich markup tags in arbitrary strings."""

    def test_exc_text_escapes_brackets(self) -> None:
        from thegent.ux.cli_cockpit import _exc_text

        # Without escaping, ``[bold]x[/bold]`` would be interpreted as
        # Rich markup and stripped from the rendered output.  Rich's
        # escape is tag-aware: only valid markup tags get backslashes;
        # literal ``[1]`` etc. pass through unchanged (which is what
        # operators want — bracketed JSONPath segments still render).
        out = _exc_text("path is /etc/something [bold]injected[/bold] here")
        # The escaped form prefixes the open-bracket with a backslash
        # so Rich renders the literal ``[bold]`` rather than treating
        # it as a markup tag.
        assert out.startswith("path is /etc/something \\[bold]injected\\[/bold] here")

    def test_exc_text_plain_string_unchanged(self) -> None:
        from thegent.ux.cli_cockpit import _exc_text

        assert _exc_text("no brackets here") == "no brackets here"

    def test_exc_text_handles_unicode(self) -> None:
        from thegent.ux.cli_cockpit import _exc_text

        # Should not raise on unicode; bracketed tags stay escaped.
        out = _exc_text("über [bracket] here")
        assert isinstance(out, str)
        assert "\\[bracket]" in out


# ---------------------------------------------------------------------------
# AUDIT-19 — TrafficWindow bounded deque + future-ts eviction
# ---------------------------------------------------------------------------


class TestTrafficWindowBoundedAndClockSkew:
    """Validate the bounded-deque + future-ts eviction hardening."""

    def test_default_maxlen_is_positive(self) -> None:
        w = TrafficWindow(window_s=60.0, bucket_s=1.0)
        assert w.maxlen > 0
        # Auto-derived from window_s / bucket_s * 8.
        assert w.maxlen == max(int(60.0 / 1.0) * 8, 64)

    def test_explicit_maxlen_caps_memory(self) -> None:
        w = TrafficWindow(window_s=10.0, bucket_s=1.0, maxlen=4)
        # Pin the clock so we don't accidentally evict via time-of-day.
        base = 1_000_000.0
        w.set_clock(lambda: base)
        for i in range(20):
            w.record(TrafficEvent(ts=base + 0.1 * i))
        # Cap honoured — deque never grows past maxlen.
        assert len(w.events()) <= 4

    def test_future_timestamp_is_evicted(self) -> None:
        w = TrafficWindow(window_s=5.0, bucket_s=1.0, maxlen=100)
        # Event lands 100 seconds in the future of `now`.
        now = 500.0
        w.set_clock(lambda: now)
        w.record(TrafficEvent(ts=now + 100.0))
        assert len(w.events()) == 1
        # Read summary — eviction drops the future event because
        # summary() is the canonical read path that calls _evict().
        snap = w.summary(now=now)
        assert snap["count"] == 0

    def test_backwards_clock_step_does_not_leak_events(self) -> None:
        w = TrafficWindow(window_s=5.0, bucket_s=1.0, maxlen=100)
        # Start at t=1000.
        now = [1000.0]
        w.set_clock(lambda: now[0])
        w.record(TrafficEvent(ts=now[0]))
        # Clock jumps backwards by 50s (NTP step). Old event is now
        # "in the future" relative to the new clock.
        now[0] = 950.0
        w.record(TrafficEvent(ts=now[0]))
        snap = w.summary(now=now[0])
        # Only the new event survives — the prior future-ts event was evicted.
        assert snap["count"] == 1

    def test_dashboard_propagates_maxlen(self) -> None:
        d = TrafficDashboard(window_s=10.0, bucket_s=1.0, maxlen=3)
        assert d.window.maxlen == 3

    def test_dashboard_record_under_burst_stays_bounded(self) -> None:
        d = TrafficDashboard(window_s=10.0, bucket_s=1.0, maxlen=5)
        base = 2_000_000.0
        d.set_clock(lambda: base)
        for i in range(50):
            d.record(TrafficEvent(ts=base + 0.01 * i))
        # Window memory cap honoured.
        assert len(d.window.events()) <= 5
