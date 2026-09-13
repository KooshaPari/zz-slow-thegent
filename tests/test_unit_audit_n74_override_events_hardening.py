"""Hardening invariants for ``governance.override_events`` — AUDIT-N+74.

15 invariants FR-GOV-OE-001 .. FR-GOV-OE-015 covering
OverrideExpiredEvent, OverrideActivatedEvent, OverrideEventEmitter,
OverrideExpiryMonitor.

Source: src/thegent/governance/override_events.py

@trace AUDIT-N+74  FR-GOV-OE-001..015
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import pytest

from thegent.governance.override_events import (
    OverrideActivatedEvent,
    OverrideEventEmitter,
    OverrideExpiredEvent,
    OverrideExpiryMonitor,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# FR-GOV-OE-001
# ---------------------------------------------------------------------------


class TestFRGOVOE001OverrideExpiredEventFields:
    def test_all_required_fields(self) -> None:
        now = time.time()
        evt = OverrideExpiredEvent(
            override_id="ovr-001",
            policy_id="pol-x",
            owner="admin",
            expired_at=now,
        )
        assert evt.override_id == "ovr-001"
        assert evt.policy_id == "pol-x"
        assert evt.owner == "admin"
        assert evt.expired_at == now


# ---------------------------------------------------------------------------
# FR-GOV-OE-002
# ---------------------------------------------------------------------------


class TestFRGOVOE002OverrideExpiredEventDefaults:
    def test_reason_default(self) -> None:
        evt = OverrideExpiredEvent(
            override_id="ovr-001",
            policy_id="pol-x",
            owner="admin",
            expired_at=time.time(),
        )
        assert evt.reason == "ttl_elapsed"

    def test_event_type_default(self) -> None:
        evt = OverrideExpiredEvent(
            override_id="ovr-001",
            policy_id="pol-x",
            owner="admin",
            expired_at=time.time(),
        )
        assert evt.event_type == "governance.override.expired"


# ---------------------------------------------------------------------------
# FR-GOV-OE-003
# ---------------------------------------------------------------------------


class TestFRGOVOE003OverrideActivatedEventFields:
    def test_all_required_fields(self) -> None:
        now = time.time()
        evt = OverrideActivatedEvent(
            override_id="ovr-002",
            policy_id="pol-y",
            owner="user1",
            activated_at=now,
            ttl_s=600.0,
            expires_at=now + 600.0,
        )
        assert evt.override_id == "ovr-002"
        assert evt.policy_id == "pol-y"
        assert evt.owner == "user1"
        assert evt.activated_at == now
        assert evt.ttl_s == 600.0
        assert evt.expires_at == now + 600.0


# ---------------------------------------------------------------------------
# FR-GOV-OE-004
# ---------------------------------------------------------------------------


class TestFRGOVOE004OverrideActivatedEventDefaults:
    def test_event_type_default(self) -> None:
        evt = OverrideActivatedEvent(
            override_id="ovr-002",
            policy_id="pol-y",
            owner="user1",
            activated_at=time.time(),
            ttl_s=300.0,
            expires_at=time.time() + 300.0,
        )
        assert evt.event_type == "governance.override.activated"


# ---------------------------------------------------------------------------
# FR-GOV-OE-005
# ---------------------------------------------------------------------------


class TestFRGOVOE005EmitterInitDefaultPath:
    def test_default_path_expanded(self) -> None:
        emitter = OverrideEventEmitter()
        assert emitter._path == Path("~/.thegent/governance_events.jsonl").expanduser()

    def test_custom_path(self, tmp_path: Path) -> None:
        p = tmp_path / "custom.jsonl"
        emitter = OverrideEventEmitter(events_path=p)
        assert emitter._path == p


# ---------------------------------------------------------------------------
# FR-GOV-OE-006
# ---------------------------------------------------------------------------


class TestFRGOVOE006EmitExpiredWritesJsonl:
    def test_writes_event_to_file(self, tmp_path: Path) -> None:
        p = tmp_path / "events.jsonl"
        emitter = OverrideEventEmitter(events_path=p)
        now = time.time()
        evt = OverrideExpiredEvent(
            override_id="ovr-exp-1",
            policy_id="pol-a",
            owner="admin",
            expired_at=now,
        )
        emitter.emit_expired(evt)
        assert p.exists()
        lines = p.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["override_id"] == "ovr-exp-1"
        assert data["event_type"] == "governance.override.expired"


# ---------------------------------------------------------------------------
# FR-GOV-OE-007
# ---------------------------------------------------------------------------


class TestFRGOVOE007EmitActivatedWritesJsonl:
    def test_writes_event_to_file(self, tmp_path: Path) -> None:
        p = tmp_path / "events.jsonl"
        emitter = OverrideEventEmitter(events_path=p)
        emitter.emit_activated("ovr-act-1", "pol-b", "user1", ttl_s=120.0)
        assert p.exists()
        lines = p.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["override_id"] == "ovr-act-1"
        assert data["event_type"] == "governance.override.activated"
        assert data["ttl_s"] == 120.0


# ---------------------------------------------------------------------------
# FR-GOV-OE-008
# ---------------------------------------------------------------------------


class TestFRGOVOE008TailEventsEmptyFile:
    def test_empty_file(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.jsonl"
        p.write_text("", encoding="utf-8")
        emitter = OverrideEventEmitter(events_path=p)
        assert emitter.tail_events() == []

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        p = tmp_path / "nope.jsonl"
        emitter = OverrideEventEmitter(events_path=p)
        assert emitter.tail_events() == []


# ---------------------------------------------------------------------------
# FR-GOV-OE-009
# ---------------------------------------------------------------------------


class TestFRGOVOE009TailEventsMalformedLineSkipped:
    def test_skips_bad_json(self, tmp_path: Path) -> None:
        p = tmp_path / "events.jsonl"
        good = json.dumps({"override_id": "ovr-1", "event_type": "test"})
        p.write_text(f"{good}\nnot-valid-json\n", encoding="utf-8")
        emitter = OverrideEventEmitter(events_path=p)
        results = emitter.tail_events()
        assert len(results) == 1
        assert results[0]["override_id"] == "ovr-1"


# ---------------------------------------------------------------------------
# FR-GOV-OE-010
# ---------------------------------------------------------------------------


class TestFRGOVOE010TailEventsReturnsLastN:
    def test_returns_last_n(self, tmp_path: Path) -> None:
        p = tmp_path / "events.jsonl"
        lines = []
        for i in range(5):
            lines.append(json.dumps({"override_id": f"ovr-{i}"}))
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        emitter = OverrideEventEmitter(events_path=p)
        results = emitter.tail_events(n=3)
        assert len(results) == 3
        assert results[0]["override_id"] == "ovr-2"
        assert results[2]["override_id"] == "ovr-4"


# ---------------------------------------------------------------------------
# FR-GOV-OE-011
# ---------------------------------------------------------------------------


class TestFRGOVOE011MonitorInitDefaults:
    def test_defaults(self) -> None:
        monitor = OverrideExpiryMonitor()
        assert monitor._poll_interval == 1.0
        assert monitor._registrations == {}
        assert monitor._thread is None
        assert isinstance(monitor._emitter, OverrideEventEmitter)

    def test_custom_emitter_and_interval(self, tmp_path: Path) -> None:
        emitter = OverrideEventEmitter(events_path=tmp_path / "ev.jsonl")
        monitor = OverrideExpiryMonitor(emitter=emitter, poll_interval_s=0.5)
        assert monitor._emitter is emitter
        assert monitor._poll_interval == 0.5


# ---------------------------------------------------------------------------
# FR-GOV-OE-012
# ---------------------------------------------------------------------------


class TestFRGOVOE012RegisterAddsRegistration:
    def test_adds_registration(self) -> None:
        def _noop() -> None:
            pass

        monitor = OverrideExpiryMonitor()
        monitor.register("ovr-100", time.time() + 999, _noop, policy_id="p1", owner="u1")
        assert "ovr-100" in monitor._registrations
        reg = monitor._registrations["ovr-100"]
        assert reg.override_id == "ovr-100"
        assert reg.policy_id == "p1"
        assert reg.owner == "u1"
        assert reg.on_expire is _noop


# ---------------------------------------------------------------------------
# FR-GOV-OE-013
# ---------------------------------------------------------------------------


class TestFRGOVOE013UnregisterRemovesRegistration:
    def test_removes_registration(self) -> None:
        monitor = OverrideExpiryMonitor()
        monitor.register("ovr-200", time.time() + 999, lambda: None)
        assert "ovr-200" in monitor._registrations
        monitor.unregister("ovr-200")
        assert "ovr-200" not in monitor._registrations

    def test_unregister_nonexistent_no_error(self) -> None:
        monitor = OverrideExpiryMonitor()
        monitor.unregister("nonexistent")  # should not raise


# ---------------------------------------------------------------------------
# FR-GOV-OE-014
# ---------------------------------------------------------------------------


class TestFRGOVOE014CheckExpirationsFiresCallback:
    def test_fires_callback_for_expired(self, tmp_path: Path) -> None:
        fired = threading.Event()
        emitter = OverrideEventEmitter(events_path=tmp_path / "ev.jsonl")
        monitor = OverrideExpiryMonitor(emitter=emitter)
        # Register an already-expired override
        monitor.register("ovr-exp", time.time() - 10, lambda: fired.set(), policy_id="p", owner="o")
        monitor._check_expirations()
        assert fired.is_set()
        assert "ovr-exp" not in monitor._registrations

    def test_does_not_fire_for_future(self, tmp_path: Path) -> None:
        fired = threading.Event()
        emitter = OverrideEventEmitter(events_path=tmp_path / "ev.jsonl")
        monitor = OverrideExpiryMonitor(emitter=emitter)
        monitor.register("ovr-future", time.time() + 9999, lambda: fired.set())
        monitor._check_expirations()
        assert not fired.is_set()
        assert "ovr-future" in monitor._registrations


# ---------------------------------------------------------------------------
# FR-GOV-OE-015
# ---------------------------------------------------------------------------


class TestFRGOVOE015LifecycleStartStop:
    def test_start_and_stop(self, tmp_path: Path) -> None:
        emitter = OverrideEventEmitter(events_path=tmp_path / "ev.jsonl")
        monitor = OverrideExpiryMonitor(emitter=emitter, poll_interval_s=0.1)
        monitor.start()
        assert monitor._thread is not None
        assert monitor._thread.is_alive()
        monitor.stop()
        assert monitor._thread is None

    def test_double_start_noop(self) -> None:
        monitor = OverrideExpiryMonitor(poll_interval_s=0.1)
        monitor.start()
        t1 = monitor._thread
        monitor.start()  # should be a no-op
        assert monitor._thread is t1
        monitor.stop()

    def test_stop_when_not_started(self) -> None:
        monitor = OverrideExpiryMonitor()
        monitor.stop()  # should not raise
