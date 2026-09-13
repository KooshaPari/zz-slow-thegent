"""Tests for soft deadline support (swarm-soft-deadlines).

@trace FR-ORC-001 -- Soft deadline: preferred completion time per agent task.
@trace FR-ORC-002 -- DeadlineMonitor: background daemon thread; warn + error events.
@trace FR-ORC-003 -- ConcurrencyController.acquire: soft_deadline_s parameter.
"""

from __future__ import annotations

import threading
import time

import pytest

from thegent.orchestration.resource.load_based_limits import (
    DeadlineMonitor,
    SoftDeadline,
    get_deadline_monitor,
)

# ---------------------------------------------------------------------------
# SoftDeadline unit tests
# ---------------------------------------------------------------------------


class TestSoftDeadline:
    """Unit tests for SoftDeadline dataclass. @trace FR-ORC-001"""

    def test_fields_set_correctly(self):
        """SoftDeadline stores run_id, deadline_ts, warn_at_pct."""
        dl = SoftDeadline(run_id="run-1", deadline_ts=60.0, warn_at_pct=0.75)
        assert dl.run_id == "run-1"
        assert dl.deadline_ts == 60.0
        assert dl.warn_at_pct == 0.75

    def test_default_warn_at_pct(self):
        """Default warn_at_pct is 0.8."""
        dl = SoftDeadline(run_id="run-x", deadline_ts=100.0)
        assert dl.warn_at_pct == 0.8

    def test_elapsed_returns_positive(self):
        """elapsed() returns a non-negative float immediately after creation."""
        dl = SoftDeadline(run_id="r", deadline_ts=10.0)
        assert dl.elapsed() >= 0.0

    def test_elapsed_increases_over_time(self):
        """elapsed() grows with wall-clock time."""
        dl = SoftDeadline(run_id="r", deadline_ts=10.0)
        t0 = dl.elapsed()
        time.sleep(0.05)
        t1 = dl.elapsed()
        assert t1 > t0

    def test_warn_threshold(self):
        """warn_threshold() == deadline_ts * warn_at_pct."""
        dl = SoftDeadline(run_id="r", deadline_ts=100.0, warn_at_pct=0.7)
        assert dl.warn_threshold() == pytest.approx(70.0)

    def test_is_warn_zone_false_when_fresh(self):
        """is_warn_zone() is False immediately after creation for a long deadline."""
        dl = SoftDeadline(run_id="r", deadline_ts=1000.0)
        assert not dl.is_warn_zone()

    def test_is_warn_zone_true_for_elapsed_deadline(self):
        """is_warn_zone() is True when deadline started long ago."""
        dl = SoftDeadline(run_id="r", deadline_ts=0.01)
        time.sleep(0.02)
        assert dl.is_warn_zone()

    def test_is_overdue_false_when_fresh(self):
        """is_overdue() is False immediately after creation for a long deadline."""
        dl = SoftDeadline(run_id="r", deadline_ts=1000.0)
        assert not dl.is_overdue()

    def test_is_overdue_true_for_tiny_deadline(self):
        """is_overdue() is True after deadline_ts has elapsed."""
        dl = SoftDeadline(run_id="r", deadline_ts=0.01)
        time.sleep(0.05)
        assert dl.is_overdue()

    def test_initial_flags_are_false(self):
        """_warned and _overdue start as False."""
        dl = SoftDeadline(run_id="r", deadline_ts=100.0)
        assert not dl._warned
        assert not dl._overdue


# ---------------------------------------------------------------------------
# DeadlineMonitor unit tests
# ---------------------------------------------------------------------------


