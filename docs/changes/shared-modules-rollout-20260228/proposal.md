# Shared Modules Rollout 2026-02-28

## Goal

Extract high-value shared modules across Phenotype repos to reduce duplicate implementation burden,
stabilize governance/quality patterns, and keep `thegent` focused on orchestration/application
composition.

## Scope

- In scope: shared CI/governance modules, config/schema cores, queue/orchestration components,
  proxy/auth SDK surfaces, and standardized lane/worktree execution contracts.
- Out of scope: `4sgm`, `trace`, `parpour`, `civ`.

## Execution Model

- Worktree-first, branch-per-lane.
- One lane owns one module extraction target.
- One atomic PR per lane (code + tests + contract docs + migration notes).
- No fallback shims. Full cutover on touched boundaries.

## Active Worktrees (Bootstrapped)

1. `helios-cli` lane:
   `/Users/kooshapari/CodeProjects/Phenotype/repos/.worktrees/helios-cli--mod-policy-gate-v1`
   branch `mod/policy-gate-v1`
2. `thegent` composition lane:
   `/Users/kooshapari/CodeProjects/Phenotype/repos/.worktrees/thegent--mod-app-composition-v1`
   branch `mod/thegent-app-composition-v1`
3. `cliproxyapi-plusplus` lane:
   `/Users/kooshapari/CodeProjects/Phenotype/repos/.worktrees/cliproxyapi-plusplus--mod-proxy-auth-access-sdk-v1`
   branch `mod/proxy-auth-access-sdk-v1`

## Success Criteria

1. Each lane produces a standalone module with explicit interface contract and tests.
2. Consumer repos adopt versioned module contracts without ad hoc copy/paste sync.
3. Shared governance checks converge to one reusable policy gate implementation.
4. `thegent` command/runtime composition no longer embeds non-orchestrator domain logic.
