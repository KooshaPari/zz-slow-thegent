"""Integration tests for governance modules (semantic_firewall, redaction, costs, tee_check, policy).

Exercises the real implementations to validate behavior end-to-end
with actual data, no mocks.

# @trace GOV-INTEGRATION FR-GOV-001..015
"""

from __future__ import annotations

import pytest

from thegent.governance.costs import CostTracker
from thegent.governance.policy import PolicyManager
from thegent.governance.redaction import PIIRedactor
from thegent.governance.semantic_firewall import SemanticFirewall
from thegent.governance.tee_check import TEEAttestation, TEEChecker, TEEType

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# SemanticFirewall — inspect_output
# ---------------------------------------------------------------------------


class TestSemanticFirewallIntegration:
    """End-to-end tests for SemanticFirewall.inspect_output."""

    def test_clean_output_passes(self):
        """Clean output should pass without redactions."""
        fw = SemanticFirewall()
        result, matches = fw.inspect_output("Hello world, all good!")
        assert result == "Hello world, all good!"
        assert matches == []

    def test_password_pattern_redacted(self):
        """Output with password= pattern should be redacted."""
        fw = SemanticFirewall()
        result, matches = fw.inspect_output("password = 'mysecret123'")
        assert len(matches) > 0
        assert "REDACTED" in result
        assert "mysecret123" not in result

    def test_rm_rf_blocked(self):
        """rm -rf / should be blocked."""
        fw = SemanticFirewall()
        result, matches = fw.inspect_output("Run this: rm -rf /important")
        assert len(matches) > 0
        assert "BLOCK" in result.upper()

    def test_cannot_perform_warned(self):
        """Refusal pattern should generate a warning."""
        fw = SemanticFirewall()
        _result, matches = fw.inspect_output("I cannot perform this action")
        assert len(matches) > 0

    def test_empty_input(self):
        """Empty string should return empty with no matches."""
        fw = SemanticFirewall()
        result, matches = fw.inspect_output("")
        assert result == ""
        assert matches == []

    def test_multiple_rules_matched(self):
        """Multiple rule matches: redact + warn in one output (no block to short-circuit)."""
        fw = SemanticFirewall()
        text = "password = 'secret' and I cannot perform this action"
        _result, matches = fw.inspect_output(text)
        assert len(matches) >= 2


# ---------------------------------------------------------------------------
# PIIRedactor — redact, contains_pii
# ---------------------------------------------------------------------------


class TestPIIRedactorIntegration:
    """End-to-end tests for PIIRedactor redaction."""

    def test_email_redacted(self):
        """Email addresses should be redacted."""
        redactor = PIIRedactor()
        text = "Contact user@example.com for details"
        result = redactor.redact(text)
        assert "user@example.com" not in result
        assert redactor.contains_pii(text)

    def test_phone_redacted(self):
        """Phone numbers should be redacted."""
        redactor = PIIRedactor()
        text = "Call me at 555-123-4567"
        result = redactor.redact(text)
        assert "555-123-4567" not in result

    def test_ssn_redacted(self):
        """SSN patterns should be redacted."""
        redactor = PIIRedactor()
        text = "My SSN is 123-45-6789"
        result = redactor.redact(text)
        assert "123-45-6789" not in result

    def test_api_key_redacted(self):
        """API key patterns should be redacted."""
        redactor = PIIRedactor()
        text = "Use key sk-abcdefghijklmnopqrstuvwxyz for auth"
        result = redactor.redact(text)
        assert "sk-abcdefghijklmnopqrstuvwxyz" not in result

    def test_clean_text_unchanged(self):
        """Text without PII should pass through unchanged."""
        redactor = PIIRedactor()
        text = "The quick brown fox jumps over the lazy dog"
        result = redactor.redact(text)
        assert result == text

    def test_contains_pii_false_clean(self):
        """contains_pii returns False for clean text."""
        redactor = PIIRedactor()
        assert not redactor.contains_pii("No PII here")

    def test_custom_pattern(self):
        """Custom patterns should be supported."""
        redactor = PIIRedactor(custom_patterns={"internal_id": r"INT-\d{6}"})
        text = "User INT-123456 has access"
        assert redactor.contains_pii(text)
        result = redactor.redact(text)
        assert "INT-123456" not in result

    def test_multiple_pii_types(self):
        """Multiple PII types in one text should all be caught."""
        redactor = PIIRedactor()
        text = "Email: a@b.com, phone: 555-123-4567, SSN: 123-45-6789"
        result = redactor.redact(text)
        assert "a@b.com" not in result
        assert "555-123-4567" not in result
        assert "123-45-6789" not in result


# ---------------------------------------------------------------------------
# CostTracker — lifecycle
# ---------------------------------------------------------------------------


