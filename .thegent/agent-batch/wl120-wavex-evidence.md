# WL-120/WL-136 Wave-X Evidence Refresh

Date: 2026-02-21
Lane: acceptance/evidence
Scope: recompute LOC evidence artifacts and trend snapshots for WL-120/WL-136 (docs artifacts only)

## What Was Refreshed

- `docs/reports/artifacts/wl120-monolith-baseline-2026-02-21.json`
- `docs/reports/artifacts/wl120-monolith-baseline-2026-02-21.txt`
- `docs/reports/artifacts/wl120-wl136-loc-trend-2026-02-21.json`
- `docs/reports/artifacts/wl120-wl136-loc-trend-2026-02-21.md`

## Recompute Method

1. Used commit snapshots only for trend evidence to avoid dirty-worktree contamination:
   - `git rev-list -1 --before="2026-02-19 23:59:59" HEAD -- src/thegent`
   - `git rev-list -1 --before="2026-02-20 23:59:59" HEAD -- src/thegent`
   - `git rev-list -1 --before="2026-02-21 23:59:59" HEAD -- src/thegent`
2. Recounted Python LOC from commit trees (`non-blank`, `non-comment`).
3. Recomputed monolith baselines for WL-124/125/126 from `HEAD` commit content (not uncommitted files).

## Recomputed Evidence

### WL-120 Monolith Baselines (HEAD commit)

- `src/thegent/cli/commands/cli.py`: `7861` lines
- `src/thegent/cli/commands/impl.py`: `6656` lines
- `src/thegent/mcp/server.py`: `3944` lines

### WL-120/WL-136 Trend Snapshots (git day-end)

- 2026-02-19 (`8a0f7e9e1f7d...`): total `122545`, core-boundary `1267`
- 2026-02-20 (`ab9cabd1840d...`): total `117587`, core-boundary `1464`
- 2026-02-21 (`ab9cabd1840d...`): total `117587`, core-boundary `1464`

## Acceptance Decision Snapshot

- WL-120 3-day strict decline: **FAIL** (`122545 -> 117587 -> 117587`)
- WL-136 core-boundary strict decline: **FAIL** (`1267 -> 1464 -> 1464`)

## Notes

- This run intentionally refreshed docs evidence artifacts only.
- Boundary test/audit commands were not re-executed in this docs-only refresh; existing verification evidence remains in prior lane reports.
