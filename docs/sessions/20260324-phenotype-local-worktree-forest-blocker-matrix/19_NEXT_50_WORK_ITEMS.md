# 19_NEXT_50_WORK_ITEMS — ordered queue (preamble + Wave D + Wave E)

**Purpose:** One **numbered list of 50** items = **2** session-hygiene tasks + **Wave D** (`10_NEXT_WAVE_D.md`, 24 items) + **Wave E** (`11_NEXT_WAVE_E.md`, 24 items). Use as the default burn-down after Wave C runbooks (**`18_WAVE_C_SLICES_4_6.md`**). **Ship** rules: **`FULL_TURN_DELIVERY.md`**, **`04_QUEUE_CADENCE.md`**.

**Tracked issues (carry-forward):** thegent **[#559](https://github.com/KooshaPari/thegent/issues/559)** (cliproxy / umbrella), **[#560](https://github.com/KooshaPari/thegent/issues/560)** (PTY/secrets reuse research).

**Execution status:** **`20_NEXT_50_EXECUTION.md`** — item-by-item **Done / Deferred / Blocked** notes.

---

## Preamble (2)

| #     | Item                                                                                                                                                                  | Source          |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| **1** | **Cross-link Wave C:** ensure **`09_NEXT_WAVE_C.md`** points to **`18_WAVE_C_SLICES_4_6.md`** for slices **4–6** runbooks (cliproxy, portage, trace/trash/ralph/org). | Session hygiene |
| **2** | **Index this file** in **`ACTIVE_BACKLOG.md`** and **`00_SESSION_OVERVIEW.md`**; append a **one-line** session log row when merged.                                   | Session hygiene |

---

## Wave D — Quality, security, docs, PR hygiene, governance, debt (24)

| #      | Item                                                                                                                       | `10` § |
| ------ | -------------------------------------------------------------------------------------------------------------------------- | ------ |
| **3**  | Run repo **quality:pre-push** / equivalent; fix failures per CI completeness policy (no “pre-existing” dismissals on PRs). | 1      |
| **4**  | Align **Taskfile** / `task` targets with CI jobs (names + ordering).                                                       | 2      |
| **5**  | **Flaky test** registry: if any test needed retries, document in `05_KNOWN_ISSUES.md` or issue.                            | 3      |
| **6**  | **Coverage** threshold: confirm runtime secrets/PTY suites still meet project bar after splits.                            | 4      |
| **7**  | **Dependency audit** (`bun audit` / OSV) on `heliosApp` apps touched by decomp lane.                                       | 5      |
| **8**  | **Secrets scan** (gitleaks or similar) on branch before merge.                                                             | 6      |
| **9**  | **SAST** / linter on new/edited TS: no new suppressions without justification.                                             | 7      |
| **10** | Review **credential-store** event payloads for **PII** in logs (bus topics unchanged).                                     | 8      |
| **11** | Update **session overview** when wave 07–10 items complete (or strike stale bullets).                                      | 9      |
| **12** | **Link** `07`–`10` from a single `README` in the session folder if one is added later (optional).                          | 10     |
| **13** | **Onboarding** one-pager: “where worktrees live” + `04_QUEUE_CADENCE.md` pointer.                                          | 11     |
| **14** | **Troubleshooting**: ENOSPC + `.tmp` + Bun cache (short subsection) in repo docs if missing.                               | 12     |
| **15** | **Stacked PRs**: if decomp depends on another branch, document dependency order in PR body.                                | 13     |
| **16** | **Rebase** feature branch on target before final review; no force-push to shared branches without policy.                  | 14     |
| **17** | **Resolve all review threads** before merge (org protocol).                                                                | 15     |
| **18** | **Squash vs merge** strategy per repo rules; state in PR.                                                                  | 16     |
| **19** | **Oldest-first** finalization: run `worktree_governance.sh oldest-first` when ready to merge lanes.                        | 17     |
| **20** | Remove **empty** or **broken** worktree entries after successful prune.                                                    | 18     |
| **21** | **Symlink** policy: document `*-wtrees` vs `repos/worktrees/...` migration path.                                           | 19     |
| **22** | **Legacy** `PROJECT-wtrees`: track remaining count; reduce one folder per sprint.                                          | 20     |
| **23** | **File size**: re-scan `wc -l` hotspots >350 in `apps/runtime` after merges; plan next split.                              | 21     |
| **24** | **TODO/FIXME** in touched files: zero or ticketed.                                                                         | 22     |
| **25** | **Metrics/logging**: if new bus events, confirm log levels don’t leak secrets.                                             | 23     |
| **26** | **Post-merge** smoke: one manual path (e.g. open app, run CLI) if product requires it.                                     | 24     |

**Roles (Wave D):** QA/CI → 3–6; AppSec → 7–10; Tech writer / onboarding → 11–14; EM or release captain → 15–18; Platform → 19–22; Tech lead → 23–26.

---

## Wave E — Post-merge ops, compliance, perf, testing, handoff, closure (24)

| #      | Item                                                                                                                                       | `11` § |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------ | ------ |
| **27** | **Tag** or release note after merge if repo uses semver tags for apps.                                                                     | 1      |
| **28** | **Monitor** first production or staging deploy after merge (error rate, bus events).                                                       | 2      |
| **29** | **Rollback plan** documented: which commit to revert if regression.                                                                        | 3      |
| **30** | **On-call / owner** for runtime secrets/PTY for one week after release.                                                                    | 4      |
| **31** | **LICENSE** headers on new files if project requires.                                                                                      | 5      |
| **32** | **Third-party** notices: Bun/Node deps unchanged or updated in lockfile review.                                                            | 6      |
| **33** | **Export control** / cryptography note if encryption module shipped (verify no new restrictions).                                          | 7      |
| **34** | **Data retention**: audit sink / temp dirs—no long-lived secrets on disk.                                                                  | 8      |
| **35** | **Latency budget** for redaction path unchanged or improved (see `redaction_latency` tests).                                               | 9      |
| **36** | **PTY** hot paths: no new sync I/O in tight loops without review.                                                                          | 10     |
| **37** | **Bundle size** or startup if runtime entrypoints changed—spot-check.                                                                      | 11     |
| **38** | **Resource limits** (memory, FDs) on long-running PTY sessions—sanity check.                                                               | 12     |
| **39** | **Integration** vs **unit** ratio: new code has tests at correct layer.                                                                    | 13     |
| **40** | **Regression** test for any bug fixed during decomp (if applicable).                                                                       | 14     |
| **41** | **E2E** or smoke path in CI if project requires for runtime changes.                                                                       | 15     |
| **42** | **Test data** hygiene: no real keys in fixtures.                                                                                           | 16     |
| **43** | **Handoff** note for next agent: pointer to `07`–`11` + current branch.                                                                    | 17     |
| **44** | If **helios** changes affect **thegent** or **helios-cli**, open linked issue or PR stub.                                                  | 18     |
| **45** | **Phenotype** shared modules: extraction opportunity → log per reuse protocol (issue, not code in this wave).                              | 19     |
| **46** | **Stale worktrees** list: regenerate from `git worktree list` after major merges.                                                          | 20     |
| **47** | Mark **completed** items in `07`–`10` (strike or move to `docs/archive/` per org policy).                                                  | 21     |
| **48** | **Archive** or delete obsolete session duplicates if any were created by mistake.                                                          | 22     |
| **49** | **Retrospective** one paragraph: what worked, what blocked (optional session note).                                                        | 23     |
| **50** | **Next wave F** placeholder: only add `12_NEXT_WAVE_F.md` work when E is mostly done or scope shifts (see item 24 in `11_NEXT_WAVE_E.md`). | 24     |

**Roles (Wave E):** SRE → 27–30; Legal/compliance → 31–34 as needed; Perf → 35–38; QA → 39–42; Program / cross-repo → 43–46; Self / SM → 47–50.

---

## Related

- `20_NEXT_50_EXECUTION.md` — burn-down status for items **1–50**.
- `10_NEXT_WAVE_D.md` — full prose for Wave D.
- `11_NEXT_WAVE_E.md` — full prose for Wave E.
- `ACTIVE_BACKLOG.md` — wave file index and session log.
