"""Glue adapters connecting governance events and KPIs into the operator cockpit.

These helpers close the WP-3003 / WP-4001 / WP-4002 / WP-Y7 composition gaps
documented in ``cockpit.py`` docstrings. Each adapter is intentionally
side-effect free and thread-safe (it forwards errors via :class:`BridgeResult`).

The connectors exposed here are:

* :class:`OverrideExpiryBridge` — converts :class:`OverrideExpiredEvent`
  records emitted by ``OverrideEventEmitter`` into
  :class:`OverrideExpiryNotice` payloads the cockpit understands.
* :class:`TrafficCockpitBridge` — pushes live ``TrafficDashboard`` summaries
  into the cockpit as ``progress=(done, total)`` ticks and alert banners.
* :class:`ExplanationCompanion` — renders an :class:`OperatorCockpit` together
  with a :class:`DecisionExplanation` for progressive disclosure.
* :func:`install_default_bridges` — convenience wiring of the two read-only
  bridges when only the cockpit and traffic surface are at hand.
"""

from __future__ import annotations

import logging
import time as _time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from ..governance.override_events import OverrideExpiredEvent
from ..ux.cockpit import (
    DecisionNotice,
    OperatorCockpit,
    OverrideExpiryNotice,
)
from ..ux.explanations import (
    DecisionExplanation,
    DisclosureLevel,
    render_explanation,
)
from ..ux.kpis.traffic import TrafficDashboard

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class BridgeResult:
    """Outcome of a bridge invocation.

    Bridges never raise to their caller — they surface anything unexpected
    through :attr:`errors` so the operator cockpit stays responsive even when
    upstream event logs are corrupt or absent.
    """

    accepted: int = 0
    dropped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """``True`` when no errors were encountered during bridging."""
        return not self.errors


# ---------------------------------------------------------------------------
# Tier mapping helper
# ---------------------------------------------------------------------------


def _notice_for(
    event: OverrideExpiredEvent,
    *,
    now_epoch: float | None = None,
) -> OverrideExpiryNotice:
    """Build an :class:`OverrideExpiryNotice` from an ``OverrideExpiredEvent``.

    The mapping is deterministic so audit-log replays produce stable output.
    The ``age_s`` on the notice is computed against the supplied clock
    (``now_epoch``) — when omitted, wall-clock at call time is used.
    """
    # NEW-3 (SOTA third-pass): route through ``_notice_age_s`` so the
    # age-fade contract (``negative deltas clamp to 0``) is enforced
    # in one place instead of being duplicated across modules.
    age_s = _notice_age_s(event.expired_at, now_epoch=now_epoch)
    return OverrideExpiryNotice(
        rule_id=event.override_id,
        owner=event.owner,
        reason=event.reason or "ttl_elapsed",
        expired_at=event.expired_at,
        age_s=age_s,
    )


# ---------------------------------------------------------------------------
# Override expiry bridge
# ---------------------------------------------------------------------------


class OverrideExpiryBridge:
    """Adapter pumping ``OverrideExpiredEvent`` lines into ``OperatorCockpit``.

    The bridge is stateless aside from the captured cockpit reference; it is
    safe to reuse across threads because
    :meth:`OperatorCockpit.record_override_event` is implemented with a lock.
    """

    def __init__(self, cockpit: OperatorCockpit) -> None:
        self._cockpit = cockpit

    def feed(self, event: OverrideExpiredEvent) -> BridgeResult:
        """Push a single ``OverrideExpiredEvent`` through the cockpit."""
        try:
            notice = _notice_for(event)
            self._cockpit.record_override_event(notice)
        except Exception as exc:  # noqa: BLE001 - bridge never raises.
            _LOGGER.warning("override bridge rejected event %s: %s", event, exc)
            return BridgeResult(errors=[str(exc)])
        return BridgeResult(accepted=1)

    def feed_many(self, events: Iterable[OverrideExpiredEvent]) -> BridgeResult:
        """Push a sequence of events and aggregate the bridge result."""
        result = BridgeResult()
        for event in events:
            sub = self.feed(event)
            result.accepted += sub.accepted
            result.dropped += sub.dropped
            result.errors.extend(sub.errors)
        return result

    def subscribe_to(
        self,
        emitter: Any,
        *,
        poll: Callable[[], Sequence[OverrideExpiredEvent]] | None = None,
    ) -> BridgeResult:
        """Drain an emitter or poll-callable once and forward the events.

        ``emitter`` is duck-typed: we accept any object whose ``drain()``
        method returns an iterable of ``OverrideExpiredEvent``. When ``poll``
        is supplied it wins — useful for tests and for callers that already
        have a pull-style loop.
        """
        if poll is not None:
            events = poll()
        else:
            drain = getattr(emitter, "drain", None)
            if drain is None:
                msg = "emitter has no drain(); pass poll=<callable> explicitly"
                raise ValueError(msg)
            events = drain()
        return self.feed_many(events)


