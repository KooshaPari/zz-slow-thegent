<DONE>
# ChatGPT Pareto Router Deep Research — Part 5: Speed Stack Providers

**Source**: chatgpt3.md, chatgpt4.md (ChatGPT research, 17m+ thought)
**Date**: 2026-02-18
**Scope**: Cerebras, NVIDIA NIM, Step 3.5 Flash, Morph, Relace — sourced research, catalog integration, routing roles

---

## 1. Reality Check: "Tokens/sec" Is Not One Metric

Vendors mix at least four different things:

| Metric                   | Description                                |
| ------------------------ | ------------------------------------------ |
| **TTFT**                 | Time to first token                        |
| **ITL**                  | Inter-token latency (TPOT)                 |
| **Output tokens/sec**    | Streaming speed after first token          |
| **Aggregate throughput** | Tokens/sec across many concurrent requests |

**Router implication**: Don't store one `toks_per_sec`. Store a **profile**:

- ttft_p50/p95
- itl_p50/p95
- tps_stream_p50/p95 (per request stream)
- tps_agg_at_concurrency (system throughput)
- queue_ms_p95 (for queued services)

---

## 2. Cerebras

### 2.1 Inference (Pay-Per-Token)

- **Llama 3.1 8B**: ~2200 tokens/sec, $0.10/M input, $0.10/M output
- **Llama 3.1 70B**: ~450 tok/s, $0.60/M
- **GPT-OSS-120B**: "up to 3,000 tokens/sec", $0.25/M in, $0.69/M out, 128k context

**Sources**: Cerebras inference docs, Artificial Analysis verification, Cerebras blog

### 2.2 Cerebras Code (Subscription, Daily Caps)

| Tier               | Tokens/Day | TPM       | RPM |
| ------------------ | ---------- | --------- | --- |
| Code Pro ($50/mo)  | 24M        | 1,000,000 | 50  |
| Code Max ($200/mo) | 120M       | 1,500,000 | 120 |

- Powered by Qwen3-Coder, "up to 2,000 tokens/sec"
- **Risks**: Queue time / utilization variance; burst/RPS causing 429s; limits can change
- Preview models can be discontinued at short notice

**Plan type**: `daily_quota_bucket` (not monthly)

### 2.3 Catalog Integration

```yaml
# Cerebras Inference (token metered)
offerId: cerebras:llama-3.1-8b:inference
provider: cerebras
planId: cerebras-payg
pricing: { inputPerMTokUsd: 0.10, outputPerMTokUsd: 0.10 }
limits: { throughputTokensPerSec: 2200 }

# Cerebras Code Max (daily bucket)
offerId: cerebras:code-max:qwen3-coder
provider: cerebras
planId: cerebras-code-max
quotaModel:
  tokensPerDayCap: 120000000
  tpmCap: 1500000
  rpmCap: 120
```

---

## 3. NVIDIA NIM

### 3.1 What NIM Is

NIM microservices = prebuilt, optimized inference containers for NVIDIA GPUs. Expose standard APIs; can run on Kubernetes.

### 3.2 Performance Example (Llama 3.1 8B Instruct)

- **1× H100 SXM, 200 concurrent requests**
- NIM ON: 1201 tokens/s throughput, ITL 32ms
- NIM OFF: 613 tokens/s, ITL 37ms

**Note**: Throughput is system-level under concurrency, not necessarily "one user sees 1201 tok/s."

### 3.3 Step 3.5 Flash (StepFun on NVIDIA build)

- **196.81B total params, ~11B active**
- "100–300 tok/s throughput, peaking at 350 tok/s for coding tasks"
- **Not** a 3000 tok/s class model

**Source**: NVIDIA model card for step-3.5-flash

### 3.4 DeepSeek-R1 NIM

- NVIDIA claims "up to 3,872 tokens/sec" on HGX H200 (8× H200)
- System-level number; measure TTFT/ITL in your harness

### 3.5 build.nvidia.com (Serverless)

- "Free serverless APIs for development"
- **Limits**: Vary per model; not published (NVIDIA forum staff)
- **Plan type**: `volatile_free` + telemetry gating

### 3.6 NIM Self-Host

- Cost = GPU rental $/hr ÷ measured throughput
- NIM ON vs OFF shows ~2× throughput improvement in examples

---

## 4. Morph & Relace (Apply/Patch Models)

### 4.1 What They Are

**Not general LLMs** — they are **file merge / patch-application engines** with:

- Very high apply throughput (~10k tok/s class)
- Strict prompt format: `<instruction>…</instruction><code>…</code><update>…</update>`
- Quality = merge correctness, not reasoning

### 4.2 Morph

- **Fast apply**: ~10,500 tok/s, ~96% accuracy
- **High-accuracy apply**: ~4,500 tok/s, ~98% accuracy
- **AWS case study**: "over 10,000 tokens/sec per request", "15,000-token multifile refactor under 400ms"

**Sources**: OpenRouter Morph page, Fly.io writeup, AWS case study

### 4.3 Relace Apply 3

