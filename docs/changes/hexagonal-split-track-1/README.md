# Track 1: Migrate Routing/Adapters/Auth to CLIProxyAPI++

## Overview

Track 1 migrates ~30K LOC of thegent's LLM routing, provider adapters, and auth integrations from Python to Go (CLIProxy). This is a **strict TDD plan** with bite-sized tasks, failing tests first, and parity verification at each stage.

**Target outcome:** All LLM calls flow through CLIProxy localhost:8317 instead of LiteLLM. Thegent becomes a thin orchestration layer.

**Scope:**

- `thegent.routing` (~11.5K LOC) → CLIProxy `/v1/routing/select` endpoint
- `thegent.adapters` (~1.4K LOC) → CLIProxy translator registry
- `thegent.integrations.auth` → CLIProxy OAuth token manager
- `thegent.integrations.quota` → CLIProxy quota enforcer

**Timeline:** 5 parallel work streams, 20 tasks total, ~12 wall-clock hours (3–4 parallel subagents).

---

## Documentation Index

### 1. **TRACK1_TDD_IMPLEMENTATION_PLAN.md** (Primary)

- Complete work breakdown: 20 tasks across 5 streams
- Each task has: failing test, minimal implementation, parity test, verification commands, commit message
- File paths, exact code snippets, expected outputs
- Quality gates, risk mitigation, appendix with file structure

**Start here if:** You're implementing Track 1.

### 2. **TRACK1_QUICK_REFERENCE.md** (Operational)

- 1-page task checklist with status tracking
- File map (where to add/edit)
- Copy-paste shell commands for each work stream
- Parallel execution strategies
- Quality gates checklist
- Gotchas & tips

**Start here if:** You're running tasks and need quick lookup.

### 3. **TRACK1_ARCHITECTURE_DECISIONS.md** (Strategic)

- 8 Architecture Decision Records (ADRs):
  - ADR-001: Port Pareto to Go (not FFI)
  - ADR-002: HTTP endpoints (not lib imports)
  - ADR-003: OAuth in CLIProxy (not distributed)
  - ADR-004: Translators in CLIProxy (not adapters in thegent)
  - ADR-005: Quota in CLIProxy (not thegent)
  - ADR-006: Task classifier separate from routing
  - ADR-007: Parity testing (dual-run before deletion)
  - ADR-008: CLIProxy as separate process (not embedded)
- 8 open questions (deferred decisions)
- Risk register
- Success criteria

**Start here if:** You need to understand _why_ decisions were made.

---

## Task Breakdown by Work Stream

### Work Stream 1: Pareto Frontier Routing (Go)

Ported algorithm, task classification, HTTP endpoint. **Foundational.**

| Task                                         | Duration | Verification                                                   |
| -------------------------------------------- | -------- | -------------------------------------------------------------- |
| **T1.1** Test: Pareto route selection        | 30m      | `go test TestParetoRoutingSelectsOptimalModelGivenConstraints` |
| **T1.2** Impl: Pareto router + frontier      | 2h       | `go test TestPareto ./pkg/llmproxy/registry -v`                |
| **T1.3** Impl: Task classifier               | 1.5h     | `go test TestTaskClassifier ./pkg/llmproxy/registry -v`        |
| **T1.4** Impl: `/v1/routing/select` endpoint | 1.5h     | `curl POST http://localhost:8317/v1/routing/select`            |
| **T1.5** Test: Parity (thegent vs CLIProxy)  | 1h       | `pytest test_parity_pareto_router_vs_cliproxy.py -v`           |

**Entry point:** T1.1. Enables T2–T4 in parallel after T1.4.

---

### Work Stream 2: Provider Adapters (Go)

Consolidate ACP, MCP adapters into CLIProxy translators. **Parallel to T1.x, starts after T1.4.**

| Task                                        | Duration | Verification                                          |
| ------------------------------------------- | -------- | ----------------------------------------------------- |
| **T2.1** Test: ACP adapter registration     | 30m      | `go test TestACPAdapterIsRegistered`                  |
| **T2.2** Impl: ACP translator               | 1.5h     | `go test TestACPAdapter ./pkg/llmproxy/translator -v` |
| **T2.3** Test: Parity (thegent vs CLIProxy) | 1h       | `pytest test_parity_adapters_vs_cliproxy.py -v`       |

