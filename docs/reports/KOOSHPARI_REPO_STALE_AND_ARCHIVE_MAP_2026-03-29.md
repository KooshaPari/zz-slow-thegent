# KooshaPari GitHub: staleness and archival map (2026-03-29)

Source export: `docs/reports/data/KOOSHPARI_GITHUB_REPOS_2026-03-29.tsv`  
Derived buckets: `docs/reports/data/KOOSHPARI_REPOS_STALE_BUCKETS.tsv`  
**Last refresh:** 2026-03-29 UTC (~06:27Z re-export; `pushedAt` timestamps updated). Bucket counts unchanged (180 / 12 / 1 / 56). **Prior delta:** `vibe-kanban` is **not** `isArchived` on GitHub vs older exports.

## Summary counts (non-archived repos only)

| Bucket          | Meaning                          | Count |
| --------------- | -------------------------------- | ----: |
| `active_90d`    | Pushed within ~90 days of export |   180 |
| `stale_90d_1y`  | Between ~90 days and 1 year      |    12 |
| `stale_1y_2y`   | Between 1 and 2 years            |     1 |
| `stale_over_2y` | Older than ~2 years              |     0 |

**GitHub-archived** repos in export: **56** (listed under `archived_github` in the buckets TSV).

## Candidates for triage (no automatic archival)

### Stale over 2 years (0)

None in the non-archived set (former coldest repos were archived in batch 1).

### Stale 1y–2y (1)

- `delete-o-matic-for-linkedin` (2025-01-20)

### Stale 90d–1y (12) — themes

- **Agslag / NetWeave:** `agslag`, `agslag-docs`, `agslag-new`, `agslag-tmp`, `agslagtmp-2`, `v0-agslag-project`, `NetWeave`
- **Other:** `aizen`, `KodeVibe`, `localbase`, `mcp-language-server`, `model-conductor-hub`

**Recommendation:** For each `stale_*` repo, choose one: **archive on GitHub**, **delete** (if duplicate), or **revive** with an AgilePlus feature.

## Already archived on GitHub (56)

Includes historical archives and the 2026-03-29 batch runs (23 + 5 repos), minus any later **unarchive** actions. Full list: `KOOSHPARI_REPOS_STALE_BUCKETS.tsv` filter `archived_github`.

## Decision log (execution)

- **Coldest 9 repos (seed):** `docs/reports/data/KOOSHPARI_STALE_TRIAGE_DECISIONS_2026-03-29.tsv`
- **Full stale set (historical, pre-batch):** `docs/reports/data/KOOSHPARI_STALE_TRIAGE_FULL_2026-03-29.tsv`
- **Remaining triage rows:** `docs/reports/data/KOOSHPARI_STALE_TRIAGE_REMAINING_2026-03-29.tsv` (archive_github actions for batch 2 marked executed)

## Regenerate data

```bash
gh repo list KooshaPari --limit 1000 --json name,isArchived,pushedAt,isPrivate \
  | jaq -r 'sort_by(.pushedAt) | reverse | .[] | "\(.pushedAt)\t\(.name)\tarchived=\(.isArchived)\tprivate=\(.isPrivate)"' \
  > docs/reports/data/KOOSHPARI_GITHUB_REPOS_YYYY-MM-DD.tsv
```

Bucket generation: parse TSV, classify by `isArchived` and age vs UTC “now” (90d / 365d / 730d thresholds). A short Python snippet lives in git history for this refresh; consider promoting to `scripts/reports/` when stabilized.
