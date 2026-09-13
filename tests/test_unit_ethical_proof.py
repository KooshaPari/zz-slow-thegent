"""Unit tests for Formal Ethical Proof (WP-39002)."""

import pytest

from thegent.verification.ethics_proof import (
    EthicalProofGenerator,
    EthicalProofVerifier,
    FormalEthicalProof,
)


@pytest.mark.unit
class TestEthicalProof:
    """Formal Ethical Proof (WP-39002)."""

    def test_generate_and_verify_proof(self) -> None:
        # @trace FR-ETH-001
        """Can generate and verify a formal ethical proof."""
        generator = EthicalProofGenerator()
        verifier = EthicalProofVerifier()

        # Valid proof
        proof = generator.generate("action-1", True, ["evidence-A", "evidence-B"])
        assert isinstance(proof, FormalEthicalProof)
        assert proof.aligned is True
        assert len(proof.evidence_ids) == 2

        success = verifier.verify(proof)
        assert success is True

    def test_verify_unaligned_proof(self) -> None:
        # @trace FR-ETH-001
        """Unaligned proof fails verification."""
        generator = EthicalProofGenerator()
        verifier = EthicalProofVerifier()

        proof = generator.generate("action-fail", False, ["evidence-C"])
        assert proof.aligned is False

        success = verifier.verify(proof)
        assert success is False

    def test_verify_proof_no_evidence(self) -> None:
        # @trace FR-ETH-001
        """Proof without evidence fails verification."""
        verifier = EthicalProofVerifier()

        # Manually create a proof with no evidence
        proof = FormalEthicalProof(
            verified_principles=["P1"], critique_hash="hash", aligned=True, signature="sig", evidence_ids=[]
        )

        success = verifier.verify(proof)
        assert success is False