- "Apply updates at 10,000 tokens/sec on average"
- Similar prompt format
- Relace engineering blog: FP8 conversion, speculative decoding

### 4.4 Router Implication

- **Separate role**: `code_apply_patch`
- **Never** compete with reasoners in same candidate set
- Used in **Reason → Apply → Validate** pipeline

---

## 5. New Micro-Roles

| Role                 | Purpose                                           |
| -------------------- | ------------------------------------------------- |
| code_reasoner        | Deep planning, debugging, architecture            |
| code_patch_generator | Outputs minimal edit snippet / patch instructions |
| code_apply_patch     | Morph/Relace-style file merge/apply               |
| code_scaffold_fast   | High-throughput code drafting (Cerebras)          |
| code_small_transform | Small edits, formatting, rename, docstring        |

### Hard Constraints per Role

**code_apply_patch**:

- Must support apply prompt format (`<instruction><code><update>` style)
- Must support large file contexts (Relace lists 256k)

**code_scaffold_fast**:

- Prefers offers with high tps_stream and low ITL
- Quality threshold lower than code_reasoner

---

## 6. Patch DAG Executor (Architecture)

```
┌──────────────────────────┐
│ code_reasoner             │  (Claude/GPT/etc)
│ - plans + writes snippet  │
└─────────────┬────────────┘
              │ edit snippet
              ▼
┌──────────────────────────┐
│ code_apply_patch          │  (Morph/Relace)
│ - merges into file(s)     │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│ validate (tests/lint)     │
└─────────────┬────────────┘
              │ fail → escalate
              ▼
┌──────────────────────────┐
│ code_reasoner (stronger)  │
└──────────────────────────┘
```

**Why Morph/Relace fit**: They remove full-file regeneration from the loop; reasoner outputs small edit snippet, apply model merges at 10k tok/s.

---

## 7. Speed Index Updates (v1.1)

### 7.1 Speed Profile (Per Offer, Per Role)

```
ttft_p50, ttft_p95
itl_p50, itl_p95 (aka TPOT)
tps_stream_p50/p95
queue_ms_p95
throughput_tokens_s@concurrency (optional)
```

### 7.2 Role-Specific Speed Score

**Interactive chat/edit**:

```
speed = queue_p95_ms + ttft_p95_ms + E[out_tokens] * itl_p95_ms
```

**Bulk generation**:

```
speed = queue_p95_ms + ttft_p95_ms + E[out_tokens] / tps_stream_p50
```

**Apply/patch**:

```
speed = apply_ms_p95_per_file
```

---

## 8. Offer Schema Additions

```yaml
speedProfileHints: # vendor claims, priors
  vendor_tps_stream: 2200
  vendor_ttft_ms: 100
  vendor_itl_ms: 0.5

measuredSpeedProfile: # from telemetry
  ttft_p95_ms: 120
  itl_p95_ms: 0.6
  tps_stream_p50: 1800
  queue_p95_ms: 50

quotaModel: # Cerebras Code
  tokensPerDayCap: 120000000
  tpmCap: 1500000
  rpmCap: 120

volatilityRisk: 0.3 # for preview/serverless

promptContract: # Morph/Relace
  contractType: apply_v1
  requiredFormat: "<instruction><code><update>"
  maxContextTokens: 256000
```

---

## 9. ADR Additions (Speed Stack)

| ADR     | Decision                                                             |
| ------- | -------------------------------------------------------------------- |
| ADR-008 | Replace single "tokens/sec" with TTFT + ITL + throughput profile     |
| ADR-009 | Add Patch/Apply stage as first-class routing role                    |
| ADR-010 | Model Cerebras Code as daily-quota bucket plan                       |
| ADR-011 | Treat NVIDIA build.nvidia.com as volatile_free with limits-discovery |
| ADR-012 | Store vendor speed claims as priors; routing uses measured telemetry |

---

## 10. Practical Routing Rules

1. **Apply models never enter same candidate set as reasoners** — separate roles
2. **Cerebras Code daily bucket** — preferred early-day, not late-day
3. **NVIDIA serverless** — canary-only until telemetry stabilizes
4. **Step 3.5 Flash** — "fast-ish" (~100–300 tok/s), not 3000 tok/s class
5. **Morph/Relace** — only pay off if you implement the patch DAG; otherwise value left on table

---

## 11. Ingestion Sources

| Provider     | Sources                                                                |
| ------------ | ---------------------------------------------------------------------- |
| Cerebras     | inference-docs.cerebras.ai, Support FAQ, Pricing page, Blogs           |
| NVIDIA NIM   | NIM microservices page, build.nvidia.com model cards, NIM docs, Forums |
| Morph/Relace | OpenRouter model pages, Morph AWS case study, Relace engineering blog  |

---

## References

- chatgpt3.md, chatgpt4.md
- CHATGPT_PARETO_DEEP_01_FOUNDATIONS.md
- CHATGPT_PARETO_DEEP_02_INDICES_ECONOMICS.md
- CHATGPT_PARETO_DEEP_06_HELIOS_UNIFIED_SPEC.md
