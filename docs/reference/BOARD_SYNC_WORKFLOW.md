# Board Sync Workflow (WL-159)

Operationalize repeatable cross-repo board update and synchronization flow using native tooling.

## Overview

The board sync workflow synchronizes local `docs/reference/WORK_STREAM.md` status with GitHub Projects or Linear issues. This provides a single source of truth for work item status across multiple repositories and remote boards.

## Quick Start

### 1. Configure Board ID

Set your board identifier in environment variables or `.env`:

```bash
# GitHub Projects
export THGENT_BOARD_ID="123"  # GitHub project number
export THGENT_BOARD_SOURCE="github"

# Linear
export THGENT_BOARD_ID="PROJ-1"  # Linear project key
export THGENT_BOARD_SOURCE="linear"
```

### 2. Preview Changes (Dry Run)

Before syncing, preview what would change:

```bash
task board:sync:dry-run

# Or with inline options
uv run thegent sync board --board 123 --source github --dry-run
```

### 3. Perform Sync

Synchronize local WORK_STREAM.md status to remote board:

```bash
task board:sync

# Or with inline options
uv run thegent sync board --board 123 --source github
```

## Detailed Usage

### Command: `task board:sync`

Synchronize WORK_STREAM.md items to remote board.

```bash
# Using environment variables
export THGENT_BOARD_ID="123"
export THGENT_BOARD_SOURCE="github"
task board:sync

# Using inline options
uv run thegent sync board --board 123 --source github --dry-run

# Using task arguments
task board:sync -- --board 123 --source linear
```

### Command: `task board:sync:dry-run`

Preview changes without writing. Useful for CI/CD and validation.

```bash
task board:sync:dry-run
```

### CLI: `thegent sync board`

The underlying CLI command provides full control:

```bash
thegent sync board \
  --board <id> \
  --source github|linear \
  [--dry-run] \
  [--project /path/to/project]
```

**Options:**

- `--board, -b`: Board ID (GitHub project number or Linear key). Required unless set in env as `THGENT_BOARD_ID`.
- `--source, -s`: Board source platform (github | linear). Default: github.
- `--dry-run, -n`: Report changes without writing.
- `--project, -p`: Project root (default: cwd).

## WORK_STREAM.md Format

Items are recognized by:

1. **Item Header**: `### [WL-NNN] Title`
2. **Status Line**: `**Status:** IN PROGRESS | COMPLETED | BACKLOG`

Example:

```markdown
### [WL-159] Cross-Repo Board Sync Operationalization

**Status:** IN PROGRESS
**Priority:** P2

Operationalize repeatable board update/import flow using native tooling.

- Item 1
- Item 2
```

## Configuration

### Environment Variables

| Variable              | Default  | Description                          |
| --------------------- | -------- | ------------------------------------ |
| `THGENT_BOARD_ID`     | (none)   | Board identifier (required for sync) |
| `THGENT_BOARD_SOURCE` | `github` | Board platform: github \| linear     |

### .env File

```bash
# .env
THGENT_BOARD_ID=123
THGENT_BOARD_SOURCE=github
```

## Workflow Examples

### Example 1: GitHub Projects Sync

```bash
export THGENT_BOARD_ID="42"
export THGENT_BOARD_SOURCE="github"

# Preview
task board:sync:dry-run

# Sync
task board:sync
```

Output:

```
[green]Board sync complete: 15 item(s) updated on github.[/green]
  [dim]synced: WL-159[/dim]
  [dim]synced: WL-160[/dim]
  [dim]synced: WL-161[/dim]
  ...
```

### Example 2: Linear Sync with Dry Run

```bash
uv run thegent sync board \
  --board "PROJ-1" \
  --source linear \
  --dry-run
```

Output:

```
[yellow]Dry-run: Board sync dry-run: would sync 12 item(s) to linear.[/yellow]
  [dim][dry-run] WL-159: IN_PROGRESS[/dim]
  [dim][dry-run] WL-160: COMPLETED[/dim]
  ...
```

### Example 3: CI/CD Integration

In GitHub Actions or other CI:

```yaml
- name: Sync Board
  env:
    THGENT_BOARD_ID: ${{ secrets.BOARD_ID }}
    THGENT_BOARD_SOURCE: github
  run: |
    uv run thegent sync board \
      --dry-run \
      --project ${{ github.workspace }}
```

## Native Tooling Integration

The board sync uses:

- **Native CLI**: `thegent sync board` (Python, no external binaries)
- **Task Runner**: `task board:sync` (Task/Taskfile.yml)
- **Environment Variables**: Standard thegent config pattern

## Status Mapping

Work item status is mapped across platforms:

| WORK_STREAM.md | GitHub      | Linear      |
| -------------- | ----------- | ----------- |
| BACKLOG        | Todo        | Backlog     |
| IN PROGRESS    | In Progress | In Progress |
| COMPLETED      | Done        | Done        |

## Troubleshooting

### Board ID not configured

**Error:** `Board sync skipped: no board_id configured`

**Solution:** Set `THGENT_BOARD_ID` environment variable or pass `--board` option.

```bash
export THGENT_BOARD_ID="123"
task board:sync
```

### No work stream items found

**Error:** `Board sync: no work stream items found to sync.`

**Solution:** Ensure WORK_STREAM.md exists and contains items with proper format:

```markdown
### [WL-NNN] Title

**Status:** IN PROGRESS
```

### Platform-specific auth

Board sync requires proper authentication for GitHub Projects or Linear:

- **GitHub**: Use `GITHUB_TOKEN` environment variable or git credentials
- **Linear**: Use `LINEAR_API_KEY` environment variable (if implemented)

## Design Notes

### Operationalization

This workflow operationalizes the repeatable board sync pattern:

1. **Local Source**: docs/reference/WORK_STREAM.md (git-tracked, version-controlled)
2. **Native Tooling**: `thegent sync board` (Python, no external Go utilities)
3. **Task Integration**: `task board:sync` and `task board:sync:dry-run`
4. **CI-Ready**: Dry-run support for validation before merging

### Future Enhancements

- [ ] Bidirectional sync (board → WORK_STREAM.md)
- [ ] Conflict resolution for diverged status
- [ ] Automatic sync on commit/push
- [ ] Status history and audit trail
- [ ] Custom field mapping per platform

## See Also

- [WORK_STREAM.md](./WORK_STREAM.md) — The canonical work item tracker
- [WL-160](./WORK_STREAM.md#wl-160) — Full Automatic Workstream Reflection
- [WL-161](./WORK_STREAM.md#wl-161) — Board-ID-First Reconciliation Policy
