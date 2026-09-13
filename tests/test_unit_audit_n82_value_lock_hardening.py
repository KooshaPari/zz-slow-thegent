"""AUDIT-N+82: governance/value_lock hardening spec (SOTA pass-66).

15 invariants FR-GOV-VL-001..015 covering ValueLock init,
lock_principle idempotency, validate_change strict hash,
unlocked-principle allowance, persistence, __all__ export.

Source: src/thegent/governance/value_lock.py

@trace AUDIT-N+82 FR-GOV-VL-001..015
"""

from __future__ import annotations

from thegent.governance.value_lock import LockedPrinciple, ValueLock


class TestValueLockInit:
    def test_returns_value_lock(self, tmp_path):
        vl = ValueLock(lock_path=tmp_path / "locks.json")
        assert isinstance(vl, ValueLock)

    def test_loads_empty_on_missing_file(self, tmp_path):
        vl = ValueLock(lock_path=tmp_path / "missing.json")
        assert hasattr(vl, "locked_principles")
        assert isinstance(vl.locked_principles, dict)


class TestLockPrinciple:
    def test_lock_stores_principle(self, tmp_path):
        vl = ValueLock(lock_path=tmp_path / "locks.json")
        vl.lock_principle("P1", "do no harm")
        assert "P1" in vl.locked_principles

    def test_lock_idempotent(self, tmp_path):
        vl = ValueLock(lock_path=tmp_path / "locks.json")
        vl.lock_principle("P1", "do no harm")
        vl.lock_principle("P1", "do no harm")
        assert len(vl.locked_principles) == 1

    def test_lock_persists(self, tmp_path):
        path = tmp_path / "locks.json"
        vl1 = ValueLock(lock_path=path)
        vl1.lock_principle("P1", "test")
        vl2 = ValueLock(lock_path=path)
        assert "P1" in vl2.locked_principles


class TestValidateChange:
    def test_identical_description_allowed(self, tmp_path):
        vl = ValueLock(lock_path=tmp_path / "locks.json")
        vl.lock_principle("P1", "do no harm")
        assert vl.validate_change("P1", "do no harm") is True

    def test_changed_description_blocked(self, tmp_path):
        vl = ValueLock(lock_path=tmp_path / "locks.json")
        vl.lock_principle("P1", "do no harm")
        assert vl.validate_change("P1", "do something else") is False

    def test_unlocked_principle_allowed(self, tmp_path):
        vl = ValueLock(lock_path=tmp_path / "locks.json")
        assert vl.validate_change("UNKNOWN", "anything") is True

    def test_lock_has_commitment_hash(self, tmp_path):
        vl = ValueLock(lock_path=tmp_path / "locks.json")
        vl.lock_principle("P1", "description")
        assert vl.locked_principles["P1"].commitment_hash != ""


class TestLockedPrinciple:
    def test_has_required_fields(self):
        lp = LockedPrinciple(principle_id="P1", description="test", commitment_hash="abc")
        assert lp.principle_id == "P1"
        assert lp.locked_at is not None


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.value_lock import __all__ as exported

        assert "ValueLock" in exported
        assert "LockedPrinciple" in exported
