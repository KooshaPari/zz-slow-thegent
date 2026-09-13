# Track 1 Architecture Decisions & Rationale

## ADR-001: Port Pareto Algorithm from Python to Go

**Decision:** Rewrite the Pareto frontier routing algorithm from Python (thegent) in Go (CLIProxy), rather than exposing thegent's router via FFI.

**Rationale:**

- **Pure Go implementation:** Allows CLIProxy to run standalone without Python dependency
- **Performance:** Native Go is 5–10x faster than Python-via-FFI for constraint filtering + frontier computation
- **Maintenance:** Single algorithm in one language, easier to reason about and optimize
- **Terminal Bench 2.0 integration:** Model metrics are already in Go (CLIProxy registry), no translation needed

**Alternative Rejected:** Expose thegent's Pareto router via cgo/FFI

- Adds complexity (FFI boundary)
- Slower (marshaling overhead)
- Ties CLIProxy to Python runtime

**Trade-off:** ~600 LOC rewrite vs. ~200 LOC FFI binding. Rewrite wins on simplicity and performance.

**Validation:** T1.5 parity test confirms identical model selection.

---

## ADR-002: Expose Routing as HTTP Endpoint, Not Direct Lib Call

**Decision:** CLIProxy exposes routing via `POST /v1/routing/select` HTTP endpoint, not as a Go library that thegent imports.

**Rationale:**

- **Decoupling:** thegent and CLIProxy are independent processes; no shared code
- **Boundary clarity:** Clear separation of concerns (orchestration vs. routing)
- **Scalability:** CLIProxy can scale independently; multiple thegent instances share routing service
- **Future multitenancy:** HTTP endpoint can be exposed to other clients (IDE, other agents)
- **Testing:** HTTP mocking is simpler than mocking Go libraries

**Alternative Rejected:** Go library that thegent calls via cgo

- Adds FFI complexity
- Couples thegent to CLIProxy's Go runtime
- Harder to scale (processes tied together)

**Trade-off:** Network latency (~10ms per routing decision) is acceptable for task-level routing (1 decision per 1–5 minutes of execution).

**Validation:** T5.4 E2E test measures end-to-end latency.

---

## ADR-003: Consolidate Auth into CLIProxy OAuth Token Manager

**Decision:** Merge thegent's OAuth lifecycle management into CLIProxy's centralized token manager, with HTTP endpoints for refresh/revoke.

**Rationale:**

- **Single source of truth:** One OAuth state for all agents/providers
- **Token refresh in one place:** CLIProxy manages expiration/refresh logic
- **Credential security:** Tokens stored in CLIProxy process, not scattered across agent instances
- **HTTP for token ops:** thegent calls `POST /v1/auth/oauth/refresh` instead of managing tokens locally

**Alternative Rejected:** Keep OAuth in thegent, have CLIProxy call back to thegent

- Circular dependency (thegent ↔ CLIProxy)
- Difficult to reason about token state
- Harder to add new agents (each must re-implement OAuth)

**Trade-off:** All agents depend on CLIProxy for token refresh; if CLIProxy is down, no auth. Mitigation: cache tokens in-process with fallback to disk.

**Validation:** T3.3 parity test confirms identical refresh behavior.

---

## ADR-004: Adapter/Translator Consolidation Strategy

**Decision:** Move thegent's ACP, MCP adapters into CLIProxy's translator registry; thegent calls CLIProxy translators, not local adapters.

**Rationale:**

- **Provider abstraction in one place:** Translators handle Claude↔OpenAI↔ACP format conversions
- **Reduces code duplication:** thegent and other harnesses use same translators
- **Provider registry:** CLIProxy can add/remove providers without modifying thegent
- **Request/response tracing:** All translations happen in one service, easier to debug

**Alternative Rejected:** Keep adapters in thegent, let CLIProxy call them

- Requires FFI or network calls back to thegent
- Circular dependency
- Harder to support new providers

**Architecture:**

```
thegent
  ↓ (chat completion request)
CLIProxy /v1/chat/completions
  ↓ (classify provider)
translator registry (ACP/Claude/OpenAI/Gemini)
  ↓ (translate to provider API)
provider (AWS Bedrock, Anthropic, OpenAI, etc.)
```

**Validation:** T2.3 parity test confirms identical transformations.

---

## ADR-005: Quota Enforcement in CLIProxy, Not thegent

**Decision:** Move quota enforcement from thegent integrations to CLIProxy's usage subsystem. All requests checked against quota before forwarding to provider.

**Rationale:**

- **Single point of enforcement:** CLIProxy is gatekeeper for all LLM calls
- **Prevents cost overruns:** Quota check happens before provider call (saves money)
- **Fair queuing:** If quota exhausted, CLIProxy can queue/reject fairly across tenants
- **Real-time metrics:** CLIProxy tracks actual usage in one place

