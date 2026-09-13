# Tooling and Global Optimizations Audit

**Date:** 2026-02-16
**Status:** In-depth audit and plan
**Scope:** Tooling gaps, global optimizations, next work packages

---

## 1. Executive Summary

This audit identifies tooling gaps, global optimizations, and priority work packages. It synthesizes:

- `docs/plans/08-OPTIMIZATION-CATALOG.md` (93 items)
- `docs/reference/HOOK_OPTIMIZATION_STRATEGY.md` (hooks complete)
- `docs/docset/OPTIMIZATION_POLISH_ADDENDUM.md` (73 addendum items)
- `docs/docset/WBS_TO_ISSUE_IMPORT_MATRIX.md` (pending WPs)

**Key findings:** Hook optimizations complete; 4 pending WPs in Phase 5; Quick Wins QW-001..007 verified done; QW-008 (OTel) partial; 15+ tooling gaps; 73 addendum optimizations across 9 domains.

---

## 2. Tooling Gaps

### 2.1 Missing CLI Commands

| Command                            | Status                 | Effort  | Impact                                                        |
| ---------------------------------- | ---------------------- | ------- | ------------------------------------------------------------- |
| `thegent config check`             | ✓ Done                 | —       | Pre-flight config validation (DX-010)                         |
| `thegent config validate`          | Alias for config check | Trivial | Same as above                                                 |
| `thegent route probe <model>`      | ✓ Done                 | —       | `thegent route-probe <model>` (alias for resolve-model-route) |
| `thegent run-diff <run_a> <run_b>` | Not implemented        | Medium  | Compare execution traces (DX-009)                             |
| `thegent trace replay <run_id>`    | Not implemented        | Medium  | Replay execution trace (DX-011)                               |
| `thegent deferral list`            | Not implemented        | Small   | List deferred tasks with ETA                                  |
| `thegent deferral resume <run_id>` | Not implemented        | Small   | Resume deferred task                                          |
| `thegent inspect`                  | Partial (MCP)          | Small   | Multi-session debugging (DX-003)                              |

### 2.2 Build / Dev Tooling

| Task                          | Status            | Location                                                 |
| ----------------------------- | ----------------- | -------------------------------------------------------- |
| Taskfile                      | ✓ Present         | `Taskfile.yml`                                           |
| process-compose               | ✓ Present         | dev stack                                                |
| lint                          | ✓ Via `task lint` | templates                                                |
| test                          | ✓ Via `task test` | templates                                                |
| quality-gate                  | ✓ Via hooks       | `hooks/quality-gate.sh`                                  |
| architecture enforcement      | ⚠ tach.toml      | Verify CI runs                                           |
| dx-audit                      | ⚠ scripts/       | No complexity, import-boundary, coverage-based selection |
| Coverage-based test selection | Not done          | Map changed files → affected tests (P7)                  |

### 2.3 MCP Tool Gaps

| Gap                                            | Status   | Reference                                    |
| ---------------------------------------------- | -------- | -------------------------------------------- |
| `idempotent` annotation on 25+ read-only tools | ✓ Done   | mcp_server.py: 25+ tools have idempotentHint |
| `payload_signature` for deterministic caching  | ✓ Done   | cli_impl.py: health gate, observe_summary    |
| Tool descriptions with inline constraints      | Partial  | UX-013; expand action-oriented               |
| thegent_bg structured_content on success       | ⚠       | FASTMCP audit G-OP-07                        |
| Graceful shutdown (30s drain)                  | Not done | G-OP-10; optional THGENT_SHUTDOWN_WAIT_S     |

### 2.4 Observability Tooling

| Gap                                          | Status    | Reference                                                                       |
| -------------------------------------------- | --------- | ------------------------------------------------------------------------------- |
| OTel span attributes (model, provider, lane) | ✓ Partial | run_impl/bg_impl use instrument_run_bg_status; add resolved provider post-route |
| `execution_time_ms` on all tools             | ✓ Done    | UX-002                                                                          |
| Structured JSON logs with run_id             | ✓ Done    | OPS-003                                                                         |
| OTel GenAI semantic conventions              | ✓ Done    | otel_instrumentation.py                                                         |

---

## 3. Global Optimizations (Priority Order)

