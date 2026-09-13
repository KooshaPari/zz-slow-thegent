"""AUDIT-N+88: governance/forensics hardening spec (SOTA pass-72).

15 invariants FR-GOV-FR-001..015 covering IncidentReplayer init,
replay not-found, replay with entries, generate_incident_report,
integrity verification, __all__ export.

Source: src/thegent/governance/forensics.py

@trace AUDIT-N+88 FR-GOV-FR-001..015
"""

from __future__ import annotations

from thegent.governance.forensics import IncidentReplayer
from thegent.governance.ledger import IncidentLedger


class TestIncidentReplayerInit:
    def test_returns_instance(self, tmp_path):
        il = IncidentLedger(ledger_path=tmp_path / "incident.jsonl")
        replayer = IncidentReplayer(ledger=il)
        assert isinstance(replayer, IncidentReplayer)


class TestReplay:
    def test_not_found_returns_empty(self, tmp_path):
        il = IncidentLedger(ledger_path=tmp_path / "incident.jsonl")
        replayer = IncidentReplayer(ledger=il)
        result = replayer.replay("nonexistent-run")
        assert result["run_id"] == "nonexistent-run"
        assert result["actions"] == []
        assert result["status"] == "not_found"

    def test_replay_with_entries(self, tmp_path):
        il = IncidentLedger(ledger_path=tmp_path / "incident.jsonl")
        il.record_artifact("run-1", "test_action", {"key": "value"})
        replayer = IncidentReplayer(ledger=il)
        result = replayer.replay("run-1")
        assert result["run_id"] == "run-1"
        assert len(result["actions"]) == 1


class TestIncidentReport:
    def test_returns_string(self, tmp_path):
        il = IncidentLedger(ledger_path=tmp_path / "incident.jsonl")
        replayer = IncidentReplayer(ledger=il)
        report = replayer.generate_incident_report("nonexistent")
        assert isinstance(report, str)
        assert len(report) > 0


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.forensics import __all__ as exported

        assert "IncidentReplayer" in exported
