# Pytest Health Dashboard and Alert Contract

## Scope

This document defines the pytest CI health signal contract used by `Taskfile` + GitHub Actions.

## 84) Observability Plumbing

### Source artifacts

The following files are produced by `task test:pr-gate`:

- `artifacts/pytest/collect/pr-collect.json`
- `artifacts/pytest/requirements/requirements-gate.json`
- `artifacts/pytest/pr/run.json`
- `artifacts/pytest/traceability/requirements-map.json`

### Health aggregation

`task test:health` aggregates the above into:

- `artifacts/pytest/health/pr-gate.json`
- `artifacts/pytest/health/pr-gate.md`

Command reference:

```bash
uv run python scripts/test_pytest_wave_artifacts.py health \
  --collect-artifact artifacts/pytest/collect/pr-collect.json \
  --requirements-gate-artifact artifacts/pytest/requirements/requirements-gate.json \
  --pr-run-artifact artifacts/pytest/pr/run.json \
  --requirements-map-artifact artifacts/pytest/traceability/requirements-map.json \
  --output artifacts/pytest/health/pr-gate.json \
  --summary artifacts/pytest/health/pr-gate.md \
  --strict \
  --fail-on-warning \
  --min-health-score 90
```

### Output contract (`artifacts/pytest/health/pr-gate.json`)

- `overall_status`: `passed` / `warn` / `failed`
- `overall_health_score`: integer 0-100
- `alerts`: array with `severity`, `code`, `title`, `details`, `artifact`, `recommended_action`
- `collect`, `requirements_gate`, `pr_run`, `requirements_map` sections preserve source artifact payloads for drill-down.
- `runbook`: contract thresholds used for this gate evaluation.

### Health scoring

- `error`: `-30`
- `warning`: `-10`
- `info`: `-3`

Default score range is `0..100` after penalty application.

## 85) CI Dashboard / Alert Surface

### CI behavior

In PR mode, CI runs `task test:pr-gate`, which now includes `health` aggregation.

- Workflow step prints alert summaries in logs for immediate visibility.
- Health alert artifact is uploaded via dedicated artifact upload name:
  - `pytest-health-${{ matrix.os }}-${{ matrix.python-version }}`

### Alert thresholds and severity mapping

- **Error**
  - Missing/invalid health input artifacts used in aggregation.
  - Pytest collect non-zero return code.
  - Collection errors > 0.
  - Mapped run failure (`status=failed` or non-zero return code).
- **Warning**
  - Collection budget exceeded.
  - Requirements gate blocked.
  - Uncovered low coverage ratio (< 0.95) in requirement map.
- **Info**
  - PR run fallback to fast lane.

### Runbook thresholds

- `requirements_map.requirement_coverage.coverage_ratio < 0.95` emits `warning`.
- `requirements.gate.blocked_count > 0` emits `warning`.
- `collect.over_budget == true` emits `warning`.
- Health score fail policy:
  - `>= 90`: pass
  - `80-89`: warn
  - `< 80`: fail

### CI gate command

- CI should call health aggregation with:
  - `--strict` (error alerts fail gate)
  - `--fail-on-warning` (warning alerts fail gate)
  - `--min-health-score 90` (hard minimum score)

### Alert handling

- Error alerts should be treated as gate-stopping defects.
- Warning alerts are required backlog items with owners and must be included in release notes if they indicate repeated failures.
- Info alerts should be reviewed before merge but can be tolerated when justified in PR context.

## 96) Requirements Extractor CLI Contract

`requirements-map` payload contract is considered a hard stability boundary.

Output contract (`artifacts/pytest/traceability/requirements-map.json`) must include:

- `schema_version` equals `requirements-map/v1`
- `generated_at`
- `record_count`
- `requirement_to_tests`
- `test_to_requirements`
- `trace_to_tests`
- `test_to_trace_requirements`
- `requirement_coverage`
- `secondary_evidence_coverage`

Command sample:

```bash
uv run python scripts/fr_trace_extractor.py \
  --input-dir tests \
  --fr-tracker docs/reference/FR_TRACKER.md \
  --output artifacts/pytest/traceability/requirements-map.json \
  --csv-output artifacts/pytest/traceability/requirements-map.csv \
  --summary artifacts/pytest/traceability/requirements-map.md \
  --diagram-output artifacts/pytest/traceability/requirements-map.mdown \
  --diagram-max-nodes 100
```

## 97) Optional Lane Promotion Criteria Contract

`requirements-promotion-criteria` and `lane-promotion` are the promotion contracts for making optional lanes required.

Schema versions are:

- `lane-promotion-criteria/v1` for criteria payload
- `lane-promotion/v1` for lane-specific decision payload
  Automation must emit:
- `criteria.required_stability_ratio`
- `criteria.required_stable_runs_required`
- `criteria.max_flake_ratio`
- `criteria.acceptable_fail_budget`
- `actual.run_count_threshold_met`
- `actual.health_score_threshold_met`
- `actual.stability_ratio`
- `actual.observed_flake_ratio`
  Decision fields are:
- `recommendation.ready_for_lane_promotion`
- `recommendation.make_optional_lanes_required`
- `recommendation.reasons`
- `recommendation.ready_to_require_optional_lanes` from lane payload
- `promotion_plan`

## 98) One-Page FR Mapping Diagram Contract

`requirements-map` can emit a one-page Mermaid diagram and `requirements-diagram` can render directly from an artifact.

Diagram schema marker:

- `requirements-map-diagram/v1`
  Generated artifacts:
- `artifacts/pytest/traceability/requirements-map.mdown`
- `artifacts/pytest/traceability/requirements-map.diagram.md`
  Truncation behavior is controlled by `--diagram-max-nodes` on map and `--max-nodes` on diagram rendering; truncation is explicit with the warning line in output.

## 99) Quarterly Traceability Cleanup Routine

Quarterly cleanup uses `traceability-cleanup` and emits both debt and issue artifacts:

`artifacts/pytest/traceability/requirements-cleanup.json` uses schema `traceability-cleanup/v1`.
`artifacts/pytest/traceability/requirements-cleanup-issue.json` uses schema `traceability-cleanup-issue/v1`.

`test:traceability:quarterly-cleanup` is the Taskfile entrypoint for the routine and sets:

- stale window: `90` days
- issue threshold: `0` (open if any stale debt exists)
- issue contract output path (`--issue-output`)
