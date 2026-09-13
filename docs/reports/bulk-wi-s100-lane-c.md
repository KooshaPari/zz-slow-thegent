### [WL-10640]

**Title:** Preserve hook reliability by separating registration from invocation
**Source:** [thegent/src/thegent/observability/prometheus.go:600]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10641]

**Title:** Preserve session consistency by separating state updates and persistence
**Source:** [thegent/src/thegent/mcp/server.go:629]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10642]

**Title:** Preserve CLI dispatch by separating command parse and handler selection
**Source:** [thegent/src/thegent/commands/dispatch.go:658]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10643]

**Title:** Preserve workflow progression by separating guard checks and execution
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:687]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10644]

**Title:** Preserve queue scheduling by separating priority and execution
**Source:** [thegent/src/thegent/hooks/dispatcher.go:716]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10645]

**Title:** Preserve observability by separating events from serialization
**Source:** [thegent/src/thegent/session/state.go:745]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10646]

**Title:** Preserve provider selection by separating rule evaluation and final selection
**Source:** [thegent/src/thegent/automation/workflow.go:774]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10647]

**Title:** Preserve policy gating by separating matching and enforcement paths
**Source:** [thegent/src/thegent/providers/registry.go:183]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10648]

**Title:** Preserve sync integrity by separating diff generation and commit
**Source:** [thegent/src/thegent/queue/storage.go:212]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10649]

**Title:** Preserve error semantics by separating retry loops and terminal outcomes
**Source:** [thegent/src/thegent/runner/runner.go:241]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
