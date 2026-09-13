### [WL-7730]

**Title:** Separate remote compute request timeout handling from generic transport failures
**Source:** [thegent/src/thegent/research/remote_compute.py:64]
**Acceptance checklist:**

- [ ] Replace broad remote compute exception handling with explicit timeout and non-timeout transport branches.
- [ ] Preserve successful remote compute result structure and field names.
- [ ] Add tests for timeout failure, transport failure, and successful execution.
      **Notes:** Current handling obscures whether failures are latency-related or caused by other network errors.

### [WL-7731]

**Title:** Split conversation dump write failures between JSON encode and filesystem stages
**Source:** [thegent/src/thegent/session/conversation_dumper.py:168]
**Acceptance checklist:**

- [ ] Replace catch-all dump exceptions with explicit serialization and file-write branches.
- [ ] Preserve current conversation dump artifact naming and payload contract.
- [ ] Add tests for serialization failure, write-permission failure, and successful dump creation.
      **Notes:** Existing diagnostics make triage slower by collapsing encoding and disk issues into one path.

### [WL-7732]

**Title:** Differentiate terminal pane startup failures across PTY init and layout render setup
**Source:** [thegent/src/thegent/compositor/terminal_pane.py:86]
**Acceptance checklist:**

- [ ] Replace broad startup exception boundaries with explicit PTY-init and render-setup branches.
- [ ] Preserve normal terminal pane bootstrap behavior for healthy initialization.
- [ ] Add tests for PTY initialization failure, render setup failure, and successful startup.
      **Notes:** The current startup failure path does not indicate which initialization stage regressed.

### [WL-7733]

**Title:** Classify session-state load errors into parse versus schema-shape failures
**Source:** [thegent/src/thegent/compositor/session_state.py:55]
**Acceptance checklist:**

- [ ] Replace generic state-load error handling with explicit parse and schema-validation branches.
- [ ] Preserve successful state restoration semantics and default fallbacks.
- [ ] Add tests for malformed persisted state, invalid schema shape, and successful load.
      **Notes:** Current errors do not expose whether file contents are malformed or structurally invalid.

### [WL-7734]

**Title:** Preserve pre-warmer diagnostics by splitting source fetch and cache write failures
**Source:** [thegent/src/thegent/cache/pre_warmer.py:176]
**Acceptance checklist:**

- [ ] Replace broad pre-warmer exception handling with explicit source-fetch and cache-write branches.
- [ ] Preserve successful pre-warm counters and output metrics contract.
- [ ] Add tests for source fetch failure, cache write failure, and successful pre-warm run.
      **Notes:** A single pre-warmer failure mode limits targeted remediation during degraded runs.

### [WL-7735]

**Title:** Separate compositor frame assembly failures from terminal flush failures
**Source:** [thegent/src/thegent/ux/compositor.py:74]
**Acceptance checklist:**

- [ ] Replace catch-all compositor loop error handling with explicit frame-assembly and terminal-flush branches.
- [ ] Preserve current compositor render cadence for successful frames.
- [ ] Add tests for frame assembly failure, flush failure, and successful render loop iteration.
      **Notes:** Existing compositor errors conflate scene construction and output emission problems.

### [WL-7736]

**Title:** Split fallback UI rendering faults between template selection and output formatting
**Source:** [thegent/src/thegent/ux/fallback_ui.py:33]
**Acceptance checklist:**

- [ ] Replace generic fallback UI exception handling with explicit template-selection and output-formatting branches.
- [ ] Preserve current fallback UI text contract on successful rendering.
- [ ] Add tests for missing template path, formatting failure, and successful fallback render.
      **Notes:** Current fallback failures do not reveal whether template discovery or formatting is at fault.

### [WL-7737]

**Title:** Differentiate shared MCP manager startup failures between config validation and process launch
**Source:** [thegent/src/thegent/shared_mcp_manager.py:118]
**Acceptance checklist:**

- [ ] Replace broad manager-start exception handling with explicit configuration-validation and process-launch branches.
- [ ] Preserve existing successful startup state transitions and health indicators.
- [ ] Add tests for invalid startup config, process spawn failure, and successful manager start.
      **Notes:** Startup observability is reduced when input-validation and runtime launch failures are merged.

### [WL-7738]

**Title:** Keep cliproxy request transform errors typed for payload parse and mapping stages
**Source:** [thegent/src/thegent/cliproxy_request_transform.py:142]
**Acceptance checklist:**

- [ ] Replace broad transform exception handling with explicit payload-parse and provider-mapping branches.
- [ ] Preserve current transformed request shape for valid inputs.
- [ ] Add tests for malformed payload input, mapping lookup failure, and successful transform.
      **Notes:** Current diagnostics hide whether bad input or mapping rules caused transformation failure.

### [WL-7739]

**Title:** Classify health-check failures by probe execution versus status evaluation
**Source:** [thegent/src/thegent/monitoring/health_check.py:29]
**Acceptance checklist:**

- [ ] Replace catch-all health-check exception handling with explicit probe-execution and status-evaluation branches.
- [ ] Preserve existing healthy-path status payload for successful checks.
- [ ] Add tests for probe execution failure, status evaluation failure, and successful health check.
      **Notes:** A single error bucket prevents fast discrimination between execution and interpretation faults.
