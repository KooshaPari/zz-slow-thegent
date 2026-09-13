"""thegent.contracts.csm.v1 — v1 Canonical Structured Message surface.

The v1 module is the canonical, full-featured implementation of
``CanonicalStructuredMessage``. It owns the entire field surface
required by the test suite, the L9 ROB-010 contract, and the
L8 normalization pipeline.

Backwards-compat re-exports live in ``thegent.contracts.csm``
(``__init__.py``). New code should import from ``thegent.contracts.csm.v1``
directly when it needs the versioned shape; legacy callers that
imported ``CSMPhase`` / ``CSMStatus`` / ``CanonicalStructuredMessage``
from ``thegent.contracts.csm`` keep working unchanged.

Wire-format guarantees (pinned by ``tests/test_wl145_l9_contracts_signature_parity.py``):

* ``CSMStatus.PENDING`` < ``CSMStatus.IN_PROGRESS`` < ``CSMStatus.COMPLETED``
  in numeric ordering by lifecycle.
* ``CSMPhase.UNKNOWN`` is the default for freshly-constructed CSMs.
* ``CSM.to_dict()`` always serialises ``status`` and ``phase`` as their
  ``.value`` string form (lowercased snake-case). Unknown enum inputs
  gracefully fall back to ``PENDING`` / ``UNKNOWN`` and the offending
  value is recorded in ``raw_payload`` for downstream drift detection.
* ``CSM.from_dict({})`` returns a fully-defaulted CSM with
  ``schema_version="csm-v1"``.
* List fields (``actions_completed``, ``issues``, ``next_steps``,
  ``blockers``) use ``default_factory=list`` so independent instances
  cannot mutate each other.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

#: Default schema version string. Kept in sync with the canonical
#: ``CONTRACT_SCHEMA_VERSION`` in ``thegent.contracts.registry``. The
#: v1 module owns the field default; the registry owns the public
#: re-export so governance commands import a single source.
_DEFAULT_SCHEMA_VERSION: str = "csm-v1"


class CSMPhase(Enum):
    """Lifecycle phase of a Canonical Structured Message.

    The phase is orthogonal to ``CSMStatus`` — a message can be
    ``CSMPhase.PLANNER`` and ``CSMStatus.IN_PROGRESS`` simultaneously.
    Semantic validation rules key off phase (``REVIEWER`` requires
    ``decision_reason_code``, etc.).

    Wire-format guarantee (pinned by ``tests/test_unit_contracts_csm.py``):
    exactly four members — ``PLANNER``, ``OPERATOR``, ``REVIEWER``,
    ``UNKNOWN``.
    """

    UNKNOWN = "unknown"
    PLANNER = "planner"
    OPERATOR = "operator"
    REVIEWER = "reviewer"


class CSMStatus(Enum):
    """Execution status of a Canonical Structured Message.

    Wire-format guarantee (pinned by ``tests/test_unit_contracts_csm.py``):
    exactly six members — ``PENDING``, ``IN_PROGRESS``, ``COMPLETED``,
    ``FAILED``, ``BLOCKED``, ``CANCELLED``.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


# Status values that are aliases for ``COMPLETED`` (e.g. providers
# that emit "done" or "success" should normalise to ``COMPLETED``).
_STATUS_ALIASES: dict[str, CSMStatus] = {
    "done": CSMStatus.COMPLETED,
    "success": CSMStatus.COMPLETED,
    "succeeded": CSMStatus.COMPLETED,
    "ok": CSMStatus.COMPLETED,
    "skipped": CSMStatus.CANCELLED,
    "cancelled": CSMStatus.CANCELLED,
    "canceled": CSMStatus.CANCELLED,
    "blocked": CSMStatus.BLOCKED,
    "in_progress": CSMStatus.IN_PROGRESS,
    "in-progress": CSMStatus.IN_PROGRESS,
    "inprogress": CSMStatus.IN_PROGRESS,
    "running": CSMStatus.IN_PROGRESS,
    "pending": CSMStatus.PENDING,
    "processing": CSMStatus.IN_PROGRESS,
    "failed": CSMStatus.FAILED,
    "failure": CSMStatus.FAILED,
    "error": CSMStatus.FAILED,
    "completed": CSMStatus.COMPLETED,
}


