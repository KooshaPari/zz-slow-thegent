"""Unit tests for Phase 15: Enterprise Lifecycle and Compliance."""

import orjson as json

from thegent.contracts.marketplace import PluginContract, PluginVerifier
from thegent.governance.ledger import IncidentLedger
from thegent.governance.support import SupportRedactor


def test_wp_15002_ledger_integrity(tmp_path):
    """WP-15002: Ledger maintains an immutable hash chain."""
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = IncidentLedger(ledger_path)

    # Record some artifacts
    ledger.record_artifact("run-1", "start", {"msg": "hello"})
    ledger.record_artifact("run-1", "output", {"val": 42})

    assert ledger.verify_integrity() is True
    assert len(ledger.get_run_artifacts("run-1")) == 2

    # Simulate tampering: rewrite the file with bad data
    lines = ledger_path.read_text().splitlines()
    bad_line = json.loads(lines[0])
    bad_line["payload"]["msg"] = "tampered"
    ledger_path.write_text(json.dumps(bad_line).decode() + "\n" + lines[1] + "\n")

    # Reload and verify failure
    new_ledger = IncidentLedger(ledger_path)
    assert new_ledger.verify_integrity() is False


def test_wp_15003_plugin_verification():
    """WP-15003: Third-party plugins must have valid signatures."""
    verifier = PluginVerifier()

    valid_contract = PluginContract(
        plugin_id="safe-plugin", version="1.0", author="acme", capabilities=["read_only"], signature="valid_sig_abc123"
    )

    invalid_contract = PluginContract(
        plugin_id="rogue-plugin", version="6.6", author="hacker", capabilities=["all"], signature="unsigned"
    )

    assert verifier.verify_contract(valid_contract) is True
    assert verifier.verify_contract(invalid_contract) is False


def test_wp_15005_redaction():
    """WP-15005: Sensitive data is redacted in support mode."""
    redactor = SupportRedactor()

    raw_text = "Support requested for user bob@example.com using key sk-1234567890abcdefghijklmnop"
    redacted = redactor.redact_text(raw_text)

    assert "bob@example.com" not in redacted
    assert "sk-1234567890" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_API_KEY]" in redacted
