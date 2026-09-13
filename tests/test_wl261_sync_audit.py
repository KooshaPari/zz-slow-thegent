"""Tests for sync policy audit command (WL-261).

# @trace WL-261
"""

from __future__ import annotations

import re
from pathlib import Path

import orjson as json
import pytest

from thegent.integrations.sync_auditor import SyncAuditor, SyncPolicyAudit


class TestSyncAuditor:
    """Test SyncAuditor class."""

    @pytest.mark.requirement("WL-261")
    def test_auditor_creation(self):
        """Test creating a sync auditor."""
        auditor = SyncAuditor()
        assert auditor is not None

    @pytest.mark.requirement("WL-261")
    def test_set_enabled_connectors(self):
        """Test setting enabled connectors."""
        auditor = SyncAuditor()
        auditor.set_enabled_connectors(["github", "gitlab"])
        assert auditor._enabled_connectors == ["github", "gitlab"]

    @pytest.mark.requirement("WL-261")
    def test_set_quota_budgets(self):
        """Test setting quota budgets."""
        auditor = SyncAuditor()
        budgets = {"github": 100, "gitlab": 50}
        auditor.set_quota_budgets(budgets)
        assert auditor._quota_budgets == budgets

    @pytest.mark.requirement("WL-261")
    def test_set_policy_modes(self):
        """Test setting policy modes."""
        auditor = SyncAuditor()
        modes = {"github": "enforce", "gitlab": "warn"}
        auditor.set_policy_modes(modes)
        assert auditor._policy_modes == modes

    @pytest.mark.requirement("WL-244")
    def test_generate_html_diff_artifact_includes_expected_markers(self, tmp_path: Path):
        """HTML diff artifact should be deterministic and include local/remote side labels."""
        local_snapshot = {"status": "ok", "items": ["wl-1", "wl-2"]}
        remote_snapshot = {"status": "drift", "items": ["wl-1"]}
        output = tmp_path / "sync-diff.html"

        SyncAuditor.generate_html_diff_artifact(local_snapshot, remote_snapshot, output)
        second_path = tmp_path / "sync-diff-2.html"
        SyncAuditor.generate_html_diff_artifact(local_snapshot, remote_snapshot, second_path)

        html = output.read_text(encoding="utf-8")
        second = second_path.read_text(encoding="utf-8")

        def normalize(value: str) -> str:
            value = re.sub(r"difflib_chg_to\d+__", "difflib_chg_to0__", value)
            value = re.sub(r"from\d+_", "from0_", value)
            value = re.sub(r"to\d+_", "to0_", value)
            return value

        assert output.exists()
        assert second_path.exists()
        assert normalize(html) == normalize(second)
        assert '<table class="diff"' in html
        assert 'colspan="2" class="diff_header">local' in html
        assert 'colspan="2" class="diff_header">remote' in html

    @pytest.mark.requirement("WL-261")
    def test_audit_returns_audit_info(self):
        """Test audit returns SyncPolicyAudit."""
        auditor = SyncAuditor()
        auditor.set_enabled_connectors(["github"])
        auditor.set_quota_budgets({"github": 100})
        auditor.set_policy_modes({"github": "enforce"})

        result = auditor.audit()

        assert isinstance(result, SyncPolicyAudit)
        assert result.enabled_connectors == ["github"]
        assert result.quota_budgets == {"github": 100}
        assert result.policy_modes == {"github": "enforce"}
        assert result.audit_status == "success"
        assert result.timestamp is not None

    @pytest.mark.requirement("WL-261")
    def test_audit_as_json(self):
        """Test audit as JSON."""
        auditor = SyncAuditor()
        auditor.set_enabled_connectors(["github"])
        auditor.set_quota_budgets({"github": 100})
        auditor.set_policy_modes({"github": "enforce"})

        json_str = auditor.audit_as_json()

        data = json.loads(json_str)
        assert data["enabled_connectors"] == ["github"]
        assert data["quota_budgets"] == {"github": 100}
        assert data["policy_modes"] == {"github": "enforce"}
        assert data["audit_status"] == "success"

    @pytest.mark.requirement("WL-261")
    def test_audit_as_dict(self):
        """Test audit as dictionary."""
        auditor = SyncAuditor()
        auditor.set_enabled_connectors(["github", "gitlab"])
        auditor.set_quota_budgets({"github": 100, "gitlab": 50})
        auditor.set_policy_modes({"github": "enforce", "gitlab": "warn"})

        result = auditor.audit_as_dict()

        assert isinstance(result, dict)
        assert result["enabled_connectors"] == ["github", "gitlab"]
        assert result["quota_budgets"] == {"github": 100, "gitlab": 50}
        assert result["policy_modes"] == {"github": "enforce", "gitlab": "warn"}

    @pytest.mark.requirement("WL-261")
    def test_validate_policy_valid(self):
        """Test policy validation with valid config."""
        auditor = SyncAuditor()
        auditor.set_enabled_connectors(["github", "gitlab"])
        auditor.set_quota_budgets({"github": 100, "gitlab": 50})
        auditor.set_policy_modes({"github": "enforce", "gitlab": "warn"})

        is_valid, issues = auditor.validate_policy()

        assert is_valid is True
        assert len(issues) == 0

    @pytest.mark.requirement("WL-261")
    def test_validate_policy_no_connectors(self):
        """Test policy validation with no connectors."""
        auditor = SyncAuditor()

        is_valid, issues = auditor.validate_policy()

        assert is_valid is False
        assert "No connectors are enabled" in issues

    @pytest.mark.requirement("WL-261")
    def test_validate_policy_quota_without_connector(self):
        """Test policy validation with quota for disabled connector."""
        auditor = SyncAuditor()
        auditor.set_enabled_connectors(["github"])
        auditor.set_quota_budgets({"github": 100, "unknown": 50})

        is_valid, issues = auditor.validate_policy()

        assert is_valid is False
        assert any("disabled connector" in issue for issue in issues)

    @pytest.mark.requirement("WL-261")
    def test_validate_policy_invalid_quota(self):
        """Test policy validation with invalid quota."""
        auditor = SyncAuditor()
        auditor.set_enabled_connectors(["github"])
        auditor.set_quota_budgets({"github": 0})
        auditor.set_policy_modes({"github": "enforce"})

        is_valid, issues = auditor.validate_policy()

        assert is_valid is False
        assert any("must be > 0" in issue for issue in issues)

    @pytest.mark.requirement("WL-261")
    def test_validate_policy_missing_mode(self):
        """Test policy validation with missing policy mode."""
        auditor = SyncAuditor()
        auditor.set_enabled_connectors(["github", "gitlab"])
        auditor.set_quota_budgets({"github": 100, "gitlab": 50})
        auditor.set_policy_modes({"github": "enforce"})  # Missing gitlab

        is_valid, issues = auditor.validate_policy()

        assert is_valid is False
        assert any("gitlab" in issue and "Missing policy mode" in issue for issue in issues)


