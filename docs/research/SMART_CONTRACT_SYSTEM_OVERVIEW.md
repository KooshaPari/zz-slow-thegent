<DONE>
# Smart Contract System — Overview

**Purpose:** Handoff doc for the QA governance smart-contract system. Explains what it is, where it lives, and how it works.

**Source:** `heliosShield/docs/guides/QA_GOVERNANCE_SMART_CONTRACT_PLAN_V3.md`, `heliosShield/chatgpt.md`, `heliosShield/docs/unified/modules/governance/smart-contracts.md`

---

## 1. What Is the Smart Contract System?

### 1.1 Definition

The **smart contract** in this context is **not** a blockchain contract. It is a **process guarantee**:

> A requirement item cannot move to Done/Released unless policy-mandated evidence exists, matches the exact requirement version/spec hash, and dependency ordering is enforced from the DAG.

**Operational definition:**

- Deterministic state transitions
- Signed, policy-valid evidence
- Optional blockchain anchoring (not required)

### 1.2 Hard Truth (from chatgpt.md)

- We **cannot** guarantee "zero bugs" for real-world software.
- We **can** guarantee the delivery process:
  - Evidence must exist before Released
  - Evidence must match spec hash
  - DAG dependency ordering enforced
  - Claims are signed, attributable, auditable

---

## 2. Contract-Driven Development Ledger (CDDL)

### 2.1 Core Model

Every item (`FR`, `NFR`, `US`, `ADR`, `TASK`) is a canonical record with:

| Field                             | Purpose                       |
| --------------------------------- | ----------------------------- |
| `id`, `type`, `version`, `status` | Identity and lifecycle        |
| `depends_on[]`                    | DAG edges; enforces ordering  |
| `acceptance[]`                    | Acceptance criteria           |
| `formal_properties[]`             | Invariants (e.g. TLA+)        |
| `evidence_policy.required[]`      | What evidence must exist      |
| `open_questions[]`                | Must be empty before Approved |
| `decisions[]`                     | ADR links                     |

### 2.2 Canonical Hash

`spec_hash = sha256(canonical_record + canonical_markdown_body)` — immutable contract anchor for gates, attestations, and optional on-chain refs.

### 2.3 State Machine

| State             | Gate to leave                               |
| ----------------- | ------------------------------------------- |
| Draft             | —                                           |
| Proposed          | —                                           |
| Approved          | `open_questions` empty; ADR links resolved  |
| Claimed           | All dependencies Verified or stronger       |
| EvidenceSubmitted | All required evidence artifacts generated   |
| Verified          | Evidence passes schema + policy + signature |
| Accepted          | Policy acceptance (auto or quorum)          |
| Released          | Release checks and provenance complete      |
| Rejected          | —                                           |

---

## 3. Evidence and Attestation

- **Format:** in-toto Statement v1 envelope; SLSA provenance predicate for build
- **Signing:** Sigstore/cosign; Rekor transparency log for critical tier
- **Policy:** Critical verifications require reproducible/hermetic execution; verifier quorum (2-of-3) for Verified
- **Fail-closed:** Missing/invalid mandatory evidence blocks transition

---

## 4. Typed Agent Assertions

Agent output must be machine-typed, not free-form. Allowed kinds:

- `observation`, `claim`, `proposal`, `question`, `decision`, `risk`
- `claim` and `observation` must include evidence references
- Only typed, schema-valid, signed claim bundles may trigger state transitions

---

## 5. Where It Lives

| Component         | Location                                                                          |
| ----------------- | --------------------------------------------------------------------------------- |
| Plan              | `heliosShield/docs/guides/QA_GOVERNANCE_SMART_CONTRACT_PLAN_V3.md`                |
| Gate script       | `heliosShield/scripts/qa-smart-contract-gate.py`                                  |
| Gate output       | `heliosShield/.claude/verification/smart-contract-gate.json`                      |
| Module overview   | `heliosShield/docs/unified/modules/governance/smart-contracts.md`                 |
| Source transcript | `heliosShield/chatgpt.md` (CDDL origin)                                           |
| Audit             | `heliosShield/docs/reports/2026-02-14-heliosShield-SMART-CONTRACT-HOOKS-AUDIT.md` |

---

## 6. Phase Plan (P1–P16)

| Phase | Description                                                           | Status                |
| ----- | --------------------------------------------------------------------- | --------------------- |
| P1–P6 | Spec→tests→evidence gate (FR regex, test discovery, evidence files)   | Implemented           |
| P7    | Canonical contract layer (schemas, ledger-init, FR-source onboarding) | Implemented           |
| P8    | Policy-as-Code engine (OPA/Rego)                                      | Pending               |
| P9    | Evidence recorder + attestation builder                               | Pending               |
| P10   | Methodology enforcer (TDD/BDD/Contract/Property/Mutation)             | Pending               |
| P11   | Reliability governance (flaky quarantine, SLO)                        | Pending               |
| P12   | Supply chain and provenance gate                                      | Pending               |
| P13   | Typed agent claim protocol                                            | Pending               |
| P14   | Optional on-chain workflow adapter                                    | Deferred              |
| P15   | Program rollout across projects                                       | Pending               |
| P16   | Attestation hardening (in-toto, Rekor, SARIF, chaos)                  | Partially implemented |

---

## 7. Schemas

- `schemas/requirement.schema.json`
- `schemas/evidence.schema.json`
- `schemas/state_machine.schema.json`
- `schemas/agent-statement.schema.json`
- `schemas/ledger.schema.json`
- `schemas/attestation.statement.schema.json` (P16)

---

## 8. Enforcement Profiles

| Tier        | Required                                                                |
| ----------- | ----------------------------------------------------------------------- |
| Baseline    | unit + integration + security + traceability                            |
| Established | baseline + e2e + contract (if API) + reliability SLO                    |
| Critical    | established + property + mutation + formal checks + stricter provenance |

---

## 9. Integration with chatgpt.md

The v3 plan integrates the full model from `heliosShield/chatgpt.md`:

| chatgpt.md concept                   | v3 coverage       |
| ------------------------------------ | ----------------- |
| Hard truth: process vs functionality | Section 2         |
| CDDL model                           | Section 4         |
| Canonical item + hash                | Section 4.1, 4.2  |
| Enforceable DAG                      | Sections 4, 6, 14 |
| Evidence as "Done" contract          | Sections 7, 16    |
| in-toto + SLSA + signatures          | Section 7         |
| On-chain vs off-chain split          | Section 11        |
| Formal methods (TLA+/Alloy/Dafny)    | Section 10        |
| Robust elicitation                   | Section 9         |
| Typed agent assertions               | Section 8         |

---

## 10. Case Study (Music Player)

The plan includes a walkthrough for `FR-1.2.0` (Seek via scrubber):

1. Elicitation closure (seek latency, paused behavior, browser compatibility)
2. Contract record and hash generation
3. Agent claim after dependency gate (FR-1.0.0, FR-1.1.0 verified)
4. Evidence: unit, e2e, model-check if required
5. Attestation/signing
6. Verifier quorum
7. State transition to Verified → Accepted/Released
