# 02_SPECIFICATIONS

## Objective

Produce a durable inventory of the local worktree forest and classify it by layout health.

## Acceptance Criteria

1. Standalone git roots are counted separately from worktree forest roots.
2. Canonical `.worktrees` roots are distinguished from legacy `*-wtrees` / `*-wtress` roots.
3. Detached, locked, and prunable lanes are called out explicitly.
4. Mixed-layout families are identified as blockers.

## Classification Rules

- `clean`: no obvious layout drift and no detached/locked/prunable indicators.
- `mixed`: both canonical and legacy worktree layouts present.
- `blocked`: detached, locked, prunable, or heavily dirty lanes present.

## Output Contract

- A session overview with counts.
- A research note with family-level findings.
- A known-issues note with the highest-risk blockers.