**Alternative Rejected:** Keep quota checks in thegent

- Multiple agents can exceed quota if not coordinated
- Hard to enforce hard limit across distributed system
- Requires synchronization between agents

**Trade-off:** thegent must call CLIProxy to check quota; adds ~10ms latency per check. Acceptable for task-level routing.

**Validation:** T4.3 parity test confirms quota blocking at same thresholds.

---

## ADR-006: Task Classification in CLIProxy, Not Pareto Router

**Decision:** Separate task classification (FAST/NORMAL/COMPLEX/HIGH_COMPLEX) from Pareto routing. Classification happens first, then routes within tier-specific frontier.

**Rationale:**

- **Modularity:** TaskClassifier is testable independently
- **Extensibility:** Can add new classification strategies without touching Pareto router
- **Clarity:** Routing decision is: classify → filter by constraints → Pareto selection
- **Performance:** Classification is fast (token count check); can cache classifiers per task type

**Alternative Rejected:** Inline classification in Pareto router

- Harder to test classification separately
- Mixing concerns (task analysis + routing)

**Architecture:**

```
Task metadata (tokens_in, tokens_out, category)
  ↓ (classify)
Category (FAST/NORMAL/COMPLEX/HIGH_COMPLEX)
  ↓ (build constraint request)
Constraints (max_cost, max_latency, min_quality)
  ↓ (route)
Selected model
```

**Validation:** T1.3 and T1.4 tests verify classification then routing.

---

## ADR-007: Parity Testing Strategy (Dual-Implementation)

**Decision:** Keep thegent's local routing/adapters/auth intact during Track 1; run parity tests comparing thegent implementation to CLIProxy. Only delete thegent code after parity is verified.

**Rationale:**

- **Safe migration:** Can fall back to thegent implementation if CLIProxy breaks
- **Verification by example:** Parity tests serve as specifications
- **Gradual rollout:** Can canary CLIProxy routing before full cutover
- **Debugging:** Easier to spot diffs if both implementations run side-by-side

**Alternative Rejected:** Migrate immediately, delete old code

- Risk: If CLIProxy has a bug, no fallback
- Harder to debug subtle diffs

**Timeline:** Parity tests in parallel with implementations (T1.5, T2.3, T3.3, T4.3), then delete old code in T5.3.

**Validation:** All parity tests pass before T5.3.

---

## ADR-008: CLIProxy as Separate Process, Not Embedded Library

**Decision:** CLIProxy runs as separate process (localhost:8317), thegent calls via HTTP. Don't embed CLIProxy into thegent binary.

**Rationale:**

- **Independent scaling:** CLIProxy can be deployed separately, shared across multiple thegent instances
- **Language agnostic:** Non-Python harnesses (Codex, Gemini) can use same CLIProxy
- **Operational clarity:** Separate process, separate logs, separate restarts
- **Zero deployment coupling:** Deploying thegent doesn't require CLIProxy deploy

**Alternative Rejected:** Link CLIProxy as Go library in thegent

- Adds build complexity (cgo)
- Ties process lifetimes
- Can't scale independently

**Trade-off:** Network overhead (~10ms per decision) is acceptable; startup time is slightly longer (need to connect to CLIProxy).

**Mitigation:** Connection pooling + retries with backoff in CLIProxyRoutingClient.

**Validation:** T5.4 E2E test verifies multi-process flow.

---

## Open Questions & Decisions Deferred

### Q1: Should quota be per-agent, per-provider, or global?

**Current decision:** Global (all thegent instances share quota across all providers). If finer granularity needed, CLIProxy quota subsystem can be extended.

**Evidence needed:** How are quotas currently managed in thegent? Are they per-provider or global?

**Action:** Review thegent.integrations.connector_quota.py before T4.1.

---

### Q2: How to handle CLIProxy downtime?

**Current decision:** If CLIProxy is down, routing calls fail loudly (no fallback). thegent should retry with backoff.

**Alternative:** Cache last N routing decisions locally, use cache if CLIProxy unavailable.

**Evidence needed:** SLO for CLIProxy uptime? Is high-availability required?

**Action:** Implement circuit breaker pattern in T1.4 if SLO < 99.9%.

---

### Q3: Should OAuth tokens be persisted across CLIProxy restarts?

**Current decision:** Tokens stored in-memory only. On CLIProxy restart, tokens are lost; agents must refresh.

**Alternative:** Persist tokens to disk (encrypted) or Redis.

**Evidence needed:** How long do OAuth tokens last? Is restart frequency a concern?

**Action:** If restarts are frequent, implement token persistence in T3.2.

---

### Q4: How to coordinate model metadata updates between CLIProxy registry and thegent?

**Current decision:** CLIProxy is source of truth for model metadata (costs, latency, quality). thegent reads via `/v1/models` endpoint.

**Alternative:** thegent caches metadata locally, polls for updates.