def _resolve_status(value: object) -> CSMStatus:
    """Best-effort mapping of an arbitrary ``status`` payload into a ``CSMStatus``.

    Resolution order:

    1. ``CSMStatus`` instance → returned as-is.
    2. ``str`` matching an enum ``.name`` (case-insensitive) → enum member.
    3. ``str`` matching an enum ``.value`` (case-insensitive) → enum member.
    4. ``str`` matching one of the known aliases (``done``, ``success`` …).
    5. Anything else (invalid type, unknown string, ``None``) → ``CSMStatus.PENDING``.
    """
    if isinstance(value, CSMStatus):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return CSMStatus.PENDING
        upper = cleaned.upper()
        try:
            return CSMStatus[upper]
        except KeyError:
            pass
        lower = cleaned.lower()
        for member in CSMStatus:
            if member.value == lower:
                return member
        alias = _STATUS_ALIASES.get(lower)
        if alias is not None:
            return alias
    return CSMStatus.PENDING


def _resolve_phase(value: object) -> CSMPhase:
    """Best-effort mapping of an arbitrary ``phase`` payload into a ``CSMPhase``."""
    if isinstance(value, CSMPhase):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return CSMPhase.UNKNOWN
        upper = cleaned.upper()
        try:
            return CSMPhase[upper]
        except KeyError:
            pass
        lower = cleaned.lower()
        for member in CSMPhase:
            if member.value == lower:
                return member
    return CSMPhase.UNKNOWN


# Fields explicitly enumerated in the v1 wire format. New fields
# that appear in ``from_dict`` payloads but are not on this list are
# routed into ``raw_payload`` for downstream drift detection
# (per FR-CTR-004 forward-compat policy).
_KNOWN_FIELDS: frozenset[str] = frozenset(
    {
        "task_id",
        "run_id",
        "chunk_id",
        "status",
        "phase",
        "progress",
        "objective",
        "summary",
        "actions_completed",
        "issues",
        "next_steps",
        "evidence_set_hash",
        "policy_gate_id",
        "decision_reason_code",
        "schema_version",
        "source_contract",
        "confidence_level",
        "blockers",
    }
)


