### [WL-6590]

**Title:** Replace endpoint reachability stub with deterministic HTTP/TCP probe checks
**Source:** [thegent/src/thegent/integrations/startup_validation.py:46]
**Acceptance checklist:**

- [ ] Implement real endpoint probing (HTTP status + timeout handling) instead of returning all-true results.
- [ ] Surface unreachable endpoints with structured reason codes used by `validate_all` warnings.
- [ ] Add unit tests that cover reachable, timeout, and DNS/connection-failure outcomes.
      **Notes:** Line 46 explicitly marks current reachability logic as a stub and always reports success.

### [WL-6591]

**Title:** Implement GitHub project item upsert flow in write sync path
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:202]
**Acceptance checklist:**

- [ ] Replace mock write result with real item create/update behavior via `gh project` operations.
- [ ] Map workstream fields to project fields with deterministic handling for missing/invalid values.
- [ ] Add integration-style tests that verify created vs updated counts and error propagation.
      **Notes:** Line 202 marks the TODO where write sync currently returns a mock zero-change response.

### [WL-6592]

**Title:** Implement conflict-aware config synchronization in unified config manager
**Source:** [thegent/src/thegent/integration/unified_config.py:163]
**Acceptance checklist:**

- [ ] Add concrete merge/conflict resolution logic for overlapping keys across systems.
- [ ] Persist resolved configuration updates to the correct source files with explicit change reporting.
- [ ] Add tests for precedence, conflict detection, and merge strategy outcomes.
      **Notes:** Line 162 is currently a placeholder block with no operational sync behavior.

### [WL-6593]

**Title:** Replace mock local-state collection with real registry-backed sync payloads
**Source:** [thegent/src/thegent/discovery/sync.py:69]
**Acceptance checklist:**

- [ ] Read real local state inputs (team registry, handoff data, recent runs) instead of static empty lists.
- [ ] Validate payload schema before writing peer inbox files.
- [ ] Add tests that verify payload content reflects real project state and handles missing sources safely.
      **Notes:** Line 69 labels local state collection as a mock and emits synthetic minimal data.

### [WL-6594]

**Title:** Implement cryptographically sound ZK proof verification beyond length checks
**Source:** [thegent/src/thegent/verification/zkp.py:59]
**Acceptance checklist:**

- [ ] Replace response-length validation with deterministic recomputation/verification of challenge response.
- [ ] Add freshness validation using proof timestamp and configurable replay window.
- [ ] Add tests for valid proof, commitment mismatch, stale proof, and tampered response cases.
      **Notes:** Line 59 marks current verification as mock behavior that accepts any 64-char response.

### [WL-6595]

**Title:** Replace hardcoded KPI placeholders with computed telemetry-backed metrics
**Source:** [thegent/src/thegent/execution.py:1048]
**Acceptance checklist:**

- [ ] Derive KPI values from run registry and contract telemetry data instead of constants.
- [ ] Define clear fallback/error behavior when required telemetry inputs are missing.
- [ ] Add tests that validate KPI calculations against fixture run/telemetry datasets.
      **Notes:** Line 1047 begins a block of placeholder KPI constants that can drift from real system behavior.

### [WL-6596]

**Title:** Implement Rich style token application in CLI design language runtime
**Source:** [thegent/src/thegent/design/design_language.py:101]
**Acceptance checklist:**

- [ ] Wire token values into concrete Rich theme/style configuration in `apply_to_cli`.
- [ ] Support platform-specific token overrides without mutating base token state.
- [ ] Add tests confirming configured styles are applied and fallback behavior is deterministic.
      **Notes:** Line 101 states CLI design application is a placeholder with no actual style configuration.

### [WL-6597]

**Title:** Implement real remote backend push path for sync command
**Source:** [thegent/src/thegent/commands/sync.py:654]
**Acceptance checklist:**

- [ ] Replace "would push" stub branch with actual remote transport/upload implementation.
- [ ] Include per-file success/failure accounting in `OperationResult.details`.
- [ ] Add tests for successful push, partial failure reporting, and remote target resolution.
      **Notes:** Line 654 is the current stub collection path that never transmits state remotely.

### [WL-6598]

**Title:** Replace MCP gateway stub executor with real tool invocation adapter
**Source:** [thegent/src/thegent/mcp/gateway.py:98]
**Acceptance checklist:**

- [ ] Execute registered MCP tools through configured server transport instead of returning placeholder results.
- [ ] Preserve timing and error metadata with stable error messages for unknown tools/transport failures.
- [ ] Add tests that validate successful invocation and failure paths across at least one registered server.
      **Notes:** Line 98 documents the execute path as a stub that only records input and returns synthetic output.

### [WL-6599]

**Title:** Integrate dispatcher task execution with real runner infrastructure and HITL gating outcome
**Source:** [thegent/src/thegent/orchestration/dispatcher.py:385]
**Acceptance checklist:**

- [ ] Replace placeholder `_execute_task` implementation with real runner invocation using resolved `runner_name`.
- [ ] Enforce HITL gate decisions as execution preconditions rather than log-only side effects.
- [ ] Add tests for successful execution, runner failure propagation, and approval-required blocking behavior.
      **Notes:** Line 385 marks `_execute_task` as placeholder production wiring and currently returns synthetic success.
