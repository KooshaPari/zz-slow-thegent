### [WL-10020]

**Title:** Preserve CLI parsing by separating validation and execution branches
**Source:** [thegent/src/thegent/automation/workflow.go:790]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10021]

**Title:** Preserve workflow transitions by separating success and mitigation paths
**Source:** [thegent/src/thegent/mcp/server.go:803]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10022]

**Title:** Preserve policy compliance by separating checks and enforcement actions
**Source:** [thegent/src/thegent/providers/registry.go:816]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10023]

**Title:** Preserve error handling by separating recoverable and terminal flows
**Source:** [thegent/src/thegent/commands/dispatch.go:829]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10024]

**Title:** Preserve hook orchestration by separating pre and post dispatch paths
**Source:** [thegent/src/thegent/queue/storage.go:842]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10025]

**Title:** Preserve queue ordering by separating staging and drain phases
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:135]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10026]

**Title:** Preserve sync orchestration by separating source detection and apply
**Source:** [thegent/src/thegent/runner/runner.go:148]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10027]

**Title:** Preserve provider registry by separating lookup and selection stages
**Source:** [thegent/src/thegent/hooks/dispatcher.go:161]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10028]

**Title:** Preserve session state by separating transitions and persistence
**Source:** [thegent/src/thegent/policy/engine.go:174]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10029]

**Title:** Preserve observability by separating metric capture and emission
**Source:** [thegent/src/thegent/session/state.go:187]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
