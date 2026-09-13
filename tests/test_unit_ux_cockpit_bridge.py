"""Tests for :mod:`thegent.ux.cockpit_bridge`.

These tests focus on the cross-component contracts documented in the
WP-3003 / WP-4001 / WP-4002 / WP-Y7 summary; the goal is to lock in the
bridge shapes so the SOTA audit lane does not regress the seams between
governance events, KPI dashboards, the cockpit, and progressive disclosure.
"""

from __future__ import annotations

import time
from typing import Any

import pytest

from thegent.governance.override_events import OverrideExpiredEvent
from thegent.ux.cockpit import (
    OperatorCockpit,
    OverrideExpiryNotice,
)
from thegent.ux.cockpit_bridge import (
    BridgeResult,
    ExplanationCompanion,
    OverrideExpiryBridge,
    TrafficCockpitBridge,
    TrafficTickPlan,
    _notice_for,
    install_default_bridges,
    iter_override_events,
)
from thegent.ux.explanations import DecisionExplanation, DisclosureLevel
from thegent.ux.kpis.traffic import TrafficDashboard, TrafficEvent

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cockpit() -> OperatorCockpit:
    return OperatorCockpit()


@pytest.fixture
def traffic() -> TrafficDashboard:
    return TrafficDashboard(window_s=60, bucket_s=1.0, trend_width=24)


