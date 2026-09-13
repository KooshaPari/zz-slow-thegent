# omega_consensus API Reference

> **Source**: `src/thegent/orchestration/omega_consensus.py`

WP-45003: Final State Consensus Protocol (Omega).

Ensures all agents in the swarm agree on the final project state using BFT.

---

## OmegaConsensus

The final consensus engine for thegent (Phase 45).

Enforces agreement on the project's 'Omega' (final) state across all agents.

### Methods

#### OmegaConsensus.**init**

```python
__init__(self: Any, swarm_size: int, threshold: float)
```

---

#### OmegaConsensus.cast_vote

```python
cast_vote(self: Any, proposal_id: str, voter_id: str, vote: bool, signature: str)
```

Cast a vote for an Omega proposal.

---

#### OmegaConsensus.finalize_consensus

```python
finalize_consensus(self: Any, proposal_id: str)
```

Check if a proposal has reached consensus and finalize the state.

---

#### OmegaConsensus.get_final_state

```python
get_final_state(self: Any)
```

Return the finalized Omega state if consensus was reached.

---

#### OmegaConsensus.propose_state

```python
propose_state(self: Any, proposer_id: str, state: Any, metadata: dict[(str, Any)])
```

Propose a new final state for the project.

---

---

## OmegaProposal

A proposal for the final state of the project.

**Inherits from**: `BaseModel`

---

## OmegaVote

A vote on an Omega proposal.

**Inherits from**: `BaseModel`

---

## cast_vote

```python
cast_vote(self: Any, proposal_id: str, voter_id: str, vote: bool, signature: str)
```

Cast a vote for an Omega proposal.

---

## finalize_consensus

```python
finalize_consensus(self: Any, proposal_id: str)
```

Check if a proposal has reached consensus and finalize the state.

---

## get_final_state

```python
get_final_state(self: Any)
```

Return the finalized Omega state if consensus was reached.

---

## propose_state

```python
propose_state(self: Any, proposer_id: str, state: Any, metadata: dict[(str, Any)])
```

Propose a new final state for the project.

---
