# Runbooks

Use these short runbooks for common operational failures.

## Runbook: Broken Shell Integration

1. Regenerate shell config snippet:

```bash
thegent shell-init zsh
```

2. Ensure your shell startup file loads it.
3. Reinstall shims:

```bash
thegent install-shims
thegent doctor
```

## Runbook: Credential/Auth Failure

1. Re-run setup:

```bash
thegent setup
```

2. Re-test with explicit provider:

```bash
thegent run "health check" --provider codex --debug
```

## Runbook: Stuck Background Sessions

1. Inspect sessions:

```bash
thegent ps
```

2. Stop problematic session:

```bash
thegent stop <session_id>
```

3. Restart with a narrower prompt or different provider.

## Runbook: MCP Connectivity Failure

1. Start MCP server:

```bash
thegent serve
```

2. Verify client target host/port.
3. Remove stale resources safely:

```bash
thegent mcp prune
```

## Runbook: Autosync Incident and Recovery

Trigger conditions:

1. `docs/reference/autosync_status.json` reports `"health": "degraded"` for 2+ cycles.
2. Emergency stop sentinel exists or `THGENT_AUTOSYNC_EMERGENCY_STOP=1`.
3. Failure queue grows continuously (`failure_queue_size` increasing across runs).

Immediate containment:

1. Enable emergency stop:

```bash
export THGENT_AUTOSYNC_EMERGENCY_STOP=1
```

2. Confirm no new write-capable sync activity (status snapshot should keep `last_error`).

Rollback and recovery:

1. Capture current state:

```bash
thegent sync autopilot-status
```

2. Remove/repair bad local changes, then clear emergency stop only after validation:

```bash
unset THGENT_AUTOSYNC_EMERGENCY_STOP
```

3. Run one controlled cycle:

```bash
thegent sync autopilot --once
```

Validation checkpoints:

1. `last_error` is empty in `docs/reference/autosync_status.json`.
2. `failure_queue_size` is stable or decreasing.
3. `docs/reference/WORK_STREAM.md` reflects expected statuses only.
