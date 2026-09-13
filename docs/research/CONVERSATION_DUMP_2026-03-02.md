# Conversation Dump — 2026-03-02

## Issues Addressed

- User requested continuation of prior repo modularization lane and implementation of phase-1 tooling de-duplication across sibling repos.
- Needed deterministic synchronization of duplicated tooling artifacts identified by prior sibling-module audit.
- Needed final verification and a commit-ready state in `thegent`.

## Fixes Applied

- Reviewed generated phase-1 artifacts in `docs/reports/reusable-tooling-audit/`:
  - `phase1_minimal_tooling_split.json`
  - `phase1_tooling_split_plan.json`
  - `run_phase1_minimal_tooling_split.sh`
  - `run_phase1_tooling_split.sh`
- Executed minimal phase-1 sync with `APPLY=1`:
  - Applied replication for 8 low-risk modules across target repos.
  - Updated `.github/workflows/alert-sync-issues.yml`, `.github/workflows/coderabbit-rate-limit-retry.yml`, `.github/workflows/required-check-names-guard.yml`,
    and Helios family scripts:
    `scripts/readme_toc.py`, `scripts/mock_responses_websocket_server.py`,
    `scripts/check-module-bazel-lock.sh`, `scripts/asciicheck.py`, `.github/scripts/install-musl-build-tools.sh`.
- In `thegent`, this normalized `.github/workflows/coderabbit-rate-limit-retry.yml` to the phase-1 source body.

## Research Findings

- Child-agent review confirmed `phase1_minimal_tooling_split.json` is a lower-risk subset of `phase1_tooling_split.json`:
  - 8 modules total, each with `hash_variants: 1`.
  - Excluded repositories: `4sgm`, `civ`, `parpour`, `trace`.
  - Additional 12 modules in `phase1_tooling_split.json` are higher-risk and deferred.
- Child-agent review of phench/workflow context confirmed multi-repo timeline/ref execution is already largely implemented in `thegent`; gap remains for folder-level persisted workflow manifest semantics if needed.

## Fixes Validation

- Verified source-target hash parity for all minimal phase-1 targets after apply (`bad_count 0`).
- `python -m py_compile` passed on all copied `.py` tooling files (12 files).
- `bash -n` passed on all copied `.sh` tooling files (8 files).
- Targeted CLI tests executed:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/commands/test_apps_main.py -q`
  - result: `24 passed, 18 skipped`.
- Lint pass:
  - `ruff check src/thegent/config/runtime_config.py src/thegent/config/settings.py src/thegent/phench/paths.py`.

## Plans

- Decide whether to apply full `phase1_tooling_split.json` (20 modules) in a controlled second wave.
- For user-requested Phenotype/projects runtime improvements, implement persistent folder workflow manifest in next lane.

## Open Questions

- Should the minimal artifacts sync be expanded immediately to the broader phase-1 set, or paused for CI observation first?
- For `Phenotype/projects` folder-level workflows, should execution provenance (`branch/tag + SHA`) be persisted in runtime state and exposed in status output in this next tranche?
