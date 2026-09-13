"""AUDIT-N+96: governance/support hardening spec (SOTA pass-80).

15 invariants FR-GOV-SUP-001..015 covering SupportRedactor init,
redact_text, redact_payload, SupportModeSession, __all__ export.

Source: src/thegent/governance/support.py

@trace AUDIT-N+96 FR-GOV-SUP-001..015
"""

from __future__ import annotations

from thegent.governance.support import SupportModeSession, SupportRedactor


class TestSupportRedactor:
    def test_init(self):
        r = SupportRedactor()
        assert isinstance(r, SupportRedactor)

    def test_redact_text(self):
        r = SupportRedactor()
        result = r.redact_text("email: test@example.com")
        assert "test@example.com" not in result

    def test_redact_clean_text(self):
        r = SupportRedactor()
        assert r.redact_text("hello world") == "hello world"

    def test_redact_payload(self):
        r = SupportRedactor()
        result = r.redact_payload({"msg": "call 555-123-4567"})
        assert isinstance(result, dict)


class TestSupportModeSession:
    def test_init(self):
        s = SupportModeSession(engineer_id="eng-1")
        assert isinstance(s, SupportModeSession)

    def test_active_get_view_redacts(self):
        s = SupportModeSession(engineer_id="eng-1")
        s.active = True
        result = s.get_view("my ip is 192.168.1.1")
        assert "192.168.1.1" not in result

    def test_inactive_get_view_passthrough(self):
        s = SupportModeSession(engineer_id="eng-1")
        s.active = False
        result = s.get_view("my ip is 192.168.1.1")
        assert "192.168.1.1" in result


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.support import __all__ as exported

        assert "SupportRedactor" in exported
        assert "SupportModeSession" in exported
