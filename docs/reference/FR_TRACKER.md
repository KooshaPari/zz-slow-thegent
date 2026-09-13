# FR Tracker: thegent

Comprehensive tracking of all Functional Requirements.

> **Last Updated:** 2026-02-23
> **Total FRs:** 91
> **Legend:** ✓ = Implemented | ~ = Partial | ○ = Pending | ⊘ = Not Applicable

---

## FR-AGT: Agents (13 FRs)

| ID         | Title                                   | Priority | Status | Implementation            | Notes                                           |
| ---------- | --------------------------------------- | -------- | ------ | ------------------------- | ----------------------------------------------- |
| FR-AGT-001 | Base Runner Interface                   | P1       | ✓      | `agents/base.py`          | AgentRunner base class with run()               |
| FR-AGT-002 | Direct Agent Invocation via Native CLIs | P1       | ✓      | `agents/direct_agents.py` | cursor-agent, gemini, codex, copilot, claude    |
| FR-AGT-003 | Noisy Stderr Filtering                  | P2       | ✓      | `agents/direct_agents.py` | Filter node deprecation, hook registry          |
| FR-AGT-004 | Codex Proxy Runner via CLIProxyAPIPlus  | P1       | ✓      | `agents/codex_proxy.py`   |                                                 |
| FR-AGT-005 | Cursor API Runner                       | P1       | ○      |                           | wisdgod cursor-api backend                      |
| FR-AGT-006 | CLIProxyAPIPlus Lifecycle Management    | P1       | ✓      |                           | Binary resolution, config YAML, health-check    |
| FR-AGT-007 | Agent Registry and Name Resolution      | P1       | ✓      |                           | 12 agents + aliases                             |
| FR-AGT-008 | Provider Fallback Chain                 | P1       | ✓      |                           | get_fallback_agents()                           |
| FR-AGT-009 | Retry with Exponential Backoff          | P1       | ✓      |                           | tenacity, max 4 attempts                        |
| FR-AGT-010 | Failure Classification                  | P1       | ✓      |                           | RATE_LIMIT, TRANSIENT, USAGE_LIMIT              |
| FR-AGT-011 | Fallback State Machine Orchestration    | P1       | ✓      | `agents/state_machine.py` |                                                 |
| FR-AGT-012 | Droid Runner for Factory Droids         | P2       | ○      |                           | droid exec subprocess                           |
| FR-AGT-013 | Multi-Agent Execution Modes             | P2       | ✓      |                           | SEQUENTIAL_DELEGATION, PARALLEL_CONSENSUS, etc. |

---

## FR-CTR: Contracts (13 FRs)

| ID         | Title                                  | Priority | Status | Implementation                       | Notes                                  |
| ---------- | -------------------------------------- | -------- | ------ | ------------------------------------ | -------------------------------------- |
| FR-CTR-001 | CSM Schema                             | P1       | ✓      | `contracts/parser.py`                | CanonicalStructuredMessage dataclass   |
| FR-CTR-002 | Incremental XML Parser                 | P1       | ✓      | `contracts/parser.py`                | Regex-based tag extraction             |
| FR-CTR-003 | XML Output Adapter Normalization       | P1       | ✓      | `contracts/adapters.py`              |                                        |
| FR-CTR-004 | Generic Output Adapter                 | P2       | ✓      |                                      | Plain text extraction                  |
| FR-CTR-005 | Provider Adapter Registry              | P1       | ✓      | `contracts/adapters.py`              | ADAPTER_REGISTRY                       |
| FR-CTR-006 | Contract Telemetry and Drift Detection | P1       | ✓      |                                      | contract_telemetry.jsonl               |
| FR-CTR-007 | Telemetry Statistics and KPI           | P2       | ✓      |                                      | get_stats()                            |
| FR-CTR-008 | Normalization Fallback Policy          | P1       | ✓      |                                      | FallbackPolicy                         |
| FR-CTR-009 | Contract Version Registry              | P1       | ✓      |                                      | ContractRegistry                       |
| FR-CTR-010 | Contract Migration Controller          | P2       | ○      |                                      | MigrationController                    |
| FR-CTR-011 | Semantic Validation of CSM Invariants  | P1       | ✓      | `contracts/validation.py`            |                                        |
| FR-CTR-012 | Conformance Test Suite                 | P2       | ✓      | `tests/test_contract_conformance.py` |                                        |
| FR-CTR-013 | Canonical Event Schemas                | P2       | ✓      |                                      | ChunkEvent, EvidenceEvent, PolicyEvent |

---

## FR-GOV: Governance (7 FRs)

