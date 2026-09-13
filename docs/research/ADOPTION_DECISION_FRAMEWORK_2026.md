## <DONE>

title: Adoption Decision Framework & Implementation Roadmap (2026)
date: 2026-02-22
status: active
owner: thegent
tags: [roadmap, adoption, governance, strategy]

---

# Adoption Decision Framework & Implementation Roadmap

**Purpose:** Translate landscape research into concrete adoption decisions with phased implementation timelines.

**Baseline:** See [LANDSCAPE_2025_2026_GOVERNANCE_POLYGLOT_MCP_RESEARCH.md](./LANDSCAPE_2025_2026_GOVERNANCE_POLYGLOT_MCP_RESEARCH.md) for detailed tool evaluation.

---

## Decision Framework: Which Tools to Adopt?

### Evaluation Criteria

Each tool is evaluated on:

1. **Blocker Severity:** Does this block current roadmap? (High/Medium/Low/None)
2. **Implementation Effort:** Weeks to production (1-2 / 2-4 / 4-8 / 8+)
3. **ROI/Benefit:** Immediate impact on cost, velocity, or reliability (High/Medium/Low)
4. **Maturity:** Production-ready? (Stable/Production-ready/Mature/Emerging)
5. **Switching Cost:** Effort to migrate away if needed (High/Medium/Low)

### Adoption Decisions (Tier System)

#### **TIER 1: ADOPT NOW** (Next 4 weeks)

These tools directly unblock current constraints and have high ROI with low switching cost.

##### 1.1 LiteLLM Proxy for Cost Governance

**Decision: ADOPT**

| Criterion            | Rating   | Rationale                                                            |
| -------------------- | -------- | -------------------------------------------------------------------- |
| **Blocker Severity** | High     | Current ad-hoc cost controls insufficient for enterprise deployments |
| **Effort**           | 2-3 days | Integrate LiteLLM client into orchestrator; add tag-based routing    |
| **ROI**              | High     | 5-10x cost reduction possible; enables budget enforcement            |
| **Maturity**         | Stable   | Production-ready; widely used (2025)                                 |
| **Switching Cost**   | Low      | Library-based; can swap out with Portkey if needed                   |

**Why This First:**

- Unlocks enterprise feature (budget enforcement).
- Complements existing model selection logic.
- Integrates cleanly with tag-based orchestration.

**Implementation Plan (Sprint 1):**

1. Install LiteLLM client: `pip install litellm`
2. Create tag-based cost tracker in orchestrator (3 files, ~200 LOC).
3. Add tag routing logic in model selector (reuse existing logic).
4. Test with 3 real agents; measure cost/call baseline.
5. Deploy to staging; monitor for 1 week.
6. Production rollout (gradual, 10% → 50% → 100%).

**Acceptance Criteria:**

- Cost tracking visible in logs/dashboard.
- Budget enforcement blocks calls at 95% of limit.
- Zero false positives (no legitimate calls rejected).
- p99 latency overhead < 5ms per call.

---

##### 1.2 Switch Type Checker to Pyright/Basedpyright

**Decision: ADOPT**

| Criterion            | Rating | Rationale                                            |
| -------------------- | ------ | ---------------------------------------------------- |
| **Blocker Severity** | Medium | CI duration pain point; slowing development velocity |
| **Effort**           | 1 day  | Config change + CI update; no code changes           |
| **ROI**              | High   | 3-5x faster type checking; reduced iteration cycle   |
| **Maturity**         | Stable | Microsoft (Pyright) or community (Basedpyright)      |
| **Switching Cost**   | Low    | Drop-in replacement for mypy                         |

**Why This First:**

- Immediate developer velocity gain (short iteration cycles).
- Zero code changes; pure config improvement.
- No risk: Pyright is stricter than mypy; catches more errors.

**Implementation Plan (Sprint 1):**

1. Install Pyright: `pip install pyright` or use Basedpyright fork.
2. Copy Pyright config (`pyrightconfig.json`) from docs/templates/.
3. Update CI: replace `mypy` with `pyright` in GitHub Actions.
4. Local test: `pyright .` (run on main branch; measure time).
5. Commit config; monitor CI duration for 1 week.

