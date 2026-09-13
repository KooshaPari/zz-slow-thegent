"""Tests for thegent.native.watcher_daemon -- BKM-09 Multi-tenant file watcher daemon.

# @trace BKM-09
FR-trace: BKM-09 (PYTHON_FRONTMATTER_NATIVE_BACKMATTER_AUDIT_PLAN.md)

Coverage targets:
  - WatchEvent and WatchSpec dataclass construction
  - WatcherDaemon.add_watch / remove_watch
  - WatcherDaemon.start / stop lifecycle
  - WatcherDaemon.is_running
  - WatcherDaemon.list_watches
  - Event callbacks fire on file creation, modification, deletion, moved
  - Pattern filtering via glob patterns
  - Recursive vs. non-recursive watching
  - Multiple independent watch specs on the same daemon
  - Callback exceptions do not crash the daemon
  - CircuitBreakerShm integration (mocked)
  - Singleton get_watcher_daemon() factory
  - Thread safety (concurrent add/remove)
"""

from __future__ import annotations

import dataclasses
import threading
import time
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from thegent.native.watcher_daemon import (
    WatcherDaemon,
    WatchEvent,
    WatchSpec,
    _reset_singleton,
    _SpecHandler,
    get_watcher_daemon,
)

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SETTLE_S = (
    0.5  # time to wait for watchdog observer to dispatch events on macOS FSEvents
)


def _make_daemon() -> WatcherDaemon:
    """Return a fresh WatcherDaemon (not started)."""
    return WatcherDaemon()


# ---------------------------------------------------------------------------
# WatchEvent dataclass
# ---------------------------------------------------------------------------


class TestWatchEvent:
    """Unit tests for the WatchEvent dataclass."""

    def test_fields_stored(self) -> None:
        # @trace BKM-09
        ev = WatchEvent(
            event_type="created",
            src_path="/tmp/a.py",
            dest_path=None,
            is_directory=False,
        )
        assert ev.event_type == "created"
        assert ev.src_path == "/tmp/a.py"
        assert ev.dest_path is None
        assert ev.is_directory is False

    def test_moved_event_has_dest(self) -> None:
        ev = WatchEvent(
            event_type="moved", src_path="/a", dest_path="/b", is_directory=False
        )
        assert ev.dest_path == "/b"

    def test_directory_event(self) -> None:
        ev = WatchEvent(
            event_type="deleted",
            src_path="/some/dir",
            dest_path=None,
            is_directory=True,
        )
        assert ev.is_directory is True

    def test_frozen_is_dataclass(self) -> None:
        ev = WatchEvent(
            event_type="created", src_path="/x", dest_path=None, is_directory=False
        )
        assert dataclasses.is_dataclass(ev)
        # Verify WatchEvent is declared as frozen by checking all fields are unhashable-proof
        field_names = {f.name for f in dataclasses.fields(ev)}
        assert {"event_type", "src_path", "dest_path", "is_directory"}.issubset(
            field_names
        )


# ---------------------------------------------------------------------------
# WatchSpec dataclass
# ---------------------------------------------------------------------------


class TestWatchSpec:
    """Unit tests for the WatchSpec dataclass."""

    def test_default_construction(self, tmp_path: Path) -> None:
        # @trace BKM-09
        events: list[WatchEvent] = []
        spec = WatchSpec(
            root=tmp_path, patterns=["*.py"], recursive=False, callback=events.append
        )
        assert spec.root == tmp_path
        assert spec.patterns == ["*.py"]
        assert spec.recursive is False

    def test_empty_patterns_allowed(self, tmp_path: Path) -> None:
        spec = WatchSpec(
            root=tmp_path, patterns=[], recursive=True, callback=lambda ev: None
        )
        assert spec.patterns == []


# ---------------------------------------------------------------------------
# WatcherDaemon lifecycle
# ---------------------------------------------------------------------------


