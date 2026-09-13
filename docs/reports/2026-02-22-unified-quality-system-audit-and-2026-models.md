# Unified Quality System Audit + 2026 Model Research

Date: 2026-02-22
Scope: `thegent` + available sibling repos in `/Users/kooshapari/temp-PRODVERCEL/485/kush`

## Executive Answer

You already have meaningful groundwork for an in-house unified quality platform, but it is not yet a full cross-language, project-system orchestrator with first-class custom rules and centralized scoring.

Current state is best described as:

- `thegent`: strong runtime/orchestration skeleton (`thegent-hooks` Rust runtime + hook dispatcher + Taskfile quality chains).
- `trace`: advanced consumer of shared quality DAG/task templates.
- `atoms-mcp-prod`: robust Python quality/testing conventions, but not unified with `thegent-hooks` runtime.
- Missing: one canonical cross-language rule model, SARIF-native aggregation, custom-checker SDK, and portfolio-wide governance dashboard.

## What Exists Today (Concrete Evidence)

### A) Thegent has a native quality/security runtime (Rust)

- Wrapper -> native runtime:
  - `hooks/quality-gate.sh` executes `thegent-hooks quality-gate`.
  - `hooks/security-pipeline.sh` executes `thegent-hooks security-pipeline`.
- Runtime crate exists and is active:
  - `crates/thegent-hooks/Cargo.toml`
  - `crates/thegent-hooks/src/bin/quality-gate.rs`
  - `crates/thegent-hooks/src/bin/security-pipeline.rs`
  - `crates/thegent-hooks/src/main.rs`

### B) Existing evaluator capabilities are real but still narrow

- Quality evaluator currently parses:
  - Ruff JSON
  - OXlint JSON
  - coverage JSON
- Complexity is currently proxy/heuristic rather than deep AST/CFG-level analyzer.
  - File: `crates/thegent-hooks/src/quality.rs`
- Security evaluator currently supports:
  - regex secret detection (OpenAI/GitHub/AWS/etc.)
  - Semgrep JSON parsing
  - severity threshold-based blocking
  - File: `crates/thegent-hooks/src/security.rs`

### C) Hook dispatcher already encodes anti-pattern governance signals

- Dispatcher references anti-pattern categories (`test-skipping`, `lint-skipping`, `quality-shortcut`, etc.)
  - File: `hooks/hook-dispatcher/src/main.rs`
- Hook execution registry includes quality/security and multiple QA/gate hooks.

### D) Task-level orchestration is already broad in thegent

- Full quality chain task exists (`quality:`) and includes lint/tests/contracts/traceability.
  - File: `Taskfile.yml`
- Includes strict lanes such as harness contracts, provider gate, runtime contracts, instruction architecture checks.

### E) Cross-repo signals

- `trace` imports shared quality task templates and exposes quality DAG/TUI/report workflows.
  - File: `trace/Taskfile.yml`
- `atoms-mcp-prod` has strong test/marker/lint/type infra (pytest markers, ruff, mypy, xdist), but appears as a separate quality system rather than unified runtime.
  - Files: `atoms-mcp-prod/pyproject.toml`, `atoms-mcp-prod/Taskfile.yml`
- Not locally present in this workspace snapshot:
  - `/Users/kooshapari/temp-PRODVERCEL/485/kush/kwality`
  - `/Users/kooshapari/temp-PRODVERCEL/485/kush/atomsAgent`

## Gap: Why this is not yet the full “Unified Quality Tool”

1. No single canonical finding schema across all tools/projects (SARIF is not yet the universal internal contract).
2. No project-system profile engine that cleanly maps language/toolchain/project-type -> required gates.
3. Custom rule story is fragmented (tool-native configs, scripts, hook logic), not one plugin/rulepack API.
4. No consolidated portfolio dashboard for quality posture across repos.
5. No consistent generated-code anti-pattern score (mutation score, property-coverage score, perf regression score) in one place.

## 2026 Model Systems Research (Primary-source oriented)

### Sonar model (SonarQube/SonarCloud)

What it gives you out-of-the-box:

- Centralized quality profiles/gates, issue triage, trend dashboards, and PR decoration.
- Broad language coverage and rule catalogs.
- Strong governance model for teams/orgs.

What it does not remove:

- You still need custom orchestration when combining non-Sonar scanners and custom in-house analyzers.
- Toolchain-specific scripts and non-native metrics (e.g., mutation/perf/test-graph metrics) still require integration work.

