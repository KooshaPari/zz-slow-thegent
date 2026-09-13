# Agent Identity & Sovereignty Depth (WP-6004)

This document defines the depth for **Agent Identity**, enabling verifiable provenance and cross-platform sovereignty for `thegent` droids.

## 1. Decentralized Identifier (DID) for Agents

Every agent instance in `thegent` is assigned a **W3C-compliant Decentralized Identifier (DID)**.

- **DID Format**: `did:thegent:swarm-1:agent-alpha-42`
- **DID Document**: A JSON metadata file that defines the agent's public keys, capabilities, and service endpoints.

## 2. Verifiable Credentials (VC)

Agents carry **Verifiable Credentials** issued by the project owner or the policy engine:

- **Capability VC**: Proof that an agent is authorized to use specific tools (e.g., `git-push`, `mcp-exec`).
- **Identity VC**: Proof that the agent belongs to a specific swarm and has been verified by a previous quality gate.

## 3. Agent-Specific Signing Keys

To support the **MAIF artifact specification**, each agent maintains its own cryptographic key pair:

- **Private Key**: Stored in the agent's secure local state (L2 memory).
- **Public Key**: Published in its DID Document.
- **Usage**: Every action result and audit event is signed by the agent's key, providing non-repudiable proof of agency.

## 4. Cross-Platform Sovereignty

When an agent "migrates" between platforms (e.g., from Cursor to Claude Code):

1. **Context Export**: The agent exports its `Identity_VC` and recent `Continuity_Packet`.
2. **Context Import**: The target platform verifies the VC against the global `thegent` registry.
3. **Resumption**: The agent resumes its run with its existing identity and signature chain intact.

---

_Cross-ref: [MAIF_ARTIFACT_SPEC_DEPTH.md](./MAIF_ARTIFACT_SPEC_DEPTH.md) | [MULTI_PLATFORM_PARITY_MASTER_PLAN.md](../plans/MULTI_PLATFORM_PARITY_MASTER_PLAN.md)_

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