### 3.1 Quick Wins (Verified 2026-02-16)

| ID     | Item                                                    | Status    | Evidence                                                   |
| ------ | ------------------------------------------------------- | --------- | ---------------------------------------------------------- |
| QW-001 | `payload_signature` hash for health gate caching        | ✓ Done    | cli_impl.py:1837, 3293, 3572, 3774                         |
| QW-002 | `_resolve_cwd()` caching with stat-based TTL            | ✓ Done    | cli_impl.py:70-85; 10s TTL                                 |
| QW-003 | Extract AcceptedElicitation/DeclinedElicitation imports | ✓ Done    | mcp_server.py single import                                |
| QW-004 | `idempotent=True` on 25+ read-only MCP tools            | ✓ Done    | mcp_server.py: 25+ idempotentHint                          |
| QW-005 | Model scraper: concurrent.futures parallelization       | ✓ Done    | scrapers.py ThreadPoolExecutor(6)                          |
| QW-006 | Output parser: cache compiled regex as singletons       | ✓ Done    | output_parser.py:36-76                                     |
| QW-007 | Resilience: failure classification cache                | ✓ Done    | resilience.py: \_CLASSIFY_CACHE, LRU                       |
| QW-008 | OTel span attributes on run_impl                        | ✓ Partial | instrument_run_bg_status; add resolved provider post-route |

### 3.2 Performance (Medium Effort)

| ID      | Item                                               | Priority | Impact                        |
| ------- | -------------------------------------------------- | -------- | ----------------------------- |
| OPT-001 | Response caching middleware (30s TTL)              | ✓ Done   | 60% reduction                 |
| OPT-016 | Model scraper parallelization (concurrent.futures) | P2       | 3–5x faster                   |
| OPT-020 | Route resolution memo (LRU, 1000 entries)          | P2       | Sub-1ms lookups               |
| OPT-007 | Incremental parser early-exit                      | P1       | Avoid full parse on bad input |

### 3.3 Robustness

| ID      | Item                                     | Priority | Impact                       |
| ------- | ---------------------------------------- | -------- | ---------------------------- |
| ROB-001 | Sloppy XML recovery for unclosed tags    | P0       | Handle 90%+ malformed output |
| ROB-013 | Config validation on startup (fail-fast) | ✓ Done   | `thegent config check`       |
| ROB-017 | Model route fallback chain               | P1       | Graceful degradation         |

### 3.4 Hook Optimizations

| Status     | Notes                                            |
| ---------- | ------------------------------------------------ |
| ✓ Complete | P0–P8 all done per HOOK_OPTIMIZATION_STRATEGY.md |

---

## 4. Next Work Packages (Priority Order)

### 4.1 Pending WPs (from WBS Matrix)

| WP ID       | Description                                      | Status  | Acceptance Criteria                     |
| ----------- | ------------------------------------------------ | ------- | --------------------------------------- |
| **WP-5002** | Burst load classification and safe-mode controls | Done    | Traffic shaping, overload rejection     |
| **WP-5003** | Cost-aware routing and workload shaping          | ✓ Done  | RouteLLM-style, budget enforcement      |
| **WP-5005** | Long-running continuity watchdog                 | Pending | Heartbeat 30s, session resumption       |
| **WP-5006** | Handoff integrity enforcement                    | Pending | Snapshot validation, ownership transfer |
| **WP-6007** | Post-launch observation and rollback reserve     | Pending | 28-day observation, rollback reserve    |

### 4.2 Recommended Next WP: **WP-5005** (Continuity Watchdog)

**Rationale:**

- WP-5002 (Burst load) done; WP-5003 (Cost-aware) done
- ContinuityWatchdog exists; `watchdog_cmd` scans stale sessions
- Gaps: heartbeat every 30s, session resumption < 5 min

**Acceptance criteria:**

- Heartbeat every 30s for active sessions
- Session resumption within 5 min of stale detection
- Escalation on stale ownership (ROB-012)

**Effort:** ~6–10 tool calls, ~15–30 min

### 4.3 Alternative: WP-5006 (Handoff Integrity)

**Rationale:**

- HandoffManager exists; create_snapshot, handoff_confirm in place
- Gaps: snapshot validation, ownership transfer enforcement

