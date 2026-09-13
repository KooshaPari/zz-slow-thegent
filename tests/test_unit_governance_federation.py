import pytest

from thegent.governance.federation import FederatedPolicyManager, PolicyNamespace


@pytest.fixture
def manager(tmp_path):
    return FederatedPolicyManager(tmp_path)


def test_relay_consent(manager):
    ns1 = PolicyNamespace("org1", "proj1", "prod")
    ns2 = PolicyNamespace("org2", "proj2", "prod")
    run_id = "run_123"
    approver = "admin_user"

    artifact = manager.relay_consent(ns1, ns2, run_id, approver)

    assert artifact["type"] == "consent_relay"
    assert artifact["source_namespace"] == "org1.proj1.prod"
    assert artifact["target_namespace"] == "org2.proj2.prod"
    assert artifact["run_id"] == run_id
    assert artifact["approver"] == approver
    assert "provenance_signature" in artifact
    assert artifact["status"] == "active"


def test_policy_resolution_hierarchy(manager, tmp_path):
    # Setup hierarchy
    (tmp_path / "org1" / "proj1" / "prod").mkdir(parents=True)
    (tmp_path / "org1" / "proj1" / "default").mkdir(parents=True)
    (tmp_path / "org1" / "default" / "default").mkdir(parents=True)

    # 1. Root default
    (tmp_path / "org1" / "default" / "default" / "p1.json").write_text('{"level": "root"}')
    # 2. Org project default
    (tmp_path / "org1" / "proj1" / "default" / "p1.json").write_text('{"level": "project"}')
    # 3. Specific env
    (tmp_path / "org1" / "proj1" / "prod" / "p1.json").write_text('{"level": "env"}')

    ns = PolicyNamespace("org1", "proj1", "prod")

    # Resolves to most specific
    policy = manager.resolve_policy(ns, "p1")
    assert policy["level"] == "env"

    # Remove env policy
    (tmp_path / "org1" / "proj1" / "prod" / "p1.json").unlink()
    policy = manager.resolve_policy(ns, "p1")
    assert policy["level"] == "project"

    # Remove project policy
    (tmp_path / "org1" / "proj1" / "default" / "p1.json").unlink()
    policy = manager.resolve_policy(ns, "p1")
    assert policy["level"] == "root"
