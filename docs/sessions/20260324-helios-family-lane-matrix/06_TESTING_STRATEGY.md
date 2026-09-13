# 06_TESTING_STRATEGY

## Validation Used

- `git worktree list --porcelain` on `heliosApp`, `heliosCLI`, `helios-cli`, `colab`, and `helMo`
- `git status --short` on the same roots
- Direct directory inspection for worktree-family children

## Recommended Follow-Up

1. Expand `heliosApp-wtrees` children into a lane-by-lane prune/migrate queue.
2. Expand `heliosCLI-wtrees` children and split clean vs dirty lanes.
3. Resolve the detached `heliosCLI-composite-actions` root.
4. Leave `helios-cli/.worktrees/helios-cli--mod-cli-task-surface-v1` and `helios-cli/.worktrees/helios-cli--mod-policy-gate-v1` untouched.
5. Collapse `colab-wtrees` and `helMo-wtrees` only after the main helios lanes are reduced.
