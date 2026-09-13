import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path("src").resolve()))

from thegent.contracts.csm.v1 import CanonicalStructuredMessage, CSMPhase, CSMStatus
from thegent.contracts.validation import validate_csm


def test_validation_layer():
    # 1. Test Workload Consistency
    csm = CanonicalStructuredMessage(
        status=CSMStatus.COMPLETED,
        progress=1.0,
        summary="Done",
        actions_pending=["some task"],
    )
    issues = validate_csm(csm)
    assert any("actions_pending" in i for i in issues)

    # 2. Test File Integrity vs Actions
    csm = CanonicalStructuredMessage(
        status=CSMStatus.IN_PROGRESS,
        progress=0.5,
        files_modified=["src/app.py"],
        actions_completed=[],
    )
    issues = validate_csm(csm)
    assert any("actions_completed" in i for i in issues)

    # 3. Test Intelligence & Review (Warnings vs Confidence)
    csm = CanonicalStructuredMessage(
        status=CSMStatus.IN_PROGRESS,
        progress=0.5,
        warnings=["Risk of timeout"],
        confidence_level=1.0,
    )
    issues = validate_csm(csm)
    assert any("Confidence level is 1.0 despite active warnings" in i for i in issues)

    # 4. Test Governance: Rollback Plan
    csm = CanonicalStructuredMessage(
        status=CSMStatus.IN_PROGRESS,
        progress=0.5,
        files_created=["new_file.txt"],
        actions_completed=["created file"],
        rollback_plan="",
    )
    issues = validate_csm(csm)
    assert any("rollback_plan" in i for i in issues)

    # 5. Test Phase-specific: REVIEWER
    csm = CanonicalStructuredMessage(
        phase=CSMPhase.REVIEWER,
        status=CSMStatus.COMPLETED,
        progress=1.0,
        summary="Approved",
        decision_reason_code="",
    )
    issues = validate_csm(csm)
    assert any("decision_reason_code" in i for i in issues)

    # 6. Test Phase-specific: PLANNER
    csm = CanonicalStructuredMessage(
        phase=CSMPhase.PLANNER,
        status=CSMStatus.COMPLETED,
        progress=1.0,
        objective="Plan stuff",
        next_steps=[],
    )
    issues = validate_csm(csm)
    assert any("next_steps" in i for i in issues)

    # 7. Test Phase-specific: OPERATOR
    csm = CanonicalStructuredMessage(
        phase=CSMPhase.OPERATOR,
        status=CSMStatus.COMPLETED,
        progress=1.0,
        summary="Implemented",
        files_modified=["src/api.py"],
        test_results="",
    )
    issues = validate_csm(csm)
    assert any("test_results" in i for i in issues)


if __name__ == "__main__":
    test_validation_layer()
