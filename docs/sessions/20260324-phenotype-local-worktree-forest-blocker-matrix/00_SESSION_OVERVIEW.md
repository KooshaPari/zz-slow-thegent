# 00_SESSION_OVERVIEW

## Goal

Consolidate the local worktree-forest scan into a blocker matrix that orders cleanup work by risk and migration readiness.

## Scope

- Local Phenotype repos under `/Users/kooshapari/CodeProjects/Phenotype/repos`
- Family-level worktree matrices for the largest blocker surfaces
- Canonical-vs-legacy layout drift, dirty roots, detached lanes, locked lanes, and prunable lanes

## Document map

| File                         | Purpose                                                                                 |
| ---------------------------- | --------------------------------------------------------------------------------------- |
| `00_SESSION_OVERVIEW.md`     | Goal, scope, status, links                                                              |
| `ACTIVE_BACKLOG.md`          | **Execution index** for waves 07–13; halt new waves until progress (see wave G)         |
| `01_RESEARCH.md`             | Family matrices, lane names, baseline counts                                            |
| `04_QUEUE_CADENCE.md`        | How 24-item / six-slice turns relate to docs; **full-turn** (PR/merge/changelog) rules  |
| `FULL_TURN_DELIVERY.md`      | **Release-grade turn:** `gh` evidence, merge gates, changelog/version, PR #549 snapshot |
| `05_KNOWN_ISSUES.md`         | Confirmed blockers and resolution criteria                                              |
| `06_TESTING_STRATEGY.md`     | Validation commands and recommended next checks                                         |
| `07_NEXT_WAVE.md`            | Wave A — 24 items                                                                       |
| `08_NEXT_WAVE_B.md`          | Wave B — next 24 items                                                                  |
| `09_NEXT_WAVE_C.md`          | Wave C — next 24 (process, release, DX, org-wide)                                       |
| `10_NEXT_WAVE_D.md`          | Wave D — next 24 (CI, security, docs, PR, governance, debt)                             |
| `11_NEXT_WAVE_E.md`          | Wave E — next 24 (ops, compliance, perf, testing depth, handoff, closure)               |
| `12_NEXT_WAVE_F.md`          | Wave F — next 24 (roadmap, knowledge, DR, DoD, observability, queue meta)               |
| `13_NEXT_WAVE_G.md`          | Wave G — next 24 (GitHub policy, reproducibility, SBOM, flags, people, halt/pivot)      |
| `16_PARALLEL_AGENT_AUDIT.md` | **5-agent Tier-1** DAG + consolidated Wave C–E audit (50 items)                         |

## Related session packs

- `../20260324-phenotype-local-worktree-forest-inventory/` — forest counts and high-risk family list
- `../20260324-helios-family-lane-matrix/` — helios / colab / helMo lane detail
- `../20260324-phenotype-local-vs-kooshapari-account-inventory/` — local standalone roots vs authenticated GitHub account repo surface
- `../20260324-worktree-governance-legacy-remediation/` — legacy lane blockers (for example detached `thegent` lanes)

## Status Summary

- **`thegent` Control**: Conflict-free detached lane resolved; remains dirty/detached (non-migratable).
- **`heliosApp` / `heliosCLI`**: Critical mass of dirty-root pressure; 350+ dirty paths in `heliosApp`.
- **`cliproxy` Family**: Naming drift (`cliproxy-wtrees` vs `cliproxy-wtress`) and detached legacy lanes.
- **`AgilePlus` / `phenotype*`**: Complex mixed-layout families (canonical + legacy); 500+ dirty paths in `AgilePlus`.
- **`portage` / `trace` / `trash-cli`**: High operational noise (prunable, detached, and locked initializing lanes).
- **`template-*`**: Structurally stable, but `template-commons` contains a stale prunable lane.

## Priority Burn-Down Queue

1. **Critical Repair**: `heliosApp` and `heliosCLI` dirty root stabilization.
2. **Canonicalization**: Resolve `cliproxy` typo-forest naming drift.
3. **Operational Cleanup**: Prune `portage` stale lanes and unlock `trace` initializing lanes.
4. **Layout Normalization**: Standardize `AgilePlus` and `phenotype-shared` mixed-forest structures.

## References

- `ACTIVE_BACKLOG.md` — execute waves 07–13; **no new wave H** until progress
- `01_RESEARCH.md`
- `04_QUEUE_CADENCE.md`
- `05_KNOWN_ISSUES.md`
- `06_TESTING_STRATEGY.md`
- `07_NEXT_WAVE.md` — wave A **24-item** (6×4) session-end queue
- `08_NEXT_WAVE_B.md` — wave B **next 24** (after wave A)
- `09_NEXT_WAVE_C.md` — wave C **next 24** (after wave B)
- `10_NEXT_WAVE_D.md` — wave D **next 24** (after wave C)
- `11_NEXT_WAVE_E.md` — wave E **next 24** (after wave D)
- `12_NEXT_WAVE_F.md` — wave F **next 24** (after wave E)
- `13_NEXT_WAVE_G.md` — wave G **next 24** (after wave F)
- `19_NEXT_50_WORK_ITEMS.md` — **Next 50** queue (preamble + waves D + E)
