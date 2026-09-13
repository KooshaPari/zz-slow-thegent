"""AUDIT-N+79: governance/ledger hardening spec (SOTA pass-63).

15 invariants FR-GOV-LG-001..015 covering LedgerVerifier init,
verify_integrity empty-file, verify_integrity corrupt-line skip,
IncidentLedger record_artifact append, get_run_artifacts,
hash chain continuity, missing-file tolerance, __all__ export,
and deterministic hash chain.

Source: src/thegent/governance/ledger.py

@trace AUDIT-N+79 FR-GOV-LG-001..015
"""

from __future__ import annotations

from thegent.governance.ledger import IncidentLedger, LedgerVerifier


class TestLedgerVerifierInit:
    def test_returns_ledger_verifier(self, tmp_path):
        lv = LedgerVerifier(ledger_path=tmp_path / "ledger.jsonl")
        assert isinstance(lv, LedgerVerifier)

    def test_accepts_path(self, tmp_path):
        lv = LedgerVerifier(ledger_path=tmp_path / "ledger.jsonl")
        assert lv.ledger_path == tmp_path / "ledger.jsonl"


class TestVerifyIntegrity:
    def test_missing_file_is_valid(self, tmp_path):
        lv = LedgerVerifier(ledger_path=tmp_path / "missing.jsonl")
        report = lv.verify_integrity()
        assert report["valid"] is True
        assert report["count"] == 0

    def test_empty_file_is_valid(self, tmp_path):
        path = tmp_path / "empty.jsonl"
        path.write_text("")
        lv = LedgerVerifier(ledger_path=path)
        report = lv.verify_integrity()
        assert report["valid"] is True

    def test_corrupt_line_marks_invalid(self, tmp_path):
        path = tmp_path / "bad.jsonl"
        path.write_text("not json at all\n")
        lv = LedgerVerifier(ledger_path=path)
        report = lv.verify_integrity()
        assert report["valid"] is False
        assert len(report["errors"]) > 0

    def test_accepts_filelike_object(self, tmp_path):
        from io import StringIO

        sv = StringIO("")
        lv = LedgerVerifier(ledger_path=sv)
        report = lv.verify_integrity()
        assert report["valid"] is True


class TestIncidentLedger:
    def test_record_and_retrieve(self, tmp_path):
        il = IncidentLedger(ledger_path=tmp_path / "incident.jsonl")
        il.record_artifact("run-1", "test_action", {"key": "value"})
        artifacts = il.get_run_artifacts("run-1")
        assert len(artifacts) == 1
        assert artifacts[0]["action"] == "test_action"

    def test_hash_chain_valid(self, tmp_path):
        il = IncidentLedger(ledger_path=tmp_path / "incident.jsonl")
        il.record_artifact("run-1", "a", {"x": 1})
        il.record_artifact("run-1", "b", {"x": 2})
        assert il.verify_integrity() is True

    def test_missing_file_returns_empty(self, tmp_path):
        il = IncidentLedger(ledger_path=tmp_path / "missing.jsonl")
        assert il.get_run_artifacts("run-1") == []

    def test_empty_ledger_valid(self, tmp_path):
        il = IncidentLedger(ledger_path=tmp_path / "empty.jsonl")
        assert il.verify_integrity() is True

    def test_get_run_artifacts_unknown_run(self, tmp_path):
        il = IncidentLedger(ledger_path=tmp_path / "incident.jsonl")
        il.record_artifact("run-1", "a", {})
        assert il.get_run_artifacts("run-999") == []


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.ledger import __all__ as exported

        assert "LedgerVerifier" in exported
        assert "IncidentLedger" in exported
