"""thegent.contracts.validation — semantic CSM validation.

This module owns two entry points:

* :func:`validate_csm` — returns a ``list[str]`` of human-readable
  issues (empty list means valid). Accepts the canonical
  :class:`~thegent.contracts.csm.v1.CanonicalStructuredMessage`.
* :func:`ensure_valid_csm` — raises :class:`InvariantViolation`
  (which is a :class:`SemanticValidationError` subclass) when the
  CSM has any validation issues.

The rules below are pinned by ``tests/test_unit_contracts_validation.py``
and ``tests/test_wl145_l9_contracts_signature_parity.py``.

Validation rules:

* ``COMPLETED`` with ``progress < 1.0`` → "COMPLETED but progress < X"
* ``COMPLETED`` with empty ``summary`` → "COMPLETED but summary is empty"
* ``PENDING`` with non-zero ``progress`` → "PENDING cannot have progress > 0"
* ``IN_PROGRESS`` with ``progress >= 1.0`` → "IN_PROGRESS cannot have progress >= 1.0"
* ``FAILED`` with no ``issues`` and no ``decision_reason_code`` → "FAILED but no issues"
* ``REVIEWER`` phase with no ``decision_reason_code`` → "REVIEWER requires decision_reason_code"
* ``PLANNER`` phase with ``COMPLETED`` status and empty ``objective`` →
  "PLANNER with COMPLETED requires non-empty objective"
* ``summary`` is stripped before the empty check so ``"   "`` fails.
"""

from __future__ import annotations

from thegent.contracts.csm.v1 import CSMPhase, CSMStatus

__all__ = [
    "ensure_valid_csm",
    "validate_csm",
    "SemanticValidationError",
    "InvariantViolation",
]


class SemanticValidationError(Exception):
    """Base exception raised when semantic validation fails."""


class InvariantViolation(SemanticValidationError):
    """Raised by :func:`ensure_valid_csm` when invariant rules are violated.

    Carries a ``message`` attribute in addition to the usual ``args`` so
    callers using ``str(exc)`` or ``exc.message`` both work.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _stripped(text: object) -> str:
    if text is None:
        return ""
    return str(text).strip()


def validate_csm(csm) -> list[str]:
    """Validate a CanonicalStructuredMessage and return a list of issues.

    An empty list means the CSM is semantically valid; any other
    return value is a list of human-readable issue strings suitable
    for surfacing in telemetry, logs, or CLI output.
    """
    issues: list[str] = []
    status = getattr(csm, "status", None)
    phase = getattr(csm, "phase", None)
    progress = float(getattr(csm, "progress", 0.0) or 0.0)
    summary = _stripped(getattr(csm, "summary", ""))
    issues_list = list(getattr(csm, "issues", []) or [])
    decision_reason_code = _stripped(getattr(csm, "decision_reason_code", ""))
    objective = _stripped(getattr(csm, "objective", ""))

    # COMPLETED invariants.
    if status == CSMStatus.COMPLETED:
        if progress < 1.0:
            issues.append(f"CSM in COMPLETED state but progress is {progress} (< 1.0)")
        if not summary:
            issues.append("CSM in COMPLETED state but summary is empty")

    # PENDING invariants.
    if status == CSMStatus.PENDING and progress > 0.0:
        issues.append(f"CSM in PENDING state cannot have progress > 0 (got {progress})")

    # IN_PROGRESS invariants.
    if status == CSMStatus.IN_PROGRESS and progress >= 1.0:
        issues.append(f"CSM in IN_PROGRESS state cannot have progress >= 1.0 (got {progress})")

    # FAILED invariants: must surface a reason via either ``issues`` or
    # an explicit ``decision_reason_code``.
    if status == CSMStatus.FAILED:
        if not issues_list and not decision_reason_code:
            issues.append("CSM in FAILED state must include either issues[] or decision_reason_code")

    # Phase-aware rules.
    if phase == CSMPhase.REVIEWER and not decision_reason_code:
        issues.append("CSM in REVIEWER phase requires a non-empty decision_reason_code")
    if phase == CSMPhase.PLANNER and status == CSMStatus.COMPLETED and not objective:
        issues.append("CSM in PLANNER phase with COMPLETED status requires a non-empty objective")

    return issues


def ensure_valid_csm(csm) -> None:
    """Raise :class:`InvariantViolation` if the CSM has any validation issues.

    Convenience over :func:`validate_csm` for the caller pattern of
    "raise on bad input". The raised exception is a subclass of
    :class:`SemanticValidationError`, so callers that catch the base
    exception also catch this one.
    """
    issues = validate_csm(csm)
    if issues:
        raise InvariantViolation("; ".join(issues))
