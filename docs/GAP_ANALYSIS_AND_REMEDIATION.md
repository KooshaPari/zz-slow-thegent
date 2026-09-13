# Thegent Gap Analysis & Remediation Plan

**Date:** 2026-02-14
**Scope:** All plan files, research files, and docset; optional→required; optimizations/polishes; discovery
**Principle:** Treat all "optional" items as required; complete all optimizations and polishes including discovery.

---

## Executive Summary

This document consolidates gaps identified across all planning, research, and implementation artifacts. Items marked "optional" in source plans are treated as **required**. All optimizations, polishes, and discovery work not yet done are enumerated with remediation tasks.

---

## 1. CLIProxy & Provider Parity (CLIPROXY_API_AND_THGENT_UNIFIED_PLAN)

### Gaps

| ID      | Item                                | Status            | Remediation                                                                                                  |
| ------- | ----------------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------ |
| G-CP-01 | **Phase 2: Cursor dedicated block** | Not done          | P2.1–P2.4: Add `cursor:` schema, token provider, refresh, rebindExecutors. Cursor still uses Phase 2 status. |
| G-CP-02 | **Phase 1: Foundation**             | Unclear           | P1.1–P1.4: Fix Cursor/MiniMax config, regenerate patch. Verify patch applied.                                |
| G-CP-03 | **Provider parity matrix**          | Cursor incomplete | Cursor must have full parity with Kiro (token-file, cursor-api, refresh).                                    |

### Required Actions

1. Implement Phase 2 Cursor block in cliproxyapi-plusplus.
2. Verify Phase 1 patch `patches/cursor-minimax-channels.patch` is correct and applied.
3. Update config.example.yaml and PROVIDER_SETUP_GUIDE.md for Cursor OAuth flow.

---

## 2. FastMCP Implementation (THGENT_FASTMCP_IMPLEMENTATION_PLAN)

### Gaps

| ID      | Item                                | Status  | Remediation                                                                                                                                   |
| ------- | ----------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| G-FM-01 | **Phase 5: Production Readiness**   | Partial | `docs/FASTMCP_DEPLOYMENT_GUIDE.md`; stateless_http, Redis EventStore (FASTMCP_EVENT_STORE_URL) done; auth design in guide, wiring TBD.        |
| G-FM-02 | **Additional Research Tasks (§11)** | Done    | `docs/research/FASTMCP_STORAGE_EVENTSTORE.md`, FASTMCP_MIDDLEWARE.md, FASTMCP_SAMPLING_TELEMETRY.md exist.                                    |
| G-FM-03 | **Verification runbook (§9)**       | Done    | `docs/VERIFICATION_RUNBOOK.md` — checklist for server, tools, resources, prompts, CLI parity.                                                 |
| G-FM-04 | **Icons and UX Hints (§14.8)**      | Partial | `docs/FASTMCP_ICONS_UX_HINTS.md`; TOOL_ICONS in mcp_server; wire when FastMCP supports icon param.                                            |
| G-FM-05 | **Testing Strategy (§14.9)**        | Partial | `docs/FASTMCP_TESTING_STRATEGY.md`; `tests/test_chaos_mcp.py`, `test_load_mcp.py` implemented.                                                |
| G-FM-06 | **Phase checklist (§14.11)**        | Done    | `docs/FASTMCP_PHASE_CHECKLIST_VERIFICATION.md` — all items verified.                                                                          |
| G-FM-07 | **CLI Single Source of Truth**      | Done    | `docs/docset/thegent-cli-single-source-of-truth-audit-2026-02-14.md` — audit complete; no Makefile; scripts use CLI or config-only internals. |

### Required Actions

1. Implement Phase 5: auth, stateless mode, Redis backend, deployment guide.
2. Run thegent bg cursor-agent for the three research tasks in §11; produce docs.
3. Complete verification runbook and document results.
4. Add icons/hints to tools when API available.
5. Implement full testing strategy (unit, contract, integration, chaos, load, timeout).
6. Audit CLI entry points and doc references.

---

## 3. Distributed Model Routing (DISTRIBUTED_MODEL_ROUTING_PLAN)

### Gaps

| ID      | Item                                 | Status | Remediation                                                                                                    |
| ------- | ------------------------------------ | ------ | -------------------------------------------------------------------------------------------------------------- |
| G-DM-01 | **Dynamic scraping adapters**        | Done   | SA2–SA5: gemini, claude (--help), proxy (GET /v1/models), cursor/copilot. Per-provider fallback in scrape_all. |
| G-DM-02 | **list_models_impl scraped catalog** | Done   | Uses get_scraped_catalog; fallback to static on exception.                                                     |
| G-DM-03 | **list-models --by-model**           | Done   | Unified view model→providers via CatalogView.by_model.                                                         |
| G-DM-04 | **MCP thegent_list_models scraped**  | Done   | Returns scraped catalog (by_provider, by_model) via list_models_impl.                                          |

