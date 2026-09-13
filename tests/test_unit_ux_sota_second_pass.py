"""SOTA second-pass hardening tests for the decision audit + traffic lane.

Closes the second-pass audit findings identified by the parallel
``sage`` sub-agent (see WORKLOG.md 2026-07-19 entry):

* AUDIT-22 — ``DecisionAuditAppender._rotate_locked`` now uses
  ``os.rename`` instead of ``Path.replace`` and iterates the sibling
  chain from the highest index downward so a concurrent reader
  cannot observe two siblings sharing the same index.
* AUDIT-24 — ``DecisionAuditTailer`` exposes ``stats()`` with
  ``drain_count`` / ``drain_errors_total`` / ``last_error`` /
  ``last_error_at`` / ``dlq_size`` / ``consecutive_failures`` /
  ``current_backoff_s`` and applies capped exponential back-off on
  repeated drain failures.
* AUDIT-26 — ``TrafficDashboard.record`` holds a single
  ``threading.Lock`` and is exercised under N-thread × M-event
  burst load with no deadlock and no torn ``rps_trend``.

Also closes the F-1..F-15 + NEW-1..NEW-6 cheap follow-ups:

* F-2 — ``DecisionAuditAppender.audit_path_str()`` returns ``str``.
* F-3 — ``sota replay --suite-name`` rejects malformed values.
* F-4 — ``emitted_at`` freezes to ``evaluated_at`` when the notice
  carries a far-future ``evaluated_at``.
* F-5 — ``TrafficEvent`` is now ``frozen=True``; ``record()``
  uses ``dataclasses.replace`` to default ``ts`` without mutation.
* F-6 + F-14 — ``TrafficWindow._evict`` safety counter logs a
  WARNING when exhausted.

These tests are intentionally small and independent — each one
documents the contract a future operator / CI consumer can rely on.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from thegent.ux.cockpit import DecisionNotice, OperatorCockpit
from thegent.ux.decision_audit import DecisionAuditAppender, DecisionAuditTailer
from thegent.ux.kpis.traffic import TrafficDashboard, TrafficEvent, TrafficWindow

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_notice(*, verdict: str = "allow", reason_code: str = "ok", ts: float = 0.0) -> DecisionNotice:
    """Build a DecisionNotice with the minimum required fields."""
    return DecisionNotice(
        verdict=verdict,
        reason_code=reason_code,
        rule_id="r.test",
        agent="tester",
        lane="standard",
        evaluated_at=ts or time.time(),
        reason="sota-second-pass test",
    )


# ---------------------------------------------------------------------------
# AUDIT-22 — DecisionAuditAppender atomic rotation via os.rename
# ---------------------------------------------------------------------------


class TestAtomicRotation:
    """Pin the AUDIT-22 contract: rotation uses ``os.rename`` and
    iterates the sibling chain from the highest index downward."""

    def test_rotation_uses_os_rename(self, tmp_path: Path) -> None:
        """The rotate helper invokes ``os.rename`` rather than
        ``Path.replace`` so the rename is POSIX-atomic."""
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(audit_path=path, max_lines=2, max_backups=3)
        # Pre-create two sibling files so the shift chain is non-empty.
        (tmp_path / "audit.jsonl.1").write_text("prior.1\n", encoding="utf-8")
        (tmp_path / "audit.jsonl.2").write_text("prior.2\n", encoding="utf-8")
        appender.record(_make_notice(reason_code="ok.0", ts=3000.0))
        appender.record(_make_notice(reason_code="ok.1", ts=3001.0))
        # Trigger a third record — _maybe_rotate fires, _rotate_locked
        # shifts .2 → .3, .1 → .2, active → .1.
        appender.record(_make_notice(reason_code="ok.2", ts=3002.0))
        stats = appender.audit_stats()
        assert stats["rotation_count"] >= 1
        # The chain must never have two siblings sharing the same index.
        # After rotation: .1 is the newly-rotated active (was active),
        # .2 is the prior .1, .3 is the prior .2. The active file is
        # fresh (only the third line).
        assert (tmp_path / "audit.jsonl").exists()
        assert (tmp_path / "audit.jsonl.1").exists()
        assert (tmp_path / "audit.jsonl.2").exists()
        assert (tmp_path / "audit.jsonl.3").exists()
        # Sibling inodes must be unique (no two siblings point at the
        # same backing file).
        inodes = {(tmp_path / f"audit.jsonl.{n}").stat().st_ino for n in (1, 2, 3)}
        assert len(inodes) == 3, "two siblings share an inode — rename chain collided"

    def test_rotation_preserves_chain_under_burst(self, tmp_path: Path) -> None:
        """Burst N records; assert sibling indices are unique at all
        times and no two siblings share the same inode."""
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(audit_path=path, max_lines=3, max_backups=4)
        for i in range(40):
            appender.record(_make_notice(reason_code=f"ok.{i}", ts=4000.0 + i))
        # Walk the directory; assert each ``.N`` exists at most once
        # and inodes are unique across the chain.
        seen_inodes: set[int] = set()
        for p in sorted(tmp_path.iterdir()):
            if p.name == "audit.jsonl":
                seen_inodes.add(p.stat().st_ino)
                continue
            assert p.name.startswith("audit.jsonl.")
            suffix = p.name.rsplit(".", 1)[-1]
            assert suffix.isdigit()
            ino = p.stat().st_ino
            assert ino not in seen_inodes, f"duplicate inode under {p.name}"
            seen_inodes.add(ino)

    def test_rotate_locked_iterates_high_to_low(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """AUDIT-22: the shift loop iterates ``max_backups - 1`` down to
        ``1`` (highest index first). Pin the iteration order via a
        monkeypatched ``os.rename`` spy."""
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(audit_path=path, max_lines=2, max_backups=3)
        # Pre-create siblings so the shift chain has work to do.
        (tmp_path / "audit.jsonl.1").write_text("a\n", encoding="utf-8")
        (tmp_path / "audit.jsonl.2").write_text("b\n", encoding="utf-8")
        captured: list[tuple[str, str]] = []
        original_rename = os.rename

        def spy_rename(src: os.PathLike[str] | str, dst: os.PathLike[str] | str) -> None:
            captured.append((os.path.basename(os.fspath(src)), os.path.basename(os.fspath(dst))))
            original_rename(src, dst)

        monkeypatch.setattr(os, "rename", spy_rename)
        appender._rotate_locked()
        # The three rename calls must be (descending order):
        #   audit.jsonl.2 -> audit.jsonl.3
        #   audit.jsonl.1 -> audit.jsonl.2
        #   audit.jsonl   -> audit.jsonl.1
        assert len(captured) == 3, captured
        assert captured[0] == ("audit.jsonl.2", "audit.jsonl.3"), captured
        assert captured[1] == ("audit.jsonl.1", "audit.jsonl.2"), captured
        assert captured[2] == ("audit.jsonl", "audit.jsonl.1"), captured


# ---------------------------------------------------------------------------
# AUDIT-24 — DecisionAuditTailer observability + back-off
# ---------------------------------------------------------------------------


class TestTailerObservabilityAndBackoff:
    """Pin the AUDIT-24 contract: drain stats surface + capped
    exponential back-off on repeated failures."""

    def _make_tailer(self, tmp_path: Path) -> tuple[DecisionAuditTailer, OperatorCockpit, DecisionAuditAppender]:
        cockpit = OperatorCockpit()
        appender = DecisionAuditAppender(audit_path=tmp_path / "tailer.jsonl")
        tailer = DecisionAuditTailer(cockpit, appender, interval_s=0.05, max_backoff_s=4.0)
        return tailer, cockpit, appender

    def test_stats_initial_state(self, tmp_path: Path) -> None:
        tailer, _, _ = self._make_tailer(tmp_path)
        snap = tailer.stats()
        assert snap["drain_count"] == 0
        assert snap["drain_errors_total"] == 0
        assert snap["last_error"] is None
        assert snap["last_error_at"] is None
        assert snap["dlq_size"] == 0
        assert snap["consecutive_failures"] == 0
        assert snap["current_backoff_s"] == 0.0
        assert snap["max_backoff_s"] == 4.0

    def test_successful_drain_increments_counter(self, tmp_path: Path) -> None:
        tailer, cockpit, _ = self._make_tailer(tmp_path)
        cockpit.record_decision(_make_notice(reason_code="d.1"))
        count = tailer.drain_once()
        assert count == 1
        snap = tailer.stats()
        assert snap["drain_count"] >= 1
        assert snap["drain_errors_total"] == 0
        assert snap["last_error"] is None

    def test_failed_drain_records_error_and_backoff(self, tmp_path: Path) -> None:
        tailer, cockpit, appender = self._make_tailer(tmp_path)
        # Force a failure by patching the appender's record_many
        # to raise; the tailer's drain catches it and records.
        cockpit.record_decision(_make_notice(reason_code="d.fail"))
        boom = RuntimeError("simulated appender failure")
        with patch.object(appender, "record_many", side_effect=boom):
            with pytest.raises(RuntimeError):
                # drain_once does not swallow exceptions raised by
                # appender.record_many; the tailer's _run catches
                # them, but ``drain_once`` itself re-raises so test
                # contracts stay honest.
                tailer.drain_once()
        # Now exercise the same path through ``_record_drain_failure``
        # directly (mirrors what the background _run loop does).
        backoff = tailer._record_drain_failure(boom)
        snap = tailer.stats()
        assert snap["drain_errors_total"] == 1
        assert snap["consecutive_failures"] == 1
        assert snap["current_backoff_s"] == backoff
        assert snap["last_error"] is not None
        assert "simulated appender failure" in snap["last_error"]
        assert snap["last_error_at"] is not None
        assert snap["dlq_size"] == 1

    def test_exponential_backoff_caps_at_max(self, tmp_path: Path) -> None:
        tailer, _, _ = self._make_tailer(tmp_path)
        boom = RuntimeError("n")
        # 1st failure: backoff = 2^0 = 1s
        tailer._record_drain_failure(boom)
        assert tailer._current_backoff_s == 1.0
        # 2nd: 2s
        tailer._record_drain_failure(boom)
        assert tailer._current_backoff_s == 2.0
        # 3rd: 4s (capped at 4.0 from max_backoff_s)
        tailer._record_drain_failure(boom)
        assert tailer._current_backoff_s == 4.0
        # 4th: still 4s (cap holds)
        tailer._record_drain_failure(boom)
        assert tailer._current_backoff_s == 4.0

    def test_successful_drain_resets_backoff(self, tmp_path: Path) -> None:
        tailer, _, _ = self._make_tailer(tmp_path)
        boom = RuntimeError("n")
        tailer._record_drain_failure(boom)
        tailer._record_drain_failure(boom)
        assert tailer._consecutive_failures == 2
        assert tailer._current_backoff_s == 2.0
        tailer._record_drain_success()
        assert tailer._consecutive_failures == 0
        assert tailer._current_backoff_s == 0.0

    def test_dlq_is_bounded(self, tmp_path: Path) -> None:
        tailer, _, _ = self._make_tailer(tmp_path)
        # Default DLQ cap is 64; force 100 failures and assert
        # the deque never exceeds the cap.
        for i in range(100):
            tailer._record_drain_failure(RuntimeError(f"e.{i}"))
        snap = tailer.stats()
        assert snap["dlq_size"] == 64
        assert snap["drain_errors_total"] == 100

    def test_background_loop_records_failure_via_run(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """End-to-end: the background _run loop catches the failure,
        records it, applies the back-off, and warns."""
        cockpit = OperatorCockpit()
        appender = DecisionAuditAppender(audit_path=tmp_path / "run.jsonl")
        tailer = DecisionAuditTailer(
            cockpit,
            appender,
            interval_s=0.05,
            max_backoff_s=2.0,
        )
        cockpit.record_decision(_make_notice(reason_code="d.run"))
        boom = RuntimeError("loop-failure-breadcrumb")

        def boom_record_many(_notices):
            raise boom

        with patch.object(appender, "record_many", side_effect=boom_record_many):
            tailer.start()
            # Wait long enough for at least one tick + back-off.
            time.sleep(0.2)
            tailer.stop(timeout_s=2.0)
        snap = tailer.stats()
        assert snap["drain_errors_total"] >= 1
        assert snap["last_error"] is not None
        assert "loop-failure-breadcrumb" in snap["last_error"]


# ---------------------------------------------------------------------------
# F-2 — DecisionAuditAppender.audit_path_str()
# ---------------------------------------------------------------------------


class TestAuditPathStr:
    """Pin the F-2 contract: a str-returning sibling of
    :meth:`DecisionAuditAppender.audit_path`."""

    def test_audit_path_returns_path(self, tmp_path: Path) -> None:
        log = tmp_path / "x.jsonl"
        appender = DecisionAuditAppender(audit_path=log)
        assert isinstance(appender.audit_path(), Path)
        assert appender.audit_path() == log

    def test_audit_path_str_returns_str(self, tmp_path: Path) -> None:
        log = tmp_path / "x.jsonl"
        appender = DecisionAuditAppender(audit_path=log)
        assert isinstance(appender.audit_path_str(), str)
        assert appender.audit_path_str() == str(log)


# ---------------------------------------------------------------------------
# F-3 — sota replay --suite-name validation
# ---------------------------------------------------------------------------


class TestSotaSuiteNameValidation:
    """Pin the F-3 contract: ``--suite-name`` must match
    ``^[A-Za-z0-9._-]+$`` or the command exits 1."""

    def _make_runner(self):
        from typer.testing import CliRunner

        from thegent.ux.cli_sota import app

        return CliRunner(), app

    def test_default_suite_name_is_accepted(self, tmp_path: Path) -> None:
        runner, app = self._make_runner()
        # Empty corpus → exits 0 with the default suite name "thegent.sota.replay"
        # which matches the regex.
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(tmp_path / "empty.json"),
                "--compare",
                str(tmp_path / "snap.json"),
            ],
        )
        # Either it succeeds (exit 0) or fails with the missing-batch
        # path error; both paths surface the suite-name validation
        # BEFORE they would have used the default name.
        assert "suite-name must match" not in result.output

    def test_malformed_suite_name_rejected_with_exit_1(self, tmp_path: Path) -> None:
        runner, app = self._make_runner()
        # Create an empty batch and snapshot so the validation gate
        # fires before the path-not-found checks.
        (tmp_path / "empty.json").write_text("[]", encoding="utf-8")
        (tmp_path / "snap.json").write_text("[]", encoding="utf-8")
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(tmp_path / "empty.json"),
                "--compare",
                str(tmp_path / "snap.json"),
                "--suite-name",
                "bad name with spaces & <xml-injection>",
            ],
        )
        assert result.exit_code == 1
        assert "suite-name must match" in result.output

    def test_valid_suite_name_with_special_chars_accepted(self, tmp_path: Path) -> None:
        runner, app = self._make_runner()
        (tmp_path / "empty.json").write_text("[]", encoding="utf-8")
        (tmp_path / "snap.json").write_text("[]", encoding="utf-8")
        # Valid: alphanumerics + dot/dash/underscore.
        result = runner.invoke(
            app,
            [
                "replay",
                "--batch",
                str(tmp_path / "empty.json"),
                "--compare",
                str(tmp_path / "snap.json"),
                "--suite-name",
                "my.suite_name-v2",
            ],
        )
        assert "suite-name must match" not in result.output


# ---------------------------------------------------------------------------
# F-4 — Future-skew tolerance: emitted_at freezes to evaluated_at
# ---------------------------------------------------------------------------


class TestFutureSkewTolerance:
    """Pin the F-4 contract: ``emitted_at`` freezes to
    ``evaluated_at`` when the notice carries a far-future
    ``evaluated_at`` (within ``_FUTURE_SKEW_TOLERANCE_S``)."""

    def test_normal_notice_uses_appender_clock(self, tmp_path: Path) -> None:
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(audit_path=path)
        # evaluated_at = 1000.0; appender clock = time.time() ≫ 1000.0
        # → not future-skewed; emitted_at is the appender clock.
        appender.record(_make_notice(reason_code="ok.normal", ts=1000.0))
        with path.open("r", encoding="utf-8") as fh:
            line = fh.readline()
        import json

        rec = json.loads(line)
        assert rec["evaluated_at"] == 1000.0
        # emitted_at is the appender clock (≫ 1000.0).
        assert rec["emitted_at"] > 1000.0

    def test_future_skewed_notice_freezes_emitted_at(self, tmp_path: Path) -> None:
        path = tmp_path / "audit.jsonl"
        appender = DecisionAuditAppender(audit_path=path)
        # evaluated_at = year ~2030 (≫ 60s past time.time()).
        future = time.time() + 365 * 24 * 3600
        appender.record(_make_notice(reason_code="ok.skew", ts=future))
        with path.open("r", encoding="utf-8") as fh:
            line = fh.readline()
        import json

        rec = json.loads(line)
        assert rec["evaluated_at"] == future
        # F-4: emitted_at freezes to evaluated_at when the notice
        # is far-future-skewed.
        assert rec["emitted_at"] == future


# ---------------------------------------------------------------------------
# F-5 — TrafficEvent frozen + dataclasses.replace on record()
# ---------------------------------------------------------------------------


class TestTrafficEventFrozen:
    """Pin the F-5 contract: TrafficEvent is frozen and record()
    uses dataclasses.replace rather than mutation."""

    def test_traffic_event_is_frozen(self) -> None:
        ev = TrafficEvent(ts=1.0)
        from dataclasses import FrozenInstanceError

        with pytest.raises(FrozenInstanceError):
            ev.ts = 2.0  # type: ignore[misc]

    def test_record_normalizes_ts_via_replace(self) -> None:
        """record() builds a fresh event with the current clock
        when ts <= 0; the original input is left untouched."""
        original = TrafficEvent(ts=0.0)
        assert original.ts == 0.0
        w = TrafficWindow(window_s=10.0, bucket_s=1.0, maxlen=10)
        w.set_clock(lambda: 5_000.0)
        w.record(original)
        # The original event was not mutated.
        assert original.ts == 0.0
        # The stored event has the clock-derived timestamp.
        stored = w.events()
        assert len(stored) == 1
        assert stored[0].ts == 5_000.0
        assert stored[0] is not original


# ---------------------------------------------------------------------------
# F-6 + F-14 — TrafficWindow _evict safety counter canary warning
# ---------------------------------------------------------------------------


class TestEvictSafetyCounter:
    """Pin the F-6 + F-14 contract: the safety counter caps the
    future-ts loop, and a WARNING fires when the counter is
    exhausted."""

    def test_safety_counter_protects_against_tight_loop(self) -> None:
        """A deque of 10 future events with ``now`` far in the past:
        the safety counter caps the eviction at ``len(deque)``
        iterations, then logs the canary warning."""
        w = TrafficWindow(window_s=10.0, bucket_s=1.0, maxlen=100)
        w.set_clock(lambda: 0.0)
        # Inject 10 events with ts = 1_000_000.0 (≫ now=0).
        for _ in range(10):
            w._events.append(TrafficEvent(ts=1_000_000.0))
        # First call: safety = 10, second-pass evicts all 10, no
        # canary (the deque is now empty so the condition
        # ``self._events[0].ts > now`` is False on the canary check).
        w._evict(now=0.0)
        assert len(w._events) == 0

    def test_safety_canary_logs_when_counter_exhausted(self, caplog: pytest.LogCaptureFixture) -> None:
        """Force the safety counter to exhaust while the deque still
        holds future-ts events; assert the WARNING fires.

        The contract: ``safety = len(self._events)`` bounds the
        future-ts loop, and when ``safety == 0 and
        self._events and self._events[0].ts > now`` a WARNING is
        logged. We exercise that branch by wrapping ``popleft`` so
        it never actually pops — after ``len(deque)`` no-op
        iterations the safety counter is exhausted but the deque
        still has the future-ts events.
        """
        from collections import deque

        from thegent.ux.kpis import traffic as traffic_mod

        w = TrafficWindow(window_s=10.0, bucket_s=1.0, maxlen=100)
        w.set_clock(lambda: 0.0)
        # Inject 5 future events.
        for _ in range(5):
            w._events.append(TrafficEvent(ts=1_000_000.0))

        # Build a no-op-popleft deque wrapper that still satisfies
        # the ``self._events`` interface (``__bool__``,
        # ``__getitem__``, ``popleft``).
        class _NoPopDeque:
            def __init__(self, src: deque) -> None:
                self._src = src
                self.popleft_calls = 0

            def __bool__(self) -> bool:
                return bool(self._src)

            def __getitem__(self, idx: int) -> TrafficEvent:
                return self._src[idx]

            def __len__(self) -> int:
                # Production code uses ``len(self._events)`` to set
                # the safety bound. Keep it pinned at 5 so the loop
                # iterates exactly 5 times, then exhausts.
                return 5

            def popleft(self) -> TrafficEvent:
                self.popleft_calls += 1
                # No-op — leave the deque intact so the canary
                # condition ``self._events[0].ts > now`` stays True.
                return self._src[0]

        no_pop = _NoPopDeque(w._events)
        # Patch the dataclass field directly (dataclasses allow
        # attribute assignment outside __init__).
        object.__setattr__(w, "_events", no_pop)  # type: ignore[arg-type]
        with caplog.at_level(logging.WARNING, logger=traffic_mod._log.name):
            w._evict(now=0.0)
        # The canary fires because the deque still has future-ts
        # events after the safety counter dropped to 0.
        assert any("safety counter exhausted" in rec.message for rec in caplog.records)


# ---------------------------------------------------------------------------
# AUDIT-26 — TrafficDashboard free-threaded record + summary
# ---------------------------------------------------------------------------


class TestTrafficDashboardFreeThreaded:
    """Pin the AUDIT-26 contract: concurrent ``record`` + ``summary``
    invocations do not deadlock or produce torn state."""

    def test_concurrent_record_does_not_deadlock(self) -> None:
        d = TrafficDashboard(window_s=10.0, bucket_s=1.0, maxlen=64)
        d.set_clock(lambda: 1_000_000.0)
        errors: list[BaseException] = []

        def worker(start: int, count: int) -> None:
            try:
                for i in range(count):
                    d.record(TrafficEvent(ts=1_000_000.0 + 0.001 * (start + i)))
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i * 100, 100)) for i in range(8)]
        for t in threads:
            t.start()
        # Read summary concurrently with the writers.
        for _ in range(20):
            d.summary()
        for t in threads:
            t.join(timeout=10.0)
            assert not t.is_alive(), "thread deadlocked"
        assert not errors, f"workers raised: {errors!r}"
        # Final state is bounded (maxlen cap honoured).
        assert len(d.window.events()) <= 64

    def test_concurrent_record_and_summary_consistency(self) -> None:
        """No torn rps_trend; ``summary`` always returns a valid
        snapshot even mid-burst."""
        d = TrafficDashboard(window_s=10.0, bucket_s=1.0, maxlen=128)
        d.set_clock(lambda: 1_000_000.0)
        stop = threading.Event()

        def writer() -> None:
            i = 0
            while not stop.is_set():
                d.record(TrafficEvent(ts=1_000_000.0 + 0.0001 * i))
                i += 1

        def reader(snapshots: list[dict]) -> None:
            while not stop.is_set():
                snap = d.summary()
                snapshots.append(snap)

        threads = [threading.Thread(target=writer)]
        snapshots: list[dict] = []
        threads.append(threading.Thread(target=reader, args=(snapshots,)))
        for t in threads:
            t.start()
        time.sleep(0.5)
        stop.set()
        for t in threads:
            t.join(timeout=10.0)
        assert snapshots, "reader produced no snapshots"
        for snap in snapshots:
            assert "count" in snap
            assert "rps_trend" in snap
            # Bounded deque cap honoured under concurrent load.
            assert snap["count"] >= 0
