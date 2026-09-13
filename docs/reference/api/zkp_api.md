# zkp API Reference

> **Source**: `src/thegent/verification/zkp.py`

WP-27002: Zero-Knowledge Proofs (ZKP) for Context Integrity.

Enables agents to prove they have certain context or permissions without revealing the raw data.
Uses a simplified ZK-SNARK-inspired pattern for agent governance.

---

## ZKGovernor

Orchestrates Zero-Knowledge governance for sensitive context.

### Methods

#### ZKGovernor.**init**

```python
__init__(self: Any, agent_id: str)
```

---

#### ZKGovernor.generate_proof

```python
generate_proof(self: Any, secret_context: str, challenge: str)
```

Generate a ZK proof for a given secret context and challenge.

---

#### ZKGovernor.verify_proof

```python
verify_proof(self: Any, proof: ZKProof, known_commitment: str)
```

Verify a ZK proof against a known commitment.

---

---

## ZKProof

Metadata for a Zero-Knowledge Proof.

**Inherits from**: `BaseModel`

---

## generate_proof

```python
generate_proof(self: Any, secret_context: str, challenge: str)
```

Generate a ZK proof for a given secret context and challenge.

---

## verify_proof

```python
verify_proof(self: Any, proof: ZKProof, known_commitment: str)
```

Verify a ZK proof against a known commitment.

---
