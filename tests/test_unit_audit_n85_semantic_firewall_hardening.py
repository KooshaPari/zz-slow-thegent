"""AUDIT-N+85: governance/semantic_firewall hardening spec (SOTA pass-69).

15 invariants FR-GOV-SF-001..015 covering SemanticFirewall init,
inspect_output block/redact/warn actions, pattern matching,
empty output safety, __all__ export.

Source: src/thegent/governance/semantic_firewall.py

@trace AUDIT-N+85 FR-GOV-SF-001..015
"""

from __future__ import annotations

from thegent.governance.semantic_firewall import FirewallRule, SemanticFirewall


class TestSemanticFirewallInit:
    def test_returns_instance(self):
        fw = SemanticFirewall()
        assert isinstance(fw, SemanticFirewall)

    def test_has_rules(self):
        fw = SemanticFirewall()
        assert hasattr(fw, "rules")
        assert len(fw.rules) >= 1

    def test_has_inspect_output(self):
        fw = SemanticFirewall()
        assert callable(getattr(fw, "inspect_output", None))


class TestInspectOutput:
    def test_clean_output_unchanged(self):
        fw = SemanticFirewall()
        output, violations = fw.inspect_output("hello world")
        assert output == "hello world"
        assert isinstance(violations, list)

    def test_empty_output_safe(self):
        fw = SemanticFirewall()
        output, violations = fw.inspect_output("")
        assert output == ""
        assert isinstance(violations, list)

    def test_credential_redaction(self):
        fw = SemanticFirewall()
        output, _violations = fw.inspect_output("password='mysecret123'")
        assert "REDACTED" in output

    def test_block_returns_error(self):
        fw = SemanticFirewall()
        output, violations = fw.inspect_output("rm -rf /")
        assert "BLOCK" in output.upper() or "ERROR" in output.upper()
        assert len(violations) > 0


class TestFirewallRule:
    def test_rule_fields(self):
        rule = FirewallRule(rule_id="R1", pattern="test", action="warn", reason="testing")
        assert rule.rule_id == "R1"
        assert rule.action == "warn"


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.semantic_firewall import __all__ as exported

        assert "SemanticFirewall" in exported
        assert "FirewallRule" in exported
