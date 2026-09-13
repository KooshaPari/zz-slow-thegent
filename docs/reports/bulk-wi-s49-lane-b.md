### [WL-7980]

**Title:** Split session bootstrap failures across workspace resolve and runtime handoff stages
**Source:** [thegent/src/thegent/session/bootstrap.py:74]
**Acceptance checklist:**

- [ ] Replace catch-all bootstrap failure handling with explicit workspace-resolve and runtime-handoff error branches.
- [ ] Preserve successful bootstrap output fields and existing session identifier semantics.
- [ ] Add tests for missing workspace roots, runtime handoff failures, and successful bootstrap completion.
      **Notes:** Stage-specific bootstrap errors reduce ambiguity during lane orchestration startup triage.

### [WL-7981]

**Title:** Enforce deterministic provider probe ordering before capability match selection
**Source:** [thegent/src/thegent/providers/probe.py:53]
**Acceptance checklist:**

- [ ] Sort candidate provider probes by explicit stable criteria before capability matching is evaluated.
- [ ] Preserve existing successful provider match behavior when only one candidate is available.
- [ ] Add tests for repeated probe runs, equal-priority candidates, and deterministic selected provider output.
      **Notes:** Probe ordering drift causes non-repeatable provider selection in mixed runtime environments.

### [WL-7982]

**Title:** Separate hook preflight validation faults between schema parse and rule enforcement
**Source:** [thegent/src/thegent/hooks/preflight_validate.py:118]
**Acceptance checklist:**

- [ ] Split preflight failures into schema-parse and rule-enforcement error categories with explicit messages.
- [ ] Preserve successful preflight pass behavior and existing hook dispatch eligibility semantics.
- [ ] Add tests for malformed schema input, rule violation cases, and successful preflight validation.
      **Notes:** Distinct preflight error classes improve triage speed for hook activation failures.

### [WL-7983]

**Title:** Harden queue claim updates by isolating index lookup and state transition errors
**Source:** [thegent/src/thegent/queue/claim_updater.py:92]
**Acceptance checklist:**

- [ ] Replace broad claim update exception handling with explicit index-lookup and state-transition branches.
- [ ] Preserve successful claim ordering and existing conflict detection behavior.
- [ ] Add tests for missing queue indexes, invalid state transitions, and successful claim updates.
      **Notes:** Claim update diagnostics should identify whether lookup or mutation is the failing stage.

### [WL-7984]

**Title:** Validate report row normalization before markdown emission in bulk WI generation
**Source:** [thegent/src/thegent/reports/bulk_wi_writer.py:67]
**Acceptance checklist:**

- [ ] Add explicit row-normalization validation before markdown emission and fail with typed row context on invalid data.
- [ ] Preserve successful markdown output shape and header formatting used by existing bulk WI files.
- [ ] Add tests for missing required row fields, invalid identifiers, and successful bulk WI rendering.
      **Notes:** Early row validation prevents malformed output that breaks downstream report consumption.

### [WL-7985]

**Title:** Split command execution diagnostics across argv construction and subprocess dispatch
**Source:** [thegent/src/thegent/infra/command_exec.py:141]
**Acceptance checklist:**

- [ ] Separate execution failure paths so argv-construction and subprocess-dispatch errors are reported independently.
- [ ] Preserve successful command stdout capture and exit-code propagation semantics.
- [ ] Add tests for invalid argv token construction, dispatch-time failures, and successful command execution.
      **Notes:** Execution diagnostics are more actionable when input-shaping and process-launch errors are not conflated.

### [WL-7986]

**Title:** Differentiate artifact collection failures between path expansion and digest persistence
**Source:** [thegent/src/thegent/artifacts/collector.py:105]
**Acceptance checklist:**

- [ ] Replace generic collection exceptions with explicit path-expansion and digest-persistence failure branches.
- [ ] Preserve successful artifact ordering and existing digest output schema.
- [ ] Add tests for unresolved glob inputs, persistence write errors, and successful collection runs.
      **Notes:** Artifact failures should pinpoint whether discovery or persistence is responsible.

### [WL-7987]

**Title:** Enforce stable dependency sort in DAG planner before runnable node extraction
**Source:** [thegent/src/thegent/planner/dag_extract.py:83]
**Acceptance checklist:**

- [ ] Apply deterministic dependency sorting before runnable node extraction from the DAG.
- [ ] Preserve existing cycle rejection behavior and runnable node eligibility rules.
- [ ] Add tests for repeated extraction on identical graphs, equal-depth dependency sets, and stable node output ordering.
      **Notes:** Stable DAG extraction output prevents cross-lane drift in parallel assignment workflows.

### [WL-7988]

**Title:** Isolate log sink write failures between buffer serialization and file commit stages
**Source:** [thegent/src/thegent/logging/sink_writer.py:59]
**Acceptance checklist:**

- [ ] Split sink write failures into buffer-serialization and file-commit branches with typed error reporting.
- [ ] Preserve successful log line ordering and timestamp formatting guarantees.
- [ ] Add tests for serialization-time exceptions, commit-time write failures, and successful sink writes.
      **Notes:** Separating serialization and commit failures shortens root-cause analysis during incident response.

### [WL-7989]

**Title:** Classify retry pipeline errors by backoff plan generation and attempt execution
**Source:** [thegent/src/thegent/retry/pipeline.py:127]
**Acceptance checklist:**

- [ ] Replace catch-all retry failures with explicit backoff-plan generation and attempt-execution branches.
- [ ] Preserve successful retry attempt counting and max-attempt termination behavior.
- [ ] Add tests for invalid backoff configurations, attempt execution faults, and successful retry completion.
      **Notes:** Retry telemetry should indicate whether timing strategy or execution path caused failure.