**Entry point:** T2.1 (after T1.4 available).

---

### Work Stream 3: OAuth Token Management (Go)

Centralized OAuth token refresh, storage, expiration. **Parallel to T1.x, starts after T1.4.**

| Task                                        | Duration | Verification                                                 |
| ------------------------------------------- | -------- | ------------------------------------------------------------ |
| **T3.1** Test: Token manager                | 30m      | `go test TestOAuthTokenManagerRefreshesExpiredToken`         |
| **T3.2** Impl: OAuth token manager          | 1.5h     | `go test TestOAuthTokenManager ./pkg/llmproxy/auth -v -race` |
| **T3.3** Test: Parity (thegent vs CLIProxy) | 1h       | `pytest test_parity_oauth_vs_cliproxy.py -v`                 |

**Entry point:** T3.1 (after T1.4 available).

---

### Work Stream 4: Quota Enforcement (Go)

Daily quota tracking, request blocking. **Parallel to T1.x, starts after T1.4.**

| Task                                        | Duration | Verification                                               |
| ------------------------------------------- | -------- | ---------------------------------------------------------- |
| **T4.1** Test: Quota enforcer               | 30m      | `go test TestQuotaEnforcerBlocksRequestWhenQuotaExhausted` |
| **T4.2** Impl: Quota enforcer               | 1.5h     | `go test TestQuotaEnforcer ./pkg/llmproxy/usage -v -race`  |
| **T4.3** Test: Parity (thegent vs CLIProxy) | 1h       | `pytest test_parity_quota_vs_cliproxy.py -v`               |

**Entry point:** T4.1 (after T1.4 available).

---

### Work Stream 5: Thegent Integration & Cleanup (Python)

Update thegent to call CLIProxy, remove old modules. **Sequential, starts after T1.5+T2.3+T3.3+T4.3.**

| Task                                               | Duration | Verification                                                   |
| -------------------------------------------------- | -------- | -------------------------------------------------------------- |
| **T5.1** Test: CLIProxy integration (failing)      | 30m      | `pytest test_cliproxy_integration_routing.py -v` (expect fail) |
| **T5.2** Impl: TaskRouter → CLIProxy               | 2h       | `pytest test_cliproxy_integration_routing.py -v` (expect pass) |
| **T5.3** Cleanup: Remove old modules, tach.toml    | 1h       | `tach check`                                                   |
| **T5.4** Test: E2E (thegent → CLIProxy → provider) | 1.5h     | `pytest test_e2e_thegent_cliproxy_provider.py -v -s`           |
| **T5.5** Test: Full parity (legacy vs CLIProxy)    | 2h       | `pytest test_parity_legacy_vs_cliproxy_migration.py -v`        |

**Entry point:** T5.1 (after all parity tests pass).

---

### Cross-Track Verification

| Task                                                | Duration | Verification                                                   |
| --------------------------------------------------- | -------- | -------------------------------------------------------------- |
| **T0.0** Smoke test: All CLIProxy endpoints respond | 30m      | `go test TestAllRoutingEndpointsRespond ./pkg/llmproxy/api -v` |

**Entry point:** After T5.5. Final validation before merge.

---

## Execution Timeline

```
Day 1 (8h wall clock):
├─ T1.1–T1.5 (Pareto router) — 6.5h, sequential
│  └─ T1.1 (30m) → T1.2 (2h) → T1.3 (1.5h) → T1.4 (1.5h) → T1.5 (1h)
├─ T2.1–T2.3 (Adapters) — 3h, parallel (starts after T1.4)
├─ T3.1–T3.3 (Auth) — 3h, parallel (starts after T1.4)
└─ T4.1–T4.3 (Quota) — 3h, parallel (starts after T1.4)

Day 2 (6h wall clock):
├─ T5.1–T5.5 (Integration) — 8h, sequential
│  └─ T5.1 (30m) → T5.2 (2h) → T5.3 (1h) → T5.4 (1.5h) → T5.5 (2h)
└─ T0.0 (Smoke test) — 30m
```

**Optimal parallelism:** Start T1.1 immediately. After T1.4 (≈5.5h), start T2.1, T3.1, T4.1 in parallel. After T1.5+T2.3+T3.3+T4.3, start T5.1.

