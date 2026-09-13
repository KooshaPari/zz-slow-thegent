# consensus API Reference

> **Source**: `src/thegent/mesh/consensus.py`

Consensus and escalation protocols for the agent mesh.

---

## CausalInfluenceTracker

Shapley-value causal influence tracking (SCLI-P3.2).

### Methods

#### CausalInfluenceTracker.**init**

```python
__init__(self: Any, mesh_root: Path)
```

---

#### CausalInfluenceTracker.record_influence

```python
record_influence(self: Any, agent_id: str, action_id: str, contribution: float)
```

Log contribution for later analysis.

---

---

## ConsensusProtocol

Crash-Preventing Weighted Byzantine Fault Tolerance (CP-WBFT) (ADR-013, SCLI-P3.1).

### Methods

#### ConsensusProtocol.**init**

```python
__init__(self: Any, mesh_root: Path)
```

---

#### ConsensusProtocol.cast_vote

```python
cast_vote(self: Any, proposal_id: str, agent_id: str, vote: bool, confidence: float)
```

Phase 4: VOTE (ADR-013). Cast a weighted vote for the finalized proposal.

---

#### ConsensusProtocol.draft

```python
draft(self: Any, proposal_id: str, agent_id: str, refinement: dict)
```

Phase 2: DRAFT (ADR-013). Agents can provide refinements or counter-proposals.

---

#### ConsensusProtocol.get_consensus

```python
get_consensus(self: Any, proposal_id: str, required_majority: float)
```

Phase 5 &amp; 6: TALLY &amp; DECIDE (ADR-013). Check if consensus is reached.

---

#### ConsensusProtocol.propose

```python
propose(self: Any, proposal_id: str, agent_id: str, topic: str, content: dict)
```

Phase 1: PROPOSE (ADR-013). Initial proposal by a leader.

---

#### ConsensusProtocol.share

```python
share(self: Any, proposal_id: str)
```

Phase 3: SHARE (ADR-013). Finalize the proposal after drafting period.

---

---

## ConsensusStatus

**Inherits from**: `enum.Enum`

---

## EscalationWorkflow

5-tier escalation workflow (SCLI-P3.3).

### Methods

#### EscalationWorkflow.**init**

```python
__init__(self: Any, mesh_root: Path)
```

---

#### EscalationWorkflow.escalate

```python
escalate(self: Any, proposal_id: str, current_tier: int)
```

Escalate to next tier (SCLI-P3.3).

---

---

## cast_vote

```python
cast_vote(self: Any, proposal_id: str, agent_id: str, vote: bool, confidence: float)
```

Phase 4: VOTE (ADR-013). Cast a weighted vote for the finalized proposal.

---

## draft

```python
draft(self: Any, proposal_id: str, agent_id: str, refinement: dict)
```

Phase 2: DRAFT (ADR-013). Agents can provide refinements or counter-proposals.

---

## escalate

```python
escalate(self: Any, proposal_id: str, current_tier: int)
```

Escalate to next tier (SCLI-P3.3).

---

## get_consensus

```python
get_consensus(self: Any, proposal_id: str, required_majority: float)
```

Phase 5 &amp; 6: TALLY &amp; DECIDE (ADR-013). Check if consensus is reached.

---

## propose

```python
propose(self: Any, proposal_id: str, agent_id: str, topic: str, content: dict)
```

Phase 1: PROPOSE (ADR-013). Initial proposal by a leader.

---

## record_influence

```python
record_influence(self: Any, agent_id: str, action_id: str, contribution: float)
```

Log contribution for later analysis.

---

## share

```python
share(self: Any, proposal_id: str)
```

Phase 3: SHARE (ADR-013). Finalize the proposal after drafting period.

---
