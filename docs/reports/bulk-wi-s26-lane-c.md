### [WL-6840]

**Title:** Replace alias-probe blanket suppression with observable shell doctor diagnostics
**Source:** [thegent/src/thegent/shell_cli.py:178]
**Acceptance checklist:**

- [ ] Replace broad alias-probe exception swallowing with typed timeout/process-failure handling.
- [ ] Emit non-fatal doctor findings that include failure reason and remediation guidance.
- [ ] Add tests for successful probe, timeout, and execution-failure branches.
      **Notes:** Silent alias-probe failures can produce false healthy shell diagnostics.

### [WL-6841]

**Title:** Distinguish git-log command failures from true empty commit windows in summaries
**Source:** [thegent/src/thegent/summary.py:64]
**Acceptance checklist:**

- [ ] Replace catch-all failure fallback in git commit collection with structured subprocess error classification.
- [ ] Preserve explicit no-commit semantics separate from command execution failure.
- [ ] Add tests for non-repository paths, empty history, and failing git invocations.
      **Notes:** Returning empty results for all failures hides operational issues in activity summaries.

### [WL-6842]

**Title:** Surface log ingestion read failures instead of silently dropping summary records
**Source:** [thegent/src/thegent/summary.py:93]
**Acceptance checklist:**

- [ ] Replace silent read exception swallowing with bounded diagnostics keyed by log path.
- [ ] Continue partial ingestion while exposing skipped/corrupt file counts.
- [ ] Add tests for mixed valid and unreadable `.jsonl` files.
      **Notes:** Hidden ingestion failures reduce confidence in generated work summaries.

### [WL-6843]

**Title:** Preserve native discovery fallback failure context instead of collapsing to empty results
**Source:** [thegent/src/thegent/native/discovery_native.py:59]
**Acceptance checklist:**

- [ ] Capture fallback discovery command failures with structured metadata (exit code, stderr, timeout).
- [ ] Distinguish no sessions found from discovery failure in returned results.
- [ ] Add tests for successful parse, missing dependency, and execution-error paths.
      **Notes:** Empty-list fallthrough on failure obscures runtime discovery issues.

### [WL-6844]

**Title:** Emit diagnostics when `sendfile` path degrades to copy fallback
**Source:** [thegent/src/thegent/infra/fast_file_ops.py:63]
**Acceptance checklist:**

- [ ] Record fallback reason when `sendfile` fails.
- [ ] Preserve correctness and metadata behavior across fallback.
- [ ] Add tests that force `sendfile` failure and verify diagnostics plus successful copy.
      **Notes:** Silent fallback behavior can hide performance regressions under load.

### [WL-6845]

**Title:** Replace startup reachability stub with deterministic endpoint probes
**Source:** [thegent/src/thegent/integrations/startup_validation.py:46]
**Acceptance checklist:**

- [ ] Implement real endpoint checks with explicit timeout and connection-failure handling.
- [ ] Return structured reachability outcomes consumed by startup validation reporting.
- [ ] Add tests for reachable, unreachable, and timeout scenarios.
      **Notes:** Stubbed reachability logic can over-report healthy startup state.

### [WL-6846]

**Title:** Implement real GitHub Project item upsert flow instead of mock sync responses
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:203]
**Acceptance checklist:**

- [ ] Replace placeholder write responses with actual project item create/update behavior.
- [ ] Validate required outbound field mappings before write attempts.
- [ ] Add tests for created vs updated counts and propagated API failures.
      **Notes:** Mock success paths hide whether synchronization actually occurred.

### [WL-6847]

**Title:** Replace MCP gateway stub execution with transport-backed registered tool calls
**Source:** [thegent/src/thegent/mcp/gateway.py:98]
**Acceptance checklist:**

- [ ] Route tool execution through configured server transport instead of synthetic stub payloads.
- [ ] Preserve explicit error contracts for unknown tools, transport failures, and execution exceptions.
- [ ] Add tests for successful execution and representative failure paths.
      **Notes:** Stub executors undermine confidence in end-to-end MCP integration health.

### [WL-6848]

**Title:** Replace dispatcher placeholder task execution with runner-backed invocation
**Source:** [thegent/src/thegent/orchestration/dispatcher.py:385]
**Acceptance checklist:**

- [ ] Route `_execute_task` through real runner resolution and invocation.
- [ ] Enforce HITL approval gates as deterministic execution preconditions.
- [ ] Add tests for success, runner failure propagation, and approval-required blocking.
      **Notes:** Placeholder success behavior can incorrectly mark blocked tasks as complete.

### [WL-6849]

**Title:** Replace hash-randomized SID mapping with deterministic WSL UID derivation
**Source:** [thegent/src/thegent/infra/wsl_interop.py:119]
**Acceptance checklist:**

- [ ] Replace Python `hash()`-based SID mapping with a stable deterministic digest-based strategy.
- [ ] Define collision handling semantics for SID-to-UID assignments.
- [ ] Add reproducibility tests ensuring stable mappings across interpreter restarts.
      **Notes:** Hash randomization can produce nondeterministic identities across process boundaries.
