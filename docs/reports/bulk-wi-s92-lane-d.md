### [WL-10250]

**Title:** Preserve queue health by separating intake and processing throttles
**Source:** [thegent/src/thegent/commands/dispatch.go:610]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10251]

**Title:** Preserve observability by separating event ingestion and metric emission
**Source:** [thegent/src/thegent/runner/runner.go:629]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10252]

**Title:** Preserve hook control by separating pre and post execution branches
**Source:** [thegent/src/thegent/session/state.go:648]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10253]

**Title:** Preserve sync correctness by separating discovery and conflict resolution
**Source:** [thegent/src/thegent/mcp/server.go:667]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10254]

**Title:** Preserve CLI flow by separating argument parsing from action dispatch
**Source:** [thegent/src/thegent/queue/storage.go:686]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10255]

**Title:** Preserve queue health by separating intake and processing throttles
**Source:** [thegent/src/thegent/hooks/dispatcher.go:705]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10256]

**Title:** Preserve observability by separating event ingestion and metric emission
**Source:** [thegent/src/thegent/observability/prometheus.go:724]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10257]

**Title:** Preserve hook control by separating pre and post execution branches
**Source:** [thegent/src/thegent/providers/registry.go:743]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10258]

**Title:** Preserve sync correctness by separating discovery and conflict resolution
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:762]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10259]

**Title:** Preserve CLI flow by separating argument parsing from action dispatch
**Source:** [thegent/src/thegent/policy/engine.go:781]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