Useful if you want:

- A ready control-plane and UI fast.
- Standardized gate governance and auditability.

### GitHub Code Scanning + SARIF model

- SARIF upload/action model is a powerful neutral interchange layer.
- Good for multi-tool ingestion and centralized PR feedback in GitHub.
- Strong fit if your repos already operate heavily in GitHub Actions.

### Semgrep/CodeQL model

- Semgrep: fast custom rule authoring and broad language support.
- CodeQL: deep semantic/security analysis with high signal for supported languages.
- Together: practical “fast + deep” security/code-quality stack.

### Qodana/other platform models

- IDE-friendly and CI integrations; useful for team productivity and policy baseline.
- Still not a replacement for a custom cross-repo orchestration layer if you need bespoke scoring and rule economics.

## Recommended Target Architecture (Build your own, integrate best-of-breed)

### 1) Core Contract: Unified Finding + Metric Schema

- Use SARIF as external interchange.
- Define internal envelope:
  - `finding` (normalized SARIF-derived fields)
  - `metric` (coverage, complexity, perf deltas, mutation score, flake rate)
  - `policy_decision` (gate, waiver, owner, expiry)

### 2) Adapter Layer

Implement adapters for:

- Ruff/OXlint/Pylint/ESLint
- Semgrep/CodeQL/Bandit
- SCA scanners (OSV/pip-audit/etc.)
- Perf/testing tools (pytest-benchmark, mutmut, property-test outputs)

Each adapter outputs unified schema + provenance.

### 3) Rulepack + Custom Checker SDK

- `rulepacks/<org>/<domain>/<version>/...`
- checker SDK contract:
  - input manifest (files, language, diff range, project profile)
  - output schema (findings + metrics)
- Allow custom checkers in Python/Rust/Go with one wire format.

### 4) Project-System Profiles

- Profile examples:
  - `python-service-strict`
  - `go-cli-fast`
  - `polyglot-agent-core`
- Profiles define required lanes and thresholds, not raw commands.

### 5) Decision Engine (Policy)

- Keep/extend existing policy gate capability (OPA-style conditions already present in thegent governance surfaces).
- Evaluate:
  - block/warn/allow
  - waiver validity
  - regression budgets

### 6) Portfolio Visibility

- Repo-level + org-level scorecards:
  - quality score
  - security score
  - generated-code risk score
  - trend + burn-down + flake budget

## Generated-Code-Specific Quality Model (Must-have)

Add first-class metrics for generated code:

1. Anti-pattern density (per KLOC)
2. Mutation score (critical modules)
3. Property-test coverage (critical logic paths)
4. Benchmark regression index (p50/p95)
5. Flake rate and nondeterminism score
6. Diff risk score (complexity delta + ownership + blast radius)

Gate on these, not only lint/test pass.

## Build-vs-Buy Decision (Pragmatic)

- If you need speed and governance UI now: pilot SonarQube/SonarCloud as control-plane, keep custom adapters for gaps.
- If you need maximum flexibility/custom scoring across many bespoke tools: keep building in-house orchestrator with SARIF core and policy engine.
- Likely best path: hybrid.
  - Use platform (Sonar/GitHub scanning) for standardized analysis and reporting.
  - Use your own orchestrator for custom checkers, generated-code metrics, and cross-repo policy economics.

## 90-Day Rollout Proposal

### Phase 1 (Weeks 1-3): Normalize

- Freeze unified schema (SARIF+metrics envelope).
- Build adapters for currently used core tools in thegent.
- Emit machine-readable artifacts per run.

### Phase 2 (Weeks 4-7): Govern

- Add profile system and policy decisions (block/warn/waive).
- Add waiver lifecycle enforcement (owner + expiry + audit).

### Phase 3 (Weeks 8-10): Generated-code intelligence

- Add mutation/property/perf adapters.
- Introduce generated-code risk gates for selected repos.

### Phase 4 (Weeks 11-13): Portfolio

- Cross-repo dashboard and trend reporting.
- Promote stable gates to required checks.

## Immediate Next Actions (High-Leverage)

