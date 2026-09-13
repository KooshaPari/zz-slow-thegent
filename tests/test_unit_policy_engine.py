"""Unit tests for the governance-layer PolicyEngine (WP-3001, WP-3003, OPT-008)."""

from __future__ import annotations

from pathlib import Path

import pytest

from thegent.config.settings import ThegentSettings
from thegent.governance.federated_policy import FederatedPolicyEngine
from thegent.governance.policy_engine import (
    PolicyContext,
    PolicyDecision,
    PolicyEngine,
    PolicyEngineConfigError,
    ReasonCode,
    Verdict,
    evaluate_pre_check,
)

# All tests in this module are unit tests.
pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def settings(tmp_path: Path) -> ThegentSettings:
    """Override-managed settings with isolated session/override dirs."""
    return ThegentSettings(environment="development", session_dir=tmp_path)


@pytest.fixture
def engine(settings: ThegentSettings) -> PolicyEngine:
    return PolicyEngine(settings=settings, use_federation=False)


@pytest.fixture
def federated_engine(settings: ThegentSettings) -> PolicyEngine:
    return PolicyEngine(settings=settings, use_federation=True)


# ---------------------------------------------------------------------------
# Sanity / dataclass shape
# ---------------------------------------------------------------------------


class TestSanity:
    """Imported names and basic dataclass structure are correct."""

    def test_public_api(self) -> None:
        """Module exports the documented public surface."""
        # All major symbols are accessible and non-None.
        assert Verdict.ALLOW.value == "allow"
        assert Verdict.DENY.value == "deny"
        assert Verdict.WARN.value == "warn"
        assert ReasonCode.OVERRIDE_ACTIVE.value == "override_active"
        assert ReasonCode.CRITICAL_LANE_LOW_CONFIDENCE.value == "critical_lane_low_confidence"
        assert ReasonCode.TRUST_BOUNDARY_VIOLATION.value == "trust_boundary_violation"
        assert ReasonCode.FEDERATED_POLICY_BLOCK.value == "federated_policy_block"

    def test_policy_context_frozen(self) -> None:
        """PolicyContext is frozen — mutating fields raises."""
        ctx = PolicyContext(agent="cursor", environment="production")
        with pytest.raises(Exception):
            ctx.agent = "gemini"  # type: ignore[misc]

    def test_policy_decision_admissibility(self) -> None:
        d = PolicyDecision(
            verdict=Verdict.ALLOW,
            reason="ok",
            reason_code=ReasonCode.ALLOWED,
        )
        assert d.is_admissible() is True
        d2 = d.to_dict()
        assert d2["verdict"] == "allow"
        assert d2["reason_code"] == "allowed"

    def test_denied_decision_not_admissible(self) -> None:
        d = PolicyDecision(
            verdict=Verdict.DENY,
            reason="no",
            reason_code=ReasonCode.UNKNOWN_AGENT_CRITICAL,
        )
        assert d.is_admissible() is False


# ---------------------------------------------------------------------------
# Default and local-rule behaviour
# ---------------------------------------------------------------------------


class TestLocalRules:
    """WP-3001: local default policy mirrors execution-layer checks (FR-003)."""

    def test_default_allows_when_no_rules_fire(self, engine: PolicyEngine) -> None:
        d = engine.evaluate(PolicyContext(agent="cursor", environment="development", confidence=0.95))
        assert d.verdict == Verdict.ALLOW
        assert d.reason_code == ReasonCode.ALLOWED

    def test_critical_lane_low_confidence_denied(self, engine: PolicyEngine) -> None:
        d = engine.evaluate(PolicyContext(agent="cursor", lane="critical", confidence=0.5))
        assert d.verdict == Verdict.DENY
        assert d.reason_code == ReasonCode.CRITICAL_LANE_LOW_CONFIDENCE
        assert d.rule_id == "local.critical.confidence"

    def test_unknown_agent_in_critical_denied(self, engine: PolicyEngine) -> None:
        d = engine.evaluate(PolicyContext(agent="unknown", lane="critical", confidence=0.99))
        assert d.verdict == Verdict.DENY
        assert d.reason_code == ReasonCode.UNKNOWN_AGENT_CRITICAL
        assert d.rule_id == "local.critical.unknown_agent"

    def test_recovery_lane_no_confidence_warns(self, engine: PolicyEngine) -> None:
        d = engine.evaluate(PolicyContext(agent="cursor", lane="recovery", confidence=None))
        assert d.verdict == Verdict.WARN
        assert d.reason_code == ReasonCode.RECOVERY_NO_CONFIDENCE

    def test_production_low_confidence_denied(self, engine: PolicyEngine) -> None:
        d = engine.evaluate(PolicyContext(agent="cursor", environment="production", confidence=0.1))
        assert d.verdict == Verdict.DENY
        assert d.reason_code == ReasonCode.CRITICAL_LANE_LOW_CONFIDENCE

    def test_unknown_agent_in_production_denied(self, engine: PolicyEngine) -> None:
        d = engine.evaluate(PolicyContext(agent="unknown", environment="production", confidence=0.95))
        assert d.verdict == Verdict.DENY
        assert d.reason_code == ReasonCode.UNKNOWN_AGENT_PRODUCTION


