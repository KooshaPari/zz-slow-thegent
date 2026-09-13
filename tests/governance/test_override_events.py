"""Tests for governance override expiry event emission.

Covers: OverrideExpiredEvent, OverrideActivatedEvent, OverrideEventEmitter,
        OverrideExpiryMonitor — JSONL audit log emission and background thread expiry.

FR traceability: @trace FR-GOV-001 (governance audit trail)
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

import orjson as json
import pytest

if TYPE_CHECKING:
    from pathlib import Path

from thegent.governance.override_events import (
    OverrideActivatedEvent,
    OverrideEventEmitter,
    OverrideExpiredEvent,
    OverrideExpiryMonitor,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def events_path(tmp_path: Path) -> Path:
    """Return a unique JSONL path inside tmp_path."""
    return tmp_path / "governance_events.jsonl"


@pytest.fixture
def emitter(events_path: Path) -> OverrideEventEmitter:
    """Return an emitter backed by a temp file."""
    return OverrideEventEmitter(events_path=events_path)


def _read_lines(path: Path) -> list[dict[str, object]]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# OverrideExpiredEvent dataclass
# ---------------------------------------------------------------------------


class TestOverrideExpiredEvent:
    """@trace FR-GOV-001"""

    def test_default_reason(self):
        evt = OverrideExpiredEvent(override_id="ovr-1", policy_id="pol-A", owner="alice", expired_at=1.0)
        assert evt.reason == "ttl_elapsed"

    def test_custom_reason(self):
        evt = OverrideExpiredEvent(
            override_id="ovr-2", policy_id="pol-B", owner="bob", expired_at=2.0, reason="manual_revoke"
        )
        assert evt.reason == "manual_revoke"

    def test_event_type_field(self):
        evt = OverrideExpiredEvent(override_id="ovr-3", policy_id="pol-C", owner="carol", expired_at=3.0)
        assert evt.event_type == "governance.override.expired"

    def test_to_dict_contains_all_fields(self):
        evt = OverrideExpiredEvent(override_id="ovr-4", policy_id="pol-D", owner="dave", expired_at=4.0)
        d = evt.to_dict()
        assert d["override_id"] == "ovr-4"
        assert d["policy_id"] == "pol-D"
        assert d["owner"] == "dave"
        assert d["expired_at"] == 4.0
        assert d["reason"] == "ttl_elapsed"
        assert d["event_type"] == "governance.override.expired"


# ---------------------------------------------------------------------------
# OverrideActivatedEvent dataclass
# ---------------------------------------------------------------------------


class TestOverrideActivatedEvent:
    """@trace FR-GOV-001"""

    def test_event_type_field(self):
        evt = OverrideActivatedEvent(
            override_id="ovr-10", policy_id="pol-X", owner="erin", activated_at=100.0, ttl_s=60.0, expires_at=160.0
        )
        assert evt.event_type == "governance.override.activated"

    def test_to_dict_contains_all_fields(self):
        evt = OverrideActivatedEvent(
            override_id="ovr-11", policy_id="pol-Y", owner="frank", activated_at=200.0, ttl_s=120.0, expires_at=320.0
        )
        d = evt.to_dict()
        assert d["override_id"] == "ovr-11"
        assert d["ttl_s"] == 120.0
        assert d["expires_at"] == 320.0
        assert d["event_type"] == "governance.override.activated"


# ---------------------------------------------------------------------------
# OverrideEventEmitter — emit_expired
# ---------------------------------------------------------------------------


class TestOverrideEventEmitterExpired:
    """@trace FR-GOV-001"""

    def test_emit_expired_creates_file(self, emitter: OverrideEventEmitter, events_path: Path):
        evt = OverrideExpiredEvent(override_id="ovr-100", policy_id="pol-1", owner="alice", expired_at=time.time())
        emitter.emit_expired(evt)
        assert events_path.exists()

    def test_emit_expired_writes_valid_json(self, emitter: OverrideEventEmitter, events_path: Path):
        evt = OverrideExpiredEvent(override_id="ovr-101", policy_id="pol-2", owner="bob", expired_at=999.0)
        emitter.emit_expired(evt)
        lines = _read_lines(events_path)
        assert len(lines) == 1
        assert lines[0]["override_id"] == "ovr-101"
        assert lines[0]["event_type"] == "governance.override.expired"

    def test_emit_expired_appends_multiple(self, emitter: OverrideEventEmitter, events_path: Path):
        for i in range(3):
            emitter.emit_expired(
                OverrideExpiredEvent(override_id=f"ovr-{i}", policy_id="pol-X", owner="alice", expired_at=float(i))
            )
        lines = _read_lines(events_path)
        assert len(lines) == 3

    def test_emit_expired_preserves_reason(self, emitter: OverrideEventEmitter, events_path: Path):
        evt = OverrideExpiredEvent(
            override_id="ovr-102", policy_id="pol-3", owner="carol", expired_at=1000.0, reason="manual_revoke"
        )
        emitter.emit_expired(evt)
        data = _read_lines(events_path)[0]
        assert data["reason"] == "manual_revoke"


# ---------------------------------------------------------------------------
# OverrideEventEmitter — emit_activated
# ---------------------------------------------------------------------------


class TestOverrideEventEmitterActivated:
    """@trace FR-GOV-001"""

    def test_emit_activated_writes_event(self, emitter: OverrideEventEmitter, events_path: Path):
        emitter.emit_activated("ovr-200", "pol-A", "dave", 300.0)
        lines = _read_lines(events_path)
        assert len(lines) == 1
        assert lines[0]["event_type"] == "governance.override.activated"
        assert lines[0]["override_id"] == "ovr-200"

    def test_emit_activated_ttl_and_expires(self, emitter: OverrideEventEmitter, events_path: Path):
        before = time.time()
        emitter.emit_activated("ovr-201", "pol-B", "eve", 60.0)
        after = time.time()
        data = _read_lines(events_path)[0]
        assert data["ttl_s"] == 60.0
        assert before + 60.0 <= data["expires_at"] <= after + 60.0

    def test_emit_activated_owner_preserved(self, emitter: OverrideEventEmitter, events_path: Path):
        emitter.emit_activated("ovr-202", "pol-C", "frank", 10.0)
        data = _read_lines(events_path)[0]
        assert data["owner"] == "frank"

    def test_emit_multiple_types(self, emitter: OverrideEventEmitter, events_path: Path):
        emitter.emit_activated("ovr-300", "pol-D", "grace", 30.0)
        emitter.emit_expired(
            OverrideExpiredEvent(override_id="ovr-300", policy_id="pol-D", owner="grace", expired_at=time.time() + 30)
        )
        lines = _read_lines(events_path)
        assert len(lines) == 2
        assert lines[0]["event_type"] == "governance.override.activated"
        assert lines[1]["event_type"] == "governance.override.expired"


# ---------------------------------------------------------------------------
# OverrideEventEmitter — tail_events
# ---------------------------------------------------------------------------


class TestTailEvents:
    """@trace FR-GOV-001"""

    def test_tail_events_empty_when_no_file(self, events_path: Path):
        emitter = OverrideEventEmitter(events_path=events_path)
        assert emitter.tail_events() == []

    def test_tail_events_returns_all_when_fewer_than_n(self, emitter: OverrideEventEmitter, events_path: Path):
        for i in range(5):
            emitter.emit_expired(OverrideExpiredEvent(f"ovr-{i}", "pol-X", "alice", float(i)))
        events = emitter.tail_events(n=20)
        assert len(events) == 5

    def test_tail_events_limits_to_n(self, emitter: OverrideEventEmitter, events_path: Path):
        for i in range(10):
            emitter.emit_expired(OverrideExpiredEvent(f"ovr-{i}", "pol-X", "alice", float(i)))
        events = emitter.tail_events(n=3)
        assert len(events) == 3

    def test_tail_events_returns_most_recent(self, emitter: OverrideEventEmitter, events_path: Path):
        for i in range(5):
            emitter.emit_expired(OverrideExpiredEvent(f"ovr-{i}", "pol-X", "alice", float(i)))
        events = emitter.tail_events(n=2)
        assert events[0]["override_id"] == "ovr-3"
        assert events[1]["override_id"] == "ovr-4"

    def test_tail_events_skips_malformed_lines(self, emitter: OverrideEventEmitter, events_path: Path):
        # Write a valid event, then a garbage line
        emitter.emit_expired(OverrideExpiredEvent("ovr-good", "pol-X", "alice", 1.0))
        with events_path.open("a", encoding="utf-8") as fh:
            fh.write("NOT_JSON\n")
        events = emitter.tail_events(n=20)
        assert len(events) == 1
        assert events[0]["override_id"] == "ovr-good"

    def test_tail_events_default_n_is_twenty(self, emitter: OverrideEventEmitter, events_path: Path):
        for i in range(25):
            emitter.emit_expired(OverrideExpiredEvent(f"ovr-{i}", "pol-X", "alice", float(i)))
        events = emitter.tail_events()
        assert len(events) == 20


# ---------------------------------------------------------------------------
# OverrideExpiryMonitor — registration
# ---------------------------------------------------------------------------


class TestOverrideExpiryMonitorRegistration:
    """@trace FR-GOV-001"""

    def test_register_and_immediate_expiry(self, events_path: Path):
        emitter = OverrideEventEmitter(events_path=events_path)
        fired = threading.Event()
        monitor = OverrideExpiryMonitor(emitter=emitter, poll_interval_s=0.05)
        monitor.start()
        try:
            monitor.register(
                override_id="ovr-mon-1",
                expires_at=time.time() - 0.1,  # already expired
                on_expire=fired.set,
            )
            assert fired.wait(timeout=2.0), "Expiry callback was not fired within 2s"
        finally:
            monitor.stop()

    def test_register_emits_expired_event(self, events_path: Path):
        emitter = OverrideEventEmitter(events_path=events_path)
        done = threading.Event()
        monitor = OverrideExpiryMonitor(emitter=emitter, poll_interval_s=0.05)
        monitor.start()
        try:
            monitor.register(
                override_id="ovr-mon-2",
                expires_at=time.time() - 0.1,
                on_expire=done.set,
            )
            done.wait(timeout=2.0)
            events = emitter.tail_events()
            assert any(e["override_id"] == "ovr-mon-2" for e in events)
        finally:
            monitor.stop()

    def test_unregister_prevents_callback(self, events_path: Path):
        emitter = OverrideEventEmitter(events_path=events_path)
        fired = threading.Event()
        monitor = OverrideExpiryMonitor(emitter=emitter, poll_interval_s=0.05)
        monitor.start()
        try:
            monitor.register(
                override_id="ovr-mon-3",
                expires_at=time.time() + 10.0,  # far future
                on_expire=fired.set,
            )
            monitor.unregister("ovr-mon-3")
            time.sleep(0.15)
            assert not fired.is_set(), "Callback fired after unregister"
        finally:
            monitor.stop()


# ---------------------------------------------------------------------------
# OverrideExpiryMonitor — lifecycle
# ---------------------------------------------------------------------------


class TestOverrideExpiryMonitorLifecycle:
    """@trace FR-GOV-001"""

    def test_start_stop_clean(self, events_path: Path):
        emitter = OverrideEventEmitter(events_path=events_path)
        monitor = OverrideExpiryMonitor(emitter=emitter, poll_interval_s=0.05)
        monitor.start()
        assert monitor._thread is not None
        assert monitor._thread.is_alive()
        monitor.stop()
        assert monitor._thread is None

    def test_double_start_is_idempotent(self, events_path: Path):
        emitter = OverrideEventEmitter(events_path=events_path)
        monitor = OverrideExpiryMonitor(emitter=emitter, poll_interval_s=0.05)
        monitor.start()
        first_thread = monitor._thread
        monitor.start()
        assert monitor._thread is first_thread  # same thread, not replaced
        monitor.stop()

    def test_stop_without_start_is_safe(self, events_path: Path):
        emitter = OverrideEventEmitter(events_path=events_path)
        monitor = OverrideExpiryMonitor(emitter=emitter)
        monitor.stop()  # must not raise

    def test_callback_error_does_not_crash_monitor(self, events_path: Path):
        emitter = OverrideEventEmitter(events_path=events_path)
        second_fired = threading.Event()

        def bad_callback() -> None:
            raise RuntimeError("intentional test error")

        monitor = OverrideExpiryMonitor(emitter=emitter, poll_interval_s=0.05)
        monitor.start()
        try:
            monitor.register("ovr-bad", time.time() - 0.1, bad_callback)
            monitor.register("ovr-good", time.time() - 0.1, second_fired.set)
            assert second_fired.wait(timeout=2.0), "Monitor crashed after callback error"
        finally:
            monitor.stop()

    def test_multiple_overrides_all_fire(self, events_path: Path):
        emitter = OverrideEventEmitter(events_path=events_path)
        results: list[str] = []
        lock = threading.Lock()

        def make_cb(name: str):
            def cb() -> None:
                with lock:
                    results.append(name)

            return cb

        monitor = OverrideExpiryMonitor(emitter=emitter, poll_interval_s=0.05)
        monitor.start()
        try:
            for i in range(5):
                monitor.register(
                    f"ovr-multi-{i}",
                    time.time() - 0.1,
                    make_cb(f"ovr-multi-{i}"),
                )
            deadline = time.time() + 3.0
            while time.time() < deadline:
                with lock:
                    if len(results) == 5:
                        break
                time.sleep(0.05)
            with lock:
                assert len(results) == 5
        finally:
            monitor.stop()
