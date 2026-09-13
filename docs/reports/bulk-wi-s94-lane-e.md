### [WL-10360]

**Title:** Preserve queue safety by separating buffer and worker scheduling
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:505]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10361]

**Title:** Preserve sync correctness by separating candidate enumeration and finalization
**Source:** [thegent/src/thegent/session/state.go:528]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10362]

**Title:** Preserve provider isolation by separating selection and transport bootstrap
**Source:** [thegent/src/thegent/providers/registry.go:551]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10363]

**Title:** Preserve policy clarity by separating rule parsing and action mapping
**Source:** [thegent/src/thegent/runner/runner.go:574]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10364]

**Title:** Preserve observability by separating metric producers and exporters
**Source:** [thegent/src/thegent/observability/prometheus.go:597]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10365]

**Title:** Preserve error semantics by separating recoverable and terminal branches
**Source:** [thegent/src/thegent/commands/dispatch.go:620]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10366]

**Title:** Preserve hook determinism by separating sync and async listeners
**Source:** [thegent/src/thegent/hooks/dispatcher.go:643]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10367]

**Title:** Preserve session continuity by separating state read and write boundaries
**Source:** [thegent/src/thegent/automation/workflow.go:666]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10368]

**Title:** Preserve CLI safety by separating command parse and action mapping
**Source:** [thegent/src/thegent/queue/storage.go:689]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10369]

**Title:** Preserve workflow integrity by separating precondition checks and execution
**Source:** [thegent/src/thegent/policy/engine.go:712]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
