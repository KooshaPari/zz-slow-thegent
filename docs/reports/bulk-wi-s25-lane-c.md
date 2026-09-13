### [WL-6790]

**Title:** Classify and surface remote shell probe failures in doctor diagnostics
**Source:** [thegent/src/thegent/shell_cli.py:178]
**Acceptance checklist:**

- [ ] Replace broad exception suppression around remote shell probe execution with typed error handling.
- [ ] Emit a non-fatal doctor finding that includes actionable failure reason metadata.
- [ ] Add tests for successful probe, timeout, and process execution failure branches.
      **Notes:** Silent probe suppression can misreport shell health and delay remediation.

### [WL-6791]

**Title:** Differentiate git invocation failure from empty-history states in summary commit collection
**Source:** [thegent/src/thegent/summary.py:64]
**Acceptance checklist:**

- [ ] Replace catch-all error handling in commit lookup with explicit subprocess failure classification.
- [ ] Preserve true “no commits found” behavior separately from command execution failure.
- [ ] Add tests for non-repository paths, empty history, and failing git invocations.
      **Notes:** Conflating failures with empty results weakens audit reliability.

### [WL-6792]

**Title:** Report per-file ingestion errors during summary log loading
**Source:** [thegent/src/thegent/summary.py:94]
**Acceptance checklist:**

- [ ] Replace silent log-read exception swallowing with bounded diagnostics keyed by file path.
- [ ] Continue partial ingestion while reporting skipped and unreadable file counts.
- [ ] Add tests for mixed valid and unreadable `.jsonl` files.
      **Notes:** Hidden read failures make summary outputs appear complete when they are not.

### [WL-6793]

**Title:** Preserve tmux fallback failure context in native session discovery
**Source:** [thegent/src/thegent/native/discovery_native.py:64]
**Acceptance checklist:**

- [ ] Capture fallback command failures with structured exit code and stderr metadata.
- [ ] Distinguish “no sessions discovered” from “session discovery failed” in returned results.
- [ ] Add tests for normal parse, missing binary, and execution-error paths.
      **Notes:** Empty-list fallthrough on failure obscures runtime discovery issues.

### [WL-6794]

**Title:** Emit observable diagnostics when `sendfile` fallback copy path is activated
**Source:** [thegent/src/thegent/infra/fast_file_ops.py:65]
**Acceptance checklist:**

- [ ] Add structured diagnostics or metrics when `sendfile` fails and fallback copy is used.
- [ ] Preserve copy fallback behavior while recording failure category details.
- [ ] Add tests that force `sendfile` failure and verify both telemetry and successful copy.
      **Notes:** Silent fallback behavior can hide performance regressions under load.

### [WL-6795]

**Title:** Replace startup endpoint reachability stub with deterministic probe outcomes
**Source:** [thegent/src/thegent/integrations/startup_validation.py:46]
**Acceptance checklist:**

- [ ] Implement real endpoint checks with explicit timeout and connection failure handling.
- [ ] Return structured reachability outcomes consumed by startup validation reporting.
- [ ] Add tests for reachable, unreachable, and timeout scenarios.
      **Notes:** Placeholder reachability logic can produce false healthy startup reports.

### [WL-6796]

**Title:** Implement concrete GitHub Project upsert path instead of mock write responses
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:203]
**Acceptance checklist:**

- [ ] Replace placeholder write responses with real project item create/update behavior.
- [ ] Validate required outbound field mappings before write attempts.
- [ ] Add tests that verify created vs updated counts and propagated API failures.
      **Notes:** Mock success paths hide whether synchronization actually occurred.

### [WL-6797]

**Title:** Wire MCP gateway execution to registered transport-backed tool invocation
**Source:** [thegent/src/thegent/mcp/gateway.py:99]
**Acceptance checklist:**

- [ ] Replace synthetic execution stubs with registered server transport invocation.
- [ ] Preserve explicit error contracts for unknown tools, transport failures, and execution exceptions.
- [ ] Add tests for successful execution plus representative failure paths.
      **Notes:** Stub executors undermine confidence in end-to-end MCP integration health.

### [WL-6798]

**Title:** Replace dispatcher placeholder task execution with runner-backed invocation
**Source:** [thegent/src/thegent/orchestration/dispatcher.py:387]
**Acceptance checklist:**

- [ ] Route `_execute_task` through real runner resolution and invocation.
- [ ] Enforce HITL approval gates as deterministic execution preconditions.
- [ ] Add tests for success, runner failure propagation, and approval-required blocking.
      **Notes:** Placeholder success behavior can incorrectly mark blocked tasks as complete.

### [WL-6799]

**Title:** Remove hash-randomized SID mapping and enforce deterministic WSL UID derivation
**Source:** [thegent/src/thegent/infra/wsl_interop.py:119]
**Acceptance checklist:**

- [ ] Replace Python `hash()`-based SID mapping with a stable deterministic digest-based strategy.
- [ ] Define collision handling semantics for SID-to-UID assignments.
- [ ] Add reproducibility tests ensuring stable mappings across interpreter restarts.
      **Notes:** Hash randomization can produce nondeterministic identities across process boundaries.