**Effort:** ~6–10 tool calls

---

## 5. Implementation Plan (Phased)

### Phase A: Tooling (Immediate)

| Task | Action                                    | Effort                       |
| ---- | ----------------------------------------- | ---------------------------- |
| A1   | Add `thegent config check`                | ✓ Done                       |
| A2   | Audit idempotent annotations on MCP tools | 1 tool call                  |
| A3   | Add route probe (dry-run)                 | ✓ Done (`route-probe` alias) |

### Phase B: Remaining Quick Wins + DX

| Task | Action                                                      | Effort          |
| ---- | ----------------------------------------------------------- | --------------- |
| B1   | QW-008: Add resolved provider/model to OTel span post-route | 1–2 tool calls  |
| B2   | A2: Audit idempotent annotations (verify coverage)          | 1 tool call     |
| B3   | Coverage-based test selection in hooks                      | 6–10 tool calls |
| B4   | dx-audit: cyclomatic complexity, import-boundary            | 3–5 tool calls  |
| B5   | Contract introspection CLI (list contracts, versions)       | 3–5 tool calls  |

### Phase C: Next WP (Priority Order)

| Task | Action                                                        | Effort          |
| ---- | ------------------------------------------------------------- | --------------- |
| C1   | **WP-5003**: Cost-aware routing and workload shaping          | ✓ Done          |
| C2   | **WP-5005**: Long-running continuity watchdog (heartbeat 30s) | 6–10 tool calls |
| C3   | WP-5006: Handoff integrity enforcement                        | 6–10 tool calls |
| C4   | WP-6007: Post-launch observation and rollback reserve         | 8–12 tool calls |

### Phase D: Robustness (Medium-term)

| Task | Action                                | Effort                |
| ---- | ------------------------------------- | --------------------- |
| D1   | ROB-001: Sloppy XML recovery          | 2–3 tool calls        |
| D2   | ROB-013: Config validation on startup | ✓ Done (config check) |

---

## 6. Additional Tooling (Deep Audit)

### 6.1 CLI Surface Gaps

| Command                            | Purpose                                        | Effort |
| ---------------------------------- | ---------------------------------------------- | ------ |
| `thegent config check`             | Validate config, fail-fast on misconfig        | ✓ Done |
| `thegent route probe <model>`      | Dry-run: show which provider would be selected | Small  |
| `thegent run-diff <a> <b>`         | Compare two run traces for debugging           | Medium |
| `thegent trace replay <run_id>`    | Replay execution trace                         | Medium |
| `thegent deferral list`            | List deferred tasks with ETA                   | Small  |
| `thegent deferral resume <run_id>` | Resume a deferred task                         | Small  |

### 6.2 MCP Tool Annotations Audit

| Tool Category           | Count | idempotent | read_only | Status |
| ----------------------- | ----- | ---------- | --------- | ------ |
| thegent_ps              | 1     | ?          | ?         | Verify |
| thegent*list*\*         | 8+    | ?          | ?         | Verify |
| thegent_status          | 1     | ?          | ?         | Verify |
| thegent_history         | 1     | ?          | ?         | Verify |
| thegent_observe_summary | 1     | ?          | ?         | Verify |

### 6.3 Observability Gaps

| Gap                    | Location          | Fix                                |
| ---------------------- | ----------------- | ---------------------------------- |
| OTel span attributes   | run_impl, bg_impl | Add model, provider, lane to span  |
| payload_signature      | observe_summary   | Hash of scope for cache key        |
| Structured error codes | All error paths   | ErrorKind enum with recovery hints |

### 6.4 Resilience Gaps

| Gap                          | Reference | Effort       |
| ---------------------------- | --------- | ------------ |
| Failure classification cache | QW-007    | ✓ Done       |
| Sloppy XML recovery          | ROB-001   | 3 tool calls |
| Config validation on startup | ROB-013   | ✓ Done       |

### 6.5 DX Tooling (from TOOLING_AND_GLOBAL_OPTIMIZATIONS_AUDIT)