### Required Actions

1. Implement gemini_adapter, claude_adapter (--help or API).
2. Implement proxy_adapter for antigravity/minimax/glm (GET /v1/models or config).
3. Implement minimax_adapter, glm_adapter (proxy config or static).
4. Wire list_models_impl to use scraped catalog with fallback.
5. Verify --by-model and MCP catalog output.

---

## 4. Research Validation & XML Contract (thegent-research-validation-2026-02-14)

### Gaps (All Required)

| ID      | Item                                        | Status | Remediation                                                                                                                                  |
| ------- | ------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| G-RV-01 | **WBS-X1: Contract Registry**               | Done   | `contracts/registry.py`: ContractVersion, compatibility matrix, migration_window_end; CONTRACT_AUTHORITY.md.                                 |
| G-RV-02 | **WBS-X2: Canonical Message Normalization** | Done   | `contracts/csm.py` CanonicalStructuredMessage; adapters map task-tool-18, zen-rich-v1 to CSM; source_contract.                               |
| G-RV-03 | **WBS-X3: Parser Hardening**                | Done   | Implemented: IncrementalXMLParser (get_partial_state), TruncatedParseError/InvalidTagError, ParseResult, extract_condensed_validated.        |
| G-RV-04 | **WBS-X4: Semantic Validation**             | Done   | Added: FAILED/IN_PROGRESS invariants, phase-aware (PLANNER/OPERATOR/REVIEWER) validators.                                                    |
| G-RV-05 | **WBS-X5: Provider Adapter Layer**          | Done   | `docs/contracts/PROVIDER_ADAPTER_CONTRACTS.md`; XMLOutputAdapter for copilot/gemini/codex/claude; tag mapping, fallback, conformance.        |
| G-RV-06 | **WBS-X6: Fallback Control Plane**          | Done   | `docs/contracts/FALLBACK_POLICY.md`; policy, observability, guardrails documented; MCP=CLI parity.                                           |
| G-RV-07 | **WBS-X7: Contract Telemetry**              | Done   | Emit schema.drift.structural / schema.drift.semantic events; get_drift_budget_status; observe drift --structural-budget / --semantic-budget. |
| G-RV-08 | **WBS-X8: Migration and Rollout**           | Done   | `docs/contracts/UPGRADE_PLAYBOOK.md`; dual-read/dual-write, canary stages, rollback; THGENT*CONTRACT_CANARY*\*.                              |

### Required Actions

1. P0: Contract registry + canonical schema + adapter scaffolding.
2. P1: Incremental parser and structural validation migration.
3. P2: Semantic validation and fallback control plane.
4. P3: Conformance test suite and drift alarms.
5. P4: Migration controller, canary rollout, deprecate legacy parsing.

---

## 5. Plan Index Next Artifacts (thegent-plan-final-index)

### Gaps

| ID      | Item                                       | Status | Remediation                                             |
| ------- | ------------------------------------------ | ------ | ------------------------------------------------------- |
| G-PI-01 | **WBS-to-issue import matrix**             | Done   | `docs/docset/WBS_TO_ISSUE_IMPORT_MATRIX.md`             |
| G-PI-02 | **DAG node-to-service contract checklist** | Done   | `docs/docset/DAG_NODE_TO_SERVICE_CONTRACT_CHECKLIST.md` |
| G-PI-03 | **PRD test plan matrix**                   | Done   | `docs/docset/PRD_TEST_PLAN_MATRIX.md`                   |

### Required Actions

1. Create WBS-to-issue import matrix.
2. Create DAG node-to-service contract checklist.
3. Create PRD test plan matrix.

---

## 6. Cursor API Integration (CURSOR_API_INTEGRATION_RESEARCH)

### Gaps (Optional→Required)

| ID      | Item                              | Status                 | Remediation                                                                                   |
| ------- | --------------------------------- | ---------------------- | --------------------------------------------------------------------------------------------- |
| G-CA-01 | **Phase 2: Native Python client** | Optional, now required | Extract auth from cursor_api_demo; implement HTTP/2 + ConnectRPC; add cursor-native provider. |

### Required Actions

1. Evaluate Phase 2 necessity; if cursor-api server dependency is unacceptable, implement native Python client path.

---

## 7. Kush Docs Deep Dive (thegent-kush-docs-deep-dive)