**Evidence needed:** How frequently do model metrics change? Can we tolerate 10-minute staleness?

**Action:** Implement polling mechanism in T5.2 if needed.

---

### Q5: How to handle provider-specific request/response details (e.g., thinking tokens, structured output)?

**Current decision:** Translators in CLIProxy handle format conversion; thegent calls standard `/v1/chat/completions`.

**Risk:** Some providers (Claude with extended thinking) need special handling. If not modeled in translator, thegent loses features.

**Mitigation:** Extend translator registry to include provider-specific extensions (e.g., `POST /v1/chat/completions?extensions=thinking`).

**Action:** Document translator extension points before T2.1.

---

### Q6: Should CLIProxy quota reject or queue over-quota requests?

**Current decision:** Reject with 429 status (rate limited). Client (thegent) handles retry.

**Alternative:** Queue in CLIProxy, serve when quota refreshes (next day).

**Evidence needed:** How do users expect quota exhaustion to be handled? Reject (fail fast) or queue (eventual success)?

**Action:** Clarify quota semantics in Q1 before T4.1.

---

### Q7: How to version CLIProxy API?

**Current decision:** Endpoints are `/v1/routing/select`, `/v1/auth/oauth/refresh`, etc. (v1 prefix).

**Risk:** If API changes, v1 endpoints must be maintained for backward compatibility.

**Mitigation:** Semantic versioning: v1.0, v1.1, v2.0. Parity tests pin to API version.

**Action:** Document API versioning policy in CLIProxy README before T1.4.

---

### Q8: How to test CLIProxy endpoints when building thegent?

**Current decision:** Assume CLIProxy is running at localhost:8317 for parity tests. Skip parity tests if CLIProxy unavailable.

**Alternative:** Mock HTTP endpoints in parity tests (use httptest.Server).

**Evidence needed:** Is localhost:8317 always available in CI/dev? If not, mocking is safer.

**Action:** Use httptest mocks in all parity tests (T1.5, T2.3, T3.3, T4.3) to avoid hard dependency on running CLIProxy.

---

## Risk Register

| Risk                                        | Probability | Impact | Mitigation                                                     |
| ------------------------------------------- | ----------- | ------ | -------------------------------------------------------------- |
| CLIProxy endpoint is slow                   | Medium      | High   | Implement timeout (10s), circuit breaker, cache                |
| Parity test reveals subtle diffs            | Medium      | Medium | Dual-run parity tests before deleting code (T5.3)              |
| Quota enforcement breaks existing workflows | Low         | High   | Feature flag to opt-in to CLIProxy quota (fallback to thegent) |
| OAuth token refresh fails silently          | Low         | High   | Explicit error on refresh failure, not fallback                |
| Model metadata diverges between systems     | Medium      | Medium | CLIProxy is source of truth, thegent polls; version control    |
| Old routing code still used after deletion  | Low         | High   | grep -r to verify no imports after T5.3                        |

---

## Success Criteria

Track 1 is **DONE** when:

1. ✓ All 20 tasks pass (test + implementation + parity)
2. ✓ Parity test suite 100% pass rate (T1.5, T2.3, T3.3, T4.3)
3. ✓ E2E test succeeds (thegent → CLIProxy → provider) (T5.4)
4. ✓ Full parity suite passes (legacy vs CLIProxy) (T5.5)
5. ✓ No regressions: `pytest tests/ -x` passes
6. ✓ Boundaries correct: `tach check` passes
7. ✓ Old modules deleted: `ls src/thegent/routing/pareto_router.py` → NOT FOUND
8. ✓ No LiteLLM imports in routing: `grep -r "litellm" src/thegent/routing/` → (empty)
9. ✓ All 20 commits have clear messages + `@trace` tags

---

## Next Steps (After Track 1)

### Track 2: Integrations & Lifecycle

- Migrate remaining cost tracking integrations
- Migrate credential source validation
- Add CLIProxy endpoints for credential refresh lifecycle

### Track 3: Optimization

- Implement response caching in CLIProxy
- Batch multiple routing requests
- Add latency metrics/SLOs

### Track 4: Production Rollout

- Canary CLIProxy routing to 10% of agents
- Monitor for parity diffs, latency
- Full rollout to 100%
- Decommission thegent.routing module

---

## References

- **Pareto Frontier Algorithm:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/routing/pareto_router.py`
- **Task Router:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/routing/task_router.py`
- **ACP Client:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/adapters/acp_client.py`
- **OAuth Lifecycle:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/integrations/` (search `oauth*`)
- **Quota Tracking:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/integrations/connector_quota.py`
- **CLIProxy Registry:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/CLIProxyAPI-plusplus/pkg/llmproxy/registry/`
- **Terminal Bench 2.0:** `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/docs/reference/MODEL_ROUTING_TERMINAL_BENCH_2_0_QUICK_REF.md`
