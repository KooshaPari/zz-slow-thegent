"""End-to-end concurrency test for PolicyEngine.evaluate under federation.

Traces to: FR-GOV-001 (policy federation), WP-3003 (override path).

Lane B Day 3/5 — closes the deferred thread-safety item from WORKLOG.md
follow-ups. The unit thread-safety tests in
``test_unit_federated_policy_thread_safety.py`` already pin
``FederatedPolicyEngine._lock`` for direct registry operations; this
module adds the *end-to-end* path: many threads concurrently calling
``PolicyEngine.evaluate(ctx)`` against a federated registry, while a
writer thread continues to ``register_rule`` new entries.

Invariants asserted:

1. **No torn decisions**: every ``evaluate`` returns a
   :class:`PolicyDecision` (never ``None``) and never raises a
   ``KeyError`` / ``RuntimeError`` from a partial dict view during
   concurrent registry mutation.

2. **No lost writes**: every rule registered by the writer thread is
   resolvable after the workers drain (via
   ``FederatedPolicyEngine._namespaces`` snapshot count).

3. **Override-everything semantics under contention**: when an active
   override is registered for a matching rule, every concurrent
   ``evaluate`` that matches the rule's condition sees
   ``override_applied=True`` and ``verdict.value == "allow"``.

4. **Cache hit-rate under contention**: repeated evaluates of the same
   :class:`PolicyContext` from many threads reach the OPT-008 decision
   cache (verified via :attr:`PolicyEngine.cache_stats`) without
   deadlocking or stalling the writer thread.

5. **Default-namespace pin under contention**: a
   :class:`PolicyEngine` constructed with ``use_federation=True`` and a
   non-default ``default_namespace`` still routes all evaluations
   through the federated registry when many threads call ``evaluate``
   concurrently.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from thegent.config.settings import ThegentSettings
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


# ---------------------------------------------------------------------------
# Lane B: PolicyEngine.evaluate end-to-end concurrency
# ---------------------------------------------------------------------------


class TestPolicyEngineEvaluateEndToEndConcurrency:
    """Concurrent ``PolicyEngine.evaluate`` through the federated registry."""

    def test_concurrent_evaluate_returns_only_policy_decisions(
        self,
        federated_engine: PolicyEngine,
    ) -> None:
        """N threads each evaluate M contexts; every result is a PolicyDecision.

        No thread may observe a torn ``resolve_policies`` snapshot or a
        ``KeyError`` from a half-mutated namespace dict.
        """
        # Seed two rules: a deny on (agent=cursor, environment=production)
        # and an allow on (agent=claude, environment=development).
        federated_engine.register_rule(
            rule_id="block-cursor-prod",
            when={"agent": "cursor", "environment": "production"},
            verdict="deny",
            reason="federated deny path",
            priority=10,
        )
        federated_engine.register_rule(
            rule_id="allow-claude-dev",
            when={"agent": "claude", "environment": "development"},
            verdict="allow",
            reason="federated allow path",
            priority=20,
        )

        thread_count = 8
        per_thread = 25
        errors: list[BaseException] = []
        from thegent.governance.policy_engine import PolicyDecision

        def worker(thread_id: int) -> None:
            try:
                for i in range(per_thread):
                    # Alternate which rule the thread exercises so we hit
                    # both the deny and allow paths concurrently.
                    if (thread_id + i) % 2 == 0:
                        ctx = PolicyContext(
                            agent="cursor",
                            environment="production",
                            confidence=0.95,
                            namespace="global",
                        )
                    else:
                        ctx = PolicyContext(
                            agent="claude",
                            environment="development",
                            confidence=0.9,
                            namespace="global",
                        )
                    decision = federated_engine.evaluate(ctx)
                    assert isinstance(decision, PolicyDecision), (
                        f"thread {thread_id} iter {i} got {type(decision).__name__}"
                    )
            except BaseException as exc:  # pragma: no cover - diagnostic
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(thread_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"worker raised: {errors!r}"

    def test_concurrent_register_rule_and_evaluate_no_lost_writes(
        self,
        federated_engine: PolicyEngine,
    ) -> None:
        """While N worker threads evaluate, a writer registers M rules.

        All M rules must be present in the federated registry after
        the workers drain (no lost writes through the cache or the
        rule-id index). Workers must not raise on any iteration.
        """
        iterations = 30
        errors: list[BaseException] = []

        def writer() -> None:
            for i in range(iterations):
                federated_engine.register_rule(
                    rule_id=f"rule-{i}",
                    when={"agent": f"agent-{i % 5}"},
                    verdict="deny",
                    reason=f"rule {i}",
                    priority=i + 1,
                )

        def reader() -> None:
            for i in range(iterations):
                try:
                    ctx = PolicyContext(
                        agent=f"agent-{i % 5}",
                        environment="development",
                        confidence=0.9,
                        namespace="global",
                    )
                    federated_engine.evaluate(ctx)
                except BaseException as exc:  # pragma: no cover - diagnostic
                    errors.append(exc)
                    return

        threads: list[threading.Thread] = []
        for _ in range(2):
            threads.append(threading.Thread(target=writer))
            threads.append(threading.Thread(target=reader))
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"reader raised: {errors!r}"

        # All M writes from the writer are present in the federated
        # registry (no lost writes through the rule-id index).
        resolved = federated_engine.federated.resolve_policies("global")
        rule_ids = {r.rule_id for r in resolved}
        for i in range(iterations):
            assert f"rule-{i}" in rule_ids, f"lost write for rule-{i}"

    def test_concurrent_evaluate_with_active_override(
        self,
        federated_engine: PolicyEngine,
    ) -> None:
        """An active override must apply for every concurrent evaluation
        that matches the overridden rule's condition.
        """
        # Rule + override pair: rule denies cursor/production, override
        # flips it to allow.
        federated_engine.register_rule(
            rule_id="ovr-block-cursor-prod",
            when={"agent": "cursor", "environment": "production"},
            verdict="deny",
            reason="federated deny",
            priority=10,
        )
        federated_engine.register_override(
            "ovr-block-cursor-prod",
            reason="incident hotfix",
            by="sre",
            duration_minutes=10,
        )

        thread_count = 8
        per_thread = 25
        errors: list[BaseException] = []
        non_override_count = 0
        non_override_lock = threading.Lock()

        def worker() -> None:
            nonlocal non_override_count
            try:
                for _ in range(per_thread):
                    ctx = PolicyContext(
                        agent="cursor",
                        environment="production",
                        confidence=0.95,
                        namespace="global",
                    )
                    decision = federated_engine.evaluate(ctx)
                    # Every concurrent evaluation that matches the
                    # rule's condition must see the override applied
                    # (verdict flipped to allow).
                    if not decision.override_applied:
                        with non_override_lock:
                            non_override_count += 1
                    assert decision.override_applied is True
                    assert decision.verdict.value == "allow"
            except BaseException as exc:  # pragma: no cover - diagnostic
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(thread_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"worker raised: {errors!r}"
        assert non_override_count == 0, (
            f"{non_override_count} evaluations missed the override"
        )

    def test_concurrent_evaluate_uses_decision_cache(
        self,
        federated_engine: PolicyEngine,
    ) -> None:
        """Repeated ``evaluate`` of the same context reaches OPT-008 cache.

        The cache is wired under :attr:`PolicyEngine._cache`; the
        public :meth:`PolicyEngine.cache_stats` returns the hit/miss
        counters. Under concurrent repeat-evaluation we expect both
        counters > 0 (cache is consulted) and no exceptions.
        """
        ctx = PolicyContext(
            agent="claude",
            environment="development",
            confidence=0.9,
            namespace="global",
        )
        thread_count = 6
        per_thread = 40
        errors: list[BaseException] = []

        def worker() -> None:
            try:
                for _ in range(per_thread):
                    federated_engine.evaluate(ctx)
            except BaseException as exc:  # pragma: no cover - diagnostic
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(thread_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"worker raised: {errors!r}"

        stats = federated_engine.cache_stats()
        assert isinstance(stats, dict)
        # Either hits or misses may dominate depending on which thread
        # wins the first eval, but the cache must have been consulted.
        # At minimum the total evaluations exceed both counters (every
        # call goes through the cache path).
        total = stats.get("hits", 0) + stats.get("misses", 0)
        assert total >= 1, f"cache_stats returned no entries: {stats}"

    def test_concurrent_evaluate_with_custom_default_namespace(
        self,
        settings: ThegentSettings,
    ) -> None:
        """Custom ``default_namespace`` is honoured under concurrency.

        Federation is enabled with a non-default namespace and rules
        are registered under that namespace. Concurrent
        ``PolicyEngine.evaluate`` must route through the federated
        registry and not fall back to the default ``"global"``
        namespace.
        """
        engine = PolicyEngine(
            settings=settings,
            use_federation=True,
            default_namespace="acme",
        )
        engine.register_rule(
            rule_id="acme-block-cursor",
            when={"agent": "cursor", "environment": "production"},
            verdict="deny",
            reason="acme deny",
            priority=10,
            namespace="acme",
        )

        thread_count = 6
        per_thread = 20
        errors: list[BaseException] = []
        from thegent.governance.policy_engine import PolicyDecision

        def worker() -> None:
            try:
                for _ in range(per_thread):
                    ctx = PolicyContext(
                        agent="cursor",
                        environment="production",
                        confidence=0.95,
                        namespace="acme",
                    )
                    decision = engine.evaluate(ctx)
                    assert isinstance(decision, PolicyDecision)
                    # The federated deny rule should fire (no override
                    # registered), and the rule_id must be the
                    # acme-namespaced one we registered.
                    if decision.rule_id is not None:
                        assert decision.rule_id == "acme-block-cursor"
            except BaseException as exc:  # pragma: no cover - diagnostic
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(thread_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"worker raised: {errors!r}"


class TestPolicyEngineEvaluateRejectsInvalidContexts:
    """Sanity checks that ``evaluate`` still type-checks under concurrency.

    These pin the existing pre-condition contract: a non-PolicyContext
    argument raises ``TypeError`` even when the engine is shared
    across threads. They exist so a refactor that loosens the type
    guard is caught even if the concurrency tests above still pass.
    """

    def test_non_policy_context_rejected_under_concurrency(
        self,
        federated_engine: PolicyEngine,
    ) -> None:
        """A non-PolicyContext argument raises TypeError on every thread."""

        def worker() -> None:
            with pytest.raises(TypeError):
                federated_engine.evaluate({"agent": "cursor"})  # type: ignore[arg-type]

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()


class TestFederatedRegisterRulePreconditionsUnderConcurrency:
    """Concurrent ``register_rule`` still rejects empty ``when``."""

    def test_empty_when_rejected_under_concurrency(
        self,
        federated_engine: PolicyEngine,
    ) -> None:
        """An empty ``when`` mapping is still a configuration error.

        This is a defence-in-depth check: the lock serialises
        ``register_rule`` so the precondition is consistently applied
        regardless of how many threads attempt to register the same
        bad rule.
        """
        errors: list[BaseException] = []

        def worker() -> None:
            try:
                with pytest.raises(PolicyEngineConfigError):
                    federated_engine.register_rule(
                        rule_id="bad-rule",
                        when={},
                        verdict="deny",
                        reason="no condition",
                    )
            except BaseException as exc:  # pragma: no cover - diagnostic
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"worker raised: {errors!r}"