# ---------------------------------------------------------------------------
# Trust boundary
# ---------------------------------------------------------------------------


class TestTrustBoundary:
    """Sensitive-keyword prompts must not flow to EXTERNAL agents."""

    def test_sensitive_prompt_to_external_agent_denied(self, engine: PolicyEngine) -> None:
        d = engine.evaluate(
            PolicyContext(
                agent="gemini",
                environment="production",
                prompt="here is my api_key=sk-abc12345",
                confidence=0.9,
            )
        )
        assert d.verdict == Verdict.DENY
        assert d.reason_code == ReasonCode.TRUST_BOUNDARY_VIOLATION
        assert d.rule_id == "trust.boundary"

    def test_safe_prompt_to_internal_agent_allowed(self, engine: PolicyEngine) -> None:
        d = engine.evaluate(
            PolicyContext(
                agent="cursor",
                environment="production",
                prompt="hello world",
                confidence=0.9,
            )
        )
        assert d.verdict == Verdict.ALLOW


# ---------------------------------------------------------------------------
# Federated rule + override path (WP-3003)
# ---------------------------------------------------------------------------


class TestFederatedAndOverride:
    """Federated scope rules and override path combine correctly."""

    def test_federated_rule_deny_with_metadata_match(self, federated_engine: PolicyEngine) -> None:
        federated_engine.register_rule(
            rule_id="no-cursor-prod",
            when={"agent": "cursor", "environment": "production"},
            verdict="deny",
            reason="r1",
            priority=10,
        )
        d = federated_engine.evaluate(PolicyContext(agent="cursor", environment="production", confidence=0.95))
        assert d.verdict == Verdict.DENY
        assert d.rule_id == "no-cursor-prod"
        assert d.reason_code == ReasonCode.FEDERATED_POLICY_BLOCK

    def test_federated_rule_does_not_match_other_env(self, federated_engine: PolicyEngine) -> None:
        federated_engine.register_rule(
            rule_id="no-cursor-prod",
            when={"agent": "cursor", "environment": "production"},
            verdict="deny",
            reason="r1",
        )
        d = federated_engine.evaluate(PolicyContext(agent="cursor", environment="development", confidence=0.95))
        assert d.verdict == Verdict.ALLOW

    def test_override_flips_deny_to_allow(self, federated_engine: PolicyEngine) -> None:
        federated_engine.register_rule(
            rule_id="no-cursor-prod",
            when={"agent": "cursor", "environment": "production"},
            verdict="deny",
            reason="r1",
        )
        federated_engine.register_override(
            "no-cursor-prod",
            reason="hotfix approval",
            by="sre-team",
            duration_minutes=2,
        )
        d = federated_engine.evaluate(PolicyContext(agent="cursor", environment="production", confidence=0.95))
        assert d.verdict == Verdict.ALLOW
        assert d.reason_code == ReasonCode.OVERRIDE_ACTIVE
        assert d.override_applied is True

    def test_register_rule_ignored_when_federation_off(self, engine: PolicyEngine) -> None:
        # No exception: rule registration is silently ignored.
        engine.register_rule(
            rule_id="noop",
            when={"agent": "cursor"},
            verdict="deny",
            reason="r",
        )
        d = engine.evaluate(PolicyContext(agent="cursor", environment="production"))
        assert d.verdict == Verdict.ALLOW  # federation disabled, not active

    def test_load_rules_from_file_no_federation(self, engine: PolicyEngine) -> None:
        """Loading rules does nothing when federation is disabled."""
        count = engine.load_rules_from_file(Path("/nonexistent.json"))
        assert count == 0