**Subagent breakdown:**

- **Agent 1:** T1.1–T1.5 (Pareto routing)
- **Agent 2:** T2.1–T2.3 (Adapters)
- **Agent 3:** T3.1–T3.3 (Auth)
- **Agent 4:** T4.1–T4.3 (Quota)
- **Agent 5 (after):** T5.1–T5.5 (Integration)

---

## Key Files by Work Stream

### CLIProxy (Go)

**Work Stream 1 (Pareto Routing):**

```
pkg/llmproxy/
├─ registry/
│  ├─ pareto_router.go (NEW - T1.2)
│  ├─ pareto_types.go (NEW - T1.2)
│  ├─ pareto_router_test.go (NEW - T1.1)
│  ├─ task_classifier.go (NEW - T1.3)
│  ├─ task_classifier_test.go (NEW - T1.3)
│  └─ routing_pareto_integration_test.go (NEW - T1.1)
└─ api/
   ├─ routing_handler.go (NEW - T1.4)
   ├─ routing_handler_test.go (NEW - T1.4)
   └─ endpoints_integration_test.go (NEW - T0.0)
```

**Work Stream 2 (Adapters):**

```
pkg/llmproxy/translator/acp/
├─ acp_adapter.go (NEW - T2.2)
├─ acp_request.go (NEW - T2.2)
├─ acp_response.go (NEW - T2.2)
└─ acp_adapter_registry_test.go (NEW - T2.1)
```

**Work Stream 3 (Auth):**

```
pkg/llmproxy/auth/
├─ oauth_token_manager.go (NEW - T3.2)
├─ oauth_types.go (NEW - T3.2)
└─ oauth_token_manager_test.go (NEW - T3.1)
```

**Work Stream 4 (Quota):**

```
pkg/llmproxy/usage/
├─ quota_enforcer.go (NEW - T4.2)
├─ quota_types.go (NEW - T4.2)
└─ quota_enforcer_test.go (NEW - T4.1)
```

### thegent (Python)

**Work Stream 1 (Parity):**

```
tests/routing/
└─ test_parity_pareto_router_vs_cliproxy.py (NEW - T1.5)
```

**Work Stream 2 (Parity):**

```
tests/adapters/
└─ test_parity_adapters_vs_cliproxy.py (NEW - T2.3)
```

**Work Stream 3 (Parity):**

```
tests/auth/
└─ test_parity_oauth_vs_cliproxy.py (NEW - T3.3)
```

**Work Stream 4 (Parity):**

```
tests/quota/
└─ test_parity_quota_vs_cliproxy.py (NEW - T4.3)
```

**Work Stream 5 (Integration):**

```
src/thegent/routing/
├─ cliproxy_client.py (NEW - T5.2)
├─ task_router.py (EDIT - T5.2, thin wrapper)
└─ pareto_router.py (DELETE - T5.3)

tests/integration/
├─ test_cliproxy_integration_routing.py (NEW - T5.1)
├─ test_e2e_thegent_cliproxy_provider.py (NEW - T5.4)
└─ test_parity_legacy_vs_cliproxy_migration.py (NEW - T5.5)

tach.toml (EDIT - T5.3)
```

---

## Quality Gates

**Before merging, verify:**

- [ ] All tests pass: `pytest tests/ -v` (thegent), `go test ./... -v` (CLIProxy)
- [ ] No lint errors: `ruff check src/`, `go vet ./pkg/llmproxy/`
- [ ] Parity suite 100%: `pytest tests/integration/test_parity_* -v`
- [ ] Boundaries correct: `tach check`
- [ ] Old modules deleted: `find src/thegent/routing -name "pareto_router.py"` → NOT FOUND
- [ ] No LiteLLM in routing: `grep -r "litellm" src/thegent/routing/` → (empty)
- [ ] Endpoints live: `curl -s http://localhost:8317/v1/routing/select` → valid response
- [ ] E2E works: `pytest tests/integration/test_e2e_* -v -s` → all pass
- [ ] 20 commits with `@trace` tags: `git log --oneline --grep="@trace" | wc -l` → 20

---

## Getting Started

### Option 1: Read Full Plan (Comprehensive)

