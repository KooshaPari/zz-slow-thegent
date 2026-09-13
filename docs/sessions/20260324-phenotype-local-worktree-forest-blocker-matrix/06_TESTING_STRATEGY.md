# 06_TESTING_STRATEGY

## Validation Used

- `git status --short` on the major standalone roots
- `git worktree list --porcelain` on the main families
- Slice-by-slice family inventories using focused subagents

## Gaps

- The matrices are family-complete for the biggest blockers, but not every child lane under every forest has been individually expanded into this report.
- The next useful validation pass is lane-by-lane expansion of the largest blocker forests.

## Execution Queue Rules

1. **Wait on Dirty**: Never attempt prune/migrate for `heliosApp` or `heliosCLI` until the main root is clean.
2. **Canonicalize First**: Resolve `cliproxy` typo drift (`cliproxy-wtress`) before touch-pruning lanes.
3. **Unlock Before Move**: Resolve `trace` locks (`codex-required-gates*`) before any forest-wide migration.
4. **Repair Before Prune**: Treat `trash-cli` detached lanes as repair items, not cleanup candidates.
5. **Small Slices**: Use the six-lane `portage` prune queue only after detached lanes are explicitly owned.

## Verification Workflow

- **State Check**: `git status --short` on candidate standalone roots.
- **Lane Audit**: `git worktree list --porcelain` on forest containers.
- **Drift Audit**: Verify `cliproxy-wtrees` and `cliproxy-wtress` contents match before deletion.

## Governance automation

If the repo defines worktree governance tasks (e.g., `task quality:governance:*`), run them after any manual migration to verify policy compliance.

## Queue cadence

See `04_QUEUE_CADENCE.md` for the six-slice / 24-item turn convention and documentation hygiene.