**Acceptance Criteria:**

- CI type checking drops from 5min → 1-2min.
- All existing type errors caught (parity with mypy).
- No new linting suppressions needed.
- Developers report faster iteration cycles.

---

#### **TIER 2: ADOPT IN NEXT SPRINT** (Weeks 3-8)

These tools address governance scalability and cost reduction but require more implementation effort.

##### 2.1 Migrate Hook Dispatch to Rust + PyO3

**Decision: ADOPT**

| Criterion            | Rating    | Rationale                                                   |
| -------------------- | --------- | ----------------------------------------------------------- |
| **Blocker Severity** | High      | 99KB shell script is maintenance burden + performance issue |
| **Effort**           | 2-4 weeks | Design + build + parity testing + gradual cutover           |
| **ROI**              | High      | 10-100x performance gain; type-safe governance              |
| **Maturity**         | Stable    | PyO3 production-ready (2025+)                               |
| **Switching Cost**   | Medium    | Requires Rust expertise; new CI lane (Rust compilation)     |

**Why This Now:**

- Governance scalability depends on hook performance.
- Current shell script is unmaintainable at 99KB.
- Rust + PyO3 is the proven pattern (production-ready).

**Implementation Plan (Sprint 2-3):**

**Week 1: Design & Scope**

1. Audit current hook script (`governance-gates.sh`):
   - Extract 3-5 most-called hooks (cost limit, auth validation, model routing).
   - Measure: latency distribution, call frequency, error rates.
2. Design Rust module:
   - Hook trait: `Hook { name, dispatch_fn, priority }`
   - Event dispatcher: `EventManager { hooks: Vec<Hook> }`
   - PyO3 binding: `hook_dispatch(event_type: str, context: dict) -> Result`

**Week 2-3: Build**

1. Create Rust library (new `src/` subdirectory):
   - `hooks/mod.rs` — Hook trait & dispatcher.
   - `lib.rs` — PyO3 bridge (maturin config).
2. Implement dispatcher:
   - Priority-based execution.
   - Parallel hook support (tokio for async hooks).
   - Error propagation (no silent failures).
3. Test parity with shell hooks:
   - Run 100 real hook calls.
   - Compare output: Rust vs. shell (must match byte-for-byte).
4. Build wheel: `maturin develop` (local) → CI wheel builds (all platforms).

**Week 4: Cutover**

1. Gradual migration:
   - 10% of calls → Rust dispatcher.
   - Monitor: latency, errors, cost for 1 day.
   - 50% → Rust; monitor 1 day.
   - 100% → Rust; disable shell hooks (keep as fallback for 1 week).
2. Cleanup: Remove shell hooks; archive to `legacy/` for reference.

**Acceptance Criteria:**

- Hook latency: p99 < 50ms (baseline: >500ms with shell spawning).
- Throughput: 100+ hooks/sec (baseline: ~10/sec).
- Error handling: All errors logged + visible in traces.
- Type safety: No panics on invalid input (all errors explicit).
- CI: Rust compilation fast (<2min for clean build).

**Technical Notes:**

- Use orsomafo for zero-cost event dispatch.
- Python binding via PyO3 (async support via pyo3-asyncio).
- Test framework: pyo3-test-runner (Python test in Rust harness).

---

##### 2.2 Implement Pareto-Frontier-Based Model Routing

**Decision: ADOPT**

| Criterion            | Rating    | Rationale                                            |
| -------------------- | --------- | ---------------------------------------------------- |
| **Blocker Severity** | Medium    | Cost explosion with growing agent base               |
| **Effort**           | 1-2 weeks | Integrate syftr/Pareto logic + LiteLLM routing       |
| **ROI**              | High      | 5-10x cost reduction without accuracy loss           |
| **Maturity**         | Emerging  | syftr framework available; patterns from 2025 papers |
| **Switching Cost**   | Low       | Plug-and-play with existing model selector           |

**Why This Now:**

- Complements LiteLLM cost governance (Tier 1).
- Pareto frontier is proven (5-10x cost reduction reported).
- Integrates naturally with tag-based routing.

