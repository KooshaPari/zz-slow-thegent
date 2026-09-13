
import pytest

from thegent.governance.compliance import (
    EU_AI_ACT_PROFILE,
    GDPR_PROFILE,
    US_SEC_PROFILE,
    ComplianceAuditTrail,
    ComplianceEnforcer,
)


@pytest.fixture
def temp_storage(tmp_path):
    return tmp_path / "compliance"


def test_enforcer_mandatory_controls():
    enforcer = ComplianceEnforcer(EU_AI_ACT_PROFILE)
    # By default, automatic checks return True in our placeholder implementation
    assert enforcer.enforce_mandatory("action", {})


def test_gdpr_manual_check():
    enforcer = ComplianceEnforcer(GDPR_PROFILE)
    # DATA-MINIMIZATION is manual
    context = {"manual_verification_DATA-MINIMIZATION": True}
    assert enforcer.check_control("DATA-MINIMIZATION", context)

    context = {"manual_verification_DATA-MINIMIZATION": False}
    assert not enforcer.check_control("DATA-MINIMIZATION", context)


def test_audit_trail_hash_chain(temp_storage):
    audit = ComplianceAuditTrail(temp_storage)

    # Record first action for US-SEC (enables hash chain)
    audit.record_action("action1", {"data": 1}, US_SEC_PROFILE)

    # Record second action
    audit.record_action("action2", {"data": 2}, US_SEC_PROFILE)

    # Read ledger
    with open(temp_storage / "compliance_ledger.jsonl") as f:
        lines = f.readlines()

    assert len(lines) == 2
    import json

    entry1 = json.loads(lines[0])
    entry2 = json.loads(lines[1])

    assert "hash" in entry1
    assert "previous_hash" in entry2
    assert entry2["previous_hash"] == entry1["hash"]


def test_compliance_profile_mandatory_list():
    assert len(EU_AI_ACT_PROFILE.get_mandatory_controls()) == 2
    assert EU_AI_ACT_PROFILE.get_mandatory_controls()[0].id == "HITL-HIGH-RISK"
