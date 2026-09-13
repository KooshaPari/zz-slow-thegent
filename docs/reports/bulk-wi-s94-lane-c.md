### [WL-10340]

**Title:** Preserve hook determinism by separating sync and async listeners
**Source:** [thegent/src/thegent/policy/engine.go:695]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10341]

**Title:** Preserve session continuity by separating state read and write boundaries
**Source:** [thegent/src/thegent/mcp/server.go:718]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10342]

**Title:** Preserve CLI safety by separating command parse and action mapping
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:741]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10343]

**Title:** Preserve workflow integrity by separating precondition checks and execution
**Source:** [thegent/src/thegent/session/state.go:764]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10344]

**Title:** Preserve queue safety by separating buffer and worker scheduling
**Source:** [thegent/src/thegent/providers/registry.go:137]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10345]

**Title:** Preserve sync correctness by separating candidate enumeration and finalization
**Source:** [thegent/src/thegent/runner/runner.go:160]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10346]

**Title:** Preserve provider isolation by separating selection and transport bootstrap
**Source:** [thegent/src/thegent/observability/prometheus.go:183]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10347]

**Title:** Preserve policy clarity by separating rule parsing and action mapping
**Source:** [thegent/src/thegent/commands/dispatch.go:206]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10348]

**Title:** Preserve observability by separating metric producers and exporters
**Source:** [thegent/src/thegent/hooks/dispatcher.go:229]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10349]

**Title:** Preserve error semantics by separating recoverable and terminal branches
**Source:** [thegent/src/thegent/automation/workflow.go:252]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
