# thegent sync — Unified Sync Command

`thegent sync` consolidates all update and synchronisation operations into a
single entry point.  It is implemented in
`src/thegent/commands/sync.py` (class `SyncCommand`) and registered in
`src/thegent/main.py` under the `sync` typer group.

---

## Subcommands

| Subcommand | Purpose |
|---|---|
| `all` (default) | Run every sync operation in sequence |
| `work-stream` | Incorporate markdown fragments from `docs/` into `WORK_STREAM.md` |
| `config` | Refresh `ThegentSettings` from the current environment |
| `agents` | Discover `.md` agent files in `agents/` not yet in the registry |
| `hooks` | Validate hook scripts against `hook-config.yaml` |

Running `thegent sync` without a subcommand is equivalent to `thegent sync all`.

---

## Usage

```bash
# Sync everything
thegent sync
thegent sync all

# Dry-run (report without writing)
thegent sync all --dry-run

# Individual subcommands
thegent sync work-stream
thegent sync work-stream --dry-run

thegent sync config
thegent sync config --dry-run

thegent sync agents
thegent sync agents --dry-run

thegent sync hooks
thegent sync hooks --dry-run

# Use a non-cwd project root
thegent sync all --cd /path/to/project
```

---

## Subcommand Details

### `sync all`

Runs `work-stream`, `config`, `agents`, and `hooks` in that order.  Prints a
Rich table of per-operation status, duration, and message.  Exits non-zero if
any operation fails.

Options:

| Flag | Default | Description |
|---|---|---|
| `--cd` | cwd | Project root directory |
| `--dry-run` | off | Report without writing |

### `sync work-stream`

Scans the following directories for markdown work items (checkbox lines
`- [ ] …` and table rows `| … |`):

- `docs/plans/*.md`
- `docs/research/*.md`
- `docs/docset/*.md`

New items (not already present in `WORK_STREAM.md`) are appended with a
`<!-- auto-incorporated by thegent sync work-stream -->` header.  Existing
CLAIMED and COMPLETED sections are not modified.

Returns `SyncOperationStatus.DRY_RUN` when `--dry-run` is set.  Returns
`SyncOperationStatus.FAILED` on I/O errors.

### `sync config`

Re-instantiates `ThegentSettings` (which reads `THGENT_*` env vars and `.env`)
and compares the new instance against the previous one field-by-field.  Reports
the count and names of fields that changed.

This is a read-only operation — it does not persist any state.  The primary
value is diagnostics: confirming that env changes took effect without
restarting a shell.

### `sync agents`

Globs `agents/*.md` and compares the discovered stem-names against
`thegent.agents.registry.AGENT_NAMES`.  Reports agent files that are present
on disk but not yet registered.

This command is informational — it does not modify the registry.  To add a
new agent, create `agents/<name>.md` following the existing persona template
and add `<name>` to `AGENT_NAMES` in `src/thegent/agents/registry.py`.

### `sync hooks`

Cross-references `hooks/*.sh` file stems against the `hooks:` section keys in
`hooks/hook-config.yaml` and reports two categories of drift:

- **unregistered** — scripts on disk with no config entry
- **orphaned** — config entries with no corresponding `.sh` file

Both categories are advisory findings.  The operation status is always
`SUCCESS` (or `DRY_RUN`) unless an exception occurs.

---

## Programmatic API

```python
from pathlib import Path
from thegent.commands.sync import SyncCommand, SyncResult

cmd = SyncCommand(project_root=Path("/my/project"))

# Run all
result: SyncResult = cmd.sync_all()
print(result.success)  # True / False
print(result.total_duration)  # seconds

# Individual operations
op = cmd.sync_work_stream(dry_run=True)
print(op.status)  # SyncOperationStatus.DRY_RUN
print(op.details)  # {"fragments_found": N}

op = cmd.sync_agents()
print(op.details["new_agents"])  # list of unregistered agent names

op = cmd.sync_hooks()
print(op.details["unregistered"])  # hook scripts with no config entry
print(op.details["orphaned"])  # config entries with no script

# Serialise
import json

print(json.dumps(result.to_dict(), indent=2))
```

---

## Data Types

### `SyncOperationStatus`

| Value | Meaning |
|---|---|
| `success` | Operation completed, changes written |
| `failed` | Operation raised an exception |
| `skipped` | Operation intentionally bypassed |
| `dry_run` | Operation completed but no writes occurred |

### `OperationResult`

| Field | Type | Description |
|---|---|---|
| `operation` | `str` | Subcommand name |
| `status` | `SyncOperationStatus` | Outcome |
| `message` | `str` | Human-readable summary |
| `duration` | `float` | Wall-clock seconds |
| `details` | `dict` | Operation-specific metadata |
| `errors` | `list[str]` | Exception messages on failure |
| `changes` | `list[str]` | Items changed / found |
| `timestamp` | `str` | ISO 8601 UTC |
| `ok` | `bool` (property) | True when status is success or dry_run |

### `SyncResult`

| Field | Type | Description |
|---|---|---|
| `operations` | `list[OperationResult]` | Per-operation results |
| `started_at` | `str` | ISO 8601 UTC |
| `finished_at` | `str` | ISO 8601 UTC (populated after `sync_all`) |
| `total_duration` | `float` | Wall-clock seconds for the full run |
| `success` | `bool` (property) | True when all operations are ok |
| `failed_operations` | `list[OperationResult]` (property) | Failed operations |

---

## Implementation Files

| File | Role |
|---|---|
| `src/thegent/commands/__init__.py` | Package marker |
| `src/thegent/commands/sync.py` | `SyncCommand`, `SyncResult`, `OperationResult`, `SyncOperationStatus` |
| `src/thegent/main.py` | CLI wiring (`sync_app`, subcommand handlers) |
| `tests/test_sync_command.py` | 44 unit tests (FR-SYNC-001 through FR-SYNC-020) |

---

## Related Commands

| Command | Description |
|---|---|
| `thegent plan incorporate` | Work-stream incorporation (lower-level) |
| `thegent rules sync` | Sync CLAUDE.md to platform rule files |
| `thegent dag sync` | Synchronise DAG state from session files |
