"""Tests for clock injection + DecisionNotice surfaces in the operator cockpit.

These tests lock in the SOTA deterministic-replay contract and the
WP-3001 -> WP-4001 decision bridge that this change wires up.
"""

from __future__ import annotations

import time

import pytest

from thegent.ux.cockpit import (
    OVERRIDE_BANNER_MAX_AGE_S,
    CockpitConfig,
    DecisionNotice,
    OperatorCockpit,
    OverrideExpiryNotice,
    render_cockpit,
)
from thegent.ux.cockpit_bridge import (
    BridgeResult,
    DecisionNoticeBridge,
    _decision_notice_for,
)
from thegent.ux.kpis.traffic import TrafficDashboard, TrafficEvent, TrafficWindow

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Clock injection (deterministic audit replay)
# ---------------------------------------------------------------------------


class _Clock:
    """Mutable wall-clock callable for deterministic replays."""

    def __init__(self, start: float = 1_700_000_000.0) -> None:
        self.now = start
        self.calls = 0

    def __call__(self) -> float:
        self.calls += 1
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TestClockInjection:
    def test_tick_uses_injected_clock(self) -> None:
        clock = _Clock(start=1000.0)
        cockpit = OperatorCockpit(clock=clock)
        cockpit.tick(runs=[])
        assert cockpit._state.last_tick_at == 1000.0
        clock.advance(5.0)
        cockpit.tick(runs=[])
        assert cockpit._state.last_tick_at == 1005.0

    def test_render_uses_injected_clock(self) -> None:
        clock = _Clock(start=2000.0)
        cockpit = OperatorCockpit(clock=clock)
        cockpit.render()
        # render() calls the clock at least twice (start + end measurement).
        assert clock.calls >= 2

    def test_override_banner_age_uses_injected_clock(self) -> None:
        clock = _Clock(start=10_000.0)
        cockpit = OperatorCockpit(clock=clock)
        # Notice that already expired 10s before "now".
        cockpit.record_override_event(
            OverrideExpiryNotice(
                rule_id="r1",
                owner="u",
                reason="ttl",
                expired_at=clock() - 10.0,
            )
        )
        # Age must be ~10s at render time (not whatever the real clock says).
        out = cockpit.render()
        assert "10s ago" in out

    def test_override_banner_fade_uses_injected_clock(self) -> None:
        clock = _Clock(start=10_000.0)
        cockpit = OperatorCockpit(clock=clock)
        cockpit.record_override_event(
            OverrideExpiryNotice(
                rule_id="stale",
                owner="u",
                reason="ttl",
                # Notice expired long ago — fade must trigger.
                expired_at=clock() - (OVERRIDE_BANNER_MAX_AGE_S + 5.0),
            )
        )
        out = cockpit.render()
        assert "override expired" not in out

    def test_render_is_byte_identical_across_runs(self) -> None:
        """Same inputs + same injected clock = byte-identical render output.

        SOTA audit-replay contract: rendering the same state under a
        frozen clock must produce the same string deterministically.
        """
        clock_a = _Clock(start=500.0)
        clock_b = _Clock(start=500.0)
        cfg = CockpitConfig(title="replay")
        # First render
        c1 = OperatorCockpit(config=cfg, clock=clock_a)
        c1.tick(
            runs=[],
            overrides=[],
            progress=(2, 4),
        )
        out_a = c1.render()
        # Second render with fresh cockpit + same clock
        c2 = OperatorCockpit(config=cfg, clock=clock_b)
        c2.tick(
            runs=[],
            overrides=[],
            progress=(2, 4),
        )
        out_b = c2.render()
        # Both renders were called at the same frozen timestamp so the
        # only difference is the frame-count annotation (#N) which is
        # baked into the header. We strip that before comparing.
        norm_a = out_a.replace(f"#{c1._frame_count}", "#N")
        norm_b = out_b.replace(f"#{c2._frame_count}", "#N")
        assert norm_a == norm_b

    def test_render_cockpit_one_shot_accepts_clock(self) -> None:
        clock = _Clock(start=12345.0)
        out = render_cockpit(runs=[], progress=(1, 1), clock=clock)
        assert "thegent operator cockpit" in out


