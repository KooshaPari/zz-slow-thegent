### [WL-8030]

**Title:** Separate workspace discovery and session attach error surfaces in CLI bootstrap
**Source:** [thegent/src/thegent/session/bootstrap.py:74]
**Acceptance checklist:**

- [ ] Return dedicated diagnostics for missing workspace and invalid session attach payloads.
- [ ] Preserve successful bootstrap output and existing session identifier stability.
- [ ] Add tests for discovery-failure, attach-failure, and successful bootstrap paths.
      **Notes:** Distinct failure classes reduce triage time during orchestrator startup.

### [WL-8031]

**Title:** Split hook preflight validation into parse and execution branches in control plane
**Source:** [thegent/src/thegent/control_plane/server.py:128]
**Acceptance checklist:**

- [ ] Emit separate status for policy parse errors versus handler execution errors.
- [ ] Preserve current hook dispatch eligibility and error-code behavior for successful parses.
- [ ] Add tests for malformed config, runtime handler exceptions, and successful preflight completion.
      **Notes:** Clearer branching improves incident diagnostics and replayability.

### [WL-8032]

**Title:** Isolate queue claim lifecycle checks from claim mutation errors
**Source:** [thegent/src/thegent/queue/claim.py:211]
**Acceptance checklist:**

- [ ] Distinguish missing index, stale state, and mutation write-back errors explicitly.
- [ ] Preserve existing claim ordering and conflict detection semantics.
- [ ] Add tests for each failure branch and successful claim transitions.
      **Notes:** Deterministic claim errors prevent ambiguous queue recovery decisions.

### [WL-8033]

**Title:** Separate artifact discovery failures from digest write failures in artifact pipeline
**Source:** [thegent/src/thegent/artifacts/collector.py:98]
**Acceptance checklist:**

- [ ] Split discovery, filtering, and persistence errors into distinct catch points.
- [ ] Preserve successful artifact ordering and metadata output contracts.
- [ ] Add tests for wildcard expansion faults, permission-denied writes, and successful runs.
      **Notes:** Stage-specific diagnostics simplify artifact recovery in noisy workflows.

### [WL-8034]

**Title:** Differentiate command plan generation and launch errors in agent proxy execution
**Source:** [thegent/src/thegent/infra/agent_runner.py:311]
**Acceptance checklist:**

- [ ] Split command assembly failures from subprocess spawn failures in error reporting.
- [ ] Preserve command output shape and exit-code forwarding semantics on success.
- [ ] Add tests for invalid argv construction, spawn exceptions, and successful command completion.
      **Notes:** Operators can fix launch issues faster when failure root cause is explicit.

### [WL-8035]

**Title:** Split DAG extraction validation from runnable-node selection in planner
**Source:** [thegent/src/thegent/planner/dag.py:412]
**Acceptance checklist:**

- [ ] Add explicit validation errors for malformed DAG payloads before runnable filtering.
- [ ] Preserve existing cycle and dependency logic when input is valid.
- [ ] Add tests for malformed DAG, valid DAG with cycles, and normal extraction output ordering.
      **Notes:** Early validation improves reliability of planning in mixed-quality streams.

### [WL-8036]

**Title:** Separate runtime metrics serialization from publication failures in metrics sink
**Source:** [thegent/src/thegent/telemetry/metrics_sink.py:59]
**Acceptance checklist:**

- [ ] Return explicit failure mode for payload serialization versus transport publish failures.
- [ ] Preserve successful metric envelope schema and timestamp ordering.
- [ ] Add tests for serialization edge cases, publish backpressure, and successful metric flushes.
      **Notes:** Split-failures provide faster rollback and safer retry behavior.

### [WL-8037]

**Title:** Distinguish config merge conflicts from runtime validation failures in settings load
**Source:** [thegent/src/thegent/config/settings.py:173]
**Acceptance checklist:**

- [ ] Raise separate errors for file-merge conflicts and runtime validation failures.
- [ ] Preserve existing default fallback behavior for valid merged config payloads.
- [ ] Add tests for conflicting overrides, invalid values, and clean config loads.
      **Notes:** Faster isolation of config faults accelerates boot-time diagnosis.

### [WL-8038]

**Title:** Split retry policy evaluation and attempt execution failures in workflow engine
**Source:** [thegent/src/thegent/retry/strategy.py:89]
**Acceptance checklist:**

- [ ] Separate malformed retry policy detection from execution-attempt failures.
- [ ] Preserve existing retry count, jitter, and final success semantics.
- [ ] Add tests for invalid policy definitions, transient execution faults, and successful completion.
      **Notes:** Clarifies why retries abort and where compensating action is required.

### [WL-8039]

**Title:** Isolate lane dependency lookup failures from downstream dispatch failures in scheduler
**Source:** [thegent/src/thegent/orchestration/scheduler.py:246]
**Acceptance checklist:**

- [ ] Emit distinct diagnostics for missing dependency rows versus dispatch invocation failures.
- [ ] Preserve current lane ordering and dispatch handoff behavior when dependencies are satisfiable.
- [ ] Add tests for unresolved dependencies, dispatch exceptions, and successful lane handoff.
      **Notes:** Reduces incorrect retries caused by conflated scheduler failures.
