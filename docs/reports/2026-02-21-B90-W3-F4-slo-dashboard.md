# B90-W3-F4: SLO Dashboard — Wave-3 Snapshot

Date: 2026-02-21
Agent: agent-f
Trace: WL-135 B90-W3-F4

## SLO Dashboard

**Generated:** 2026-02-21
**Wave:** B90 Wave-3 (Hardening)
**Collector:** `scripts/collect_loc_metrics.py`

## LOC Metrics (Fresh Run)

Collected via `uv run python scripts/collect_loc_metrics.py`:

| Metric                          | Value   |
| ------------------------------- | ------- |
| Total LOC                       | 167,814 |
| Total files                     | 1,101   |
| Oversized functions (>40 lines) | 839     |

### Top 5 Largest Files

| Rank | File                               | LOC   |
| ---- | ---------------------------------- | ----- |
| 1    | `src/thegent/cli/commands/cli.py`  | 5,665 |
| 2    | `src/thegent/cli/commands/impl.py` | 5,367 |
| 3    | `src/thegent/mcp/server.py`        | 3,179 |
| 4    | `src/thegent/execution.py`         | 2,048 |
| 5    | `src/thegent/doctor.py`            | 1,692 |

## SLO Trend

**Status:** BASELINE established. No historical JSONL trend data is yet available.

`slo-metrics.jsonl` is not yet populated by CI. Trend analysis requires N ≥ 3 CI runs to produce a meaningful slope. Wave-4 CI integration will begin populating the trend file.

## Key SLO Thresholds

| SLO Name           | Green (pass) | Yellow (warn) | Red (fail) | Current               | Status  |
| ------------------ | ------------ | ------------- | ---------- | --------------------- | ------- |
| `file_loc`         | ≤ 1,200 LOC  | 1,200–1,800   | ≥ 1,800    | 5,665 (cli.py)        | RED     |
| `function_loc_p95` | ≤ 80 lines   | 80–120        | ≥ 120      | 839 oversized         | RED     |
| `impl_importers`   | ≤ 20         | 20–40         | ≥ 40       | TBD (not yet counted) | UNKNOWN |

## Current cli.py Status

- **Logical LOC (collector):** 5,665
- **Raw lines (wc -l):** 6,881
- **SLO threshold:** ≤ 1,800 LOC (red boundary)
- **Status:** RED — 3,865 LOC above the red ceiling
- **Extraction completed:** cli_dag.py (621 lines), cli_tooling.py (257 lines) — ~878 lines extracted
- **Estimated pre-extraction baseline:** ~7,759 lines — extractions have reduced it by ~11%

## Recommended Actions

1. **[CRITICAL]** Continue cli.py extractions: cli_session, cli_infra, cli_plan, cli_run, cli_team modules needed to approach the 1,800 LOC red threshold.
2. **[HIGH]** Wire `slo:check` into CI quality gate pipeline so SLO violations block merges automatically.
3. **[MEDIUM]** Address impl.py (5,367 LOC) — also well above the red threshold.
4. **[MEDIUM]** Reduce oversized functions count (839 functions > 40 lines) — target below 500 by Wave-5.
5. **[LOW]** Begin populating `slo-metrics.jsonl` via CI to enable trend analysis in Wave-4.

## Baseline Record

This report establishes the Wave-3 SLO baseline snapshot. Future CI runs will compare against this baseline to detect regressions or improvements in the LOC profile.
