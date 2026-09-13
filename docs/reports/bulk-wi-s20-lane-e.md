### [WL-6560]

**Title:** Implement concrete `sync update` backend flow instead of placeholder success reporting
**Source Path+Line:** [thegent/src/thegent/commands/sync.py:569]
**Acceptance Checklist:**

- [ ] Replace placeholder update branch with real remote state comparison and update execution.
- [ ] Populate `OperationResult.details` with changed artifacts and per-step outcomes.
- [ ] Add focused tests for success, no-op, and remote failure paths.
      **Notes:** Current path explicitly reports placeholder success without performing backend update work.

### [WL-6561]

**Title:** Replace `sync push` stub response with authenticated remote publish logic
**Source Path+Line:** [thegent/src/thegent/commands/sync.py:662]
**Acceptance Checklist:**

- [ ] Implement real push transport for discovered agents/hooks with deterministic ordering.
- [ ] Surface remote errors and partial-push outcomes in structured result fields.
- [ ] Add tests covering empty payload, successful publish, and rejected publish scenarios.
      **Notes:** The current message is marked `[stub]` and never attempts remote mutation.

### [WL-6562]

**Title:** Implement `sync pull` retrieval and apply pipeline for remote state
**Source Path+Line:** [thegent/src/thegent/commands/sync.py:700]
**Acceptance Checklist:**

- [ ] Replace stubbed pull response with backend fetch and local apply behavior.
- [ ] Track pulled files, merge/conflict decisions, and apply status in `OperationResult.details`.
- [ ] Add tests for empty remote state, conflict handling, and transport failures.
      **Notes:** This branch currently reports success while returning a fixed stub payload.

### [WL-6563]

**Title:** Wire MCP gateway execution to real server invocation instead of placeholder output
**Source Path+Line:** [thegent/src/thegent/mcp/gateway.py:98]
**Acceptance Checklist:**

- [ ] Replace stub executor behavior with concrete MCP request/response handling.
- [ ] Preserve explicit unknown-server, timeout, and tool-failure error payloads.
- [ ] Add tests for successful invocation, unknown server ID, and execution error branches.
      **Notes:** The method docstring marks this path as deferred integration and placeholder-only today.

### [WL-6564]

**Title:** Implement native `diff_stat` through real git bindings with accurate counts
**Source Path+Line:** [thegent/src/thegent/native/git_native.py:57]
**Acceptance Checklist:**

- [ ] Replace TODO + zeroed return values with real repository diff statistics.
- [ ] Keep return schema stable while removing unconditional warning behavior.
- [ ] Add tests on temp repos for modified, insertion, and deletion counting.
      **Notes:** Current implementation always returns zeros, masking real repository churn.

### [WL-6565]

**Title:** Replace startup endpoint reachability stub with bounded network probes
**Source Path+Line:** [thegent/src/thegent/integrations/startup_validation.py:55]
**Acceptance Checklist:**

- [ ] Implement actual endpoint probes with timeout and protocol-safe error handling.
- [ ] Return per-endpoint boolean results derived from real probe outcomes.
- [ ] Add tests for reachable, unreachable, and timeout endpoints.
      **Notes:** The current implementation hardcodes all endpoints as reachable.

### [WL-6566]

**Title:** Integrate dispatcher node execution with real runner invocation path
**Source Path+Line:** [thegent/src/thegent/orchestration/dispatcher.py:398]
**Acceptance Checklist:**

- [ ] Replace placeholder output generation with actual runner dispatch/execution.
- [ ] Propagate non-success execution state and captured error details to callers.
- [ ] Add tests for successful execution, runner failure, and missing-runner handling.
      **Notes:** `_execute_task` currently returns synthetic success without running workload logic.

### [WL-6567]

**Title:** Implement unified configuration sync conflict detection and merge semantics
**Source Path+Line:** [thegent/src/thegent/integration/unified_config.py:162]
**Acceptance Checklist:**

- [ ] Detect config conflicts across sources and classify merge-required cases.
- [ ] Apply deterministic merge strategy and persist resolved state where needed.
- [ ] Add tests for no-conflict sync, conflict resolution, and irreconcilable conflict behavior.
      **Notes:** The method currently consists of placeholder comments and no executable sync logic.

### [WL-6568]

**Title:** Replace SLO payload stub emitter with transport-backed metrics emission
**Source Path+Line:** [thegent/src/thegent/metrics/collector.py:48]
**Acceptance Checklist:**

- [ ] Implement real metric emission pathway while retaining structured payload contract.
- [ ] Record and surface emission failures instead of silently returning a local-only stub.
- [ ] Add tests for successful emit, threshold status evaluation, and transport errors.
      **Notes:** `emit_slo_stub` is intentionally marked as a stub and should become production telemetry wiring.

### [WL-6569]

**Title:** Implement SAML assertion parsing and validation in auth bridge flow
**Source Path+Line:** [thegent/src/thegent/security/auth_bridge.py:75]
**Acceptance Checklist:**

- [ ] Replace placeholder claim dictionary with parsed assertions from SAML response input.
- [ ] Validate required claims and issuer/signature expectations before returning identity data.
- [ ] Add tests for valid assertions, missing required claims, and invalid assertion format.
      **Notes:** Current implementation returns a fixed mock identity and does not parse assertions.
