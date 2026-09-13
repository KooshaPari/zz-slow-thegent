<DONE>
# ChatGPT Pareto Router Deep Research — Part 3: API, Pipelines & User Journeys

**Source**: chatgpt3.md, chatgpt4.md
**Date**: 2026-02-18
**Scope**: User journeys, API processes, data pipelines, execution flow

---

## 1. User Journeys

### Journey A — "Route a request" (Hot Path)

**Actor**: App / agent / IDE extension
**Goal**: Pick best offer under constraints, execute, log, fallback if needed.

**Flow**:

1. Client sends request with role, hardConstraints, prompt/messages, optional budgets
2. Router loads latest snapshot: offers + capabilities, pricing + shadow prices, telemetry + predicted latency, quality indices per role
3. Router filters hard constraints
4. Router computes objective vectors, Pareto frontier, lexicographic pick
5. Router executes call via gateway/provider adapter
6. Router logs telemetry + usage and returns response + route metadata
7. If call fails → router executes fallback chain until success or terminal failure

**Outputs**: response, routeTrace, offerId, fallbackUsed?, cost estimate, usage tokens, latency stats

### Journey B — "Add a new provider"

**Actor**: Admin/devops
**Goal**: Integrate a new provider with minimal effort.

**Flow**:

1. Implement adapter interface (metadata + usage + execution)
2. Register adapter + credentials in secrets manager
3. Run "adapter validation" job: list models, fetch pricing, execute test request
4. Provider offers appear in Offer Registry with state=inactive
5. Enable provider for limited roles / canary percent
6. Observe telemetry; gradually expand

### Journey C — "Subscription changes mid-month"

**Actor**: System + admin
**Goal**: Keep effective costs accurate and prevent quota blowups.

**Flow**:

1. Subscription adapter scrapes usage/quota/renewal date
2. Commercial Engine recomputes: remaining quotas, throttling risk, shadow prices
3. Budget allocator may: tighten per-role caps, enable cheaper offers, enter degraded mode if nearing burn limit

### Journey D — "Degraded mode after budget burn"

**Actor**: System
**Goal**: Keep service alive within budget.

**Flow**:

1. Budget burn crosses threshold (e.g. 85% of monthly)
2. Router policy flips: disables premium offers, forces cache-first behavior, prioritizes self-host / low-cost API models
3. User receives responses with "degraded mode" metadata

---

## 2. Core API (Hot Path)

### POST /v1/route — Route + Execute (One Stop)

**Request**:

```json
{
  "role": "code_complex",
  "messages": [...],
  "hard": {
    "maxCostUsd": 0.12,
    "maxLatencyMsP95": 2500,
    "minQuality": 0.78,
    "needsTools": true,
    "needsJson": false,
    "minContextTokens": 32000
  },
  "soft": {
    "optOrder": ["quality", "cost", "speed"],
    "epsilon": { "quality": 0.02, "cost": 0.10, "speed": 0.15 }
  },
  "meta": {
    "projectId": "atoms",
    "userId": "u_123",
    "traceId": "t_..."
  }
}
```

**Response**:

```json
{
  "response": {...},
  "routeTrace": {
    "selectedOfferId": "openrouter:anthropic:claude-opus:us-east",
    "paretoSet": ["...", "..."],
    "fallbackChain": ["...", "..."],
    "fallbackUsed": false,
    "scores": {
      "speedScore": 1880,
      "costUsd": 0.083,
      "qualityScore": 0.84
    }
  },
  "usage": {
    "promptTokens": 12450,
    "completionTokens": 2800,
    "totalTokens": 15250
  }
}
```

### POST /v1/plan — Dry-Run

Returns route decision only (no execution). Used for debugging, testing, CI.

### Optional: Plan-Only Router (Agent Frameworks)

For complex agents:

- Route each step differently (planner vs coder vs reviewer)
- Or run N candidates cheap then validate with strong model

**Endpoints**:

- `POST /v1/route/planOnly`
- `POST /v1/route/executeSelected`

---

## 3. Admin APIs

| Endpoint                                      | Purpose                                                          |
| --------------------------------------------- | ---------------------------------------------------------------- |
| `POST /v1/admin/providers/:providerId/enable` | Enable provider offers (optionally scoped by roles)              |
| `POST /v1/admin/offers/:offerId/state`        | Set active \| inactive \| canary \| blocked                      |
| `POST /v1/admin/policies`                     | Update role policies (constraints + opt order)                   |
| `GET /v1/admin/health`                        | Shows provider health, error rates, disabled offers, budget burn |

---

## 4. Pipelines (Data + Control Plane)

### Pipeline 1 — Offer & Metadata Ingestion

**Goal**: Keep offer registry accurate.

**Inputs**:

- OpenRouter models/pricing API
- Vercel AI Gateway model mappings
- Direct provider docs/APIs
- Self-host registry (inference fleet inventory)

**Stages**:

