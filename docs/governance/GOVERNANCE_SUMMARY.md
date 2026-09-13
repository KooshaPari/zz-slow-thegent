# Architectural Governance Summary

**Status:** Active
**Scope:** Mandatory harness contract gates for merge readiness

## Core Rule

Merge only when both mandatory harness contract gates pass.

## CI Section

- The `quality` workflow job is fail-closed for harness gates.
- CI always executes both mandatory gates, captures each exit code, and fails the job if either gate fails.
- The quality lane remains limited to these mandatory harness gates; no extra governance lanes are required there.
- Long-lived canary and high-extreme package branches must follow the canonical structured refresh policy in `UNIFIED_WORKTREE_WORKFLOW_GOVERNANCE.md` before merge; the CI workflow enforces that policy via `task quality:governance:canary-refresh`, and the local pre-push contract uses `task quality:pre-push:strict-governance`.
- legacy worktrees are reported separately through `task quality:governance:legacy-remediation-report`; clean legacy lanes are then migrated through `thegent worktree migrate-legacy`, and strict governance still fails until the remaining dirty lanes are migrated or pruned.

## Mandatory Harness Contract Gates

- `task quality:sitback-contracts`
- `task quality:harness-model-contracts`

## Deterministic Benchmark Governance (WL-079)

- CI must run deterministic benchmark smoke via `task bench:smoke:ci`.
- The CI step `Deterministic benchmark smoke` must call the task wrapper only; do not inline raw `cargo bench` in workflow YAML.
- The benchmark command must stay offline and locked:
  `CARGO_NET_OFFLINE=true cargo bench --locked --manifest-path crates/Cargo.toml -p thegent-router --bench audit_bench`
- PR readiness is blocked if the CI step named `Deterministic benchmark smoke` is missing from `.github/workflows/ci.yml`.

## Contract Verification Evidence

Use this compact checklist to verify the contract gates and document outcomes.

| Check                                   | Command                                                                             | Expected outcome                                                 |
| --------------------------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ----------------- |
| Sitback contracts gate                  | `task quality:sitback-contracts`                                                    | Exit code `0`; contract suite reports pass                       |
| Harness model contracts gate            | `task quality:harness-model-contracts`                                              | Exit code `0`; contract suite reports pass                       |
| Gate list present in governance summary | `rg -n "task quality:(sitback-contracts                                             | harness-model-contracts)" docs/governance/GOVERNANCE_SUMMARY.md` | Exactly 2 matches |
| Evidence subsection present             | `rg -n "^## Contract Verification Evidence$" docs/governance/GOVERNANCE_SUMMARY.md` | Exactly 1 match                                                  |

## Quick Links

- Full policy: `docs/governance/ARCHITECTURAL_GOVERNANCE.md`
- Contract definitions: `docs/governance/METRIC_CONTRACTS.md`
- WBS coordination: `docs/reference/WBS_AGENT_PROGRESS.md`

## Batch-1 Agent-6 Verification Note (2026-02-21)

- Command: `uv run pytest -k inject_proxy_models tests/routing/test_request_extensions.py`
- Signal: PASS (`7 passed, 12 deselected`)

## Regression-Spiral Guardrail (2026-02-21)

- After every batch merge, run `task quality:harness-contracts:list-check` first, then run both mandatory gates: `task quality:sitback-contracts` and `task quality:harness-model-contracts`.
- Treat merge readiness as blocked until all three commands exit with code `0` in the post-merge run.

## Operator Checklist (List-Check vs Quick vs Full)

| Chain               | Command                                     | Use when                                                                     |
| ------------------- | ------------------------------------------- | ---------------------------------------------------------------------------- |
| List-check only     | `task quality:harness-contracts:list-check` | Verify harness contract task names are present before running any gate chain |
| Smoke alias         | `task quality:list-check`                   | Run the same list-check through the short alias for a quick preflight        |
| Quick harness chain | `task quality:harness-contracts:quick`      | Run a fast local harness sanity check before commit                          |
| Full harness chain  | `task quality:harness-contracts`            | Run merge-readiness and post-merge harness verification                      |

## Runtime Modularization Matrix (WL-130)

Source: `contracts/runtime/runtime-modularization-matrix.json`
Last Updated: 2026-02-21

| Workload                              | Current                               | Target                                 | Priority | Status      |
| ------------------------------------- | ------------------------------------- | -------------------------------------- | -------- | ----------- |
| CLI dispatch                          | Python monolith (cli.py, impl.py)     | Python frontmatter + Rust helpers      | P0       | in_progress |
| Policy/gate evaluation                | Mixed Python + shell (hooks pipeline) | Rust backmatter (thegent-hooks)        | P0       | in_progress |
| MCP transport/tool registry           | Python monolith (mcp/server.py)       | Python thin transport + Rust utilities | P1       | planned     |
| Low-level memory/layout primitives    | Zig POC interop                       | Zig ABI contract (thegent-zmx-interop) | P2       | planned     |
| Deterministic scoring/ranking kernels | Placeholder Python/Mojo bridge        | Mojo kernel contracts                  | P2       | planned     |

> Machine-readable contract: `contracts/runtime/runtime-modularization-matrix.json`

## Runtime Matrix (B90 Wave-2)

The polyglot runtime modularization matrix is maintained at `contracts/runtime/runtime-modularization-matrix.json`.

| Runtime | Workload                    | Status      |
| ------- | --------------------------- | ----------- |
| Python  | parse_model_suffix baseline | done        |
| Rust    | parse_model_suffixes (PyO3) | in_progress |
| Zig     | ABI contract v1.0.0         | in_progress |
| Mojo    | deterministic kernel smoke  | in_progress |

For promotion criteria, see `docs/governance/POLYGLOT_RUNTIME_COVERAGE_AND_CONVERSION_MATRIX_2026-02-21.md`.

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->

## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.
