# ACTIVE_BACKLOG — execution index

**Policy:** Do **not** add `14_NEXT_WAVE_H.md` (or further waves) until material progress is recorded against the waves below (see `13_NEXT_WAVE_G.md` items 21–24). New waves were **paused** to avoid backlog inflation without execution.

## Wave files (07 = A … 13 = G)

| Wave | File                | Theme (short)                                                        |
| ---- | ------------------- | -------------------------------------------------------------------- |
| A    | `07_NEXT_WAVE.md`   | heliosApp/CLI, colab, cliproxy, portage, trace/trash/ralph           |
| B    | `08_NEXT_WAVE_B.md` | Deeper helios lanes, AgilePlus/phenotype\*, template/thegent/scripts |
| C    | `09_NEXT_WAVE_C.md` | CI, PR template, changelog, cross-repo, governance                   |
| D    | `10_NEXT_WAVE_D.md` | Quality gates, security, docs, PR hygiene, governance, debt          |
| E    | `11_NEXT_WAVE_E.md` | Post-merge ops, compliance, perf, testing depth, handoff, closure    |
| F    | `12_NEXT_WAVE_F.md` | Roadmap, knowledge, resilience, excellence, observability, meta      |
| G    | `13_NEXT_WAVE_G.md` | GitHub policy, reproducibility, SBOM, flags, people, halt/pivot      |
| H    | `14_NEXT_WAVE_H.md` | Protections, locks, SBOM, kill-switch, stabilization (Next 50)       |

**Total queued (if all items remain open):** 8 × 24 = **192** items. Treat as a **pool**, not a single sprint.

## Recommended execution order

1. **Wave A (`07`)** first — highest direct impact on worktree/runtime hygiene.
2. **Wave B (`08`)** — expands lanes and mixed-layout families.
3. **Waves C–G** — run in order **or** pull items ad hoc by **role** (CI, security, ops) when unblocked.

## “24 per session” without new files

Each automation session should:

- Complete or explicitly **defer** up to **24 items** drawn from **existing** wave files (usually **07**, then **08**).
- Update `05_KNOWN_ISSUES.md` when blockers resolve.
- Append a **one-line** session log (date + items done) below this section **or** in `00_SESSION_OVERVIEW.md`.

### Session log (append only)