# ---------------------------------------------------------------------------
# DecisionNotice + record_decision
# ---------------------------------------------------------------------------


class TestDecisionNotice:
    def test_is_deny(self) -> None:
        assert DecisionNotice(verdict="deny", reason_code="x", rule_id="r").is_deny()
        assert not DecisionNotice(
            verdict="allow", reason_code="x", rule_id="r"
        ).is_deny()

    def test_is_warn(self) -> None:
        assert DecisionNotice(verdict="warn", reason_code="x", rule_id="r").is_warn()
        assert not DecisionNotice(
            verdict="deny", reason_code="x", rule_id="r"
        ).is_warn()

    def test_record_decision_appends_to_bounded_deque(self) -> None:
        cockpit = OperatorCockpit()
        for i in range(70):
            cockpit.record_decision(
                DecisionNotice(
                    verdict="allow",
                    reason_code=f"r{i}",
                    rule_id=f"rule-{i}",
                )
            )
        # Bounded: maxlen=64 means oldest 6 are evicted.
        assert len(cockpit._state.decision_notices) == 64
        assert cockpit._state.decision_notices[-1].reason_code == "r69"
        assert cockpit._state.decision_notices[0].reason_code == "r6"

    def test_record_decision_rejects_wrong_type(self) -> None:
        cockpit = OperatorCockpit()
        with pytest.raises(TypeError):
            cockpit.record_decision({"verdict": "deny"})  # type: ignore[arg-type]

    def test_record_decision_zero_evaluated_at_uses_clock(self) -> None:
        clock = _Clock(start=9999.0)
        cockpit = OperatorCockpit(clock=clock)
        cockpit.record_decision(
            DecisionNotice(verdict="deny", reason_code="r1", rule_id="rule-1")
        )
        assert cockpit._state.decision_notices[-1].evaluated_at == 9999.0

    def test_snapshot_includes_decision_notices(self) -> None:
        cockpit = OperatorCockpit()
        cockpit.record_decision(
            DecisionNotice(
                verdict="deny",
                reason_code="critical_lane_low_confidence",
                rule_id="local.critical.confidence",
                agent="cursor",
                lane="critical",
                evaluated_at=time.time(),
                reason="confidence 0.4 below 0.9",
            )
        )
        snap = cockpit.snapshot()
        assert "decision_notices" in snap
        assert snap["decision_notices"][0]["verdict"] == "deny"
        assert (
            snap["decision_notices"][0]["reason_code"] == "critical_lane_low_confidence"
        )

    def test_deny_banner_surfaces_inline(self) -> None:
        """A fresh deny decision shows up as a focused banner."""
        cockpit = OperatorCockpit()
        cockpit.record_decision(
            DecisionNotice(
                verdict="deny",
                reason_code="critical_lane_low_confidence",
                rule_id="local.critical.confidence",
                lane="critical",
                evaluated_at=time.time(),
                reason="confidence too low",
            )
        )
        out = cockpit.render()
        assert "policy deny" in out
        assert "local.critical.confidence" in out
        assert "critical" in out

    def test_allow_does_not_create_banner_noise(self) -> None:
        """Allow decisions accumulate but do not surface as banners."""
        cockpit = OperatorCockpit()
        for _ in range(5):
            cockpit.record_decision(
                DecisionNotice(
                    verdict="allow",
                    reason_code="allowed",
                    rule_id="local.default.allow",
                )
            )
        out = cockpit.render()
        assert "policy deny" not in out

    def test_allow_accumulates_in_snapshot(self) -> None:
        cockpit = OperatorCockpit()
        cockpit.record_decision(
            DecisionNotice(
                verdict="allow", reason_code="allowed", rule_id="local.default.allow"
            )
        )
        snap = cockpit.snapshot()
        assert len(snap["decision_notices"]) == 1
        assert snap["decision_notices"][0]["verdict"] == "allow"

    def test_banner_prefers_freshest_event(self) -> None:
        """When both an override and a deny are fresh, the freshest wins."""
        now = time.time()
        cockpit = OperatorCockpit()
        # Older override notice (15s ago)
        cockpit.record_override_event(
            OverrideExpiryNotice(
                rule_id="ovr-rule",
                owner="alice",
                reason="manual",
                expired_at=now - 15.0,
            )
        )
        # Fresh deny (just now)
        cockpit.record_decision(
            DecisionNotice(
                verdict="deny",
                reason_code="critical_lane_low_confidence",
                rule_id="local.critical.confidence",
                lane="critical",
                evaluated_at=now,
                reason="confidence 0.4",
            )
        )
        out = cockpit.render()
        assert "policy deny" in out
        assert "override expired" not in out

    def test_stale_decision_does_not_summon_banner(self) -> None:
        cockpit = OperatorCockpit()
        cockpit.record_decision(
            DecisionNotice(
                verdict="deny",
                reason_code="x",
                rule_id="r",
                evaluated_at=time.time() - (OVERRIDE_BANNER_MAX_AGE_S + 5.0),
            )
        )
        out = cockpit.render()
        assert "policy deny" not in out


