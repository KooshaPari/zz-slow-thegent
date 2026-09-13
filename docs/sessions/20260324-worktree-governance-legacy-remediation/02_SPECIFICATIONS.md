# 02_SPECIFICATIONS

## Remediation workflow

1. Generate remediation report via `task quality:governance:legacy-remediation-report`.
2. For each clean legacy worktree, migrate into the canonical root with `thegent worktree migrate-legacy`.
3. Re-run governance checks after migration to measure remaining legacy lanes.

## Acceptance criteria

- Legacy remediation report exists and is current.
- Migration command moves a clean legacy worktree into the canonical root and renames the branch to the structured tuple.
- Strict governance is expected to fail while any legacy worktrees remain.
