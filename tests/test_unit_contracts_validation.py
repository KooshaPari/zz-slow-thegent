"""Unit tests for thegent.contracts.validation -- validate_csm, ensure_valid_csm."""

import pytest

from tests.conftest_factories import make_csm
from thegent.contracts.validation import (
    InvariantViolation,
    SemanticValidationError,
    ensure_valid_csm,
    validate_csm,
)


@pytest.mark.unit
class TestValidateCSM:
    """Tests for validate_csm()."""

    def test_valid_completed_csm(self) -> None:
        # @trace FR-CTR-011
        csm = make_csm(status="COMPLETED", progress=1.0, summary="done")
        issues = validate_csm(csm)
        assert issues == []

    def test_completed_low_progress_violation(self) -> None:
        # @trace FR-CTR-011
        csm = make_csm(status="COMPLETED", progress=0.5, summary="done")
        issues = validate_csm(csm)
        assert any("progress" in i.lower() for i in issues)

    def test_pending_nonzero_progress_violation(self) -> None:
        # @trace FR-CTR-011
        csm = make_csm(status="PENDING", progress=0.5)
        issues = validate_csm(csm)
        assert any("pending" in i.lower() for i in issues)

    def test_pending_zero_progress_valid(self) -> None:
        # @trace FR-CTR-011
        csm = make_csm(status="PENDING", progress=0.0)
        issues = validate_csm(csm)
        assert not any("pending" in i.lower() for i in issues)

    def test_in_progress_progress_at_one_violation(self) -> None:
        # @trace FR-CTR-011
        csm = make_csm(status="IN_PROGRESS", progress=1.0, summary="still going")
        issues = validate_csm(csm)
        assert any("in_progress" in i.lower() for i in issues)

    def test_in_progress_valid_range(self) -> None:
        # @trace FR-CTR-011
        csm = make_csm(status="IN_PROGRESS", progress=0.5)
        issues = validate_csm(csm)
        assert not any("in_progress" in i.lower() for i in issues)

    def test_completed_empty_summary_violation(self) -> None:
        # @trace FR-CTR-011
        csm = make_csm(status="COMPLETED", progress=1.0, summary="")
        issues = validate_csm(csm)
        assert any("summary" in i.lower() for i in issues)

    def test_failed_no_evidence_violation(self) -> None:
        # @trace FR-CTR-011
        csm = make_csm(status="FAILED", progress=0.0)
        issues = validate_csm(csm)
        assert any("failed" in i.lower() for i in issues)

    def test_failed_with_issues_valid(self) -> None:
        # @trace FR-CTR-011
        csm = make_csm(status="FAILED", progress=0.0, issues=["disk full"])
        issues = validate_csm(csm)
        assert not any("failed" in i.lower() and "issues" in i.lower() and "empty" in i.lower() for i in issues)

    def test_reviewer_phase_missing_decision_code(self) -> None:
        # @trace FR-CTR-011
        csm = make_csm(
            status="COMPLETED",
            progress=1.0,
            summary="reviewed",
            phase="REVIEWER",
        )
        issues = validate_csm(csm)
        assert any("reviewer" in i.lower() for i in issues)

    def test_reviewer_phase_with_decision_code_valid(self) -> None:
        # @trace FR-CTR-011
        csm = make_csm(
            status="COMPLETED",
            progress=1.0,
            summary="reviewed",
            phase="REVIEWER",
            decision_reason_code="APPROVED",
        )
        issues = validate_csm(csm)
        assert not any("reviewer" in i.lower() for i in issues)

    def test_planner_completed_empty_objective(self) -> None:
        # @trace FR-CTR-011
        csm = make_csm(
            status="COMPLETED",
            progress=1.0,
            summary="planned",
            phase="PLANNER",
            objective="",
        )
        issues = validate_csm(csm)
        assert any("planner" in i.lower() and "objective" in i.lower() for i in issues)


@pytest.mark.unit
class TestEnsureValidCSM:
    """Tests for ensure_valid_csm()."""

    def test_valid_csm_no_exception(self) -> None:
        # @trace FR-CTR-011
        csm = make_csm(status="COMPLETED", progress=1.0, summary="done")
        ensure_valid_csm(csm)

    def test_invalid_csm_raises_invariant_violation(self) -> None:
        # @trace FR-CTR-011
        csm = make_csm(status="COMPLETED", progress=0.0, summary="")
        with pytest.raises(InvariantViolation):
            ensure_valid_csm(csm)

    def test_invariant_violation_is_semantic_error(self) -> None:
        # @trace FR-CTR-011
        assert issubclass(InvariantViolation, SemanticValidationError)