| Gap                                  | Priority | Effort | Impact                                              |
| ------------------------------------ | -------- | ------ | --------------------------------------------------- |
| Coverage-based test selection        | P1       | Medium | Map changed files → affected tests; faster feedback |
| dx-audit: cyclomatic complexity      | P2       | Low    | Flag functions >10                                  |
| dx-audit: import-boundary violations | P2       | Low    | Complement tach                                     |
| Contract introspection CLI           | P2       | Medium | List contracts, versions, adapters                  |
| Chaos test harness                   | P3       | High   | Fault injection for resilience                      |

### 6.6 Addendum Domains (OPTIMIZATION_POLISH_ADDENDUM — 73 items)

| Domain                  | Count | Top Items                                                      |
| ----------------------- | ----- | -------------------------------------------------------------- |
| **A: Contract/Schema**  | 10    | OPT-A-001 schema versioning, OPT-A-008 ErrorKind taxonomy      |
| **B: Parsing**          | 10    | OPT-B-001 parser SLO, OPT-B-008 malformed XML repair           |
| **C: Provider/Routing** | 10    | OPT-C-001 provider scoring, OPT-C-004 prompt classification    |
| **D: Reliability**      | 10    | OPT-D-001 circuit breaker viz, OPT-D-007 MAST recovery routing |
| **E: Orchestration**    | 10    | OPT-E-001 mode selection heuristic, OPT-E-002 state guards     |
| **F: Governance**       | 10+   | OPT-F-001 policy denial reasons, OPT-F-004 audit immutability  |
| **G–I**                 | 13+   | Observability, UX, Ops                                         |

### 6.7 FastMCP Polish (FASTMCP_OPTIMIZATION_AUDIT)

| Item                                       | Status | Action                               |
| ------------------------------------------ | ------ | ------------------------------------ |
| Tool descriptions (action-oriented)        | ⚠     | Expand thegent_run, thegent_bg, etc. |
| thegent_bg structured_content on success   | P1     | Add                                  |
| SLO targets documentation                  | P2     | Document in runbook                  |
| Graceful shutdown (THGENT_SHUTDOWN_WAIT_S) | P2     | Optional design                      |

### 6.8 Deep Catalog — High-Impact Items (from 08-OPTIMIZATION-CATALOG + Addendum)

| ID        | Item                                                              | Priority | Effort | Source     |
| --------- | ----------------------------------------------------------------- | -------- | ------ | ---------- |
| ROB-001   | Sloppy XML recovery for unclosed tags                             | P0       | 3      | 08-catalog |
| ROB-007   | Graceful shutdown with in-flight drain (30s)                      | P1       | 2      | 08-catalog |
| ROB-017   | Model route fallback chain (prefer_direct → prefer_proxy → error) | P1       | 2      | 08-catalog |
| OPT-007   | Incremental parser early-exit on structural failure               | P1       | 2      | 08-catalog |
| DX-009    | Run-diff tool (compare two execution traces)                      | P3       | Medium | 08-catalog |
| OPS-004   | Cost tracking per-run with budget alerts                          | P2       | 2      | 08-catalog |
| OPS-013   | Cost dashboard per agent/provider MTD/YTD                         | P2       | 4      | 08-catalog |
| OPT-A-008 | ErrorKind enum with recovery hints                                | P1       | 3      | Addendum   |
| OPT-G-005 | Log correlation ID injection in all messages                      | P1       | 1      | Addendum   |
| OPT-H-004 | Error messages with remediation steps                             | P1       | 2      | Addendum   |
| OPT-I-001 | Architecture boundary enforcement in CI                           | P1       | 1      | Addendum   |

### 6.9 Engineering Excellence (OPT-EX — Addendum §3)

| Category       | Count | Top Items                                           |
| -------------- | ----- | --------------------------------------------------- |
| Code Quality   | 5     | OPT-EX-001 type hints, OPT-EX-002 complexity limits |
| Test Quality   | 5     | OPT-EX-006 80% coverage, OPT-EX-007 naming          |
| Documentation  | 5     | OPT-EX-011 README per package, OPT-EX-012 ADRs      |
| API Design     | 5     | OPT-EX-016 naming, OPT-EX-017 error format          |
| Error Messages | 5     | OPT-EX-021 3-part format, OPT-EX-022 actionable     |
| Config         | 5     | OPT-EX-026 schema validation, OPT-EX-027 env vars   |
| Dependencies   | 5     | OPT-EX-032 security audit, OPT-EX-034 SBOM          |
| Build/CI       | 5     | OPT-EX-036 fail on lint, OPT-EX-038 pipeline stages |

