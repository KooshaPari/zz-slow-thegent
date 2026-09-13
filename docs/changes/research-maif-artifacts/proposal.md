# Research: MAIF Action Artifacts — Proposal

**Status**: Research Complete | **Priority**: High | **Effort**: 8-12 tool calls
**Work Item**: WP-3002 | **Date**: 2026-02-18

---

## Executive Summary

Implement **MAIF (Multi-Agent Immutable Framework) Action Artifacts**: a system for creating cryptographically signed, immutable records of every significant agent action. Artifacts are stored in Supermemory's L4 (Documents API) with hash chain verification for tamper detection, enabling comprehensive audit trails, deterministic replay for debugging, and compliance verification.

**Business Value**:

- **Auditability**: Complete, tamper-proof record of all agent actions
- **Debuggability**: Deterministic replay to understand decision history
- **Compliance**: Hash chain verification for regulatory requirements
- **Cost**: ~$0.002 per artifact (~$1.5k/month at 750k artifacts)

---

## Problem Statement

### Current State

thegent lacks:

1. **Immutable Action Logs**: Agent actions are not cryptographically signed or tamper-proof
2. **Deterministic Replay**: No way to replay past decisions to understand why they were made
3. **Audit Trail Gaps**: No hash chain to detect tampering
4. **Compliance Gaps**: No non-repudiation or agent identity verification

### Target State

- Every significant agent action creates a signed MAIF artifact
- Hash chain links artifacts chronologically (any tampering breaks chain)
- Artifacts stored in Supermemory L4 (immutable, replicated)
- Replay engine reconstructs decision context from L3 + L4
- Audit system verifies artifact integrity

---

## Scope

### In-Scope

✅ MAIF artifact structure (signature, hash chain, metadata)
✅ Storage in Supermemory L4
✅ Hash chain creation and verification
✅ Artifact creation hooks (CodeChange, FileOperation, SystemCall, Decision, Error)
✅ Basic audit and retrieval APIs
✅ Integration with Supermemory L3/L4

### Out-of-Scope

❌ Advanced forensics (chain repair, multi-signature, threshold signatures)
❌ Replay simulation engine (separate WP-4007)
❌ Compliance-specific extensions (GxP, HIPAA audits)
❌ Performance optimization for extreme scale (>10M artifacts/day)

---

## Design Approach

### High-Level Architecture

```
Agent Actions
    │
    ├─ CodeChange → Artifact creation
    ├─ FileOperation → Artifact creation
    ├─ SystemCall → Artifact creation
    ├─ Decision → Artifact creation
    └─ Error → Artifact creation
    │
    ▼
MAIF Artifact (signed, hash chain)
    │
    ▼
Supermemory L4 (immutable storage)
    │
    ├─ Retrieve for audit
    ├─ Verify hash chain
    └─ Replay decision (via L3 context)
```

### Key Components

| Component             | Purpose                      | Location                         |
| --------------------- | ---------------------------- | -------------------------------- |
| `MAIFArtifact` struct | Artifact definition          | `thegent-maif/src/lib.rs`        |
| `MAIFStorage`         | L4 storage & retrieval       | `thegent/src/maif/storage.py`    |
| `HashChain`           | Hash chain management        | `thegent/src/maif/hash_chain.py` |
| `ArtifactHooks`       | Action → artifact conversion | `hooks/maif-artifact-hooks.sh`   |
| `AuditAPI`            | Artifact querying            | `thegent/src/maif/audit.py`      |

### Hash Chain Mechanism

```
Artifact 1: hash_chain_1 = H(input₁ || output₁ || prev_hash=0)
    ↓ (signed)
Artifact 2: hash_chain_2 = H(input₂ || output₂ || prev_hash=hash_chain_1)
    ↓ (signed)
Artifact 3: hash_chain_3 = H(input₃ || output₃ || prev_hash=hash_chain_2)
```

Any tampering breaks the chain forward (all subsequent artifacts invalidate).

---

## Success Criteria

- [ ] MAIF artifact structure defined and implemented
- [ ] Cryptographic signing working (RSA-2048 or Ed25519)
- [ ] Hash chain creation and verification functional
- [ ] All significant actions create artifacts (>80% coverage)
- [ ] Supermemory L4 storage operational
- [ ] Artifact retrieval and audit API working
- [ ] Chain integrity verification <10ms latency
- [ ] Artifact creation overhead <1ms per action
- [ ] Zero new security vulnerabilities
- [ ] Comprehensive test coverage (>90%)
- [ ] Integration tests with Supermemory passing

---

## Acceptance Criteria (Functional)

1. **Artifact Creation**: On each significant action (code change, file operation, system call, decision), create and sign MAIF artifact
2. **Hash Chain**: Each artifact references previous artifact's hash; chain is immutable
3. **Storage**: Artifacts persisted in Supermemory L4 with redundancy
4. **Verification**: `verify(artifact, previous_artifact)` returns true iff hash chain valid
5. **Audit**: Retrieve artifacts by session, agent, timestamp; verify chain integrity
6. **Performance**: All operations meet latency targets (<1ms create, <10ms verify)

---

## Risks & Mitigations

| Risk                                    | Impact | Mitigation                                                  |
| --------------------------------------- | ------ | ----------------------------------------------------------- |
| **Hash chain broken (data corruption)** | High   | Immutable L4 storage, periodic integrity checks, alerts     |
| **Storage failure**                     | High   | Local queue, retry with exponential backoff, fallback to L2 |
| **Signature verification expensive**    | Medium | Batch verification, caching, hardware acceleration          |
| **Supermemory API unavailable**         | Medium | Fallback to local storage, queue for later sync             |
| **Replay non-deterministic**            | Low    | Separate concern (WP-4007); mark non-replayable             |

---

## Related Work

**Depends On**:

- WP-5001-SM: Supermemory integration (L4 Documents API)
- WP-5001: Lifecycle loop optimization

**Enables**:

- WP-4007: Simulation & replay engine (uses artifacts)
- WP-AUDIT: Audit system (uses artifact chain)
- WP-COMPLIANCE: Regulatory compliance module

**References**:

- [SESSION_RESEARCH_FRAGMENTS_EXPANDED.md § 4](../SESSION_RESEARCH_FRAGMENTS_EXPANDED.md#4-maif-action-artifacts)
- [Supermemory.ai Documentation](https://supermemory.ai/docs)

---

## References & Context

See [design.md](design.md) for technical architecture and [tasks.md](tasks.md) for implementation checklist.