class TestDeadlineMonitorRegisterUnregister:
    """Tests for register/unregister lifecycle. @trace FR-ORC-002"""

    def setup_method(self):
        """Create a fresh monitor for each test (not auto-started)."""
        self.monitor = DeadlineMonitor(interval_s=999.0)  # long interval -- no auto-checks

    def teardown_method(self):
        """Stop the monitor after each test."""
        self.monitor.stop(timeout=1.0)

    def test_register_returns_soft_deadline(self):
        """register() returns a SoftDeadline instance."""
        dl = self.monitor.register("run-a", deadline_ts=30.0)
        assert isinstance(dl, SoftDeadline)
        assert dl.run_id == "run-a"

    def test_register_stores_deadline(self):
        """After register(), active_deadlines() contains the run_id."""
        self.monitor.register("run-b", deadline_ts=60.0)
        active = self.monitor.active_deadlines()
        assert "run-b" in active

    def test_register_replaces_existing(self):
        """Registering the same run_id twice replaces the entry."""
        self.monitor.register("run-c", deadline_ts=10.0, warn_at_pct=0.5)
        self.monitor.register("run-c", deadline_ts=20.0, warn_at_pct=0.9)
        active = self.monitor.active_deadlines()
        assert active["run-c"].deadline_ts == pytest.approx(20.0)
        assert active["run-c"].warn_at_pct == pytest.approx(0.9)

    def test_unregister_removes_entry(self):
        """unregister() removes the run_id from active_deadlines."""
        self.monitor.register("run-d", deadline_ts=5.0)
        self.monitor.unregister("run-d")
        assert "run-d" not in self.monitor.active_deadlines()

    def test_unregister_noop_for_unknown(self):
        """unregister() on unknown run_id does not raise."""
        self.monitor.unregister("nonexistent")  # must not raise

    def test_active_deadlines_returns_copy(self):
        """active_deadlines() returns a shallow copy -- mutations don't affect internal state."""
        self.monitor.register("run-e", deadline_ts=10.0)
        copy = self.monitor.active_deadlines()
        del copy["run-e"]
        assert "run-e" in self.monitor.active_deadlines()


class TestDeadlineMonitorThread:
    """Tests for thread lifecycle. @trace FR-ORC-002"""

    def test_start_spawns_daemon_thread(self):
        """start() creates a daemon thread named DeadlineMonitor."""
        monitor = DeadlineMonitor(interval_s=999.0)
        monitor.start()
        assert monitor.is_running()
        assert monitor._thread is not None
        assert monitor._thread.daemon
        assert monitor._thread.name == "DeadlineMonitor"
        monitor.stop(timeout=1.0)

    def test_start_idempotent(self):
        """Calling start() twice does not create a second thread."""
        monitor = DeadlineMonitor(interval_s=999.0)
        monitor.start()
        t1 = monitor._thread
        monitor.start()
        t2 = monitor._thread
        assert t1 is t2
        monitor.stop(timeout=1.0)

    def test_stop_terminates_thread(self):
        """stop() waits for the thread to exit."""
        monitor = DeadlineMonitor(interval_s=999.0)
        monitor.start()
        assert monitor.is_running()
        monitor.stop(timeout=2.0)
        assert not monitor.is_running()

    def test_stop_before_start_is_noop(self):
        """stop() before start() does not raise."""
        monitor = DeadlineMonitor(interval_s=999.0)
        monitor.stop(timeout=0.1)  # must not raise

    def test_is_running_false_before_start(self):
        """is_running() returns False on a freshly created monitor."""
        monitor = DeadlineMonitor(interval_s=999.0)
        assert not monitor.is_running()