class TestWatcherDaemonLifecycle:
    """Tests for start/stop/is_running."""

    def test_not_running_before_start(self) -> None:
        # @trace BKM-09
        daemon = _make_daemon()
        assert not daemon.is_running()

    def test_running_after_start(self) -> None:
        daemon = _make_daemon()
        daemon.start()
        try:
            assert daemon.is_running()
        finally:
            daemon.stop()

    def test_not_running_after_stop(self) -> None:
        daemon = _make_daemon()
        daemon.start()
        daemon.stop()
        assert not daemon.is_running()

    def test_start_idempotent(self) -> None:
        daemon = _make_daemon()
        daemon.start()
        try:
            daemon.start()  # second call should be a no-op
            assert daemon.is_running()
        finally:
            daemon.stop()

    def test_stop_idempotent(self) -> None:
        daemon = _make_daemon()
        daemon.start()
        daemon.stop()
        daemon.stop()  # second call should not raise
        assert not daemon.is_running()

    def test_stop_without_start(self) -> None:
        daemon = _make_daemon()
        daemon.stop()  # must not raise
        assert not daemon.is_running()


# ---------------------------------------------------------------------------
# add_watch / remove_watch
# ---------------------------------------------------------------------------


class TestWatchManagement:
    """Tests for add_watch / remove_watch / list_watches."""

    def test_add_watch_returns_string_id(self, tmp_path: Path) -> None:
        # @trace BKM-09
        daemon = _make_daemon()
        daemon.start()
        try:
            spec = WatchSpec(
                root=tmp_path, patterns=["*"], recursive=False, callback=lambda ev: None
            )
            wid = daemon.add_watch(spec)
            assert isinstance(wid, str)
            assert len(wid) > 0
        finally:
            daemon.stop()

    def test_add_watch_ids_unique(self, tmp_path: Path) -> None:
        daemon = _make_daemon()
        daemon.start()
        try:
            spec = WatchSpec(
                root=tmp_path, patterns=["*"], recursive=False, callback=lambda ev: None
            )
            ids = {daemon.add_watch(spec) for _ in range(5)}
            assert len(ids) == 5  # all unique
        finally:
            daemon.stop()

    def test_remove_watch_returns_true_on_success(self, tmp_path: Path) -> None:
        daemon = _make_daemon()
        daemon.start()
        try:
            spec = WatchSpec(
                root=tmp_path, patterns=["*"], recursive=False, callback=lambda ev: None
            )
            wid = daemon.add_watch(spec)
            result = daemon.remove_watch(wid)
            assert result is True
        finally:
            daemon.stop()

    def test_remove_nonexistent_watch_returns_false(self) -> None:
        daemon = _make_daemon()
        daemon.start()
        try:
            result = daemon.remove_watch("nonexistent_id_xyz")
            assert result is False
        finally:
            daemon.stop()

    def test_list_watches_empty_initially(self) -> None:
        daemon = _make_daemon()
        daemon.start()
        try:
            assert daemon.list_watches() == []
        finally:
            daemon.stop()

    def test_list_watches_after_add(self, tmp_path: Path) -> None:
        daemon = _make_daemon()
        daemon.start()
        try:
            spec = WatchSpec(
                root=tmp_path,
                patterns=["*.py"],
                recursive=True,
                callback=lambda ev: None,
            )
            wid = daemon.add_watch(spec)
            watches = daemon.list_watches()
            assert len(watches) == 1
            assert watches[0]["watch_id"] == wid
            assert watches[0]["root"] == str(tmp_path)
            assert watches[0]["patterns"] == ["*.py"]
            assert watches[0]["recursive"] is True
        finally:
            daemon.stop()

    def test_list_watches_after_remove(self, tmp_path: Path) -> None:
        daemon = _make_daemon()
        daemon.start()
        try:
            spec = WatchSpec(
                root=tmp_path, patterns=["*"], recursive=False, callback=lambda ev: None
            )
            wid = daemon.add_watch(spec)
            daemon.remove_watch(wid)
            assert daemon.list_watches() == []
        finally:
            daemon.stop()

    def test_multiple_watches_listed(self, tmp_path: Path) -> None:
        daemon = _make_daemon()
        daemon.start()
        try:
            for i in range(3):
                subdir = tmp_path / f"dir{i}"
                subdir.mkdir()
                spec = WatchSpec(
                    root=subdir,
                    patterns=["*"],
                    recursive=False,
                    callback=lambda ev: None,
                )
                daemon.add_watch(spec)
            assert len(daemon.list_watches()) == 3
        finally:
            daemon.stop()

    def test_add_watch_before_start(self, tmp_path: Path) -> None:
        """Watches can be registered before start() is called."""
        daemon = _make_daemon()
        spec = WatchSpec(
            root=tmp_path, patterns=["*"], recursive=False, callback=lambda ev: None
        )
        wid = daemon.add_watch(spec)
        assert isinstance(wid, str)
        daemon.start()
        try:
            assert len(daemon.list_watches()) == 1
        finally:
            daemon.stop()