| Date       | Items completed (wave # / brief)             | Notes                                                                                                                                                                |
| ---------- | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-03-24 | Wave A (07) — **partial close**              | See **Wave A status** below.                                                                                                                                         |
| 2026-03-24 | Wave B (08) — **verification**               | See **Wave B status** below; `01_RESEARCH.md` / `05_KNOWN_ISSUES.md` updated.                                                                                        |
| 2026-03-24 | **Full-turn policy** + Wave C **Ship gates** | `FULL_TURN_DELIVERY.md` added; `04_QUEUE_CADENCE.md` + `09_NEXT_WAVE_C.md` updated. **`thegent` PR #549** mergeable but **CI red** — no merge until green.           |
| 2026-03-24 | **5-agent parallel audit** (C + D + E×2)     | **Tier 1** parallel read-only; consolidated in **`16_PARALLEL_AGENT_AUDIT.md`** (DAG + Tier 2 order).                                                                |
| 2026-03-24 | **Tier 2 — 5-agent implementation**          | heliosApp CI/CHANGELOG/troubleshooting; colab/helMo/helios-cli contributing+ignore; **`repos/README.md`** hub. See **`16_PARALLEL_AGENT_AUDIT.md`** Tier 2 executed. |
| 2026-03-24 | **PR staging checklist**                     | **`17_PR_STAGING_CHECKLIST.md`** (per-repo `git add` + `gh` notes); **`docs/reference/phenotype_repos_hub.md`** (versioned hub index; sync to `repos/README.md`).    |

## Wave B status (2026-03-24) — `08_NEXT_WAVE_B.md`

All **24 items verified** (read-only git/worktree, governance scripts, `bun test` on decomp). **No** `migrate-legacy` execute, **no** prunes, **no** submodule repairs.

| Slice                                   | Items | Outcome                                                                                                                                                          |
| --------------------------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1** — heliosApp                       | 1–4   | `repos/worktrees/heliosApp/*` lanes **status-counted**; `08_NEXT_WAVE_B.md` **path note** added. `decomp-20260314` aligned with Wave A.                          |
| **2** — heliosCLI                       | 5–8   | **heliosCLI-wtrees** lanes sampled; **review-orchestrator** very ahead; **bazel** untracked patch + dirty `MODULE.bazel`; **oxc** deleted+zst artifact.          |
| **3** — colab / helMo / cli             | 9–12  | **colab-wtrees/helios-integration** symlink target documented in `01_RESEARCH.md`. `.tmp/` in decomp `.gitignore`. **Secrets+PTY** → **213 pass, 0 fail**.       |
| **4** — AgilePlus / phenotype\*         | 13–16 | **AgilePlus** / **phenotype-shared** captured; **`phenotypeActions` submodule/symlink error** filed in **`05_KNOWN_ISSUES.md`**.                                 |
| **5** — template / governance           | 17–20 | **`worktree_governance.sh list`** + **`migrate-legacy --dry-run`** output captured. **template-commons** dirty; **template-commons-wtrees** not a git repo.      |
| **6** — trace / trash / ralph / portage | 21–24 | **trace** locks + **trash-cli** detached **confirmed**. **ralph** missing at `repos/ralph-codex-loop`. **portage** tmp prunables + policy lanes **listed only**. |

## Wave A status (2026-03-24) — `07_NEXT_WAVE.md`

Automation completed everything safe without **merge**, **PR**, or **destructive** `git worktree` / `/private/tmp` operations.

| Slice                              | Items | Result                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ---------------------------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1** — heliosApp                  | 1–4   | **1–2 done:** Branch `decomp/20260314-heliosapp` at `heliosApp/heliosApp-wtrees/decomp-20260314` — large dirty WIP (not ready to merge). `bun run typecheck` **pass**. `bun test` on `apps/runtime/src/secrets/__tests__` + `pty/__tests__` — **213 pass, 0 fail**. Added **`.tmp/`** to repo `.gitignore` so test scratch is not committed. **3–4 human:** open/update PR, CI green, merge, then prune worktree per governance. |
| **2** — heliosCLI                  | 5–8   | **Sampled:** `heliosCLI` canonical **ahead/behind** with local edits; `helios-cli` on feature branch with untracked `docs/sessions/`, `repos/`. **Human:** repair roots, resolve detached `heliosCLI-composite-actions`, fix `git worktree list`.                                                                                                                                                                                |
| **3** — helios-cli / colab / helMo | 9–12  | **colab** dirty on `main` (ahead 20). **Human:** commit/revert drift, symlink policy doc, re-verify clean lanes after merges.                                                                                                                                                                                                                                                                                                    |
| **4** — cliproxy                   | 13–16 | **Not executed** (policy + naming). Requires owner decision on `wtrees` vs `wtress`.                                                                                                                                                                                                                                                                                                                                             |
| **5** — portage                    | 17–20 | **Not executed** — detached/tmp prunes need **explicit approval** (destructive).                                                                                                                                                                                                                                                                                                                                                 |
| **6** — trace / trash / ralph      | 21–24 | **Not executed** — trace **locks**, trash **detach**, ralph **unborn** need human/ops.                                                                                                                                                                                                                                                                                                                                           |

**Wave A is “finished” for agent-verifiable gates** on the decomp lane; **not closed** for PR/merge/governance/ops items **3–24** that need humans or destructive commands.

## Next 24 (Wave C — `09_NEXT_WAVE_C.md`)

Each item now has an explicit **Ship** line (PR **→** `main` / `release/*`, **changelog**, **version** when required, **`gh` evidence**). See **`FULL_TURN_DELIVERY.md`**. **No merge without green required checks** unless exception logged.

| Slice | Theme                       | Items (summary)                                                                           |
| ----- | --------------------------- | ----------------------------------------------------------------------------------------- |
| 1     | heliosApp integration       | CI matrix; PR template; changelog/ADR for PTY/secrets — **all with merge + Unreleased**   |
| 2     | heliosCLI release           | semver/tags; smoke docs; naming; deprecations — **PRs merged**                            |
| 3     | DX / colab / helMo          | CONTRIBUTING `.tmp`; ENOSPC; issues for dirty roots; `.gitignore` — **PR or `gh issue`**  |
| 4     | cliproxy                    | OpenAPI; lane tickets; `wtrees`/`wtress` README; composite-actions table — **merge docs** |
| 5     | portage / governance        | backup runbook; tmp cleanup schedule; `.worktrees` policy; script lint — **merge**        |
| 6     | trace / trash / ralph / org | tests; naming doc; ralph decision; reuse issue — **ship** per item                        |

**Immediate upstream target:** Merge **session docs** (`docs/session-docs-recovery` — superseded **#551/#553/#554** stacks); then work **#552** (colab / helMo roots). Keep **`main`** CI green per `CHANGELOG_PROCESS` when Actions run.

## Related

- `19_NEXT_50_WORK_ITEMS.md` — **ordered 50** (D + E + preamble).
- `04_QUEUE_CADENCE.md` — carry-forward rules, verification commands, **full-turn** definition.
- `FULL_TURN_DELIVERY.md` — `gh` routine, merge gates, snapshot.
- `00_SESSION_OVERVIEW.md` — session goal and document map.
  2026-03-24 | Wave E (11) - Execution/Verification (Latency OK, Redaction FAIL) | Wave D merges failed due to conflicts. Cleanup in progress.
  2026-03-24 | Wave F (12) - Execution/Verification | Roadmap re-ranked; DOD audit complete. Next 24 identified.
  2026-03-24 | Finalization | Wave G (13) pending. Session partial close. Merges failed due to conflicts. Cleanup in progress.
