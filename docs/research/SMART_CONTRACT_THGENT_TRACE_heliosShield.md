<DONE>
# Smart Contract System — thegent, trace, heliosShield Roles

**Purpose:** Handoff doc explaining how thegent, trace, and heliosShield participate in the smart contract QA governance system.

**Related:** [SMART_CONTRACT_SYSTEM_OVERVIEW.md](./SMART_CONTRACT_SYSTEM_OVERVIEW.md)

---

## 1. Summary

| Project          | Role in Smart Contract System                                                                          |
| ---------------- | ------------------------------------------------------------------------------------------------------ |
| **heliosShield** | Hosts the smart contract system: gate script, hooks, governance, P7–P16 phases                         |
| **trace**        | Strictness reference for rollout; requirement traceability system; uses thegent for agent runs         |
| **thegent**      | Agent orchestration CLI; single source of truth; integrates with heliosShield via discovery/dev health |

---

## 2. heliosShield — Host of the Smart Contract System

### 2.1 Responsibilities

- **Gate enforcement:** `scripts/qa-smart-contract-gate.py` enforces spec→tests→evidence
- **FR-source onboarding:** P7 scripts (`generate-fr-source-onboarding.py`, `rollout-fr-source-contracts.sh`, etc.)
- **Governance hooks:** 17 hooks under `~/.claude` (qa-dag-dependency-gate, qa-policy-engine, qa-attestation-builder, etc.)
- **Policy engine:** OPA/Rego policies (when P8 complete)
- **Evidence/attestation:** in-toto, SLSA, Sigstore (P9, P16)

### 2.2 Integration Points

- `make quality` runs the smart-contract gate
- Advisory for `established` tier; strict for `critical`
- Gate output: `.claude/verification/smart-contract-gate.json`
- Uses **trace** as strictness reference for rollout (pyproject.toml, .golangci.yml, etc.)

### 2.3 thegent Usage

- heliosShield uses thegent for external agent orchestration
- Example: `thegent bg -d "$(pwd)" --owner "$USER:heliosShield" -f cursor '...'`
- No Makefile wrappers; CLI is single source of truth per `2026-02-14-THGENT-PLAN-AUDIT-FULL.md`

---

## 3. trace — Strictness Reference and Traceability

### 3.1 Role

- **Strictness reference:** QA_GOVERNANCE_SMART_CONTRACT_PLAN_V3 §3.3 designates trace as the canonical strictness profile for rollout:
  - Python: `trace/pyproject.toml`
  - Go: `trace/backend/.golangci.yml`
  - TypeScript: `trace/frontend/.oxlintrc.json`
  - Module boundaries: `trace/tach.toml`

- **Requirement traceability:** Trace is a requirement traceability and project tracking system. Its patterns (FR IDs, traceability matrix, sync engine) align with the smart contract model (FR→tests→evidence).

### 3.2 thegent Usage

- trace uses `thegent run <agent> <prompt>` for agent runs
- No Makefile wrappers; references `THGENT_QUICK_REFERENCE.md`, `claude.md`, `agents.md`

### 3.3 Relationship to Smart Contract

- trace does **not** host the smart contract gate
- trace provides the **baseline** for what "strict" means when heliosShield rolls out governance to other projects
- trace’s FR/traceability model is conceptually aligned with CDDL (requirement→evidence→state)

---

## 4. thegent — Agent Orchestration CLI

### 4.1 Role

- **Single source of truth** for CLI: no Makefile targets or scripts wrap or bypass it
- **Agent orchestration:** `run`, `bg`, `ps`, `status`, `logs`, `wait`, `stop`, `list-agents`, `list-droids`, `list-models`
- **DAG:** `dag list`, `validate`, `add`, `update`, `remove`, `cancel`, `ready`, `run`, `status`, `sync`
- **MCP:** `thegent serve` for MCP tools

### 4.2 Integration with heliosShield

- `thegent discovery register` — registers projects with heliosShield
- `heliosShield dev health` — delegates to harness; can be used to check health of thegent-managed sessions
- heliosShield and trace both invoke thegent directly; no wrappers

### 4.3 Relationship to Smart Contract

- thegent does **not** implement the smart contract gate
- thegent **orchestrates agents** that produce evidence (tests, attestations, claims)
- Typed agent assertions (P13) will constrain agent output; thegent runs those agents
- MCP tools (`thegent_run`, `thegent_bg`, etc.) enable Cursor/IDEs to drive agents that participate in the evidence pipeline

---

## 5. Data Flow (Conceptual)

```
┌─────────────────────────────────────────────────────────────────┐
│  PRD, ADR, Func_Reqs, PLAN (DAG), USER_JOURNEYS                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  heliosShield: Conversion pipeline → canonical records → ledger     │
│  (P7 schemas, ledger-init, FR-source onboarding)                │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  thegent: Agent runs (run, bg) produce tests, evidence, claims   │
│  (trace, heliosShield, other projects invoke thegent)               │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  heliosShield: qa-smart-contract-gate.py                            │
│  - FR discovery, test discovery, evidence check                │
│  - Policy engine (P8), attestation (P9), methodology (P10)       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  State transition: EvidenceSubmitted → Verified → Released      │
│  (only when policy-mandated evidence exists and passes)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Key Documents

| Doc                                                                               | Purpose                              |
| --------------------------------------------------------------------------------- | ------------------------------------ |
| `heliosShield/docs/guides/QA_GOVERNANCE_SMART_CONTRACT_PLAN_V3.md`                | Full v3 plan                         |
| `heliosShield/chatgpt.md`                                                         | CDDL origin (chatgpt transcript)     |
| `heliosShield/docs/unified/modules/governance/smart-contracts.md`                 | Module overview                      |
| `heliosShield/docs/reports/2026-02-14-heliosShield-SMART-CONTRACT-HOOKS-AUDIT.md` | Audit and gaps                       |
| `heliosShield/docs/reports/2026-02-14-THGENT-PLAN-AUDIT-FULL.md`                  | thegent/heliosShield/trace CLI audit |
| `trace/00_START_HERE.md`                                                          | Trace project overview               |

---

## 7. Handoff Notes for AI Assistants

1. **Smart contract ≠ blockchain.** It is a process guarantee: evidence-backed state transitions.
2. **heliosShield** owns the gate, hooks, and governance; **trace** is the strictness reference; **thegent** runs agents.
3. P1–P7 are implemented; P8–P16 are pending or deferred.
4. For rollout, use trace’s configs (`pyproject.toml`, `.golangci.yml`, etc.) as the strictness baseline.
5. All three projects use thegent CLI directly—no Makefile wrappers.
