### [WL-10090]

**Title:** Preserve hook orchestration by separating pre and post dispatch paths
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:260]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10091]

**Title:** Preserve queue ordering by separating staging and drain phases
**Source:** [thegent/src/thegent/runner/runner.go:273]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10092]

**Title:** Preserve sync orchestration by separating source detection and apply
**Source:** [thegent/src/thegent/hooks/dispatcher.go:286]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10093]

**Title:** Preserve provider registry by separating lookup and selection stages
**Source:** [thegent/src/thegent/policy/engine.go:299]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10094]

**Title:** Preserve session state by separating transitions and persistence
**Source:** [thegent/src/thegent/session/state.go:312]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10095]

**Title:** Preserve observability by separating metric capture and emission
**Source:** [thegent/src/thegent/observability/prometheus.go:325]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10096]

**Title:** Preserve CLI parsing by separating validation and execution branches
**Source:** [thegent/src/thegent/automation/workflow.go:338]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10097]

**Title:** Preserve workflow transitions by separating success and mitigation paths
**Source:** [thegent/src/thegent/mcp/server.go:351]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10098]

**Title:** Preserve policy compliance by separating checks and enforcement actions
**Source:** [thegent/src/thegent/providers/registry.go:364]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10099]

**Title:** Preserve error handling by separating recoverable and terminal flows
**Source:** [thegent/src/thegent/commands/dispatch.go:377]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