def _event(
    *,
    override_id: str = "ov-1",
    policy_id: str = "pol-1",
    owner: str = "koosha",
    expired_in: float = -60.0,
    reason: str = "ttl_elapsed",
    occurred_at: float | None = None,
) -> OverrideExpiredEvent:
    """Build an :class:`OverrideExpiredEvent` with sane defaults."""
    now = occurred_at if occurred_at is not None else time.time()
    return OverrideExpiredEvent(
        override_id=override_id,
        policy_id=policy_id,
        owner=owner,
        expired_at=now + expired_in,
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Notice mapping
# ---------------------------------------------------------------------------


def test_notice_for_uses_supplied_clock() -> None:
    event = _event(expired_in=10.0)
    notice = _notice_for(
        event,
        now_epoch=event.expired_at + 5.0,  # 5s after expiry
    )
    assert notice.age_s == 5.0


def test_notice_for_zero_age_when_clock_pre_expiry() -> None:
    event = _event(expired_in=-30.0)
    notice = _notice_for(event, now_epoch=event.expired_at)
    assert notice.age_s == 0.0


def test_notice_for_copies_fields() -> None:
    event = _event(
        override_id="ov-x",
        owner="alice",
        reason="manual",
    )
    notice = _notice_for(event, now_epoch=event.expired_at)
    assert notice.rule_id == "ov-x"
    assert notice.owner == "alice"
    assert notice.reason == "manual"


def test_notice_for_falls_back_to_default_reason() -> None:
    event = OverrideExpiredEvent(
        override_id="ov-1",
        policy_id="pol-1",
        owner="u",
        expired_at=time.time(),
        reason="",
    )
    notice = _notice_for(event, now_epoch=event.expired_at)
    assert notice.reason == "ttl_elapsed"


# ---------------------------------------------------------------------------
# OverrideExpiryBridge
# ---------------------------------------------------------------------------


def test_override_bridge_feed_records_notice(cockpit: OperatorCockpit) -> None:
    bridge = OverrideExpiryBridge(cockpit)
    result = bridge.feed(_event(override_id="ov-feed"))
    assert isinstance(result, BridgeResult)
    assert result.ok
    assert result.accepted == 1
    assert result.dropped == 0
    notices = cockpit.snapshot()["override_notices"]
    assert notices and notices[0]["rule_id"] == "ov-feed"


def test_override_bridge_feed_many_aggregates(
    cockpit: OperatorCockpit,
) -> None:
    bridge = OverrideExpiryBridge(cockpit)
    events = [_event(override_id=f"ov-{i}") for i in range(5)]
    result = bridge.feed_many(events)
    assert result.ok
    assert result.accepted == 5
    notices = cockpit.snapshot()["override_notices"]
    assert len(notices) == 5


def test_override_bridge_subscribe_uses_drain(
    cockpit: OperatorCockpit,
) -> None:
    bridge = OverrideExpiryBridge(cockpit)

    class _FakeEmitter:
        def __init__(self, events: list[OverrideExpiredEvent]) -> None:
            self._events = events
            self.drained = 0

        def drain(self) -> list[OverrideExpiredEvent]:
            self.drained += 1
            return list(self._events)

    emitter = _FakeEmitter([_event(override_id="ov-drain")])
    result = bridge.subscribe_to(emitter)
    assert result.ok
    assert result.accepted == 1
    assert emitter.drained == 1


def test_override_bridge_subscribe_poll_wins(
    cockpit: OperatorCockpit,
) -> None:
    bridge = OverrideExpiryBridge(cockpit)

    poll_calls = 0

    def _poll() -> list[OverrideExpiredEvent]:
        nonlocal poll_calls
        poll_calls += 1
        return [_event(override_id="ov-poll")]

    result = bridge.subscribe_to(object(), poll=_poll)
    assert result.ok
    assert result.accepted == 1
    assert poll_calls == 1


def test_override_bridge_subscribe_without_drain_raises(
    cockpit: OperatorCockpit,
) -> None:
    bridge = OverrideExpiryBridge(cockpit)
    with pytest.raises(ValueError, match="drain"):
        bridge.subscribe_to(object())


# ---------------------------------------------------------------------------
# TrafficCockpitBridge
# ---------------------------------------------------------------------------


def test_traffic_bridge_plan_progress(
    cockpit: OperatorCockpit, traffic: TrafficDashboard
) -> None:
    traffic.record(TrafficEvent(ts=time.time(), lane="std", duration_ms=10.0))
    traffic.record(TrafficEvent(ts=time.time(), lane="std", duration_ms=20.0))
    bridge = TrafficCockpitBridge(cockpit)
    plan = bridge.plan(traffic)
    assert isinstance(plan, TrafficTickPlan)
    done, total = plan.progress
    assert done >= 1
    assert total >= 1


def test_traffic_bridge_push_updates_progress(
    cockpit: OperatorCockpit, traffic: TrafficDashboard
) -> None:
    traffic.record(TrafficEvent(ts=time.time(), lane="std", duration_ms=10.0))
    bridge = TrafficCockpitBridge(cockpit).bind(traffic)
    result = bridge.push(traffic)
    assert result.ok
    assert cockpit.snapshot()["progress"][0] >= 1


def test_traffic_bridge_triggers_notice_on_error_threshold(
    cockpit: OperatorCockpit, traffic: TrafficDashboard
) -> None:
    # Threshold is 5% by default; force one error among two events.
    now = time.time()
    traffic.record(TrafficEvent(ts=now, status="ok", duration_ms=10.0))
    traffic.record(TrafficEvent(ts=now, status="error", duration_ms=10.0))
    bridge = TrafficCockpitBridge(cockpit).bind(traffic)
    plan = bridge.plan(traffic)
    assert plan.notice is not None
    assert "error_rate" in plan.notice.reason


def test_traffic_bridge_no_notice_below_threshold(
    cockpit: OperatorCockpit, traffic: TrafficDashboard
) -> None:
    for _ in range(20):
        traffic.record(TrafficEvent(ts=time.time(), status="ok", duration_ms=5.0))
    bridge = TrafficCockpitBridge(cockpit).bind(traffic)
    plan = bridge.plan(traffic)
    assert plan.notice is None


def test_traffic_bridge_threshold_is_honoured(
    cockpit: OperatorCockpit, traffic: TrafficDashboard
) -> None:
    # 50% errors but raise threshold to 99%.
    traffic.record(TrafficEvent(ts=time.time(), status="ok", duration_ms=1.0))
    traffic.record(TrafficEvent(ts=time.time(), status="error", duration_ms=1.0))
    bridge = TrafficCockpitBridge(cockpit, error_rate_threshold=0.99).bind(traffic)
    plan = bridge.plan(traffic)
    assert plan.notice is None


def test_traffic_bridge_push_default_requires_binding(
    cockpit: OperatorCockpit,
) -> None:
    bridge = TrafficCockpitBridge(cockpit)
    with pytest.raises(RuntimeError, match="bound dashboard"):
        bridge.push_default()


def test_traffic_bridge_push_default_after_bind(
    cockpit: OperatorCockpit, traffic: TrafficDashboard
) -> None:
    traffic.record(TrafficEvent(ts=time.time(), status="ok", duration_ms=10.0))
    bridge = TrafficCockpitBridge(cockpit).bind(traffic)
    result = bridge.push_default()
    assert result.ok


# ---------------------------------------------------------------------------
# ExplanationCompanion
# ---------------------------------------------------------------------------


def test_explanation_companion_payload_and_render(
    cockpit: OperatorCockpit,
) -> None:
    explanation = DecisionExplanation(
        title="Routing decision",
        verdict="allow",
        reason="Within budget",
        confidence=0.92,
    )
    companion = ExplanationCompanion(cockpit, explanation)
    payload: dict[str, Any] = dict(companion.payload())
    assert payload["cockpit"] == cockpit.snapshot()
    assert payload["explanation"]["verdict"] == "allow"
    rendered = companion.render()
    assert "Within budget" in rendered
    assert "allow" in rendered or "[OK]" in rendered


def test_explanation_companion_respects_level(
    cockpit: OperatorCockpit,
) -> None:
    explanation = DecisionExplanation(
        title="x",
        verdict="deny",
        reason="policy",
        confidence=0.5,
    )
    concise = ExplanationCompanion(
        cockpit, explanation, level=DisclosureLevel.CONCISE
    ).render()
    detailed = ExplanationCompanion(
        cockpit, explanation, level=DisclosureLevel.DETAILED
    ).render()
    assert len(detailed) >= len(concise)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def test_iter_override_events_is_passthrough() -> None:
    events = [_event(override_id=f"ov-{i}") for i in range(3)]
    out = list(iter_override_events(events))
    assert out == list(events)


def test_install_default_bridges_returns_pair(
    cockpit: OperatorCockpit, traffic: TrafficDashboard
) -> None:
    traffic.record(TrafficEvent(ts=time.time(), status="ok", duration_ms=1.0))
    override_bridge, traffic_bridge = install_default_bridges(cockpit, traffic)
    assert isinstance(override_bridge, OverrideExpiryBridge)
    assert isinstance(traffic_bridge, TrafficCockpitBridge)
    # Round trip - exercise the actual instances we returned.
    result = override_bridge.feed(_event(override_id="ov-inst"))
    assert result.ok
    assert traffic_bridge.push(traffic).ok


# ---------------------------------------------------------------------------
# Hardening (concurrency / error tolerance)
# ---------------------------------------------------------------------------


def test_override_bridge_swallows_cockpit_errors(
    monkeypatch: pytest.MonkeyPatch,
    cockpit: OperatorCockpit,
) -> None:
    bridge = OverrideExpiryBridge(cockpit)

    def _boom(_notice: OverrideExpiryNotice) -> None:
        raise RuntimeError("cockpit wedged")

    monkeypatch.setattr(cockpit, "record_override_event", _boom)
    result = bridge.feed(_event())
    assert result.accepted == 0
    assert not result.ok
    assert "wedged" in result.errors[0]


def test_traffic_bridge_swallows_cockpit_errors(
    monkeypatch: pytest.MonkeyPatch,
    cockpit: OperatorCockpit,
    traffic: TrafficDashboard,
) -> None:
    traffic.record(TrafficEvent(ts=time.time(), status="ok", duration_ms=1.0))
    bridge = TrafficCockpitBridge(cockpit).bind(traffic)

    def _boom(_progress: tuple[int, int]) -> None:
        raise RuntimeError("cockpit wedged")

    monkeypatch.setattr(cockpit, "tick", _boom)
    result = bridge.push(traffic)
    assert result.accepted == 0
    assert not result.ok


def test_bridge_idempotency(cockpit: OperatorCockpit) -> None:
    """Bridges must not deduplicate events - the idempotent contract is in iter."""
    bridge = OverrideExpiryBridge(cockpit)
    event = _event(override_id="ov-once")
    result_a = bridge.feed(event)
    result_b = bridge.feed(event)
    assert result_a.ok and result_b.ok
    assert result_a.accepted == 1 and result_b.accepted == 1
    notices = cockpit.snapshot()["override_notices"]
    assert len(notices) == 2  # Two distinct notices, no dedup.
