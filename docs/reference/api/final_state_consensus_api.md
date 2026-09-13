# final_state_consensus API Reference

> **Source**: `src/thegent/work_packages/final_state_consensus.py`

WP-45003: Final State Consensus Protocol.

---

## FinalStateConsensusProtocol

Final state consensus protocol for distributed systems.

### Methods

#### FinalStateConsensusProtocol.**init**

```python
__init__(self: Any)
```

Initialize consensus protocol.

---

#### FinalStateConsensusProtocol.get_final_state

```python
get_final_state(self: Any, proposal_id: str)
```

Get final consensus state.

**Parameters**:

- `proposal_id`: Proposal identifier

**Returns**: Final state or None

---

#### FinalStateConsensusProtocol.propose_state

```python
propose_state(self: Any, node_id: str, state: dict[(str, Any)])
```

Propose a state.

**Parameters**:

- `node_id`: Node identifier
- `state`: Proposed state

**Returns**: True if proposal accepted

---

#### FinalStateConsensusProtocol.reach_consensus

```python
reach_consensus(self: Any, proposal_id: str, threshold: float)
```

Check if consensus is reached.

**Parameters**:

- `proposal_id`: Proposal identifier
- `threshold`: Consensus threshold (0.0-1.0)

**Returns**: True if consensus reached

---

#### FinalStateConsensusProtocol.vote

```python
vote(self: Any, proposal_id: str, node_id: str, vote: bool)
```

Vote on a proposal.

**Parameters**:

- `proposal_id`: Proposal identifier
- `node_id`: Voting node identifier
- `vote`: Vote (True/False)

---

---

## get_final_state

```python
get_final_state(self: Any, proposal_id: str)
```

Get final consensus state.

**Parameters**:

- `proposal_id`: Proposal identifier

**Returns**: Final state or None

---

## propose_state

```python
propose_state(self: Any, node_id: str, state: dict[(str, Any)])
```

Propose a state.

**Parameters**:

- `node_id`: Node identifier
- `state`: Proposed state

**Returns**: True if proposal accepted

---

## reach_consensus

```python
reach_consensus(self: Any, proposal_id: str, threshold: float)
```

Check if consensus is reached.

**Parameters**:

- `proposal_id`: Proposal identifier
- `threshold`: Consensus threshold (0.0-1.0)

**Returns**: True if consensus reached

---

## vote

```python
vote(self: Any, proposal_id: str, node_id: str, vote: bool)
```

Vote on a proposal.

**Parameters**:

- `proposal_id`: Proposal identifier
- `node_id`: Voting node identifier
- `vote`: Vote (True/False)

---
