# Multi-Project Tenancy Autosync (WL-199)

## Purpose

Run board/autosync workflows across multiple project roots with one explicit sync-policy contract at `.thegent/sync-policy.yaml`.

## Contract File

Create `.thegent/sync-policy.yaml` in each project root:

```yaml
schema_version: sync-policy/v1
conflict_precedence: board_id_first
strict_mode: true
connectors:
  github:
    enabled: true
    mode: enforce
    direction: bidirectional
    quota_daily: 200
    board_id: your-org:1
  linear:
    enabled: false
    mode: disabled
    direction: write_only
    quota_daily: 1
tenancy:
  mode: multi_project
  default_tenant: tenant-default
  projects:
    - root: /abs/path/project-a
      tenant_id: tenant-a
      autosync_enabled: true
    - root: /abs/path/project-b
      tenant_id: tenant-b
      autosync_enabled: true
```

## Validate Policy

Run:

```bash
thegent sync audit --format table --project /abs/path/project-a
```

Expected:

- `Schema Version: sync-policy/v1`
- connector modes and quotas loaded from file
- tenancy mode/project count visible in output

## Dead-Letter Recovery

Failed remote writes are persisted at:

- default: `docs/reference/workstream_remote_writes_dead_letter.jsonl`
- override: `THGENT_SYNC_DEAD_LETTER_PATH=/custom/path.jsonl`

Replay pending entries:

```bash
thegent sync dead-letter-replay --source github --board your-org:1 --limit 100
```

Preview replay candidates without mutation:

```bash
thegent sync dead-letter-replay --dry-run
```

## Operational Notes

- Keep connector `mode=disabled` for projects not ready to write remote state.
- Use connector-level `board_id` in policy to avoid per-command board flags.
- Keep tenancy `projects[].root` unique; duplicate roots are rejected by contract validation.
- Use one policy file per project root to avoid cross-tenant ambiguity.