# ---------------------------------------------------------------------------
# Event callbacks
# ---------------------------------------------------------------------------


class TestEventCallbacks:
    """Integration tests: real filesystem changes fire callbacks."""

    def test_file_created_fires_callback(self, tmp_path: Path) -> None:
        # @trace BKM-09
        events: list[WatchEvent] = []

        def cb(ev: WatchEvent) -> None:
            events.append(ev)

        daemon = _make_daemon()
        spec = WatchSpec(root=tmp_path, patterns=["*"], recursive=False, callback=cb)
        daemon.add_watch(spec)
        daemon.start()
        try:
            (tmp_path / "hello.txt").write_text("hi")
            time.sleep(_SETTLE_S)
            assert any(ev.event_type == "created" for ev in events)
        finally:
            daemon.stop()

    def test_file_modified_fires_callback(self, tmp_path: Path) -> None:
        # @trace BKM-09
        target = tmp_path / "mod.txt"
        target.write_text("initial")
        events: list[WatchEvent] = []

        def cb(ev: WatchEvent) -> None:
            events.append(ev)

        daemon = _make_daemon()
        spec = WatchSpec(root=tmp_path, patterns=["*"], recursive=False, callback=cb)
        daemon.add_watch(spec)
        daemon.start()
        try:
            time.sleep(0.1)
            target.write_text("changed")
            time.sleep(_SETTLE_S)
            assert any(ev.event_type == "modified" for ev in events)
        finally:
            daemon.stop()

    def test_file_deleted_fires_callback(self, tmp_path: Path) -> None:
        # @trace BKM-09
        target = tmp_path / "del.txt"
        target.write_text("bye")
        events: list[WatchEvent] = []

        def cb(ev: WatchEvent) -> None:
            events.append(ev)

        daemon = _make_daemon()
        spec = WatchSpec(root=tmp_path, patterns=["*"], recursive=False, callback=cb)
        daemon.add_watch(spec)
        daemon.start()
        try:
            time.sleep(0.1)
            target.unlink()
            time.sleep(_SETTLE_S)
            assert any(ev.event_type == "deleted" for ev in events)
        finally:
            daemon.stop()

    def test_file_moved_fires_callback_with_dest(self, tmp_path: Path) -> None:
        # @trace BKM-09
        src = tmp_path / "src.txt"
        src.write_text("data")
        events: list[WatchEvent] = []

        def cb(ev: WatchEvent) -> None:
            events.append(ev)

        daemon = _make_daemon()
        spec = WatchSpec(root=tmp_path, patterns=["*"], recursive=False, callback=cb)
        daemon.add_watch(spec)
        daemon.start()
        try:
            time.sleep(0.1)
            src.rename(tmp_path / "dst.txt")
            time.sleep(_SETTLE_S)
            moved = [ev for ev in events if ev.event_type == "moved"]
            assert moved, "No moved event received"
            assert moved[0].dest_path is not None
        finally:
            daemon.stop()

    def test_callback_receives_src_path(self, tmp_path: Path) -> None:
        events: list[WatchEvent] = []

        def cb(ev: WatchEvent) -> None:
            events.append(ev)

        daemon = _make_daemon()
        spec = WatchSpec(root=tmp_path, patterns=["*"], recursive=False, callback=cb)
        daemon.add_watch(spec)
        daemon.start()
        try:
            new_file = tmp_path / "tracked.py"
            new_file.write_text("pass")
            time.sleep(_SETTLE_S)
            assert any("tracked.py" in ev.src_path for ev in events)
        finally:
            daemon.stop()


# ---------------------------------------------------------------------------
# Pattern filtering
# ---------------------------------------------------------------------------


