### [WL-6630]

**Title:** Implement real remote pull execution for `sync pull` instead of stub-only success output
**Source:** [thegent/src/thegent/commands/sync.py:700]
**Acceptance checklist:**

- [ ] Replace stub message flow with actual remote state fetch and local materialization logic.
- [ ] Populate `OperationResult.details` with real `files_pulled` entries and per-file failure metadata.
- [ ] Add command tests for successful pull, authentication failure, and unreachable remote cases.
      **Notes:** Line 700 currently returns a stub message indicating no remote backend is configured.

### [WL-6631]

**Title:** Implement GitHub Project item create/update operations in `sync_to_github`
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:202]
**Acceptance checklist:**

- [ ] Replace TODO branch with concrete `gh project` item create/update calls for mapped workstream fields.
- [ ] Track and return accurate `items_created` and `items_updated` counts with row-level errors.
- [ ] Add integration-style tests that validate write behavior and auth failure handling.
      **Notes:** Line 202 marks the unimplemented item mutation path and currently returns mock counts.

### [WL-6632]

**Title:** Implement conflict-aware merge execution in unified config synchronization
**Source:** [thegent/src/thegent/integration/unified_config.py:162]
**Acceptance checklist:**

- [ ] Add cross-source conflict detection with key provenance and conflict classification.
- [ ] Apply explicit merge strategy rules and persist resolved config outputs.
- [ ] Add tests for no-conflict sync, conflicting keys, and deterministic merge outcomes.
      **Notes:** Line 162 is a placeholder where config conflict handling and merge logic are not executed.

### [WL-6633]

**Title:** Replace GitHub read stub in autosync with real project status reconciliation
**Source:** [thegent/src/thegent/integrations/workstream_autosync.py:431]
**Acceptance checklist:**

- [ ] Query GitHub project item statuses and map them to local workstream item state.
- [ ] Update `items_successful` and `items_failed` based on per-item reconciliation outcomes.
- [ ] Add tests for successful sync, partial mismatch, and API error paths.
      **Notes:** Line 431 logs a stub read operation without fetching or applying GitHub status data.

### [WL-6634]

**Title:** Implement resource contention window analysis in planning simulation
**Source:** [thegent/src/thegent/planning/simulation.py:148]
**Acceptance checklist:**

- [ ] Compute time-window demand aggregation per resource and derive contention ratios.
- [ ] Emit `ContentionResult` entries with impacted tasks and peak-over-capacity intervals.
- [ ] Add deterministic tests for no-contention and over-capacity scenarios.
      **Notes:** Line 148 marks `simulate_resource_contention` as a D2 stub that currently returns an empty list.

### [WL-6635]

**Title:** Replace MCP gateway stub executor with real server tool invocation path
**Source:** [thegent/src/thegent/mcp/gateway.py:98]
**Acceptance checklist:**

- [ ] Wire `execute` to actual MCP server process/client invocation with argument forwarding.
- [ ] Preserve structured timing/error fields in `McpToolResult` for success and failure responses.
- [ ] Add tests for unknown server, successful tool call, and server-side execution error handling.
      **Notes:** Line 98 documents that execution currently returns placeholder results instead of invoking MCP tools.

### [WL-6636]

**Title:** Decode macOS screenshot PNG output into validated RGBA `ScreenFrame` buffers
**Source:** [thegent/src/thegent/automation/providers/macos_virtual_desktop.py:120]
**Acceptance checklist:**

- [ ] Decode `screencapture` PNG bytes into canonical RGBA pixel data instead of slicing raw bytes.
- [ ] Validate frame dimensions and byte length before constructing `ScreenFrame`.
- [ ] Add tests for successful decode, malformed image bytes, and fallback blank frame behavior.
      **Notes:** Line 120 identifies placeholder capture behavior that does not decode PNG output.

### [WL-6637]

**Title:** Integrate dispatcher task execution with concrete runner backend contracts
**Source:** [thegent/src/thegent/orchestration/dispatcher.py:399]
**Acceptance checklist:**

- [ ] Replace placeholder output generation with real runner invocation and output capture.
- [ ] Propagate runner errors into `DispatchResult` with stable error taxonomy.
- [ ] Add async tests for success, timeout, and runner failure paths.
      **Notes:** Line 399 returns a placeholder dispatch result instead of executing through runner infrastructure.

### [WL-6638]

**Title:** Replace Mojo bridge placeholder script with module/function invocation wiring
**Source:** [thegent/src/thegent/infra/mojo_bridge.py:414]
**Acceptance checklist:**

- [ ] Generate Mojo script content that imports and executes the requested module/function with provided args.
- [ ] Serialize structured return values/errors back into Python-compatible result objects.
- [ ] Add tests for successful kernel execution, contract validation failure, and missing-module behavior.
      **Notes:** Line 414 still emits placeholder Mojo code that prints env args rather than invoking target kernels.

### [WL-6639]

**Title:** Implement actual sub-agent execution lifecycle for synchronous dispatcher path
**Source:** [thegent/src/thegent/orchestration/sub_agent_dispatcher.py:138]
**Acceptance checklist:**

- [ ] Replace stub dispatch completion path with concrete agent execution and result-state transitions.
- [ ] Record accurate timing, budget consumption, and event emissions across lifecycle states.
- [ ] Add tests for local execution success, budget rejection, and remote backend delegation behavior.
      **Notes:** Line 138 documents dispatcher behavior as a stub where execution results are currently modeled, not run.
