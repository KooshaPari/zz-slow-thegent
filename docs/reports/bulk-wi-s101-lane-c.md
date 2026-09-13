### [WL-10690]

**Title:** Preserve hook reliability by separating registration from invocation
**Source:** [thegent/src/thegent/policy/engine.go:190]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10691]

**Title:** Preserve session consistency by separating state updates and persistence
**Source:** [thegent/src/thegent/observability/prometheus.go:219]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10692]

**Title:** Preserve CLI dispatch by separating command parse and handler selection
**Source:** [thegent/src/thegent/mcp/server.go:248]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10693]

**Title:** Preserve workflow progression by separating guard checks and execution
**Source:** [thegent/src/thegent/commands/dispatch.go:277]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10694]

**Title:** Preserve queue scheduling by separating priority and execution
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:306]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10695]

**Title:** Preserve observability by separating events from serialization
**Source:** [thegent/src/thegent/hooks/dispatcher.go:335]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10696]

**Title:** Preserve provider selection by separating rule evaluation and final selection
**Source:** [thegent/src/thegent/session/state.go:364]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10697]

**Title:** Preserve policy gating by separating matching and enforcement paths
**Source:** [thegent/src/thegent/automation/workflow.go:393]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10698]

**Title:** Preserve sync integrity by separating diff generation and commit
**Source:** [thegent/src/thegent/providers/registry.go:422]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10699]

**Title:** Preserve error semantics by separating retry loops and terminal outcomes
**Source:** [thegent/src/thegent/queue/storage.go:451]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