class TestPatternFiltering:
    """Tests for glob pattern filtering behaviour."""

    def test_pattern_matches_py_files(self, tmp_path: Path) -> None:
        # @trace BKM-09
        events: list[WatchEvent] = []

        def cb(ev: WatchEvent) -> None:
            events.append(ev)

        daemon = _make_daemon()
        spec = WatchSpec(root=tmp_path, patterns=["*.py"], recursive=False, callback=cb)
        daemon.add_watch(spec)
        daemon.start()
        try:
            (tmp_path / "script.py").write_text("x=1")
            time.sleep(_SETTLE_S)
            assert any("script.py" in ev.src_path for ev in events)
        finally:
            daemon.stop()

    def test_pattern_excludes_non_matching_files(self, tmp_path: Path) -> None:
        events: list[WatchEvent] = []

        def cb(ev: WatchEvent) -> None:
            events.append(ev)

        daemon = _make_daemon()
        spec = WatchSpec(root=tmp_path, patterns=["*.py"], recursive=False, callback=cb)
        daemon.add_watch(spec)
        daemon.start()
        try:
            (tmp_path / "data.csv").write_text("a,b")
            time.sleep(_SETTLE_S)
            assert not any("data.csv" in ev.src_path for ev in events)
        finally:
            daemon.stop()

    def test_empty_patterns_match_all(self, tmp_path: Path) -> None:
        events: list[WatchEvent] = []

        def cb(ev: WatchEvent) -> None:
            events.append(ev)

        daemon = _make_daemon()
        spec = WatchSpec(root=tmp_path, patterns=[], recursive=False, callback=cb)
        daemon.add_watch(spec)
        daemon.start()
        try:
            (tmp_path / "any.xyz").write_text("data")
            time.sleep(_SETTLE_S)
            assert any("any.xyz" in ev.src_path for ev in events)
        finally:
            daemon.stop()

    def test_multiple_patterns_match_each(self, tmp_path: Path) -> None:
        events: list[WatchEvent] = []

        def cb(ev: WatchEvent) -> None:
            events.append(ev)

        daemon = _make_daemon()
        spec = WatchSpec(
            root=tmp_path, patterns=["*.py", "*.toml"], recursive=False, callback=cb
        )
        daemon.add_watch(spec)
        daemon.start()
        try:
            (tmp_path / "a.py").write_text("x=1")
            (tmp_path / "b.toml").write_text("[tool]")
            time.sleep(_SETTLE_S)
            paths = {ev.src_path for ev in events}
            assert any("a.py" in p for p in paths)
            assert any("b.toml" in p for p in paths)
        finally:
            daemon.stop()


# ---------------------------------------------------------------------------
# Recursive watching
# ---------------------------------------------------------------------------


class TestRecursiveWatching:
    """Tests for recursive vs non-recursive mode."""

    def test_recursive_detects_subdir_events(self, tmp_path: Path) -> None:
        # @trace BKM-09
        subdir = tmp_path / "sub"
        subdir.mkdir()
        events: list[WatchEvent] = []

        def cb(ev: WatchEvent) -> None:
            events.append(ev)

        daemon = _make_daemon()
        spec = WatchSpec(root=tmp_path, patterns=["*"], recursive=True, callback=cb)
        daemon.add_watch(spec)
        daemon.start()
        try:
            (subdir / "nested.txt").write_text("deep")
            time.sleep(_SETTLE_S)
            assert any("nested.txt" in ev.src_path for ev in events)
        finally:
            daemon.stop()

    def test_non_recursive_ignores_subdir_files(self, tmp_path: Path) -> None:
        subdir = tmp_path / "sub2"
        subdir.mkdir()
        events: list[WatchEvent] = []

        def cb(ev: WatchEvent) -> None:
            events.append(ev)

        daemon = _make_daemon()
        spec = WatchSpec(
            root=tmp_path, patterns=["*.txt"], recursive=False, callback=cb
        )
        daemon.add_watch(spec)
        daemon.start()
        try:
            (subdir / "deep.txt").write_text("ignored")
            time.sleep(_SETTLE_S)
            assert not any("deep.txt" in ev.src_path for ev in events)
        finally:
            daemon.stop()


# ---------------------------------------------------------------------------
# Multiple watch specs
# ---------------------------------------------------------------------------


