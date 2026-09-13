### [WL-8130]

**Title:** Separate lane model priority validation from lane ordering behavior in execution lanes
**Source:** [thegent/src/thegent/orchestration/execution/lanes.py:38]
**Acceptance checklist:**

- [ ] Split invalid lane configuration, unknown lane label handling, and valid lane resolution into separate error branches.
- [ ] Preserve existing lane urgency, protected lane, and sort behavior for valid inputs.
- [ ] Add tests for invalid lane strings, mixed urgency workloads, and stable lane ordering with valid models.
      **Notes:** Clear stage separation keeps malformed lane input from polluting scheduling diagnostics.

### [WL-8131]

**Title:** Split dispatch configuration validation from runner resolution in lane dispatcher
**Source:** [thegent/src/thegent/orchestration/dispatcher.py:89]
**Acceptance checklist:**

- [ ] Distinguish config/default timeout validation errors from runner resolution and dispatch failures.
- [ ] Preserve existing dispatch result payload and concurrency behavior on successful plans.
- [ ] Add tests for invalid dispatch config, unresolved runners, and successful node handoff.
      **Notes:** Explicit failure branches reduce ambiguity during run-loop outages.

### [WL-8132]

**Title:** Separate orchestrate CLI argument parsing from scheduling action execution
**Source:** [thegent/src/thegent/cli/apps/orchestrate.py:89]
**Acceptance checklist:**

- [ ] Split parse/validation failures from invocation of underlying run/plan command execution.
- [ ] Preserve existing CLI options and successful flow for supported orchestration modes.
- [ ] Add tests for parse error handling, malformed workstream identifiers, and successful invocation paths.
      **Notes:** Operators can fix bad CLI inputs without losing visibility into valid invocation behavior.

### [WL-8133]

**Title:** Isolate task construction from persistence writes in prompt queue storage
**Source:** [thegent/src/thegent/queue/storage.py:34]
**Acceptance checklist:**

- [ ] Separate payload validation errors from queue persistence and lease state update failures.
- [ ] Preserve existing queue ordering, IDs, and successful append/claim semantics.
- [ ] Add tests for malformed payloads, persistence failures, and successful queue operations.
      **Notes:** Better failure granularity improves retry and evidence capture for queue backlogs.

### [WL-8134]

**Title:** Split work-stream next-item discovery from owner claim transition logic
**Source:** [thegent/src/thegent/cli/services/work_stream_orchestration.py:16]
**Acceptance checklist:**

- [ ] Split empty queue checks, invalid task-file errors, and claim transition errors into dedicated failure paths.
- [ ] Preserve existing ownership handoff and completion transitions when tasks are valid.
- [ ] Add tests for missing workstream files, claim conflicts, and successful claim/complete paths.
      **Notes:** Distinct branches make lane-b throughput stalls easier to diagnose.

### [WL-8135]

**Title:** Separate conflict prediction from merge execution in smart merger flow
**Source:** [thegent/src/thegent/coordination/smart_merge.py:36]
**Acceptance checklist:**

- [ ] Split conflict prediction failures from structural merge execution failures in diagnostics.
- [ ] Preserve successful merge outputs and content for clean merge inputs.
- [ ] Add tests for prediction-only conflicts, merge execution conflicts, and successful merge output checks.
      **Notes:** Keeps proactive conflict guidance from being conflated with merge runtime failures.

### [WL-8136]

**Title:** Separate handoff command validation from MCP handoff side-effects
**Source:** [thegent/src/thegent/mcp/server/tools_handoff_queue.py:11]
**Acceptance checklist:**

- [ ] Distinguish snapshot ID/owner validation issues from tool call execution errors.
- [ ] Preserve existing handoff list/show/confirm contract for valid tool inputs.
- [ ] Add tests for invalid inputs, queue backend failures, and successful handoff confirmations.
      **Notes:** Improves recovery when MCP transport and domain validation fail independently.

### [WL-8137]

**Title:** Split Pareto TUI audit-file parsing from data presentation formatting
**Source:** [thegent/src/thegent/cli/tui/pareto.py:42]
**Acceptance checklist:**

- [ ] Separate JSON line parsing failures from status rendering path failures.
- [ ] Preserve existing dashboard status output shape for successfully parsed audit files.
- [ ] Add tests for malformed log lines, missing audit files, and successful status rendering.
      **Notes:** Keeps UI failures observable without masking data-parse failures.

### [WL-8138]

**Title:** Separate retry-wrapper setup from request execution in fast HTTP client
**Source:** [thegent/src/thegent/infra/fast_http_client.py:32]
**Acceptance checklist:**

- [ ] Add explicit diagnostics for retry wrapper construction versus transport/request execution failures.
- [ ] Preserve existing backend selection and request semantics for successful API calls.
- [ ] Add tests for client init failures, transport failures, and successful get/post flows.
      **Notes:** Distinguishing initialization and execution failures shortens client-side incident response.

### [WL-8139]

**Title:** Split execution complexity routing from command launch in execution engine
**Source:** [thegent/src/thegent/orchestration/execution/engine.py:32]
**Acceptance checklist:**

- [ ] Separate complexity classification/routing decision failures from actual run invocation failures.
- [ ] Preserve existing complexity-aware routing outcomes when classification is successful.
- [ ] Add tests for invalid run metadata, unreachable routing paths, and successful execution handoff.
      **Notes:** Keeps routing intelligence errors from hiding execution runtime exceptions.
