# Worklog Wave 75 - Master

Date: 2026-02-23
Method: child-output-only synthesis from 6 lane reports (A-F), 10 researched items each (60 total).

## Input Lanes

- `docs/reports/2026-02-23-worklog-wave75-lane-a.md`
- `docs/reports/2026-02-23-worklog-wave75-lane-b.md`
- `docs/reports/2026-02-23-worklog-wave75-lane-c.md`
- `docs/reports/2026-02-23-worklog-wave75-lane-d.md`
- `docs/reports/2026-02-23-worklog-wave75-lane-e.md`
- `docs/reports/2026-02-23-worklog-wave75-lane-f.md`

## Cross-Lane Findings

1. The fastest practical win is not one tool, it is a layered quality pipeline: fast lint/type gates, security scanning, and focused test lanes.
2. Pytest performance gains come from collection control, selective execution, and tuned parallel modes, not blanket `-n auto`.
3. FR/user-story traceability is mature enough to enforce now via strict markers plus generated traceability artifacts.
4. Generated-code governance requires structural checks and policy-as-code, not just style linting.
5. Cross-language quality unification should center on a normalized result model plus SARIF interoperability.
6. Security controls must be default-on in agent workflows: prompt-injection boundaries, secret scanning, and required status checks.
7. Reliability needs explicit flake handling and telemetry to avoid masking systemic instability with retries.

## Consolidated Priority Actions

1. Establish a unified baseline gate in `thegent`:
   - Python: Ruff + (Mypy or Pyright)
   - Go: golangci-lint
   - Multi-language security: Semgrep + CodeQL
   - Test lane: `python -m pytest` with marker-driven slicing
2. Implement FR traceability contract:
   - Canonical marker: `@pytest.mark.requirement("FR-...")`
   - CI artifacts: `requirement->tests`, `test->requirements`, gap report
   - Strict enforcement: `--strict-markers`
3. Add generated-code anti-pattern gates:
   - Semgrep custom rules
   - ast-grep structural rules
   - Architecture boundary checks
4. Build unified-quality substrate:
   - Internal diagnostic schema
   - SARIF import/export pipeline
   - Reporter adapters for terminal + PR checks
5. Add impact and execution acceleration:
   - DAG-aware run planner (`quality graph`)
   - Content-addressed cache key model
   - Diff/new-code-first gating
6. Secure the execution envelope:
   - Secret scanning in pre-commit + CI
   - Policy-as-code checks on workflow/IaC files
   - Prompt-injection-safe boundaries for agent-triggered operations

## Implementation Sequence (Recommended)

1. Phase 0: Baseline and observability
   - Add unified command contract (`task quality`) and publish output schema.
   - Emit JSON + SARIF from current checks.
2. Phase 1: Fast deterministic gates
   - Enforce lint/type/security baseline on PRs.
   - Introduce marker-strict pytest slicing and duration profiling.
3. Phase 2: Traceability and governance
   - Enforce FR mapping on changed tests.
   - Publish requirement coverage and gap artifacts per CI run.
4. Phase 3: Scale and performance
   - Add DAG planner + cache integration.
   - Add flake telemetry and reliability-aware retry policy.
5. Phase 4: Advanced automation
   - Controlled autofix lane for selected rule IDs.
   - Keep explicit human approval before patch application.

## Adopt/Watch/Avoid Snapshot

- Adopt Now:
  - Strict marker governance + FR trace artifacts
  - Ruff/Mypy|Pyright + Semgrep + CodeQL baseline
  - Secret scanning in push/CI + prompt-injection boundary controls
  - DAG-aware planning and diff/new-code-first gates
- Watch:
  - SonarQube alternatives and platform wrappers where policy portability is unclear
  - AI-assisted autofix beyond constrained rule sets
- Avoid:
  - Claims of autonomy without deterministic controls, auditability, and rollback

## Immediate Backlog Candidates (Wave 76 seed)

1. `quality-contract`: define canonical outputs (JSON + SARIF + markdown summary).
2. `fr-trace-extractor`: generate requirement/test mapping and coverage gaps.
3. `quality-graph`: DAG planner with impacted-node execution.
4. `quality-cache`: pluggable cache key and backend abstraction.
5. `policy-pack`: semgrep + ast-grep + architecture rules bundle.
6. `quality-reporter`: PR status + review comment adapters.
7. `reliability-metrics`: flake/retry telemetry and trend report.