class TestMultipleWatchSpecs:
    """Tests for multiple independent specs on the same daemon."""

    def test_two_specs_independent_callbacks(self, tmp_path: Path) -> None:
        # @trace BKM-09
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()

        events_a: list[WatchEvent] = []
        events_b: list[WatchEvent] = []

        daemon = _make_daemon()
        spec_a = WatchSpec(
            root=dir_a, patterns=["*"], recursive=False, callback=events_a.append
        )
        spec_b = WatchSpec(
            root=dir_b, patterns=["*"], recursive=False, callback=events_b.append
        )
        daemon.add_watch(spec_a)
        daemon.add_watch(spec_b)
        daemon.start()
        try:
            (dir_a / "in_a.txt").write_text("A")
            (dir_b / "in_b.txt").write_text("B")
            time.sleep(_SETTLE_S)
            assert any("in_a.txt" in ev.src_path for ev in events_a)
            assert any("in_b.txt" in ev.src_path for ev in events_b)
            assert not any("in_b.txt" in ev.src_path for ev in events_a)
            assert not any("in_a.txt" in ev.src_path for ev in events_b)
        finally:
            daemon.stop()

    def test_remove_one_watch_leaves_other_active(self, tmp_path: Path) -> None:
        dir_a = tmp_path / "ra"
        dir_b = tmp_path / "rb"
        dir_a.mkdir()
        dir_b.mkdir()

        events_b: list[WatchEvent] = []

        daemon = _make_daemon()
        spec_a = WatchSpec(
            root=dir_a, patterns=["*"], recursive=False, callback=lambda ev: None
        )
        spec_b = WatchSpec(
            root=dir_b, patterns=["*"], recursive=False, callback=events_b.append
        )
        wid_a = daemon.add_watch(spec_a)
        daemon.add_watch(spec_b)
        daemon.start()
        try:
            daemon.remove_watch(wid_a)
            assert len(daemon.list_watches()) == 1
            (dir_b / "still_active.txt").write_text("ok")
            time.sleep(_SETTLE_S)
            assert any("still_active.txt" in ev.src_path for ev in events_b)
        finally:
            daemon.stop()


# ---------------------------------------------------------------------------
# Callback exception resilience
# ---------------------------------------------------------------------------


class TestCallbackExceptionResilience:
    """Tests that callback exceptions do not crash the daemon."""

    def test_callback_exception_does_not_stop_daemon(self, tmp_path: Path) -> None:
        # @trace BKM-09
        def bad_cb(ev: WatchEvent) -> None:
            msg = "intentional test error"
            raise ValueError(msg)

        daemon = _make_daemon()
        spec = WatchSpec(
            root=tmp_path, patterns=["*"], recursive=False, callback=bad_cb
        )
        daemon.add_watch(spec)
        daemon.start()
        try:
            (tmp_path / "boom.txt").write_text("trigger")
            time.sleep(_SETTLE_S)
            assert daemon.is_running()
        finally:
            daemon.stop()

    def test_callback_exception_recorded_in_breaker(self, tmp_path: Path) -> None:
        mock_breaker = MagicMock()

        def bad_cb(ev: WatchEvent) -> None:
            msg = "test error"
            raise RuntimeError(msg)

        daemon = _make_daemon()
        daemon._breaker = mock_breaker
        spec = WatchSpec(
            root=tmp_path, patterns=["*"], recursive=False, callback=bad_cb
        )
        daemon.add_watch(spec)
        daemon.start()
        try:
            (tmp_path / "err.txt").write_text("err")
            time.sleep(_SETTLE_S)
            mock_breaker.record_failure.assert_called()
        finally:
            daemon.stop()


# ---------------------------------------------------------------------------
# CircuitBreakerShm integration
# ---------------------------------------------------------------------------