class TestDeadlineMonitorChecks:
    """Tests that the monitor emits the right log events. @trace FR-ORC-002"""

    def test_warn_event_emitted_on_check(self, caplog):
        """_check_all() sets _warned flag when warn zone is reached but not yet overdue."""
        monitor = DeadlineMonitor(interval_s=999.0)
        # Use a large deadline but manipulate _started_at so that elapsed
        # falls between warn_threshold and deadline_ts.
        # deadline=10s, warn_at_pct=0.05 -> warn after 0.5s
        # We back-date _started_at by 1s so elapsed~1s > warn(0.5s) but < 10s
        dl = SoftDeadline(run_id="warn-run", deadline_ts=10.0, warn_at_pct=0.05)
        dl._started_at = time.time() - 1.0  # 1 second elapsed

        assert dl.is_warn_zone()
        assert not dl.is_overdue()

        with monitor._lock:
            monitor._deadlines["warn-run"] = dl

        monitor._check_all()

        # The flag should be flipped; overdue must remain False
        assert dl._warned
        assert not dl._overdue

    def test_error_event_emitted_on_check(self, caplog):
        """_check_all() sets _overdue flag when deadline is exceeded."""
        monitor = DeadlineMonitor(interval_s=999.0)
        dl = SoftDeadline(run_id="overdue-run", deadline_ts=0.001)
        time.sleep(0.01)
        assert dl.is_overdue()

        with monitor._lock:
            monitor._deadlines["overdue-run"] = dl

        monitor._check_all()

        assert dl._overdue

    def test_warn_flag_prevents_duplicate_warn(self):
        """A second _check_all() does not re-set _warned."""
        monitor = DeadlineMonitor(interval_s=999.0)
        dl = SoftDeadline(run_id="dup-warn", deadline_ts=0.001, warn_at_pct=0.5)
        time.sleep(0.005)
        dl._warned = True  # Simulate already warned

        with monitor._lock:
            monitor._deadlines["dup-warn"] = dl

        monitor._check_all()

        # Still true; no double-fire
        assert dl._warned

    def test_overdue_flag_prevents_duplicate_error(self):
        """A second _check_all() does not re-set _overdue."""
        monitor = DeadlineMonitor(interval_s=999.0)
        dl = SoftDeadline(run_id="dup-err", deadline_ts=0.001)
        time.sleep(0.01)
        dl._overdue = True  # Simulate already logged

        with monitor._lock:
            monitor._deadlines["dup-err"] = dl

        monitor._check_all()

        assert dl._overdue

    def test_no_events_for_fresh_deadline(self):
        """No flags set for a deadline well within budget."""
        monitor = DeadlineMonitor(interval_s=999.0)
        dl = SoftDeadline(run_id="fresh", deadline_ts=10000.0)

        with monitor._lock:
            monitor._deadlines["fresh"] = dl

        monitor._check_all()

        assert not dl._warned
        assert not dl._overdue

    def test_real_background_thread_triggers_warn(self):
        """Integration: background thread fires warn event within check interval."""
        warned = threading.Event()
        original_emit = DeadlineMonitor._emit_warn

        def patched_emit(dl, elapsed):
            warned.set()
            original_emit(dl, elapsed)

        monitor = DeadlineMonitor(interval_s=0.05)
        try:
            DeadlineMonitor._emit_warn = staticmethod(patched_emit)
            monitor.start()
            # Register a deadline that will immediately be in warn zone
            monitor.register("bg-warn", deadline_ts=0.001, warn_at_pct=0.5)
            time.sleep(0.05)  # Let thread run at least once after deadline_ts
            assert warned.wait(timeout=1.0), "DeadlineMonitor never fired warn event"
        finally:
            DeadlineMonitor._emit_warn = staticmethod(original_emit)
            monitor.stop(timeout=2.0)

    def test_tasks_never_cancelled(self):
        """Soft deadlines emit logs but do not raise or cancel execution."""
        monitor = DeadlineMonitor(interval_s=0.05)
        monitor.start()
        try:
            monitor.register("no-cancel", deadline_ts=0.001)
            time.sleep(0.15)
            # run_id still present until explicitly unregistered -- task is not cancelled
            monitor.unregister("no-cancel")
        finally:
            monitor.stop(timeout=2.0)
        # Reaching here means no exception was raised -- task not cancelled.


# ---------------------------------------------------------------------------
# Module-level singleton tests
# ---------------------------------------------------------------------------


class TestGetDeadlineMonitor:
    """Tests for the module-level singleton. @trace FR-ORC-002"""

    def test_singleton_is_running(self):
        """get_deadline_monitor() returns an already-started monitor."""
        monitor = get_deadline_monitor()
        assert monitor.is_running()

    def test_singleton_identity(self):
        """Two calls to get_deadline_monitor() return the same object."""
        m1 = get_deadline_monitor()
        m2 = get_deadline_monitor()
        assert m1 is m2

    def test_singleton_register_unregister(self):
        """Can register and unregister via the singleton safely."""
        monitor = get_deadline_monitor()
        monitor.register("singleton-test", deadline_ts=300.0)
        assert "singleton-test" in monitor.active_deadlines()
        monitor.unregister("singleton-test")
        assert "singleton-test" not in monitor.active_deadlines()


# ---------------------------------------------------------------------------
# ConcurrencyController.acquire integration tests
# ---------------------------------------------------------------------------


