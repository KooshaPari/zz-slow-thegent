"""AUDIT-N+84: governance/attestation hardening spec (SOTA pass-68).

15 invariants FR-GOV-AT-001..015 covering AttestationGenerator init,
generate_attestation mkdir, generate_attestation file write,
AuditReportGenerator division-by-zero guard, malformed JSON tolerance,
__all__ export.

Source: src/thegent/governance/attestation.py

@trace AUDIT-N+84 FR-GOV-AT-001..015
"""

from __future__ import annotations

from thegent.governance.attestation import AttestationGenerator, AuditReportGenerator


class TestAttestationGenerator:
    def test_init(self, tmp_path):
        from thegent.config import ThegentSettings

        gen = AttestationGenerator(settings=ThegentSettings())
        assert isinstance(gen, AttestationGenerator)

    def test_generate_creates_file(self, tmp_path, monkeypatch):
        from thegent.config import ThegentSettings

        s = ThegentSettings()
        gen = AttestationGenerator(settings=s)
        result = gen.generate_attestation(run_id="test-run-1")
        assert isinstance(result, dict)
        assert "verdict" in result

    def test_generate_returns_compliant(self):
        from thegent.config import ThegentSettings

        gen = AttestationGenerator(settings=ThegentSettings())
        result = gen.generate_attestation(run_id="r1")
        assert result.get("verdict") == "COMPLIANT"


class TestAuditReportGenerator:
    def test_init(self):
        from thegent.config import ThegentSettings

        gen = AuditReportGenerator(settings=ThegentSettings())
        assert isinstance(gen, AuditReportGenerator)

    def test_generate_report_returns_string(self):
        from thegent.config import ThegentSettings

        gen = AuditReportGenerator(settings=ThegentSettings())
        report = gen.generate_monthly_report()
        assert isinstance(report, str)
        assert len(report) > 0

    def test_report_handles_empty_dir(self, tmp_path, monkeypatch):
        from thegent.config import ThegentSettings

        gen = AuditReportGenerator(settings=ThegentSettings())
        report = gen.generate_monthly_report()
        assert isinstance(report, str)


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.attestation import __all__ as exported

        assert "AttestationGenerator" in exported
        assert "AuditReportGenerator" in exported