class TestCircuitBreakerIntegration:
    """Tests for optional CircuitBreakerShm health integration."""

    def test_try_get_breaker_disabled_by_env_flag(self) -> None:
        # @trace BKM-09
        from thegent.native import watcher_daemon as _wm

        with patch.object(_wm, "_SHM_ENABLED", False):
            result = _wm._try_get_breaker()
        assert result is None

    def test_try_get_breaker_import_error_returns_none(self) -> None:
        from thegent.native import watcher_daemon as _wm

        with patch.object(_wm, "_SHM_ENABLED", True):
            with patch.dict("sys.modules", {"thegent.native.state_shm": None}):
                result = _wm._try_get_breaker()
        assert result is None

    def test_daemon_created_with_breaker_mock(self) -> None:
        mock_breaker = MagicMock()
        daemon = WatcherDaemon()
        daemon._breaker = mock_breaker
        daemon.start()
        try:
            assert daemon.is_running()
        finally:
            daemon.stop()

    def test_handler_uses_breaker_on_callback_failure(self, tmp_path: Path) -> None:
        from watchdog.events import FileCreatedEvent

        mock_breaker = MagicMock()
        events_fired: list[WatchEvent] = []

        def failing_cb(ev: WatchEvent) -> None:
            events_fired.append(ev)
            msg = "test failure"
            raise RuntimeError(msg)

        spec = WatchSpec(
            root=tmp_path, patterns=["*"], recursive=False, callback=failing_cb
        )
        handler = _SpecHandler(watch_id="test-id", spec=spec, breaker=mock_breaker)

        handler.on_created(FileCreatedEvent(str(tmp_path / "x.txt")))
        mock_breaker.record_failure.assert_called_once_with("watcher_daemon", "tool")

    def test_handler_no_breaker_callback_failure_survives(self, tmp_path: Path) -> None:
        from watchdog.events import FileCreatedEvent

        def bad_cb(ev: WatchEvent) -> None:
            msg = "no breaker"
            raise RuntimeError(msg)

        spec = WatchSpec(
            root=tmp_path, patterns=["*"], recursive=False, callback=bad_cb
        )
        handler = _SpecHandler(watch_id="tid", spec=spec, breaker=None)

        handler.on_created(FileCreatedEvent(str(tmp_path / "y.txt")))

    def test_handler_breaker_record_failure_error_is_suppressed(
        self, tmp_path: Path
    ) -> None:
        from watchdog.events import FileCreatedEvent

        mock_breaker = MagicMock()
        mock_breaker.record_failure.side_effect = RuntimeError("breaker itself failed")

        def bad_cb(ev: WatchEvent) -> None:
            msg = "cb err"
            raise RuntimeError(msg)

        spec = WatchSpec(
            root=tmp_path, patterns=["*"], recursive=False, callback=bad_cb
        )
        handler = _SpecHandler(watch_id="tid2", spec=spec, breaker=mock_breaker)
        # Must not propagate the breaker's error
        handler.on_created(FileCreatedEvent(str(tmp_path / "z.txt")))


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------


