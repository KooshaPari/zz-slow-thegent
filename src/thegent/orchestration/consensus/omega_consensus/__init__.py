"""Omega-style swarm consensus (dormant SOTA pass-22 hardening).

@trace FR-CON-001 (WP-45003)
@trace FR-ORC-CON-075 .. FR-ORC-CON-079 (dormant hardening invariants)

The ``OmegaConsensus`` object tracks a swarm of voters that must reach a
YES/NO quorum over a sequence of proposals.  Each proposal is a free-form
``state`` payload submitted by a ``proposer_id``; voters record
``cast_vote(proposal_id, voter_id, vote, signature)`` and the swarm
finalises a proposal once enough YES votes have been cast.

Thread safety: the swarm uses an ``RLock`` so concurrent ``propose_state``
/ ``cast_vote`` / ``finalize_consensus`` calls from worker threads never
see torn state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

__all__ = ["FinalState", "OmegaConsensus"]


@dataclass(frozen=True)
class FinalState:
    """Immutable snapshot of the finalised proposal.

    Attributes:
        proposal_id: Unique identifier of the proposal that won quorum.
        state: The payload that the proposer submitted.
        metadata: Free-form metadata the proposer attached.
    """

    proposal_id: str
    state: Any
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class _Proposal:
    """Internal proposal record (mutable, guarded by ``OmegaConsensus._lock``)."""

    proposer_id: str
    state: Any
    metadata: dict[str, Any]
    votes: dict[str, tuple[bool, str]]  # voter_id -> (vote, signature)


class OmegaConsensus:
    """Swarm quorum / consensus engine.

    Args:
        swarm_size: Total number of eligible voters.  Must be a positive
            integer; ``0`` / negative values raise ``ValueError``.
        threshold: Fraction of YES votes (0 .. 1) required for quorum.
            Values outside ``[0, 1]`` raise ``ValueError``.

    Raises:
        ValueError: ``swarm_size <= 0`` or ``threshold`` out of range.
    """

    def __init__(self, swarm_size: int, threshold: float = 0.5) -> None:
        if not isinstance(swarm_size, int) or swarm_size <= 0:
            raise ValueError(f"swarm_size must be a positive integer, got {swarm_size!r}")
        if threshold < 0.0 or threshold > 1.0:
            raise ValueError(f"threshold must be in [0, 1], got {threshold!r}")
        self.swarm_size = swarm_size
        self.threshold = threshold
        self._proposals: dict[str, _Proposal] = {}
        self._final_state: FinalState | None = None
        self._lock = RLock()

    # -- proposal lifecycle --------------------------------------------------

    def propose_state(
        self,
        proposer_id: str,
        state: Any,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Submit a new proposal and return its ``proposal_id``."""
        pid = uuid.uuid4().hex
        with self._lock:
            self._proposals[pid] = _Proposal(
                proposer_id=proposer_id,
                state=state,
                metadata=dict(metadata) if metadata else {},
                votes={},
            )
        return pid

    # -- voting --------------------------------------------------------------

    def cast_vote(self, proposal_id: str, voter_id: str, vote: bool, signature: str) -> bool:
        """Record ``voter_id``'s ``vote`` on ``proposal_id``.

        Returns ``False`` for unknown ``proposal_id``.  Duplicate votes
        from the same ``voter_id`` on the same proposal are idempotent
        — the original vote is retained and ``True`` is returned (the
        vote was successfully *recorded*, even though the tally is
        unchanged).
        """
        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if proposal is None:
                return False
            if voter_id in proposal.votes:
                return True
            proposal.votes[voter_id] = (bool(vote), signature)
            return True

    # -- finalisation --------------------------------------------------------

    def finalize_consensus(self, proposal_id: str) -> bool:
        """Tally the votes on ``proposal_id`` and finalise if quorum is met.

        Returns ``True`` when YES votes / ``swarm_size`` >= threshold and
        the proposal becomes the swarm's current ``FinalState``.  Returns
        ``False`` for unknown proposals or when the YES ratio is below
        threshold; ``get_final_state()`` is left untouched in the latter
        case.
        """
        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if proposal is None:
                return False
            yes_votes = sum(1 for v, _ in proposal.votes.values() if v)
            if yes_votes / self.swarm_size < self.threshold:
                return False
            self._final_state = FinalState(
                proposal_id=proposal_id,
                state=proposal.state,
                metadata=dict(proposal.metadata),
            )
            return True

    def get_final_state(self) -> FinalState | None:
        """Return the swarm's current ``FinalState`` or ``None`` if unset."""
        with self._lock:
            return self._final_state
