# Workstream Autosync Zero-Touch Quick Start (WL-180)

## Goal

Set up unattended workstream reflection between local `docs/reference/WORK_STREAM.md`, GitHub Projects, and Linear with deterministic verification.

## Prerequisites

- Python environment is active for this repo.
- `gh` CLI is installed and authenticated for project access.
- Linear API key has permission for the target team.
- Project board identifiers are known.

## 1) Configure Environment

Set required variables before starting the autosync runner:

```bash
export THGENT_WORKSTREAM_AUTOSYNC_ENABLED=true
export THGENT_WORKSTREAM_AUTOSYNC_INTERVAL=300
export THGENT_AUTOSYNC_STANDALONE_MODE=false

export THGENT_GITHUB_ENABLED=true
export THGENT_GITHUB_OWNER="<github-owner>"
export THGENT_GITHUB_PROJECT_NUMBER="<project-number>"
export THGENT_GITHUB_DIRECTION=bidirectional

export THGENT_LINEAR_ENABLED=true
export THGENT_LINEAR_API_KEY="<linear-api-key>"
export THGENT_LINEAR_TEAM_KEY="<linear-team-key>"
export THGENT_LINEAR_DIRECTION=bidirectional
```

## 2) Verify Config Resolution

Run a quick Python check to confirm effective settings:

```bash
python - <<'PY'
from thegent.integrations.workstream_autosync import load_autosync_config_from_env
cfg = load_autosync_config_from_env()
print({
    "enabled": cfg.enabled,
    "github": cfg.should_sync_github(),
    "linear": cfg.should_sync_linear(),
    "partition_size": cfg.effective_partition_size,
})
PY
```

## 3) Run Integration Safety Tests

Validate connector behavior with deterministic fixtures before enabling unattended mode:

```bash
python -m pytest -q tests/integrations/test_wl178_github_sync_integration.py
python -m pytest -q tests/integrations/test_wl179_linear_sync_integration.py
```

## 4) Enable Zero-Touch Operation

Start the service path used by your environment and keep it running. Do not restart the full dev stack unless required by the user-managed TUI workflow.

## 5) Verify Health and Drift

Check status snapshots and failure queue after at least one cycle:

```bash
cat docs/reference/autosync_status.json
cat docs/reference/workstream_autosync_failures.json
```

Healthy indicators:

- `health` is `ok`.
- `last_error` is `null`.
- `failure_queue_size` is `0`.

## Emergency Stop

Use an explicit stop signal for write-capable sync paths:

```bash
export THGENT_AUTOSYNC_EMERGENCY_STOP=true
```

Unset the variable only after resolving the issue that triggered the stop.
