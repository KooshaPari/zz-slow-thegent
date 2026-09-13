### [WL-10080]

**Title:** Preserve provider registry by separating lookup and selection stages
**Source:** [thegent/src/thegent/queue/storage.go:130]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10081]

**Title:** Preserve session state by separating transitions and persistence
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:143]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10082]

**Title:** Preserve observability by separating metric capture and emission
**Source:** [thegent/src/thegent/runner/runner.go:156]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10083]

**Title:** Preserve CLI parsing by separating validation and execution branches
**Source:** [thegent/src/thegent/hooks/dispatcher.go:169]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10084]

**Title:** Preserve workflow transitions by separating success and mitigation paths
**Source:** [thegent/src/thegent/policy/engine.go:182]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10085]

**Title:** Preserve policy compliance by separating checks and enforcement actions
**Source:** [thegent/src/thegent/session/state.go:195]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10086]

**Title:** Preserve error handling by separating recoverable and terminal flows
**Source:** [thegent/src/thegent/observability/prometheus.go:208]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10087]

**Title:** Preserve hook orchestration by separating pre and post dispatch paths
**Source:** [thegent/src/thegent/automation/workflow.go:221]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10088]

**Title:** Preserve queue ordering by separating staging and drain phases
**Source:** [thegent/src/thegent/mcp/server.go:234]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10089]

**Title:** Preserve sync orchestration by separating source detection and apply
**Source:** [thegent/src/thegent/providers/registry.go:247]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