| ID         | Title                                 | Priority | Status | Implementation                   | Notes |
| ---------- | ------------------------------------- | -------- | ------ | -------------------------------- | ----- |
| FR-GOV-001 | Cost Estimation per Run               | P1       | ✓      | `governance/costs.py`            |       |
| FR-GOV-002 | Daily Cost Aggregation by Owner       | P1       | ○      |                                  |       |
| FR-GOV-003 | Input Guardrail - Prompt Length       | P1       | ✓      | `governance/input_guardrails.py` |       |
| FR-GOV-004 | Input Guardrail - Blocklist Patterns  | P1       | ✓      |                                  |       |
| FR-GOV-005 | Input Guardrail - Allowlists          | P1       | ✓      |                                  |       |
| FR-GOV-006 | Input Guardrail - CWD Restriction     | P1       | ○      |                                  |       |
| FR-GOV-007 | Guardrails from Environment Variables | P1       | ✓      |                                  |       |

---

## FR-EXE: Execution (10 FRs)

| ID         | Title                                    | Priority | Status | Implementation         | Notes                           |
| ---------- | ---------------------------------------- | -------- | ------ | ---------------------- | ------------------------------- |
| FR-EXE-001 | Run Metadata Model                       | P1       | ✓      |                        |                                 |
| FR-EXE-002 | Run Registry with Hash-Chained Audit     | P1       | ✓      | `execution.py`         |                                 |
| FR-EXE-003 | Run Registry Schema Versioning           | P1       | ○      |                        |                                 |
| FR-EXE-004 | Run State Tracking                       | P1       | ✓      |                        | Running/Paused/Completed/Failed |
| FR-EXE-005 | Idempotency Token Lookup                 | P1       | ○      |                        |                                 |
| FR-EXE-006 | Trust Score Calibration                  | P1       | ○      |                        |                                 |
| FR-EXE-007 | Checkpoint Registry for DAG State        | P1       | ○      |                        |                                 |
| FR-EXE-008 | PolicyEngine with OPA Integration        | P1       | ✓      | `governance/policy.py` |                                 |
| FR-EXE-009 | Critical Lane and Production Trust Gates | P1       | ○      |                        |                                 |
| FR-EXE-010 | Trust Boundary Validation                | P1       | ○      |                        | Environment transitions         |

---

## FR-MOD: Models (6 FRs)

| ID         | Title                       | Priority | Status | Implementation | Notes            |
| ---------- | --------------------------- | -------- | ------ | -------------- | ---------------- |
| FR-MOD-001 | Static Model Catalog        | P1       | ✓      |                | Route resolution |
| FR-MOD-002 | Model Alias Normalization   | P1       | ✓      |                |                  |
| FR-MOD-003 | Model Blacklist Enforcement | P1       | ○      |                |                  |
| FR-MOD-004 | Dynamic Model Scraping      | P1       | ✓      |                | With cache       |
| FR-MOD-005 | Proxy Model Classification  | P1       | ○      |                | By provider      |
| FR-MOD-006 | Route Contract Metadata     | P1       | ○      |                | For auditing     |

---

## FR-PLN: Planning (3 FRs)

| ID         | Title                          | Priority | Status | Implementation | Notes         |
| ---------- | ------------------------------ | -------- | ------ | -------------- | ------------- |
| FR-PLN-001 | PERT Forward Pass Analysis     | P1       | ○      |                |               |
| FR-PLN-002 | Resource Contention Simulation | P1       | ○      |                |               |
| FR-PLN-003 | Continuity Risk Scoring        | P1       | ○      |                | Shift handoff |

---

## FR-CLI: CLI (5 FRs)

| ID         | Title                            | Priority | Status | Implementation | Notes             |
| ---------- | -------------------------------- | -------- | ------ | -------------- | ----------------- |
| FR-CLI-001 | CLI Command Framework via Typer  | P1       | ✓      |                |                   |
| FR-CLI-002 | Working Directory Resolution     | P1       | ✓      |                | With caching      |
| FR-CLI-003 | Agent and Model Resolution       | P1       | ✓      |                | For runs          |
| FR-CLI-004 | Time Constraint Budget Injection | P1       | ○      |                |                   |
| FR-CLI-005 | Session Continuation             | P1       | ○      |                | Multi-hop context |

---

## FR-MCP: MCP Server (4 FRs)

| ID         | Title                                 | Priority | Status | Implementation | Notes |
| ---------- | ------------------------------------- | -------- | ------ | -------------- | ----- |
| FR-MCP-001 | FastMCP Server with Tool Registration | P1       | ✓      |                |       |
| FR-MCP-002 | MCP Server Middleware Stack           | P1       | ○      |                |       |
| FR-MCP-003 | MCP Client Configuration Management   | P1       | ✓      |                |       |
| FR-MCP-004 | MCP Server CWD and Owner Elicitation  | P1       | ○      |                |       |

---

## FR-CFG: Configuration (6 FRs)

