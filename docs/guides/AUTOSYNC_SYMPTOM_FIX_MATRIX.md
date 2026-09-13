# Autosync Symptom-to-Fix Matrix

This matrix provides a quick diagnostic and remediation guide for common autosync issues. Use the symptom to identify the likely cause, run the diagnostic command, and apply the recommended fix.

## Symptom-to-Fix Reference

| Symptom                            | Likely Cause                         | Diagnostic Command                                    | Fix Command                                             | Reference                                    |
| ---------------------------------- | ------------------------------------ | ----------------------------------------------------- | ------------------------------------------------------- | -------------------------------------------- |
| Drift detected in sync             | Schema mismatch or stale mapping     | `thegent autosync drift-check <connector>`            | `thegent autosync remap <connector>`                    | docs/guides/AUTOSYNC_CONFLICT_RESOLUTION.md  |
| Conflict queue full, sync blocked  | Too many unresolved conflicts        | `thegent autosync conflicts-list <connector>`         | `thegent autosync resolve-conflicts <connector> --auto` | docs/guides/AUTOSYNC_CONFLICT_RESOLUTION.md  |
| Auth token expired, 401 errors     | OAuth token expired or revoked       | `thegent autosync auth-status <connector>`            | `thegent autosync refresh-auth <connector>`             | docs/guides/AUTOSYNC_AUTH_TROUBLESHOOTING.md |
| Rate limit hit, backoff active     | Connector rate limit exhausted       | `thegent autosync quota-status <connector>`           | `thegent autosync backoff --reset <connector>`          | docs/guides/AUTOSYNC_RATE_LIMITING.md        |
| Sync stuck, no progress            | Process deadlocked or hung           | `thegent autosync status <connector> --verbose`       | `thegent autosync restart <connector>`                  | docs/guides/AUTOSYNC_LIFECYCLE.md            |
| Board ID collision, write rejected | Duplicate board ID assignment        | `thegent autosync board-ids <connector> --check-dups` | `thegent autosync reindex-boards <connector>`           | docs/guides/AUTOSYNC_BOARD_MANAGEMENT.md     |
| Startup validation failed          | Connector not ready or misconfigured | `thegent autosync startup-validate <connector>`       | `thegent autosync configure <connector> --interactive`  | docs/guides/AUTOSYNC_STARTUP.md              |
| Rollback needed, revert state      | Production issue, need to recover    | `thegent autosync snapshots list <connector>`         | `thegent autosync rollback <connector> <snapshot-id>`   | docs/guides/AUTOSYNC_ROLLBACK.md             |
| Mapping stale, schema evolved      | Connector schema changed upstream    | `thegent autosync schema-diff <connector>`            | `thegent autosync schema-sync <connector>`              | docs/guides/AUTOSYNC_SCHEMA_EVOLUTION.md     |
| Writer lock held, writes blocked   | Another process holds write lock     | `thegent autosync lock-status <connector>`            | `thegent autosync lock-release <connector> --force`     | docs/guides/AUTOSYNC_LOCKING.md              |

## Usage

1. **Identify the symptom** from the list above.
2. **Run the diagnostic command** to confirm the root cause.
3. **Apply the fix command** to resolve the issue.
4. **Consult the reference** document for detailed explanation and options.

## Examples

### Example 1: Drift Detected

```bash
# Symptom: Drift detected in sync
# 1. Diagnose
thegent autosync drift-check jira

# 2. Apply fix
thegent autosync remap jira

# 3. Verify resolution
thegent autosync drift-check jira  # Should show no drift
```

### Example 2: Rate Limit Hit

```bash
# Symptom: Rate limit hit, backoff active
# 1. Check quota status
thegent autosync quota-status linear

# 2. Reset backoff
thegent autosync backoff --reset linear

# 3. Verify progress
thegent autosync status linear
```

### Example 3: Sync Stuck

```bash
# Symptom: Sync stuck, no progress
# 1. Get verbose status
thegent autosync status asana --verbose

# 2. Restart connector
thegent autosync restart asana

# 3. Monitor recovery
thegent autosync status asana --follow
```

## Advanced Diagnostics

For complex issues, use these tools:

- **Full audit**: `thegent autosync audit <connector>` — Comprehensive health check
- **Event log**: `thegent autosync events <connector> --tail 100` — Last 100 events
- **State dump**: `thegent autosync dump-state <connector>` — Full internal state snapshot
- **Trace**: `thegent autosync trace <connector> <operation>` — Operation-level trace

## Escalation

If symptoms persist after applying the fix command:

1. Consult the reference documentation linked in the matrix
2. Run advanced diagnostics from the section above
3. Check `docs/governance/AUTOSYNC_SIGNOFF_TEMPLATE.md` for compliance status
4. Contact the platform team with the audit and state dump outputs