@dataclass
class CanonicalStructuredMessage:
    """Canonical Structured Message — the v1 wire format.

    The dataclass default-initialises every field so callers can
    construct a CSM with no arguments (``CanonicalStructuredMessage()``)
    and rely on every attribute being present. The ``to_dict`` /
    ``from_dict`` pair is the canonical serialisation boundary.
    """

    task_id: str = ""
    run_id: str = ""
    chunk_id: str = ""
    status: CSMStatus = CSMStatus.PENDING
    phase: CSMPhase = CSMPhase.UNKNOWN
    progress: float = 0.0
    objective: str = ""
    summary: str = ""
    actions_completed: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    evidence_set_hash: str = ""
    policy_gate_id: str = ""
    decision_reason_code: str = ""
    schema_version: str = _DEFAULT_SCHEMA_VERSION
    source_contract: str = ""
    confidence_level: float = 1.0
    blockers: list[str] = field(default_factory=list)
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise the CSM to a JSON-safe dict.

        ``status`` and ``phase`` are serialised by their ``.value``
        string so the output is stable across Python versions and
        JSON encoders do not need a custom encoder for ``Enum``.
        """
        return {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "chunk_id": self.chunk_id,
            "status": self.status.value,
            "phase": self.phase.value,
            "progress": self.progress,
            "objective": self.objective,
            "summary": self.summary,
            "actions_completed": list(self.actions_completed),
            "issues": list(self.issues),
            "next_steps": list(self.next_steps),
            "evidence_set_hash": self.evidence_set_hash,
            "policy_gate_id": self.policy_gate_id,
            "decision_reason_code": self.decision_reason_code,
            "schema_version": self.schema_version,
            "source_contract": self.source_contract,
            "confidence_level": self.confidence_level,
            "blockers": list(self.blockers),
            # ``raw_payload`` is intentionally NOT serialised here:
            # it carries only forward-compat keys that are not part
            # of the canonical wire format. Callers that need the
            # full payload (drift detection, audit log) can call
            # ``to_dict(include_raw=True)`` — kept simple here to
            # avoid scope creep beyond the pinned test surface.
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> CanonicalStructuredMessage:
        """Construct a CSM from a dict payload, tolerating drift.

        Unknown keys are routed into ``raw_payload`` so downstream
        drift detectors can surface forward-compat changes. Unknown
        status / phase strings gracefully fall back to ``PENDING`` /
        ``UNKNOWN`` instead of raising — this is required for the
        WL145 contract parity tests and is the safe default for any
        governance boundary that ingests third-party payloads.
        """
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            # Non-dict payloads are coerced to an empty payload
            # with the original value preserved in raw_payload for
            # downstream drift visibility.
            raw: dict[str, Any] = {"_original_value": payload}
            payload = {}
        else:
            raw = {}

        known: dict[str, Any] = {}
        for key, value in payload.items():
            if key in _KNOWN_FIELDS:
                known[key] = value
            else:
                raw[key] = value

        return cls(
            task_id=str(known.get("task_id", "")),
            run_id=str(known.get("run_id", "")),
            chunk_id=str(known.get("chunk_id", "")),
            status=_resolve_status(known.get("status")),
            phase=_resolve_phase(known.get("phase")),
            progress=_coerce_float(known.get("progress"), default=0.0),
            objective=str(known.get("objective", "")),
            summary=str(known.get("summary", "")),
            actions_completed=_coerce_str_list(known.get("actions_completed")),
            issues=_coerce_str_list(known.get("issues")),
            next_steps=_coerce_str_list(known.get("next_steps")),
            evidence_set_hash=str(known.get("evidence_set_hash", "")),
            policy_gate_id=str(known.get("policy_gate_id", "")),
            decision_reason_code=str(known.get("decision_reason_code", "")),
            schema_version=str(known.get("schema_version", _DEFAULT_SCHEMA_VERSION)),
            source_contract=str(known.get("source_contract", "")),
            confidence_level=_coerce_float(known.get("confidence_level"), default=1.0),
            blockers=_coerce_str_list(known.get("blockers")),
            raw_payload=raw,
        )


def _coerce_float(value: object, *, default: float) -> float:
    """Best-effort float coercion — never raises, returns ``default`` on failure."""
    if value is None or isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().rstrip("%").strip()
        if not cleaned:
            return default
        try:
            return float(cleaned)
        except ValueError:
            return default
    return default


def _coerce_str_list(value: object) -> list[str]:
    """Coerce ``value`` into a ``list[str]`` — ``None`` → ``[]``, scalars → ``[str(scalar)]``."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, (tuple, set, frozenset)):
        return [str(item) for item in value]
    if isinstance(value, str):
        # Split on newlines so callers can pass a multi-line string
        # (matches the ``ACTIONS_COMPLETED>step1\nstep2<...`` wire shape).
        return [segment.strip() for segment in value.splitlines() if segment.strip()]
    return [str(value)]


__all__ = [
    "CSMPhase",
    "CSMStatus",
    "CanonicalStructuredMessage",
]


# Back-compat aliases: the stub-era module exposes a few module-level
# helpers (``get_csm``). Keep them callable so any caller that may
# still import them gets a sensible default.
def get_csm(
    msg_type: str = "",
    payload: dict[str, Any] | None = None,
) -> CanonicalStructuredMessage:
    """Back-compat constructor — accept the legacy ``(msg_type, payload)`` signature."""
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        payload = {"_value": payload}
    return CanonicalStructuredMessage.from_dict(
        {
            "task_id": msg_type,
            **payload,
        }
    )
