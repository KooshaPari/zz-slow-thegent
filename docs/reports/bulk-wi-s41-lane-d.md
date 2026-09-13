### [WL-7600]

**Title:** Persist plan status updates to PLAN_STATUS.md instead of keeping mutations in-memory only
**Source:** [thegent/src/thegent/integration/plan_system.py:229]
**Acceptance checklist:**

- [ ] Implement `_save_plan_status` to write deterministic markdown table updates back to `PLAN_STATUS.md`.
- [ ] Preserve non-status content in the file while updating task rows.
- [ ] Add tests that verify status changes survive a fresh `PlanSystemIntegration` reload.
      **Notes:** The current method is documented as simplified and does not persist updates, so status edits are lost across process boundaries.

### [WL-7601]

**Title:** Remove silent fallback URL behavior when shared MCP bootstrap returns an error string
**Source:** [thegent/src/thegent/shared_mcp_manager.py:166]
**Acceptance checklist:**

- [ ] Change `get_shared_mcp_url` to return a typed failure or raise when `ensure_shared_mcp_server` reports an error.
- [ ] Keep successful URL returns unchanged for healthy startup paths.
- [ ] Add tests for startup failure, invalid lockfile paths, and healthy server resolution.
      **Notes:** Returning a default localhost URL on bootstrap error can route callers to a non-existent endpoint and hide startup failures.

### [WL-7602]

**Title:** Emit worker stdout lines through structured logging instead of dropping non-heartbeat output
**Source:** [thegent/src/thegent/infra/multi_runtime_bridge.py:140]
**Acceptance checklist:**

- [ ] Forward non-heartbeat worker stdout lines to logger with runtime/task context.
- [ ] Preserve heartbeat parsing and timestamp refresh behavior.
- [ ] Add tests validating that representative worker log lines are surfaced and heartbeats still update state.
      **Notes:** The current `pass` branch discards useful runtime diagnostics and complicates incident triage.

### [WL-7603]

**Title:** Capture and surface worker stderr payloads from runtime bridge log forwarding
**Source:** [thegent/src/thegent/infra/multi_runtime_bridge.py:144]
**Acceptance checklist:**

- [ ] Parse stderr bytes safely and log bounded output with runtime identifiers.
- [ ] Attach stderr snippets to worker termination/error paths for debugging.
- [ ] Add tests for worker failures that write stderr and verify it is observable.
      **Notes:** Ignoring stderr drops the highest-signal failure context for runtime startup and execution errors.

### [WL-7604]

**Title:** Replace implicit runtime failover with explicit runtime selection and failure signaling
**Source:** [thegent/src/thegent/infra/multi_runtime_bridge.py:154]
**Acceptance checklist:**

- [ ] Remove automatic fallback to alternate runtime in `dispatch`.
- [ ] Return a clear error when requested runtime startup fails, including actionable diagnostics.
- [ ] Add tests that assert no cross-runtime mutation of `task.runtime` on startup failure.
      **Notes:** Silent failover can change execution semantics and mask environment-specific regressions.

### [WL-7605]

**Title:** Report malformed run registry rows with counters instead of silently skipping JSON parse failures
**Source:** [thegent/src/thegent/ux/kpis.py:31]
**Acceptance checklist:**

- [ ] Track malformed JSONL row count during `_iter_run_registry_rows` parsing.
- [ ] Emit a warning with file path and malformed-row count when bad rows are present.
- [ ] Add tests with mixed valid/invalid rows to confirm metrics still compute and warnings are emitted.
      **Notes:** Current silent drops make data-quality problems invisible while KPI numbers degrade.

### [WL-7606]

**Title:** Surface finance KPI dependency failures rather than defaulting to zero cost silently
**Source:** [thegent/src/thegent/ux/kpis.py:99]
**Acceptance checklist:**

- [ ] Replace broad exception swallowing around `CostAggregator` with typed error handling and diagnostics.
- [ ] Include an explicit `finance_status` field (for example `ok`/`error`) in metrics output.
- [ ] Add tests for missing/failed cost backends and successful finance metric reads.
      **Notes:** Defaulting silently to `0.0` can misrepresent spend and break operational decision-making.

### [WL-7607]

**Title:** Surface fatigue KPI provider failures rather than returning zero fatigue silently
**Source:** [thegent/src/thegent/ux/kpis.py:108]
**Acceptance checklist:**

- [ ] Replace broad exception swallowing around `AlertFatigueController` calls with typed diagnostics.
- [ ] Add `fatigue_status` metadata to output so downstream consumers can distinguish real values from failure states.
- [ ] Add tests for unavailable fatigue provider and normal fatigue computation paths.
      **Notes:** A silent zero fatigue value can mask alert overload conditions and reduce operator trust in KPI output.

### [WL-7608]

**Title:** Promote SLO emission from local stub payload builder to pluggable sink-backed metric delivery
**Source:** [thegent/src/thegent/metrics/collector.py:53]
**Acceptance checklist:**

- [ ] Replace `emit_slo_stub` with a sink interface that supports no-op, log, and HTTP/export backends.
- [ ] Preserve current payload shape compatibility for existing callers.
- [ ] Add tests covering sink selection, transport failures, and payload integrity.
      **Notes:** The current stub only formats data and logs locally, limiting operational observability integration.

### [WL-7609]

**Title:** Return explicit partial-size status when directory size traversal encounters permission/read errors
**Source:** [thegent/src/thegent/infra/fast_file_ops.py:205]
**Acceptance checklist:**

- [ ] Replace silent suppression in `get_size` with a result that distinguishes full vs partial traversal.
- [ ] Include error counts or paths skipped so callers can make informed decisions.
- [ ] Add tests for permission-denied entries, disappearing files during walk, and fully successful traversal.
      **Notes:** Silent `pass` on traversal failures returns plausible but incomplete size totals without any signal.