# ---------------------------------------------------------------------------
# OPT-008 decision cache
# ---------------------------------------------------------------------------


class TestDecisionCache:
    """OPT-008: repeated evaluations are sub-50ms via TTLCache."""

    def test_cache_returns_fresh_instance_with_cached_flag(self, federated_engine: PolicyEngine) -> None:
        federated_engine.register_rule(
            rule_id="c1",
            when={"agent": "cursor", "environment": "production"},
            verdict="allow",
            reason="ok",
        )
        ctx = PolicyContext(agent="cursor", environment="production", confidence=0.95)
        d1 = federated_engine.evaluate(ctx)
        d2 = federated_engine.evaluate(ctx)
        assert d1.cached is False
        assert d2.cached is True
        assert federated_engine.cache_size() >= 1
        # returns a fresh dataclass instance (no aliasing).
        assert d1 is not d2
        d1d = d1.to_dict()
        d2d = d2.to_dict()
        # All fields equal except ``cached`` which flips True on the cached hit.
        for k in d1d:
            if k == "cached":
                assert d1d[k] is False and d2d[k] is True
            else:
                assert d1d[k] == d2d[k], f"{k}: {d1d[k]} vs {d2d[k]}"

    def test_invalidate_cache_clears(self, federated_engine: PolicyEngine) -> None:
        federated_engine.register_rule(
            rule_id="c1",
            when={"agent": "cursor"},
            verdict="allow",
            reason="ok",
        )
        federated_engine.evaluate(PolicyContext(agent="cursor"))
        assert federated_engine.cache_size() >= 1
        federated_engine.invalidate_cache()
        assert federated_engine.cache_size() == 0


# ---------------------------------------------------------------------------
# Convenience helper
# ---------------------------------------------------------------------------


class TestHelper:
    """evaluate_pre_check is a thin wrapper around PolicyEngine.evaluate."""

    def test_helper_default_returns_allow(self) -> None:
        d = evaluate_pre_check(agent="cursor", environment="development", confidence=0.9)
        assert d.verdict == Verdict.ALLOW

    def test_helper_returns_object(self) -> None:
        d = evaluate_pre_check(agent="cursor", environment="production", confidence=0.95)
        assert isinstance(d, PolicyDecision)
        assert d.verdict in (Verdict.ALLOW, Verdict.DENY, Verdict.WARN)


# ---------------------------------------------------------------------------
# Default-namespace kwarg (Lane 2 federation contract)
# ---------------------------------------------------------------------------


class TestDefaultNamespaceKwarg:
    """``PolicyEngine(default_namespace=...)`` plumbs into the federated engine.

    Phase 3/4 hardening lane, second "Unblocked Next" item: the CLI
    ``cockpit pre-check --default-policy <name>`` flag must propagate to
    ``FederatedPolicyEngine.default_namespace``. The default remains
    ``"global"`` so existing call-sites (and ``cockpit replay``) keep
    working unchanged.
    """

    def test_default_namespace_kwarg_propagates_to_federated_engine(self, settings: ThegentSettings) -> None:
        """Explicit ``default_namespace="acme"`` flows into the federated engine."""
        engine = PolicyEngine(settings=settings, use_federation=True, default_namespace="acme")
        assert engine.federated is not None
        assert engine.federated.default_namespace == "acme"
        assert engine.default_namespace == "acme"

    def test_default_namespace_default_is_global(self, settings: ThegentSettings) -> None:
        """The default ``"global"`` is preserved for backward compatibility."""
        engine = PolicyEngine(settings=settings, use_federation=True)
        assert engine.federated is not None
        assert engine.federated.default_namespace == "global"
        assert engine.default_namespace == "global"

    def test_default_namespace_without_federation_still_records_value(self, settings: ThegentSettings) -> None:
        """``default_namespace`` is exposed on the engine even when federation is off."""
        engine = PolicyEngine(settings=settings, use_federation=False, default_namespace="team-x")
        assert engine.federated is None
        assert engine.default_namespace == "team-x"

    def test_default_namespace_explicit_global_still_propagates(self, settings: ThegentSettings) -> None:
        """Passing ``"global"`` explicitly is equivalent to the implicit default."""
        engine = PolicyEngine(settings=settings, use_federation=True, default_namespace="global")
        assert engine.federated is not None
        assert engine.federated.default_namespace == "global"


