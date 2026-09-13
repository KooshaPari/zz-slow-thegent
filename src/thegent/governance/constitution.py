"""Constitutional AI and alignment enforcement for thegent (WP-3001).

@trace AUDIT-N+48 — FR-GOV-CN-001..015 dormant-core hardening spec.
"""

import hashlib
import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

_log = logging.getLogger(__name__)


class ConstitutionalViolation(BaseModel):
    """FR-GOV-CN-012: Pydantic model for a constitutional violation."""

    principle_id: str
    reason: str
    remediation: str


class ProofOfAlignment(BaseModel):
    """Verifiable proof that an action aligns with the constitution.

    @trace AUDIT-N+48 — FR-GOV-CN-013
    """

    verified_principles: list[str]
    critique_hash: str
    aligned: bool


class ConstitutionManager:
    """WP-3001: Manages project principles and critique logic.

    @trace AUDIT-N+48 — FR-GOV-CN-001..015
    """

    def __init__(self, constitution_path: Path) -> None:
        self.path = constitution_path
        self._load()

    def _load(self) -> None:
        """Load principles from YAML file.

        @trace AUDIT-N+48 — FR-GOV-CN-002, FR-GOV-CN-003, FR-GOV-CN-004, FR-GOV-CN-014
        """
        # FR-GOV-CN-014: reject relative paths
        if not self.path.is_absolute():
            msg = f"constitution_path must be an absolute path, got {self.path!r}"
            raise ValueError(msg)
        if not self.path.exists():
            self.principles = []
            return
        try:
            with open(self.path) as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError):
            _log.warning("Failed to load constitution from %s", self.path)
            self.principles = []
            return
        self.principles = data.get("principles", []) if isinstance(data, dict) else []

    def critique_action(self, action: dict[str, Any]) -> list[ConstitutionalViolation]:
        """WP-3001: Pre-execution critique of a proposed agent action.

        @trace AUDIT-N+48 — FR-GOV-CN-005, FR-GOV-CN-006, FR-GOV-CN-007, FR-GOV-CN-008, FR-GOV-CN-009
        """
        violations: list[ConstitutionalViolation] = []

        prompt = str(action.get("prompt", "")).lower()

        for p in self.principles:
            if p["id"] == "P1-SAFETY":
                if any(kw in prompt for kw in ["rm -rf", "force push", "delete all"]):
                    violations.append(
                        ConstitutionalViolation(
                            principle_id=p["id"],
                            reason="Destructive command detected in prompt.",
                            remediation="Use simulation mode or get explicit human sign-off.",
                        )
                    )

            if p["id"] == "P2-PRIVACY":
                if any(kw in prompt for kw in ["password", "api_key", "secret_key"]):
                    violations.append(
                        ConstitutionalViolation(
                            principle_id=p["id"],
                            reason="Potential secret leakage detected.",
                            remediation="Mask sensitive values before submitting.",
                        )
                    )

        return violations

    def generate_poa(self, action_id: str, aligned: bool) -> ProofOfAlignment:
        """Generate a Proof of Alignment for a MAIF artifact.

        @trace AUDIT-N+48 — FR-GOV-CN-010, FR-GOV-CN-011
        """
        verified = [p["id"] for p in self.principles]
        critique_data = f"{action_id}|{aligned}|{','.join(verified)}"
        c_hash = hashlib.sha256(critique_data.encode()).hexdigest()

        return ProofOfAlignment(verified_principles=verified, critique_hash=c_hash, aligned=aligned)