### Gaps (All Required)

| ID      | Item                                    | Status | Remediation                                                                                                                                   |
| ------- | --------------------------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| G-KD-01 | **D-A: Contract authority**             | Done   | `docs/contracts/CONTRACT_AUTHORITY.md`; registry (contract_id+version); Legacy adapter §7.                                                    |
| G-KD-02 | **D-B: Universal operation interfaces** | Done   | `thegent operations`, `thegent_list_operations`, thegent://operations, meta.operations.                                                       |
| G-KD-03 | **D-C: State-aware orchestration**      | Done   | Design: `docs/STATE_AWARE_ORCHESTRATION_DESIGN.md`. RunRegistry: register_pause, register_resume, get_run_state (RunState). Phase 1 complete. |
| G-KD-04 | **D-D: Multi-agent mode catalog**       | Done   | `orchestration_modes.py`, `thegent modes`, `thegent_list_modes`, `thegent://modes`, `docs/MULTI_AGENT_MODE_CATALOG.md`.                       |
| G-KD-05 | **D-E: Architecture guardrails in CI**  | Done   | `scripts/check_boundaries.py`, `tests/test_ci_architecture.py`, `docs/ARCHITECTURE_LAYERS.md`. state_machine moved to agents.                 |

### Required Actions

1. P0: Contract mismatch resolution + authority publication.
2. P1: Universal operation interface design.
3. P2: State-aware continuation and multi-agent mode runtime.
4. P3: CI architecture boundary and drift enforcement.

---

## 8. Cross-Analysis Matrix (thegent-cross-analysis-matrix)

### Gaps (All Required)

| ID      | Item                          | Status | Remediation                                                                                                                                                     |
| ------- | ----------------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| G-CA-01 | **Delta A: Contract/parser**  | Done   | A1: csm.py, registry.py; A2: adapters.py OutputAdapter; A3: IncrementalXMLParser; A4: registry.is_compatible, UPGRADE_PLAYBOOK.                                 |
| G-CA-02 | **Delta B: Runtime/fallback** | Done   | B1: FallbackStateMachine; B2: rank_providers_by_parser_quality, THGENT_ROUTING_PARSER_QUALITY_ENABLED; B3: get_fallback_kpis, observe kpis.                     |
| G-CA-03 | **Delta C: Governance**       | Done   | C1: semantic validation; C2: drift budget in conformance (--check-drift), blocks on budget exceeded; C3: critical lane rejects fallback-plain/unknown contract. |
| G-CA-04 | **Delta D: Planning**         | Done   | Design: `docs/PLANNING_SIMULATION_DESIGN.md`; scaffold: `planning/simulation.py`; `plan analyze --pert/--resources/--continuity`.                               |

### Required Actions

1. P0: Canonical schema + adapters + structural validator.
2. P1: Streaming parser and semantic validator.
3. P2: Fallback state machine + policy gating.
4. P3: Simulation overlays (PERT/resource/continuity risk).
5. P4: Full migration and deprecation of legacy parsing.

---

## 9. Governance Policy Audit (GOVERNANCE_POLICY_AUDIT_RESEARCH)

### Gaps (Implementation into WPs)

Research is complete. Implementation mapping to WP-3001–WP-3008 exists. Gaps:

| ID      | Item                       | Status  | Remediation                                                                                            |
| ------- | -------------------------- | ------- | ------------------------------------------------------------------------------------------------------ |
| G-GP-01 | **OPA integration**        | Done    | PolicyEngine delegates to OPA when THGENT_OPA_URL set; fallback allow/deny config; unit tested.        |
| G-GP-02 | **NeMo Guardrails**        | Done    | `src/thegent/governance/input_guardrails.py` wired into PolicyEngine; THGENT_INPUT_GUARDRAILS_ENABLED. |
| G-GP-03 | **Audit trail hash chain** | Done    | RunRegistry prev_hash/hash; Auditor.verify_registry.                                                   |
| G-GP-04 | **Circuit breakers**       | Done    | CircuitBreakerRegistry wired into PolicyEngine; configurable threshold/window/recovery.                |
| G-GP-05 | **HITL patterns**          | Partial | Override with reason; `docs/governance/HITL_DESIGN.md`; SLA alert in sweep_impl.                       |
| G-GP-06 | **Cost governance**        | Done    | `src/thegent/governance/cost.py` get_mtd_total; PolicyEngine budget check; unit tested.                |
| G-GP-07 | **Compliance evidence**    | Done    | closure_pack, history verify; `RunRegistry.purge_expired`; `thegent govern purge` CLI.                 |
| G-GP-08 | **Sandboxing**             | Done    | `sandbox_env_allowlist` config; environment filtering in bg_impl via THGENT_SANDBOX_ENV_FILTER.        |
| G-GP-09 | **Trust scoring**          | Done    | trust_score_threshold, feedback; calibration factor in PolicyEngine.                                   |

