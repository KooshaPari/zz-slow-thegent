import pytest

from thegent.governance.isolation import AccessDenied, TenantIsolationProvider
from thegent.phases.policy_federation import (
    FederatedPolicyEngine,
    PolicyConflictResolver,
)


@pytest.fixture
def tenant_a_engine():
    return FederatedPolicyEngine(namespace="acme.payments")


@pytest.fixture
def tenant_b_engine():
    return FederatedPolicyEngine(namespace="competitor.analytics")


@pytest.fixture
def isolation_provider():
    return TenantIsolationProvider()


def test_tb001_tenant_isolation(tenant_a_engine, tenant_b_engine):
    """TB-001: Attempt to read Policy A from Tenant B's context."""
    # Set policy in Tenant A
    tenant_a_engine.set_policy("cost_cap", 100.0)

    # Verify Tenant B cannot access Tenant A's policies
    assert tenant_b_engine.get_policy("cost_cap") is None


def test_tb002_policy_inheritance():
    """TB-002: Tenant A (Org level) defines a 'No High-Cost Models' policy."""
    org_engine = FederatedPolicyEngine(namespace="acme")
    org_engine.set_policy("max_model_cost", 0.10)

    project_engine = FederatedPolicyEngine(namespace="acme.payments")

    # Verify project inherits org policy
    assert project_engine.get_policy("max_model_cost") == 0.10

    # Verify policy is enforced
    assert not project_engine.is_allowed("model", {"cost": 0.15})
    assert project_engine.is_allowed("model", {"cost": 0.05})


def test_tb003_policy_overrides():
    """TB-003: Tenant A (Project level) overrides Org level 'Standard Lane' policy."""
    org_engine = FederatedPolicyEngine(namespace="acme_org")
    org_engine.set_policy("default_lane", "standard")

    project_engine = FederatedPolicyEngine(namespace="acme_org.payments")
    project_engine.set_policy("default_lane", "fast")

    # Verify project uses override
    assert project_engine.get_policy("default_lane") == "fast"

    # Verify other projects use org default
    other_project = FederatedPolicyEngine(namespace="acme_org.analytics")
    assert other_project.get_policy("default_lane") == "standard"


def test_tb004_telemetry_leakage(isolation_provider):
    """TB-004: Run A emits telemetry. Tenant B attempts to access it via session ID."""
    # Create session in Tenant A
    session_a = isolation_provider.create_session("acme.payments", "session-1")
    session_a.emit_telemetry({"event": "model_call", "cost": 0.50})

    # Attempt to access from Tenant B
    with pytest.raises(AccessDenied):
        isolation_provider.get_session_telemetry("competitor.analytics", "session-1")

    # Verify Tenant A can access its own telemetry
    telemetry_a = isolation_provider.get_session_telemetry("acme.payments", "session-1")
    assert len(telemetry_a) == 1
    assert telemetry_a[0]["cost"] == 0.50


def test_tb005_policy_conflict():
    """TB-005: Two namespaces provide conflicting 'Auto-Approve' rules."""
    resolver = PolicyConflictResolver()

    # Define conflicting policies
    policies = [
        {"namespace": "acme", "rules": {"auto_approve": False}},
        {"namespace": "acme.payments", "rules": {"auto_approve": True}},
    ]

    # Resolve conflict (project overrides org)
    resolved = resolver.resolve(policies, "acme.payments")

    assert resolved["auto_approve"] is True, "Project-level policy should win"