# ---------------------------------------------------------------------------
# DecisionNoticeBridge (WP-3001 -> WP-4001)
# ---------------------------------------------------------------------------


class _FakeDecision:
    """Minimal duck-typed PolicyDecision stand-in."""

    def __init__(
        self,
        *,
        verdict: str = "allow",
        reason_code: str = "allowed",
        rule_id: str | None = "r",
        reason: str = "",
        evaluated_at: float = 0.0,
    ) -> None:
        self.verdict = verdict
        self.reason_code = reason_code
        self.rule_id = rule_id
        self.reason = reason
        self.evaluated_at = evaluated_at


class TestDecisionNoticeFor:
    def test_accepts_policydecision_like_object(self) -> None:
        d = _FakeDecision(verdict="deny", reason_code="x", rule_id="r1")
        notice = _decision_notice_for(
            d, agent="cursor", lane="critical", now_epoch=42.0
        )
        assert notice.verdict == "deny"
        assert notice.reason_code == "x"
        assert notice.rule_id == "r1"
        assert notice.agent == "cursor"
        assert notice.lane == "critical"
        # evaluated_at was 0.0 -> filled with supplied clock.
        assert notice.evaluated_at == 42.0

    def test_accepts_mapping(self) -> None:
        payload = {"verdict": "warn", "reason_code": "w", "rule_id": "r2"}
        notice = _decision_notice_for(payload, now_epoch=7.0)
        assert notice.verdict == "warn"
        assert notice.reason_code == "w"
        assert notice.rule_id == "r2"

    def test_preserves_evaluated_at_when_nonzero(self) -> None:
        d = _FakeDecision(evaluated_at=12.5)
        notice = _decision_notice_for(d, now_epoch=99.0)
        assert notice.evaluated_at == 12.5


