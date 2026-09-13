### [WL-10390]

**Title:** Preserve hook determinism by separating sync and async listeners
**Source:** [thegent/src/thegent/hooks/dispatcher.go:545]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10391]

**Title:** Preserve session continuity by separating state read and write boundaries
**Source:** [thegent/src/thegent/automation/workflow.go:568]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10392]

**Title:** Preserve CLI safety by separating command parse and action mapping
**Source:** [thegent/src/thegent/queue/storage.go:591]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10393]

**Title:** Preserve workflow integrity by separating precondition checks and execution
**Source:** [thegent/src/thegent/policy/engine.go:614]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10394]

**Title:** Preserve queue safety by separating buffer and worker scheduling
**Source:** [thegent/src/thegent/mcp/server.go:637]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10395]

**Title:** Preserve sync correctness by separating candidate enumeration and finalization
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:660]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10396]

**Title:** Preserve provider isolation by separating selection and transport bootstrap
**Source:** [thegent/src/thegent/session/state.go:683]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10397]

**Title:** Preserve policy clarity by separating rule parsing and action mapping
**Source:** [thegent/src/thegent/providers/registry.go:706]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10398]

**Title:** Preserve observability by separating metric producers and exporters
**Source:** [thegent/src/thegent/runner/runner.go:729]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10399]

**Title:** Preserve error semantics by separating recoverable and terminal branches
**Source:** [thegent/src/thegent/observability/prometheus.go:752]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
