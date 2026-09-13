<DONE>
# ChatGPT Pareto Router Deep Research — Part 6: Helios Router v1.1 Unified Spec

**Source**: chatgpt3.md, chatgpt4.md (ChatGPT, 14m+ thought)
**Date**: 2026-02-18
**Scope**: Full Unified PRD + Phased WBS/DAG + Technical ALD + ADR Docket (v1.1 with Speed Stack)

---

## 1. PRD Summary

### 1.1 Product Name

**Helios Router** — Cost-Aware Multi-Provider LLM Control Plane

### 1.2 Problem Statement

- Multiple paid subscriptions with unclear "true token coverage"
- Metered premium units (Copilot) with model multipliers and 0× models
- Rate/plan caps (tokens/day, TPM/RPM, RPS bursts)
- Volatile preview/free offers
- Self-host rentals that are only "cheap" if throughput is real

Static "pick a model" logic fails because pricing, availability, and speed claims (TTFT vs ITL vs throughput) vary.

### 1.3 Scope (v1.1)

**In scope**:
- Offer-first routing (provider+model+plan).
- Unified plan economics: PAYG, fixed bucket, daily quota bucket, weighted unit bucket, prompt rate-limited, volatile free, compute-metered.
- Speed index: TTFT + ITL + throughput profile.
- Quality index robust to missing benchmarks.
- Patch-based coding DAG: Reason → Apply → Validate → Escalate.

**Out of scope**:
- Fully learned routing policy (bandits/RL) — keep Pareto + lexicographic.
- Automated benchmark OCR.

### 1.4 Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-1 | Offer-first catalog (provider+model+plan+region) |
| FR-2 | Plan/economics engine: all plan types |
| FR-3 | Speed index uses TTFT+ITL |
| FR-4 | Quality index stable under missing benchmarks |
| FR-5 | Patch-based coding DAG |
| FR-6 | Fallback + circuit breakers |

### 1.5 Non-Functional Requirements

- Router decision latency: <5ms p95 (in-memory snapshots)
- Deterministic decisions per snapshot version
- Clear trace output: why an offer won
- Provider outages degrade gracefully

---

## 2. Phased WBS + DAG

### Phase 0 — Foundations

- P0.1 Canonical schemas (Offer/Plan/Snapshots)
- P0.2 Offer Registry + versioned snapshots
- P0.3 Execution gateway contract (OpenAI-compat)
- P0.4 Audit logging + trace IDs

### Phase 1 — Economics Engine

- P1.1 Plan types: payg_token, fixed_bucket_tokens, daily_quota_bucket, weighted_unit_bucket, prompt_rate_limited, volatile_free, compute_metered
- P1.2 Budget pacing shadow (global)
- P1.3 Plan pacing shadows (per-plan)
- P1.4 EconomicsSnapshot builder

### Phase 2 — Telemetry + Speed Profiles

- P2.1 Emit TTFT/ITL metrics in gateway logs
- P2.2 Aggregator computes p50/p95 and queue inference
- P2.3 Role-based verbosity stats (E[out_tokens])
- P2.4 TelemetrySnapshot builder

### Phase 3 — Quality Engine

- P3.1 Benchmark matrix ingest (manual)
- P3.2 Normalize per benchmark
- P3.3 Family/global shrinkage imputation
- P3.4 Coverage penalty + confidence
- P3.5 Online outcomes (tests pass, escalation, adherence)
- P3.6 QualitySnapshot builder

### Phase 4 — Router Core

- P4.1 Hard constraint engine
- P4.2 Pareto frontier implementation
- P4.3 Lexicographic selector (role-specific)
- P4.4 Fallback chains + circuit breakers
- P4.5 Route trace output

### Phase 5 — Speed Stack Integration (v1.1)

- P5.1 Cerebras adapters (token-metered + Code daily bucket)
- P5.2 NVIDIA adapters (serverless + self-host)
- P5.3 Apply model adapters (Morph/Relace)
- P5.4 Telemetry gating rules for volatile_free

