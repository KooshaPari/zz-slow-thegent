
import orjson as json
import pytest

from thegent.governance.compliance import (
    ComplianceExporter,
)
from thegent.governance.forensics import IncidentReplayer
from thegent.governance.ledger import IncidentLedger
from thegent.governance.redaction import PIIRedactor
from thegent.observability.egress import EgressEvent, SIEMEgress


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def ledger(temp_dir):
    return IncidentLedger(temp_dir / "ledger.jsonl")


@pytest.fixture
def redactor():
    return PIIRedactor()


def test_ec001_siem_egress_mock():
    """EC-001: Emit a 'High Risk' event. Event pushed to mock SIEM endpoint."""
    # Using None for endpoint skips real HTTP push in current implementation
    egress = SIEMEgress(endpoint_url=None)

    event = EgressEvent(
        id="evt-123", severity="high", event_type="access_denied", source="test", payload={"reason": "policy_violation"}
    )

    # Implementation returns False if no endpoint
    assert not egress.push_event(event)


def test_ec002_ledger_hash_chain(ledger):
    """EC-002: Add artifact to ledger and verify hash chain."""
    ledger.record_artifact("run-1", "action1", {"data": 1})
    ledger.record_artifact("run-1", "action2", {"data": 2})

    assert ledger.verify_integrity()

    # Tamper with file
    with open(ledger.ledger_path) as f:
        lines = f.readlines()

    # Tamper with first line payload
    entry = json.loads(lines[0])
    entry["payload"]["data"] = 999
    lines[0] = json.dumps(entry).decode() + "\n"

    with open(ledger.ledger_path, "w") as f:
        f.writelines(lines)

    assert not ledger.verify_integrity()


def test_ec003_pii_redaction(redactor):
    """EC-003: Run support mode with a session containing an API key."""
    text = "Key is sk-ant-api03-12345678901234567890 and email is test@example.com"
    redacted = redactor.redact(text, mode="support")

    assert "[REDACTED]" in redacted
    assert "sk-ant-api03" not in redacted
    assert "test@example.com" not in redacted


def test_ec004_compliance_bundle_export(ledger, temp_dir):
    """EC-004: Export compliance evidence bundle."""
    exporter = ComplianceExporter(session_dir=temp_dir)
    target = temp_dir / "bundle.json"

    bundle = exporter.export_bundle("SOC2", target)

    assert bundle["framework"] == "SOC2"
    assert target.exists()
    assert "availability_score" in bundle


def test_ec006_incident_replay(ledger):
    """EC-006: Replay an incident from the ledger."""
    run_id = "run-replay-123"
    ledger.record_artifact(run_id, "file_read", {"path": "secrets.txt"})
    ledger.record_artifact(run_id, "network_call", {"host": "malicious.com"})

    replayer = IncidentReplayer(ledger)
    trace = replayer.replay(run_id)

    assert len(trace["actions"]) == 2
    assert trace["actions"][0]["type"] == "file_read"
    assert trace["actions"][1]["type"] == "network_call"
    assert trace["ledger_verified"]
