# Polyglot Governance Parity Audit

**Date:** 2026-02-20
**Repo:** `thegent`
**Status:** Audit complete, rollout plan defined

---

## 1. Scope

This audit covers:

- Language families: Go, TS/JS (+ variations), Python (+ variations), Java, C/C++, C#/.NET, Rust, Zig, Mojo, and additional supported stacks.
- Non-language file types: shell, JSON/YAML/TOML, Markdown, infra/config artifacts.
- Non-file/program governance: traceability, contracts, attestation, reliability/SLO, debt/playbook contracts, and on-chain/formal governance hooks.

Parity target means each stack has:

1. Lint + format + test baseline.
2. Security/dependency checks where applicable.
3. Pre-commit + CI + task-runner integration.
4. Shared governance overlays (file length, suppression policy, traceability/reporting).

---

## 2. Evidence Anchors

- Templates inventory: `templates/quality/` (multi-stack policies and tool configs).
- Runtime hooks and gate engine: `hooks/governance-gates.sh`, `hooks/hook-config.yaml`, `hooks/async-test-runner.sh`.
- Current execution wiring:
  - `Taskfile.yml` (quality tasks),
  - `.pre-commit-config.yaml` (local gates),
  - `.github/workflows/ci.yml` (CI),
  - `.github/workflows/release.yml` (SBOM/provenance).
- Shared max-lines gate implementation:
  - `scripts/max-lines-gate.sh`,
  - `crates/thegent-utils/src/bin/max_lines.rs`.
- Speed contract:
  - `docs/governance/POLYGLOT_GOVERNANCE_SPEED_SPEC_2026-02-20.md`.

---

## 3. Current Parity Matrix (Code + File Types)

Legend:

- `A` = active and wired in current repo execution path.
- `P` = partially wired (some pieces exist, not full parity).
- `T` = template-ready only (governance intent exists, not wired).
- `M` = missing.

| Surface                                           |                               Templates | Task/Hook/CI Wiring | Status | Notes                                                                                                        |
| ------------------------------------------------- | --------------------------------------: | ------------------: | ------ | ------------------------------------------------------------------------------------------------------------ |
| Python (py, pyi)                                  |                                     Yes |              Strong | `A`    | Ruff/ty/basedpyright/mypy/pytest/security present in task + CI.                                              |
| Go                                                |                                     Yes |             Partial | `P`    | Go exists in max-lines + hook extension lists; no dedicated Go lane in main `thegent` CI.                    |
| TS/JS (ts,tsx,js,jsx,mjs,cjs)                     |                                     Yes |             Partial | `P`    | Oxlint template parity logic exists in governance gate; not fully wired as first-class CI lane in `thegent`. |
| Shell (sh,zsh,bash,bats)                          |                                     Yes |             Partial | `P`    | ShellCheck in Taskfile and template; not enforced in CI workflow currently.                                  |
| JSON/YAML/TOML                                    |                                     Yes |             Partial | `P`    | pre-commit checks exist; stronger schema policy exists mostly in governance hooks.                           |
| Markdown/docs                                     |       Yes (markdownlint/vale templates) |                Weak | `P`    | Docs build gate exists; markdown lint policy not fully wired in CI/pre-commit.                               |
| Rust                                              |                                     Yes |             Partial | `P`    | Rust assets and benchmarks exist; no first-class fmt/clippy/test/audit lane in main CI yet.                  |
| Zig                                               |              No dedicated template file |             Partial | `P`    | Tooling setup + build and max-lines support exist; no fmt/test policy lane wired.                            |
| Mojo                                              |              No dedicated template file |             Minimal | `P`    | Mentioned in setup and max-lines extension list; no formatter/test/security lanes wired.                     |
| Java                                              |                        Yes (checkstyle) |       Template only | `T`    | No active Java lint/test lane wired.                                                                         |
| C/C++                                             |               Yes (clang-tidy/cppcheck) |       Template only | `T`    | No active C/C++ lane wired.                                                                                  |
| C#/.NET                                           | No dedicated quality template currently |             Missing | `M`    | No active .NET lane or template in current quality set.                                                      |
| Kotlin/Swift/Dart/PHP/Ruby/Perl/Lua/Terraform/etc |                 Yes (various templates) |       Template only | `T`    | Policy scaffolding exists but not executed as lanes.                                                         |

---

## 4. Shared Cross-Language Governance Status

| Cross-language Gate                   | Status                        | Notes                                                                                                         |
| ------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Max file length gate                  | `P`                           | Implemented (Rust + Zig runner + shell wrapper) but not yet fully wired into pre-commit + CI + task defaults. |
| Suppression policy blocker            | `A` (template), `P` (runtime) | Template pre-commit rule exists; repo-level full enforcement still needs unified rollout.                     |
| Smart changed-file execution          | `A`                           | Hook config supports changed/all scopes and incremental analysis.                                             |
| Async test dispatch by file extension | `A`                           | Broad extension routing exists across many languages.                                                         |
| Trace parity template audit           | `A` (for py/go/oxlint)        | Existing trace parity gate currently focuses on ruff/golangci/oxlint semantics.                               |
| Per-stack policy spec centralization  | `P`                           | Strong template inventory exists; stack execution contracts are uneven.                                       |