**Implementation Plan (Sprint 2):**

**Week 1: Baseline & Measurement**

1. Profile current model usage:
   - Which models are used for which task types?
   - Cost per model per task (baseline metrics).
   - Accuracy per model (task success rate).
2. Identify task complexity heuristics:
   - Prompt length, reasoning depth, tool count, etc.
   - Build simple classifier: simple/medium/complex.

**Week 2: Pareto Routing**

1. Map models to Pareto frontier:
   - Simple tasks: Qwen3-32B (~$0.001/call, 85% accuracy).
   - Medium tasks: Claude-Sonnet (~$0.01/call, 95% accuracy).
   - Complex tasks: Claude-Opus (~$0.05/call, 99% accuracy).
   - (Use 2025 benchmarks from papers; adjust per actual data.)
2. Implement router:
   - Input: task context + complexity heuristic.
   - Output: model recommendation (from Pareto frontier).
   - Integration: Hook into existing `select_model()` function.
3. Test A/B:
   - Control: random model selection (baseline cost).
   - Treatment: Pareto routing.
   - Metrics: cost/task, accuracy, latency.

**Week 3: Rollout**

1. Shadow mode (1 week): Log routing decisions; don't enforce.
2. 10% rollout: Real routing; monitor closely.
3. Gradual: 10% → 50% → 100%.

**Acceptance Criteria:**

- Cost reduction: 5-10x (verify through baseline comparison).
- Accuracy loss: <5% (measure against baseline).
- Latency: Routing decision < 50ms (negligible).
- Error handling: Clear fallback if model unavailable.

---

#### **TIER 3: MONITOR & EVALUATE** (Q2-Q3 2026)

These tools have medium-high value but should be re-evaluated against evolving requirements.

##### 3.1 Letta for Agent Memory (If memory complexity grows)

**Decision: MONITOR**

**Trigger for Adoption:**

- Agents frequently perform multi-turn conversations (>10 turns).
- Memory consolidation becomes bottleneck (>1s latency).
- Need for cross-agent memory sharing (teams of agents).

**Expected Effort:** 2-4 weeks (integration + parity harness).

