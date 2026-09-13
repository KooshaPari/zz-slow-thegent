"""Tests for FederatedPolicyEngine and FederatedPolicyManager (WL-020).

Traces to:
  FR-GOV-001 (policy federation), FR-GOV-002 (scope precedence)
  FR-FED-001: Three-level namespace org.project.environment
  FR-FED-002: Policy resolution order
  FR-FED-003: Jurisdiction profiles
  FR-FED-004: Cross-namespace consent relay
  FR-FED-005: Most-restrictive-wins conflict arbitration
  FR-FED-006: Federation health + drift observability
"""

from __future__ import annotations

import json as _stdlib_json
import tempfile
from pathlib import Path

import orjson as json
import pytest

from thegent.governance.federated_policy import (
    FederatedPolicyEngine,
    PolicyRule,
    PolicyScope,
)
from thegent.governance.federation import (
    JURISDICTION_PROFILES,
    FederatedPolicyManager,
    PolicyNamespace,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rule(
    rule_id: str = "r1",
    scope: PolicyScope = PolicyScope.LOCAL,
    condition: str = "flag",
    action: str = "deny",
    priority: int = 10,
) -> PolicyRule:
    return PolicyRule.create(
        rule_id=rule_id,
        scope=scope,
        condition=condition,
        action=action,
        priority=priority,
    )


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------


def _rule_count(engine: FederatedPolicyEngine) -> int:
    """Count total rules across all namespaces (test helper)."""
    return sum(len(ns_rules) for ns_rules in engine._namespaces.values())


@pytest.mark.unit
def test_register_adds_rule() -> None:
    """FR-GOV-001: register() stores a rule retrievable via evaluate()."""
    engine = FederatedPolicyEngine()
    engine.register(_rule("r1", condition="active"))
    assert _rule_count(engine) == 1


@pytest.mark.unit
def test_register_replaces_existing_rule() -> None:
    """FR-GOV-001: registering same rule_id replaces the previous entry."""
    engine = FederatedPolicyEngine()
    engine.register(_rule("r1", action="deny"))
    engine.register(_rule("r1", action="alert"))
    assert _rule_count(engine) == 1
    results = engine.evaluate("global", {"flag": True})
    assert results[0].action == "alert"


# ---------------------------------------------------------------------------
# evaluate
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_evaluate_returns_matching_rules() -> None:
    """FR-GOV-001: evaluate() returns only rules whose condition is truthy in context."""
    engine = FederatedPolicyEngine()
    engine.register(_rule("r1", condition="cost_exceeded"))
    engine.register(_rule("r2", condition="sla_breached"))
    matched = engine.evaluate("global", {"cost_exceeded": True})
    assert len(matched) == 1
    assert matched[0].rule_id == "r1"


@pytest.mark.unit
def test_evaluate_returns_empty_when_no_match() -> None:
    """FR-GOV-001: evaluate() returns [] when no conditions are met."""
    engine = FederatedPolicyEngine()
    engine.register(_rule("r1", condition="cost_exceeded"))
    assert engine.evaluate("global", {}) == []
    assert engine.evaluate("global", {"cost_exceeded": False}) == []


@pytest.mark.unit
def test_evaluate_sorted_by_priority_ascending() -> None:
    """FR-GOV-001: evaluate() returns rules ordered by ascending priority."""
    engine = FederatedPolicyEngine()
    engine.register(_rule("r-high", condition="flag", priority=5))
    engine.register(_rule("r-low", condition="flag", priority=1))
    engine.register(_rule("r-mid", condition="flag", priority=3))
    result = engine.evaluate("global", {"flag": True})
    priorities = [r.priority for r in result]
    assert priorities == sorted(priorities)
    assert result[0].rule_id == "r-low"


@pytest.mark.unit
def test_evaluate_multiple_conditions() -> None:
    """FR-GOV-001: evaluate() matches multiple rules when multiple conditions are met."""
    engine = FederatedPolicyEngine()
    engine.register(_rule("r1", condition="cost_exceeded", priority=1))
    engine.register(_rule("r2", condition="sla_breached", priority=2))
    engine.register(_rule("r3", condition="quota_exceeded", priority=3))
    ctx = {"cost_exceeded": True, "sla_breached": True}
    matched = engine.evaluate("global", ctx)
    assert len(matched) == 2
    assert {r.rule_id for r in matched} == {"r1", "r2"}


# ---------------------------------------------------------------------------
# merge — scope precedence
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_merge_non_conflicting_rules_are_unioned() -> None:
    """FR-GOV-002: merge() combines rules that do not share rule_ids."""
    e1 = FederatedPolicyEngine()
    e1.register(_rule("local-rule", scope=PolicyScope.LOCAL))
    e2 = FederatedPolicyEngine()
    e2.register(_rule("global-rule", scope=PolicyScope.GLOBAL))
    merged = e1.merge(e2)
    assert _rule_count(merged) == 2


@pytest.mark.unit
def test_merge_global_beats_local_on_conflict() -> None:
    """FR-GOV-002: GLOBAL scope wins over LOCAL when rule_ids conflict."""
    e1 = FederatedPolicyEngine()
    e1.register(_rule("r1", scope=PolicyScope.LOCAL, action="alert"))
    e2 = FederatedPolicyEngine()
    e2.register(_rule("r1", scope=PolicyScope.GLOBAL, action="deny"))
    merged = e1.merge(e2)
    result = merged.evaluate("global", {"flag": True})
    assert len(result) == 1
    assert result[0].scope == PolicyScope.GLOBAL
    assert result[0].action == "deny"


@pytest.mark.unit
def test_merge_global_beats_regional_on_conflict() -> None:
    """FR-GOV-002: GLOBAL scope wins over REGIONAL when rule_ids conflict."""
    e1 = FederatedPolicyEngine()
    e1.register(_rule("r1", scope=PolicyScope.REGIONAL, action="alert"))
    e2 = FederatedPolicyEngine()
    e2.register(_rule("r1", scope=PolicyScope.GLOBAL, action="deny"))
    merged = e1.merge(e2)
    result = merged.evaluate("global", {"flag": True})
    assert result[0].scope == PolicyScope.GLOBAL


@pytest.mark.unit
def test_merge_regional_beats_local_on_conflict() -> None:
    """FR-GOV-002: REGIONAL scope wins over LOCAL when rule_ids conflict."""
    e1 = FederatedPolicyEngine()
    e1.register(_rule("r1", scope=PolicyScope.LOCAL, action="allow"))
    e2 = FederatedPolicyEngine()
    e2.register(_rule("r1", scope=PolicyScope.REGIONAL, action="deny"))
    merged = e1.merge(e2)
    result = merged.evaluate("global", {"flag": True})
    assert result[0].scope == PolicyScope.REGIONAL
    assert result[0].action == "deny"


@pytest.mark.unit
def test_merge_self_wins_on_scope_tie() -> None:
    """FR-GOV-002: on equal scope, self takes precedence over other."""
    e1 = FederatedPolicyEngine()
    e1.register(_rule("r1", scope=PolicyScope.REGIONAL, action="self-action"))
    e2 = FederatedPolicyEngine()
    e2.register(_rule("r1", scope=PolicyScope.REGIONAL, action="other-action"))
    merged = e1.merge(e2)
    result = merged.evaluate("global", {"flag": True})
    assert result[0].action == "self-action"


@pytest.mark.unit
def test_merge_returns_new_engine_leaves_originals_intact() -> None:
    """FR-GOV-002: merge() is non-destructive; originals are unchanged."""
    e1 = FederatedPolicyEngine()
    e1.register(_rule("r1"))
    e2 = FederatedPolicyEngine()
    e2.register(_rule("r2"))
    merged = e1.merge(e2)
    assert _rule_count(e1) == 1
    assert _rule_count(e2) == 1
    assert _rule_count(merged) == 2


# ---------------------------------------------------------------------------
# load_from_file
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_load_from_file_registers_rules() -> None:
    """FR-GOV-001: load_from_file() populates engine from JSON."""
    data = [
        {
            "rule_id": "file-rule-1",
            "scope": "GLOBAL",
            "condition": "cost_exceeded",
            "action": "deny",
            "priority": 1,
        },
        {
            "rule_id": "file-rule-2",
            "scope": "LOCAL",
            "condition": "quota_exceeded",
            "action": "alert",
            "priority": 5,
        },
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fh:
        # NOTE: orjson exposes ``dumps`` (bytes) but no ``dump`` stream
        # writer. Use stdlib ``json.dump`` for this hot path so the file
        # is materialised on disk rather than buffered as bytes. The
        # rest of the file uses ``orjson.dumps`` for performance where
        # bytes are acceptable.
        _stdlib_json.dump(data, fh)
        tmp_path = Path(fh.name)

    try:
        engine = FederatedPolicyEngine()
        engine.load_from_file(tmp_path)
        assert _rule_count(engine) == 2
        matched = engine.evaluate("global", {"cost_exceeded": True})
        assert len(matched) == 1
        assert matched[0].scope == PolicyScope.GLOBAL
    finally:
        tmp_path.unlink(missing_ok=True)


@pytest.mark.unit
def test_load_from_file_scope_case_insensitive() -> None:
    """FR-GOV-001: scope field in JSON is case-insensitive."""
    data = [
        {
            "rule_id": "r1",
            "scope": "global",
            "condition": "flag",
            "action": "deny",
            "priority": 1,
        }
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as fh:
        _stdlib_json.dump(data, fh)
        tmp_path = Path(fh.name)
    try:
        engine = FederatedPolicyEngine()
        engine.load_from_file(tmp_path)
        result = engine.evaluate("global", {"flag": True})
        assert result[0].scope == PolicyScope.GLOBAL
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# PolicyScope ordering
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_policy_scope_values_ordered_correctly() -> None:
    """FR-GOV-002: GLOBAL > REGIONAL > LOCAL by numeric value."""
    assert PolicyScope.GLOBAL.value > PolicyScope.REGIONAL.value
    assert PolicyScope.REGIONAL.value > PolicyScope.LOCAL.value


# ===========================================================================
# FR-FED-001 through FR-FED-006 (WL-020) — FederatedPolicyManager tests
# ===========================================================================


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fed_base(tmp_path: Path) -> Path:
    return tmp_path / "fed_store"


@pytest.fixture
def fed_manager(fed_base: Path) -> FederatedPolicyManager:
    return FederatedPolicyManager(base_dir=fed_base, session_dir=fed_base)


def _write_fed_policy(base_dir: Path, org: str, project: str, env: str, policy_id: str, data: dict) -> None:
    d = base_dir / org / project / env
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{policy_id}.json").write_text(json.dumps(data).decode(), encoding="utf-8")


# ---------------------------------------------------------------------------
# FR-FED-001: PolicyNamespace hierarchy
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_fed_001_hierarchy_most_specific_first() -> None:
    # @trace FR-FED-001
    ns = PolicyNamespace(org="acme", project="payments", environment="production")
    assert ns.get_hierarchy()[0] == "acme.payments.production"


@pytest.mark.unit
def test_fed_001_hierarchy_contains_project_default() -> None:
    # @trace FR-FED-001
    ns = PolicyNamespace(org="acme", project="payments", environment="production")
    assert "acme.payments.default" in ns.get_hierarchy()


@pytest.mark.unit
def test_fed_001_hierarchy_contains_org_default() -> None:
    # @trace FR-FED-001
    ns = PolicyNamespace(org="acme", project="payments", environment="production")
    assert "acme.default.default" in ns.get_hierarchy()


@pytest.mark.unit
def test_fed_001_hierarchy_contains_global() -> None:
    # @trace FR-FED-001
    ns = PolicyNamespace(org="acme", project="payments", environment="production")
    assert "global" in ns.get_hierarchy()


@pytest.mark.unit
def test_fed_001_hierarchy_resolution_order() -> None:
    # @trace FR-FED-001 / FR-FED-002
    ns = PolicyNamespace(org="acme", project="payments", environment="production")
    h = ns.get_hierarchy()
    env_idx = h.index("acme.payments.production")
    proj_idx = h.index("acme.payments.default")
    org_idx = h.index("acme.default.default")
    assert env_idx < proj_idx < org_idx


@pytest.mark.unit
def test_fed_001_repr_is_dotted_string() -> None:
    # @trace FR-FED-001
    ns = PolicyNamespace(org="o", project="p", environment="e")
    assert repr(ns) == "o.p.e"
    assert str(ns) == "o.p.e"


# ---------------------------------------------------------------------------
# FR-FED-002: Policy resolution
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_fed_002_env_level_policy_found(fed_manager: FederatedPolicyManager, fed_base: Path) -> None:
    # @trace FR-FED-002
    _write_fed_policy(fed_base, "acme", "pay", "prod", "base", {"allow": True})
    ns = PolicyNamespace("acme", "pay", "prod")
    policy = fed_manager.resolve_policy(ns, "base")
    assert policy["allow"] is True


@pytest.mark.unit
def test_fed_002_project_default_fallback(fed_manager: FederatedPolicyManager, fed_base: Path) -> None:
    # @trace FR-FED-002
    _write_fed_policy(fed_base, "acme", "pay", "default", "base", {"risk_threshold": 0.8})
    ns = PolicyNamespace("acme", "pay", "staging")
    policy = fed_manager.resolve_policy(ns, "base")
    assert policy["risk_threshold"] == 0.8


@pytest.mark.unit
def test_fed_002_org_default_fallback(fed_manager: FederatedPolicyManager, fed_base: Path) -> None:
    # @trace FR-FED-002
    _write_fed_policy(fed_base, "acme", "default", "default", "base", {"risk_threshold": 0.7})
    ns = PolicyNamespace("acme", "unknown_proj", "staging")
    policy = fed_manager.resolve_policy(ns, "base")
    assert policy["risk_threshold"] == 0.7


@pytest.mark.unit
def test_fed_002_env_overrides_org_default(fed_manager: FederatedPolicyManager, fed_base: Path) -> None:
    # @trace FR-FED-002
    _write_fed_policy(fed_base, "acme", "default", "default", "base", {"risk_threshold": 0.7})
    _write_fed_policy(fed_base, "acme", "pay", "prod", "base", {"risk_threshold": 0.5})
    ns = PolicyNamespace("acme", "pay", "prod")
    policy = fed_manager.resolve_policy(ns, "base")
    assert policy["risk_threshold"] == 0.5


@pytest.mark.unit
def test_fed_002_no_policy_returns_empty(fed_manager: FederatedPolicyManager) -> None:
    # @trace FR-FED-002
    ns = PolicyNamespace("no_org", "no_proj", "no_env")
    policy = fed_manager.resolve_policy(ns, "nonexistent")
    assert policy == {}


# ---------------------------------------------------------------------------
# FR-FED-003: Jurisdiction profiles
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_fed_003_eu_adds_human_in_loop(fed_manager: FederatedPolicyManager) -> None:
    # @trace FR-FED-003
    base = {"risk_threshold": 0.9}
    result = fed_manager.apply_jurisdiction_constraints(base, "EU")
    assert result.get("human_in_loop_required") is True


@pytest.mark.unit
def test_fed_003_eu_lowers_risk_threshold(fed_manager: FederatedPolicyManager) -> None:
    # @trace FR-FED-003
    base = {"risk_threshold": 0.9}
    result = fed_manager.apply_jurisdiction_constraints(base, "EU")
    assert result["risk_threshold"] <= 0.7


@pytest.mark.unit
def test_fed_003_us_sets_retention(fed_manager: FederatedPolicyManager) -> None:
    # @trace FR-FED-003
    base = {}
    result = fed_manager.apply_jurisdiction_constraints(base, "US")
    assert result.get("audit_retention_days") == 2555


@pytest.mark.unit
def test_fed_003_profile_additive_preserves_base_fields(
    fed_manager: FederatedPolicyManager,
) -> None:
    # @trace FR-FED-003
    base = {"allow": True, "custom_field": "preserved"}
    result = fed_manager.apply_jurisdiction_constraints(base, "EU")
    assert result.get("custom_field") == "preserved"
    assert result.get("allow") is True


@pytest.mark.unit
def test_fed_003_base_lower_risk_threshold_kept(
    fed_manager: FederatedPolicyManager,
) -> None:
    # @trace FR-FED-003
    base = {"risk_threshold": 0.3}
    result = fed_manager.apply_jurisdiction_constraints(base, "EU")
    assert result["risk_threshold"] == 0.3


@pytest.mark.unit
def test_fed_003_apply_by_profile_name(fed_manager: FederatedPolicyManager) -> None:
    # @trace FR-FED-003
    base = {}
    result = fed_manager.apply_jurisdiction_profile(base, "EU-AI-ACT")
    assert result.get("jurisdiction_profile") == "EU-AI-ACT"


@pytest.mark.unit
def test_fed_003_unknown_region_returns_base(
    fed_manager: FederatedPolicyManager,
) -> None:
    # @trace FR-FED-003
    base = {"risk_threshold": 0.9}
    result = fed_manager.apply_jurisdiction_constraints(base, "UNKNOWN")
    assert result == base


@pytest.mark.unit
def test_fed_003_jurisdiction_profiles_dict_eu() -> None:
    # @trace FR-FED-003
    assert "EU-AI-ACT" in JURISDICTION_PROFILES
    eu = JURISDICTION_PROFILES["EU-AI-ACT"]
    assert eu.get("human_in_loop_required") is True
    assert eu.get("risk_threshold") == 0.7


@pytest.mark.unit
def test_fed_003_jurisdiction_profiles_dict_us() -> None:
    # @trace FR-FED-003
    assert "US-SEC" in JURISDICTION_PROFILES
    us = JURISDICTION_PROFILES["US-SEC"]
    assert us.get("audit_retention_days") == 2555


# ---------------------------------------------------------------------------
# FR-FED-004: Cross-namespace consent relay
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_fed_004_relay_returns_artifact(fed_manager: FederatedPolicyManager) -> None:
    # @trace FR-FED-004
    ns1 = PolicyNamespace("org1", "pay", "prod")
    ns2 = PolicyNamespace("org2", "billing", "prod")
    artifact = fed_manager.relay_consent(ns1, ns2, "run_c01", "alice")
    assert artifact["type"] == "consent_relay"
    assert artifact["run_id"] == "run_c01"
    assert artifact["status"] == "active"


@pytest.mark.unit
def test_fed_004_relay_has_sha256_signature(
    fed_manager: FederatedPolicyManager,
) -> None:
    # @trace FR-FED-004
    ns1 = PolicyNamespace("org1", "pay", "prod")
    ns2 = PolicyNamespace("org2", "billing", "prod")
    artifact = fed_manager.relay_consent(ns1, ns2, "run_sig", "bob")
    assert len(artifact.get("provenance_signature", "")) == 64


@pytest.mark.unit
def test_fed_004_relay_persisted_to_store(
    fed_manager: FederatedPolicyManager,
) -> None:
    # @trace FR-FED-004
    ns1 = PolicyNamespace("org1", "pay", "prod")
    ns2 = PolicyNamespace("org2", "billing", "prod")
    fed_manager.relay_consent(ns1, ns2, "run_persist", "alice")
    items = fed_manager.get_consent_relays(run_id="run_persist")
    assert len(items) == 1
    assert items[0]["run_id"] == "run_persist"


@pytest.mark.unit
def test_fed_004_relay_namespace_fields(fed_manager: FederatedPolicyManager) -> None:
    # @trace FR-FED-004
    ns1 = PolicyNamespace("o1", "p1", "e1")
    ns2 = PolicyNamespace("o2", "p2", "e2")
    artifact = fed_manager.relay_consent(ns1, ns2, "run_ns", "carol")
    assert artifact["source_namespace"] == "o1.p1.e1"
    assert artifact["target_namespace"] == "o2.p2.e2"


# ---------------------------------------------------------------------------
# FR-FED-005: Conflict arbitration
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_fed_005_risk_threshold_takes_min(fed_manager: FederatedPolicyManager) -> None:
    # @trace FR-FED-005
    result = fed_manager.arbitrate_conflict([{"risk_threshold": 0.9}, {"risk_threshold": 0.6}])
    assert result["risk_threshold"] == 0.6


@pytest.mark.unit
def test_fed_005_human_in_loop_or(fed_manager: FederatedPolicyManager) -> None:
    # @trace FR-FED-005
    result = fed_manager.arbitrate_conflict([{"human_in_loop_required": False}, {"human_in_loop_required": True}])
    assert result["human_in_loop_required"] is True


@pytest.mark.unit
def test_fed_005_audit_retention_takes_max(fed_manager: FederatedPolicyManager) -> None:
    # @trace FR-FED-005
    result = fed_manager.arbitrate_conflict([{"audit_retention_days": 365}, {"audit_retention_days": 2555}])
    assert result["audit_retention_days"] == 2555


@pytest.mark.unit
def test_fed_005_arbitration_applied_flag(fed_manager: FederatedPolicyManager) -> None:
    # @trace FR-FED-005
    result = fed_manager.arbitrate_conflict([{"k": 1}, {"k": 2}])
    assert result.get("arbitration_applied") is True


@pytest.mark.unit
def test_fed_005_empty_policies_returns_empty(
    fed_manager: FederatedPolicyManager,
) -> None:
    # @trace FR-FED-005
    assert fed_manager.arbitrate_conflict([]) == {}


@pytest.mark.unit
def test_fed_005_arbitration_log_written(fed_manager: FederatedPolicyManager, fed_base: Path) -> None:
    # @trace FR-FED-005
    fed_manager.arbitrate_conflict(
        [{"risk_threshold": 0.9}, {"risk_threshold": 0.5}],
        namespace="acme.pay.prod",
        policy_id="base",
    )
    log_path = fed_base / "policy_arbitration.jsonl"
    assert log_path.exists()
    entries = [json.loads(l) for l in log_path.read_text().splitlines() if l.strip()]
    assert len(entries) >= 1
    assert entries[0]["key"] == "risk_threshold"
    assert entries[0]["chosen_value"] == 0.5


@pytest.mark.unit
def test_fed_005_require_audit_or(fed_manager: FederatedPolicyManager) -> None:
    # @trace FR-FED-005
    result = fed_manager.arbitrate_conflict([{"require_audit": False}, {"require_audit": True}])
    assert result["require_audit"] is True


# ---------------------------------------------------------------------------
# FR-FED-006: Federation health + drift
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_fed_006_empty_base_dir_reports_empty(
    fed_manager: FederatedPolicyManager,
) -> None:
    # @trace FR-FED-006
    health = fed_manager.get_federation_health()
    assert health["status"] == "empty"
    assert health["namespace_count"] == 0


@pytest.mark.unit
def test_fed_006_populated_reports_healthy(fed_manager: FederatedPolicyManager, fed_base: Path) -> None:
    # @trace FR-FED-006
    _write_fed_policy(fed_base, "acme", "pay", "prod", "base", {})
    health = fed_manager.get_federation_health()
    assert health["status"] == "healthy"
    assert health["namespace_count"] >= 1


@pytest.mark.unit
def test_fed_006_health_lists_namespaces(fed_manager: FederatedPolicyManager, fed_base: Path) -> None:
    # @trace FR-FED-006
    _write_fed_policy(fed_base, "acme", "pay", "prod", "base", {})
    health = fed_manager.get_federation_health()
    assert "acme.pay.prod" in health["namespaces"]


@pytest.mark.unit
def test_fed_006_drift_detected_no_org_default(fed_manager: FederatedPolicyManager, fed_base: Path) -> None:
    # @trace FR-FED-006
    _write_fed_policy(fed_base, "acme", "pay", "prod", "base", {})
    health = fed_manager.get_federation_health()
    drift = health["drift"]
    assert drift["drifted_count"] >= 1
    ns_names = [d["namespace"] for d in drift["drifted_namespaces"]]
    assert "acme.pay.prod" in ns_names


@pytest.mark.unit
def test_fed_006_no_drift_when_org_default_exists(fed_manager: FederatedPolicyManager, fed_base: Path) -> None:
    # @trace FR-FED-006
    _write_fed_policy(fed_base, "acme", "default", "default", "base", {})
    _write_fed_policy(fed_base, "acme", "pay", "prod", "base", {})
    health = fed_manager.get_federation_health()
    assert health["drift"]["drifted_count"] == 0
    assert health["drift"]["status"] == "in_sync"


@pytest.mark.unit
def test_fed_006_health_endpoint_field(fed_manager: FederatedPolicyManager) -> None:
    # @trace FR-FED-006
    ep = fed_manager.get_federation_health_endpoint()
    assert ep["endpoint"] == "GET /governance/federation/health"
    assert "health" in ep


@pytest.mark.unit
def test_fed_006_health_has_checked_at_utc(fed_manager: FederatedPolicyManager) -> None:
    # @trace FR-FED-006
    health = fed_manager.get_federation_health()
    assert "checked_at_utc" in health
