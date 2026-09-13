# proof_carrying API Reference

> **Source**: `src/thegent/verification/proof_carrying.py`

WP-18003: Proof-Carrying Code for MCP Tools.

Ensures that all MCP tools carry logical proofs or signatures that can be verified at runtime.

---

## PCCVerifier

Verifies proof-carrying code for MCP tools.

### Methods

#### PCCVerifier.**init**

```python
__init__(self: Any)
```

---

#### PCCVerifier.register_proof

```python
register_proof(self: Any, tool_id: str, property_id: str, signature: str, proof_type: str)
```

Register a proof for a tool.

---

#### PCCVerifier.verify_tool

```python
verify_tool(self: Any, tool_id: str, tool_code: str)
```

Verify that a tool's code matches its registered proofs.

---

---

## Proof

A proof or signature for an MCP tool.

**Inherits from**: `BaseModel`

---

## register_proof

```python
register_proof(self: Any, tool_id: str, property_id: str, signature: str, proof_type: str)
```

Register a proof for a tool.

---

## verify_tool

```python
verify_tool(self: Any, tool_id: str, tool_code: str)
```

Verify that a tool's code matches its registered proofs.

---
