### [WL-10600]

**Title:** Preserve session lifecycle by separating transition and persistence writes
**Source:** [thegent/src/thegent/providers/registry.go:700]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10601]

**Title:** Preserve sync safety by separating detection and application
**Source:** [thegent/src/thegent/queue/storage.go:717]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10602]

**Title:** Preserve observability by separating metric producers from transport sink
**Source:** [thegent/src/thegent/runner/runner.go:734]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10603]

**Title:** Preserve runtime health by separating recoverable and terminal failures
**Source:** [thegent/src/thegent/policy/engine.go:751]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10604]

**Title:** Preserve hook pipeline by separating before and after handlers
**Source:** [thegent/src/thegent/observability/prometheus.go:768]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10605]

**Title:** Preserve session lifecycle by separating transition and persistence writes
**Source:** [thegent/src/thegent/mcp/server.go:785]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10606]

**Title:** Preserve sync safety by separating detection and application
**Source:** [thegent/src/thegent/commands/dispatch.go:802]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10607]

**Title:** Preserve observability by separating metric producers from transport sink
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:819]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10608]

**Title:** Preserve runtime health by separating recoverable and terminal failures
**Source:** [thegent/src/thegent/hooks/dispatcher.go:836]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10609]

**Title:** Preserve hook pipeline by separating before and after handlers
**Source:** [thegent/src/thegent/session/state.go:853]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