class TestCostTrackerIntegration:
    """End-to-end tests for CostTracker session lifecycle."""

    def test_start_and_record(self):
        """start_session + record_cost should accumulate correctly."""
        tracker = CostTracker()
        tracker.start_session("test-run-1")
        tracker.record_cost("test-run-1", cost=0.05)
        tracker.record_cost("test-run-1", cost=0.03)
        cost = tracker.get_session_cost("test-run-1")
        assert cost == pytest.approx(0.08)

    def test_budget_check(self):
        """is_within_budget should respect budget limits."""
        tracker = CostTracker()
        tracker.start_session("budget-test")
        tracker.record_cost("budget-test", cost=0.05)
        assert tracker.is_within_budget("budget-test", budget=0.10)
        tracker.record_cost("budget-test", cost=0.06)
        assert not tracker.is_within_budget("budget-test", budget=0.10)

    def test_unknown_session_returns_zero(self):
        """Unknown session should return zero cost."""
        tracker = CostTracker()
        assert tracker.get_session_cost("nonexistent") == 0.0

    def test_multiple_costs_tracked(self):
        """Multiple costs should be summed correctly."""
        tracker = CostTracker()
        tracker.start_session("multi-model")
        tracker.record_cost("multi-model", cost=0.10)
        tracker.record_cost("multi-model", cost=0.05)
        tracker.record_cost("multi-model", cost=0.02)
        cost = tracker.get_session_cost("multi-model")
        assert cost == pytest.approx(0.17)


# ---------------------------------------------------------------------------
# TEEChecker — check, enforce_tee
# ---------------------------------------------------------------------------


class TestTEECheckerIntegration:
    """End-to-end tests for TEEChecker attestation flow."""

    def test_mock_mode_returns_attested(self):
        """Mock mode should return an attested TEEAttestation."""
        checker = TEEChecker(mock_mode=True)
        attestation = checker.check()
        assert attestation.is_attested is True
        assert attestation.tee_type == TEEType.MOCK
        assert attestation.provider_id == "mock-tee-provider"
        assert attestation.measurement_hash is not None
        assert attestation.firmware_version is not None

    def test_mock_mode_measurement_hash_format(self):
        """Mock measurement hash should follow sha256 format."""
        checker = TEEChecker(mock_mode=True)
        attestation = checker.check()
        assert attestation.measurement_hash.startswith("sha256:")

    def test_enforce_tee_passes_in_mock(self):
        """enforce_tee should not raise in mock mode."""
        checker = TEEChecker(mock_mode=True)
        checker.enforce_tee()  # should not raise

    def test_non_mock_returns_non_attested_on_desktop(self):
        """Non-mock mode on a desktop should return non-attested (no /dev/nsm)."""
        import os

        if os.path.exists("/dev/nsm"):
            pytest.skip("Running inside AWS Nitro — attestation expected")
        checker = TEEChecker(mock_mode=False)
        attestation = checker.check()
        # Desktop without TEE hardware: not attested
        assert attestation.is_attested is False
        assert attestation.tee_type == TEEType.NONE

    def test_attestation_dataclass_fields(self):
        """TEEAttestation should have all expected fields."""
        att = TEEAttestation(
            tee_type=TEEType.MOCK,
            is_attested=True,
            provider_id="test",
            measurement_hash="sha256:abc",
            firmware_version="1.0",
        )
        assert att.tee_type == TEEType.MOCK
        assert att.is_attested is True
        assert att.provider_id == "test"
        assert att.measurement_hash == "sha256:abc"
        assert att.firmware_version == "1.0"

    def test_tee_type_enum_completeness(self):
        """TEEType enum should have all expected variants."""
        expected = {"none", "aws_nitro", "intel_sgx", "amd_sev", "azure_tdx", "mock"}
        actual = {t.value for t in TEEType}
        assert expected == actual


# ---------------------------------------------------------------------------
# PolicyManager — get_policy, update
# ---------------------------------------------------------------------------


class TestPolicyManagerIntegration:
    """End-to-end tests for PolicyManager lifecycle."""

    def test_empty_policy_returns_none(self):
        """Empty manager should return None for unknown keys."""
        pm = PolicyManager()
        assert pm.get_policy("nonexistent") is None

    def test_initial_policies(self):
        """Initial policies should be retrievable."""
        pm = PolicyManager(initial_policies={"max_tokens": 4096, "timeout": 30})
        assert pm.get_policy("max_tokens") == 4096
        assert pm.get_policy("timeout") == 30

    def test_update_adds_policies(self):
        """update() should add new policies."""
        pm = PolicyManager()
        pm.update({"enable_cache": True, "retry_count": 3})
        assert pm.get_policy("enable_cache") is True
        assert pm.get_policy("retry_count") == 3

    def test_update_overrides_existing(self):
        """update() should override existing policies."""
        pm = PolicyManager(initial_policies={"max_tokens": 2048})
        pm.update({"max_tokens": 8192})
        assert pm.get_policy("max_tokens") == 8192

    def test_update_merges(self):
        """update() should merge with existing policies, not replace."""
        pm = PolicyManager(initial_policies={"a": 1, "b": 2})
        pm.update({"b": 99, "c": 3})
        assert pm.get_policy("a") == 1
        assert pm.get_policy("b") == 99
        assert pm.get_policy("c") == 3
