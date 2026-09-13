### [WL-10620]

**Title:** Preserve provider selection by separating rule evaluation and final selection
**Source:** [thegent/src/thegent/automation/workflow.go:640]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10621]

**Title:** Preserve workflow progression by separating guard checks and execution
**Source:** [thegent/src/thegent/providers/registry.go:669]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10622]

**Title:** Preserve hook reliability by separating registration from invocation
**Source:** [thegent/src/thegent/queue/storage.go:698]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10623]

**Title:** Preserve policy gating by separating matching and enforcement paths
**Source:** [thegent/src/thegent/runner/runner.go:727]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10624]

**Title:** Preserve queue scheduling by separating priority and execution
**Source:** [thegent/src/thegent/policy/engine.go:756]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10625]

**Title:** Preserve session consistency by separating state updates and persistence
**Source:** [thegent/src/thegent/observability/prometheus.go:785]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10626]

**Title:** Preserve sync integrity by separating diff generation and commit
**Source:** [thegent/src/thegent/mcp/server.go:194]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10627]

**Title:** Preserve observability by separating events from serialization
**Source:** [thegent/src/thegent/commands/dispatch.go:223]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10628]

**Title:** Preserve CLI dispatch by separating command parse and handler selection
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:252]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10629]

**Title:** Preserve error semantics by separating retry loops and terminal outcomes
**Source:** [thegent/src/thegent/hooks/dispatcher.go:281]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
