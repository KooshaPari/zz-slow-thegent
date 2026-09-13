# 00_SESSION_OVERVIEW

## Goal

Convert the helios-family local worktree scan into a lane-by-lane blocker matrix and identify the next prune/migrate queue.

## Scope

- `heliosApp`, `heliosCLI`, `helios-cli`
- Their sibling worktree forests and detached children
- Related small control slices `colab` and `helMo`

## Snapshot

- `heliosApp` is the largest dirty root in the helios family.
- `heliosCLI` has both a dirty root and a detached linked worktree.
- `helios-cli` is structurally cleaner but still dirty.
- `colab` and `helMo` are small, but still have worktree-family drift.

## Next Burn-Down Order

1. `heliosApp-wtrees` lane-by-lane expansion and cleanup.
2. `heliosCLI-wtrees` lane-by-lane expansion and cleanup.
3. `heliosCLI-composite-actions` detached root resolution.
4. `helios-cli-wtrees` normalization.
5. `colab` / `helMo` cleanup only after the main helios lanes are reduced.

## References

- `01_RESEARCH.md`
- `05_KNOWN_ISSUES.md`
- `../20260324-phenotype-local-worktree-forest-blocker-matrix/` — consolidated multi-family blocker matrix and queue cadence (`04_QUEUE_CADENCE.md`)