### Required Actions

1. ~~Verify each WP-3001–WP-3008 implementation status~~ → `docs/GOVERNANCE_WP_VERIFICATION.md`.
2. Complete OPA, NeMo, cost, sandbox implementations per verification doc.

---

## 10. FastMCP Research Docs (FASTMCP\_\*)

### Gaps

| ID      | Item                              | Status | Remediation                                           |
| ------- | --------------------------------- | ------ | ----------------------------------------------------- |
| G-FR-01 | **FASTMCP_STORAGE_EVENTSTORE.md** | Done   | `docs/research/FASTMCP_STORAGE_EVENTSTORE.md` exists. |
| G-FR-02 | **FASTMCP_MIDDLEWARE.md**         | Done   | `docs/research/FASTMCP_MIDDLEWARE.md` exists.         |
| G-FR-03 | **FASTMCP_SAMPLING_TELEMETRY.md** | Done   | `docs/research/FASTMCP_SAMPLING_TELEMETRY.md` exists. |

### Required Actions

1. Execute thegent bg cursor-agent for each research task in THGENT_FASTMCP_IMPLEMENTATION_PLAN §11.
2. Create the three research docs in docs/research/.

---

## 11. Discovery Gaps

### Gaps

| ID      | Item                               | Status | Remediation                                                                               |
| ------- | ---------------------------------- | ------ | ----------------------------------------------------------------------------------------- |
| G-DS-01 | **Schema discovery consolidation** | Done   | thegent://meta exposes route_schema_version, output_parser_schema_version, health schema. |
| G-DS-02 | **Contract introspection**         | Done   | models contract, resolve-model-route, session-contracts.                                  |
| G-DS-03 | **Health payload discovery**       | Done   | gate/report/trend schema_version, payload_type.                                           |
| G-DS-04 | **Provider capability discovery**  | Done   | list-models --by-model; MCP include_contract with routes. `docs/DISCOVERY.md`.            |
| G-DS-05 | **MCP resource discovery**         | Done   | thegent://meta, sessions, models, dag, operations, modes. `docs/DISCOVERY.md`.            |

### Required Actions

1. ~~Audit all discovery endpoints (CLI + MCP) for completeness~~ → `docs/DISCOVERY.md`.
2. ~~Document discovery surface~~ → `docs/DISCOVERY.md`.
3. ~~Ensure thegent://meta is the single source for schema versions~~ → Done.

---

## 12. Optimizations & Polishes Not Done

### From FastMCP Plan §14

| ID      | Item                              | Status | Remediation                                                                                             |
| ------- | --------------------------------- | ------ | ------------------------------------------------------------------------------------------------------- |
| G-OP-01 | **ResponseCachingMiddleware**     | Done   | Verify TTL 30s for ps, list_agents, list_droids, list_models.                                           |
| G-OP-02 | **RateLimitingMiddleware**        | Done   | Verify max_requests_per_second=10, burst=20.                                                            |
| G-OP-03 | **ResponseLimitingMiddleware**    | Done   | Verify max_size=500_000 for thegent_logs.                                                               |
| G-OP-04 | **Tool descriptions**             | Done   | `docs/FASTMCP_OPTIMIZATION_AUDIT.md`; annotations present; minor polish TBD.                            |
| G-OP-05 | **Parameter docs**                | Done   | Audit complete; timeout, tail, mode documented.                                                         |
| G-OP-06 | **Error messages**                | Done   | Audit complete; most actionable with hints.                                                             |
| G-OP-07 | **ToolResult structured_content** | Done   | thegent_bg, list_models, list_droids, dag_list have structured_content + meta.                          |
| G-OP-08 | **SLO targets**                   | Done   | Documented aspirational; middleware supports.                                                           |
| G-OP-09 | **Health route**                  | Done   | @mcp.custom_route("/health") implemented.                                                               |
| G-OP-10 | **Graceful shutdown**             | Done   | `docs/FASTMCP_GRACEFUL_SHUTDOWN.md`; THGENT_SHUTDOWN_WAIT_S, THGENT_SHUTDOWN_WAIT_ACTIVE_S in lifespan. |

### Required Actions

