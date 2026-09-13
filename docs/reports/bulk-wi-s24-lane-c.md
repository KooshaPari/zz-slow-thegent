### [WL-6740]

**Title:** Report alias-probe failures in `shell doctor` instead of suppressing exception paths
**Source:** [thegent/src/thegent/shell_cli.py:178]
**Acceptance checklist:**

- [ ] Replace broad exception suppression around alias probing with typed timeout/process failure handling.
- [ ] Emit a non-fatal doctor finding that preserves probe failure reason and remediation guidance.
- [ ] Add tests for successful alias detection, timeout, and probe-execution failure branches.
      **Notes:** Silent probe failures can produce false healthy diagnostics in shell doctor output.

### [WL-6741]

**Title:** Distinguish git command failure from true empty-commit windows in summary generation
**Source:** [thegent/src/thegent/summary.py:64]
**Acceptance checklist:**

- [ ] Replace catch-all failure behavior in `get_git_commits` with structured subprocess error classification.
- [ ] Preserve explicit “no commits found” semantics distinct from command-execution failure.
- [ ] Add tests for non-git directories, empty history, and failing git invocations.
      **Notes:** Returning empty results for all failures masks operational issues during summary audits.

### [WL-6742]

**Title:** Surface per-file read failures when ingesting log files for summary parsing
**Source:** [thegent/src/thegent/summary.py:94]
**Acceptance checklist:**

- [ ] Replace silent exception swallowing in `_read_log_file` with bounded diagnostics keyed by file path.
- [ ] Continue partial ingestion while exposing skipped/corrupt file counts to callers.
- [ ] Add tests for mixed valid and unreadable `.jsonl` files.
      **Notes:** Hidden ingestion errors reduce trust in generated summaries and activity timelines.

### [WL-6743]

**Title:** Preserve fallback session discovery error context in native discovery paths
**Source:** [thegent/src/thegent/native/discovery_native.py:64]
**Acceptance checklist:**

- [ ] Capture tmux fallback command failures with structured metadata (exit code, stderr, timeout).
- [ ] Differentiate “no sessions found” from “session discovery failed” in caller-visible results.
- [ ] Add tests for successful parse, missing tmux binary, and tmux execution errors.
      **Notes:** Collapsing discovery failures into empty arrays obscures real runtime issues.

### [WL-6744]

**Title:** Add observable telemetry when Linux `sendfile` fallback copy path is triggered
**Source:** [thegent/src/thegent/infra/fast_file_ops.py:65]
**Acceptance checklist:**

- [ ] Emit structured diagnostics/metrics when `sendfile` errors and fallback copy path is used.
- [ ] Preserve functional fallback behavior while recording failure category details.
- [ ] Add tests forcing `sendfile` failure to validate telemetry and successful fallback copy.
      **Notes:** Silent fallback behavior can hide throughput regressions under production load.

### [WL-6745]

**Title:** Replace placeholder endpoint reachability logic with deterministic network probes
**Source:** [thegent/src/thegent/integrations/startup_validation.py:46]
**Acceptance checklist:**

- [ ] Implement real endpoint checks with timeout handling and explicit reachability outcomes.
- [ ] Return structured failure reasons (DNS, connection, timeout, HTTP status) used by startup validation.
- [ ] Add tests for reachable targets, unreachable targets, and timeout conditions.
      **Notes:** Stubbed reachability paths currently over-report healthy endpoint state.

### [WL-6746]

**Title:** Complete GitHub Project write-sync path by replacing mock upsert responses
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:203]
**Acceptance checklist:**

- [ ] Replace placeholder write result with actual project item create/update behavior.
- [ ] Map and validate required workstream fields before write attempts.
- [ ] Add tests validating created vs updated counts and error propagation behavior.
      **Notes:** Mock write responses hide whether outbound project synchronization actually occurred.

### [WL-6747]

**Title:** Replace MCP gateway stub executor with real registered-tool invocation flow
**Source:** [thegent/src/thegent/mcp/gateway.py:99]
**Acceptance checklist:**

- [ ] Route tool execution through configured server transport instead of synthetic stub payloads.
- [ ] Preserve stable error contracts for unknown tools, transport failures, and execution exceptions.
- [ ] Add tests for successful execution and representative failure paths.
      **Notes:** Stub execution undermines confidence in MCP integration health and tool availability.

### [WL-6748]

**Title:** Implement runner-backed dispatcher task execution instead of placeholder success path
**Source:** [thegent/src/thegent/orchestration/dispatcher.py:385]
**Acceptance checklist:**

- [ ] Replace `_execute_task` placeholder behavior with real runner invocation using resolved runner identity.
- [ ] Enforce HITL gate decisions as execution preconditions with deterministic blocking behavior.
- [ ] Add tests for successful execution, runner failure propagation, and approval-required blocking.
      **Notes:** Synthetic success outputs can incorrectly mark blocked or failed tasks as completed.

### [WL-6749]

**Title:** Replace hash-randomized SID mapping with deterministic UID derivation in WSL interop
**Source:** [thegent/src/thegent/infra/wsl_interop.py:119]
**Acceptance checklist:**

- [ ] Replace Python `hash()`-based SID mapping with a stable deterministic digest strategy.
- [ ] Define and enforce collision-handling behavior for SID-to-UID assignments.
- [ ] Add reproducibility tests verifying stable mappings across interpreter restarts.
      **Notes:** Hash randomization can produce nondeterministic UID mappings across process boundaries.
