"""Unit tests for Omega Consensus (WP-45003)."""

import pytest

from thegent.orchestration.consensus.omega_consensus import OmegaConsensus


@pytest.mark.unit
class TestOmegaConsensus:
    """Omega Consensus (WP-45003)."""

    def test_reach_consensus_on_final_state(self) -> None:
        # @trace FR-CON-001
        """A proposal reaches consensus if enough agents vote YES."""
        consensus = OmegaConsensus(swarm_size=5, threshold=0.6)

        # Propose state
        proposal_id = consensus.propose_state(
            proposer_id="agent-master",
            state={"status": "completed", "version": "1.0"},
            metadata={"reason": "Project goals reached."},
        )

        # Cast 4/5 YES votes (80% > 60% threshold)
        for i in range(4):
            consensus.cast_vote(proposal_id, f"voter-{i}", True, f"signature-{i}")

        reached = consensus.finalize_consensus(proposal_id)
        assert reached is True

        final_state = consensus.get_final_state()
        assert final_state is not None
        assert final_state.proposal_id == proposal_id

    def test_fail_consensus_below_threshold(self) -> None:
        # @trace FR-CON-001
        """Consensus fails if YES votes are below threshold."""
        consensus = OmegaConsensus(swarm_size=10, threshold=0.8)

        proposal_id = consensus.propose_state(proposer_id="agent-master", state={"status": "failed"}, metadata={})

        # Cast 7/10 YES votes (70% < 80% threshold)
        for i in range(7):
            consensus.cast_vote(proposal_id, f"voter-{i}", True, "sig")

        reached = consensus.finalize_consensus(proposal_id)
        assert reached is False
        assert consensus.get_final_state() is None

    def test_vote_on_unknown_proposal(self) -> None:
        # @trace FR-CON-001
        """Voting on unknown proposal returns False."""
        consensus = OmegaConsensus(swarm_size=3)
        success = consensus.cast_vote("unknown", "agent-1", True, "sig")
        assert success is False
