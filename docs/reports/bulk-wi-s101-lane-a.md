### [WL-10670]

**Title:** Preserve provider selection by separating rule evaluation and final selection
**Source:** [thegent/src/thegent/session/state.go:230]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10671]

**Title:** Preserve workflow progression by separating guard checks and execution
**Source:** [thegent/src/thegent/automation/workflow.go:259]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10672]

**Title:** Preserve hook reliability by separating registration from invocation
**Source:** [thegent/src/thegent/providers/registry.go:288]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10673]

**Title:** Preserve policy gating by separating matching and enforcement paths
**Source:** [thegent/src/thegent/queue/storage.go:317]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10674]

**Title:** Preserve queue scheduling by separating priority and execution
**Source:** [thegent/src/thegent/runner/runner.go:346]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10675]

**Title:** Preserve session consistency by separating state updates and persistence
**Source:** [thegent/src/thegent/policy/engine.go:375]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10676]

**Title:** Preserve sync integrity by separating diff generation and commit
**Source:** [thegent/src/thegent/observability/prometheus.go:404]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10677]

**Title:** Preserve observability by separating events from serialization
**Source:** [thegent/src/thegent/mcp/server.go:433]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10678]

**Title:** Preserve CLI dispatch by separating command parse and handler selection
**Source:** [thegent/src/thegent/commands/dispatch.go:462]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10679]

**Title:** Preserve error semantics by separating retry loops and terminal outcomes
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:491]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
