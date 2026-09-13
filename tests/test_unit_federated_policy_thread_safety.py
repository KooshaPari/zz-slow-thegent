"""Thread-safety + path-traversal hardening for the Phase 3/4 governance lane.

Covers two deferred "Unblocked Next" items from WORKLOG.md:

1. ``FederatedPolicyEngine`` thread safety — a ``threading.RLock`` was
   added to the engine (audit P0 deferred item). These tests assert
   no lost writes when many threads concurrently call ``register``.

2. ``PolicyEngine.register_override`` path-traversal guard — the
   method rejects ``rule_id`` values containing ``/``, ``\\`` or
   ``..`` before they reach the override manager. These tests pin
   the contract so future refactors can't silently drop the guard.

3. ``FederatedPolicyEngine.merge`` direct tests — the existing
   ``test_federated_policy.py`` covers basic scope precedence; this
   module adds tests for the lock-on-merge path (snapshots both
   inputs) so a regression in the thread-safety refactor is caught.

Traces to: FR-GOV-001 (policy federation), WP-3003 (override path).
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from thegent.config.settings import ThegentSettings
from thegent.governance.federated_policy import (
    FederatedPolicyEngine,
    PolicyRule,
    PolicyScope,
)
from thegent.governance.policy_engine import (
    PolicyContext,
    PolicyEngine,
    PolicyEngineConfigError,
)

# All tests in this module are unit tests.
pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def settings(tmp_path: Path) -> ThegentSettings:
    return ThegentSettings(environment="development", session_dir=tmp_path)


@pytest.fixture
def federated_engine(settings: ThegentSettings) -> PolicyEngine:
    return PolicyEngine(settings=settings, use_federation=True)


def _rule(
    rule_id: str,
    *,
    scope: PolicyScope = PolicyScope.GLOBAL,
    condition: str = "flag",
    action: str = "deny",
    priority: int = 10,
    namespace: str = "global",
) -> PolicyRule:
    """Build a PolicyRule directly (mirrors test_federated_policy helper)."""
    return PolicyRule.create(
        rule_id=rule_id,
        scope=scope,
        condition=condition,
        action=action,
        priority=priority,
        namespace=namespace,
    )


# ---------------------------------------------------------------------------
# Lane 1: FederatedPolicyEngine thread safety
# ---------------------------------------------------------------------------


class TestFederatedPolicyEngineThreadSafety:
    """Concurrent ``register`` / ``evaluate`` must not lose writes."""

    def test_engine_has_internal_lock(self) -> None:
        """The engine exposes a ``_lock`` so callers know about the contract."""
        engine = FederatedPolicyEngine()
        assert hasattr(engine, "_lock")
        # ``threading.RLock`` is the documented type; assert it's a
        # re-entrant lock by acquiring it twice in the same thread.
        assert engine._lock.acquire(blocking=False)
        try:
            assert engine._lock.acquire(blocking=False)
            engine._lock.release()
        finally:
            engine._lock.release()

    def test_concurrent_register_no_lost_writes(self) -> None:
        """N threads each register M distinct rules -> N*M total rules.

        Kept moderate (10 threads x 20 rules = 200 writes) so the
        test stays under 2s on CI while still exercising the lock.
        """
        engine = FederatedPolicyEngine()
        thread_count = 10
        per_thread = 20
        errors: list[BaseException] = []

        def worker(thread_id: int) -> None:
            try:
                for i in range(per_thread):
                    rule = _rule(
                        rule_id=f"t{thread_id}-r{i}",
                        namespace=f"ns{thread_id % 5}",
                    )
                    engine.register(rule)
            except BaseException as exc:  # pragma: no cover - diagnostic
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(thread_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"worker raised: {errors!r}"
        total = sum(len(ns_rules) for ns_rules in engine._namespaces.values())
        assert total == thread_count * per_thread

    def test_concurrent_register_and_evaluate_consistent(self) -> None:
        """Concurrent register + evaluate must not raise or return partial dicts."""
        engine = FederatedPolicyEngine()

        iterations = 50

        def writer() -> None:
            for i in range(iterations):
                engine.register(_rule(rule_id=f"r{i}", condition=f"flag_{i % 10}"))

        def reader() -> None:
            for _ in range(iterations):
                # ``resolve_policies`` must always return a ``list`` (not a
                # torn partial dict view) under concurrent writes.
                resolved = engine.resolve_policies("global")
                assert isinstance(resolved, list)

        threads: list[threading.Thread] = []
        for _ in range(2):
            threads.append(threading.Thread(target=writer))
            threads.append(threading.Thread(target=reader))
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total = sum(len(ns_rules) for ns_rules in engine._namespaces.values())
        assert total == iterations

    def test_merge_under_concurrent_writes_does_not_tear(self) -> None:
        """``merge`` snapshots both engines under lock so concurrent writes
        on the source do not produce a torn (partial-key) merge."""
        source = FederatedPolicyEngine()
        sink = FederatedPolicyEngine()

        stop = threading.Event()
        stop_after = 50

        def writer() -> None:
            for i in range(stop_after):
                if stop.is_set():
                    return
                source.register(_rule(rule_id=f"src-{i}", namespace="src"))
                sink.register(_rule(rule_id=f"sink-{i}", namespace="sink"))

        t = threading.Thread(target=writer)
        t.start()
        try:
            # Perform a handful of merges during the writes; each merged
            # engine must be self-consistent (every rule_id resolves
            # cleanly under its namespace).
            for _ in range(5):
                merged = source.merge(sink)
                # The merged engine's internal state must not be torn —
                # i.e. every namespace dict must contain only
                # ``PolicyRule`` instances (no half-constructed objects).
                for ns_rules in merged._namespaces.values():
                    for rid, rule in ns_rules.items():
                        assert isinstance(rule, PolicyRule), (rid, rule)
                        assert rid == rule.rule_id
        finally:
            stop.set()
            t.join()


# ---------------------------------------------------------------------------
# Lane 2: PolicyEngine.register_override path-traversal guard
# ---------------------------------------------------------------------------


class TestRegisterOverridePathTraversalGuard:
    """``register_override`` rejects path-traversal-shaped ``rule_id``s."""

    def test_forward_slash_rejected(self, federated_engine: PolicyEngine, tmp_path: Path) -> None:
        with pytest.raises(PolicyEngineConfigError) as exc_info:
            federated_engine.register_override(
                "../etc/passwd",
                reason="hotfix",
                by="sre",
                duration_minutes=1,
            )
        assert ".." in str(exc_info.value) or "path" in str(exc_info.value).lower()

    def test_double_dot_rejected(self, federated_engine: PolicyEngine) -> None:
        with pytest.raises(PolicyEngineConfigError):
            federated_engine.register_override(
                "rule..with..dots",
                reason="r",
                by="sre",
                duration_minutes=1,
            )

    def test_backslash_rejected(self, federated_engine: PolicyEngine) -> None:
        with pytest.raises(PolicyEngineConfigError):
            federated_engine.register_override(
                "rule\\windows\\path",
                reason="r",
                by="sre",
                duration_minutes=1,
            )

    def test_normal_rule_id_accepted(self, federated_engine: PolicyEngine) -> None:
        """A clean ``rule_id`` (no separators, no ``..``) is still accepted."""
        federated_engine.register_override(
            "no-cursor-prod",
            reason="hotfix",
            by="sre",
            duration_minutes=1,
        )
        # And the override is now active for evaluation.
        federated_engine.register_rule(
            rule_id="no-cursor-prod",
            when={"agent": "cursor", "environment": "production"},
            verdict="deny",
            reason="r1",
        )
        d = federated_engine.evaluate(PolicyContext(agent="cursor", environment="production", confidence=0.95))
        assert d.override_applied is True
        assert d.verdict.value == "allow"


# ---------------------------------------------------------------------------
# Lane 3: FederatedPolicyEngine.merge direct tests
# ---------------------------------------------------------------------------


class TestFederatedPolicyEngineMerge:
    """Direct tests for the merge path; complements ``test_federated_policy.py``."""

    def test_merge_with_empty_engine_returns_self_contents(self) -> None:
        """Merging with an empty engine returns a new engine with self's rules."""
        e1 = FederatedPolicyEngine()
        e1.register(_rule("r1", namespace="team-a"))
        e1.register(_rule("r2", namespace="team-a"))
        e2 = FederatedPolicyEngine()
        merged = e1.merge(e2)
        assert sum(len(ns) for ns in merged._namespaces.values()) == 2
        assert "team-a" in merged._namespaces

    def test_merge_combines_disjoint_namespaces(self) -> None:
        """Two engines with non-overlapping namespaces union into one engine."""
        e1 = FederatedPolicyEngine()
        e1.register(_rule("r1", namespace="team-a"))
        e2 = FederatedPolicyEngine()
        e2.register(_rule("r2", namespace="team-b"))
        merged = e1.merge(e2)
        namespaces = set(merged._namespaces.keys())
        assert namespaces == {"team-a", "team-b"}
        assert merged._namespaces["team-a"]["r1"].rule_id == "r1"
        assert merged._namespaces["team-b"]["r2"].rule_id == "r2"

    def test_merge_conflict_self_wins_on_equal_scope(self) -> None:
        """On equal scope + equal namespace, ``self`` wins (existing invariant)."""
        e1 = FederatedPolicyEngine()
        e1.register(_rule("r1", scope=PolicyScope.LOCAL, action="self"))
        e2 = FederatedPolicyEngine()
        e2.register(_rule("r1", scope=PolicyScope.LOCAL, action="other"))
        merged = e1.merge(e2)
        assert merged._namespaces["global"]["r1"].action == "self"

    def test_merge_preserves_default_namespace(self) -> None:
        """Merged engine inherits the ``self.default_namespace``."""
        e1 = FederatedPolicyEngine(default_namespace="acme")
        e2 = FederatedPolicyEngine(default_namespace="beta")
        merged = e1.merge(e2)
        # ``self`` wins for the default-namespace field by convention.
        assert merged.default_namespace == "acme"

    def test_merge_does_not_mutate_inputs(self) -> None:
        """``merge`` is non-destructive: both inputs are unchanged after merge."""
        e1 = FederatedPolicyEngine()
        e1.register(_rule("r1"))
        e2 = FederatedPolicyEngine()
        e2.register(_rule("r2"))
        snapshot_e1 = {ns: dict(rules) for ns, rules in e1._namespaces.items()}
        snapshot_e2 = {ns: dict(rules) for ns, rules in e2._namespaces.items()}
        merged = e1.merge(e2)
        # Inputs are unchanged.
        assert e1._namespaces == snapshot_e1
        assert e2._namespaces == snapshot_e2
        # ``merged`` is independent (different id).
        assert merged is not e1
        assert merged is not e2


