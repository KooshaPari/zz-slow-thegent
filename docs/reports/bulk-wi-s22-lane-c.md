### [WL-6640]

**Title:** Replace endpoint reachability stub with real network probing and failure classification
**Source:** [thegent/src/thegent/integrations/startup_validation.py:46]
**Acceptance checklist:**

- [ ] Implement deterministic endpoint checks (timeout + status handling) instead of returning all-true results.
- [ ] Return structured reachability outcomes that distinguish DNS, connection, timeout, and HTTP-failure cases.
- [ ] Add tests covering reachable endpoints, unreachable endpoints, and timeout behavior.
      **Notes:** Line 46 explicitly marks reachability checks as a stub and currently reports every endpoint as reachable.

### [WL-6641]

**Title:** Implement real GitHub Project item create/update flow for outbound sync
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:203]
**Acceptance checklist:**

- [ ] Replace mock write response with real `gh project` item creation and update logic.
- [ ] Map workstream payload fields to project item fields with validation for missing values.
- [ ] Add integration-style tests that verify item create counts, update counts, and surfaced errors.
      **Notes:** Line 202 is the TODO where write sync currently short-circuits to a zero-change mock response.

### [WL-6642]

**Title:** Implement conflict-aware configuration synchronization in unified config manager
**Source:** [thegent/src/thegent/integration/unified_config.py:163]
**Acceptance checklist:**

- [ ] Add conflict detection across participating config sources using explicit precedence rules.
- [ ] Implement merge strategy application and persist reconciled values to source-of-truth files.
- [ ] Add tests for conflict detection, merge outcomes, and no-op sync behavior.
      **Notes:** Line 162 marks `sync_configs` as placeholder-only with comments describing missing merge/conflict logic.

### [WL-6643]

**Title:** Replace mock local-state collection with registry-backed sync payload construction
**Source:** [thegent/src/thegent/discovery/sync.py:69]
**Acceptance checklist:**

- [ ] Load real local state inputs (team registry, handoff records, and recent sync metadata) from project files.
- [ ] Validate payload schema and include safe defaults when optional sources are absent.
- [ ] Add tests for successful state extraction and malformed/missing input handling.
      **Notes:** Line 69 labels local-state collection as mock behavior and emits static empty lists.

### [WL-6644]

**Title:** Upgrade ZK proof verification from length checks to deterministic proof validation
**Source:** [thegent/src/thegent/verification/zkp.py:59]
**Acceptance checklist:**

- [ ] Replace response-length-only validation with deterministic challenge-response verification.
- [ ] Enforce freshness/replay constraints on proof material before accepting verification.
- [ ] Add tests for valid proofs, commitment mismatch, stale proofs, and tampered responses.
      **Notes:** Line 59 currently accepts any response with length 64, which is insufficient as a verifier.

### [WL-6645]

**Title:** Implement CLI design-token application in `apply_to_cli`
**Source:** [thegent/src/thegent/design/design_language.py:101]
**Acceptance checklist:**

- [ ] Wire design tokens into concrete Rich style/theme configuration used by CLI output.
- [ ] Support platform-specific token overrides while preserving default token behavior.
- [ ] Add tests that assert applied styles and deterministic fallback when tokens are missing.
      **Notes:** Line 101 states the CLI styling path is placeholder-only and does not currently apply tokens.

### [WL-6646]

**Title:** Replace KPI placeholder constants with telemetry-derived calculations
**Source:** [thegent/src/thegent/execution.py:1047]
**Acceptance checklist:**

- [ ] Compute KPI fields from run registry and contract telemetry inputs instead of hardcoded constants.
- [ ] Define fallback semantics for sparse/empty datasets and include explicit confidence or data-availability markers.
- [ ] Add tests validating KPI math against fixture datasets and edge cases.
      **Notes:** Line 1047 begins a block of placeholder KPI values that can drift from real runtime behavior.

### [WL-6647]

**Title:** Implement remote sync push transport instead of dry-run style stub reporting
**Source:** [thegent/src/thegent/commands/sync.py:654]
**Acceptance checklist:**

- [ ] Replace stub-only push path with actual remote upload/transfer operations.
- [ ] Persist per-file success/failure details in `OperationResult.details` and include retry-safe error metadata.
- [ ] Add tests for successful pushes, partial failures, and invalid/missing target handling.
      **Notes:** Line 654 marks the current branch as a stub that only reports files that would be pushed.

### [WL-6648]

**Title:** Replace MCP gateway placeholder executor with real server tool invocation
**Source:** [thegent/src/thegent/mcp/gateway.py:99]
**Acceptance checklist:**

- [ ] Implement server dispatch that invokes the requested MCP tool using registered server configuration.
- [ ] Preserve latency/error metadata and return stable errors for unknown tools and transport failures.
- [ ] Add tests covering successful execution, unknown server IDs, and downstream execution failures.
      **Notes:** Line 98 documents `execute` as a stub that returns a synthetic success payload.

### [WL-6649]

**Title:** Integrate dispatcher task execution with real runner infrastructure and HITL outcomes
**Source:** [thegent/src/thegent/orchestration/dispatcher.py:385]
**Acceptance checklist:**

- [ ] Replace placeholder `_execute_task` behavior with real runner invocation based on selected `runner_name`.
- [ ] Enforce HITL gate decisions as execution preconditions rather than log-and-continue behavior.
- [ ] Add tests for successful execution, runner failure propagation, and approval-required blocking.
      **Notes:** Line 385 marks `_execute_task` as placeholder code that currently returns synthetic success output.
