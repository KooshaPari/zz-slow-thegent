### [WL-7630]

**Title:** Split session transcript export errors into fetch and serialization stages
**Source:** [thegent/src/thegent/session/transcript_exporter.py:184]
**Acceptance checklist:**

- [ ] Replace broad transcript export exception handling with explicit transcript-fetch and output-serialization branches.
- [ ] Preserve existing exported transcript schema and artifact naming conventions.
- [ ] Add tests for successful export, fetch-stage failure, and serialization-stage failure.
      **Notes:** Current catch-all handling masks whether export failures come from source retrieval or formatting.

### [WL-7631]

**Title:** Classify MCP startup failures by configuration validation versus process launch
**Source:** [thegent/src/thegent/mcp/startup.py:129]
**Acceptance checklist:**

- [ ] Replace generic MCP startup exception handling with explicit config-validation and process-launch failure branches.
- [ ] Preserve current startup return contract for successful initialization.
- [ ] Add tests for valid startup, invalid configuration, and launch failure.
      **Notes:** A single startup failure path hides the distinction between bad inputs and runtime spawn faults.

### [WL-7632]

**Title:** Separate cache hydration parse faults from cache I/O faults
**Source:** [thegent/src/thegent/cache/hydration.py:91]
**Acceptance checklist:**

- [ ] Replace broad hydration exception handling with explicit cache-parse and filesystem-I/O error branches.
- [ ] Preserve existing cache hydration fallback behavior for empty state initialization.
- [ ] Add tests for successful hydration, malformed cache payload, and read failure.
      **Notes:** Conflated hydration failures make triage noisy when cache data and disk availability fail differently.

### [WL-7633]

**Title:** Differentiate command plan build errors from dependency resolution errors
**Source:** [thegent/src/thegent/planner/command_plan.py:256]
**Acceptance checklist:**

- [ ] Replace generic planning exception handling with explicit plan-construction and dependency-resolution branches.
- [ ] Preserve current planner output shape on successful command plan generation.
- [ ] Add tests for successful plan build, invalid plan structure, and dependency resolution failure.
      **Notes:** The current error boundary combines independent failure modes into one non-actionable path.

### [WL-7634]

**Title:** Split renderer asset-load failures from template-evaluation failures
**Source:** [thegent/src/thegent/ui/render_pipeline.py:338]
**Acceptance checklist:**

- [ ] Replace catch-all render pipeline exception handling with explicit asset-load and template-evaluation branches.
- [ ] Preserve existing rendered output contract for successful UI pipeline execution.
- [ ] Add tests for successful render, missing asset, and template evaluation error.
      **Notes:** Single-path render failures reduce visibility into whether data inputs or assets are broken.

### [WL-7635]

**Title:** Classify approval workflow errors by policy evaluation versus persistence stage
**Source:** [thegent/src/thegent/approval/workflow.py:173]
**Acceptance checklist:**

- [ ] Replace broad workflow exception handling with explicit policy-evaluation and persistence-write failure branches.
- [ ] Preserve current approval decision semantics and status transitions on success.
- [ ] Add tests for successful approval, policy evaluation failure, and persistence failure.
      **Notes:** Policy and storage failures currently collapse into one result, obscuring remediation priority.

### [WL-7636]

**Title:** Differentiate local tool execution timeout errors from non-zero exit failures
**Source:** [thegent/src/thegent/tools/local_runner.py:214]
**Acceptance checklist:**

- [ ] Replace generic local-runner exception handling with explicit timeout and process-exit failure branches.
- [ ] Preserve existing command invocation API and successful output parsing behavior.
- [ ] Add tests for successful execution, timeout handling, and non-zero exit handling.
      **Notes:** Combining timeout and exit failures makes retry strategy decisions inconsistent.

### [WL-7637]

**Title:** Separate config merge schema violations from override collision failures
**Source:** [thegent/src/thegent/config/merge.py:147]
**Acceptance checklist:**

- [ ] Replace broad config merge exception handling with explicit schema-validation and override-collision branches.
- [ ] Preserve current merged-config output format when inputs are valid.
- [ ] Add tests for successful merge, schema violation, and collision rejection.
      **Notes:** A single merge error does not indicate whether input structure or key conflicts caused failure.

### [WL-7638]

**Title:** Split telemetry flush failures into queue-drain and transport-submit stages
**Source:** [thegent/src/thegent/telemetry/flush.py:202]
**Acceptance checklist:**

- [ ] Replace blanket telemetry flush exception handling with explicit queue-drain and transport-submit failure branches.
- [ ] Preserve current non-blocking telemetry behavior for caller-facing flows.
- [ ] Add tests for successful flush, drain failure, and submit failure.
      **Notes:** Current handling obscures which flush phase degrades and limits targeted alerting.

### [WL-7639]

**Title:** Classify workspace scan failures by glob expansion versus filesystem traversal
**Source:** [thegent/src/thegent/workspace/scanner.py:118]
**Acceptance checklist:**

- [ ] Replace broad workspace scan exception handling with explicit glob-expansion and filesystem-traversal branches.
- [ ] Preserve existing scan result structure and filtering semantics on success.
- [ ] Add tests for successful scan, invalid glob input, and traversal failure.
      **Notes:** Scan diagnostics are currently too coarse to distinguish invalid patterns from environmental filesystem faults.
