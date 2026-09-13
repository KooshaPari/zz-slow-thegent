# 04_IMPLEMENTATION_STRATEGY

## Approach

- Use shell and git-native inspection only.
- Split the forest into family slices so the work stays parallel and resumable.
- Treat any detached or prunable lane as a blocker until it is explicitly cleaned.

## Rationale

- The local repository surface is too large for a single exhaustive pass.
- Family-based slicing surfaces layout drift faster than chasing individual lanes in isolation.

## Reusable Commands

- `find /Users/kooshapari/CodeProjects/Phenotype/repos -maxdepth 2 -type d \( -name '.worktrees' -o -name '*-wtrees' -o -name '*-wtress' \)`
- `git -C <repo> worktree list --porcelain`
- `git -C <repo> status --short`
