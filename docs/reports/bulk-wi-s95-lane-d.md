### [WL-10400]

**Title:** Preserve policy clarity by separating rule parsing and action mapping
**Source:** [thegent/src/thegent/automation/workflow.go:125]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10401]

**Title:** Preserve observability by separating metric producers and exporters
**Source:** [thegent/src/thegent/queue/storage.go:148]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10402]

**Title:** Preserve error semantics by separating recoverable and terminal branches
**Source:** [thegent/src/thegent/policy/engine.go:171]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10403]

**Title:** Preserve hook determinism by separating sync and async listeners
**Source:** [thegent/src/thegent/mcp/server.go:194]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10404]

**Title:** Preserve session continuity by separating state read and write boundaries
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:217]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10405]

**Title:** Preserve CLI safety by separating command parse and action mapping
**Source:** [thegent/src/thegent/session/state.go:240]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10406]

**Title:** Preserve workflow integrity by separating precondition checks and execution
**Source:** [thegent/src/thegent/providers/registry.go:263]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10407]

**Title:** Preserve queue safety by separating buffer and worker scheduling
**Source:** [thegent/src/thegent/runner/runner.go:286]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10408]

**Title:** Preserve sync correctness by separating candidate enumeration and finalization
**Source:** [thegent/src/thegent/observability/prometheus.go:309]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10409]

**Title:** Preserve provider isolation by separating selection and transport bootstrap
**Source:** [thegent/src/thegent/commands/dispatch.go:332]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