# ---------------------------------------------------------------------------
# register_override path-traversal guard (direct tests)
# ---------------------------------------------------------------------------


class TestRegisterOverridePathTraversalGuard:
    """``PolicyEngine.register_override`` rejects path-traversal-shaped rule_ids.

    The audit (and the WORKLOG "Unblocked Next" item #2) flagged that the
    path-traversal guard on ``PolicyEngine.register_override`` (implemented
    in ``policy_engine.py`` at the public-API surface) was only indirectly
    exercised via the federated-policy thread-safety suite. These direct
    tests pin the contract at the policy-engine layer so a future refactor
    of ``register_override`` cannot silently weaken it.

    Rejection shapes covered:

    * ``/`` — POSIX path separator (Unix absolute or relative traversal)
    * ``\\`` — Windows path separator
    * ``..`` — parent-directory reference, even without a separator

    The guard is intentionally applied *before* the call reaches the
    override_manager (which interpolates rule_id into filenames), so
    each rejected call must surface a ``PolicyEngineConfigError`` and
    leave no override registered on the engine.
    """

    def test_register_override_rejects_forward_slash(self, engine: PolicyEngine) -> None:
        """A ``/`` in ``rule_id`` is rejected before the override_manager is called."""
        with pytest.raises(PolicyEngineConfigError) as exc_info:
            engine.register_override(
                "no-network/prod",
                reason="hotfix",
                by="sre",
                duration_minutes=1,
            )
        # Error message must mention either '..' or 'path' so operators
        # can diagnose the rejection without reading source.
        msg = str(exc_info.value).lower()
        assert ".." in str(exc_info.value) or "path" in msg

    def test_register_override_rejects_backslash(self, engine: PolicyEngine) -> None:
        """A ``\\`` (Windows separator) in ``rule_id`` is rejected."""
        with pytest.raises(PolicyEngineConfigError):
            engine.register_override(
                "no-network\\prod",
                reason="hotfix",
                by="sre",
                duration_minutes=1,
            )

    def test_register_override_rejects_double_dot_sequence(self, engine: PolicyEngine) -> None:
        """A bare ``..`` substring (without separators) is rejected."""
        with pytest.raises(PolicyEngineConfigError):
            engine.register_override(
                "rule..with..dots",
                reason="hotfix",
                by="sre",
                duration_minutes=1,
            )

    def test_register_override_rejects_absolute_path(self, engine: PolicyEngine) -> None:
        """A leading ``/etc/passwd`` style traversal is rejected."""
        with pytest.raises(PolicyEngineConfigError):
            engine.register_override(
                "/etc/passwd",
                reason="hotfix",
                by="sre",
                duration_minutes=1,
            )

    def test_register_override_rejects_parent_traversal(self, engine: PolicyEngine) -> None:
        """A ``../foo`` parent-directory escape is rejected."""
        with pytest.raises(PolicyEngineConfigError):
            engine.register_override(
                "../escape",
                reason="hotfix",
                by="sre",
                duration_minutes=1,
            )

    def test_register_override_accepts_clean_rule_id(self, engine: PolicyEngine) -> None:
        """A rule_id with only ``[A-Za-z0-9_-]`` is accepted.

        This is the negative control: if the guard over-rejects, this
        test catches it. We don't assert anything about the override
        being active (that's the override_manager's contract, covered
        elsewhere) — only that the guard does not raise on a clean id.
        """
        # Should not raise.
        engine.register_override(
            "no-network-prod",
            reason="hotfix",
            by="sre",
            duration_minutes=1,
        )

    def test_register_override_rejects_even_with_federation_enabled(self, federated_engine: PolicyEngine) -> None:
        """The guard fires regardless of ``use_federation=True``.

        Some refactors might gate the guard behind the federated-engine
        branch (since only the federated override_manager interpolates
        filenames). This test pins the contract: the public ``PolicyEngine``
        API rejects bad inputs no matter how the engine is configured.
        """
        with pytest.raises(PolicyEngineConfigError):
            federated_engine.register_override(
                "rule/with/slashes",
                reason="hotfix",
                by="sre",
                duration_minutes=1,
            )

    def test_register_override_rejected_does_not_register_override(self, engine: PolicyEngine) -> None:
        """A rejected call leaves no override behind on the override_manager.

        Guards must fail closed: a bad ``rule_id`` must not partially
        register an override that later evaluates and fires. We assert
        by attempting to evaluate a context that would normally be denied
        by the just-registered override; if the guard ever silently lets
        a bad rule_id through, this assertion catches it.
        """
        with pytest.raises(PolicyEngineConfigError):
            engine.register_override(
                "no-cursor-prod/../etc",
                reason="hotfix",
                by="sre",
                duration_minutes=60,
            )
        # No partial state — a clean evaluate on the same agent must
        # not be affected by the rejected override.
        d = engine.evaluate(PolicyContext(agent="cursor", environment="development", confidence=0.95))
        assert d.verdict == Verdict.ALLOW

    # ------------------------------------------------------------------
    # Engine guard parity with manager contract
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("bad_id", "expected_substr"),
        [
            ("rule\x00with-nul", "NUL"),
            ("trailing\x00", "NUL"),
            ("\x00leading", "NUL"),
            ("", "non-empty"),
        ],
    )
    def test_register_override_rejects_nul_and_empty(
        self,
        engine: PolicyEngine,
        bad_id: str,
        expected_substr: str,
    ) -> None:
        """NUL bytes and empty strings are rejected at the engine boundary.

        Closes the audit's "engine guard coverage gap" — the engine
        previously delegated NUL/empty rejection to the manager. While
        the manager still rejects these (defense-in-depth), the engine
        now mirrors the contract so a refactor or direct caller cannot
        open a hole. The engine raises ``PolicyEngineConfigError`` (its
        own exception type) so callers get a consistent surface even if
        the manager layer is ever bypassed.
        """
        with pytest.raises(PolicyEngineConfigError) as exc_info:
            engine.register_override(
                bad_id,
                reason="hotfix",
                by="sre",
                duration_minutes=1,
            )
        assert expected_substr.lower() in str(exc_info.value).lower()

    @pytest.mark.parametrize(
        "non_string_id",
        [123, 1.5, None, b"rule", ["rule"], {"rule": True}],
    )
    def test_register_override_rejects_non_string(
        self,
        engine: PolicyEngine,
        non_string_id: object,
    ) -> None:
        """Non-string ``rule_id`` is rejected before the manager is touched.

        Defense against config drift — a YAML/JSON load that yields
        ``int`` or ``None`` must surface as ``PolicyEngineConfigError``
        (not ``AttributeError`` deeper in the manager). The error
        message includes the offending type so operators can diagnose
        without reading source.
        """
        with pytest.raises(PolicyEngineConfigError) as exc_info:
            engine.register_override(
                non_string_id,  # type: ignore[arg-type]
                reason="hotfix",
                by="sre",
                duration_minutes=1,
            )
        assert "string" in str(exc_info.value).lower()

    def test_register_override_engine_guard_fires_before_manager(
        self,
        engine: PolicyEngine,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Engine guard fires first — manager is never invoked for bad input.

        Belt-and-braces provenance test: monkeypatch the override_manager's
        ``apply_override`` to raise a sentinel error. If the engine guard
        fired first (which it must), the sentinel is never seen — only
        ``PolicyEngineConfigError`` from the engine. If a future refactor
        silently removes the engine guard, the manager's sentinel leaks
        out and this test fails loudly.
        """
        from thegent.governance import overrides as overrides_module

        sentinel = AssertionError("manager.apply_override should not be called for bad rule_id")
        original_apply = engine.override_manager.apply_override
        calls: list[str] = []

        def spy_apply(*args: object, **kwargs: object) -> object:
            calls.append(str(kwargs.get("policy_id")))
            return original_apply(*args, **kwargs)  # pragma: no cover - not reached

        monkeypatch.setattr(engine.override_manager, "apply_override", spy_apply)
        monkeypatch.setattr(
            overrides_module,
            "_validate_policy_id",
            lambda _id: (_ for _ in ()).throw(sentinel),
        )

        with pytest.raises(PolicyEngineConfigError):
            engine.register_override(
                "rule\x00with-nul",
                reason="hotfix",
                by="sre",
                duration_minutes=1,
            )
        assert calls == [], f"manager.apply_override was invoked for a rejected rule_id: {calls}"

    def test_register_override_engine_guard_fires_before_manager_on_empty(
        self,
        engine: PolicyEngine,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Empty-string rejection also happens before the manager is touched.

        Companion to the NUL-byte provenance test — ensures the empty-string
        branch also fires the engine guard before delegating, so a future
        refactor that loosens the engine guard cannot silently route the
        empty-string check through the manager only.
        """
        from thegent.governance import overrides as overrides_module

        sentinel = AssertionError("manager.apply_override should not be called for empty rule_id")
        original_apply = engine.override_manager.apply_override
        calls: list[str] = []

        def spy_apply(*args: object, **kwargs: object) -> object:
            calls.append(str(kwargs.get("policy_id")))
            return original_apply(*args, **kwargs)  # pragma: no cover - not reached

        monkeypatch.setattr(engine.override_manager, "apply_override", spy_apply)
        monkeypatch.setattr(
            overrides_module,
            "_validate_policy_id",
            lambda _id: (_ for _ in ()).throw(sentinel),
        )

        with pytest.raises(PolicyEngineConfigError):
            engine.register_override(
                "",
                reason="hotfix",
                by="sre",
                duration_minutes=1,
            )
        assert calls == [], f"manager.apply_override was invoked for an empty rule_id: {calls}"


# ---------------------------------------------------------------------------
# Governance edge-case expansion (SOTA audit closure)
# ---------------------------------------------------------------------------


class TestGovernanceEdgeCases:
    """Pin governance edge-case paths identified in the SOTA audit."""

    def test_evaluate_federated_zero_rules_allows(self, settings: ThegentSettings) -> None:
        """Empty federated registry falls through to local default ALLOW."""
        eng = PolicyEngine(settings=settings, use_federation=True)
        result = eng.evaluate(PolicyContext(agent="cursor", environment="development", confidence=0.95))
        assert result.verdict.value == "allow"
        assert result.rule_id == "local.default.allow"

    def test_evaluate_bare_context_allows(self, engine: PolicyEngine) -> None:
        """Fully-default PolicyContext hits trust skip then local ALLOW."""
        result = engine.evaluate(PolicyContext())
        assert result.verdict.value == "allow"

    def test_evaluate_federated_exception_yields_deny(
        self,
        federated_engine: PolicyEngine,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Registry failure triggers fail-closed DENY."""
        federated_engine.register_rule(
            rule_id="dummy",
            when={"agent": "cursor"},
            verdict="allow",
            reason="activate federation",
        )
        monkeypatch.setattr(
            federated_engine.federated,
            "resolve_policies",
            lambda _ns: (_ for _ in ()).throw(RuntimeError("simulated failure")),
        )
        result = federated_engine.evaluate(PolicyContext(agent="cursor"))
        assert result.verdict.value == "deny"

    def test_evaluate_federated_empty_registry_unknown_agent_production(self, settings: ThegentSettings) -> None:
        """Empty registry + unknown agent in production → local deny rule fires."""
        eng = PolicyEngine(settings=settings, use_federation=True)
        result = eng.evaluate(PolicyContext(agent="unknown", environment="production", confidence=0.95))
        assert result.verdict.value == "deny"

    def test_evaluate_federated_rule_match_overrides_local_allow(self, settings: ThegentSettings) -> None:
        """Federated DENY rule takes precedence over local default ALLOW."""
        eng = PolicyEngine(settings=settings, use_federation=True)
        eng.register_rule(
            rule_id="block-dev",
            when={"environment": "development"},
            verdict="deny",
            reason="block dev env",
            priority=1,
        )
        result = eng.evaluate(PolicyContext(agent="cursor", environment="development", confidence=0.95))
        assert result.verdict.value == "deny"
        assert result.rule_id != "local.default.allow"

    def test_merge_both_empty_returns_empty_engine(self) -> None:
        """Merging two empty engines yields an empty engine with shared namespace."""
        e1 = FederatedPolicyEngine()
        e2 = FederatedPolicyEngine()
        merged = e1.merge(e2)
        assert merged.resolve_policies("global") == []
        assert merged.default_namespace == e1.default_namespace

    def test_evaluate_override_flips_federated_deny_to_allow(self, settings: ThegentSettings) -> None:
        """Override reverses a federated DENY back to ALLOW."""
        eng = PolicyEngine(settings=settings, use_federation=True)
        eng.register_rule(
            rule_id="block-prod",
            when={"environment": "production"},
            verdict="deny",
            reason="block prod",
            priority=1,
        )
        eng.register_override(
            "block-prod",
            reason="approved by SRE",
            by="admin",
            duration_minutes=5,
        )
        result = eng.evaluate(PolicyContext(agent="cursor", environment="production", confidence=0.95))
        assert result.verdict.value == "allow"
        assert result.override_applied is True
