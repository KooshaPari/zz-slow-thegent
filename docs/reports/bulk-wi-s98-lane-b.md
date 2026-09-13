### [WL-10530]

**Title:** Preserve hook pipeline by separating before and after handlers
**Source:** [thegent/src/thegent/hooks/dispatcher.go:750]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10531]

**Title:** Preserve session lifecycle by separating transition and persistence writes
**Source:** [thegent/src/thegent/session/state.go:767]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10532]

**Title:** Preserve sync safety by separating detection and application
**Source:** [thegent/src/thegent/automation/workflow.go:784]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10533]

**Title:** Preserve observability by separating metric producers from transport sink
**Source:** [thegent/src/thegent/providers/registry.go:801]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10534]

**Title:** Preserve runtime health by separating recoverable and terminal failures
**Source:** [thegent/src/thegent/queue/storage.go:818]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10535]

**Title:** Preserve hook pipeline by separating before and after handlers
**Source:** [thegent/src/thegent/runner/runner.go:835]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10536]

**Title:** Preserve session lifecycle by separating transition and persistence writes
**Source:** [thegent/src/thegent/policy/engine.go:852]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10537]

**Title:** Preserve sync safety by separating detection and application
**Source:** [thegent/src/thegent/observability/prometheus.go:869]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10538]

**Title:** Preserve observability by separating metric producers from transport sink
**Source:** [thegent/src/thegent/mcp/server.go:886]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10539]

**Title:** Preserve runtime health by separating recoverable and terminal failures
**Source:** [thegent/src/thegent/commands/dispatch.go:903]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