# ---------------------------------------------------------------------------
# Traffic → cockpit bridge
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class TrafficTickPlan:
    """Plan a single ``tick()`` call against an operator cockpit.

    The cockpit's :meth:`tick` method is the only public surface for
    refreshing the live runs / overrides / progress pane. ``TrafficCockpitBridge``
    builds a :class:`TrafficTickPlan` rather than poking the cockpit directly
    so callers can inspect or adjust the plan before it lands.
    """

    progress: tuple[int, int]
    notice: OverrideExpiryNotice | None = None


class TrafficCockpitBridge:
    """Adapter pushing ``TrafficDashboard`` summaries into a cockpit.

    The bridge translates dashboard health into the cockpit's progress bar and
    triggers an :class:`OverrideExpiryNotice` when an error-rate threshold is
    crossed.
    """

    def __init__(
        self,
        cockpit: OperatorCockpit,
        *,
        error_rate_threshold: float = 0.05,
    ) -> None:
        self._cockpit = cockpit
        self._error_rate_threshold = error_rate_threshold
        self._dashboard: TrafficDashboard | None = None

    def plan(self, dashboard: TrafficDashboard) -> TrafficTickPlan:
        """Build a :class:`TrafficTickPlan` from the current dashboard state."""
        snap = dashboard.summary()
        count = int(snap.get("count", 0))
        window = max(int(snap.get("duration_ms_window", 60)), 1)
        error_rate = float(snap.get("error_rate", 0.0))
        plan = TrafficTickPlan(progress=(count, window))
        if error_rate >= self._error_rate_threshold:
            now = _time.time()
            plan.notice = OverrideExpiryNotice(
                rule_id="traffic-error-budget",
                owner="traffic-bridge",
                reason=f"error_rate={error_rate:.2%} exceeded threshold",
                expired_at=now,
                age_s=0.0,
            )
        return plan

    def push(self, dashboard: TrafficDashboard) -> BridgeResult:
        """Forward a dashboard snapshot through the cockpit."""
        try:
            tick_plan = self.plan(dashboard)
            self._cockpit.tick(progress=tick_plan.progress)
            if tick_plan.notice is not None:
                self._cockpit.record_override_event(tick_plan.notice)
        except Exception as exc:  # noqa: BLE001 - never propagate.
            _LOGGER.warning("traffic bridge rejected summary: %s", exc)
            return BridgeResult(errors=[str(exc)])
        return BridgeResult(accepted=1)

    def bind(self, dashboard: TrafficDashboard) -> TrafficCockpitBridge:
        """Bind a dashboard so subsequent :meth:`push` calls have a default."""
        self._dashboard = dashboard
        return self

    def push_default(self) -> BridgeResult:
        """Push the bound dashboard; raises if no dashboard has been bound."""
        if self._dashboard is None:
            msg = "TrafficCockpitBridge has no bound dashboard; call bind() first"
            raise RuntimeError(msg)
        return self.push(self._dashboard)


