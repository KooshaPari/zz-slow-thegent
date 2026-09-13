# Fallback Control Plane

**Status:** Authoritative
**Date:** 2026-02-14
**Scope:** Normalization fallback policy for MCP and CLI

---

## 1. Purpose

When agent output cannot be normalized via a provider adapter (XML, JSON, etc.), thegent falls back to plain-text extraction. This document defines the **fallback control plane**: policy, observability, and guardrails that govern when fallback is acceptable.

---

## 2. Policy Configuration

| Config                                          | Default | Description                                                     |
| ----------------------------------------------- | ------- | --------------------------------------------------------------- |
| `THGENT_NORMALIZATION_POLICY_ALLOW_FALLBACK`    | true    | Allow plain-text fallback when adapter fails                    |
| `THGENT_NORMALIZATION_POLICY_MIN_CONFIDENCE`    | 0.4     | Minimum confidence threshold; below triggers policy violation   |
| `THGENT_NORMALIZATION_POLICY_MAX_FALLBACK_RATE` | 0.3     | Max global fallback rate (30%); above triggers policy violation |
| `THGENT_NORMALIZATION_POLICY_STRICT_PROVIDERS`  | ""      | Comma-separated providers that must never use fallback          |

---

## 3. Fallback Flow

1. **Adapter attempt:** Provider adapter (e.g. XMLOutputAdapter for gemini) normalizes raw output.
2. **On failure:** If adapter throws or returns parse_errors, fallback is considered.
3. **Fallback:** `extract_condensed()` produces a minimal CSM with `source_contract="fallback-plain"`, confidence 0.3–0.5.
4. **Policy evaluation:** `evaluate_fallback()` checks strict providers, confidence, global fallback rate.
5. **Telemetry:** `ContractTelemetry.record_normalization()` records fallback events for observability.

---

## 4. MCP and CLI Parity

Both MCP `thegent_run` and CLI `thegent run` use the same `run_with_failover` path, which:

- Calls `normalize_output(agent, raw)` after each run
- Evaluates `evaluate_fallback()` with config-driven `FallbackPolicy`
- Records to `ContractTelemetry` for drift detection

**MCP fallback policy** = same as CLI; no separate MCP-specific policy.

---

## 5. Observability

- **ContractTelemetry:** Tracks fallback rate per provider and globally.
- **Drift detection:** `detect_drift()` flags significant fallback rate increases.
- **Fallback KPIs (G-CA-02 B3):** `get_fallback_kpis()` returns structured metrics; `thegent observe kpis` for dashboard/alerting.
- **Parser-quality routing (G-CA-02 B2):** `rank_providers_by_parser_quality()` orders providers by confidence/fallback; enabled via `THGENT_ROUTING_PARSER_QUALITY_ENABLED`.
- **Session dir:** Telemetry stored under `THGENT_SESSION_DIR` (default `.thegent/sessions`).

---

## 6. Guardrails

| Guardrail                  | Behavior                                                                                                                      |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Critical lane (G-CA-03 C3) | `--lane critical` rejects runs with `source_contract` fallback-plain or unknown; run fails with error_class unknown_contract. |
| Strict provider            | If provider in `strict_providers`, fallback is blocked; `SemanticValidationError` raised when `allow_fallback=False`.         |
| Confidence threshold       | Below `min_confidence_threshold` → policy violation logged.                                                                   |
| Max fallback rate          | Global rate > `max_fallback_rate` → policy violation logged.                                                                  |
| Parse error class          | `parse_truncated` from `extract_condensed_validated` → adapter result returned (no fallback to COMPLETED).                    |

---

## 7. Implementation

- **Policy:** `src/thegent/contracts/policy.py` — `FallbackPolicy`, `evaluate_fallback`
- **Config:** `src/thegent/config.py` — `normalization_policy_*`
- **Telemetry:** `src/thegent/contracts/telemetry.py` — `ContractTelemetry`
- **Usage:** `src/thegent/cli_impl.py` — `run_with_failover`

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index
- [PROVIDER_ADAPTER_CONTRACTS.md](./PROVIDER_ADAPTER_CONTRACTS.md) — adapter contracts