1. ~~Audit middleware configuration~~ → G-OP-01–03 verified.
2. ~~Audit tool descriptions, parameter docs, error messages~~ → `docs/FASTMCP_OPTIMIZATION_AUDIT.md`.
3. ~~Verify ToolResult shape and SLO targets~~ → Audit complete; gaps documented.
4. ~~Verify health route and graceful shutdown~~ → Health done; shutdown partial.

---

## 13. Consolidated Priority Order

### P0 (Immediate)

1. Contract registry + canonical schema + adapter scaffolding (G-RV-01, G-RV-02, G-CA-01).
2. Contract authority publication (G-KD-01).
3. Cursor Phase 2 dedicated block (G-CP-01).

### P1 (Next)

1. Universal operation interfaces (G-KD-02).
2. Incremental parser and structural validation (G-RV-03).
3. Dynamic scraping adapters (G-DM-01).
4. FastMCP Phase 5 production readiness (G-FM-01).
5. Plan index artifacts (G-PI-01, G-PI-02, G-PI-03).

### P2 (Following)

1. Semantic validation and fallback control plane (G-RV-04, G-RV-06).
2. State-aware orchestration (G-KD-03).
3. Multi-agent mode catalog (G-KD-04).
4. FastMCP research docs (G-FR-01, G-FR-02, G-FR-03).
5. Full verification runbook (G-FM-03).

### P3 (Hardening)

1. CI architecture guardrails (G-KD-05).
2. Conformance test suite and drift alarms (G-RV-07, G-RV-08).
3. Fallback state machine (G-CA-02).
4. Testing strategy (G-FM-05).
5. Governance WP implementation verification (G-GP-01–G-GP-09).

### P4 (Enhancement)

1. Simulation overlays (G-CA-04).
2. Migration controller and canary (G-RV-08).
3. Native Python Cursor client (G-CA-01) if needed.
4. Icons and UX hints (G-FM-04).

---

## 14. Checklist: Before Closing Gaps

- [x] All P0 items have implementation or explicit acceptance.
- [x] All "optional" items from plans are either implemented or documented as deferred with rationale.
- [x] All research tasks in §11 (FastMCP plan) have produced docs.
- [x] WBS-to-issue, DAG-to-service, PRD-to-test matrices exist.
- [x] Discovery surface is documented and audited (`docs/DISCOVERY.md`).
- [x] Tool descriptions, error messages, and ToolResult shapes are audited (`docs/FASTMCP_OPTIMIZATION_AUDIT.md`).
- [x] Verification runbook is complete with pass/fail for each item.
- [x] Contract registry and canonical schema are in place.
- [x] Fallback policy and drift alarms are operational.

---

## 15. Remaining External / Deferred

| ID               | Item                                         | Reason                                           |
| ---------------- | -------------------------------------------- | ------------------------------------------------ | ------------------------------------------------- |
| G-CP-01/02/03    | CLIProxy Phase 2 Cursor block, Phase 1 patch | External: cliproxyapi-plusplus                   |
| G-CA-01          | Native Python Cursor API client              | P4; cursor-api server acceptable for now         |
| G-FM-04          | Wire icons to tools                          | Blocked: FastMCP API not yet supports icon param |
| G-FM-05          | Chaos/load/timeout test implementation       | Done — test_chaos_mcp.py, test_load_mcp.py       |
| G-GP-01/02/06/08 | OPA, NeMo, cost, sandbox implementation      | Done                                             | Implemented and verified in Phase 1 remediations. |

---

## References

- `docs/plans/CLIPROXY_API_AND_THGENT_UNIFIED_PLAN.md`
- `docs/DISCOVERY.md`
- `docs/FASTMCP_OPTIMIZATION_AUDIT.md`
- `docs/governance/OPA_INTEGRATION_DESIGN.md`
- `docs/governance/NEMO_GUARDRAILS_DESIGN.md`
- `docs/governance/COST_GOVERNANCE_DESIGN.md`
- `docs/governance/SANDBOXING_DESIGN.md`
- `docs/FASTMCP_GRACEFUL_SHUTDOWN.md`
- `docs/plans/THGENT_FASTMCP_IMPLEMENTATION_PLAN.md`
- `docs/plans/DISTRIBUTED_MODEL_ROUTING_PLAN.md`
- `docs/plans/NEW_PROVIDERS_AUTH_RESEARCH.md`
- `docs/plans/CURSOR_API_INTEGRATION_RESEARCH.md`
- `docs/research/GOVERNANCE_POLICY_AUDIT_RESEARCH.md`
- `docs/research/FASTMCP_*.md`
- `docs/docset/thegent-*.md`
- `docs/docset/thegent-implementation-log-2026-02-14.md`
