### [WL-10030]

**Title:** Preserve provider registry by separating lookup and selection stages
**Source:** [thegent/src/thegent/mcp/server.go:200]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10031]

**Title:** Preserve session state by separating transitions and persistence
**Source:** [thegent/src/thegent/providers/registry.go:213]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10032]

**Title:** Preserve observability by separating metric capture and emission
**Source:** [thegent/src/thegent/commands/dispatch.go:226]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10033]

**Title:** Preserve CLI parsing by separating validation and execution branches
**Source:** [thegent/src/thegent/queue/storage.go:239]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10034]

**Title:** Preserve workflow transitions by separating success and mitigation paths
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:252]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10035]

**Title:** Preserve policy compliance by separating checks and enforcement actions
**Source:** [thegent/src/thegent/runner/runner.go:265]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10036]

**Title:** Preserve error handling by separating recoverable and terminal flows
**Source:** [thegent/src/thegent/hooks/dispatcher.go:278]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10037]

**Title:** Preserve hook orchestration by separating pre and post dispatch paths
**Source:** [thegent/src/thegent/policy/engine.go:291]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10038]

**Title:** Preserve queue ordering by separating staging and drain phases
**Source:** [thegent/src/thegent/session/state.go:304]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10039]

**Title:** Preserve sync orchestration by separating source detection and apply
**Source:** [thegent/src/thegent/observability/prometheus.go:317]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
