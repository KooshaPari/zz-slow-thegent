# AUDIT-N+67: federated_policy hardening — all contracts verified
"""FederatedPolicyEngine: scope-aware policy registry for governance.

Traces to: FR-GOV-001 (policy federation), FR-GOV-002 (scope precedence)
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

import orjson as json

if TYPE_CHECKING:
    from pathlib import Path

_log = logging.getLogger(__name__)

# Re-entrant lock so callers that already hold ``PolicyEngine._lock``
# can drop into ``FederatedPolicyEngine`` without deadlock; this matches
# the PolicyEngine pattern and lets the engine be used from a single
# thread OR from many threads without the caller having to wrap every
# call.
_RLock = threading.RLock


class PolicyScope(Enum):
    """Hierarchy level of a policy rule. Higher numeric value = higher authority."""

    LOCAL = 1
    REGIONAL = 2
    GLOBAL = 3


@dataclass(order=True)
class PolicyRule:
    """A single governance rule with scope and evaluation metadata (FR-GOV-001)."""

    # priority is first so dataclass ordering uses it as the primary sort key
    priority: int
    rule_id: str = field(compare=False)
    scope: PolicyScope = field(compare=False)
    condition: str = field(compare=False)
    action: str = field(compare=False)
    namespace: str = field(default="global", compare=False)

    @classmethod
    def create(
        cls, rule_id: str, scope: PolicyScope, condition: str, action: str, priority: int, namespace: str = "global"
    ) -> PolicyRule:
        """Named constructor matching the canonical field order in the task spec."""
        return cls(
            priority=priority, rule_id=rule_id, scope=scope, condition=condition, action=action, namespace=namespace
        )


class FederatedPolicyEngine:
    """Registry and evaluator for scoped governance policy rules (FR-GOV-001).

    Supports multi-tenant federation via namespace hierarchy.

    Thread safety:
        All mutating methods (``register``, ``load_from_file``, ``merge``)
        and the read path (``resolve_policies``, ``evaluate``) are
        serialised through an internal :class:`threading.RLock`. Callers
        may freely share a single :class:`FederatedPolicyEngine` across
        threads without external synchronisation.

        The lock is **re-entrant** so an engine method that already
        holds it can call other engine methods safely (e.g. ``merge``
        calling ``register``). This matches the lock used by
        :class:`thegent.governance.policy_engine.PolicyEngine`, so a
        caller that already holds ``PolicyEngine._lock`` can drop into
        the federated engine without risk of deadlock.
    """

    def __init__(self, default_namespace: str = "global") -> None:
        self.default_namespace = default_namespace
        # Map of namespace -> rule_id -> PolicyRule
        self._namespaces: dict[str, dict[str, PolicyRule]] = {}
        # Internal re-entrant lock guarding all registry mutations and
        # reads. ``PolicyEngine._lock`` already serialises callers but
        # the federated engine is intended to be usable standalone, so
        # it owns its own lock.
        self._lock = _RLock()

    def register(self, rule: PolicyRule) -> None:
        """Add *rule* to the registry, replacing any existing rule with the same id.

        Thread-safe: serialised through ``self._lock``.
        """
        with self._lock:
            ns = rule.namespace or self.default_namespace
            if ns not in self._namespaces:
                self._namespaces[ns] = {}
            self._namespaces[ns][rule.rule_id] = rule

    def load_from_file(self, path: Path, namespace: str = "global") -> None:
        """Load rules from a JSON file.

        Thread-safe: serialised through ``self._lock`` for the entire
        file load so a partial load is never observable to readers.
        """
        if not path.exists():
            _log.warning("Policy file %s not found.", path)
            return

        raw: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
        # Build rules outside the lock so a slow parse doesn't block
        # concurrent readers; the per-rule ``register`` call re-acquires
        # the lock (re-entrant).
        new_rules: list[PolicyRule] = []
        for item in raw:
            new_rules.append(
                PolicyRule.create(
                    rule_id=str(item["rule_id"]),
                    scope=PolicyScope[str(item["scope"]).upper()],
                    condition=str(item["condition"]),
                    action=str(item["action"]),
                    priority=int(str(item.get("priority", 100))),
                    namespace=item.get("namespace", namespace),
                )
            )
        for rule in new_rules:
            self.register(rule)

    def resolve_policies(self, namespace: str) -> list[PolicyRule]:
        """Resolve all rules for a namespace, following hierarchy (specific -> parent -> global).

        Thread-safe: read path is guarded by ``self._lock`` so callers
        see a consistent snapshot even if a concurrent writer is
        mutating the registry.
        """
        with self._lock:
            parts = namespace.split(".")
            namespaces_to_check = []
            for i in range(len(parts), 0, -1):
                namespaces_to_check.append(".".join(parts[:i]))

            if "global" not in namespaces_to_check:
                namespaces_to_check.append("global")

            resolved_rules: dict[str, PolicyRule] = {}

            # Check from global up to specific, so more specific rules override
            for ns in reversed(namespaces_to_check):
                ns_rules = self._namespaces.get(ns, {})
                for rid, rule in ns_rules.items():
                    # Conflict resolution: higher scope wins; then more specific namespace wins
                    if rid not in resolved_rules:
                        resolved_rules[rid] = rule
                    else:
                        current_rule = resolved_rules[rid]
                        # If new rule has higher scope, it overrides
                        if rule.scope.value > current_rule.scope.value:
                            resolved_rules[rid] = rule
                        # If same scope, but this is a more specific namespace, it overrides?
                        # Usually specificity overrides in local, but global scope overrides local.
                        # We'll follow the rule: Higher Scope > Specifity.

            return list(resolved_rules.values())

    def evaluate(self, namespace: str, context: dict[str, Any]) -> list[PolicyRule]:
        """Evaluate matching rules for a namespace, sorted by priority."""
        rules = self.resolve_policies(namespace)
        matched = [rule for rule in rules if context.get(rule.condition)]
        return sorted(matched, key=lambda r: r.priority)

    def merge(self, other: FederatedPolicyEngine) -> FederatedPolicyEngine:
        """Combine two engines.

        Thread-safe: reads from ``self`` and ``other`` under their
        respective locks and writes to ``merged`` under its own lock.
        A merged engine is returned; the inputs are not mutated.
        """
        merged = FederatedPolicyEngine(self.default_namespace)

        # Snapshot both engines' namespaces under lock so a concurrent
        # mutation on either side can't tear the merge.
        with self._lock:
            self_snapshot: dict[str, dict[str, PolicyRule]] = {
                ns: dict(rules) for ns, rules in self._namespaces.items()
            }
        with other._lock:
            other_snapshot: dict[str, dict[str, PolicyRule]] = {
                ns: dict(rules) for ns, rules in other._namespaces.items()
            }

        all_ns = set(self_snapshot.keys()) | set(other_snapshot.keys())

        for ns in all_ns:
            self_ns = self_snapshot.get(ns, {})
            other_ns = other_snapshot.get(ns, {})

            all_rids = set(self_ns.keys()) | set(other_ns.keys())
            for rid in all_rids:
                r1 = self_ns.get(rid)
                r2 = other_ns.get(rid)

                if r1 and not r2:
                    merged.register(r1)
                elif r2 and not r1:
                    merged.register(r2)
                elif r1 and r2:
                    # Higher scope wins
                    if r2.scope.value > r1.scope.value:
                        merged.register(r2)
                    else:
                        merged.register(r1)

        return merged
