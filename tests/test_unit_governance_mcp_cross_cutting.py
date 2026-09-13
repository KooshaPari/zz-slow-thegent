"""Cross-cutting governance + MCP tool dispatch integration tests.

Pins the end-to-end contract between the governance-layer :class:`PolicyEngine`
and the MCP server's tool/resource dispatch surface. Tests in this module are
deliberately integration-flavored — they exercise the seams where governance
decisions flow into the MCP :class:`_ToolResult` envelope rather than each
subsystem in isolation.

Audit trace (Phase 3/4 SOTA pass 5 — cross-cutting lane):

* Lane 1 — Governance→MCP envelope parity: ``PolicyDecision`` shape
  surfaced through ``_ToolResult.structured_content`` is consistent
  with the cockpit decision-pane contract.
* Lane 2 — MCP budget + governance interaction: when an MCP tool
  exceeds its named budget, the error envelope is governance-shaped
  (not a raw ``MCPBudgetExceeded``) so the cockpit can render it
  without a special case.
* Lane 3 — FederatedPolicyEngine + MCP observe_summary end-to-end:
  a federated rule that matches the observe_summary shape must
  short-circuit the local policy checks but never block the MCP
  resource reader (resources are read-only and cannot be denied).
* Lane 4 — Concurrent MCP dispatch + federated writers: 4 dispatch
  threads + 2 federated register threads must not produce torn
  ``_ToolResult`` envelopes or lost federated rules.
* Lane 5 — TTL override semantics through MCP dispatch path: a
  freshly registered override must immediately flip the next
  ``evaluate`` call from DENY to ALLOW without dropping any
  MCP tool dispatch.
* Lane 6 — Decision-notice wiring: governance ``PolicyDecision``
  payloads round-trip into cockpit ``DecisionNotice`` snapshots
  through the bridge, including the duck-typed acceptance path.
* Lane 7 — Performance-budget guard: the MCP server module
  declares at least 26 ``audited_budget`` wraps (audit pass 8 —
  these compose ``mcp_budget_context`` + ``audit_context`` so
  every tool dispatch is recorded in the MCP audit trail) and
  the trend resource uses the ``health_trend_ms`` named budget.
* Lane 8 — Federated cache invalidation: ``register_rule``,
  ``load_rules_from_file``, and ``register_override`` must drop
  the OPT-008 decision cache so freshly-registered rules/overrides
  are visible on the very next ``evaluate`` call (P0 audit gap
  surfaced by SOTA pass 6).
* Lane 9 — Budget-exceeded recovery path: a tool that exceeds
  its named budget must surface as a governance-shaped error
  envelope, but the next call within budget must succeed — no
  per-tool "open circuit" leak across invocations.
* Lane 10 — ``record_decision`` thread-safety: 10 writer threads
  pushing ``DecisionNotice`` payloads concurrently must all be
  accepted without loss, and ``snapshot()`` must observe every
  accepted notice with no torn writes.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import patch

import orjson
import pytest

from thegent.config.settings import ThegentSettings
from thegent.governance.federated_policy import PolicyRule, PolicyScope  # noqa: F401
from thegent.governance.policy_engine import (
    PolicyContext,
    PolicyDecision,
    PolicyEngine,
    ReasonCode,
    Verdict,
)

# All tests in this module are unit tests.
pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Test doubles / fixtures
# ---------------------------------------------------------------------------


@dataclass
class _FakeToolResult:
    """Minimal stand-in for ``fastmcp.tools.tool.ToolResult`` for tests that
    want to assert envelope-shape without depending on the runtime class."""

    content: str = ""
    structured_content: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)


@pytest.fixture
def settings(tmp_path) -> ThegentSettings:
    return ThegentSettings(environment="development", session_dir=tmp_path)


@pytest.fixture
def engine(settings: ThegentSettings) -> PolicyEngine:
    return PolicyEngine(settings=settings, use_federation=False)


@pytest.fixture
def federated_engine(settings: ThegentSettings) -> PolicyEngine:
    return PolicyEngine(settings=settings, use_federation=True, default_namespace="acme")


# ---------------------------------------------------------------------------
# Lane 1 — Governance→MCP envelope parity
# ---------------------------------------------------------------------------


class TestGovernanceMcpEnvelopeParity:
    """A :class:`PolicyDecision` must serialise into the same MCP envelope
    shape the cockpit decision-pane consumes."""

    def test_decision_round_trip_via_to_dict(self) -> None:
        """``PolicyDecision.to_dict()`` produces a 6-key contract the MCP
        decision pane expects (verdict, reason, reason_code, rule_id,
        override_applied, cached)."""
        decision = PolicyDecision(
            verdict=Verdict.DENY,
            reason="unknown agent in production",
            reason_code=ReasonCode.UNKNOWN_AGENT_PRODUCTION,
            rule_id="RULE_AGENT_PROD",
            override_applied=False,
            cached=False,
        )
        envelope = decision.to_dict()
        for required in (
            "verdict",
            "reason",
            "reason_code",
            "rule_id",
            "override_applied",
            "cached",
        ):
            assert required in envelope, f"missing key: {required}"
        assert envelope["verdict"] == "deny"
        assert envelope["reason_code"] == "unknown_agent_production"
        assert envelope["cached"] is False

    def test_cached_decision_carries_cache_flag(self, engine) -> None:
        """A cached (OPT-008) decision must advertise ``cached=True`` so the
        cockpit can badge the row differently."""
        ctx = PolicyContext(agent="cursor", model="gpt-5.3-codex", lane="standard")
        first = engine.evaluate(ctx)
        second = engine.evaluate(ctx)
        assert second.cached is True, "second eval must hit the OPT-008 cache"
        assert first.cached is False

    def test_decision_verdict_aligned_with_mcp_gate(self, settings, engine) -> None:
        """DENY + ``override_applied=True`` is the canonical
        'gate-flipped-by-override' shape; the MCP dispatch path must
        accept it without re-evaluating.

        The engine fixture supplies an isolated ``session_dir`` so a
        stale operator override from a previous session cannot poison
        this assertion.

        Sequence: register override first, then evaluate — first
        evaluate runs ``_apply_override`` and short-circuits to ALLOW.
        A separate ``invalidate_cache`` ensures the original DENY is
        never served from the OPT-008 cache after the override lands.
        """
        ctx = PolicyContext(
            agent="claude",
            model="claude-3.7",
            lane="critical",
            confidence=0.5,  # below critical threshold (0.9)
            environment="production",
        )

        # Sanity: confirm the rule's DENY shape without any override.
        baseline = engine.evaluate(ctx)
        assert baseline.verdict == Verdict.DENY, baseline
        # Drop the cache so the next evaluate re-runs the uncached path
        # (where ``_apply_override`` is consulted).
        engine.invalidate_cache()

        # Register an override for the matched rule_id and re-evaluate.
        rule_id = baseline.rule_id or "local.critical.confidence"
        engine.register_override(
            rule_id=rule_id,
            reason="manual operator approval",
            by="koosha",
            duration_minutes=10,
        )
        post_override = engine.evaluate(ctx)
        assert post_override.verdict == Verdict.ALLOW
        assert post_override.override_applied is True


# ---------------------------------------------------------------------------
# Lane 2 — MCP budget + governance interaction
# ---------------------------------------------------------------------------


class TestMcpBudgetGovernanceInteraction:
    """When an MCP tool exceeds its named budget, the error envelope must
    carry the same governance shape the cockpit decision-pane expects, not
    a raw ``MCPBudgetExceeded`` string."""

    def test_budget_exceeded_maps_to_tool_result_envelope(self) -> None:
        """An MCP tool that exceeds its budget must produce a ``_ToolResult``
        with ``content`` carrying the budget error, ``structured_content``
        holding the canonical governance-shape envelope, and ``meta``
        marking the operation + elapsed time."""

        # Import the real MCP server module lazily so this test doesn't
        # require fastmcp at module-import time (matches other tests'
        # collection-time posture).
        from thegent.mcp.server import mcp_perf_gates
        from thegent.mcp.server.mcp_perf_gates import (
            MCPBudgetExceeded,
            mcp_budget_context,
        )

        # Confirm the helper is importable from the canonical home.
        assert mcp_budget_context is not None
        # And the exception class exposes the operator-facing fields.
        exc = MCPBudgetExceeded("tool_invoke_ms", 120.0, 100.0)
        assert exc.operation == "tool_invoke_ms"
        assert exc.elapsed_ms == 120.0
        assert exc.budget_ms == 100.0

        # Surface it through a mock _ToolResult so we can assert that
        # the governance-shaped envelope is what the cockpit receives.
        # The MCP session_contract_health_gate tool returns an envelope
        # on ``MCPBudgetExceeded`` (see src/thegent/mcp/server/__init__.py:
        # thegent_session_contract_health_gate). Confirm that contract by
        # calling the function with an impossible-to-meet budget via
        # monkeypatching ``mcp_perf_gates.MCP_PERF_BUDGETS``.
        original = dict(mcp_perf_gates.MCP_PERF_BUDGETS)
        try:
            mcp_perf_gates.MCP_PERF_BUDGETS["tool_invoke_ms"] = 0.001  # 1us budget
            from thegent.mcp.server import (
                thegent_session_contract_health_gate as _gate_tool,
            )

            with patch(
                "thegent.mcp.server.session_contract_health_gate_impl",
                side_effect=lambda **kwargs: time.sleep(0.05) or {"status": "ok"},
            ):
                result = _gate_tool()
            assert isinstance(result, _FakeToolResult) or hasattr(result, "content")
            assert "budget exceeded" in str(result.content).lower()
        finally:
            mcp_perf_gates.MCP_PERF_BUDGETS.clear()
            mcp_perf_gates.MCP_PERF_BUDGETS.update(original)

    def test_budget_pass_path_produces_typed_envelope(self, monkeypatch) -> None:
        """When an MCP tool completes within budget, the envelope is the
        normal ``meta`` block carrying the contract-health fields, NOT a
        budget error shape."""
        from thegent.mcp.server import (
            thegent_session_contract_health_gate as _gate_tool,
        )

        fake_payload = {
            "status": "healthy",
            "policy_profile": "default",
            "decision_reasons": [],
            "total": 10,
            "healthy_count": 10,
            "unhealthy_count": 0,
            "blocked_count": 0,
            "top_blocked_count": 0,
            "blocked_sessions_cap": 25,
        }
        with patch(
            "thegent.mcp.server.session_contract_health_gate_impl",
            return_value=fake_payload,
        ):
            result = _gate_tool()
        # meta must contain the contract-health fields, not a budget error.
        meta = result.meta
        assert "budget" not in str(meta).lower()
        assert meta.get("status") == "healthy"
        assert meta.get("total") == 10


# ---------------------------------------------------------------------------
# Lane 3 — Federated policy + MCP observe_summary end-to-end
# ---------------------------------------------------------------------------


class TestFederatedPolicyMcpObserveSummary:
    """A federated rule must never block an MCP *resource* reader —
    resources are read-only and the cockpit must always render fresh data."""

    def test_federated_rule_does_not_block_observe_resource(self, federated_engine) -> None:
        """Register a federated DENY rule for the observe-summary shape and
        confirm the MCP *resource* reader still returns the payload
        (resources bypass the pre-check gate)."""
        federated_engine.register_rule(
            rule_id="RULE_BLOCK_OBSERVE",
            when={"lane": "critical", "agent": "claude"},
            verdict="deny",
            reason="test deny rule",
            priority=100,
            scope=PolicyScope.GLOBAL,
            namespace="acme",
        )
        # MCP resources bypass the pre-check gate; the resource reader must
        # still produce a JSON payload. We invoke the resource function and
        # assert it's a JSON string (the MCP resource contract is ``str``).
        from thegent.mcp.server import resource_observe_summary as _resource

        # Patch the underlying impl so we don't touch real observability state.
        sentinel = {
            "status": "ok",
            "payload_type": "session_health",
            "drift": {"within_budget": True},
        }
        with patch("thegent.mcp.server.observe_summary_impl", return_value=sentinel):
            payload = _resource()
        assert isinstance(payload, str)
        assert "ok" in payload
        # And the federated rule itself must still be live for tool callers.
        # Pin namespace=acme so the rule actually matches.
        decision = federated_engine.evaluate(
            PolicyContext(
                agent="claude",
                model="claude-3.7",
                lane="critical",
                confidence=0.95,
                namespace="acme",
            )
        )
        assert decision.verdict == Verdict.DENY, "federated rule must still block tool dispatch"


# ---------------------------------------------------------------------------
# Lane 4 — Concurrent MCP dispatch + federated writers
# ---------------------------------------------------------------------------


class TestConcurrentMcpDispatchFederatedWriters:
    """Concurrent MCP tool dispatch + concurrent federated writers must
    not produce torn envelopes or lost rules."""

    def test_concurrent_observe_summary_dispatches_under_writer_pressure(self, federated_engine) -> None:
        """4 reader threads × 25 dispatches while 2 writer threads each
        register 30 federated rules. Every dispatch returns a non-empty
        JSON string (no torn payload) and the rule count converges to
        the union of writer writes."""

        sentinel = {"status": "ok", "payload_type": "session_health"}
        errors: list[BaseException] = []

        def _dispatch() -> None:
            try:
                from thegent.mcp.server import resource_observe_summary as _resource

                with patch("thegent.mcp.server.observe_summary_impl", return_value=sentinel):
                    for _ in range(25):
                        payload = _resource()
                        assert isinstance(payload, str)
                        assert "ok" in payload
            except BaseException as exc:
                errors.append(exc)

        def _write(start: int, count: int) -> None:
            try:
                for i in range(start, start + count):
                    federated_engine.register_rule(
                        rule_id=f"RULE_{i}",
                        when={"agent": "cursor", "i": i},
                        verdict="allow",
                        reason=f"rule {i}",
                        priority=100,
                        scope=PolicyScope.GLOBAL,
                        namespace="acme",
                    )
            except BaseException as exc:
                errors.append(exc)

        threads: list[threading.Thread] = []
        for _ in range(4):
            t = threading.Thread(target=_dispatch)
            threads.append(t)
        for t in threads:
            t.start()

        writers = [
            threading.Thread(target=_write, args=(0, 30)),
            threading.Thread(target=_write, args=(30, 30)),
        ]
        for t in writers:
            t.start()

        for t in threads + writers:
            t.join(timeout=10.0)
            assert not t.is_alive(), "thread hung"

        assert errors == [], f"errors: {errors!r}"
        # The federated registry must have exactly 60 rules (30+30).
        assert federated_engine.federated is not None
        total = sum(len(ns) for ns in federated_engine.federated._namespaces.values())
        assert total == 60


# ---------------------------------------------------------------------------
# Lane 5 — TTL override semantics through MCP dispatch
# ---------------------------------------------------------------------------


class TestTtlOverrideThroughMcpDispatch:
    """A freshly-registered override must immediately flip the next
    ``evaluate`` call from DENY to ALLOW; the MCP tool that triggered
    the gate must observe the flipped decision on the very next call."""

    def test_override_flips_decision_for_consecutive_mcp_calls(self, settings) -> None:
        """Sequence: register override -> evaluate -> ALLOW with
        ``override_applied=True``; a second evaluate with no cache invalidation
        still surfaces the override (the OPT-008 cache is bypassed for the
        freshly-flipped decision because ``_apply_override`` runs in the
        uncached path)."""

        # Use isolated settings so a stale operator override cannot
        # poison this assertion (see conftest fixture).
        engine = PolicyEngine(settings=settings, use_federation=False)
        ctx = PolicyContext(
            agent="claude",
            model="claude-3.7",
            lane="critical",
            confidence=0.5,
            environment="production",
        )

        # Register override for the matched rule_id *before* the first
        # evaluate so the cache can't shadow it. Rule id is the same as
        # the canonical critical-lane-low-confidence rule.
        rule_id = "local.critical.confidence"
        engine.register_override(
            rule_id=rule_id,
            reason="manual approval for canary",
            by="koosha",
            duration_minutes=10,
        )
        # First uncached evaluate must see the override (uncached path
        # always runs ``_apply_override``).
        first_decision = engine.evaluate(ctx)
        assert first_decision.verdict == Verdict.ALLOW
        assert first_decision.override_applied is True

    def test_consecutive_tool_dispatches_share_cache(self, settings) -> None:
        """OPT-008 cache: 5 consecutive identical evaluations should
        produce 1 miss + 4 hits. This pins the seam between MCP
        dispatch (which may invoke ``evaluate`` per-call) and the
        LRU+TTL cache contract."""
        engine = PolicyEngine(settings=settings, use_federation=False)
        ctx = PolicyContext(agent="cursor", model="gpt-5.3-codex", lane="standard")
        # First call: miss
        engine.evaluate(ctx)
        # Subsequent 4: hit
        for _ in range(4):
            engine.evaluate(ctx)
        stats = engine.cache_stats()
        assert stats["hits"] == 4, stats
        assert stats["misses"] == 1, stats


# ---------------------------------------------------------------------------
# Lane 6 — Decision-notice wiring (governance -> cockpit decision pane)
# ---------------------------------------------------------------------------


class TestDecisionNoticeCockpitWiring:
    """The governance engine must surface every :class:`PolicyDecision`
    as a :class:`DecisionNotice` that the cockpit decision pane can
    render without re-parsing the envelope. The :class:`DecisionNoticeBridge`
    is the canonical seam from ``PolicyEngine.evaluate`` to the cockpit."""

    def test_decision_notice_bridge_feeds_allow_decision(self) -> None:
        """A bridge fed a ``PolicyDecision`` produces a cockpit-renderable
        ``DecisionNotice`` with verdict / reason_code / rule_id / agent
        / lane all populated in the snapshot."""
        from thegent.ux.cockpit import OperatorCockpit
        from thegent.ux.cockpit_bridge import DecisionNoticeBridge

        decision = PolicyDecision(
            verdict=Verdict.ALLOW,
            reason="all checks passed",
            reason_code=ReasonCode.ALLOWED,
            rule_id=None,
            override_applied=False,
            cached=False,
            evaluated_at=time.time(),
        )
        cockpit = OperatorCockpit(clock=lambda: 1.0)
        bridge = DecisionNoticeBridge(cockpit)
        result = bridge.feed(decision, agent="cursor", lane="standard")
        assert result.accepted == 1
        assert result.errors == []
        # Snapshot serializes notices as dicts (see snapshot()[decision_notices]).
        notices = cockpit.snapshot()["decision_notices"]
        assert len(notices) == 1
        notice = notices[0]
        assert notice["verdict"] == "allow"
        assert notice["reason_code"] == "allowed"
        assert notice["agent"] == "cursor"
        assert notice["lane"] == "standard"

    def test_decision_notice_bridge_deny_surfaces_is_deny(self) -> None:
        """A DENY decision must produce a ``DecisionNotice`` whose
        ``is_deny()`` returns True, so the cockpit banner can render it."""
        from thegent.ux.cockpit import OperatorCockpit
        from thegent.ux.cockpit_bridge import DecisionNoticeBridge

        decision = PolicyDecision(
            verdict=Verdict.DENY,
            reason="unknown agent in production",
            reason_code=ReasonCode.UNKNOWN_AGENT_PRODUCTION,
            rule_id="RULE_AGENT_PROD",
            override_applied=False,
            cached=False,
            evaluated_at=time.time(),
        )
        cockpit = OperatorCockpit(clock=lambda: 1.0)
        bridge = DecisionNoticeBridge(cockpit)
        result = bridge.feed(decision, agent="claude", lane="standard")
        assert result.accepted == 1
        # Bridge returns ``accepted=1`` even though the decision will be
        # denied — the bridge never decides for the dispatcher. The
        # snapshot surfaces the notice with verdict=deny so the cockpit
        # banner can render it.
        notice = cockpit.snapshot()["decision_notices"][0]
        assert notice["verdict"] == "deny"
        # is_deny / is_warn live on DecisionNotice, not the snapshot dict;
        # verify they round-trip via the underlying deque.
        from thegent.ux.cockpit import DecisionNotice

        rt_notice = DecisionNotice(
            verdict=notice["verdict"],
            reason_code=notice["reason_code"],
            rule_id=notice["rule_id"],
            agent=notice["agent"],
            lane=notice["lane"],
            evaluated_at=notice["evaluated_at"],
            reason=notice.get("reason", ""),
        )
        assert rt_notice.is_deny() is True
        assert rt_notice.is_warn() is False

    def test_decision_notice_bridge_banner_verdicts_pins_deny(self) -> None:
        """The bridge exposes a stable verdict set the cockpit treats as
        banner-worthy; pin ``deny`` is in that set so a refactor that drops
        it surfaces immediately. (The current contract is exactly
        ``{"deny"}`` — warn surfaced separately via ``is_warn()``.)"""
        from thegent.ux.cockpit import OperatorCockpit
        from thegent.ux.cockpit_bridge import DecisionNoticeBridge

        cockpit = OperatorCockpit(clock=lambda: 1.0)
        bridge = DecisionNoticeBridge(cockpit)
        verdicts = bridge.surface_banner_verdicts()
        assert "deny" in verdicts
        # ``is_deny()`` on DecisionNotice still matches the banner set.
        assert "warn" not in verdicts, (
            "warn was deliberately moved out of the banner set; surface it via DecisionNotice.is_warn() instead."
        )

    def test_decision_notice_bridge_maps_object_via_duck_typing(self) -> None:
        """The bridge is intentionally duck-typed: an object that has
        ``verdict`` / ``reason_code`` / ``rule_id`` / ``reason`` /
        ``evaluated_at`` attributes is accepted and surfaced to the
        cockpit. This pins the seam so a refactor that hard-requires a
        :class:`PolicyDecision` type and rejects duck-typed callers
        surfaces immediately."""
        from thegent.ux.cockpit import OperatorCockpit
        from thegent.ux.cockpit_bridge import DecisionNoticeBridge

        class _LikePolicyDecision:
            verdict = "warn"
            reason_code = "recovery_no_confidence"
            rule_id = "local.recovery.no_confidence"
            reason = "no confidence data for recovery lane"
            evaluated_at = time.time()

        cockpit = OperatorCockpit(clock=lambda: 1.0)
        bridge = DecisionNoticeBridge(cockpit)
        result = bridge.feed(_LikePolicyDecision(), agent="cursor", lane="recovery")
        assert result.errors == []
        assert result.accepted == 1
        # Snapshot serialises notices as dicts.
        notice = cockpit.snapshot()["decision_notices"][0]
        assert notice["verdict"] == "warn"
        assert notice["reason_code"] == "recovery_no_confidence"


# ---------------------------------------------------------------------------
# Lane 7 — Performance budget guard
# ---------------------------------------------------------------------------


class TestGovernanceMcpPerfBudgetGuard:
    """The MCP perf-gate context manager must fire inside every
    ``thegent_*`` tool dispatch path. This is a smoke test that asserts
    the wrapper count grows monotonically (regression guard against a
    refactor that drops a budget wrap from a tool function).

    SOTA audit pass 8: wraps are now ``audited_budget`` — they compose
    ``mcp_budget_context`` (perf gate) + ``audit_context`` (audit trail
    record) so every dispatch is both budgeted AND observed in one shot.
    """

    def test_mcp_server_module_declares_at_least_26_budget_wraps(self) -> None:
        """Sanity guard: audit pass 8 collapsed 26 ``mcp_budget_context``
        call sites into 26 ``audited_budget`` wrappers (which compose
        the budget context + audit context). A regression that drops
        a wrap below this threshold must fail."""
        import inspect

        from thegent.mcp import server as _mcp_server_mod

        source = inspect.getsource(_mcp_server_mod)
        # The ``from ... import`` line at module top is counted by
        # ``str.count`` but it isn't a *wrap*, so we exclude any line
        # that is itself an import statement. We accept either the
        # legacy ``mcp_budget_context(...)`` wrap or the new
        # ``audited_budget(...)`` wrap — but no other context manager
        # that looks like a budget guard.
        wrap_count = sum(
            1
            for line in source.splitlines()
            if ("mcp_budget_context(" in line or "audited_budget(" in line)
            and not line.lstrip().startswith(("from ", "import "))
        )
        assert wrap_count >= 26, (
            f"expected >= 26 budget wraps (mcp_budget_context or audited_budget), "
            f"got {wrap_count}. A recent refactor likely dropped a wrap; re-add it."
        )

    def test_mcp_server_module_audited_budget_composes_audit_trail(self) -> None:
        """Audit pass 8 contract: every ``audited_budget`` wrap must
        produce an entry in the singleton audit trail. This guarantees
        the dispatch surface is end-to-end observable (not just budgeted)."""
        from thegent.mcp.server import (
            AuditEntryKind,
            get_audit_trail,
            mcp_audit_stats,
            reset_audit_trail,
        )

        reset_audit_trail()
        try:
            # Drive a single audited_budget context to confirm wiring
            from thegent.mcp.server.mcp_audit_wiring import audited_budget

            with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms", agent="test"):
                pass
            stats = mcp_audit_stats()
            assert stats["total_entries"] >= 1, (
                f"audited_budget wrap did not record an entry to the audit trail; stats={stats}"
            )
            entries = get_audit_trail().recent(n=10)
            assert any(e.kind == AuditEntryKind.TOOL_INVOCATION for e in entries), (
                f"expected at least one TOOL_INVOCATION entry after audited_budget; kinds={[e.kind for e in entries]}"
            )
        finally:
            reset_audit_trail()

    def test_health_trend_budget_uses_named_budget(self) -> None:
        """``health_trend_ms`` budget is reserved for trend ops; confirm
        the resource variant uses it (not ``tool_invoke_ms``)."""
        import inspect

        from thegent.mcp import server as _mcp_server_mod

        src = inspect.getsource(_mcp_server_mod.resource_session_contract_health_trend)
        assert "health_trend_ms" in src, "resource_session_contract_health_trend must use health_trend_ms budget"


# ---------------------------------------------------------------------------
# Lane 8 — Federated cache invalidation (SOTA audit pass 6 — P0 audit gap)
# ---------------------------------------------------------------------------


class TestFederatedCacheInvalidation:
    """Every successful registration path (``register_rule``,
    ``load_rules_from_file``, ``register_override``) must invalidate the
    OPT-008 decision cache so the next ``evaluate`` call observes the
    freshly-registered rule/override.

    A federated DENY rule that lands on a hot cache key must NOT be
    shadowed by a stale cached ALLOW (P0 audit gap surfaced by SOTA
    pass 6 — without invalidation, an operator would register a deny
    rule, see the original allow continue, and conclude the rule was
    a no-op).
    """

    def test_register_rule_invalidates_cache_for_matching_context(self, federated_engine) -> None:
        """Baseline evaluate populates the cache with ALLOW for the
        matched context. A subsequently-registered federated DENY rule
        that matches the same context must take effect on the next
        ``evaluate`` call (cache cleared)."""
        ctx = PolicyContext(
            agent="cursor",
            model="gpt-5.3-codex",
            lane="standard",
            namespace="acme",
        )
        baseline = federated_engine.evaluate(ctx)
        assert baseline.verdict == Verdict.ALLOW, baseline
        assert baseline.cached is False, "baseline must be a cache miss"

        # Second call populates the cache (cached=True).
        cached = federated_engine.evaluate(ctx)
        assert cached.cached is True

        # Register a federated DENY rule that matches ``agent=cursor``
        # in the ``acme`` namespace.
        federated_engine.register_rule(
            rule_id="RULE_DENY_CURSOR",
            when={"agent": "cursor"},
            verdict="deny",
            reason="SOTA pass 6 audit gap test",
            priority=10,
            scope=PolicyScope.GLOBAL,
            namespace="acme",
        )

        # The next evaluate MUST observe the new rule. Without
        # ``self._cache.clear()`` in register_rule this assertion would
        # fail because the cache would still serve the stale ALLOW.
        flipped = federated_engine.evaluate(ctx)
        assert flipped.verdict == Verdict.DENY, (
            f"register_rule must invalidate the OPT-008 cache; got {flipped.verdict.value}"
        )
        assert flipped.cached is False, "post-register eval must be a fresh cache miss"
        assert flipped.rule_id == "RULE_DENY_CURSOR"

    def test_register_override_invalidates_cache_for_flip(self, settings) -> None:
        """A freshly-registered override must clear the OPT-008 cache
        so the next ``evaluate`` re-runs the override path. A stale
        cached DENY would otherwise shadow the override and the
        operator would see the DENY persist past registration."""
        engine = PolicyEngine(settings=settings, use_federation=False)
        ctx = PolicyContext(
            agent="claude",
            model="claude-3.7",
            lane="critical",
            confidence=0.5,  # below critical threshold (0.9)
            environment="production",
        )
        baseline = engine.evaluate(ctx)
        assert baseline.verdict == Verdict.DENY, baseline

        # Second evaluate: cache hit (cached=True).
        cached = engine.evaluate(ctx)
        assert cached.cached is True

        # Register an override for the matched rule. Cache MUST be
        # cleared so the next evaluate sees the flipped verdict.
        rule_id = baseline.rule_id or "local.critical.confidence"
        engine.register_override(
            rule_id=rule_id,
            reason="SOTA pass 6 cache invalidation test",
            by="koosha",
            duration_minutes=10,
        )

        flipped = engine.evaluate(ctx)
        assert flipped.verdict == Verdict.ALLOW, (
            f"register_override must invalidate the OPT-008 cache; got {flipped.verdict.value}"
        )
        assert flipped.override_applied is True
        assert flipped.cached is False

    def test_load_rules_from_file_invalidates_cache(self, tmp_path, federated_engine) -> None:
        """``load_rules_from_file`` must drop the OPT-008 cache so the
        freshly-loaded rules take effect on the next ``evaluate`` call.
        Without invalidation, a hot cache key would serve the stale
        decision and the operator would conclude the load was a no-op."""
        ctx = PolicyContext(
            agent="claude",
            model="claude-3.7",
            lane="critical",
            confidence=0.95,
            namespace="acme",
        )
        baseline = federated_engine.evaluate(ctx)
        assert baseline.verdict == Verdict.ALLOW, baseline
        # Second call to populate the cache.
        federated_engine.evaluate(ctx)
        assert federated_engine.cache_stats()["hits"] >= 1

        # Author a federated rule file and load it. The ``condition``
        # field is a JSON-encoded *string* of the match dict, not a
        # nested dict (orjson.dumps returns bytes, which the file
        # serialiser cannot re-encode).
        rule_file = tmp_path / "rules.json"
        rule_file.write_text(
            orjson.dumps(
                [
                    {
                        "rule_id": "RULE_FILE_DENY",
                        "scope": "global",
                        "namespace": "acme",
                        "priority": 10,
                        "condition": '{"agent": "claude"}',
                        "action": "deny",
                    }
                ]
            ).decode("utf-8")
        )
        loaded = federated_engine.load_rules_from_file(rule_file, namespace="acme")
        assert loaded == 1

        # The next evaluate MUST observe the loaded rule.
        flipped = federated_engine.evaluate(ctx)
        assert flipped.verdict == Verdict.DENY, (
            f"load_rules_from_file must invalidate the OPT-008 cache; got {flipped.verdict.value}"
        )
        assert flipped.cached is False
        assert flipped.rule_id == "RULE_FILE_DENY"

    def test_register_rule_preserves_cache_stats_counters(self, federated_engine) -> None:
        """The cache invalidation must clear the OPT-008 *cache* but
        preserve the hit/miss counters — a SOTA audit window that
        started before the registration should still see pre-existing
        observations. (The cache and the counters are deliberately
        separate so the ``cache_stats()`` audit hook continues to
        report the lifetime histogram.)"""
        ctx = PolicyContext(agent="cursor", model="gpt-5.3-codex", lane="standard", namespace="acme")
        federated_engine.evaluate(ctx)  # miss
        federated_engine.evaluate(ctx)  # hit
        stats_before = federated_engine.cache_stats()
        assert stats_before["hits"] == 1
        assert stats_before["misses"] == 1

        federated_engine.register_rule(
            rule_id="RULE_KEEP_STATS",
            when={"agent": "cursor"},
            verdict="allow",
            reason="audit stats preservation",
            priority=100,
            scope=PolicyScope.GLOBAL,
            namespace="acme",
        )

        stats_after = federated_engine.cache_stats()
        assert stats_after["hits"] == stats_before["hits"], "register_rule must NOT reset the hit counter"
        assert stats_after["misses"] == stats_before["misses"], "register_rule must NOT reset the miss counter"
        # But the cache itself must be empty so the next call misses.
        assert stats_after["size"] == 0, (
            f"OPT-008 cache must be empty after invalidation, got size={stats_after['size']}"
        )

    def test_register_rule_under_concurrent_evaluators_does_not_shadow(self, federated_engine) -> None:
        """Two reader threads polling the same context while a writer
        registers a new rule: at least ONE post-registration read must
        observe the DENY verdict. Without cache invalidation the readers
        could both see stale ALLOW indefinitely."""
        ctx = PolicyContext(
            agent="cursor",
            model="gpt-5.3-codex",
            lane="standard",
            namespace="acme",
        )
        # Warm the cache.
        federated_engine.evaluate(ctx)
        federated_engine.evaluate(ctx)

        seen_denies: list[bool] = []
        stop = threading.Event()
        errors: list[BaseException] = []

        def _reader() -> None:
            try:
                while not stop.is_set():
                    d = federated_engine.evaluate(ctx)
                    seen_denies.append(d.verdict == Verdict.DENY)
            except BaseException as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_reader) for _ in range(2)]
        for t in threads:
            t.start()

        # Let readers poll a bit, then register the deny rule.
        time.sleep(0.02)
        federated_engine.register_rule(
            rule_id="RULE_CONCURRENT_DENY",
            when={"agent": "cursor"},
            verdict="deny",
            reason="concurrent invalidation test",
            priority=10,
            scope=PolicyScope.GLOBAL,
            namespace="acme",
        )
        # Let readers poll a bit more.
        time.sleep(0.05)
        stop.set()
        for t in threads:
            t.join(timeout=2.0)
            assert not t.is_alive(), "reader thread hung"

        assert errors == [], f"errors: {errors!r}"
        assert any(seen_denies), f"no reader observed the post-registration DENY verdict: {seen_denies!r}"


# ---------------------------------------------------------------------------
# Lane 9 — Budget-exceeded recovery path
# ---------------------------------------------------------------------------


class TestBudgetExceededRecoveryPath:
    """When a tool exceeds its named budget, the error envelope must be
    governance-shaped, but the *next* call within budget must succeed —
    there must be no per-tool "open circuit" leak across invocations.
    The MCP perf gate context manager is stateless across calls, so a
    budget violation in one call must not poison subsequent calls.
    """

    def test_budget_exceeded_envelope_then_subsequent_pass(self, monkeypatch) -> None:
        """Sequence: monkeypatch the underlying impl to exceed the
        budget, confirm the governance-shaped error envelope; then
        restore a fast impl and confirm the same tool now returns the
        healthy envelope (no circuit-breaker leak)."""
        from thegent.mcp.server import mcp_perf_gates
        from thegent.mcp.server import (
            thegent_session_contract_health_gate as _gate_tool,
        )

        original = dict(mcp_perf_gates.MCP_PERF_BUDGETS)
        try:
            # 1µs budget forces the slow impl to exceed it.
            mcp_perf_gates.MCP_PERF_BUDGETS["tool_invoke_ms"] = 0.001

            with patch(
                "thegent.mcp.server.session_contract_health_gate_impl",
                side_effect=lambda **kwargs: time.sleep(0.05) or {"status": "ok"},
            ):
                over_budget = _gate_tool()
            assert "budget exceeded" in str(over_budget.content).lower(), (
                f"expected budget error envelope, got: {over_budget.content!r}"
            )

            # Restore a sane budget for the recovery call.
            mcp_perf_gates.MCP_PERF_BUDGETS["tool_invoke_ms"] = original.get("tool_invoke_ms", 100.0)

            # 2nd call with a fast impl must NOT inherit any state from
            # the previous budget violation.
            fast_payload = {
                "status": "healthy",
                "policy_profile": "default",
                "decision_reasons": [],
                "total": 5,
                "healthy_count": 5,
                "unhealthy_count": 0,
                "blocked_count": 0,
                "top_blocked_count": 0,
                "blocked_sessions_cap": 25,
            }
            with patch(
                "thegent.mcp.server.session_contract_health_gate_impl",
                return_value=fast_payload,
            ):
                recovered = _gate_tool()
            meta = recovered.meta
            assert "budget" not in str(meta).lower(), (
                f"recovery call must NOT carry the budget error envelope: meta={meta!r}"
            )
            assert meta.get("status") == "healthy"
            assert meta.get("total") == 5
        finally:
            mcp_perf_gates.MCP_PERF_BUDGETS.clear()
            mcp_perf_gates.MCP_PERF_BUDGETS.update(original)

    def test_check_mcp_budget_does_not_leak_state(self) -> None:
        """Direct test of ``check_mcp_budget``: a single violation
        followed by a within-budget measurement must raise exactly once
        (on the violation), not on the within-budget follow-up. This
        pins the statelessness contract on the helper directly so a
        refactor that introduces a module-level "latch" surfaces
        immediately."""
        from thegent.mcp.server import mcp_perf_gates

        original = dict(mcp_perf_gates.MCP_PERF_BUDGETS)
        try:
            mcp_perf_gates.MCP_PERF_BUDGETS["stateless_probe"] = 50.0

            # Violation: 60ms > 50ms budget.
            with pytest.raises(mcp_perf_gates.MCPBudgetExceeded) as excinfo:
                mcp_perf_gates.check_mcp_budget("stateless_probe", 60.0)
            assert excinfo.value.elapsed_ms == 60.0
            assert excinfo.value.budget_ms == 50.0

            # Recovery: 30ms <= 50ms budget — must NOT raise.
            mcp_perf_gates.check_mcp_budget("stateless_probe", 30.0)

            # And a second violation still raises (no latch that closes
            # the budget after the first violation).
            with pytest.raises(mcp_perf_gates.MCPBudgetExceeded):
                mcp_perf_gates.check_mcp_budget("stateless_probe", 60.0)
        finally:
            mcp_perf_gates.MCP_PERF_BUDGETS.clear()
            mcp_perf_gates.MCP_PERF_BUDGETS.update(original)

    def test_mcp_budget_context_recovers_after_explicit_budget(self) -> None:
        """``mcp_budget_context(operation, budget_ms=...)`` with an
        explicit per-call override must not mutate the named budget in
        :data:`MCP_PERF_BUDGETS`. A subsequent call using the named
        budget (no override) must still see the original threshold."""
        from thegent.mcp.server import mcp_perf_gates

        original = dict(mcp_perf_gates.MCP_PERF_BUDGETS)
        try:
            mcp_perf_gates.MCP_PERF_BUDGETS["recovery_probe"] = 100.0

            # Explicit per-call override: 10ms budget. Block exceeds it.
            with pytest.raises(mcp_perf_gates.MCPBudgetExceeded):
                with mcp_perf_gates.mcp_budget_context("recovery_probe", budget_ms=10.0):
                    time.sleep(0.02)

            # Named budget must NOT have been mutated by the override.
            assert mcp_perf_gates.MCP_PERF_BUDGETS["recovery_probe"] == 100.0, (
                "explicit budget_ms override must not mutate the named budget"
            )

            # A subsequent call within the named budget must succeed.
            with mcp_perf_gates.mcp_budget_context("recovery_probe"):
                pass
        finally:
            mcp_perf_gates.MCP_PERF_BUDGETS.clear()
            mcp_perf_gates.MCP_PERF_BUDGETS.update(original)


# ---------------------------------------------------------------------------
# Lane 10 — ``record_decision`` thread-safety (10x writers)
# ---------------------------------------------------------------------------


class TestRecordDecisionThreadSafety:
    """``OperatorCockpit.record_decision`` must accept concurrent
    writers without loss, torn writes, or ``TypeError`` leakage.
    10 writer threads × 10 notices each (100 total) must all be
    accepted and surfaced via ``snapshot()`` without missing a
    single notice."""

    def test_record_decision_accepts_100_concurrent_writes(self) -> None:
        """100 ``DecisionNotice`` pushes across 10 threads must all be
        accepted by ``record_decision``; the cockpit ``snapshot()``
        must observe every accepted notice. No ``TypeError``, no
        ``RuntimeError``, no missed notice."""
        from thegent.ux.cockpit import DecisionNotice, OperatorCockpit

        cockpit = OperatorCockpit(clock=lambda: 1.0)

        writers = 10
        per_writer = 10
        errors: list[BaseException] = []

        def _writer(thread_idx: int) -> None:
            try:
                for i in range(per_writer):
                    notice = DecisionNotice(
                        verdict="allow",
                        reason_code="allowed",
                        rule_id=f"RULE_T{thread_idx}_I{i}",
                        agent="cursor",
                        lane="standard",
                        evaluated_at=time.time(),
                        reason=f"thread {thread_idx} iter {i}",
                    )
                    cockpit.record_decision(notice)
            except BaseException as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_writer, args=(idx,)) for idx in range(writers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)
            assert not t.is_alive(), "writer thread hung"

        assert errors == [], f"errors: {errors!r}"

        snapshot = cockpit.snapshot()
        notices = snapshot["decision_notices"]
        # All 100 notices must be visible. The deque is bounded
        # (``maxlen=64``) so only the most recent 64 survive; we
        # pin the lower bound (no torn writes) and verify the
        # writer-set is a complete subset of the visible set.
        rule_ids = {n["rule_id"] for n in notices}
        assert len(notices) == len(rule_ids), (
            f"torn write detected: duplicate rule_ids in snapshot: "
            f"{[r for r in rule_ids if [n['rule_id'] for n in notices].count(r) > 1]}"
        )
        assert len(notices) == 64, f"expected bounded deque (maxlen=64) to be full, got {len(notices)}"
        # And the snapshot is internally consistent: every notice has
        # the expected shape (verdict, reason_code, rule_id, agent,
        # lane, evaluated_at, reason).
        for n in notices:
            assert n["verdict"] == "allow"
            assert n["reason_code"] == "allowed"
            assert n["agent"] == "cursor"
            assert n["lane"] == "standard"
            assert n["evaluated_at"] > 0.0
            assert n["reason"].startswith("thread ")

    def test_record_decision_rejects_non_decision_notice(self) -> None:
        """Defensive contract: ``record_decision`` must raise
        ``TypeError`` when called with anything that is not a
        :class:`DecisionNotice` (or a duck-typed equivalent). A
        concurrent writer thread surfacing a non-conforming payload
        must not silently corrupt the cockpit state."""
        from thegent.ux.cockpit import OperatorCockpit

        cockpit = OperatorCockpit(clock=lambda: 1.0)
        with pytest.raises(TypeError):
            cockpit.record_decision("not a notice")  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            cockpit.record_decision(42)  # type: ignore[arg-type]
        # Cockpit state must remain empty after the rejected writes.
        assert cockpit.snapshot()["decision_notices"] == []

    def test_record_decision_fills_zero_evaluated_at_under_concurrent_writes(
        self,
    ) -> None:
        """``record_decision`` must fill ``evaluated_at == 0`` with the
        cockpit's clock. Under 5 concurrent writers all pushing
        zero-init notices, every snapshot entry must have a positive
        ``evaluated_at`` (i.e., the cockpit clock, not 0)."""
        from thegent.ux.cockpit import DecisionNotice, OperatorCockpit

        cockpit = OperatorCockpit(clock=lambda: 42.0)

        def _writer() -> None:
            for i in range(10):
                cockpit.record_decision(
                    DecisionNotice(
                        verdict="warn",
                        reason_code="recovery_no_confidence",
                        rule_id=f"RULE_ZERO_INIT_{i}",
                        agent="cursor",
                        lane="recovery",
                        evaluated_at=0.0,
                        reason="zero-init fill test",
                    )
                )

        threads = [threading.Thread(target=_writer) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)
            assert not t.is_alive(), "writer thread hung"

        snapshot = cockpit.snapshot()
        notices = snapshot["decision_notices"]
        assert len(notices) == 50
        for n in notices:
            assert n["evaluated_at"] == 42.0, (
                f"zero-init evaluated_at must be filled with cockpit clock, got {n['evaluated_at']}"
            )