1. Extract current `thegent-hooks` output into one explicit JSON contract file and version it.
   - Status (2026-02-22): complete for v1 baseline.
   - Added v1 input contracts and executable validation tests:
     - `schemas/thegent-hooks-quality-gate-input-v1.schema.json`
     - `schemas/thegent-hooks-security-pipeline-input-v1.schema.json`
     - `crates/thegent-hooks/tests/hook_io_contracts.rs`
   - Added v1 output/result envelope contract and runtime emit path:
     - `schemas/thegent-hooks-result-v1.schema.json`
     - `crates/thegent-hooks/tests/hook_output_contracts.rs`
     - `hooks/quality-gate.sh` -> `artifacts/hooks/quality-gate-result.json`
     - `hooks/security-pipeline.sh` -> `artifacts/hooks/security-pipeline-result.json`
2. Add SARIF export bridge for current findings.
   - Status (2026-02-22): baseline bridge implemented.
   - `scripts/export_hook_results_to_sarif.py` maps hook envelope checks to SARIF results.
   - Task wiring: `quality:hooks:sarif`.
3. Implement first custom checker SDK example (anti-pattern checker for generated Python code).
   - Status (2026-02-22): baseline checker implemented.
   - `scripts/check_generated_python_antipatterns.py` emits JSON + SARIF and supports severity fail gate.
   - Task wiring: `quality:generated-python:antipatterns`.
4. Add mutation/perf gate pilot to one repo (`thegent` or `trace`) as non-blocking nightly.
   - Status (2026-02-22): baseline pilot lane implemented in `thegent`.
   - `scripts/mutation_perf_pilot.py` writes a unified pilot artifact and keeps mutation stage non-blocking when `mutmut` is unavailable.
   - Task wiring: `quality:pilot:mutation-perf`.
5. Decide control-plane posture:
   - Status (2026-02-22): decided and ratified.
   - Decision: GitHub+SARIF-native only as default control plane, with optional Sonar downstream adapter.
   - ADR: `ADR-017` + `docs/reference/ADR-017-unified-quality-control-plane.md`.
   - Enforced by contract: `contracts/quality-control-plane-v1.json` validated via `schemas/quality-control-plane-v1.schema.json`.

## Execution Addendum: "Do It + 10 More" (2026-02-22)

- Added control-plane ADR and policy contract validation/report scripts.
- Added unified quality aggregate lane (`quality:ci:unified`) and explicit contract/report tasks.
- Added tests for SARIF export, generated-Python checker, mutation/perf pilot, and control-plane scripts.
- Added canonical unified summary artifact generator:
  - `scripts/aggregate_unified_quality_summary.py`
  - `schemas/unified-quality-summary-v1.schema.json`
  - task: `quality:summary`
- Added CI wiring in `.github/workflows/ci.yml`:
  - `quality-unified` job (PR + nightly schedule) running `task quality:ci:unified`
  - uploads `artifacts/hooks` and `artifacts/quality`
  - uploads SARIF outputs to GitHub code scanning (`hooks-results.sarif`, `generated-python-antipatterns.sarif`)
- Added unified gate evaluator:
  - `scripts/evaluate_unified_quality_gate.py`
  - `Taskfile.yml` task `quality:gate:unified`
  - Policy contract: `contracts/unified-quality-gate-policy-v1.json`
  - Policy schema: `schemas/unified-quality-gate-policy-v1.schema.json`
  - PR mode: policy profile `pr` (`QUALITY_UNIFIED_MODE=pr`)
  - Nightly mode: policy profile `nightly` (`QUALITY_UNIFIED_MODE=nightly`)
- Added workflow contract coverage for unified quality lane:
  - `tests/e2e/test_unified_quality_ci_contract.py`

## Sources (for this research pass)

- SonarQube docs (quality gates): https://docs.sonarsource.com/sonarqube-server/latest/quality-standards-administration/managing-quality-gates/introduction-to-quality-gates/
- SonarQube docs (quality profiles): https://docs.sonarsource.com/sonarqube-server/latest/quality-standards-administration/managing-quality-profiles/introduction-to-quality-profiles/
- SonarQube server latest docs index: https://docs.sonarsource.com/sonarqube-server/latest/
- Sonar updates page: https://www.sonarsource.com/products/updates/sonarqube/
- GitHub SARIF support: https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning
- CodeQL overview: https://docs.github.com/en/code-security/concepts/code-scanning/codeql/about-code-scanning-with-codeql
- Semgrep docs: https://semgrep.dev/docs/
- Qodana docs: https://www.jetbrains.com/help/qodana/getting-started.html
- DeepSource docs: https://docs.deepsource.com/
- OASIS SARIF TC: https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=sarif
- `thegent`/`trace`/`atoms-mcp-prod` local repository evidence in this workspace
