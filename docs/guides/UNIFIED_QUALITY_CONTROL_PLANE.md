# Unified Quality Control Plane

This guide describes the contract-first quality control plane used by `thegent`.

## Default posture

- ADR: `ADR-017`
- Default plane: `github_sarif_native`
- Policy contract: `contracts/quality-control-plane-v1.json`
- Contract schema: `schemas/quality-control-plane-v1.schema.json`

## Artifact contracts

- Hook result envelope: `schemas/thegent-hooks-result-v1.schema.json`
- Hook input contracts:
  - `schemas/thegent-hooks-quality-gate-input-v1.schema.json`
  - `schemas/thegent-hooks-security-pipeline-input-v1.schema.json`

## Primary tasks

- `task quality:hooks:sarif`
- `task quality:generated-python:antipatterns`
- `task quality:pilot:mutation-perf`
- `task quality:control-plane:validate`
- `task quality:control-plane:report`
- `task quality:summary`
- `task quality:ci:unified`

## CI model

- PR: run artifact producers in non-blocking mode where appropriate.
- Nightly: enforce contract validation and readiness reporting gates.
- Promotion: move pilots to blocking after stability and flake budget review.

Current wiring:

- `.github/workflows/ci.yml` includes `quality-unified` job for `pull_request` and nightly `schedule`.
- Gate policy contract: `contracts/unified-quality-gate-policy-v1.json`
- Gate policy schema: `schemas/unified-quality-gate-policy-v1.schema.json`
- Gate task: `task quality:gate:unified`
- PR runs set `QUALITY_UNIFIED_MODE=pr`.
- Nightly runs set `QUALITY_UNIFIED_MODE=nightly` (fail-closed on policy-defined warn/fail conditions).
