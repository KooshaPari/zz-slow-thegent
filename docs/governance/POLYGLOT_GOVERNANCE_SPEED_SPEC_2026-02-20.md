# Polyglot Governance Speed Spec

**Date:** 2026-02-20
**Purpose:** Formal speed-first execution model for all governance gates/checkers across code + non-code surfaces.

---

## 1. Design Goal

Deliver strict governance with low latency by combining:

1. **Fast local loop** (changed-files, bounded checks, immediate feedback),
2. **Strict CI loop** (full-scan and heavier analyzers),
3. **Progressive profile system** (`ultrafast`, `fast`, `standard`, `full`) with explicit SLOs.

This is a governance orchestrator contract, not a replacement for native language analyzers.

---

## 2. Proven Baselines to Reuse

### 2.1 Trace baseline (simple and fast)

- Local pre-commit intentionally optimized for `<5s` with slow checks moved to CI.
- Changed-file filtering and parallel local checks.
- Lightweight local gates for LOC and naming explosion.

Evidence:

- `trace/.pre-commit-config.yaml:1-10`
- `trace/.pre-commit-config.yaml:25-26`
- `trace/.pre-commit-config.yaml:95-121`

### 2.2 Thegent runtime baseline (bounded and cached)

- Stop execution has hard-clamped latency bounds and profile-based hook sets.
- Governance gate dispatcher uses one-time parse + cache + batched evaluation.
- Common layer caches tool availability and quality config reads.

Evidence:

- `thegent/hooks/hook-dispatcher/src/main.rs:1027-1031`
- `thegent/hooks/hook-dispatcher/src/main.rs:2263-2297`
- `thegent/hooks/governance-gates.sh:8-10`
- `thegent/hooks/governance-gates.sh:31-39`
- `thegent/hooks/lib/common.sh:224-251`
- `thegent/hooks/lib/common.sh:288-307`

---

## 3. Execution Profiles (Formal)

| Profile     | Target Use            |  Max Local Wall-Clock | Mandatory Checks                                       |
| ----------- | --------------------- | --------------------: | ------------------------------------------------------ |
| `ultrafast` | tight edit loops      |                 <= 2s | syntax/file sanity + reconcile floor                   |
| `fast`      | default dev loop      |                 <= 5s | lint/format on changed files + core governance floor   |
| `standard`  | pre-push/local verify |                <= 15s | adds stricter type/test subsets + lifecycle gates      |
| `full`      | CI/nightly/release    | unbounded by local UX | full-stack lint/type/test/security/contracts/assurance |

Rules:

1. Local defaults must remain `fast`.
2. `full` profile is authoritative for merge/release gates.
3. Any new gate must declare supported profiles and expected runtime budget.

---

## 4. Speed Contract for All Gates

Every gate/checker must implement:

1. **Scope mode**: `changed` and `all`.
2. **Deterministic cache key**: inputs + config + tool version (or toolchain lock hash).
3. **Bounded timeout**: explicit idle + absolute timeout.
4. **Machine-readable report**: normalized JSON outcome and metrics.
5. **Severity tier**: `advisory`, `soft_fail`, `hard_fail`.

If a checker cannot satisfy this contract, it remains CI-only until adapted.

---

## 5. Unified Pipeline Topology

### Stage A: Preflight (local + CI)

- Changed-files resolution.
- Tool availability + config load cached once.
- Skip non-relevant gates by extension/path policy.

### Stage B: Fast checks (local default)

- Native fast linters/formatters on changed files.
- Shared policy gates (file-length, suppressions, naming, config sanity).

### Stage C: Strict checks (CI + selected local profiles)

- Full type checks, deep lint/security, full tests, contract/traceability assertions.

### Stage D: Assurance/attestation (CI/release)

- SBOM/provenance/contract evidence, reliability trend checks, formal/onchain where applicable.

---

## 6. Language Lane Requirements (Performance-Aware)

For each language lane (Go, TS/JS, Python, Java, C/C++, C#/.NET, Rust, Zig, Mojo, others):

1. Native toolchain lane must expose `lint`, `format`, `test`, and optional `security`.
2. Fast local mode uses changed-files subsets and safe auto-fixes only.
3. Strict CI mode runs full repository scope with artifacts.
4. Lane output is normalized into shared governance schema.

Non-code types (shell, JSON/YAML/TOML, Markdown, contracts, schemas) follow the same profile contract.

---

## 7. Non-Code Governance Performance Model

For governance contracts/traceability/smart-contract-like checks:

1. Parse once, reuse many times per run (batch extraction).
2. Prefer string/builtin matching over expensive process loops where correctness is preserved.
3. Evaluate independent gates in parallel batches with dependency boundaries.
4. Persist cache for repeated unchanged policy runs.

Applies to:

- claim lifecycle, DAG/ledger checks, assurance case, reliability SLO, debt/playbook gates, etc.

---

## 8. SLOs and Telemetry

Minimum telemetry per gate:

- `duration_ms`
- `scope` (`changed`/`all`)
- `cache_hit` (bool)
- `result` (pass/warn/fail/na)
- `profile`

Minimum SLOs:

1. `fast` local profile p95 <= 5s.
2. Cache hit ratio >= 70% on repeated local runs (same branch/session).
3. No single local gate > 2s p95 without explicit waiver.
4. CI full lane reports per-stage timings and regression deltas.

---

## 9. Optimization Playbook (Mandatory Order)

1. **Filter first**: limit by changed files/path/extension.
2. **Cache second**: config/tool/status/gate outputs.
3. **Batch third**: parse once, evaluate many.
4. **Parallelize fourth**: only independent checks.
5. **Rewrite fifth**: custom/native rewrite only after measured bottleneck remains.

---

## 10. Rollout Steps

### Step 1 (immediate)

- Enforce shared max-lines gate in `fast` local + CI `full`.
- Add per-gate timing and cache-hit output fields.

### Step 2

- Make each language lane declare profile support and SLO budget.
- Wire missing lanes progressively (Rust/Go/TS first, then secondary stacks).

### Step 3

- Convert advanced governance stubs to evaluators where required by profile `full`.
- Add nightly performance regression for gate runtime budgets.

---

## 11. Definition of Done

A stack/surface reaches parity only when:

1. It is wired in pre-commit/task/CI with profile support.
2. It emits normalized machine-readable reports.
3. It meets profile SLO budgets in observed telemetry.
4. It has exception governance (owner/reason/expiry) for any temporary relaxations.

---

## 12. Lane Commands (WL-134 Slice)

The canonical lane entry points are now:

1. `task test:fast-lane`

- Intended cadence: default local + PR loop.
- Includes: `test:unit` + `test:hooks:selector-fast`.

2. `task test:nightly-lane`

- Intended cadence: nightly/deep validation.
- Includes: `test:hooks:governance` + `test:pyramid`.

Policy:

1. New expensive checks go to nightly lane first unless they meet fast-lane SLO.
2. Fast lane stays bounded and contract-focused.

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->

## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.
