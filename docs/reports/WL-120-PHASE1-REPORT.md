# WL-120 Phase 1 Report: Python LOC Reduction - impl.py Observability Extraction

**Date:** 2026-02-20
**Status:** Phase 1 complete
**Author:** Agent (type-fix-wave3 team)

## Summary

Extracted the observability/health/escalation/governance/review/compliance block from `src/thegent/cli/commands/impl.py` into a new module `src/thegent/cli/commands/observability_impl.py`.

## Metrics

| File                           | Before      | After       | Delta                 |
| ------------------------------ | ----------- | ----------- | --------------------- |
| `impl.py`                      | 7,425 lines | 6,375 lines | -1,050 lines (-14.1%) |
| `observability_impl.py`        | N/A (new)   | 1,125 lines | +1,125 lines          |
| Net LOC reduction in `impl.py` | --          | --          | **-1,050 lines**      |

## What Was Extracted

The following functional domains were moved to `observability_impl.py`:

1. **Constants**: `HEALTH_PAYLOAD_SCHEMA_VERSION`, `HEALTH_PAYLOAD_TYPES`, `OBSERVE_SUMMARY_SCHEMA_VERSION`, `OBSERVE_SUMMARY_PAYLOAD_TYPES`, `HEALTH_POLICY_PROFILES`
2. **Observe summary helpers**: `_hash_observe_summary_payload`, `_build_observe_summary_trend_scope`, `_hash_observe_summary_trend_scope`, `_parse_observe_summary_timestamp`, `_parse_observe_summary_env_float`, `_parse_observe_summary_env_int`, `_observe_summary_freshness_bucket`, `_load_observe_summary_snapshots`, `_classify_observe_summary_trend_health`, `_append_observe_summary_snapshot`
3. **Health helpers**: `_hash_health_payload`, `_resolve_health_policy`, `_health_snapshot_log_path`, `_health_snapshot_max_lines`, `_compact_health_snapshot_log`, `_health_scope_key`, `_coerce_issue_types`, `_load_previous_health_snapshot`, `_append_health_snapshot`
4. **Server meta**: `get_server_meta_impl`
5. **Calibration**: `update_calibration_impl`, `_extract_agent_from_line`, `_process_run_line`
6. **Sweep/observe**: `sweep_impl`, `observe_summary_impl`
7. **Escalation impls**: `escalate_add_impl`, `escalate_approve_impl`, `escalate_list_impl`, `escalate_resolve_impl`
8. **Governance impls**: `govern_approve_impl`, `govern_reject_impl`, `govern_list_pending_impl`, `govern_vet_impl`
9. **Review**: `review_impl`, `_REVIEW_ALLOWED_TOOLS`, `_REVIEW_SCHEMA_PREAMBLE`
10. **Data protection/compliance**: `get_data_protection_status_impl`, `sitback_dashboard_impl`, `get_compliance_report_impl`

## Backward Compatibility

All extracted symbols are re-exported from `impl.py` via a single import block. All existing callers (which use lazy `from thegent.cli.commands.impl import X` patterns) continue to work without modification.

## Cross-module Dependencies

The new module has two lazy imports back to `impl.py`:

- `review_impl` imports `run_impl` (lazy, inside function body)
- `sitback_dashboard_impl` imports `ps_impl` (lazy, inside function body)

These are safe because they are lazy imports (inside function bodies), not top-level circular imports.

## Validation

- Both files pass Python AST parsing (`ast.parse`)
- Re-export block verified complete (all 42 symbols)
- No callers need modification

## Remaining Hotspots

| File        | Current LOC | Target |
| ----------- | ----------- | ------ |
| `impl.py`   | 6,375       | <=500  |
| `cli.py`    | 6,994       | <=500  |
| `server.py` | 3,929       | <=500  |

## Next Steps

1. Continue `impl.py` decomposition: extract session management (~800 lines), DAG functions (~400 lines), work stream functions (~600 lines)
2. Continue `cli.py` decomposition: further domain splits
3. Continue `server.py` decomposition: transport/auth/tools/router boundaries