# ---------------------------------------------------------------------------
# Explanation companion
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class ExplanationCompanion:
    """Render an :class:`OperatorCockpit` with a paired :class:`DecisionExplanation`.

    The companion is intentionally a thin wrapper so it does not leak cockpit
    layout details into :mod:`thegent.ux.explanations`. Operators receive a
    single text blob (``render()``) plus a structured ``payload()`` view for
    telemetry.
    """

    cockpit: OperatorCockpit
    explanation: DecisionExplanation
    level: DisclosureLevel | int = DisclosureLevel.SUMMARY
    width: int = 80

    def payload(self) -> Mapping[str, Any]:
        """Return a structured payload ready for downstream JSONL logging."""
        return {
            "cockpit": self.cockpit.snapshot(),
            "explanation": {
                "title": self.explanation.title,
                "verdict": self.explanation.verdict,
                "reason": self.explanation.reason,
                "confidence": self.explanation.confidence,
                "level": int(self.level),
            },
        }

    def render(self) -> str:
        """Render cockpit snapshot + progressive disclosure blob as text."""
        cockpit_text = self.cockpit.render()
        explanation_text = render_explanation(
            self.explanation,
            level=self.level,
            width=self.width,
        )
        return f"{cockpit_text}\n\n---\n{explanation_text}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def iter_override_events(
    events: Iterable[OverrideExpiredEvent],
) -> Iterator[OverrideExpiredEvent]:
    """Pass-through iterator for :class:`OverrideExpiredEvent` sequences."""
    return iter(events)


def install_default_bridges(
    cockpit: OperatorCockpit,
    traffic: TrafficDashboard,
    *,
    error_rate_threshold: float = 0.05,
) -> tuple[OverrideExpiryBridge, TrafficCockpitBridge]:
    """Wire the two read-only bridges against the supplied cockpit and traffic.

    Returns the constructed bridges so callers can feed events on demand
    without reaching back into :mod:`thegent.ux.cockpit_bridge`.
    """
    traffic_bridge = TrafficCockpitBridge(
        cockpit,
        error_rate_threshold=error_rate_threshold,
    ).bind(traffic)
    return OverrideExpiryBridge(cockpit), traffic_bridge


# ---------------------------------------------------------------------------
# Decision bridge (WP-3001 -> WP-4001)
# ---------------------------------------------------------------------------


# Decision verdicts that should be surfaced as an inline banner.
# ``allow`` verdicts are common and would create banner noise; we only
# surface denies inline and accumulate the rest into the bounded deque.
_BANNER_VERDICTS = frozenset({"deny"})


def _notice_age_s(notice_ts: float, *, now_epoch: float | None = None) -> float:
    """Return ``max(0, now - notice_ts)`` for age-fade semantics.

    NEW-3 (SOTA third-pass): the inline ``max(0.0, now - ts)``
    computation was duplicated in :func:`_notice_for`,
    :func:`_decision_notice_for`, and the cockpit's banner / pane
    renderers. We centralise it here so the contract (``negative
    deltas clamp to 0``, ``now`` defaults to wall clock) is enforced
    in one place and tests can pin the behaviour without rebuilding
    the same expression across modules.
    """
    now = now_epoch if now_epoch is not None else _time.time()
    return max(0.0, now - notice_ts)


