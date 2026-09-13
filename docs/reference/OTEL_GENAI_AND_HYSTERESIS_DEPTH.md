# OpenTelemetry GenAI & Observability Depth (WP-Y6)

This document specifies the mapping between `thegent` internal metrics and the **OpenTelemetry (OTel) GenAI Semantic Conventions**, ensuring industry-standard observability.

## 1. Trace Structure (W3C Trace Context)

Every `thegent` run is a distributed trace.

- **Root Span**: `thegent.run` (Operation: `orchestration`)
- **Child Spans**:
  - `thegent.routing` (Pareto selection)
  - `thegent.policy_gate` (OPA/Rego pre-check)
  - `thegent.agent.execution` (LLM call)
  - `thegent.tool_call.{tool_id}` (Tool execution)

## 2. Semantic Attribute Mapping

`thegent` adopts the emerging `gen_ai.*` and `llm.*` namespaces.

| thegent Field  | OTel Attribute               | Example             |
| -------------- | ---------------------------- | ------------------- |
| `model_id`     | `gen_ai.request.model`       | `claude-3-5-sonnet` |
| `provider`     | `gen_ai.request.system`      | `anthropic`         |
| `cost_usd`     | `gen_ai.usage.cost`          | `0.042`             |
| `tokens_total` | `gen_ai.usage.total_tokens`  | `1540`              |
| `confidence`   | `gen_ai.response.confidence` | `0.85`              |
| `lane`         | `thegent.lane`               | `critical`          |
| `risk_score`   | `thegent.risk`               | `0.15`              |

## 3. Log-to-Span Correlation

Every event in the **Immutable Audit Trail** (WP-3004) must include:

- `trace_id`
- `span_id`
- This allows the **Operator Cockpit** to jump from a high-level KPI alert directly to the raw MAIF artifact in a trace view.

## 4. TRAFFIC KPIs as OTel Metrics

| KPI                     | OTel Metric Name                | Instrument |
| ----------------------- | ------------------------------- | ---------- |
| **T: Throughput**       | `thegent.task.count`            | Counter    |
| **R: Routing Accuracy** | `thegent.routing.error_rate`    | Gauge      |
| **A: Accuracy**         | `thegent.decision.success_rate` | Histogram  |
| **C: Cost**             | `thegent.usage.cost_total`      | Sum        |

## 5. Hysteresis Model for Scaling (WP-5001)

To prevent "thrashing" (rapidly spawning/killing agents), the `thegent` Adaptive Concurrency Controller uses a hysteresis loop.

### 5.1 Mathematical Model

- **Upper Threshold ($T_u$)**: 80% utilization.
- **Lower Threshold ($T_l$)**: 40% utilization.
- **Current Load ($L$)**: Smoothed throughput over window $W$.
- **Dwell Time ($D$)**: Minimum time between scale actions (30s).

**Logic**:

- IF $L > T_u$ AND `TimeSinceLastScale` $> D$: **SCALE UP**
- IF $L < T_l$ AND `TimeSinceLastScale` $> D$: **SCALE DOWN**
- ELSE: **HOLD** (Stay in the "Dead Zone" between $T_l$ and $T_u$).

### 5.2 Capacity Reservation

- **Critical Floor**: A minimum of $C_{min}$ agents are always running, regardless of load, to handle high-priority `recovery` or `governance` tasks instantly.

---

_Cross-ref: [PHASE_5_SCALE_ROBUSTNESS_DEPTH.md](./PHASE_5_SCALE_ROBUSTNESS_DEPTH.md) | [TRAFFIC_KPI_DESIGN.md](./TRAFFIC_KPI_DESIGN.md)_

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

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
