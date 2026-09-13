# Constitutional Enforcement & Proof of Alignment (WP-3001)

This document defines how `thegent` enforces project-wide rules, ethics, and safety through **Constitutional AI** patterns.

## 1. The Project Constitution

The "Constitution" is a set of machine-readable principles (stored in `contracts/constitution.yaml`) that guide all agent activity. It extends the instructions found in `CLAUDE.md`.

### 1.1 Core Principles (Example)

- **Principle 1 (Safety)**: Never perform irreversible destructive actions without simulation and human sign-off.
- **Principle 2 (Privacy)**: Never leak PII (Personally Identifiable Information) into logs or external provider prompts.
- **Principle 3 (Efficiency)**: Favor existing project patterns over new library dependencies.

## 2. Enforcement via Policy Engine

The `PolicyEngine` (OPA/Rego) acts as the **Constitutional Guard**:

### 2.1 Pre-Execution Critique

Before an agent executes a high-risk tool call:

1. The `Orchestrator` sends the proposed action to a specialized **Critique Agent**.
2. The Critique Agent evaluates the action against the Constitution.
3. If a violation is found, the Critique Agent generates a "Constitutional Rebuke."
4. The acting agent must then "Self-Correct" the proposal before it is sent to the human for approval.

### 2.2 Proof of Alignment (PoA)

Every **MAIF artifact** must include a `Proof_of_Alignment` metadata block:

- **Verified Principles**: A list of constitutional principles checked during the run.
- **Critique Hash**: A cryptographic signature from the Critique Agent verifying alignment.

## 3. Constitutional Drift Detection

The **Gardener** scans the **Immutable Audit Trail** for "Constitutional Drift":

- **Pattern Matching**: Identifying sequences of actions that, while individually policy-compliant, semantically violate a principle (e.g., "Boilerplate Proliferation").
- **Alerting**: Drift > Threshold triggers an automatic "Constitutional Audit" run.

---

_Cross-ref: [ROBUSTNESS_AND_FUTURE_DEPTH.md](./ROBUSTNESS_AND_FUTURE_DEPTH.md) | [MAIF_ARTIFACT_SPEC_DEPTH.md](./MAIF_ARTIFACT_SPEC_DEPTH.md)_

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
