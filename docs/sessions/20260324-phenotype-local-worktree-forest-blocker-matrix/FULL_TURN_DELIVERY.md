# Full-turn delivery (release-grade)

**Purpose:** Align automation turns with **shipping**: merges to **`main`** or a **`release/*`** branch, with **traceable GitHub state** and **versioned documentation**.

## Definition — “full turn” (minimum)

Each **full** automation turn **must** close with **at least one** of the following **per repo touched**, unless a written **exception** is recorded in `05_KNOWN_ISSUES.md` (blocked CI, policy hold, or destructive-op approval pending):

| Gate          | Requirement                                                                                                                 | Evidence                                                                              |
| ------------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **PR**        | Open or update a PR with a scoped branch; base = `main` or `release/*`                                                      | `gh pr view <n> --json url,baseRefName,headRefName,mergeable`                         |
| **CI**        | Required checks **green** (or fix-forward in the same PR)                                                                   | `gh pr checks <n>` / Actions URLs                                                     |
| **Merge**     | Merge to base after green (squash/merge per repo rules)                                                                     | `gh pr merge` or GitHub UI merge event; `main` fast-forward or merge commit on remote |
| **Changelog** | Entry under `## [Unreleased]` (or project template) for user-visible or policy-visible change                               | Diff in `CHANGELOG.md` / `docs/CHANGELOG.md` per `docs/guides/CHANGELOG_PROCESS.md`   |
| **Version**   | Semver bump **when** the release policy says so (not every docs-only session): crate `Cargo.toml`, `pyproject.toml`, or tag | Same PR or follow-up release PR                                                       |
| **Docs**      | Session packs: update `00_SESSION_OVERVIEW.md` / `ACTIVE_BACKLOG.md`; product repos: public docs if behavior changed        | Linked commit                                                                         |

**Multiple merges per turn** are encouraged when CI allows: e.g. **docs PR** + **fix PR** in different repos, or stacked PRs in one repo.

## Billing / Actions quota — when required checks never run

Sometimes **GitHub Actions does not start jobs** (billing exhausted, org plan limits, or account-level blocks). Required checks then stay **queued** or **pending** forever. That is **infrastructure**, not a failing test.

**Allowed merge path** (exception to the usual “green CI” gate):

1. **Confirm** the problem is **capacity/billing**, not a red workflow: open the **Actions** tab and look for billing errors, “not enough minutes,” or jobs that never leave **Queued** with no runner.
2. **Run** whatever you can **locally** (for example `task quality`, `cargo test`, `uv run pytest`) and note the commands in the PR or session log.
3. **Log** a one-line exception in **`05_KNOWN_ISSUES.md`**: repo, PR number, date, `reason: Actions billing / quota`, and what was verified locally.
4. **Merge** with administrator bypass (requires repo **admin**):  
   `gh pr merge <n> --repo <owner>/<repo> --squash --admin`  
   Use **`--merge`** or **`--rebase`** instead of **`--squash`** if the repo policy forbids squash.

**Do not** use **`--admin`** when CI is **actually failing** (red logs, failing tests). Fix-forward or revert in that case.

**Optional (repo settings):** Under **Settings → Rules → Rulesets**, you can add **bypass actors** for trusted roles so merges are not permanently blocked when billing recurs. Only change rulesets with org approval.

**Cleanup:** When billing is restored, remove the billing-exception line from **`05_KNOWN_ISSUES.md`** and let **`main`** go green on Actions again.

## GitHub CLI routine (every turn)

```bash
gh auth status
gh pr list --repo <owner>/<repo> --state open --limit 20
# For each candidate merge:
gh pr view <n> --repo <owner>/<repo>
gh pr checks <n> --repo <owner>/<repo>
# After merge:
gh pr list --repo <owner>/<repo> --state merged --limit 5
```

## Snapshot — `KooshaPari/thegent` (2026-03-24)

| PR                                                     | Title                                                     | Base   | Mergeable | CI                                                                                  |
| ------------------------------------------------------ | --------------------------------------------------------- | ------ | --------- | ----------------------------------------------------------------------------------- |
| [#549](https://github.com/KooshaPari/thegent/pull/549) | Migrate thegent-cache to phenotype-infrakit cache-adapter | `main` | MERGEABLE | **Red** — multiple failing workflows (Build wheels, Lint & Test, Policy Gate, etc.) |

**Action:** **Do not merge** until CI is green and review threads resolved (org **CI completeness** policy). Next turn should **fix-forward** on `feat/migrate-cache` or rebase and re-run checks.

## Blockers — local canonical trees

Many Phenotype canonical roots (`thegent`, `heliosApp`, …) show **large dirty working trees** and non-GitHub `origin` (e.g. airlock). **Full-turn PRs** should be prepared from **dedicated worktrees** or a **fresh branch** from `upstream/main` with **only** scoped files; avoid mixing session docs with unrelated WIP.

## Script lint note

`scripts/worktree_governance.sh` is **bash** — use `bash -n scripts/worktree_governance.sh` (not `sh -n`, which errors on `process substitution`).

## Related

- `04_QUEUE_CADENCE.md` — per-turn batch size + **full-turn** rules
- `09_NEXT_WAVE_C.md` — Wave C items with **Ship** criteria
- `docs/guides/CHANGELOG_PROCESS.md` — changelog format
