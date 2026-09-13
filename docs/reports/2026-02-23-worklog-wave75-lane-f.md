# Worklog Wave 75 - Lane F (2026-02-23)

## Task

Design-space research for a unified cross-language quality tool in thegent: test runner + linters + custom rules + policy + scoring.

## Research Items (10)

1. **New-code-first gating (SonarQube pattern)**

- Pattern: enforce strict gates on changed code first, not full historical debt, to keep PR flow fast while quality trends upward.
- Sources:
  - https://docs.sonarsource.com/sonarqube/latest/user-guide/quality-gates
  - https://docs.sonarsource.com/sonarqube/latest/project-administration/clean-as-you-code-settings/defining-new-code/
- Concrete implication for thegent:
  - Implement lane-level gate profiles that default to `new_code_only=true` with fail conditions on `new_issues`, `new_duplication`, and `new_coverage`.

2. **Go/no-go commit statuses as first-class outputs (CodeClimate -> Qlty evolution)**

- Pattern: modern quality platforms expose explicit PR statuses (gate, coverage, diff coverage) and moved from legacy Code Climate into Qlty Cloud + CLI.
- Sources:
  - https://docs.qlty.sh/cloud/gates
  - https://docs.codeclimate.com/docs/faq
  - https://docs.qlty.sh/cloud/continuous-quality
- Concrete implication for thegent:
  - Add native status emitters (`thegent quality status`) for `quality_gate`, `coverage`, and `diff_coverage` so branch protection can consume deterministic checks.

3. **Shared, layered analysis config across repos (enterprise multi-repo governance)**

- Pattern: org-wide reusable analysis sources + per-repo overrides (Qlty custom sources) reduce policy drift.
- Sources:
  - https://docs.qlty.sh/qlty-cli/additional-information/shared-analysis-configuration
- Concrete implication for thegent:
  - Introduce layered config resolution: `org baseline -> repo policy -> lane override`, with pin-by-tag support for reproducible policy snapshots.

4. **Diff-aware review comments and fix suggestions (Reviewdog pattern)**

- Pattern: ingest arbitrary linter formats, filter to changed lines, and post PR-native review output/suggestions.
- Sources:
  - https://github.com/reviewdog/reviewdog
- Concrete implication for thegent:
  - Build a reporter adapter layer that normalizes tool output into one internal diagnostic schema, then supports `github-pr-check`, `github-pr-review`, and local terminal reporters.

5. **SARIF as the cross-tool interchange backbone**

- Pattern: SARIF remains the practical interop format for heterogeneous scanners and code-host ingestion.
- Sources:
  - https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/sarif-v2.1.0-os.html
  - https://docs.github.com/en/enterprise-cloud@latest/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning
  - https://github.com/github/codeql-action
- Concrete implication for thegent:
  - Make SARIF the canonical export/import boundary (`thegent quality sarif merge|split|upload`) and preserve category/run IDs to avoid result clobbering in monorepos.

6. **Action/task graph introspection for precise orchestration (Bazel + Nx)**

- Pattern: graph introspection (`aquery`/`cquery`, task graphs) enables targeted execution and root-cause explainability.
- Sources:
  - https://bazel.build/docs/aquery
  - https://docs.bazel.build/versions/master/cquery.html
  - https://nx.dev/docs/guides/tasks--caching
- Concrete implication for thegent:
  - Add a `quality graph` command that models analyzers/tests as DAG nodes with explicit inputs/outputs so only impacted nodes run on change.

7. **Content-addressed remote cache as default accelerator (Bazel/Pants/Nx/Turbo convergence)**

- Pattern: modern build/quality systems converge on deterministic hashes + remote cache sharing across dev and CI.
- Sources:
  - https://www.pantsbuild.org/2.29/docs/using-pants/remote-caching-and-execution/remote-caching
  - https://turborepo.com/repo/docs/core-concepts/remote-caching
  - https://nx.dev/docs/features/cache-task-results
  - https://github.com/buchgr/bazel-remote
- Concrete implication for thegent:
  - Create a cache abstraction keyed by `(tool, version, rulepack, file-hash, env-fingerprint)` and support pluggable backends (local FS, HTTP/gRPC remote).

8. **Remote execution protocol compatibility for scale-out**

- Pattern: REAPI-based remote execution/caching enables horizontal scaling and cross-tool compatibility.
- Sources:
  - https://github.com/bazelbuild/remote-apis
  - https://www.pantsbuild.org/2.26/docs/using-pants/remote-caching-and-execution
- Concrete implication for thegent:
  - Define an execution provider interface with a local executor and REAPI executor, so heavyweight analyzers/tests can burst to remote workers without changing policy logic.

9. **Reliability-aware CI loops: flake detection + auto-retry + self-healing**

- Pattern: 2025-2026 systems increasingly optimize `time-to-green` via automatic flaky-task detection/retry and AI-assisted fix proposals.
- Sources:
  - https://nx.dev/docs/features/ci-features/flaky-tasks
  - https://nx.dev/ci/features/self-healing-ci
- Concrete implication for thegent:
  - Add reliability metadata to quality runs (`flake_rate`, `retry_count`, `healed_by`) and separate policy handling for deterministic failures vs flake/environment failures.

10. **AI-assisted maintainability loops are becoming mainstream (GitHub Code Quality preview)**

- Pattern: code-quality findings + one-click AI fixes at PR time are now productized in mainstream forges.
- Sources:
  - https://docs.github.com/en/code-security/code-quality/get-started/quickstart
  - https://github.com/orgs/community/discussions/177488
- Concrete implication for thegent:
  - Define a controlled autofix lane: generate fix patches for selected rule IDs, run policy/test gates, then require explicit approval before apply to keep governance deterministic.

## Suggested Architecture Slice for thegent

- **Ingestion layer**: adapters for test/lint/security tools -> internal diagnostic model.
- **Normalization layer**: internal model <-> SARIF + PR reporter outputs.
- **Execution layer**: local + REAPI executors, DAG-aware scheduler, remote cache.
- **Policy layer**: new-code gates, reliability-aware decisions, org/repo/lane policy stack.
- **Scoring layer**: weighted score from severity, coverage/diff coverage, duplication, flake penalty, and policy compliance.

## Immediate Thegent Backlog Candidates

1. `quality graph` command with DAG + affected-node execution.
2. SARIF canonical pipeline (`merge/split/upload`) with monorepo-safe categories.
3. Pluggable cache/executor interfaces (`local`, `remote-cache`, `reapi`).
4. Policy stack loader (`org -> repo -> lane`) with immutable snapshot IDs.
5. Reliability dimension in scoring (`flake-adjusted gate`) and retry telemetry.
