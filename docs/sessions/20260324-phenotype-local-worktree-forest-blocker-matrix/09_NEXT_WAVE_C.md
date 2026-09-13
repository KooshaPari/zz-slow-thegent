# 09_NEXT_WAVE_C — next 24 items (6 × 4) + **Ship** gates

**Follows** `07` / `08`. **Snapshot:** 2026-03-24.

**Full-turn rule:** Each slice should end with **at least one** merge-ready outcome **or** a logged exception (**red CI**, **approval**, **dirty tree**) in `05_KNOWN_ISSUES.md`. See **`FULL_TURN_DELIVERY.md`** and **`04_QUEUE_CADENCE.md`** (Full-turn delivery).

**Evidence bundle per slice:** `gh pr view` URL(s), `CHANGELOG` diff (or “N/A — internal-only”), version file bump if applicable.

**Runbook (slices 4–6):** **`18_WAVE_C_SLICES_4_6.md`** — cliproxy, portage/governance, trace/trash/ralph/org; umbrella **[#559](https://github.com/KooshaPari/thegent/issues/559)**, reuse research **[#560](https://github.com/KooshaPari/thegent/issues/560)**.

**Next 50 (Wave D + E):** **`19_NEXT_50_WORK_ITEMS.md`** — ordered queue **1–50** after this wave’s Ship work.

---

## Slice 1 — heliosApp / product integration (4)

1. Confirm **CI workflow** on `heliosApp` default branch matches local `bun`/Node matrix used in decomp lane.
   - **Ship:** PR updating workflow **or** issue + doc; **merge to `main`** after green CI. **Changelog:** release repo’s `CHANGELOG` / release notes if matrix change affects contributors.

2. Add or update **PR template** checklist: runtime tests, typecheck, worktree name.
   - **Ship:** PR to `main`; **merge** after review. **Docs:** `.github/pull_request_template.md`.

3. **CHANGELOG** or release notes entry for PTY/secrets test split (if user-facing).
   - **Ship:** PR with `CHANGELOG` **Unreleased** section; **merge** with (1) or standalone.

4. **ADR or short note** if file-size policy drove splits (link to line-count targets).
   - **Ship:** PR adding `docs/` ADR or session link; **merge** to `main`.

---

## Slice 2 — heliosCLI / CLI release hygiene (4)

5. Versioning: ensure **semver** / tag policy for `heliosCLI` matches release workflow.
   - **Ship:** PR touching version source (`Cargo.toml` / `package.json` / release workflow); **tag** only if release branch policy says so.

6. **Binary artifacts** / smoke script documented for reviewers.
   - **Ship:** PR to `main` updating `docs/` or `README`; **merge** after green CI.

7. **Cross-repo** `helios-cli` vs `heliosCLI` naming: doc the canonical names for contributors.
   - **Ship:** PR in **each** repo **or** single doc in primary repo + links; **merge**.

8. Deprecations: grep for `@deprecated` in touched CLI surfaces; note in changelog if any.
   - **Ship:** PR with changelog **Deprecated** entries; **merge**.

---

## Slice 3 — developer experience / colab / helMo (4)

9. **CONTRIBUTING.md** (or equivalent): document `tempdir.ts` / `.tmp` for secrets tests; never commit scratch.
   - **Ship:** PR to `main`; **changelog** “Added” if public repo.

10. **Disk space** runbook: ENOSPC → clear `.tmp`, then user caches; link in troubleshooting.
    - **Ship:** PR; **merge**; **docs** index updated.

11. `colab` / `helMo`: if canonical roots stay dirty, create **tracking issue** instead of silent drift.
    - **Ship:** `gh issue create` with links; **or** PR that stabilizes root (**merge** if small).

12. **Editor/IDE**: ensure `.gitignore` covers `.tmp/runtime-secrets-tests` and local tooling noise.
    - **Ship:** PR; **merge** to `main`; note in **Unreleased** if behavior-visible.

---

## Slice 4 — cliproxy / API surfaces (4)

13. **OpenAPI** or client contract: confirm no breaking change from credential event payloads.
    - **Ship:** PR with contract note or **issue** + label; **merge** doc-only if applicable.

14. **Rate-limit / bridge** lanes in cliproxy forests: one ticket per detached lane.
    - **Ship:** `gh issue create` per lane **or** single umbrella issue with checklist.

15. **Duplicate forest** (`wtrees` vs `wtress`): add **README** note at parent `repos` level (pointer only).
    - **Ship:** PR to **`Phenotype/repos`** or owning meta-repo; **merge**.

16. **Composite-actions** repos: list which are GitHub Actions consumers; avoid orphan checkouts.
    - **Ship:** PR adding `docs/reference/` table; **merge**.

---

## Slice 5 — portage / infra / governance scripts (4)

17. **Backup** unique commits on any worktree before `git worktree remove`.
    - **Ship:** Doc PR in `thegent` / `repos` hub **or** runbook addition; **merge**.

18. **Cron or manual** schedule for `/private/tmp` portage cleanup (owner + command).
    - **Ship:** Issue **or** internal runbook PR; **merge** if doc lives in git.

19. **Portage** `.worktrees` policy: who may create lanes under canonical path.
    - **Ship:** ADR or `AGENTS.md` clarification PR; **merge**.

20. Run **lint on scripts** (`bash -n scripts/worktree_governance.sh` — **not** `sh -n`; bash process substitution — or project Task) after any script edit.
    - **Ship:** PR with script fix + CI green; **merge**; **changelog** if user-facing.

---

## Slice 6 — trace / trash / ralph / org-wide (4)

21. **trace**: when locks clear, add **smoke test** for `git worktree add` in new layout.
    - **Ship:** PR with test; **merge** after green.

22. **trash-cli**: confirm **PROJECT-wtrees** naming matches `AGENTS.md` (`repos/worktrees/...` target).
    - **Ship:** PR doc fix **or** issue; **merge** if trivial.

23. **ralph-codex-loop**: decide **archive vs init**; if archive, move to `.archive/` per stability protocol.
    - **Ship:** PR/issue decision record; **merge** if filesystem change in repo.

24. **Phenotype org**: skim **cross-repo reuse** (shared modules) for duplicated PTY/secrets patterns—file extraction issue if >50 LOC duplicated.
    - **Ship:** `gh issue create` in tracking repo **or** PR to shared module; **merge** if code moves.

---

**Roles:** PM/tech-lead owns slice **Ship** bundling; implementer executes PRs; **SRE** owns 17–20; **security** reviews secrets paths; **architect** owns 24.

**CI policy:** **No merge to `main` / `release/*` with red required checks** unless exception documented (`FULL_TURN_DELIVERY.md`).
