### [WL-10300]

**Title:** Preserve queue health by separating intake and processing throttles
**Source:** [thegent/src/thegent/hooks/dispatcher.go:260]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10301]

**Title:** Preserve observability by separating event ingestion and metric emission
**Source:** [thegent/src/thegent/observability/prometheus.go:279]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10302]

**Title:** Preserve hook control by separating pre and post execution branches
**Source:** [thegent/src/thegent/providers/registry.go:298]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10303]

**Title:** Preserve sync correctness by separating discovery and conflict resolution
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:317]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10304]

**Title:** Preserve CLI flow by separating argument parsing from action dispatch
**Source:** [thegent/src/thegent/policy/engine.go:336]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10305]

**Title:** Preserve queue health by separating intake and processing throttles
**Source:** [thegent/src/thegent/automation/workflow.go:355]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10306]

**Title:** Preserve observability by separating event ingestion and metric emission
**Source:** [thegent/src/thegent/commands/dispatch.go:374]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10307]

**Title:** Preserve hook control by separating pre and post execution branches
**Source:** [thegent/src/thegent/runner/runner.go:393]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10308]

**Title:** Preserve sync correctness by separating discovery and conflict resolution
**Source:** [thegent/src/thegent/session/state.go:412]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10309]

**Title:** Preserve CLI flow by separating argument parsing from action dispatch
**Source:** [thegent/src/thegent/mcp/server.go:431]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