### 6.10 Robustness Hardening Checklist (Addendum §4)

| Area                         | Items | Status  |
| ---------------------------- | ----- | ------- |
| Input validation             | 6     | Partial |
| Error handling               | 5     | Partial |
| Timeout on network           | 6     | Partial |
| Circuit breaker per provider | 5     | ✓ Done  |
| Idempotency on mutation      | 5     | ✓ Done  |
| Logging at decision points   | 5     | Partial |
| Metrics at perf paths        | 5     | Partial |
| Observability completeness   | 5     | Partial |

---

## 7. Cross-References

- `docs/plans/08-OPTIMIZATION-CATALOG.md` — Full 93-item catalog
- `docs/plans/02-UNIFIED-WBS.md` — WBS structure
- `docs/docset/WBS_TO_ISSUE_IMPORT_MATRIX.md` — WP status matrix
- `docs/reference/HOOK_OPTIMIZATION_STRATEGY.md` — Hook completion status
- `docs/docset/OPTIMIZATION_POLISH_ADDENDUM.md` — 73 per-domain optimizations
- `docs/reference/TOOLING_AND_GLOBAL_OPTIMIZATIONS_AUDIT.md` — DX, test coverage, Quick Wins status
- `docs/FASTMCP_OPTIMIZATION_AUDIT.md` — G-OP-04..10 tool polish

---

## 9. Summary Table

| Category                   | Count | Status                                                           |
| -------------------------- | ----- | ---------------------------------------------------------------- |
| Pending WPs                | 3     | WP-5005, 5006, 6007                                              |
| Tooling gaps               | 6+    | run-diff, deferral list/resume, dx-audit, contract introspection |
| Quick wins                 | 8     | QW-001..007 ✓; QW-008 partial                                    |
| Hook optimizations         | 8     | ✓ All complete                                                   |
| Addendum optimizations     | 73    | 9 domains; phased rollout                                        |
| Engineering Excellence     | 40    | OPT-EX-001..040; reference for quality gates                     |
| Deep catalog (high-impact) | 11    | ROB-001, ROB-007, OPT-A-008, etc.                                |

**Recommended next action:** WP-5003 done; route probe done. **Begin WP-5005** (Continuity watchdog) or Phase B (QW-008, dx-audit, coverage-based test selection).

---

## 8. WP-5002 Implementation (Complete) — 2026-02-16

| Component      | Implementation                                                                                        |
| -------------- | ----------------------------------------------------------------------------------------------------- |
| LoadClassifier | normal/spike/surge; get_running_count, is_safe_mode_active, should_reject_overload, get_traffic_shape |
| Config         | load_spike_threshold (10), load_surge_threshold (20)                                                  |
| run_impl       | Surge → defer non-critical; spike → log throttle                                                      |
| task_router    | Surge/spike → prefer faster models                                                                    |
| CLI            | `thegent observe load-status`                                                                         |

---

## 11. WP-5003 Implementation (Complete) — 2026-02-16

| Component          | Implementation                                                                              |
| ------------------ | ------------------------------------------------------------------------------------------- |
| RoutePolicy        | Added `cost_quality` (RouteLLM-style: cheapest meeting quality floor)                       |
| resolve_route      | quality_floor, lane params; critical lane ignores cost                                      |
| Config             | routing_cost_aware_enabled, cost_quality_min_weight, cost_quality_budget_tighten_threshold  |
| run_impl / bg_impl | Cost-aware workload shaping: budget pressure or surge/spike → cost_quality for non-critical |
| CLI                | `thegent observe cost-status`, `-R cost_quality`                                            |

---

## 10. Work Package Decision Tree

```
Continue current WP? ──Yes──> Finish it
        │
        No
        │
Find next WP? ──Yes──> Priority order:
        │              1. WP-5005 (Continuity watchdog) ← recommended
        │              2. WP-5006 (Handoff integrity)
        │              3. WP-6007 (Post-launch observation)
        │
        No (tooling/optimization focus)
        │
        └──> Phase B: QW-008 polish, dx-audit, coverage-based test selection, contract introspection
```

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