### Phase 6 — Patch DAG Executor

- P6.1 Implement reason→apply→validate pipeline
- P6.2 Add role policies for apply_patch
- P6.3 Safety checks (prevent file deletion, patch sanity)
- P6.4 Escalation and rollback behaviors

---

## 3. Technical ALD (Architecture)

### 3.1 High-Level Topology

```
                  ┌────────────────────────────┐
                  │ Client / IDE / Agent Harness│
                  └──────────────┬─────────────┘
                                 │  (role + msgs + hard/soft)
                                 ▼
                      ┌─────────────────────┐
                      │ Router API (hotpath)│
                      └───────┬─────────────┘
                              │ loads immutable snapshots
                              ▼
        ┌─────────────────────────────────────────────┐
        │ Hard Filter -> Score -> Pareto -> LexiPick   │
        └───────────────┬─────────────────────────────┘
                        │
                        ▼
             ┌─────────────────────────┐
             │ Execution Gateway        │  (OpenAI-compat shim)
             └───────┬─────────────────┘
                     │
     ┌───────────────┼──────────────────────────┐
     ▼               ▼                          ▼
[Provider Adapters] [Self-host/NIM]      [Apply/Patch Adapters]
(OpenRouter, etc.)  (GPU rentals)        (Morph/Relace)
```

### 3.2 Control Plane vs Data Plane

**Data plane (hot path)**: Router API, Execution Gateway, Fallback engine
**Control plane (slow path)**: Offer Registry, Plan Registry, Economics Engine, Telemetry Aggregator, Quality Engine, Snapshot Builder

### 3.3 Key Pipelines

- **Pipeline A** — Offer ingestion: Sources → Adapters → OfferRegistry → OfferSnapshot
- **Pipeline B** — Telemetry: Gateway logs → Aggregator → Per-offer TTFT/ITL/TPS → TelemetrySnapshot
- **Pipeline C** — Economics: Plans → Shadow pricing → EconomicsSnapshot

---

## 4. ADR Docket (v1.1)

| ID | Decision | Status |
|----|----------|--------|
| ADR-001 | Offer-first routing (provider+model+plan) | Accepted |
| ADR-002 | Pareto frontier + lexicographic tie-break | Accepted |
| ADR-003 | Copilot = weighted unit bucket + 0× included models | Accepted |
| ADR-004 | Speed profile uses TTFT+ITL (not "tok/s") | Accepted |
| ADR-005 | Cerebras Code modeled as daily_quota_bucket | Accepted |
| ADR-006 | NVIDIA build.nvidia.com classified as volatile_free | Accepted |
| ADR-007 | Apply/Patch models are separate role + DAG stage | Accepted |
| ADR-008 | Vendor speed claims are priors; measured telemetry wins | Accepted |

---

## 5. Routing Algorithm (Final)

```python
for offer in offers:
    if not hard_constraints_ok(offer):
        continue
    cost = effective_cost(offer)
    if cost > maxCost:
        continue
    speed = speed_score(offer)
    quality = quality_score(offer)
    candidates.append((offer, cost, speed, quality))

pareto = non_dominated(candidates)
selected = lexicographic(pareto, order=[quality, cost, speed])
execute_with_fallback(selected)
```

---

## 6. "Tell It Like It Is" Notes

- **Step 3.5 Flash** is not a 3000 tok/s model. Model card: ~100–300 tok/s (peak 350).
- **NIM "tokens/sec"** claims are often throughput under concurrency. Track TTFT/ITL in your harness.
- **Cerebras Code** will 429 you if you burst. FAQ explicitly calls out RPS burst behavior.
- **Morph/Relace** only pay off if you implement the patch DAG. Otherwise value left on table.

---

## References

- chatgpt3.md, chatgpt4.md
- CHATGPT_PARETO_DEEP_01 through 05
- CHATGPT_PARETO_ROUTER_EXTENSION.md