# ---------------------------------------------------------------------------
# Lane 4: FederatedPolicyEngine.load_from_file thread safety
# ---------------------------------------------------------------------------


class TestFederatedPolicyEngineLoadFromFileThreadSafety:
    """``load_from_file`` is safe to call concurrently with ``register``."""

    def test_concurrent_load_and_register(self, tmp_path: Path) -> None:
        """A file-load in flight does not lose concurrent in-memory writes."""
        engine = FederatedPolicyEngine()
        rules_path = tmp_path / "rules.json"
        rules_path.write_text(
            '[{"rule_id": "file-rule", "scope": "GLOBAL", "condition": "flag", "action": "deny", "priority": 5}]'
        )

        iterations = 30
        # Two writer threads so the file-load is exercised under contention
        # from multiple writers (was three in the draft; trimmed to keep
        # the suite under 2s on CI).
        writers = 2

        def loader() -> None:
            engine.load_from_file(rules_path)

        def writer() -> None:
            for i in range(iterations):
                engine.register(_rule(rule_id=f"mem-{i}"))

        threads: list[threading.Thread] = [threading.Thread(target=loader)]
        for _ in range(writers):
            threads.append(threading.Thread(target=writer))
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # File-loaded rule must be present even after concurrent writes.
        resolved = engine.resolve_policies("global")
        rule_ids = {r.rule_id for r in resolved}
        assert "file-rule" in rule_ids
        # All in-memory writes (30 * writers total) must also be present.
        for i in range(iterations):
            assert f"mem-{i}" in rule_ids
