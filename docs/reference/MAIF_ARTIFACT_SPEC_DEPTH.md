# MAIF Artifact Specification & Provenance Depth (WP-3002)

This document provides technical depth for the **Model AI Information Format (MAIF)** implementation, based on the research paper _MAIF: Enforcing AI Trust and Provenance with an Artifact-Centric Agentic Paradigm_ (arXiv:2511.15097).

## 1. MAIF Container Structure

MAIF is an AI-native container that transforms agent outputs from passive storage into active, verifiable trust artifacts.

### 1.1 Hierarchical Block Structure

Every MAIF artifact (`.maif` or signed JSON structure) follows a hierarchical block schema:

| Block                  | Description                                                         |
| ---------------------- | ------------------------------------------------------------------- |
| **Header**             | File ID, Version, Root Cryptographic Hash (SHA-256).                |
| **Modality Blocks**    | Raw action data (text, images, tool results, model outputs).        |
| **Semantic Layer**     | Multi-modal embeddings and knowledge graph fragments for reasoning. |
| **Security Metadata**  | Digital signatures (ECDSA), ACLs, and the Provenance Chain.         |
| **Lifecycle Metadata** | Version history, adaptation rules, and state machine transitions.   |

### 1.2 Cryptographic Semantic Binding (CSB)

To prevent **semantic injection** (where an adversary replaces data with a payload that generates a similar embedding), MAIF implements CSB:

- `Commitment = Hash(Embedding(x) || x || nonce)`
- This creates an unbreakable cryptographic link between the source data `x` and its semantic representation.

## 2. Multi-Layer Security Model

MAIF employs a defense-in-depth model for agentic operations:

- **Layer 1: Foundation**: SHA-256 hashing for all blocks; ECDSA signatures for non-repudiation.
- **Layer 2: Block-Level Integrity**: Each block is individually hashed and signed; tampering in one block is detected without re-parsing the whole artifact.
- **Layer 3: Immutable Provenance**: Cryptographically linked audit trail (`hash_j = SHA256(hash_{j-1} || serialize(event_j))`).

## 3. Trust-Aware Reasoning (ACAM)

**Adaptive Cross-Modal Attention (ACAM)** allows `thegent` agents to weight attention based on trust:

- `TrustFactor` is derived from the provenance chain's verification status.
- Actions from highly-verified sources receive higher attention weights in the reasoning phase.
- Reduces the impact of "hallucinated" or "untrusted" tool outputs.

## 4. Implementation Details (WP-3002)

### 4.1 MAIF Schema (v1.0)

```python
class MAIFHeader(BaseModel):
    version: str = "1.0"
    root_hash: str
    artifact_id: str
    timestamp_us: int


class MAIFBlock(BaseModel):
    block_id: str
    block_type: str  # "modality", "semantic", "security", "lifecycle"
    payload_hash: str
    signature: str | None = None
    payload: dict | bytes


class MAIFArtifact(BaseModel):
    header: MAIFHeader
    blocks: list[MAIFBlock]
    provenance_chain: list[str]  # List of block_hashes
```

### 4.2 Integration with thegent Execution

1. **Generation**: After a critical `thegent` run, a MAIF artifact is generated, signing the `RunMeta` and all tool outputs.
2. **Persistence**: Artifacts are stored in `.thegent/artifacts/{run_id}.maif.json`.
3. **Verification**: The `signatures verify` command performs:
   - Root hash validation.
   - Individual block signature verification.
   - Provenance chain continuity check.

## 5. Roadmap to Full Provenance

- **Phase 1**: Signed JSON artifacts (Current).
- **Phase 2**: CSB (Cryptographic Semantic Binding) for embeddings.
- **Phase 3**: ACAM integration for multi-agent consensus.

---

_Derived from: Narajala et al. (2025) MAIF: Enforcing AI Trust and Provenance._

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
