# Worktree and Delegation Governance Index

Use this index as the entrypoint for multi-agent worktree/commit/delegation governance.

## Documents

| File                                          | Purpose                                                                                                 |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `METHODOLOGY_SYNTHESIS_GSD_BMAD_AGILEPLUS.md` | **Read first.** Unified process principles from GSD + BMAD + AgilePlus integrated into thegent workflow |
| `UNIFIED_WORKTREE_WORKFLOW_GOVERNANCE.md`     | Path schema, lifecycle states, BMAD/AgilePlus harmonization, legacy migration plan                      |
| `WORKTREE_SCALE_COMMIT_VERSION_PR_POLICY.md`  | Commit strategy, versioning, PR topology, merge policy (still authoritative)                            |
| `DELEGATION_ARCHITECTURE_LN.md`               | L1→Ln role layers, universal delegation decision engine                                                 |
| `TASK_CLASSIFIER_SCHEMA.yaml`                 | Canonical YAML classifier: domain, scale, risk, worktree mode                                           |
| `DOMAIN_PLAYBOOKS.md`                         | Per-domain delegation rules (backend, frontend, infra, data, security, QA)                              |
| `GOVERNANCE_ROADMAP_DAG.md`                   | Governance evolution DAG                                                                                |
| `MCP_A2A_CONTROL_PLANE_BOUNDARY.md`           | MCP and agent-to-agent control plane boundaries                                                         |
| `ROLLOUT_PHASES_CHECKLIST.md`                 | Lane rollout checklist                                                                                  |

## Reading Order

1. `UNIFIED_WORKTREE_WORKFLOW_GOVERNANCE.md` — path schema + cross-system vocabulary
2. `WORKTREE_SCALE_COMMIT_VERSION_PR_POLICY.md` — commit/PR/merge rules
3. `TASK_CLASSIFIER_SCHEMA.yaml` — classifier fields and outputs
4. `DELEGATION_ARCHITECTURE_LN.md` — delegation tiers
5. `DOMAIN_PLAYBOOKS.md` — domain-specific rules

The canonical structured worktree refresh rule lives in `UNIFIED_WORKTREE_WORKFLOW_GOVERNANCE.md`; this index only points readers to that source and the CLI/script/MCP/task surfaces that expose it.

## Enforced Commands

```bash
./scripts/worktree_governance.sh new <domain> <scale> <change-anchor> [start-point]
./scripts/worktree_governance.sh check
./scripts/worktree_governance.sh state <change-anchor> <new-state>
./scripts/worktree_governance.sh list
./scripts/worktree_governance.sh prune [--dry-run]
```

The same lifecycle surface is also available through:

```bash
thegent worktree new <domain> <scale> <change-anchor> [start-point]
thegent worktree state <change-anchor> <new-state>
thegent worktree migrate-legacy <legacy-path> <domain> <scale> <change-anchor> [state]
thegent worktree list
thegent worktree prune [--dry-run]
thegent worktree check
thegent help worktree
thegent help git
task quality:governance:worktree-inventory
task quality:governance:legacy-remediation-report
```

## Non-Negotiables

1. Primary checkout stays on `main`. Retain `.thegent-primary-main`.
2. All non-primary worktrees under `<repo>/.worktrees/<domain>/<scale>/<change-anchor>/<state>/`.
3. No legacy bypass — `THGENT_WORKTREE_ALLOW_LEGACY=1` is blocked by strict gates.
4. Every M/L/XL worktree has a corresponding AgilePlus proposal (`agileplus validate --strict` before creation).
5. Legacy lanes are triaged through `task quality:governance:legacy-remediation-report` and migrated with `thegent worktree migrate-legacy` before they can join the canonical root.
6. On merge: `agileplus archive <change-anchor> --yes` then `git worktree prune`.
