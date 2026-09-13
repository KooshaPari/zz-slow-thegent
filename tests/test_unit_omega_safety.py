"""Unit tests for Omega Safety (WP-45002)."""

import pytest

from thegent.verification.omega_safety import OmegaSafetyGuard


@pytest.mark.unit
class TestOmegaSafety:
    """Omega Safety (WP-45002)."""

    def test_verify_safe_action(self) -> None:
        # @trace FR-SAF-001
        """A safe action passes verification."""
        guard = OmegaSafetyGuard()
        action_data = {
            "type": "READ",
            "target_file": "src/main.py",
            "is_moral_dilemma": False,
            "require_formal_proof": False,
        }

        is_safe = guard.is_safe("action-safe", action_data)
        assert is_safe is True
        assert len(guard.verify_action("action-safe", action_data)) == 0

    def test_verify_ledger_deletion_violation(self) -> None:
        # @trace FR-SAF-001
        """Deleting critical ledger files violates OMEGA-001."""
        guard = OmegaSafetyGuard()
        action_data = {
            "type": "DELETE",
            "target_file": "docs/reference/evidence_ledger.jsonl",
        }

        violations = guard.verify_action("action-del", action_data)
        assert len(violations) == 1
        assert violations[0].invariant_id == "OMEGA-001"
        assert guard.is_safe("action-del", action_data) is False

    def test_verify_hitl_bypass_violation(self) -> None:
        # @trace FR-SAF-001
        """Moral dilemma without HITL verification violates OMEGA-002."""
        guard = OmegaSafetyGuard()
        action_data = {
            "type": "EXECUTE",
            "is_moral_dilemma": True,
            "hitl_verified": False,
        }

        violations = guard.verify_action("action-moral", action_data)
        assert len(violations) == 1
        assert violations[0].invariant_id == "OMEGA-002"

    def test_verify_proof_missing_violation(self) -> None:
        # @trace FR-SAF-001
        """Missing formal proof when required violates OMEGA-003."""
        guard = OmegaSafetyGuard()
        action_data = {
            "type": "EXECUTE",
            "require_formal_proof": True,
            "proof_verified": False,
        }

        violations = guard.verify_action("action-proof", action_data)
        assert len(violations) == 1
        assert violations[0].invariant_id == "OMEGA-003"