1. Read **TRACK1_TDD_IMPLEMENTATION_PLAN.md** (detailed specs)
2. Read **TRACK1_ARCHITECTURE_DECISIONS.md** (why)
3. Use **TRACK1_QUICK_REFERENCE.md** (while implementing)

### Option 2: Quick Start (Hands-On)

1. Skim **TRACK1_QUICK_REFERENCE.md** (overview + commands)
2. Start with T1.1 from plan
3. Refer to **TRACK1_TDD_IMPLEMENTATION_PLAN.md** for detailed specs per task

### Option 3: Strategic (Leadership)

1. Read **TRACK1_ARCHITECTURE_DECISIONS.md** (decisions + rationale)
2. Skim task table in this README
3. Review risk register + success criteria

---

## Parity Testing Philosophy

Track 1 uses **dual-implementation parity testing:** Both thegent (Python) and CLIProxy (Go) implementations run in parallel. Tests compare their outputs. Only after parity is verified (T1.5, T2.3, T3.3, T4.3) does T5.3 delete the old thegent code.

**Why?**

- Verification by example: Parity tests ARE the specification
- Safe migration: Can fall back to thegent if CLIProxy breaks
- Debugging: Easier to spot bugs if both run side-by-side
- Confidence: 100% passing parity suite = safe to delete old code

**Timeline:**

- Days 1–2 (T1.1–T5.2): Both implementations active, tests passing
- T5.3: Delete old thegent modules
- T5.4–T5.5: Verify full system works with CLIProxy only

---

## Success Criteria

Track 1 is **COMPLETE** when:

1. ✅ All 20 tasks pass (test + implementation + parity)
2. ✅ Parity test suite: 100% pass rate
3. ✅ E2E test passes (thegent → CLIProxy → provider)
4. ✅ Full parity suite passes (legacy Python vs CLIProxy Go)
5. ✅ No regressions: `pytest tests/ -x`, `go test ./... -x`
6. ✅ Boundaries correct: `tach check`
7. ✅ Old modules deleted: Zero pareto_router.py references
8. ✅ No LiteLLM imports in routing
9. ✅ Clean commit history: 20 commits with `@trace` tags

---

## Risk Summary

| Risk                               | Mitigation                                   |
| ---------------------------------- | -------------------------------------------- |
| CLIProxy endpoint is slow          | Timeout 10s, circuit breaker, cache          |
| Parity reveals subtle diffs        | Dual-run tests before deletion               |
| Quota enforcement breaks workflows | Feature flag, fallback to thegent            |
| Old code still used after deletion | grep verification in T5.3                    |
| Model metadata diverges            | CLIProxy is source of truth, version control |

---

## Next Phases

- **Track 2:** Migrate remaining integrations (cost tracking, credential lifecycle)
- **Track 3:** Optimize CLIProxy (caching, batching, latency)
- **Track 4:** Production rollout (canary → 100%, decommission old routing)

---

## Questions? Open Issues?

See **TRACK1_ARCHITECTURE_DECISIONS.md** — "Open Questions & Decisions Deferred" section covers:

- Q1: Quota per-agent vs. global?
- Q2: CLIProxy downtime handling?
- Q3: Persist OAuth tokens across restarts?
- Q4: Model metadata sync strategy?
- Q5: Provider-specific extensions (e.g., thinking tokens)?
- Q6: Quota reject vs. queue?
- Q7: API versioning policy?
- Q8: Mock CLIProxy in tests?

---

## Document Map

```
docs/changes/hexagonal-split-track-1/
├─ README.md (this file)
│  └─ Overview, task grid, file map, success criteria
├─ TRACK1_TDD_IMPLEMENTATION_PLAN.md
│  └─ Complete specs: 20 tasks, code snippets, commands, commit messages
├─ TRACK1_QUICK_REFERENCE.md
│  └─ 1-page checklists, commands, parallel strategies, gotchas
└─ TRACK1_ARCHITECTURE_DECISIONS.md
   └─ 8 ADRs, open questions, risk register, success criteria
```

---

**Status:** 📋 Ready for implementation (all specs written, no blocking unknowns)

**Kickoff:** Start with T1.1. Parallelize T2–T4 after T1.4. T5 after all parity tests pass.

**Estimated Duration:** 12 wall-clock hours with 4 parallel subagents.
