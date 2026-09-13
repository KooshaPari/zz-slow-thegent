### [WL-6490]

**Title:** Implement concrete `sync update` execution path instead of placeholder success return
**Source:** [thegent/src/thegent/commands/sync.py:569]
**Acceptance checklist:**

- [ ] Replace placeholder success branch with real update orchestration for configured sync targets.
- [ ] Surface partial-failure details in `OperationResult.errors` and `OperationResult.details`.
- [ ] Add focused unit tests covering success, dry-run, and failure modes.
      **Notes:**
- Current flow always reports up-to-date even when no backend update check runs.

### [WL-6491]

**Title:** Wire `sync push` to a real remote backend instead of stubbed file-count response
**Source:** [thegent/src/thegent/commands/sync.py:662]
**Acceptance checklist:**

- [ ] Replace stub message path with backend upload logic for discovered agent and hook artifacts.
- [ ] Preserve deterministic payload ordering and record remote identifiers in result details.
- [ ] Add tests validating target resolution and upload failure handling.
      **Notes:**
- The current `"stub": true` branch masks transport/auth errors.

### [WL-6492]

**Title:** Implement real `sync pull` state fetch and apply workflow
**Source:** [thegent/src/thegent/commands/sync.py:700]
**Acceptance checklist:**

- [ ] Replace stub response with backend download + local apply pipeline.
- [ ] Record fetched artifact set and conflict policy decisions in structured details.
- [ ] Add tests for empty remote state, merge conflicts, and connectivity failures.
      **Notes:**
- Existing logic always returns success with zero pulled files.

### [WL-6493]

**Title:** Replace MCP gateway stub executor with actual tool invocation transport
**Source:** [thegent/src/thegent/mcp/gateway.py:98]
**Acceptance checklist:**

- [ ] Implement execution path that dispatches calls to configured MCP server processes.
- [ ] Map transport/tool errors into `McpToolResult.error` with actionable diagnostics.
- [ ] Add tests for unknown server, successful invocation, and timeout/error cases.
      **Notes:**
- Current implementation only logs and returns placeholder output.

### [WL-6494]

**Title:** Implement endpoint reachability probing in startup validation
**Source:** [thegent/src/thegent/integrations/startup_validation.py:46]
**Acceptance checklist:**

- [ ] Replace always-true map with real network reachability checks and bounded timeouts.
- [ ] Distinguish DNS, connection, TLS, and timeout failures in return data.
- [ ] Add deterministic tests using mocked transport results.
      **Notes:**
- Stub behavior can produce false-green startup checks.

### [WL-6495]

**Title:** Integrate dispatcher `_execute_task` with real runner infrastructure
**Source:** [thegent/src/thegent/orchestration/dispatcher.py:399]
**Acceptance checklist:**

- [ ] Replace placeholder output generation with concrete runner dispatch and result capture.
- [ ] Propagate runner errors and non-zero outcomes through `DispatchResult` semantics.
- [ ] Add tests for runner selection fallback and execution failure propagation.
      **Notes:**
- Current path reports success without executing workload logic.

### [WL-6496]

**Title:** Convert `SubAgentDispatcher` from synchronous stub semantics to true execution backend
**Source:** [thegent/src/thegent/orchestration/sub_agent_dispatcher.py:138]
**Acceptance checklist:**

- [ ] Implement real agent execution lifecycle behind `dispatch()` while keeping event emission contract.
- [ ] Ensure budget enforcement remains authoritative across local and remote execution paths.
- [ ] Add integration tests for capability routing, budget rejection, and completion events.
      **Notes:**
- The class contract documents a stubbed completion model that hides runtime failures.

### [WL-6497]

**Title:** Complete PERT forward pass with dependency-aware critical path calculation
**Source:** [thegent/src/thegent/planning/simulation.py:38]
**Acceptance checklist:**

- [ ] Extend forward pass to compute earliest/latest dates and true `critical_path` flags.
- [ ] Populate `total_float` based on predecessor graph instead of fixed zero values.
- [ ] Add tests with branched DAG fixtures validating critical path correctness.
      **Notes:**
- Present implementation computes only per-node expected duration/variance.

### [WL-6498]

**Title:** Implement resource contention simulation instead of empty result return
**Source:** [thegent/src/thegent/planning/simulation.py:148]
**Acceptance checklist:**

- [ ] Build time-window overlap analysis across task demand profiles and resource capacities.
- [ ] Return ranked contention windows with affected task IDs and contention ratios.
- [ ] Add tests covering no-contention, single-window contention, and multi-resource contention.
      **Notes:**
- Returning `[]` prevents downstream bottleneck workflows from receiving signal.

### [WL-6499]

**Title:** Implement GitHub Project CSV import flow through `gh` API mutations
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:359]
**Acceptance checklist:**

- [ ] Parse CSV rows into validated project item mutations with schema checks.
- [ ] Execute create/update operations via authenticated `gh` commands with retryable error handling.
- [ ] Add tests for malformed CSV, auth failures, and partial import recovery behavior.
      **Notes:**
- Current function returns mock success data without importing records.
