"""Evidence capture at promotion gates (WP-1005, FR-004).

PromotionGate captures evidence snapshots at orchestration promotion
gates, computes integrity hashes, and maintains an append-only JSONL
audit trail.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(init=False)
class PromotionGate:
    """Gate for evidence-based promotion decisions.

    Manages evidence capture, validation, and integrity verification
    for orchestration promotion gates.
    """

    session_dir: Path
    evidence_dir: Path = field(init=False)
    audit_path: Path = field(init=False)

    def __init__(self, session_dir: Path) -> None:
        self.session_dir = Path(session_dir)
        self.evidence_dir = self.session_dir / "evidence"
        self.audit_path = self.session_dir / "evidence_audit.jsonl"

    def _resolve_phase(self, csm: Any) -> str:
        """Resolve the phase value, preferring .value, falling back to str."""
        return getattr(csm.phase, "value", str(csm.phase))

    def capture_evidence(self, run_id: str, csm: Any) -> str:
        """Capture evidence from a CSM and return its SHA-256 hash.

        Creates the evidence directory, serializes the CSM to JSON,
        writes the evidence file, and appends to the audit trail.
        """
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        phase = self._resolve_phase(csm)
        csm_data = csm.to_dict()
        evidence_path = self.evidence_dir / f"{run_id}_{phase}.json"

        content = json.dumps(csm_data, sort_keys=True)
        evidence_path.write_text(content)

        evidence_hash = hashlib.sha256(content.encode()).hexdigest()

        audit_entry = {
            "run_id": run_id,
            "phase": phase,
            "evidence_hash": evidence_hash,
            "ts": datetime.now(UTC).isoformat(),
            "evidence_path": str(evidence_path),
        }
        with self.audit_path.open("a") as f:
            f.write(json.dumps(audit_entry) + "\n")

        return evidence_hash

    def validate_promotion(self, csm: Any, policy: Any) -> list[str]:
        """Validate whether a CSM can be promoted.

        Checks confidence level against the policy threshold and
        inspects for active blockers.
        """
        issues: list[str] = []

        if csm.confidence_level < policy.min_confidence_threshold:
            issues.append(
                f"Confidence {csm.confidence_level} below threshold {policy.min_confidence_threshold}"
            )

        if csm.blockers:
            issues.append(
                f"Active blockers present: {', '.join(str(b) for b in csm.blockers)}"
            )

        return issues

    def verify_evidence_hash(self, run_id: str, phase: str, evidence_hash: str) -> bool:
        """Verify evidence integrity by comparing SHA-256 hashes.

        Returns True if the computed hash matches the provided hash.
        """
        evidence_path = self.evidence_dir / f"{run_id}_{phase}.json"

        if not evidence_path.exists():
            return False

        content = evidence_path.read_text()
        actual_hash = hashlib.sha256(content.encode()).hexdigest()

        return actual_hash == evidence_hash


__all__ = ["PromotionGate"]
