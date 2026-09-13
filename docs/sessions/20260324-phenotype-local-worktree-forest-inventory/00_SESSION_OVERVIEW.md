# 00_SESSION_OVERVIEW

## Goal

Inventory the local Phenotype worktree forest, not just standalone git roots, and identify the highest-risk layout drift and migration blockers.

## Scope

- Local directories under `/Users/kooshapari/CodeProjects/Phenotype/repos`
- Standalone git roots
- Worktree-forest roots: `.worktrees`, `*-wtrees`, `*-wtress`, and `PROJECT-wtrees`

## Snapshot

- Standalone git roots: `55`
- Worktree-family top-level roots: `45`
- Forest roots including nested variants: `65`
- Canonical `.worktrees` roots: `8`
- Legacy `*-wtrees` / `*-wtress` roots: `57`

## High-Risk Families

- `thegent`: detached dirty legacy lane still exists, but the main `DU` conflict was resolved.
- `heliosApp` / `heliosCLI`: very large dirty surfaces with many worktrees.
- `cliproxy-wtrees` / `cliproxy-wtress`: duplicate naming drift plus unusually large worktree forests.
- `AgilePlus`, `phenotype-shared`, `phenotypeActions`, `phenotype-config`: mixed canonical + legacy layouts.
- `portage`: prunable worktrees exist in `/private/tmp`, indicating stale refs.
- `trace`: one locked initializing lane plus multiple active lanes.
- `trash-cli`: detached worktree inside `PROJECT-wtrees`.

## References

- `01_RESEARCH.md`
- `05_KNOWN_ISSUES.md`
