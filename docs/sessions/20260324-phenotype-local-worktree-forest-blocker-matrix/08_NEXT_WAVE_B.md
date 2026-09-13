# 08_NEXT_WAVE_B — next 24 items (6 × 4)

**Follows** `07_NEXT_WAVE.md`. Re-verify paths before acting. **Snapshot:** 2026-03-24. Skip full-repo inventory unless running a dedicated inventory session.

## Slice 1 — heliosApp (deeper lanes)

**Path note (local layout):** several heliosApp lanes live under `repos/worktrees/heliosApp/<lane>/` (not only under `heliosApp/heliosApp-wtrees/`). Re-verify with `git worktree list` from the `heliosApp` canonical repo.

1. `heliosApp-wtrees/ci-workflow-fix` — dirty/repair or merge and remove.
2. `heliosApp-wtrees/claude-md-standardize` — same.
3. `heliosApp-wtrees/parity-debt-wave-20260303` / `phase2-decompose` / `sync-main-upstream-20260305` — pick next by branch age or CI failure.
4. `heliosApp/heliosApp-wtrees/decomp-20260314` — if still active, coordinate with `07` items 1–4 (no duplicate PR work).

## Slice 2 — heliosCLI (deeper lanes)

5. `heliosCLI-wtrees/code-reduction` — status and merge or close.
6. `heliosCLI-wtrees/review-orchestrator` / `spec-docs-pr` — triage.
7. `heliosCLI-wtrees/oxc-migration-20260303` — align with App oxc lanes.
8. `heliosCLI-wtrees/bazel-llvm-modules-fix` — resolve `MODULE.bazel` + untracked patch or drop lane.

## Slice 3 — helios-cli / colab / helMo (follow-through)

9. Document symlink policy for `colab-wtrees/helios-integration` (alias vs real worktree).
10. `helMo` canonical root dirty set — commit, stash, or branch.
11. Ensure `tempdir.ts` / `.tmp/runtime-secrets-tests` in `.gitignore` if not already in heliosApp runtime.
12. Re-run secrets + PTY test subsets after any merge from decomp lane.

## Slice 4 — AgilePlus / phenotype\* (mixed layout)

13. `AgilePlus` + `AgilePlus-wtrees` — pick one canonical layout note in repo docs (no mass moves without decision).
14. `phenotype-shared-wtrees` — enumerate dirty descendants; one repair PR.
15. `phenotypeActions-wtrees` / `phenotype-config-wtrees` — verify containers clean vs dirty.
16. `phenodocs` / `phench` — quick `git status` on canonical roots; file issues for drift.

## Slice 5 — template / thegent / governance tooling

17. `template-commons-wtrees` — remove stale prunable lane if still listed.
18. `thegent` detached legacy lane (`.worktrees/...lane-split-modules-bootstrap-v2`) — clean, merge, or document abandon.
19. Run `./scripts/worktree_governance.sh list` (or repo equivalent) from `repos` hub; capture output in session notes if changed.
20. `./scripts/worktree_governance.sh migrate-legacy --dry-run` — review output; execute only if policy-approved.

## Slice 6 — trace / trash / ralph / portage tail

21. After trace locks clear: migrate `trace-wtrees/*` toward `repos/worktrees/<project>/...` layout per AGENTS.md.
22. `trash-cli` PROJECT-wtrees lane — attach or `git worktree remove` with backup of unique commits.
23. `ralph-codex-loop` — `git init` + first commit **or** remove broken worktree registration.
24. Portage: second-pass on **non-tmp** detached lanes (`oxc-governance-fix`, `oxc-migration-fix`, policy-federation-onboard) — owner decision, then prune or repair.

---

**Roles:** implementer owns slices 1–3; platform/governance owns 4–5; ops + security review on secrets paths (slice 3–4). **CI policy:** no merge with red checks unless exception documented.