class TestConcurrencyControllerSoftDeadline:
    """Integration tests for ConcurrencyController.acquire soft_deadline_s param.

    @trace FR-ORC-003
    """

    def _make_controller(self, tmp_path):
        """Create a ConcurrencyController backed by a tmp session dir."""
        from thegent.execution import ConcurrencyController

        return ConcurrencyController(
            session_dir=tmp_path,
            max_concurrency=10,
            use_load_based=False,  # Avoid psutil/resource sampling in unit tests
        )

    def test_acquire_without_deadline_succeeds(self, tmp_path, monkeypatch):
        """acquire() without soft_deadline_s works as before."""
        monkeypatch.setattr(
            "thegent.cli.commands.impl.ps_impl",
            lambda **kwargs: [],  # no active sessions
        )
        ctrl = self._make_controller(tmp_path)
        result = ctrl.acquire(owner="agent-a", run_id="r1")
        assert isinstance(result, bool)

    def test_acquire_with_deadline_registers_in_monitor(self, tmp_path, monkeypatch):
        """acquire() with soft_deadline_s registers deadline when admitted."""
        monkeypatch.setattr("thegent.cli.commands.impl.ps_impl", lambda **kwargs: [])
        ctrl = self._make_controller(tmp_path)

        run_id = "deadline-test-run"
        admitted = ctrl.acquire(
            owner="agent-b",
            run_id=run_id,
            soft_deadline_s=300.0,
            warn_at_pct=0.8,
        )
        monitor = get_deadline_monitor()
        try:
            if admitted:
                assert run_id in monitor.active_deadlines()
                dl = monitor.active_deadlines()[run_id]
                assert dl.deadline_ts == pytest.approx(300.0)
                assert dl.warn_at_pct == pytest.approx(0.8)
        finally:
            monitor.unregister(run_id)

    def test_acquire_blocked_does_not_register(self, tmp_path, monkeypatch):
        """When acquire() is blocked (slot limit hit), no deadline is registered."""
        # Return 100 running sessions so slot_limit is exceeded with max_concurrency=10
        running = [{"status": "running"}] * 100
        monkeypatch.setattr("thegent.cli.commands.impl.ps_impl", lambda **kwargs: running)

        ctrl = self._make_controller(tmp_path)
        run_id = "blocked-run"
        admitted = ctrl.acquire(
            owner="agent-c",
            run_id=run_id,
            soft_deadline_s=60.0,
        )
        assert not admitted
        assert run_id not in get_deadline_monitor().active_deadlines()

    def test_acquire_with_zero_deadline_skips_registration(self, tmp_path, monkeypatch):
        """soft_deadline_s=0 is treated as 'no deadline' (non-positive guard)."""
        monkeypatch.setattr("thegent.cli.commands.impl.ps_impl", lambda **kwargs: [])
        ctrl = self._make_controller(tmp_path)
        run_id = "zero-deadline"
        ctrl.acquire(owner="agent-d", run_id=run_id, soft_deadline_s=0.0)
        assert run_id not in get_deadline_monitor().active_deadlines()

    def test_release_unregisters_deadline(self, tmp_path, monkeypatch):
        """release() removes the soft deadline from the monitor."""
        monkeypatch.setattr("thegent.cli.commands.impl.ps_impl", lambda **kwargs: [])
        ctrl = self._make_controller(tmp_path)
        run_id = "release-run"
        admitted = ctrl.acquire(owner="agent-e", run_id=run_id, soft_deadline_s=300.0)
        if not admitted:
            pytest.skip("slot not acquired -- cannot test release")

        assert run_id in get_deadline_monitor().active_deadlines()
        ctrl.release(owner="agent-e", run_id=run_id, elapsed_ms=100.0)
        assert run_id not in get_deadline_monitor().active_deadlines()

    def test_acquire_uses_owner_as_run_id_fallback(self, tmp_path, monkeypatch):
        """When run_id is empty, owner is used as the deadline key."""
        monkeypatch.setattr("thegent.cli.commands.impl.ps_impl", lambda **kwargs: [])
        ctrl = self._make_controller(tmp_path)
        admitted = ctrl.acquire(
            owner="fallback-owner",
            run_id="",
            soft_deadline_s=300.0,
        )
        monitor = get_deadline_monitor()
        try:
            if admitted:
                assert "fallback-owner" in monitor.active_deadlines()
        finally:
            monitor.unregister("fallback-owner")
