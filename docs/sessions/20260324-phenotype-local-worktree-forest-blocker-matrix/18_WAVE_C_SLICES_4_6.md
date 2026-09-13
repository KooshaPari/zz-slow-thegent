# Wave C — Slices 4–6 (execution notes)

**Date:** 2026-03-24  
**Purpose:** Close **Ship** gaps from **`09_NEXT_WAVE_C.md`** slices **4–6** with repo-grounded runbooks, issues, and verification — without destructive worktree operations.

---

## Slice 4 — cliproxy / API surfaces

| Item                                        | Ship outcome                                                                                                                                                                                                                                                                                     |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **13 — OpenAPI / credential payloads**      | **Doc stance:** Breaking changes to credential event payloads must be reviewed in the **cliproxy** repo when the public SDK/OpenAPI is published. Until then, treat **SDK plan / internal contract** as source of truth; add a **contract note PR** in cliproxy when the OpenAPI artifact lands. |
| **14 — Rate-limit / bridge detached lanes** | **Umbrella issue:** [thegent#559](https://github.com/KooshaPari/thegent/issues/559) — checklist for detached lanes; split per-lane issues when an owner picks them up.                                                                                                                           |
| **15 — `wtrees` vs `wtress`**               | **Done:** `repos/README.md` + **`docs/reference/phenotype_repos_hub.md`** on `main` — naming note + prefer `repos/worktrees/<project>/...`.                                                                                                                                                      |
| **16 — Composite-actions consumers**        | **Done:** **`docs/reference/composite-actions.md`** on `main` — definitions + consumer workflows.                                                                                                                                                                                                |

---

## Slice 5 — portage / infra / governance scripts

| Item                                         | Ship outcome                                                                                                                                                                                                                                                                |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **17 — Backup before `git worktree remove`** | **Procedure:** (1) `git worktree list` — note path. (2) `git -C <path> log --oneline -20` — copy unique SHAs. (3) Optional: `git format-patch -o /tmp/backup-<branch> <base>..HEAD` in that worktree. (4) Only then `git worktree remove <path>` (or `remove` after merge). |
| **18 — `/private/tmp` portage cleanup**      | **Manual schedule:** Run **monthly** or when disk pressure appears. Example audit (read-only): `find /private/tmp -maxdepth 2 -name '*portage*' 2>/dev/null \| head`. **Destructive delete** only with explicit owner approval — do not automate deletion here.             |
| **19 — Portage `.worktrees` policy**         | **Policy:** New lanes belong under **`repos/worktrees/<project>/...`** per root **`AGENTS.md`** / **`CLAUDE.md`**; avoid ad-hoc top-level `*-wtrees` except during migration (compatibility symlinks).                                                                      |
| **20 — Script lint**                         | **Verified:** `bash -n scripts/worktree_governance.sh` → **OK** (2026-03-24). Re-run after any edit to that script (do **not** use `sh -n` — bash process substitution).                                                                                                    |

---

## Slice 6 — trace / trash / ralph / org-wide

| Item                                                     | Ship outcome                                                                                                                                                                 |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **21 — trace smoke `git worktree add`**                  | **Deferred** while **trace** lanes remain locked (**05_KNOWN_ISSUES**). Re-open when locks clear.                                                                            |
| **22 — trash-cli `PROJECT-wtrees` vs `repos/worktrees`** | **Doc stance:** Target layout is **`repos/worktrees/...`** per **`AGENTS.md`**. Legacy **`PROJECT-wtrees`** paths are migration sources — normalize when touching that repo. |
| **23 — ralph-codex-loop**                                | **Decision:** Already **archived** under **`.archive/ralph-codex-loop`** per session notes — no new init unless product revives it.                                          |
| **24 — Cross-repo PTY/secrets duplication**              | **Tracking issue:** [thegent#560](https://github.com/KooshaPari/thegent/issues/560) — extract shared helpers if **>50 LOC** duplicated after a quick scan.                   |

---

## Cross-links

- **`09_NEXT_WAVE_C.md`** — original slice definitions.
- **`composite-actions.md`** — composite action map.
- **`phenotype_repos_hub.md`** — hub `wtrees`/`wtress` note.
- **`05_KNOWN_ISSUES.md`** — operational blockers (trace, trash, portage, ralph).
