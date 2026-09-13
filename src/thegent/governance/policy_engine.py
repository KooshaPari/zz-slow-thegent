"""WP-3001 + WP-3003: Pre-check policy gate evaluator with override path.

Implements the governance-layer ``PolicyEngine`` for ``thegent``:

* Pre-check gate evaluator (FR-003, FR-011, FR-033, P-066)
* Override path with TTL and revalidation (WP-3003, FR-011, P-075)
* LRU-cached decision results for sub-50ms repeated evaluations (OPT-008)
* Integration points:
  - ``OverrideManager`` (overrides.py) — TTL-based human override
  - ``TrustBoundaryChecker`` (trust.py) — trust boundary enforcement
  - ``FederatedPolicyEngine`` (federated_policy.py) — scope-aware policy
    registry (used when ``use_federation=True``)
* Fail-closed: deny on missing/empty config unless an active override exists

Public surface:
  - ``PolicyDecision`` (dataclass) — verdict payload returned by ``evaluate``
  - ``PolicyEngine`` — main entry point
  - ``evaluate_pre_check`` — convenience helper

The runtime ``thegent.execution.PolicyEngine`` (used by the orchestrator) is
intentionally preserved; this module is the governance-layer counterpart
that adds the override-aware pre-check path before a run is admitted to the
execution pipeline.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import orjson as json
from cachetools import TTLCache

from thegent.config import ThegentSettings
from thegent.governance.federated_policy import (
    FederatedPolicyEngine,
    PolicyRule,
    PolicyScope,
)
from thegent.governance.overrides import OverrideManager
from thegent.governance.trust import TrustBoundaryChecker

_log = logging.getLogger(__name__)


class PolicyEngineConfigError(ValueError):
    """Raised when a rule definition, condition, or override is invalid."""


class Verdict(StrEnum):
    """Pre-check gate verdict."""

    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"


class ReasonCode(StrEnum):
    """Machine-readable reason codes for decisions."""

    ALLOWED = "allowed"
    OVERRIDE_ACTIVE = "override_active"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    CRITICAL_LANE_LOW_CONFIDENCE = "critical_lane_low_confidence"
    UNKNOWN_AGENT_PRODUCTION = "unknown_agent_production"
    UNKNOWN_AGENT_CRITICAL = "unknown_agent_critical"
    TRUST_BOUNDARY_VIOLATION = "trust_boundary_violation"
    DRIFT_BUDGET_EXCEEDED = "drift_budget_exceeded"
    RECOVERY_NO_CONFIDENCE = "recovery_no_confidence"
    FEDERATED_POLICY_BLOCK = "federated_policy_block"
    MISSING_CONFIG = "missing_config"


@dataclass(frozen=True)
class PolicyContext:
    """Inputs to a pre-check evaluation.

    ``agent``/``model`` are accepted as either-or: ``model`` is preferred for
    routing decisions; ``agent`` is the legacy alias kept for back-compat.
    """

    agent: str = ""
    model: str = ""
    lane: str = "standard"  # one of: standard, critical, recovery, deferral
    confidence: float | None = None
    environment: str = "development"
    namespace: str = "global"
    prompt: str = ""
    cost_usd: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyDecision:
    """Verdict returned by :meth:`PolicyEngine.evaluate`."""

    verdict: Verdict
    reason: str
    reason_code: ReasonCode
    rule_id: str | None = None
    override_applied: bool = False
    cached: bool = False
    evaluated_at: float = field(default_factory=time.time)

    def is_admissible(self) -> bool:
        """Whether the decision admits the request to the execution pipeline."""
        return self.verdict != Verdict.DENY

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "reason": self.reason,
            "reason_code": self.reason_code.value,
            "rule_id": self.rule_id,
            "override_applied": self.override_applied,
            "cached": self.cached,
            "evaluated_at": self.evaluated_at,
        }


def _cache_key(ctx: PolicyContext) -> str:
    """Stable cache key for a context.

    Uses the most decision-affecting fields only; ``prompt`` is hashed so
    long prompts do not bloat the key.
    """
    prompt_hash = hashlib.sha256(ctx.prompt.encode("utf-8")).hexdigest()[:16]
    confidence_str = f"{ctx.confidence:.4f}" if ctx.confidence is not None else "-"
    return "|".join(
        [
            ctx.agent or "",
            ctx.model or "",
            ctx.lane,
            confidence_str,
            ctx.environment,
            ctx.namespace,
            prompt_hash,
        ]
    )


class PolicyEngine:
    """Governance-layer pre-check gate evaluator (WP-3001, FR-003).

    Args:
        settings: Optional :class:`ThegentSettings`; defaults to a new instance.
        use_federation: If True, evaluate the :class:`FederatedPolicyEngine`
            scope rules before the local checks. Off by default for back-compat
            with the existing execution-layer pipeline.
        default_namespace: Default namespace handed to the
            :class:`FederatedPolicyEngine` when ``use_federation=True``.
            Defaults to ``"global"`` (the federated registry's own default)
            so existing call-sites keep working unchanged. Used by the CLI
            ``cockpit pre-check --default-policy`` / ``cockpit replay``
            flags to pin the federated default per-invocation.
        cache_ttl_sec: TTL for the decision cache (default 5 min).
        cache_maxsize: Max entries in the decision cache.
    """

    CRITICAL_LANE_CONFIDENCE_MIN = 0.9
    PRODUCTION_CONFIDENCE_MIN_DEFAULT = 0.8

    def __init__(
        self,
        settings: ThegentSettings | None = None,
        *,
        use_federation: bool = False,
        default_namespace: str = "global",
        cache_ttl_sec: int = 300,
        cache_maxsize: int = 1000,
    ) -> None:
        self.settings = settings or ThegentSettings()
        self.use_federation = use_federation
        # Carry the configured default namespace so callers (CLI ``cockpit
        # pre-check --default-policy``, ``cockpit replay``) can plumb the
        # federated registry's default without having to mutate ``settings``.
        self.default_namespace = default_namespace
        self.override_manager = OverrideManager(settings=self.settings)
        self.trust_checker = TrustBoundaryChecker(self.settings, cache_ttl_sec=cache_ttl_sec)
        if use_federation:
            # Use the explicit ``default_namespace`` kwarg (rather than the
            # historical ``getattr(settings, ...)`` fallback) so the CLI can
            # pin the federated default per-invocation. ``global`` is the
            # registry's default; we mirror it here for backward compat.
            self.federated: FederatedPolicyEngine | None = FederatedPolicyEngine(default_namespace=default_namespace)
        else:
            self.federated = None
        # OPT-008: LRU + TTL decision cache (sub-50ms repeated evaluations)
        # NOTE: cachetools' TTLCache is NOT thread-safe per upstream docs; all
        # mutations and reads are serialised through ``self._lock`` (RLock so
        # evaluate() can re-enter via _apply_override safely).
        self._lock = threading.RLock()
        self._cache: TTLCache[str, PolicyDecision] = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl_sec)
        # OPT-008 observability: hit / miss counters incremented under
        # ``_lock`` so SOTA tooling and operator dashboards can assert
        # cache wiring without reaching into the underlying TTLCache.
        # ``_cache_hits`` / ``_cache_misses`` are counters (not gauges),
        # so a long-running process that wants a hit-rate over the last
        # N evals needs to snapshot both via ``cache_stats()`` and
        # diff them.
        self._cache_hits = 0
        self._cache_misses = 0

    # ------------------------------------------------------------------ registry

    def register_rule(
        self,
        rule: PolicyRule | None = None,
        *,
        rule_id: str | None = None,
        when: dict[str, Any] | None = None,
        verdict: str = "allow",
        reason: str = "",
        priority: int = 100,
        scope: PolicyScope = PolicyScope.GLOBAL,
        namespace: str = "global",
    ) -> None:
        """Register a federated policy rule (no-op if federation is disabled).

        Accepts either a fully-built :class:`PolicyRule` or a convenience dict
        form (``rule_id``, ``when`` mapping key->expected value, ``verdict``,
        ``reason``, ``priority``, ``scope``, ``namespace``).

        Empty or missing ``when`` is rejected with ``PolicyEngineConfigError``
        — an empty condition would otherwise match every context (silent
        catch-all), which is unsafe for policy authoring.

        AUDIT-N+20 (SOTA audit pass 6): every successful registration
        invalidates the OPT-008 decision cache so the next ``evaluate``
        call re-runs the federated pass and observes the new rule. Without
        this, a freshly-registered federated deny rule would be silently
        shadowed by a stale cached allow decision for the same context
        (a P0 audit gap surfaced by the SOTA pass 6 cross-cutting lane).
        """
        if self.federated is None:
            _log.debug("register_rule ignored: federation disabled")
            return
        if rule is not None:
            with self._lock:
                self.federated.register(rule)
                self._cache.clear()
            return
        if rule_id is None:
            raise PolicyEngineConfigError("register_rule requires rule_id when no PolicyRule is passed")
        if not when:
            raise PolicyEngineConfigError(
                f"register_rule({rule_id}): 'when' must be a non-empty mapping; "
                "empty condition would match every context (catch-all). "
                "Use a specific condition like {'agent': 'cursor'}."
            )
        # orjson already emits compact, key-sorted JSON by default (no separators
        # between items / no whitespace, top-to-bottom key sort) — equivalent to
        # stdlib ``json.dumps(sort_keys=True, separators=(",", ":"))``.
        # The previously-held line ``json.dumps(when, sort_keys=True, ...)``
        # broke at runtime because ``orjson.dumps`` rejects those kwargs.
        condition = json.dumps(when)
        with self._lock:
            self.federated.register(
                PolicyRule.create(
                    rule_id=rule_id,
                    scope=scope,
                    condition=condition,
                    action=verdict,
                    priority=priority,
                    namespace=namespace,
                )
            )
            # Invalidate the OPT-008 cache: a newly-registered federated
            # rule must take effect on the next ``evaluate`` call. The
            # hit/miss counters are preserved (a future audit-window
            # analysis should still see pre-existing observations).
            self._cache.clear()

    def load_rules_from_file(self, path: str | Path, namespace: str = "global") -> int:
        """Load federated rules from a JSON file. Returns count loaded.

        ``path`` is treated as untrusted; we resolve it and require it to
        exist. Authored rule bodies are operator-managed; the file body must
        be valid JSON of the schema documented in
        ``src/thegent/governance/federated_policy.py``.

        AUDIT-N+20 (SOTA audit pass 6): a successful load invalidates the
        OPT-008 decision cache so freshly-loaded rules are visible on the
        next ``evaluate`` call.
        """
        if self.federated is None:
            return 0
        resolved = Path(path).resolve()
        if not resolved.exists():
            raise PolicyEngineConfigError(f"Rule file not found: {resolved}")
        before = sum(len(ns) for ns in self.federated._namespaces.values())
        with self._lock:
            self.federated.load_from_file(resolved, namespace=namespace)
            # Drop the OPT-008 cache so the next ``evaluate`` call sees
            # the freshly-loaded rules. Counters are preserved so a
            # SOTA audit window that started before the load still
            # reflects the pre-load observations.
            self._cache.clear()
        after = sum(len(ns) for ns in self.federated._namespaces.values())
        return after - before

    def register_override(
        self,
        rule_id: str,
        *,
        reason: str,
        by: str,
        duration_minutes: int,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a TTL-based human override for ``rule_id`` (WP-3003).

        Thin pass-through to :meth:`OverrideManager.apply_override` so callers
        do not need to reach into the override_manager directly. Callers are
        responsible for sanitising ``reason`` and ``by`` (PII).

        The engine applies its **own** path-traversal guard before delegating
        to the override_manager so the public API is fail-closed even if a
        future refactor removes the manager-side check, or a direct caller
        bypasses the manager entirely. The check matches the manager
        contract in :func:`thegent.governance.overrides._validate_policy_id`:
        empty strings, ``/``, ``\\``, ``..`` substrings, and NUL bytes are
        all rejected with :class:`PolicyEngineConfigError` before any state
        is mutated.

        AUDIT-N+20 (SOTA audit pass 6): every successful override
        invalidates the OPT-008 decision cache so the next ``evaluate``
        call re-runs the override path. Without this, a freshly-registered
        override would be silently shadowed by a stale cached deny
        decision for the same context (a P0 audit gap surfaced by the
        SOTA pass 6 cross-cutting lane).
        """
        if not isinstance(rule_id, str):
            # Defensive: surface config drift as PolicyEngineConfigError so
            # callers get one consistent exception type at this boundary.
            raise PolicyEngineConfigError(f"rule_id must be a string, got {type(rule_id).__name__}")
        if not rule_id:
            raise PolicyEngineConfigError("rule_id must be a non-empty string")
        if "/" in rule_id or "\\" in rule_id:
            raise PolicyEngineConfigError(f"rule_id contains path separator: {rule_id!r}")
        if ".." in rule_id:
            raise PolicyEngineConfigError(f"rule_id contains '..' sequence: {rule_id!r}")
        if "\x00" in rule_id:
            raise PolicyEngineConfigError(f"rule_id contains NUL byte: {rule_id!r}")
        with self._lock:
            self.override_manager.apply_override(
                policy_id=rule_id,
                reason=reason,
                by=by,
                duration_minutes=duration_minutes,
                metadata=metadata,
            )
            # Drop the OPT-008 cache so the next ``evaluate`` call sees
            # the freshly-registered override. Counters are preserved
            # so a SOTA audit window that started before the override
            # still reflects the pre-override observations.
            self._cache.clear()

    # ------------------------------------------------------------------ evaluate

    def evaluate(self, ctx: PolicyContext) -> PolicyDecision:
        """Evaluate ``ctx`` and return a :class:`PolicyDecision`.

        Order of checks (short-circuits on first ``DENY`` that has no override):

        1. Cached decision lookup (OPT-008).
        2. Federated rules (if enabled) — highest priority first.
        3. Trust boundary (sensitive prompt + low-trust agent).
        4. Local rules (mirrors execution-layer checks, FR-003, FR-033):
           - critical lane + confidence < 0.9 -> deny
           - unknown agent in production -> deny
           - unknown agent in critical lane -> deny
           - recovery lane + no confidence -> warn
           - production + confidence < trust threshold -> deny
        5. Active override for the matched rule_id (override path, WP-3003).
        """
        if not isinstance(ctx, PolicyContext):  # type: ignore[unreachable]
            raise TypeError(f"PolicyEngine.evaluate expects PolicyContext, got {type(ctx).__name__}")

        key = _cache_key(ctx)
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                self._cache_hits += 1
            else:
                self._cache_misses += 1
        if cached is not None:
            return PolicyDecision(
                verdict=cached.verdict,
                reason=cached.reason,
                reason_code=cached.reason_code,
                rule_id=cached.rule_id,
                override_applied=cached.override_applied,
                cached=True,
                evaluated_at=cached.evaluated_at,
            )

        decision = self._evaluate_uncached(ctx)
        with self._lock:
            # Guard against a race where another thread won the cache miss
            # and populated a fresh decision between our evaluate and set.
            existing = self._cache.get(key)
            if existing is None:
                self._cache[key] = decision
            else:
                decision = existing
        return decision

    def _evaluate_uncached(self, ctx: PolicyContext) -> PolicyDecision:
        # 1. Federated rules (highest priority)
        if self.federated is not None:
            fed_decision = self._evaluate_federated(ctx)
            if fed_decision is not None and fed_decision.verdict != Verdict.ALLOW:
                if fed_decision.verdict == Verdict.DENY:
                    return self._apply_override(ctx, fed_decision, rule_id=fed_decision.rule_id)
                return fed_decision

        # 2. Trust boundary (fail-closed if checker is misbehaving)
        trust_decision = self._evaluate_trust(ctx)
        if trust_decision is not None:
            return trust_decision

        # 3. Local rules
        local = self._evaluate_local(ctx)
        if local.verdict == Verdict.DENY:
            return self._apply_override(ctx, local, rule_id=local.rule_id)
        return local

    def _build_metadata(self, ctx: PolicyContext) -> dict[str, Any]:
        """Effective metadata bag used to match federated rule conditions."""
        meta: dict[str, Any] = {
            "agent": ctx.agent,
            "model": ctx.model,
            "lane": ctx.lane,
            "environment": ctx.environment,
            "namespace": ctx.namespace,
            "confidence": ctx.confidence,
        }
        meta.update(ctx.metadata)
        return meta

    def _rule_matches(self, rule: PolicyRule, meta: dict[str, Any]) -> bool:
        """Match a rule against the context metadata bag.

        An empty or malformed ``condition`` is treated as **no match** rather
        than match-all: a policy author who forgets the ``when`` block gets a
        safe, non-matching rule instead of a silent catch-all.
        """
        if not rule.condition:
            return False
        try:
            cond = json.loads(rule.condition)
        except (ValueError, TypeError) as exc:
            _log.warning("rule %s has malformed condition JSON: %s", rule.rule_id, exc)
            return False
        if not isinstance(cond, dict) or not cond:
            return False
        return all(meta.get(k) == v for k, v in cond.items())

    def _dispatch_rule(self, rule: PolicyRule) -> PolicyDecision | None:
        """Translate a rule's action verb into a PolicyDecision (or None for allow)."""
        action = rule.action.lower()
        if action == "allow":
            return None
        if action == "deny":
            return PolicyDecision(
                verdict=Verdict.DENY,
                reason=f"federated rule {rule.rule_id} denied",
                reason_code=ReasonCode.FEDERATED_POLICY_BLOCK,
                rule_id=rule.rule_id,
            )
        if action == "warn":
            return PolicyDecision(
                verdict=Verdict.WARN,
                reason=f"federated rule {rule.rule_id} warns",
                reason_code=ReasonCode.FEDERATED_POLICY_BLOCK,
                rule_id=rule.rule_id,
            )
        _log.warning("unknown federated action %r on rule %s", action, rule.rule_id)
        return None

    def _evaluate_federated(self, ctx: PolicyContext) -> PolicyDecision | None:
        """Evaluate federated rules; return first non-allow decision or None."""
        if self.federated is None:
            return None
        try:
            meta = self._build_metadata(ctx)
            resolved = self.federated.resolve_policies(ctx.namespace)
        except Exception as exc:  # fail-closed on registry error
            _log.error("Federated policy evaluation failed: %s", exc)
            return PolicyDecision(
                verdict=Verdict.DENY,
                reason=f"federated policy error: {exc}",
                reason_code=ReasonCode.FEDERATED_POLICY_BLOCK,
            )
        # Sort ascending by priority so lower priority numbers (more specific)
        # win first. Walk the sorted rules and return the first non-allow.
        matched = [rule for rule in resolved if self._rule_matches(rule, meta)]
        matched.sort(key=lambda r: r.priority)
        for rule in matched:
            decision = self._dispatch_rule(rule)
            if decision is not None:
                return decision
        return None

    def _evaluate_trust(self, ctx: PolicyContext) -> PolicyDecision | None:
        """Run trust boundary check. Returns DENY on violation, None on pass.

        Fail-CLOSED: if the checker returns a malformed payload (no
        ``allowed`` key, or ``allowed`` missing), we conservatively return
        DENY to maintain the module's stated posture.
        """
        if not ctx.prompt or not ctx.agent:
            return None
        result = self.trust_checker.evaluate_routing(ctx.prompt, ctx.agent)
        if not isinstance(result, dict):
            _log.warning("trust_checker returned non-dict: %r", type(result).__name__)
            return PolicyDecision(
                verdict=Verdict.DENY,
                reason="trust boundary check returned malformed payload",
                reason_code=ReasonCode.TRUST_BOUNDARY_VIOLATION,
                rule_id="trust.boundary",
            )
        allowed = result.get("allowed", False)  # fail-closed default
        if not allowed:
            return PolicyDecision(
                verdict=Verdict.DENY,
                reason=str(result.get("reason") or "trust boundary violation"),
                reason_code=ReasonCode.TRUST_BOUNDARY_VIOLATION,
                rule_id="trust.boundary",
            )
        return None

    def _check_critical_low_confidence(self, ctx: PolicyContext) -> PolicyDecision | None:
        if ctx.lane == "critical" and ctx.confidence is not None and ctx.confidence < self.CRITICAL_LANE_CONFIDENCE_MIN:
            return PolicyDecision(
                verdict=Verdict.DENY,
                reason=(
                    f"confidence {ctx.confidence:.3f} below critical-lane floor {self.CRITICAL_LANE_CONFIDENCE_MIN}"
                ),
                reason_code=ReasonCode.CRITICAL_LANE_LOW_CONFIDENCE,
                rule_id="local.critical.confidence",
            )
        return None

    def _check_unknown_agent_production(self, ctx: PolicyContext, is_unknown: bool) -> PolicyDecision | None:
        if ctx.environment == "production" and is_unknown:
            return PolicyDecision(
                verdict=Verdict.DENY,
                reason="unknown agent blocked in production",
                reason_code=ReasonCode.UNKNOWN_AGENT_PRODUCTION,
                rule_id="local.production.unknown_agent",
            )
        return None

    def _check_unknown_agent_critical(self, ctx: PolicyContext, is_unknown: bool) -> PolicyDecision | None:
        if ctx.lane == "critical" and is_unknown:
            return PolicyDecision(
                verdict=Verdict.DENY,
                reason="unknown agent blocked in critical lane",
                reason_code=ReasonCode.UNKNOWN_AGENT_CRITICAL,
                rule_id="local.critical.unknown_agent",
            )
        return None

    def _check_recovery_no_confidence(self, ctx: PolicyContext) -> PolicyDecision | None:
        if ctx.lane == "recovery" and ctx.confidence is None:
            return PolicyDecision(
                verdict=Verdict.WARN,
                reason="no confidence data for recovery lane",
                reason_code=ReasonCode.RECOVERY_NO_CONFIDENCE,
                rule_id="local.recovery.no_confidence",
            )
        return None

    def _check_production_low_confidence(self, ctx: PolicyContext, threshold: float) -> PolicyDecision | None:
        if ctx.environment == "production" and ctx.confidence is not None and ctx.confidence < threshold:
            return PolicyDecision(
                verdict=Verdict.DENY,
                reason=f"confidence {ctx.confidence:.3f} below production floor {threshold:.3f}",
                reason_code=ReasonCode.CRITICAL_LANE_LOW_CONFIDENCE,
                rule_id="local.production.confidence",
            )
        return None

    def _evaluate_local(self, ctx: PolicyContext) -> PolicyDecision:
        agent_or_model = (ctx.model or ctx.agent or "").lower()
        is_unknown = agent_or_model in ("", "unknown", "untrusted")
        threshold = float(
            getattr(
                self.settings,
                "trust_score_threshold",
                self.PRODUCTION_CONFIDENCE_MIN_DEFAULT,
            )
        )
        checks: list[PolicyDecision | None] = [
            self._check_critical_low_confidence(ctx),
            self._check_unknown_agent_production(ctx, is_unknown),
            self._check_unknown_agent_critical(ctx, is_unknown),
            self._check_recovery_no_confidence(ctx),
            self._check_production_low_confidence(ctx, threshold),
        ]
        for decision in checks:
            if decision is not None:
                return decision
        return PolicyDecision(
            verdict=Verdict.ALLOW,
            reason="allowed by local policy",
            reason_code=ReasonCode.ALLOWED,
            rule_id="local.default.allow",
        )

    def _apply_override(self, ctx: PolicyContext, decision: PolicyDecision, *, rule_id: str | None) -> PolicyDecision:
        """Apply a TTL-based override if one is active for ``rule_id``.

        WP-3003: overrides carry a reason and operator; they are logged
        with ``governance.override.applied`` at WARNING level (an override
        is a bypass and warrants attention) for auditability. Expired
        overrides are cleaned up by :meth:`OverrideManager.get_override`
        which deletes the file and returns ``None``.
        """
        if rule_id is None:
            return decision
        try:
            with self._lock:
                override = self.override_manager.get_override(rule_id)
        except Exception as exc:
            _log.warning("override lookup failed for %s: %s", rule_id, exc)
            return decision
        if override is None or not override.is_active():
            return decision

        ttl_remaining = override.expires_at - time.time()
        _log.warning(
            "governance.override.applied rule_id=%s by=%s reason_present=%s ttl_remaining=%.0fs",
            rule_id,
            override.by,
            bool(override.reason),
            ttl_remaining,
        )
        return PolicyDecision(
            verdict=Verdict.ALLOW,
            reason=f"override by {override.by}: {override.reason}",
            reason_code=ReasonCode.OVERRIDE_ACTIVE,
            rule_id=rule_id,
            override_applied=True,
        )

    # ------------------------------------------------------------------ helpers

    def invalidate_cache(self) -> None:
        """Drop all cached decisions (e.g., after a rule change).

        Also resets the hit/miss counters so a "fresh observation
        window" starts cleanly — SOTA tooling that snapshots stats
        before and after a config change can rely on the diff being
        purely post-change.
        """
        with self._lock:
            self._cache.clear()
            self._cache_hits = 0
            self._cache_misses = 0

    def cache_size(self) -> int:
        with self._lock:
            return len(self._cache)

    def cache_stats(self) -> dict[str, Any]:
        """Return a snapshot of the OPT-008 decision-cache observability surface.

        The snapshot is taken under :attr:`_lock` so the counters and
        ``size`` are consistent with each other (a concurrent
        ``evaluate`` can't bump a counter between the two reads). The
        returned mapping is safe to JSON-serialize and is the shape
        ``thegent cockpit …`` dashboards consume.

        Keys:

        * ``size`` — current number of entries in the bounded
          ``TTLCache`` (``0 <= size <= cache_maxsize``).
        * ``maxsize`` — the configured ceiling.
        * ``hits`` — monotonic counter; reset on :meth:`invalidate_cache`
          and on construction.
        * ``misses`` — monotonic counter; reset on :meth:`invalidate_cache`
          and on construction.
        * ``total`` — ``hits + misses``.
        * ``hit_rate`` — ``hits / total`` when ``total > 0`` else ``0.0``.
          Useful as a single-line gauge on operator dashboards.
        """
        with self._lock:
            hits = self._cache_hits
            misses = self._cache_misses
            size = len(self._cache)
        total = hits + misses
        hit_rate = (hits / total) if total > 0 else 0.0
        return {
            "size": size,
            "maxsize": self._cache.maxsize,
            "hits": hits,
            "misses": misses,
            "total": total,
            "hit_rate": hit_rate,
        }


def evaluate_pre_check(
    ctx: PolicyContext | None = None,
    *,
    settings: ThegentSettings | None = None,
    use_federation: bool = False,
    **fields: Any,
) -> PolicyDecision:
    """Functional wrapper around :meth:`PolicyEngine.evaluate`.

    Accepts either a pre-built :class:`PolicyContext` (positional) or any of the
    :class:`PolicyContext` fields as keyword arguments.  Remaining fields
    default to ``PolicyContext()``'s defaults.
    """
    if ctx is None:
        ctx = PolicyContext(**fields)
    elif fields:
        raise TypeError("Pass either a PolicyContext or keyword fields, not both.")
    return PolicyEngine(settings=settings, use_federation=use_federation).evaluate(ctx)


__all__ = [
    "PolicyContext",
    "PolicyRule",
    "PolicyDecision",
    "PolicyEngine",
    "PolicyEngineConfigError",
    "ReasonCode",
    "Verdict",
    "evaluate_pre_check",
]  # PolicyRule is re-exported from federated_policy
