# Portfolio audit snapshot (2026-03-29)

Execution pass: locate Pheno SDK, clone canonical sources, freeze GitHub org inventory, AgilePlus child features, and decomposition hints per `docs/governance/23_ARCHITECTURAL_GOVERNANCE.md`.

## AgilePlus features

| Slug                              | Purpose                                     |
| --------------------------------- | ------------------------------------------- |
| `portfolio-audit-kooshapari-2026` | Parent portfolio program                    |
| `phenosdk-wave-a-contracts`       | SDD / ports extraction (research + planned) |
| `kooshapari-stale-repo-triage`    | Stale bucket decisions                      |
| `codeprojects-archive-manifest`   | Local archive MANIFEST                      |

Specs live under `apps/AgilePlus/kitty-specs/<slug>/` (gitignored in AgilePlus repo).

## Pheno SDK: canonical location

| Item                | Detail                                                                       |
| ------------------- | ---------------------------------------------------------------------------- |
| **GitHub (active)** | `KooshaPari/phenoSDK` — `main`, last push **2026-02-23**                     |
| **GitHub (legacy)** | `KooshaPari/pheno-sdk` — **archived** on GitHub; **`phenoSDK` is canonical** |
| **Local clone**     | `repos/worktrees/phenoSDK/main`                                              |

## Scale (phenoSDK)

- Python-first under `src/pheno/` (~420k Python LOC tokei-classified, order-of-magnitude).
- No root `go.mod` / `Cargo.toml` in snapshot — polyglot via **Phenotype libs** + contracts.

## Data files

- `docs/reports/data/KOOSHPARI_GITHUB_REPOS_2026-03-29.tsv` — org export (249 repos); refreshed **2026-03-29** ~06:27 UTC (`pushedAt` pass; bucket counts unchanged)
- `docs/reports/data/KOOSHPARI_REPOS_STALE_BUCKETS.tsv` — staleness buckets (56 `archived_github`, 13 non-archived stale; `vibe-kanban` unarchived since prior snapshot)
- `docs/reports/data/KOOSHPARI_STALE_TRIAGE_DECISIONS_2026-03-29.tsv` — **proposed** triage for coldest repos

## Related reports

- `KOOSHPARI_REPO_STALE_AND_ARCHIVE_MAP_2026-03-29.md`
- `CODEPROJECTS_ARCHIVE_HEALTH_2026-03-29.md`
- `PHENOSDK_EXTRACTION_SLICES_2026-03-29.md`
- `PHENOSDK_PORTS_INVENTORY_2026-03-29.md`
- `PHENOSDK_WAVE_A_RECON_2026-03-29.md` — subagent ports/adapters/contracts recon
- `PHENOSDK_OPENAPI_EXPORT_HOWTO_2026-03-29.md` — FastAPI extra + snapshot command
- `GH_ARCHIVE_EXECUTED_2026-03-29.md` — archive batches 1–2 + lists; `data/gh_archive_run_remaining_2026-03-29.txt`
- `ORPHANS_DEV_CROSSWALK_2026-03-29.md`
- `data/KOOSHPARI_STALE_TRIAGE_FULL_2026-03-29.tsv`
- `data/gh_archive_proposed_archive_github.sh` — batch archive (executed 2026-03-29)
- `data/gh_archive_run_2026-03-29.log` — CLI log
- `data/phenosdk_openapi_snapshot_2026-03-29.json` — committed OpenAPI

## Local manifest (outside monorepo)

`/Users/kooshapari/CodeProjects/archive/MANIFEST.md` — directory + blob inventory.

## atoms.tech

Inspiration-only; re-implement behind Phenotype contracts; no verbatim transplant.
