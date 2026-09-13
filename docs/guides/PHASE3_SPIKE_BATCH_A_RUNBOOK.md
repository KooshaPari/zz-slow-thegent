# Phase 3 Spike Batch A Runbook

## Scope

Operational runbook for Lane B spike checks:

- `task lint:prose`
- `task integration:context7:smoke`
- `task integration:beads:smoke`

## Prerequisites

- Run from repo root: `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent`
- `task` installed
- `vale` installed and on `PATH`
- Python runtime available through `uv`

## Required Environment Variables

- `CONTEXT7_BASE_URL` (example: `http://127.0.0.1:8087`)
- `BEADS_BASE_URL` (example: `http://127.0.0.1:8091`)

Set for current shell:

```bash
export CONTEXT7_BASE_URL="http://127.0.0.1:8087"
export BEADS_BASE_URL="http://127.0.0.1:8091"
```

## Execution Order

Run in this order:

```bash
task lint:prose
task integration:context7:smoke
task integration:beads:smoke
```

## Expected Behavior

- `lint:prose`
  - Pass: exits `0` after running `vale` on `README.md`, `AGENTS.md`, `CLAUDE.md`, and `docs/`.
  - Fail: non-zero exit with prose violations; fix wording/style issues and rerun.
- `integration:context7:smoke`
  - Pass: exits `0` and prints JSON with `"ok": true`, `"target": "context7"`, health URL, status `200`.
  - Fail: raises loudly (non-zero) for missing `CONTEXT7_BASE_URL`, network errors, timeout, or non-200.
- `integration:beads:smoke`
  - Pass: exits `0` and prints JSON with `"ok": true`, `"target": "beads"`, health URL, status `200`.
  - Fail: raises loudly (non-zero) for missing `BEADS_BASE_URL`, network errors, timeout, or non-200.

## Fast Failure Triage

- Missing env var: export the required variable and rerun the specific smoke command.
- Connection refused/timeout: verify service is running and reachable at `<BASE_URL>/health`.
- Non-200 status: treat as upstream service health failure; do not suppress.

## Rollback (Remove Spike)

If the spike must be removed, delete the smoke tasks and scripts in one change:

1. Remove task entries from `Taskfile.yml`:
   - `integration:context7:smoke`
   - `integration:beads:smoke`
2. Delete scripts:
   - `scripts/context7_contract_smoke.py`
   - `scripts/beads_contract_smoke.py`
3. Remove references in docs/reports that mention these spike tasks.
4. Validate cleanup:

```bash
rg -n "integration:context7:smoke|integration:beads:smoke|context7_contract_smoke|beads_contract_smoke" Taskfile.yml scripts docs
```

Expected rollback validation result: no matches.