1. Fetch raw model lists and pricing
2. Normalize to canonical Offer
3. Deduplicate and assign stable offerId
4. Validate capabilities via probe calls (optional)
5. Write to Offer Registry + version snapshot

**ASCII**:

```
[Provider APIs]     [Docs/HTML]     [Self-host Fleet]
      |                 |                |
      +-------> [Adapters / Scrapers] <---+
                       |
                       v
              [Normalizer + Validator]
                       |
                       v
               [Offer Registry (db)]
                       |
                       v
             [Offer Snapshot (immutable)]
```

### Pipeline 2 — Telemetry & Observability

**Goal**: Build speed/reliability predictors and online quality stats.

**Inputs**:

- Router execution traces
- Gateway logs (Vercel, LiteLLM, OpenRouter metadata)
- Local inference metrics (vLLM, TGI, etc.)

**Stages**:

1. Log per-request metrics: latency (TTFT, total), tokens in/out, cache hit/miss, errors + retries, output schema validity
2. Aggregate into rolling windows (5m, 1h, 24h): p50/p95, error rate, adherence rate
3. Publish "Telemetry Snapshot" used by router hot path

**ASCII**:

```
  [Router Calls]
       |
       v
[Event Log / Queue] ---> [Stream Aggregator] ---> [Telemetry DB]
                                 |
                                 v
                       [Telemetry Snapshot]
                                 |
                                 v
                           (Hot Path)
```

### Pipeline 3 — Economics: Subscriptions, Budgets, Shadow Prices

**Goal**: Convert messy subscription rules into effective marginal cost.

**Inputs**:

- Subscription dashboards (scraped)
- Provider billing usage endpoints
- Your metering (truth source)
- Seasonal multipliers + promos
- Manual overrides ("freeze spending on provider X")

**Stages**:

1. Scrape/ingest current plan status: remaining quota, renewal date, throttle regime
2. Compute: remaining_ratio vs expected_remaining (time-based), shadow price per plan/model
3. Produce effectiveUnitCost function parameters per offer
4. Budget allocator: sets role budgets and per-day burn caps, triggers degraded mode flags

**ASCII**:

```
[Sub Dashboards] [Billing APIs] [Your Metering]
       |              |             |
       +-------> [Plan Adapters / Scrapers]
                      |
                      v
           [Commercial Engine]
   (quota, multipliers, throttle, shadow)
                      |
                      v
        [Effective Cost Table + Budgets]
                      |
                      v
                 (Hot Path)
```

---

## 5. Hot Path Data Model (Snapshots)

Router runs purely off **snapshots** (fast, deterministic):

| Snapshot          | Contents                                     |
| ----------------- | -------------------------------------------- |
| OfferSnapshot     | Capabilities + base pricing                  |
| TelemetrySnapshot | Latency/errors/adherence                     |
| EconomicsSnapshot | Effective cost + shadow price + budget state |
| QualitySnapshot   | Per-role quality indices                     |

**ASCII**:

```
                   ┌────────────────────────┐
Request + Role ---> │ Router Hot Path        │
                   │  loads snapshots:       │
                   │  - OfferSnapshot        │
                   │  - TelemetrySnapshot    │
                   │  - EconomicsSnapshot    │
                   │  - QualitySnapshot      │
                   └───────────┬────────────┘
                               v
            Hard Filters -> Pareto -> LexiPick -> Execute -> Log
```

---

## 6. Execution + Fallback Process

### Failure Types → Fallback Action

| Failure Type               | Fallback Action                       |
| -------------------------- | ------------------------------------- |
| Rate limit / 429           | Switch provider/offer immediately     |
| Timeout                    | Switch to fastest offer on Pareto set |
| Schema/tool failure        | Switch to "high adherence" offer      |
| Bad output quality (tests) | Escalate to higher quality tier       |

### Fallback Chain Generator

1. Next best on Pareto frontier
2. Same provider, different region (if helpful)
3. Different provider, same "tier"
4. Safe high-adherence model
5. Cheapest survivable fallback (self-host)

### Example Fallback Chain

```
[openrouter:claude-opus:us-east]
 -> if 429: [google:gemini-flash:us-central]
 -> if schema fail: [direct-anthropic:claude-opus:us-west]
 -> if all fail: [selfhost:qwen-coder-32b:phoenix]  (if tools not required)
```

---

## 7. Deliverables Checklist

- [ ] Canonical Offer schema + snapshots
- [ ] Adapter interfaces + initial adapters (OpenRouter, Vercel, self-host)
- [ ] Telemetry event schema + aggregator
- [ ] Subscription plan schema + shadow pricing engine
- [ ] Router service (hard filters + pareto + lexi + fallback)
- [ ] Admin policy editor (roles + budgets)
- [ ] Dashboards: spend, latency, routing decisions, failovers

---

## References

- chatgpt3.md, chatgpt4.md
- CHATGPT_PARETO_DEEP_01_FOUNDATIONS.md
- CHATGPT_PARETO_DEEP_02_INDICES_ECONOMICS.md