def _decision_notice_for(
    decision: Any,
    *,
    agent: str = "",
    lane: str = "standard",
    now_epoch: float | None = None,
) -> DecisionNotice:
    """Build a :class:`DecisionNotice` from a :class:`PolicyDecision`-like object.

    Duck-typed: accepts anything with ``verdict``, ``reason_code``,
    ``rule_id``, and ``reason`` attributes (or keys). The mapping is
    deterministic so audit-log replays produce stable output.
    """
    if isinstance(decision, Mapping):
        verdict = decision.get("verdict", "allow")
        reason_code = decision.get("reason_code", "")
        rule_id = decision.get("rule_id")
        reason = decision.get("reason", "")
        # Mapping callers rarely carry an evaluated_at; default to 0 so
        # the post-mapping ``if evaluated_at <= 0.0`` branch stamps
        # ``now`` (the supplied ``now_epoch`` or wall clock).
        evaluated_at_raw: float = 0.0
    else:
        verdict = getattr(decision, "verdict", "allow")
        reason_value = getattr(decision, "reason_code", "")
        reason_code = reason_value.value if hasattr(reason_value, "value") else str(reason_value)
        rule_id = getattr(decision, "rule_id", None)
        reason = getattr(decision, "reason", "")
        # PolicyDecision's evaluated_at timestamp drives the cockpit's
        # age-fade semantics; for duck-typed callers without it we fall
        # back to the supplied clock so the notice still surfaces.
        # NEW-2 (SOTA third-pass): the previous implementation called
        # ``getattr(decision, "evaluated_at", 0.0)`` twice — once here
        # and once again on the post-mapping line — which (a) wasted a
        # descriptor lookup, and (b) made the fallback ``or 0.0``
        # ambiguous (the second call would never see the original).
        # We capture it once into ``evaluated_at_raw`` and reuse it.
        evaluated_at_raw = getattr(decision, "evaluated_at", 0.0) or 0.0
    verdict_str = verdict.value if hasattr(verdict, "value") else str(verdict)
    evaluated_at = float(evaluated_at_raw)
    if evaluated_at <= 0.0:
        # ``_notice_age_s`` defaults to wall clock when ``now_epoch`` is
        # ``None``, so the inline fallback stays consistent with the
        # helper used by the banner/pane renderers.
        evaluated_at = now_epoch if now_epoch is not None else _time.time()
    return DecisionNotice(
        verdict=verdict_str,
        reason_code=str(reason_code),
        rule_id=rule_id,
        agent=str(agent),
        lane=str(lane),
        evaluated_at=evaluated_at,
        reason=str(reason or ""),
    )


class DecisionNoticeBridge:
    """Adapter pumping :class:`PolicyDecision` records into ``OperatorCockpit``.

    Bridges WP-3001 (``PolicyEngine.evaluate``) into the WP-4001 4-pane
    cockpit so verdicts appear inline as the runtime produces them.

    The bridge is stateless aside from the captured cockpit reference; it is
    safe to reuse across threads because
    :meth:`OperatorCockpit.record_decision` is implemented with a lock.
    """

    def __init__(self, cockpit: OperatorCockpit) -> None:
        self._cockpit = cockpit

    def feed(self, decision: Any, *, agent: str = "", lane: str = "standard") -> BridgeResult:
        """Push a single ``PolicyDecision``-like object through the cockpit."""
        try:
            notice = _decision_notice_for(decision, agent=agent, lane=lane)
            self._cockpit.record_decision(notice)
        except Exception as exc:  # noqa: BLE001 - bridge never raises.
            _LOGGER.warning("decision bridge rejected decision %s: %s", decision, exc)
            return BridgeResult(errors=[str(exc)])
        return BridgeResult(accepted=1)

    def feed_many(self, decisions: Iterable[Any], *, agent: str = "", lane: str = "standard") -> BridgeResult:
        """Push a sequence of decisions and aggregate the bridge result."""
        result = BridgeResult()
        for decision in decisions:
            sub = self.feed(decision, agent=agent, lane=lane)
            result.accepted += sub.accepted
            result.dropped += sub.dropped
            result.errors.extend(sub.errors)
        return result

    def surface_banner_verdicts(self) -> frozenset[str]:
        """Return the verdict set the bridge treats as banner-worthy.

        Exposed so callers / tests can assert the contract stays stable.
        """
        return _BANNER_VERDICTS


__all__ = [
    "BridgeResult",
    "DecisionNoticeBridge",
    "ExplanationCompanion",
    "OverrideExpiryBridge",
    "TrafficCockpitBridge",
    "TrafficTickPlan",
    "install_default_bridges",
    "iter_override_events",
]