---

## 5. Non-File / Program Governance (Contracts, Traceability, Smart Governance)

Current governance engine already supports extensive non-code controls:

- PRD/ledger/DAG compile and lifecycle gates.
- Agent claim schema + evidence lifecycle validation.
- Reliability SLO and flake quarantine governance.
- Brownfield/greenfield/probabilistic delivery-model gates.
- Rolling-wave and assurance-case schema gates.
- Privacy proof, on-chain adapter/transition gates.
- Formal methods and formal registry gates.
- Debt registry and playbook contract gates.
- Artifact quality and SCC metrics gate.

### Important gaps in this layer

1. `onchain-contract` gate currently reports stub mode when contracts exist but toolchain gates are not installed/evaluated.
2. `formal-methods` gate currently reports stub mode when formal specs exist but TLC/Dafny/Alloy evaluators are not installed/wired.
3. Schema coverage is uneven between contract artifacts and repository-level schema directories; some gates rely on runtime/project-local schemas.

Net: governance architecture is strong, but some advanced assurance gates are still stubs or environment-dependent.

---

## 6. Gap Summary by Priority

### Priority 0 (already strong)

- Python baseline quality lane.
- Governance gate framework for non-code artifacts and policy enforcement.
- Release SBOM/provenance path.

### Priority 1 (close to parity, finish wiring)

- Rust lane: fmt + clippy + tests + security dependency checks.
- TS/JS lane: strict lint/format/test lane in CI aligned with policy templates.
- Go lane: first-class CI/task parity in this repo.
- Shared max-lines gate: enforce in pre-commit/CI/task.

### Priority 2 (template-rich, execution-poor)

- Java and C/C++ lanes from existing templates.
- Shell/docs/config lint gates as consistent mandatory checks.

### Priority 3 (missing foundation)

- C#/.NET lane definition (toolchain, templates, CI hooks).
- Mojo and Zig dedicated formatter/test lane definitions.

---

## 7. Formal Rollout Plan (Phased)

### Phase A: Core parity substrate (all stacks)

1. Wire shared max-lines gate in pre-commit + CI + `task lint`.
2. Define normalized output schema for all check runners.
3. Add policy severity tiers (`advisory`, `soft_fail`, `hard_fail`) with explicit owner/date.

### Phase B: Primary stack parity (Go/TS/Python/Rust/Shell)

1. Rust: `fmt`, `clippy`, `test`, dependency/security checks.
2. Go: format/lint/test/security parity in this repo’s CI and tasks.
3. TS/JS: strict lint/format/type/test lane aligned with oxlint template + boundaries policy.
4. Shell/docs/config: shellcheck + markdown/config linting lanes.

### Phase C: Secondary stack activation (Java/C/C++/Zig/Mojo/.NET)

1. Activate Java lane from checkstyle template + test lane.
2. Activate C/C++ lane from clang-tidy/cppcheck templates + build/test lane.
3. Add Zig lane (`fmt`/build/test) and Mojo lane (`format`/compile/test) policies.
4. Add C#/.NET baseline lane (format/lint/build/test/security) and add template set.

### Phase D: Advanced governance completion

1. Replace stub on-chain/formal gates with real toolchain-backed evaluators where applicable.
2. Add schema hard-fail checks for all contract outputs.
3. Add governance SLO dashboards (gate latency, flake, failure trend, waiver debt).

---

## 8. Execution Rules (Required)

1. Native tool semantics stay native; thegent orchestrates and governs.
2. Adapter/wrapper first, rewriter last.
3. Every exception/waiver requires owner, reason, expiry, and cleanup issue.
4. New lanes start advisory and graduate to hard-fail only after baseline stabilization.
5. All lanes must support changed-files mode locally and full-scan mode in CI/nightly.

---

## 9. Immediate Next Batch

1. Integrate max-lines gate into:
   - `.pre-commit-config.yaml`,
   - `Taskfile.yml` (`lint` path),
   - `.github/workflows/ci.yml` (`quality` job).
2. Add Rust quality job in CI (fmt + clippy + tests + audit/deny).
3. Add shell/docs/config job in CI (shellcheck + markdown/config lint).
4. Draft lane spec for Java/C/C++/Zig/Mojo/.NET in a single policy contract file for staged activation.

---

## 10. Optimization Canon (Required)

Implementation must follow the speed spec:

1. Profile-driven execution (`ultrafast|fast|standard|full`).
2. Changed-file first, full-scan in CI/nightly.
3. Parse/config/tool availability cached once per run.
4. Parallelize only independent gates with bounded timeout.
5. Emit per-gate telemetry (`duration_ms`, `cache_hit`, `scope`, `profile`).

Reference: `docs/governance/POLYGLOT_GOVERNANCE_SPEED_SPEC_2026-02-20.md`.

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->

## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.
