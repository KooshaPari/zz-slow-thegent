"""AUDIT-N+77: governance/compliance_reports hardening spec (SOTA pass-61).

15 invariants FR-GOV-CR-001..015 covering ComplianceReporter init,
generate_report format guard, generate_governance_rollup defensive defaults,
build_governance_queue severity sorting, generate_governance_telemetry
coercion, export_report path existence, __all__ export, and deterministic output.

Source: src/thegent/governance/compliance_reports.py

@trace AUDIT-N+77 FR-GOV-CR-001..015
"""

from __future__ import annotations

import json

import pytest

from thegent.governance.compliance_reports import ComplianceReporter

# ---------------------------------------------------------------------------
# FR-GOV-CR-001 .. FR-GOV-CR-015
# ---------------------------------------------------------------------------


class TestComplianceReporterInit:
    def test_returns_compliance_reporter(self):
        r = ComplianceReporter()
        assert isinstance(r, ComplianceReporter)

    def test_has_reports_list(self):
        r = ComplianceReporter()
        assert hasattr(r, "reports")
        assert isinstance(r.reports, list)

    def test_has_generate_report_method(self):
        r = ComplianceReporter()
        assert callable(getattr(r, "generate_report", None))

    def test_has_export_report_method(self):
        r = ComplianceReporter()
        assert callable(getattr(r, "export_report", None))


class TestGenerateReportFormatGuard:
    def test_json_format(self):
        r = ComplianceReporter()
        result = r.generate_report({"findings": []}, format="json")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_unsupported_format_raises(self):
        r = ComplianceReporter()
        with pytest.raises(ValueError, match="Unsupported compliance report format"):
            r.generate_report({}, format="xml")

    def test_markdown_format(self):
        r = ComplianceReporter()
        result = r.generate_report({"findings": []}, format="markdown")
        assert isinstance(result, str)
        assert len(result) > 0


class TestGovernanceRollup:
    def test_empty_evidence_returns_empty_rollup(self):
        r = ComplianceReporter()
        rollup = r.generate_governance_rollup([])
        assert rollup["total_records"] == 0

    def test_missing_kind_defaults_to_unknown(self):
        r = ComplianceReporter()
        rollup = r.generate_governance_rollup([{"severity": "high"}])
        assert "unknown" in rollup.get("by_kind", {})

    def test_deterministic_output(self):
        r = ComplianceReporter()
        evidence = [
            {"kind": "a", "actor": "x", "severity": "low"},
            {"kind": "b", "actor": "y", "severity": "high"},
        ]
        r1 = r.generate_governance_rollup(evidence)
        r2 = r.generate_governance_rollup(evidence)
        assert r1 == r2


class TestBuildGovernanceQueue:
    def test_sorted_by_severity(self):
        r = ComplianceReporter()
        queue = r.build_governance_queue(
            [
                {
                    "payload": {"requires_action": True, "severity": "low"},
                    "timestamp_utc": "2025-01-01",
                },
                {
                    "payload": {"requires_action": True, "severity": "critical"},
                    "timestamp_utc": "2025-01-02",
                },
            ]
        )
        severities = [item["severity"] for item in queue]
        assert severities == ["critical", "low"]

    def test_unknown_severity_sorts_last(self):
        r = ComplianceReporter()
        queue = r.build_governance_queue(
            [
                {
                    "payload": {"requires_action": True, "severity": "unknown_xyz"},
                    "timestamp_utc": "2025-01-01",
                },
                {
                    "payload": {"requires_action": True, "severity": "critical"},
                    "timestamp_utc": "2025-01-02",
                },
            ]
        )
        assert queue[-1]["severity"] == "unknown_xyz"


class TestGovernanceTelemetry:
    def test_returns_dict(self):
        r = ComplianceReporter()
        result = r.generate_governance_telemetry(rollup={"total_records": 5}, queue=[])
        assert isinstance(result, dict)
        assert result["total_records"] == 5

    def test_coerces_total_records_to_int(self):
        r = ComplianceReporter()
        result = r.generate_governance_telemetry(rollup={"total_records": "10"}, queue=[])
        assert result["total_records"] == 10


class TestExportReport:
    def test_exports_json_to_path(self, tmp_path):
        r = ComplianceReporter()
        out = r.export_report({"findings": []}, tmp_path / "report.json")
        assert out.exists()
        assert out.suffix == ".json"

    def test_exports_markdown(self, tmp_path):
        r = ComplianceReporter()
        out = r.export_report({"findings": []}, tmp_path / "report.md", format="markdown")
        assert out.exists()

    def test_creates_parent_dirs(self, tmp_path):
        r = ComplianceReporter()
        out = r.export_report({"findings": []}, tmp_path / "sub" / "dir" / "report.json")
        assert out.exists()


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.compliance_reports import __all__ as exported

        assert "ComplianceReporter" in exported
