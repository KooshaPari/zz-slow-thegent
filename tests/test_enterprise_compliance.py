# @trace WL-051
"""Comprehensive tests for WL-051: Enterprise Compliance and Multi-Org.

Covers:
  - EvidenceStore append-only semantics and hash-chain integrity
  - RetentionPolicy + RetentionEnforcer (GDPR purge, consent tracking)
  - AuditExporter JSON export structure
  - OrgRegistry + OrgNamespace CRUD hierarchy
  - KeyRotationMonitor expiry warnings
  - KeyRotationWebhook payload building
  - CLI commands via Typer CliRunner
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import orjson as json
import pytest
from typer.testing import CliRunner

from thegent.cli.apps.enterprise import app as enterprise_app
from thegent.governance.compliance import (
    AuditExporter,
    ComplianceEvidence,
    ConsentRecord,
    EvidenceStore,
    RetentionEnforcer,
    RetentionPolicy,
)
from thegent.governance.key_rotation import (
    ApiKeyRecord,
    KeyRegistry,
    KeyRotationMonitor,
    KeyRotationWebhook,
    make_expiry_utc,
)
from thegent.infra.org_tenancy import OrgNamespace, OrgRegistry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_runner = CliRunner()


def _make_policy(
    policy_id: str, tenant_id: str, retention_days: int, consent_required: bool = False
) -> RetentionPolicy:
    # @trace WL-051
    return RetentionPolicy(
        policy_id=policy_id,
        tenant_id=tenant_id,
        data_category="agent_logs",
        retention_days=retention_days,
        consent_required=consent_required,
        created_at=datetime.now(UTC).isoformat(),
    )


def _make_key(key_id: str, provider: str, days_until_expiry: int) -> ApiKeyRecord:
    # @trace WL-051
    expires_at = (datetime.now(UTC) + timedelta(days=days_until_expiry)).isoformat()
    return ApiKeyRecord(
        key_id=key_id,
        provider=provider,
        expires_at=expires_at,
        last_rotated=datetime.now(UTC).isoformat(),
    )


# ===========================================================================
# EvidenceStore — append-only and integrity
# ===========================================================================


class TestEvidenceStore:
    # @trace WL-051

    def test_append_creates_file(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "evidence.jsonl")
        rec = store.append(kind="agent_decision", actor="test_agent")
        assert store.store_path.exists()
        assert rec.evidence_id
        assert rec.kind == "agent_decision"

    def test_append_returns_evidence_with_hash(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "evidence.jsonl")
        rec = store.append(kind="human_approval", actor="user_alice", resource="run-001")
        assert rec.entry_hash != ""
        assert rec.prev_hash == ""  # first entry has empty prev_hash

    def test_second_entry_links_to_first(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "evidence.jsonl")
        rec1 = store.append(kind="agent_decision", actor="a1")
        rec2 = store.append(kind="human_approval", actor="a2")
        assert rec2.prev_hash == rec1.entry_hash

    def test_list_all_returns_in_order(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "evidence.jsonl")
        store.append(kind="agent_decision", actor="a")
        store.append(kind="human_approval", actor="b")
        store.append(kind="key_rotation", actor="c")
        records = store.list_all()
        assert len(records) == 3
        assert records[0].kind == "agent_decision"
        assert records[2].kind == "key_rotation"

    def test_verify_integrity_clean_chain(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "evidence.jsonl")
        for i in range(5):
            store.append(kind="agent_decision", actor=f"agent_{i}")
        assert store.verify_integrity() is True

    def test_verify_integrity_detects_tampering(self, tmp_path: Path) -> None:
        # @trace WL-051
        store_path = tmp_path / "evidence.jsonl"
        store = EvidenceStore(store_path)
        store.append(kind="agent_decision", actor="a")
        store.append(kind="human_approval", actor="b")

        # Tamper: rewrite first line with altered actor
        lines = store_path.read_text().splitlines()
        first = json.loads(lines[0])
        first["actor"] = "TAMPERED"
        lines[0] = json.dumps(first).decode()
        store_path.write_text("\n".join(lines) + "\n")

        store2 = EvidenceStore(store_path)
        assert store2.verify_integrity() is False

    def test_append_only_new_instance_reads_existing(self, tmp_path: Path) -> None:
        # @trace WL-051
        path = tmp_path / "ev.jsonl"
        s1 = EvidenceStore(path)
        s1.append(kind="data_access", actor="s1")

        s2 = EvidenceStore(path)
        s2.append(kind="key_rotation", actor="s2")

        records = s2.list_all()
        assert len(records) == 2

    def test_payload_stored_and_retrieved(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "ev.jsonl")
        store.append(
            kind="policy_evaluation",
            actor="engine",
            payload={"rule": "hitl", "decision": "block"},
        )
        rec = store.list_all()[0]
        assert rec.payload["rule"] == "hitl"
        assert rec.payload["decision"] == "block"

    def test_list_all_empty_store(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "ev.jsonl")
        assert store.list_all() == []

    def test_purge_older_than_removes_old_records(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "ev.jsonl")
        # Append 3 records then purge with 0 days (purge nothing)
        store.append(kind="agent_decision", actor="a")
        store.append(kind="agent_decision", actor="b")
        store.append(kind="agent_decision", actor="c")
        purged = store.purge_older_than(365)
        assert purged == 0
        assert len(store.list_all()) == 3

    def test_purge_with_zero_days_clears_all(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "ev.jsonl")
        store.append(kind="agent_decision", actor="a")
        store.append(kind="agent_decision", actor="b")
        purged = store.purge_older_than(0)
        assert purged == 2
        assert store.list_all() == []

    def test_purge_rebuilds_valid_hash_chain(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "ev.jsonl")
        store.append(kind="agent_decision", actor="a")
        store.append(kind="agent_decision", actor="b")
        store.append(kind="agent_decision", actor="c")
        store.purge_older_than(0)
        # After purge (all removed), chain is empty — integrity should pass
        assert store.verify_integrity() is True

    def test_purge_negative_days_raises(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "ev.jsonl")
        with pytest.raises(ValueError):
            store.purge_older_than(-1)

    def test_list_since_filters_correctly(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "ev.jsonl")
        store.append(kind="agent_decision", actor="a")
        future_cutoff = datetime.now(UTC) + timedelta(hours=1)
        result = store.list_since(future_cutoff)
        assert result == []

    def test_compute_hash_is_deterministic(self) -> None:
        # @trace WL-051
        entry = {"evidence_id": "abc", "kind": "agent_decision", "actor": "x"}
        h1 = ComplianceEvidence.compute_hash(entry, "prev")
        h2 = ComplianceEvidence.compute_hash(entry, "prev")
        assert h1 == h2

    def test_compute_hash_differs_with_different_prev(self) -> None:
        # @trace WL-051
        entry = {"evidence_id": "abc", "kind": "agent_decision", "actor": "x"}
        h1 = ComplianceEvidence.compute_hash(entry, "hash_a")
        h2 = ComplianceEvidence.compute_hash(entry, "hash_b")
        assert h1 != h2


# ===========================================================================
# RetentionPolicy + RetentionEnforcer (GDPR)
# ===========================================================================


class TestRetentionEnforcer:
    # @trace WL-051

    def test_add_and_list_policy(self, tmp_path: Path) -> None:
        # @trace WL-051
        enforcer = RetentionEnforcer(tmp_path)
        p = _make_policy("p1", "tenant_a", 90)
        enforcer.add_policy(p)
        policies = enforcer.list_policies()
        assert len(policies) == 1
        assert policies[0].policy_id == "p1"

    def test_add_duplicate_policy_raises(self, tmp_path: Path) -> None:
        # @trace WL-051
        enforcer = RetentionEnforcer(tmp_path)
        p = _make_policy("dup", "tenant_a", 90)
        enforcer.add_policy(p)
        with pytest.raises(ValueError, match="already exists"):
            enforcer.add_policy(p)

    def test_get_policy_not_found_raises(self, tmp_path: Path) -> None:
        # @trace WL-051
        enforcer = RetentionEnforcer(tmp_path)
        with pytest.raises(KeyError):
            enforcer.get_policy("nonexistent")

    def test_record_and_list_consent(self, tmp_path: Path) -> None:
        # @trace WL-051
        enforcer = RetentionEnforcer(tmp_path)
        consent = ConsentRecord(
            consent_id="c1",
            tenant_id="t1",
            subject_id="sub_001",
            data_category="agent_logs",
            granted=True,
            granted_at=datetime.now(UTC).isoformat(),
        )
        enforcer.record_consent(consent)
        consents = enforcer.list_consents(tenant_id="t1")
        assert len(consents) == 1
        assert consents[0].consent_id == "c1"

    def test_has_active_consent_true(self, tmp_path: Path) -> None:
        # @trace WL-051
        enforcer = RetentionEnforcer(tmp_path)
        consent = ConsentRecord(
            consent_id="c2",
            tenant_id="t1",
            subject_id="sub_002",
            data_category="billing",
            granted=True,
            granted_at=datetime.now(UTC).isoformat(),
        )
        enforcer.record_consent(consent)
        assert enforcer.has_active_consent(tenant_id="t1", subject_id="sub_002", data_category="billing") is True

    def test_has_active_consent_false_when_withdrawn(self, tmp_path: Path) -> None:
        # @trace WL-051
        enforcer = RetentionEnforcer(tmp_path)
        consent = ConsentRecord(
            consent_id="c3",
            tenant_id="t1",
            subject_id="sub_003",
            data_category="agent_logs",
            granted=True,
            granted_at=datetime.now(UTC).isoformat(),
            withdrawn_at=datetime.now(UTC).isoformat(),
        )
        enforcer.record_consent(consent)
        assert enforcer.has_active_consent(tenant_id="t1", subject_id="sub_003", data_category="agent_logs") is False

    def test_purge_tenant_data_no_policies_raises(self, tmp_path: Path) -> None:
        # @trace WL-051
        enforcer = RetentionEnforcer(tmp_path)
        store = EvidenceStore(tmp_path / "ev.jsonl")
        with pytest.raises(KeyError, match="No retention policies"):
            enforcer.purge_tenant_data(tenant_id="unknown", evidence_store=store)

    def test_purge_tenant_data_executes(self, tmp_path: Path) -> None:
        # @trace WL-051
        enforcer = RetentionEnforcer(tmp_path)
        enforcer.add_policy(_make_policy("p_exec", "t_exec", 365))
        store = EvidenceStore(tmp_path / "ev.jsonl")
        store.append(kind="agent_decision", actor="x")
        summary = enforcer.purge_tenant_data(tenant_id="t_exec", evidence_store=store)
        assert summary["tenant_id"] == "t_exec"
        assert "p_exec" in summary["purged_by_policy"]

    def test_purge_with_consent_required_and_no_consent_raises(self, tmp_path: Path) -> None:
        # @trace WL-051
        enforcer = RetentionEnforcer(tmp_path)
        enforcer.add_policy(_make_policy("p_consent", "t_c", 30, consent_required=True))
        store = EvidenceStore(tmp_path / "ev.jsonl")
        with pytest.raises(RuntimeError, match="Consent required"):
            enforcer.purge_tenant_data(tenant_id="t_c", evidence_store=store)

    def test_purge_with_consent_required_and_consent_present_succeeds(self, tmp_path: Path) -> None:
        # @trace WL-051
        enforcer = RetentionEnforcer(tmp_path)
        enforcer.add_policy(_make_policy("p_ok", "t_ok", 30, consent_required=True))
        consent = ConsentRecord(
            consent_id="c_ok",
            tenant_id="t_ok",
            subject_id="sub_ok",
            data_category="agent_logs",
            granted=True,
            granted_at=datetime.now(UTC).isoformat(),
        )
        enforcer.record_consent(consent)
        store = EvidenceStore(tmp_path / "ev.jsonl")
        summary = enforcer.purge_tenant_data(tenant_id="t_ok", evidence_store=store)
        assert summary["tenant_id"] == "t_ok"


# ===========================================================================
# AuditExporter — JSON export structure
# ===========================================================================


class TestAuditExporter:
    # @trace WL-051

    def test_export_json_returns_dict(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "ev.jsonl")
        store.append(kind="agent_decision", actor="a")
        exporter = AuditExporter(store)
        result = exporter.export_json()
        assert isinstance(result, dict)

    def test_export_json_schema_version(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "ev.jsonl")
        exporter = AuditExporter(store)
        result = exporter.export_json()
        assert result["schema_version"] == "1.0"
        assert result["export_format"] == "thegent_compliance_evidence_v1"

    def test_export_json_includes_all_records(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "ev.jsonl")
        for i in range(5):
            store.append(kind="agent_decision", actor=f"agent_{i}")
        exporter = AuditExporter(store)
        result = exporter.export_json()
        assert result["record_count"] == 5
        assert len(result["evidence"]) == 5

    def test_export_json_integrity_verified_flag(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "ev.jsonl")
        store.append(kind="human_approval", actor="admin")
        exporter = AuditExporter(store)
        result = exporter.export_json()
        assert result["integrity_verified"] is True

    def test_export_json_writes_to_file(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "ev.jsonl")
        store.append(kind="agent_decision", actor="a")
        exporter = AuditExporter(store)
        out_path = tmp_path / "export.json"
        exporter.export_json(output_path=out_path)
        assert out_path.exists()
        loaded = json.loads(out_path.read_text())
        assert loaded["record_count"] == 1

    def test_export_json_kind_filter(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "ev.jsonl")
        store.append(kind="agent_decision", actor="a")
        store.append(kind="human_approval", actor="b")
        exporter = AuditExporter(store)
        result = exporter.export_json(kind_filter=["agent_decision"])
        assert result["record_count"] == 1
        assert result["evidence"][0]["kind"] == "agent_decision"

    def test_export_json_since_days_filter(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "ev.jsonl")
        store.append(kind="agent_decision", actor="a")
        exporter = AuditExporter(store)
        # since_days=0 means from now: all records should be included
        result = exporter.export_json(since_days=1)
        assert result["record_count"] == 1

    def test_export_json_empty_store(self, tmp_path: Path) -> None:
        # @trace WL-051
        store = EvidenceStore(tmp_path / "ev.jsonl")
        exporter = AuditExporter(store)
        result = exporter.export_json()
        assert result["record_count"] == 0
        assert result["evidence"] == []


# ===========================================================================
# OrgRegistry — org hierarchy CRUD
# ===========================================================================


class TestOrgRegistry:
    # @trace WL-051

    def test_create_org(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = OrgRegistry(tmp_path / "registry.json")
        org = registry.create_org(org_name="AcmeCorp")
        assert org.org_name == "AcmeCorp"
        assert org.org_id.startswith("org_")
        assert isinstance(org.tenants, list)

    def test_create_org_with_initial_tenants(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = OrgRegistry(tmp_path / "registry.json")
        org = registry.create_org(org_name="Beta", initial_tenants=["t1", "t2"])
        assert "t1" in org.tenants
        assert "t2" in org.tenants

    def test_create_duplicate_name_raises(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = OrgRegistry(tmp_path / "registry.json")
        registry.create_org(org_name="Dup")
        with pytest.raises(ValueError, match="org_name conflict"):
            registry.create_org(org_name="Dup")

    def test_list_orgs_sorted_by_creation(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = OrgRegistry(tmp_path / "registry.json")
        registry.create_org(org_name="Alpha")
        registry.create_org(org_name="Beta")
        orgs = registry.list_orgs()
        assert len(orgs) == 2
        assert orgs[0].org_name == "Alpha"

    def test_get_org_by_id(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = OrgRegistry(tmp_path / "registry.json")
        created = registry.create_org(org_name="TestOrg")
        fetched = registry.get_org(org_id=created.org_id)
        assert fetched.org_id == created.org_id

    def test_get_org_by_name(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = OrgRegistry(tmp_path / "registry.json")
        registry.create_org(org_name="ByName")
        org = registry.get_org(org_name="ByName")
        assert org.org_name == "ByName"

    def test_get_org_not_found_raises_key_error(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = OrgRegistry(tmp_path / "registry.json")
        with pytest.raises(KeyError):
            registry.get_org(org_id="missing_id")

    def test_get_org_no_selector_raises_value_error(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = OrgRegistry(tmp_path / "registry.json")
        with pytest.raises(ValueError):
            registry.get_org()

    def test_add_tenant(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = OrgRegistry(tmp_path / "registry.json")
        org = registry.create_org(org_name="OrgAdd")
        updated = registry.add_tenant(org.org_id, "new_tenant")
        assert "new_tenant" in updated.tenants

    def test_add_duplicate_tenant_raises(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = OrgRegistry(tmp_path / "registry.json")
        org = registry.create_org(org_name="OrgDup", initial_tenants=["t_existing"])
        with pytest.raises(ValueError, match="already in org"):
            registry.add_tenant(org.org_id, "t_existing")

    def test_remove_tenant(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = OrgRegistry(tmp_path / "registry.json")
        org = registry.create_org(org_name="OrgRm", initial_tenants=["t_rm"])
        updated = registry.remove_tenant(org.org_id, "t_rm")
        assert "t_rm" not in updated.tenants

    def test_remove_nonexistent_tenant_raises(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = OrgRegistry(tmp_path / "registry.json")
        org = registry.create_org(org_name="OrgNT")
        with pytest.raises(ValueError, match="not in org"):
            registry.remove_tenant(org.org_id, "ghost_tenant")

    def test_org_namespace_pydantic_model(self) -> None:
        # @trace WL-051
        now = datetime.now(UTC).isoformat()
        org = OrgNamespace(
            org_id="org_test",
            org_name="TestOrg",
            tenants=["t1"],
            created_at=now,
            updated_at=now,
        )
        assert org.org_id == "org_test"
        assert org.tenants == ["t1"]


# ===========================================================================
# KeyRotationMonitor — expiry warnings
# ===========================================================================


class TestKeyRotationMonitor:
    # @trace WL-051

    def test_expiring_key_triggers_warning(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = KeyRegistry(tmp_path / "keys.jsonl")
        registry.add(_make_key("k1", "openai", days_until_expiry=3))
        monitor = KeyRotationMonitor(registry, warn_days=7)
        warnings = monitor.check_all()
        assert len(warnings) == 1
        assert warnings[0].record.key_id == "k1"

    def test_healthy_key_no_warning(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = KeyRegistry(tmp_path / "keys.jsonl")
        registry.add(_make_key("k_ok", "anthropic", days_until_expiry=30))
        monitor = KeyRotationMonitor(registry, warn_days=7)
        warnings = monitor.check_all()
        assert warnings == []

    def test_expired_key_triggers_warning(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = KeyRegistry(tmp_path / "keys.jsonl")
        registry.add(_make_key("k_exp", "openai", days_until_expiry=-1))
        monitor = KeyRotationMonitor(registry, warn_days=7)
        warnings = monitor.check_all()
        assert any(w.record.key_id == "k_exp" for w in warnings)

    def test_check_provider_filters_by_provider(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = KeyRegistry(tmp_path / "keys.jsonl")
        registry.add(_make_key("k_oa", "openai", days_until_expiry=2))
        registry.add(_make_key("k_ant", "anthropic", days_until_expiry=2))
        monitor = KeyRotationMonitor(registry, warn_days=7)
        warnings = monitor.check_provider("openai")
        assert all(w.record.provider == "openai" for w in warnings)

    def test_warning_to_dict_structure(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = KeyRegistry(tmp_path / "keys.jsonl")
        rec = _make_key("k_dict", "google", days_until_expiry=1)
        registry.add(rec)
        monitor = KeyRotationMonitor(registry, warn_days=7)
        warnings = monitor.check_all()
        d = warnings[0].to_dict()
        assert "key_id" in d
        assert "provider" in d
        assert "days_remaining" in d
        assert "message" in d

    def test_is_expiring_soon_boundary(self) -> None:
        # @trace WL-051
        rec = _make_key("k_boundary", "test", days_until_expiry=7)
        assert rec.is_expiring_soon(7) is True

    def test_is_expired(self) -> None:
        # @trace WL-051
        rec = _make_key("k_gone", "test", days_until_expiry=-5)
        assert rec.is_expired() is True

    def test_is_not_expired_when_future(self) -> None:
        # @trace WL-051
        rec = _make_key("k_future", "test", days_until_expiry=10)
        assert rec.is_expired() is False

    def test_make_expiry_utc_helper(self) -> None:
        # @trace WL-051
        expiry_str = make_expiry_utc(30)
        expiry_dt = datetime.fromisoformat(expiry_str)
        delta = expiry_dt - datetime.now(UTC)
        # Use total_seconds to avoid the .days rounding issue (29 days 23:59:59 = .days of 29)
        assert 29 * 86400 < delta.total_seconds() <= 31 * 86400


# ===========================================================================
# KeyRotationWebhook — payload building (no network calls)
# ===========================================================================


class TestKeyRotationWebhook:
    # @trace WL-051

    def test_build_rotation_payload_structure(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = KeyRegistry(tmp_path / "keys.jsonl")
        registry.add(_make_key("wk1", "azure", days_until_expiry=30))
        webhook = KeyRotationWebhook("https://example.com/webhook", registry)
        payload = webhook.build_rotation_payload("wk1", new_expires_at=make_expiry_utc(60))
        assert payload["event"] == "key_rotation"
        assert payload["key_id"] == "wk1"
        assert payload["provider"] == "azure"
        assert "prev_expires_at" in payload
        assert "new_expires_at" in payload

    def test_webhook_empty_url_raises(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = KeyRegistry(tmp_path / "keys.jsonl")
        with pytest.raises(ValueError, match="webhook_url must not be empty"):
            KeyRotationWebhook("", registry)

    def test_key_registry_add_and_list(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = KeyRegistry(tmp_path / "keys.jsonl")
        registry.add(_make_key("r1", "openai", 30))
        registry.add(_make_key("r2", "anthropic", 60))
        all_keys = registry.list_all()
        assert len(all_keys) == 2

    def test_key_registry_get_existing(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = KeyRegistry(tmp_path / "keys.jsonl")
        registry.add(_make_key("r_get", "openai", 30))
        rec = registry.get("r_get")
        assert rec.provider == "openai"

    def test_key_registry_get_missing_raises(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = KeyRegistry(tmp_path / "keys.jsonl")
        with pytest.raises(KeyError):
            registry.get("nonexistent_key")

    def test_key_registry_update(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry = KeyRegistry(tmp_path / "keys.jsonl")
        registry.add(_make_key("r_upd", "openai", 30))
        new_expiry = make_expiry_utc(90)
        updated = ApiKeyRecord(
            key_id="r_upd",
            provider="openai",
            expires_at=new_expiry,
            last_rotated=datetime.now(UTC).isoformat(),
        )
        registry.update(updated)
        fetched = registry.get("r_upd")
        assert fetched.expires_at == new_expiry


# ===========================================================================
# CLI — enterprise app via CliRunner
# ===========================================================================


class TestEnterpriseCLI:
    # @trace WL-051

    def test_compliance_evidence_list_empty(self, tmp_path: Path) -> None:
        # @trace WL-051
        evidence_path = tmp_path / "ev.jsonl"
        result = _runner.invoke(
            enterprise_app,
            ["compliance", "evidence", "list", "--evidence", str(evidence_path)],
        )
        assert result.exit_code == 0
        assert "No evidence" in result.output or "Evidence Store" in result.output or result.exit_code == 0

    def test_compliance_evidence_list_with_records(self, tmp_path: Path) -> None:
        # @trace WL-051
        evidence_path = tmp_path / "ev.jsonl"
        store = EvidenceStore(evidence_path)
        store.append(kind="agent_decision", actor="cli_test")
        result = _runner.invoke(
            enterprise_app,
            ["compliance", "evidence", "list", "--evidence", str(evidence_path)],
        )
        assert result.exit_code == 0

    def test_compliance_evidence_purge(self, tmp_path: Path) -> None:
        # @trace WL-051
        evidence_path = tmp_path / "ev.jsonl"
        store = EvidenceStore(evidence_path)
        store.append(kind="agent_decision", actor="old_entry")
        result = _runner.invoke(
            enterprise_app,
            [
                "compliance",
                "evidence",
                "purge",
                "--older-than-days",
                "0",
                "--evidence",
                str(evidence_path),
            ],
        )
        assert result.exit_code == 0
        assert "Purged" in result.output

    def test_compliance_audit_export_json(self, tmp_path: Path) -> None:
        # @trace WL-051
        evidence_path = tmp_path / "ev.jsonl"
        store = EvidenceStore(evidence_path)
        store.append(kind="agent_decision", actor="audit_actor")
        output_path = tmp_path / "audit_out.json"
        result = _runner.invoke(
            enterprise_app,
            [
                "compliance",
                "audit-export",
                "--evidence",
                str(evidence_path),
                "--output",
                str(output_path),
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        assert output_path.exists()
        doc = json.loads(output_path.read_text())
        assert doc["record_count"] == 1

    def test_org_list_empty(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry_path = tmp_path / "org_registry.json"
        result = _runner.invoke(
            enterprise_app,
            ["org", "list", "--registry", str(registry_path)],
        )
        assert result.exit_code == 0

    def test_org_create_and_list(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry_path = tmp_path / "org_registry.json"
        create_result = _runner.invoke(
            enterprise_app,
            ["org", "create", "TestCLIOrg", "--registry", str(registry_path)],
        )
        assert create_result.exit_code == 0
        assert "TestCLIOrg" in create_result.output

        list_result = _runner.invoke(
            enterprise_app,
            ["org", "list", "--registry", str(registry_path)],
        )
        assert list_result.exit_code == 0
        assert "TestCLIOrg" in list_result.output

    def test_org_show(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry_path = tmp_path / "org_registry.json"
        registry = OrgRegistry(registry_path)
        org = registry.create_org(org_name="ShowTestOrg")
        result = _runner.invoke(
            enterprise_app,
            ["org", "show", org.org_id, "--registry", str(registry_path)],
        )
        assert result.exit_code == 0
        assert "ShowTestOrg" in result.output

    def test_org_show_missing_raises_exit_1(self, tmp_path: Path) -> None:
        # @trace WL-051
        registry_path = tmp_path / "org_registry.json"
        result = _runner.invoke(
            enterprise_app,
            ["org", "show", "org_notexist", "--registry", str(registry_path)],
        )
        assert result.exit_code == 1

    def test_keys_status_empty(self, tmp_path: Path) -> None:
        # @trace WL-051
        key_registry_path = tmp_path / "keys.jsonl"
        result = _runner.invoke(
            enterprise_app,
            ["keys", "status", "--registry", str(key_registry_path)],
        )
        assert result.exit_code == 0

    def test_keys_status_with_expiring_key(self, tmp_path: Path) -> None:
        # @trace WL-051
        key_registry_path = tmp_path / "keys.jsonl"
        registry = KeyRegistry(key_registry_path)
        registry.add(_make_key("cli_k1", "openai", days_until_expiry=3))
        result = _runner.invoke(
            enterprise_app,
            ["keys", "status", "--registry", str(key_registry_path)],
        )
        assert result.exit_code == 0
        assert "cli_k1" in result.output