@pytest.mark.requirement("WL-249")
def test_detect_local_orphans_report() -> None:
    """Local orphan detection should return local-only IDs and mapping metadata."""
    report = SyncAuditor.detect_local_orphans(
        local_ids=["WL-101", "WL-102", "WL-103"],
        mapped_remote_ids=["WL-101", "WL-105"],
    )
    assert report.local_ids == ["WL-101", "WL-102", "WL-103"]
    assert report.mapped_remote_ids == ["WL-101", "WL-105"]
    assert report.local_orphan_ids == ["WL-102", "WL-103"]
    assert report.orphan_count == 2
    assert report.to_dict()["local_orphan_ids"] == ["WL-102", "WL-103"]

    @pytest.mark.requirement("WL-197")
    def test_load_policy_contract_maps_connector_fields(self, tmp_path: Path):
        """load_policy_contract reads .thegent/sync-policy.yaml into audit surfaces."""
        policy_path = tmp_path / ".thegent" / "sync-policy.yaml"
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        policy_path.write_text(
            """
schema_version: sync-policy/v1
conflict_precedence: board_id_first
strict_mode: true
connectors:
  github:
    enabled: true
    mode: enforce
    direction: bidirectional
    quota_daily: 123
tenancy:
  mode: single_project
  default_tenant: tenant-default
  projects: []
""".strip(),
            encoding="utf-8",
        )

        auditor = SyncAuditor()
        contract = auditor.load_policy_contract(project_root=tmp_path)

        assert contract.schema_version == "sync-policy/v1"
        assert auditor._enabled_connectors == ["github"]
        assert auditor._quota_budgets == {"github": 123}
        assert auditor._policy_modes == {"github": "enforce"}

    @pytest.mark.requirement("WL-261")
    @pytest.mark.requirement("WL-232")
    def test_signed_audit_artifact_chain_verifies(self):
        """Signed audit artifact chain should verify when untouched."""
        auditor = SyncAuditor()
        auditor.append_artifact(
            sync_id="sync-1",
            source="github",
            operator="autosync",
            cycle_number=1,
            secret="lane6-secret",
        )
        auditor.append_artifact(
            sync_id="sync-2",
            source="linear",
            operator="autosync",
            cycle_number=2,
            secret="lane6-secret",
        )
        ok, reason = auditor.verify_artifact_chain("lane6-secret")
        assert ok is True
        assert reason == ""

    @pytest.mark.requirement("WL-261")
    @pytest.mark.requirement("WL-232")
    def test_signed_audit_artifact_chain_detects_tamper(self):
        """Chain verification must fail after tampering."""
        auditor = SyncAuditor()
        auditor.append_artifact(
            sync_id="sync-1",
            source="github",
            operator="autosync",
            cycle_number=1,
            secret="lane6-secret",
        )
        auditor.append_artifact(
            sync_id="sync-2",
            source="linear",
            operator="autosync",
            cycle_number=2,
            secret="lane6-secret",
        )
        auditor._artifact_chain[1].signature = "tampered"  # noqa: SLF001 -- test-only tamper simulation
        ok, reason = auditor.verify_artifact_chain("lane6-secret")
        assert ok is False
        assert "signature verification failed" in reason