**Context:** See [Agent Memory Systems](./LANDSCAPE_2025_2026_GOVERNANCE_POLYGLOT_MCP_RESEARCH.md#4-agent-memory-systems).

---

##### 3.2 OpenTelemetry for Observability (If multi-agent deployment)

**Decision: MONITOR**

**Trigger for Adoption:**

- Multi-agent orchestration at scale (>10 agents).
- Need for end-to-end tracing (cross-service correlation).
- Enterprise observability requirement (audit trail).

**Expected Effort:** 1 week (structlog → OpenTelemetry integration).

**Context:** See [Observability & Structured Logging](./LANDSCAPE_2025_2026_GOVERNANCE_POLYGLOT_MCP_RESEARCH.md#6-observability--structured-logging).

---

##### 3.3 PyO3 for Performance-Critical Hotspots (If profiling identifies bottleneck)

**Decision: MONITOR**

**Trigger for Adoption:**

- Profile shows 10-20% of CPU time in single Python module.
- Measured latency impact (>1s per call).
- ROI: 5-15x speedup justified by operational cost.

**Expected Effort:** 2-4 weeks per module (design + build + testing).

**Context:** See [Polyglot Build Systems](./LANDSCAPE_2025_2026_GOVERNANCE_POLYGLOT_MCP_RESEARCH.md#5-polyglot-build-systems-python--rustzig).

---

#### **TIER 4: DO NOT ADOPT (Unless Requirements Change)**

##### 4.1 Open Policy Agent (OPA)

**Decision: HOLD**

**Reason:**

- Overhead not justified for single-project governance.
- Current governance via shell hooks (Tier 2 migration) is sufficient.
- OPA is valuable for _enterprise_ multi-team scenarios; thegent doesn't have this yet.

**Reevaluate if:**

- thegent becomes multi-tenant platform.
- Fine-grained policy enforcement becomes requirement (per-org, per-user).

---

##### 4.2 NeMo Guardrails

**Decision: HOLD**

**Reason:**

- Safety/content moderation is not a current blocker.
- If guardrails needed: Guardrails AI is simpler and more flexible.
- NeMo Guardrails is heavier; reserved for specific use cases (state machine workflows).

**Reevaluate if:**

- Safety compliance becomes regulatory requirement.
- Content moderation SLA emerges.

---

##### 4.3 Full Codebase → Rust Conversion (via PyO3)

**Decision: HOLD**

**Reason:**

- Not justified; Python is appropriate for orchestration/glue logic.
- Only convert performance-critical hot paths (10-20% of code).
- "Replace Python with Rust entirely" is an anti-pattern (YAGNI).

---

## Implementation Roadmap: Q1-Q3 2026

### Q1 2026 (Now - End of March)

**Sprint 1 (Weeks 1-2):**

- [ ] **LiteLLM Cost Governance:** Integrate proxy + tag-based routing.
- [ ] **Pyright Switch:** Update type checker config + CI.
- [ ] **Measurement Plan:** Baseline for cost/hook latency/type check time.

**Sprint 2 (Weeks 3-4):**

- [ ] **Hook System Design:** Audit shell script; design Rust module.
- [ ] **Pareto Routing Baseline:** Profile current model usage; identify heuristics.

### Q2 2026 (April - June)

**Sprint 3-4 (Weeks 5-8):**

- [ ] **Hook Migration:** Build Rust lib + PyO3 bridge; parity testing.
- [ ] **Pareto Routing:** Implement router; A/B test; gradual rollout.

**Sprint 5-6 (Weeks 9-12):**

- [ ] **Hook Cutover:** 10% → 50% → 100% migration; monitor.
- [ ] **Pareto Monitoring:** Track cost reduction; adjust heuristics.
- [ ] **Re-evaluate Letta:** Measure memory bottlenecks; decide on adoption.

### Q3 2026 (July - September)

**Sprint 7-8 (Weeks 13-16):**

- [ ] **Letta Integration (if triggered):** or continue monitoring.
- [ ] **OpenTelemetry Evaluation (if multi-agent deployment triggered).**

**Sprint 9-10 (Weeks 17-20):**

- [ ] **Performance Profiling:** Identify hotspots for PyO3 conversion.
- [ ] **Type Checker Hardening:** Increase strictness; add pre-commit validation.

---

## Success Metrics & Monitoring

### Metric Dashboard (To Be Updated Monthly)

| Metric                     | Current (Baseline)   | Target (Post-Adoption)        | Timeline |
| -------------------------- | -------------------- | ----------------------------- | -------- |
| **Cost Governance**        |
| Cost per agent call        | $X (unknown)         | $X \* 0.1-0.2 (10x reduction) | Q2 end   |
| Budget overrun frequency   | N/A                  | <1% of agents                 | Q1 end   |
| **Hook Performance**       |
| Hook p99 latency           | >500ms               | <50ms                         | Q2 end   |
| Hook throughput            | ~10/sec              | 100+/sec                      | Q2 end   |
| **Type Checking**          |
| CI duration (type check)   | 5min                 | 1-2min                        | Q1 end   |
| Type error detection rate  | ~80% (mypy baseline) | ~95% (Pyright)                | Q1 end   |
| **Model Routing**          |
| Cost per successful task   | $Y (baseline)        | $Y \* 0.1-0.2                 | Q2 end   |
| Accuracy loss vs. baseline | N/A                  | <5%                           | Q2 end   |
| **Overall**                |
| Developer NPS              | TBD                  | +20% (velocity improvement)   | Q3 end   |
| Agent cost/month           | $Z (baseline)        | $Z \* 0.1-0.2                 | Q2 end   |

---

## Risk Mitigation

### Q1 Risks (Low)

- **Pyright config incompatibility:** Mitigate with parallel runs (mypy + Pyright for 1 week).
- **LiteLLM integration bugs:** Test in staging for 1 week before production.

### Q2 Risks (Medium)

- **Rust compilation in CI adds latency:** Mitigate with cache + incremental builds.
- **Hook parity: Rust behavior differs from shell:** Mitigate with byte-for-byte test suite.
- **Pareto routing reduces accuracy:** Mitigate with A/B test + gradual rollout (don't exceed 5% loss).

### Q3 Risks (Low to Medium)

- **Letta integration delays:** No blocker; can defer to Q4.
- **OpenTelemetry overhead:** Monitor p99 latency; add sampling if needed.

---

## Rollback Plan

### Per-Tool Rollback (If Adoption Fails)

**LiteLLM:**

- Rollback: Remove LiteLLM client; revert to ad-hoc cost tracking.
- Effort: 1 day.
- Risk: Cost visibility lost; easy to revert.

**Pyright:**

- Rollback: Revert CI config; switch back to mypy.
- Effort: 1 hour.
- Risk: Type checking slower again; no code loss.

**Hook Migration (Rust):**

- Rollback: Disable Rust dispatcher; restore shell hooks.
- Effort: 1-2 hours.
- Risk: Performance drops; keep both running during cutover for safety net.

**Pareto Routing:**

- Rollback: Revert to hardcoded model selection.
- Effort: 1 hour.
- Risk: Cost savings lost; no code loss.

---

## Communication Plan

### Stakeholders

| Audience         | Frequency      | Message                                                                |
| ---------------- | -------------- | ---------------------------------------------------------------------- |
| **Developers**   | Weekly standup | Velocity improvements (type checking) + cost insights                  |
| **DevOps/Ops**   | Bi-weekly      | Cost governance metrics; hook performance; alerting                    |
| **Leadership**   | Monthly        | Cost savings ($ impact); velocity metrics; roadmap progress            |
| **Users/Agents** | Async (Slack)  | New features (cost budgets, faster type checking); no breaking changes |

### Key Messages

1. **Q1:** "We're adopting cost governance and faster type checking. No breaking changes; 3-5x faster iteration cycles."
2. **Q2:** "Hook system migration complete. 100x faster governance; governance is now type-safe and scalable."
3. **Q2:** "Smart model routing launched. Agents now automatically select the right model for the task. Expected 5-10x cost reduction."
4. **Q3:** "Observability and memory improvements under evaluation. Monitoring agent behavior to inform next quarter's roadmap."

---

## Success Definition

**Q1 Success:**

- [ ] LiteLLM integrated; cost visibility available.
- [ ] Pyright in place; CI 3-5x faster.
- [ ] Baseline metrics established.

**Q2 Success:**

- [ ] Hook migration complete; latency 10-100x improved.
- [ ] Pareto routing live; cost reduction 5-10x.
- [ ] Zero regressions; all governance gates still functioning.

**Q3 Success:**

- [ ] Letta/OpenTelemetry decision made (adopt or monitor).
- [ ] Performance profiling complete; PyO3 candidates identified.
- [ ] Agent cost/month reduced by 50-80% (from baselines).
- [ ] Developer velocity improved (shorter iteration cycles).

---

## Appendix: Detailed Effort Estimates

### Time Breakdown by Task

**LiteLLM Integration (2-3 days)**

- Day 1: Install, read docs, plan integration.
- Day 2: Implement tag-based routing in orchestrator (~200 LOC).
- Day 3: Test, fix bugs, document API.

**Pyright Switch (1 day)**

- 2 hours: Config + CI setup.
- 2 hours: Local testing + comparison with mypy.
- 2 hours: Documentation + team communication.

**Hook System Migration (2-4 weeks)**

- Week 1: Design, audit, scope.
- Weeks 2-3: Build, test, parity validation.
- Week 4: Gradual cutover + monitoring.

**Pareto Routing (1-2 weeks)**

- Week 1: Baseline profiling + heuristic design.
- Week 2: Implementation + A/B test + monitoring.

---

## References

- [Landscape Research: 2025-2026](./LANDSCAPE_2025_2026_GOVERNANCE_POLYGLOT_MCP_RESEARCH.md)
- [LiteLLM Docs](https://docs.litellm.ai/)
- [PyO3 User Guide](https://pyo3.rs/)
- [Pareto Frontier for AI Agents](https://arxiv.org/abs/2505.20266)
