### [WL-6930]

**Title:** Replace alias-probe blanket exception swallowing with typed degraded diagnostics
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:180]
**Acceptance Checklist:**

- [ ] Replace broad alias-probe exception swallowing with timeout and subprocess-error classification.
- [ ] Emit non-fatal doctor output with explicit failure reason and suggested remediation.
- [ ] Add tests for successful probe, timeout path, and execution-failure path.
      **Notes:** Silent alias-probe failures can produce false healthy shell diagnostics.

### [WL-6931]

**Title:** Distinguish git log execution failures from true empty commit windows
**Source Path+Line:** [thegent/src/thegent/summary.py:64]
**Acceptance Checklist:**

- [ ] Replace catch-all git-log failure fallback with structured subprocess error handling.
- [ ] Preserve explicit zero-commit semantics separately from command-execution failures.
- [ ] Add tests for non-repository paths, empty ranges, and failing git invocations.
      **Notes:** Returning empty commit lists for all failures hides operational issues in summaries.

### [WL-6932]

**Title:** Surface malformed summary JSON entries instead of silently dropping parse failures
**Source Path+Line:** [thegent/src/thegent/summary.py:84]
**Acceptance Checklist:**

- [ ] Replace parse exception swallowing with bounded malformed-entry diagnostics.
- [ ] Continue line-by-line ingestion while exposing skipped malformed record counts.
- [ ] Add tests for mixed valid and malformed `.jsonl` records.
      **Notes:** Hidden parse failures reduce trust in generated activity summaries.

### [WL-6933]

**Title:** Preserve tmux fallback discovery failures as degraded-state diagnostics
**Source Path+Line:** [thegent/src/thegent/native/discovery_native.py:61]
**Acceptance Checklist:**

- [ ] Capture fallback discovery command failures with structured metadata.
- [ ] Differentiate discovery failure from legitimate empty session results.
- [ ] Add tests for successful parse, missing dependency, and command failure paths.
      **Notes:** Empty-list fallthrough on failure obscures runtime discovery health.

### [WL-6934]

**Title:** Emit observable diagnostics when optimized sendfile copy falls back
**Source Path+Line:** [thegent/src/thegent/infra/fast_file_ops.py:63]
**Acceptance Checklist:**

- [ ] Record fallback reason when optimized `sendfile` transfer fails.
- [ ] Preserve correctness and metadata behavior across fallback copy paths.
- [ ] Add tests that force `sendfile` failure and assert diagnostics plus successful copy.
      **Notes:** Silent fallback behavior can hide performance regressions under load.

### [WL-6935]

**Title:** Replace startup endpoint reachability stub with deterministic network probes
**Source Path+Line:** [thegent/src/thegent/integrations/startup_validation.py:46]
**Acceptance Checklist:**

- [ ] Implement real endpoint checks with explicit timeout and connection-failure handling.
- [ ] Return structured reachability outcomes consumed by startup validation reporting.
- [ ] Add tests for reachable, unreachable, and timeout scenarios.
      **Notes:** Stubbed reachability logic can over-report healthy startup state.

### [WL-6936]

**Title:** Replace GitHub Project sync mock write response with real item upsert flow
**Source Path+Line:** [thegent/src/thegent/integrations/gh_project_sync.py:202]
**Acceptance Checklist:**

- [ ] Replace placeholder write response with real project item create and update behavior.
- [ ] Validate required outbound field mappings before write attempts.
- [ ] Add tests for created-versus-updated counts and API failure propagation.
      **Notes:** Mock success paths hide whether synchronization actually occurred.

### [WL-6937]

**Title:** Replace MCP gateway stub executor with transport-backed tool execution
**Source Path+Line:** [thegent/src/thegent/mcp/gateway.py:98]
**Acceptance Checklist:**

- [ ] Route tool execution through configured server transport rather than synthetic payloads.
- [ ] Preserve explicit error contracts for unknown tools, transport failures, and execution exceptions.
- [ ] Add tests for successful execution and representative failure branches.
      **Notes:** Stub executor behavior undermines confidence in end-to-end MCP integration health.

### [WL-6938]

**Title:** Replace dispatcher placeholder task execution with runner-backed invocation
**Source Path+Line:** [thegent/src/thegent/orchestration/dispatcher.py:385]
**Acceptance Checklist:**

- [ ] Route `_execute_task` through real runner resolution and invocation.
- [ ] Enforce HITL approval gates as deterministic execution preconditions.
- [ ] Add tests for success, runner failure propagation, and approval-required blocking.
      **Notes:** Placeholder execution can incorrectly mark blocked tasks as completed.

### [WL-6939]

**Title:** Replace hash-randomized SID mapping with deterministic UID derivation
**Source Path+Line:** [thegent/src/thegent/infra/wsl_interop.py:119]
**Acceptance Checklist:**

- [ ] Replace Python `hash()` SID mapping with stable deterministic digest-based derivation.
- [ ] Define explicit collision handling semantics for SID-to-UID assignments.
- [ ] Add reproducibility tests ensuring stable mappings across interpreter restarts.
      **Notes:** Hash randomization can produce nondeterministic identities across process boundaries.