class TestDecisionNoticeBridge:
    def test_feed_records_decision(self) -> None:
        cockpit = OperatorCockpit()
        bridge = DecisionNoticeBridge(cockpit)
        result = bridge.feed(
            _FakeDecision(verdict="deny", reason_code="x", rule_id="r1")
        )
        assert isinstance(result, BridgeResult)
        assert result.ok
        assert result.accepted == 1
        notices = cockpit.snapshot()["decision_notices"]
        assert notices and notices[0]["verdict"] == "deny"
        assert notices[0]["rule_id"] == "r1"

    def test_feed_many_aggregates(self) -> None:
        cockpit = OperatorCockpit()
        bridge = DecisionNoticeBridge(cockpit)
        decisions = [
            _FakeDecision(verdict="allow", reason_code=f"a{i}", rule_id=f"r{i}")
            for i in range(7)
        ]
        result = bridge.feed_many(decisions, agent="cursor", lane="standard")
        assert result.ok
        assert result.accepted == 7
        assert len(cockpit.snapshot()["decision_notices"]) == 7

    def test_swallows_cockpit_errors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cockpit = OperatorCockpit()
        bridge = DecisionNoticeBridge(cockpit)

        def _boom(_notice: DecisionNotice) -> None:
            raise RuntimeError("cockpit wedged")

        monkeypatch.setattr(cockpit, "record_decision", _boom)
        result = bridge.feed(_FakeDecision())
        assert result.accepted == 0
        assert not result.ok
        assert "wedged" in result.errors[0]

    def test_banner_verdicts_constant_is_deny_only(self) -> None:
        """The contract: only ``deny`` produces a banner; allows are quiet."""
        bridge = DecisionNoticeBridge(OperatorCockpit())
        assert bridge.surface_banner_verdicts() == frozenset({"deny"})

    def test_end_to_end_policy_engine_to_cockpit_banner(self) -> None:
        """End-to-end: PolicyDecision -> bridge -> cockpit banner."""
        from thegent.governance.policy_engine import (
            PolicyContext,
            PolicyDecision,
            PolicyEngine,
            ReasonCode,
            Verdict,
        )

        engine = PolicyEngine(use_federation=False)
        # Critical lane + low confidence => deny
        ctx = PolicyContext(
            agent="cursor",
            lane="critical",
            confidence=0.4,
            environment="production",
        )
        decision: PolicyDecision = engine.evaluate(ctx)
        assert decision.verdict == Verdict.DENY

        clock = _Clock(start=100.0)
        cockpit = OperatorCockpit(clock=clock)
        bridge = DecisionNoticeBridge(cockpit)
        result = bridge.feed(decision, agent=ctx.agent, lane=ctx.lane)
        assert result.ok
        # Cockpit should show the deny banner.
        out = cockpit.render()
        assert "policy deny" in out
        assert (
            ReasonCode.CRITICAL_LANE_LOW_CONFIDENCE.value in out
            or "critical" in out.lower()
        )


# ---------------------------------------------------------------------------
# Traffic clock injection (deterministic dashboard replays)
# ---------------------------------------------------------------------------


class TestTrafficClockInjection:
    def test_traffic_window_uses_injected_clock_for_zero_init(self) -> None:
        clock = _Clock(start=1000.0)
        window = TrafficWindow.__new__(TrafficWindow)
        # Initialise manually to mirror dataclass __post_init__ without
        # touching __init__ (dataclass-generated __init__ would clobber
        # the clock). This keeps the test surgical.
        from collections import deque as _dq

        window.window_s = 60.0
        window.bucket_s = 1.0
        window._events = _dq()
        window._lock = __import__("threading").Lock()
        window.set_clock(clock)
        window.record(TrafficEvent(ts=0.0, status="ok"))
        assert window._events[0].ts == 1000.0

    def test_traffic_summary_uses_injected_clock(self) -> None:
        clock = _Clock(start=2000.0)
        dashboard = TrafficDashboard(window_s=60.0, clock=clock)
        dashboard.record(TrafficEvent(ts=clock() - 5.0, status="ok", duration_ms=10.0))
        snap = dashboard.summary()
        assert snap["count"] == 1
        # rps depends on window_s (60) so is deterministic; the
        # important thing is that summary() honoured the injected clock
        # and did not error on a frozen timestamp.

    def test_traffic_set_clock_replaces_wall_clock(self) -> None:
        dashboard = TrafficDashboard(window_s=60.0)
        clock = _Clock(start=3000.0)
        dashboard.set_clock(clock)
        dashboard.record(TrafficEvent(ts=0.0, status="ok", duration_ms=1.0))
        # First event was given ts=0 by the test, but the dashboard's
        # injected clock stamped it at 3000.0.
        assert dashboard.window._events[0].ts == 3000.0
