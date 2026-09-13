### [WL-10110]

**Title:** Preserve session state by separating transitions and persistence
**Source:** [thegent/src/thegent/hooks/dispatcher.go:520]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10111]

**Title:** Preserve observability by separating metric capture and emission
**Source:** [thegent/src/thegent/policy/engine.go:533]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10112]

**Title:** Preserve CLI parsing by separating validation and execution branches
**Source:** [thegent/src/thegent/session/state.go:546]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10113]

**Title:** Preserve workflow transitions by separating success and mitigation paths
**Source:** [thegent/src/thegent/observability/prometheus.go:559]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10114]

**Title:** Preserve policy compliance by separating checks and enforcement actions
**Source:** [thegent/src/thegent/automation/workflow.go:572]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10115]

**Title:** Preserve error handling by separating recoverable and terminal flows
**Source:** [thegent/src/thegent/mcp/server.go:585]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10116]

**Title:** Preserve hook orchestration by separating pre and post dispatch paths
**Source:** [thegent/src/thegent/providers/registry.go:598]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10117]

**Title:** Preserve queue ordering by separating staging and drain phases
**Source:** [thegent/src/thegent/commands/dispatch.go:611]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10118]

**Title:** Preserve sync orchestration by separating source detection and apply
**Source:** [thegent/src/thegent/queue/storage.go:624]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10119]

**Title:** Preserve provider registry by separating lookup and selection stages
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:637]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
