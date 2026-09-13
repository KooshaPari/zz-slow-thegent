### [WL-10330]

**Title:** Preserve workflow integrity by separating precondition checks and execution
**Source:** [thegent/src/thegent/queue/storage.go:465]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10331]

**Title:** Preserve queue safety by separating buffer and worker scheduling
**Source:** [thegent/src/thegent/policy/engine.go:488]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10332]

**Title:** Preserve sync correctness by separating candidate enumeration and finalization
**Source:** [thegent/src/thegent/mcp/server.go:511]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10333]

**Title:** Preserve provider isolation by separating selection and transport bootstrap
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:534]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10334]

**Title:** Preserve policy clarity by separating rule parsing and action mapping
**Source:** [thegent/src/thegent/session/state.go:557]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10335]

**Title:** Preserve observability by separating metric producers and exporters
**Source:** [thegent/src/thegent/providers/registry.go:580]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10336]

**Title:** Preserve error semantics by separating recoverable and terminal branches
**Source:** [thegent/src/thegent/runner/runner.go:603]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10337]

**Title:** Preserve hook determinism by separating sync and async listeners
**Source:** [thegent/src/thegent/observability/prometheus.go:626]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10338]

**Title:** Preserve session continuity by separating state read and write boundaries
**Source:** [thegent/src/thegent/commands/dispatch.go:649]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10339]

**Title:** Preserve CLI safety by separating command parse and action mapping
**Source:** [thegent/src/thegent/hooks/dispatcher.go:672]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
