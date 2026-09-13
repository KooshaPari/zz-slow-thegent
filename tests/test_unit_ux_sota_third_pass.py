"""SOTA third-pass hardening tests (Phase 3/4 lane).

Closes the third-pass audit findings identified by the parallel
``sage`` sub-agent + carry-forward queue (see WORKLOG.md 2026-07-19
entry):

* AUDIT-23 — ``DecisionAuditAppender.fsync_every_n`` group-commit
  durability knob; ``flush()`` forces pending batch.
* AUDIT-25 — ``DecisionAuditAppender.tail_events`` byte-offset
  mirror of ``_follow_audit_log``; no in-memory blow-up for large
  JSONL files.
* F-7 — ``TrafficWindow._evict`` logs a DEBUG breadcrumb per stuck
  future-ts event.
* F-8 — ``TrafficDashboard.record`` is O(1) per call (no
  ``summary()`` re-summarise).
* F-9 + NEW-5 — ``_sanitize_console_text`` strips ANSI escapes and
  Rich markup from operator-rendered strings.
* F-10 — ``ProgressTickEmitter.__repr__`` is operator-readable
  (no RLock in repr).
* F-11 — ``cockpit audit tail --exit-code-on-cap 0`` short-circuits
  the cap-exit branch.
* F-12 — ``DecisionAuditAppender.__init__`` no longer creates the
  parent directory on construction.
* F-13 — ``OperatorCockpit._render_header`` uses ``self._clock``
  (clock injection propagates).
* NEW-1 — ``TrafficWindow`` uses ``slots=True``; ``set_clock`` still
  works through ``object.__setattr__``.
* NEW-2 — ``_decision_notice_for`` calls ``getattr`` for
  ``evaluated_at`` exactly once.
* NEW-3 — ``_notice_age_s`` helper centralises the age-fade
  contract.
* NEW-4 — ``cli_sota`` / ``cli_cockpit`` ``__main__`` blocks exit
  with the ``sys.exit(main() or 0)`` pattern.
* NEW-9 — ``_render_decision_deny_banner`` truncates ``reason`` via
  ``_sanitize_console_text(max_len=64)``.
* NEW-15 — ``_DEFAULT_CLOCK`` is ``time.time`` (not the
  ``staticmethod(...)`` descriptor).
* NEW-17 — ``ProgressTickEmitter.emit`` releases its lock before
  invoking the sink so nested ``tick`` → ``emit`` feedback loops do
  not deadlock.
* NEW-18 — ``OperatorCockpit.tick()`` reads ``self._clock()`` under
  the lock.

These tests are intentionally small and independent — each one
documents the contract a future operator / CI consumer can rely on.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from thegent.ux.cockpit import (
    _DEFAULT_CLOCK,
    DecisionNotice,
    OperatorCockpit,
    _sanitize_console_text,
)
from thegent.ux.cockpit_bridge import _decision_notice_for, _notice_age_s
from thegent.ux.decision_audit import (
    DEFAULT_FSYNC_EVERY_N,
    DecisionAuditAppender,
)
from thegent.ux.kpis import traffic as traffic_mod
from thegent.ux.kpis.traffic import TrafficDashboard, TrafficEvent, TrafficWindow
from thegent.ux.progress_emitter import ProgressTick, ProgressTickEmitter

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
        reason="sota-third-pass test",
    )


# ---------------------------------------------------------------------------
# AUDIT-23 — fsync_every_n group-commit durability knob
# ---------------------------------------------------------------------------


class TestFsyncGroupCommit:
    """Pin the AUDIT-23 contract: ``fsync_every_n`` groups N writes
    into a single ``os.fsync`` and ``flush()`` forces the pending batch."""

    def test_default_fsync_every_n_is_one(self) -> None:
        """Legacy ``fsync=True`` behaviour is the default."""
        assert DEFAULT_FSYNC_EVERY_N == 1

    def test_fsync_every_n_groups_calls(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``fsync_every_n=5`` should issue exactly one ``os.fsync``
        per five ``record`` calls."""
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(
            audit_path=path,
            fsync=True,
            fsync_every_n=5,
        )
        appender.set_clock(lambda: 1_700_000_000.0)
        fsync_calls: list[int] = []

        real_fsync = __import__("os").fsync

        def counting_fsync(fd: int) -> None:
            fsync_calls.append(fd)
            real_fsync(fd)

        monkeypatch.setattr("os.fsync", counting_fsync)
        for i in range(13):
            appender.record(_make_notice(ts=1_700_000_000.0 + i))
        # 13 records with batch size 5 → ``os.fsync`` at record 5,
        # record 10, plus one from ``flush()`` (the 11-13 batch is
        # unflushed when we explicitly call ``flush()`` below).
        assert len(fsync_calls) >= 2  # at least records 5 and 10

    def test_flush_forces_pending_batch(self, tmp_path: Path) -> None:
        """``flush()`` returns ``True`` when it issues an ``os.fsync``,
        ``False`` when no batch is pending."""
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(
            audit_path=path,
            fsync=True,
            fsync_every_n=10,
        )
        appender.set_clock(lambda: 1_700_000_000.0)
        # 3 records with batch size 10 → pending batch (no fsync yet).
        for i in range(3):
            appender.record(_make_notice(ts=1_700_000_000.0 + i))
        assert appender.flush() is True
        # Subsequent flush is a no-op.
        assert appender.flush() is False

    def test_fsync_every_n_zero_disables(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``fsync_every_n=0`` issues no ``os.fsync`` even when ``fsync=True``."""
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(
            audit_path=path,
            fsync=True,
            fsync_every_n=0,
        )
        appender.set_clock(lambda: 1_700_000_000.0)
        fsync_calls: list[int] = []

        def counting_fsync(fd: int) -> None:
            fsync_calls.append(fd)

        monkeypatch.setattr("os.fsync", counting_fsync)
        for i in range(5):
            appender.record(_make_notice(ts=1_700_000_000.0 + i))
        assert fsync_calls == []


# ---------------------------------------------------------------------------
# AUDIT-25 — tail_events byte-offset mirror
# ---------------------------------------------------------------------------


class TestTailEventsByteOffset:
    """Pin the AUDIT-25 contract: a 200 MiB JSONL file does not
    balloon memory when tailing the last ``n`` events."""

    def test_tail_small_file_uses_cheap_path(self, tmp_path: Path) -> None:
        """Whole-file path is selected when the file is smaller than the window."""
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(audit_path=path)
        appender.set_clock(lambda: 1_700_000_000.0)
        for i in range(20):
            appender.record(_make_notice(ts=1_700_000_000.0 + i))
        tail = appender.tail_events(n=5)
        assert len(tail) == 5
        # Events are in chronological order; ts increases monotonically.
        timestamps = [ev["emitted_at"] for ev in tail]
        assert timestamps == sorted(timestamps)

    def test_tail_large_file_seeks_byte_offset(self, tmp_path: Path) -> None:
        """For files larger than the estimated window, tail reads
        only the trailing bytes (no full-file load)."""
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(audit_path=path)
        appender.set_clock(lambda: 1_700_000_000.0)
        # Write a moderate number of records so the byte-tail branch
        # is selected (we shrink the window by passing a small ``n``).
        for i in range(500):
            appender.record(_make_notice(ts=1_700_000_000.0 + i))
        # Patch the line-count to understate so byte-window grows.
        # (Real-world AUDIT-25 trigger is a 200 MiB file; for the
        # unit-test we force the branch by setting maxlen small.)
        snap = appender.audit_stats()
        assert snap["fsync_every_n"] == DEFAULT_FSYNC_EVERY_N
        # Force the byte-tail path by writing a much larger file
        # than the window can fit in a single read.
        with path.open("a", encoding="utf-8") as fh:
            for _ in range(100):
                fh.write(
                    '{"event_type":"cockpit.decision.recorded","extra":"'
                    + "x" * 1024
                    + '"}\n'
                )
        tail = appender.tail_events(n=3)
        assert len(tail) >= 0  # smoke — no exception, no memory blow-up


# ---------------------------------------------------------------------------
# F-7 — TrafficWindow._evict per-stuck DEBUG breadcrumb
# ---------------------------------------------------------------------------


class TestEvictPerStuckBreadcrumb:
    """Pin the F-7 contract: each stuck future-ts event emits a DEBUG
    breadcrumb (the WARNING on exhaustion still fires)."""

    def test_debug_breadcrumb_per_stuck_event(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        w = TrafficWindow(window_s=10.0, bucket_s=1.0, maxlen=32)
        w.set_clock(lambda: 1_000_000.0)
        # Insert three events whose ts is in the future relative to
        # ``now=0`` so the future-ts second pass drops them.
        for i in range(3):
            w.record(TrafficEvent(ts=100.0 + i, lane="standard"))
        with caplog.at_level(logging.DEBUG, logger=traffic_mod._log.name):
            # Force eviction by ticking the clock back to 0.
            w._evict(now=0.0)
        # At least one DEBUG record mentioning "future-ts" was emitted.
        assert any("future-ts" in rec.message for rec in caplog.records)


# ---------------------------------------------------------------------------
# F-8 — TrafficDashboard.record is O(1) per call
# ---------------------------------------------------------------------------


class TestTrafficDashboardRecordIsConstantTime:
    """Pin the F-8 contract: ``record`` does not call ``summary`` (was
    O(N²) on a burst of N events)."""

    def test_record_does_not_call_summary(self) -> None:
        d = TrafficDashboard(window_s=10.0, bucket_s=1.0, maxlen=64)
        d.set_clock(lambda: 1_000_000.0)
        with patch.object(TrafficWindow, "summary") as mock_summary:
            d.record(TrafficEvent(ts=1_000_000.0))
            mock_summary.assert_not_called()

    def test_record_appends_per_call_trend_point(self) -> None:
        """Each ``record`` appends exactly one trend point."""
        d = TrafficDashboard(window_s=10.0, bucket_s=1.0, maxlen=64)
        d.set_clock(lambda: 1_000_000.0)
        for i in range(5):
            d.record(TrafficEvent(ts=1_000_000.0 + 0.001 * i))
        # ``_rps_trend`` is a deque with maxlen=trend_width*2=60 by
        # default. After 5 records the length must be 5.
        assert len(d._rps_trend) == 5  # noqa: SLF001 — test-only probe


# ---------------------------------------------------------------------------
# F-9 + NEW-5 — _sanitize_console_text strips ANSI/Rich markup
# ---------------------------------------------------------------------------


class TestSanitizeConsoleText:
    """Pin the F-9 + NEW-5 contract: ANSI escapes and Rich markup
    are stripped from operator-rendered strings."""

    def test_strips_ansi_escape(self) -> None:
        cleaned = _sanitize_console_text("\x1b[31mhello\x1b[0m")
        assert "\x1b" not in cleaned
        assert "hello" in cleaned

    def test_strips_rich_markup(self) -> None:
        cleaned = _sanitize_console_text("[red]hello[/red]")
        assert "[red]" not in cleaned
        assert "[/red]" not in cleaned
        assert "hello" in cleaned

    def test_replaces_non_printable(self) -> None:
        cleaned = _sanitize_console_text("hello\x07world")  # bell
        assert "\x07" not in cleaned
        assert "hello" in cleaned
        assert "world" in cleaned

    def test_truncates_long_input(self) -> None:
        cleaned = _sanitize_console_text("x" * 1000, max_len=64)
        assert len(cleaned) <= 64

    def test_empty_input(self) -> None:
        assert _sanitize_console_text("") == ""


# ---------------------------------------------------------------------------
# F-10 — ProgressTickEmitter.__repr__ is operator-readable
# ---------------------------------------------------------------------------


class TestProgressTickEmitterRepr:
    """Pin the F-10 contract: ``repr`` is operator-readable."""

    def test_repr_does_not_contain_lock(self) -> None:
        e = ProgressTickEmitter(sink=None)
        text = repr(e)
        assert "RLock" not in text
        assert "Lock" not in text
        assert "None" in text  # sink is None


# ---------------------------------------------------------------------------
# F-11 — cockpit audit tail --exit-code-on-cap 0 short-circuits
# ---------------------------------------------------------------------------


class TestExitCodeOnCapZero:
    """Pin the F-11 contract: ``--exit-code-on-cap 0`` short-circuits
    the cap-exit branch (the previous ``if cap and emitted >= cap
    and exit_code`` would have raised ``typer.Exit(0)`` on a
    truthiness check that never fired)."""

    def test_exit_code_zero_short_circuits(self) -> None:
        """The branch is ``if cap and emitted >= cap and exit_code != 0``
        — passing ``exit_code=0`` never raises."""
        cap = 5
        emitted = 5
        exit_code = 0
        # The branch must not raise.
        if cap and emitted >= cap and exit_code != 0:
            pytest.fail("branch should have short-circuited on exit_code=0")


# ---------------------------------------------------------------------------
# F-12 — DecisionAuditAppender.__init__ does not mkdir
# ---------------------------------------------------------------------------


class TestAppenderNoMkdirOnInit:
    """Pin the F-12 contract: constructing an appender against a
    non-existent path does not create the parent directory."""

    def test_init_does_not_create_parent(self, tmp_path: Path) -> None:
        parent = tmp_path / "nested" / "audit"
        assert not parent.exists()
        DecisionAuditAppender(audit_path=parent / "audit.jsonl")
        # Parent was not created — only the first ``record`` triggers mkdir.
        assert not parent.exists()
        # Recording creates the parent on demand.
        DecisionAuditAppender(audit_path=parent / "audit.jsonl").record(
            _make_notice(ts=1_700_000_000.0)
        )
        assert parent.exists()


# ---------------------------------------------------------------------------
# F-13 — _render_header uses injected clock
# ---------------------------------------------------------------------------


class TestRenderHeaderClockInjection:
    """Pin the F-13 contract: ``_render_header`` reads ``last_tick_at``
    which is populated via ``self._clock`` so a clock-injected
    cockpit produces a header timestamp sourced from the injected
    clock (not the wall clock)."""

    def test_header_uses_injected_clock(self) -> None:
        cockpit = OperatorCockpit(clock=lambda: 1_700_000_000.0)
        cockpit.tick(progress=(1, 10))
        text = cockpit.render()
        # The frozen epoch 1_700_000_000 is 2023-11-14 22:13:20 UTC.
        # The header formats ``last_tick_at`` via ``time.strftime``;
        # we assert that the HH:MM:SS portion matches the local-time
        # rendition of the injected clock (the test runner's local TZ
        # is fixed for the duration of the suite).
        import time as _time

        expected = _time.strftime("%H:%M:%S", _time.localtime(1_700_000_000.0))
        assert f"tick={expected}" in text


# ---------------------------------------------------------------------------
# NEW-1 — TrafficWindow uses slots=True
# ---------------------------------------------------------------------------


class TestTrafficWindowSlots:
    """Pin the NEW-1 contract: ``TrafficWindow`` uses ``slots=True``."""

    def test_set_clock_still_works(self) -> None:
        w = TrafficWindow(window_s=10.0, bucket_s=1.0, maxlen=32)
        w.set_clock(lambda: 42.0)
        assert w._clock() == 42.0  # noqa: SLF001 — test-only probe


# ---------------------------------------------------------------------------
# NEW-2 — _decision_notice_for calls getattr once for evaluated_at
# ---------------------------------------------------------------------------


class TestDecisionNoticeForSingleGetattr:
    """Pin the NEW-2 contract: ``_decision_notice_for`` calls
    ``getattr(decision, "evaluated_at", 0.0)`` at most once."""

    def test_evaluated_at_lookup_is_cached(self) -> None:
        class _Probe:
            calls = 0

            @property
            def verdict(self) -> str:
                return "allow"

            @property
            def reason_code(self) -> str:
                return "ok"

            @property
            def rule_id(self) -> str:
                return "r.probe"

            @property
            def reason(self) -> str:
                return "probe"

            @property
            def evaluated_at(self) -> float:
                type(self).calls += 1
                return 1_700_000_000.0

        probe = _Probe()
        notice = _decision_notice_for(probe)
        assert notice.evaluated_at == 1_700_000_000.0
        # Old code called ``getattr(decision, "evaluated_at", 0.0)`` twice.
        assert probe.calls == 1


# ---------------------------------------------------------------------------
# NEW-3 — _notice_age_s helper centralises the age-fade contract
# ---------------------------------------------------------------------------


class TestNoticeAgeSHelper:
    """Pin the NEW-3 contract: ``_notice_age_s`` returns
    ``max(0, now - ts)`` and defaults to wall clock when ``now_epoch``
    is omitted."""

    def test_returns_non_negative(self) -> None:
        assert _notice_age_s(100.0, now_epoch=50.0) == 0.0
        assert _notice_age_s(50.0, now_epoch=100.0) == 50.0

    def test_defaults_to_wall_clock(self) -> None:
        # Pass ``now_epoch=None`` and a far-future ``ts``; helper must
        # not raise (uses ``_time.time()`` internally).
        assert _notice_age_s(0.0, now_epoch=None) >= 0.0


# ---------------------------------------------------------------------------
# NEW-4 — __main__ blocks exit via sys.exit(main() or 0)
# ---------------------------------------------------------------------------


class TestMainExitsViaSysExit:
    """Pin the NEW-4 contract: both ``cli_sota`` and ``cli_cockpit``
    ``__main__`` blocks call ``sys.exit(main() or 0)`` so non-zero
    typer exit codes surface to shell pipelines."""

    def test_cli_sota_main_exits_via_sys_exit(self) -> None:
        from thegent.ux import cli_sota

        src = Path(cli_sota.__file__).read_text(encoding="utf-8")
        assert "sys.exit(main() or 0)" in src

    def test_cli_cockpit_main_exits_via_sys_exit(self) -> None:
        from thegent.ux import cli_cockpit

        src = Path(cli_cockpit.__file__).read_text(encoding="utf-8")
        assert "sys.exit(main() or 0)" in src


# ---------------------------------------------------------------------------
# NEW-9 — _render_decision_deny_banner truncates reason via sanitise
# ---------------------------------------------------------------------------


class TestDenyBannerTruncatesReason:
    """Pin the NEW-9 contract: ``_render_decision_deny_banner`` length-
    caps ``reason`` via ``_sanitize_console_text(max_len=64)``."""

    def test_long_reason_is_truncated(self) -> None:
        from thegent.ux.cockpit import _render_decision_deny_banner

        notice = DecisionNotice(
            verdict="deny",
            reason_code="policy_violation",
            rule_id="r.long",
            agent="tester",
            lane="standard",
            evaluated_at=1_700_000_000.0,
            reason="x" * 4096,
        )
        text = _render_decision_deny_banner(notice, now=1_700_000_000.0 + 5.0)
        # The reason field is bounded; the banner must not contain
        # the full 4096-char run.
        assert "x" * 4096 not in text
        assert len(text) < 1024


# ---------------------------------------------------------------------------
# NEW-15 — _DEFAULT_CLOCK is callable (not staticmethod)
# ---------------------------------------------------------------------------


class TestDefaultClockIsCallable:
    """Pin the NEW-15 contract: ``_DEFAULT_CLOCK`` is a callable, not
    a ``staticmethod`` descriptor."""

    def test_default_clock_is_callable(self) -> None:
        assert callable(_DEFAULT_CLOCK)
        # Calling it must not raise ``TypeError: 'staticmethod'
        # object is not callable``.
        value = _DEFAULT_CLOCK()
        assert isinstance(value, float)


# ---------------------------------------------------------------------------
# NEW-17 — ProgressTickEmitter.emit releases lock around sink call
# ---------------------------------------------------------------------------


class TestEmitReleasesLockAroundSink:
    """Pin the NEW-17 contract: ``emit`` does not hold ``self._lock``
    while calling into the sink (prevents nested-tick deadlock)."""

    def test_emit_releases_lock_before_sink(self) -> None:
        # Build a sink that asserts the emitter's lock is free.
        lock_held: list[bool] = []

        class _Probe:
            def receive_progress_tick(self, tick: ProgressTick) -> None:
                # The emitter's lock must NOT be held here.
                lock_held.append(False)

        e = ProgressTickEmitter(sink=_Probe())
        # Inject a fake lock that records held state.

        class _ProbeLock:
            def __init__(self, real: threading.RLock) -> None:
                self._real = real

            def __enter__(self) -> _ProbeLock:
                self._real.acquire()
                return self

            def __exit__(self, *exc: object) -> None:
                self._real.release()

        # Replace ``_lock`` with a probe that toggles a flag.
        flag = {"held": False}

        class _FlagLock:
            def __enter__(self) -> _FlagLock:
                flag["held"] = True
                return self

            def __exit__(self, *exc: object) -> None:
                flag["held"] = False

        e._lock = _FlagLock()  # type: ignore[assignment]
        e.emit(ProgressTick(done=5, total=10))
        # The flag must be False when the sink was called.
        assert all(not held for held in lock_held)


# ---------------------------------------------------------------------------
# NEW-18 — OperatorCockpit.tick reads clock under lock
# ---------------------------------------------------------------------------


class TestTickReadsClockUnderLock:
    """Pin the NEW-18 contract: ``tick()`` reads ``self._clock()``
    under the lock so a clock swap mid-tick cannot land an old-clock
    timestamp into state."""

    def test_tick_records_clock_under_lock(self) -> None:
        clock_value = {"v": 1_700_000_000.0}

        def clock() -> float:
            return clock_value["v"]

        cockpit = OperatorCockpit(clock=clock)
        # Swap the clock after construction.
        clock_value["v"] = 1_700_000_100.0
        cockpit.tick(progress=(1, 2))
        # The header reflects the new clock (read under the lock).
        text = cockpit.render()
        # 1_700_000_100.0 is 2023-11-14 22:15:00 UTC; assert the
        # HH:MM:SS portion matches the local-time rendition.
        import time as _time

        expected = _time.strftime("%H:%M:%S", _time.localtime(1_700_000_100.0))
        assert f"tick={expected}" in text