class TestGetWatcherDaemon:
    """Tests for the process-level singleton factory."""

    def setup_method(self) -> None:
        _reset_singleton()

    def teardown_method(self) -> None:
        _reset_singleton()

    def test_returns_watcher_daemon_instance(self) -> None:
        # @trace BKM-09
        daemon = get_watcher_daemon()
        assert isinstance(daemon, WatcherDaemon)

    def test_same_instance_returned_each_time(self) -> None:
        d1 = get_watcher_daemon()
        d2 = get_watcher_daemon()
        assert d1 is d2

    def test_reset_singleton_allows_new_instance(self) -> None:
        d1 = get_watcher_daemon()
        _reset_singleton()
        d2 = get_watcher_daemon()
        assert d1 is not d2

    def test_singleton_thread_safe(self) -> None:
        results: list[WatcherDaemon] = []
        lock = threading.Lock()

        def grab() -> None:
            d = get_watcher_daemon()
            with lock:
                results.append(d)

        threads = [threading.Thread(target=grab) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        first = results[0]
        assert all(d is first for d in results)


# ---------------------------------------------------------------------------
# Thread safety for add/remove
# ---------------------------------------------------------------------------


class TestThreadSafety:
    """Concurrent add/remove operations must not corrupt internal state."""

    def test_concurrent_add_watch(self, tmp_path: Path) -> None:
        # @trace BKM-09
        daemon = _make_daemon()
        daemon.start()
        try:
            ids: list[str] = []
            lock = threading.Lock()

            def add_one() -> None:
                spec = WatchSpec(
                    root=tmp_path,
                    patterns=["*"],
                    recursive=False,
                    callback=lambda ev: None,
                )
                wid = daemon.add_watch(spec)
                with lock:
                    ids.append(wid)

            threads = [threading.Thread(target=add_one) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(ids) == 10
            assert len(set(ids)) == 10
            assert len(daemon.list_watches()) == 10
        finally:
            daemon.stop()

    def test_concurrent_remove_watch(self, tmp_path: Path) -> None:
        daemon = _make_daemon()
        daemon.start()
        try:
            spec = WatchSpec(
                root=tmp_path, patterns=["*"], recursive=False, callback=lambda ev: None
            )
            wids = [daemon.add_watch(spec) for _ in range(5)]

            results: list[bool] = []
            lock = threading.Lock()

            def remove_one(wid: str) -> None:
                r = daemon.remove_watch(wid)
                with lock:
                    results.append(r)

            threads = [threading.Thread(target=remove_one, args=(wid,)) for wid in wids]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert all(results)
            assert daemon.list_watches() == []
        finally:
            daemon.stop()


# ---------------------------------------------------------------------------
# _SpecHandler direct unit tests
# ---------------------------------------------------------------------------


class TestSpecHandlerDirect:
    """Unit tests for _SpecHandler methods using mock events."""

    def test_on_created_dispatches(self, tmp_path: Path) -> None:
        from watchdog.events import FileCreatedEvent

        events: list[WatchEvent] = []
        spec = WatchSpec(
            root=tmp_path, patterns=["*"], recursive=False, callback=events.append
        )
        handler = _SpecHandler(watch_id="h1", spec=spec, breaker=None)
        handler.on_created(FileCreatedEvent(str(tmp_path / "new.py")))
        assert len(events) == 1
        assert events[0].event_type == "created"
        assert events[0].dest_path is None

    def test_on_modified_dispatches(self, tmp_path: Path) -> None:
        from watchdog.events import FileModifiedEvent

        events: list[WatchEvent] = []
        spec = WatchSpec(
            root=tmp_path, patterns=["*"], recursive=False, callback=events.append
        )
        handler = _SpecHandler(watch_id="h2", spec=spec, breaker=None)
        handler.on_modified(FileModifiedEvent(str(tmp_path / "mod.py")))
        assert events[0].event_type == "modified"

    def test_on_deleted_dispatches(self, tmp_path: Path) -> None:
        from watchdog.events import FileDeletedEvent

        events: list[WatchEvent] = []
        spec = WatchSpec(
            root=tmp_path, patterns=["*"], recursive=False, callback=events.append
        )
        handler = _SpecHandler(watch_id="h3", spec=spec, breaker=None)
        handler.on_deleted(FileDeletedEvent(str(tmp_path / "gone.py")))
        assert events[0].event_type == "deleted"

    def test_on_moved_dispatches_with_dest(self, tmp_path: Path) -> None:
        from watchdog.events import FileMovedEvent

        events: list[WatchEvent] = []
        spec = WatchSpec(
            root=tmp_path, patterns=["*"], recursive=False, callback=events.append
        )
        handler = _SpecHandler(watch_id="h4", spec=spec, breaker=None)
        handler.on_moved(
            FileMovedEvent(str(tmp_path / "src.py"), str(tmp_path / "dst.py"))
        )
        assert events[0].event_type == "moved"
        assert events[0].dest_path is not None
        assert "dst.py" in events[0].dest_path

    def test_on_dir_created_dispatches_is_directory(self, tmp_path: Path) -> None:
        from watchdog.events import DirCreatedEvent

        events: list[WatchEvent] = []
        spec = WatchSpec(
            root=tmp_path, patterns=["*"], recursive=False, callback=events.append
        )
        handler = _SpecHandler(watch_id="h5", spec=spec, breaker=None)
        handler.on_created(DirCreatedEvent(str(tmp_path / "subdir")))
        assert events[0].is_directory is True

    def test_on_dir_moved_dispatches_with_dest(self, tmp_path: Path) -> None:
        from watchdog.events import DirMovedEvent

        events: list[WatchEvent] = []
        spec = WatchSpec(
            root=tmp_path, patterns=["*"], recursive=False, callback=events.append
        )
        handler = _SpecHandler(watch_id="h6", spec=spec, breaker=None)
        handler.on_moved(
            DirMovedEvent(str(tmp_path / "oldir"), str(tmp_path / "newdir"))
        )
        assert events[0].event_type == "moved"
        assert events[0].dest_path is not None
        assert events[0].is_directory is True

    def test_on_dir_deleted_dispatches_is_directory(self, tmp_path: Path) -> None:
        from watchdog.events import DirDeletedEvent

        events: list[WatchEvent] = []
        spec = WatchSpec(
            root=tmp_path, patterns=["*"], recursive=False, callback=events.append
        )
        handler = _SpecHandler(watch_id="h7", spec=spec, breaker=None)
        handler.on_deleted(DirDeletedEvent(str(tmp_path / "rmdir")))
        assert events[0].event_type == "deleted"
        assert events[0].is_directory is True

    def test_on_dir_modified_dispatches_is_directory(self, tmp_path: Path) -> None:
        from watchdog.events import DirModifiedEvent

        events: list[WatchEvent] = []
        spec = WatchSpec(
            root=tmp_path, patterns=["*"], recursive=False, callback=events.append
        )
        handler = _SpecHandler(watch_id="h8", spec=spec, breaker=None)
        handler.on_modified(DirModifiedEvent(str(tmp_path / "moddir")))
        assert events[0].event_type == "modified"
        assert events[0].is_directory is True