| ID         | Title                             | Priority | Status | Implementation | Notes                        |
| ---------- | --------------------------------- | -------- | ------ | -------------- | ---------------------------- |
| FR-CFG-001 | Pydantic Settings                 | P1       | ✓      |                | Environment variable binding |
| FR-CFG-002 | Agent-Specific Default Model      | P1       | ✓      |                |                              |
| FR-CFG-003 | Timeout Configuration             | P1       | ✓      |                | Agent-specific overrides     |
| FR-CFG-004 | Retention Policy Configuration    | P1       | ○      |                | Tiered                       |
| FR-CFG-005 | Normalization and Contract Policy | P1       | ○      |                |                              |
| FR-CFG-006 | Startup Configuration Validation  | P1       | ✓      |                | Fail-fast                    |

---

## FR-OPS: Operations (3 FRs)

| ID         | Title                                  | Priority | Status | Implementation | Notes                            |
| ---------- | -------------------------------------- | -------- | ------ | -------------- | -------------------------------- |
| FR-OPS-001 | Operation Taxonomy Mapping             | P1       | ✓      |                |                                  |
| FR-OPS-002 | Multi-Agent Orchestration Mode Catalog | P1       | ✓      |                |                                  |
| FR-OPS-003 | Mode Selection Policy                  | P1       | ○      |                | Based on risk/urgency/confidence |

---

## FR-INS: Install (4 FRs)

| ID         | Title                              | Priority | Status | Implementation | Notes                      |
| ---------- | ---------------------------------- | -------- | ------ | -------------- | -------------------------- |
| FR-INS-001 | Source-to-Destination Mapping      | P1       | ✓      |                | Claude and Factory targets |
| FR-INS-002 | Smart Copy with Modification Time  | P1       | ✓      |                |                            |
| FR-INS-003 | Exclusion of Cache/Transient       | P1       | ✓      |                |                            |
| FR-INS-004 | Symlink Mode for Editable Installs | P1       | ○      |                |                            |

---

## FR-OUT: Output Parser (5 FRs)

| ID         | Title                                 | Priority | Status | Implementation | Notes             |
| ---------- | ------------------------------------- | -------- | ------ | -------------- | ----------------- |
| FR-OUT-001 | JSONL Stream Extraction               | P1       | ✓      |                |                   |
| FR-OUT-002 | Plain Text Noise Stripping            | P1       | ✓      |                |                   |
| FR-OUT-003 | Think Tag Removal                     | P1       | ✓      |                |                   |
| FR-OUT-004 | ParseResult with Error Classification | P1       | ✓      |                |                   |
| FR-OUT-005 | Condensed Output Extraction           | P1       | ✓      |                | extract_condensed |

---

## FR-FED: Policy Federation (6 FRs)

| ID         | Title                           | Priority | Status | Implementation             | Notes            |
| ---------- | ------------------------------- | -------- | ------ | -------------------------- | ---------------- |
| FR-FED-001 | Hierarchical Policy Namespace   | P1       | ✓      | `governance/federation.py` |                  |
| FR-FED-002 | Federated Policy Resolution     | P1       | ✓      |                            |                  |
| FR-FED-003 | Jurisdiction Profile Mapping    | P1       | ○      |                            |                  |
| FR-FED-004 | Cross-Namespace Consent Relay   | P1       | ✓      |                            |                  |
| FR-FED-005 | Policy Conflict Arbitration     | P1       | ○      |                            |                  |
| FR-FED-006 | Federation Health Observability | P1       | ○      |                            | Drift monitoring |

---

## FR-EXIT: Exit Codes (1 FR)

| ID          | Title                   | Priority | Status | Implementation | Notes                   |
| ----------- | ----------------------- | -------- | ------ | -------------- | ----------------------- |
| FR-EXIT-001 | Standardized Exit Codes | P1       | ✓      | `cli/`         | Human-readable messages |

---

## FR-HAX: Harmonious Agent Experience (5 FRs)

| ID         | Title                             | Priority | Status | Implementation | Notes                         |
| ---------- | --------------------------------- | -------- | ------ | -------------- | ----------------------------- |
| FR-HAX-001 | Unified Prompt Queue (UPQ)        | P1       | ○      |                | `.thegent/prompt_queue.jsonl` |
| FR-HAX-002 | Cross-Platform Rules Sync         | P1       | ✓      |                | `rules sync` command          |
| FR-HAX-003 | Pareto-Optimal Model Routing      | P1       | ✓      |                | Via LiteLLM                   |
| FR-HAX-004 | Universal Memory Provider         | P1       | ✓      |                | Supermemory.ai                |
| FR-HAX-005 | Automated Documentation Gardening | P1       | ✓      |                | Gardener agent                |

---

## Summary

| Status        | Count  | Percentage |
| ------------- | ------ | ---------- |
| ✓ Implemented | 58     | 64%        |
| ○ Pending     | 33     | 36%        |
| ~ Partial     | 0      | 0%         |
| **Total**     | **91** | **100%**   |

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index
- [FUNCTIONAL_REQUIREMENTS.md](../FUNCTIONAL_REQUIREMENTS.md) — full FR definitions
- [PRD.md](../PRD.md) — product requirements
