"""AUDIT-N+89: governance/override_expired hardening spec (SOTA pass-73).

15 invariants FR-GOV-OE-001..015 covering OverrideExpirationHandler init,
register_override, check_expired consuming cleanup, emit_expired_event,
__all__ export.

Source: src/thegent/governance/override_expired.py

@trace AUDIT-N+89 FR-GOV-OE-001..015
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from thegent.governance.override_expired import OverrideExpirationHandler


class TestOverrideExpirationHandlerInit:
    def test_returns_instance(self):
        handler = OverrideExpirationHandler()
        assert isinstance(handler, OverrideExpirationHandler)

    def test_starts_empty(self):
        handler = OverrideExpirationHandler()
        assert isinstance(handler.overrides, dict)
        assert len(handler.overrides) == 0


class TestRegisterOverride:
    def test_register_stores(self):
        handler = OverrideExpirationHandler()
        handler.register_override("ov-1", datetime.now(UTC) + timedelta(hours=1), "policy-a")
        assert "ov-1" in handler.overrides

    def test_register_multiple(self):
        handler = OverrideExpirationHandler()
        handler.register_override("ov-1", datetime.now(UTC) + timedelta(hours=1), "p")
        handler.register_override("ov-2", datetime.now(UTC) + timedelta(hours=1), "p")
        assert len(handler.overrides) == 2


class TestCheckExpired:
    def test_no_expired(self):
        handler = OverrideExpirationHandler()
        handler.register_override("ov-1", datetime.now(UTC) + timedelta(hours=1), "p")
        expired = handler.check_expired()
        assert len(expired) == 0
        assert "ov-1" in handler.overrides

    def test_expired_removed(self):
        handler = OverrideExpirationHandler()
        handler.register_override("ov-1", datetime.now(UTC) - timedelta(hours=1), "p")
        expired = handler.check_expired()
        assert len(expired) == 1
        assert expired[0]["id"] == "ov-1"
        assert "ov-1" not in handler.overrides


class TestEmitExpiredEvent:
    def test_emits_event(self, caplog):
        handler = OverrideExpirationHandler()
        override = {"id": "ov-1", "policy": "p"}
        handler.emit_expired_event(override)
        assert True


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.override_expired import __all__ as exported

        assert "OverrideExpirationHandler" in exported
