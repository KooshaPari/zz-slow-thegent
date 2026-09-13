### [WL-10470]

**Title:** Preserve dispatch safety by separating parse and execute boundaries
**Source:** [thegent/src/thegent/automation/workflow.go:520]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10471]

**Title:** Preserve governance compliance by separating evaluation and action phases
**Source:** [thegent/src/thegent/policy/engine.go:410]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10472]

**Title:** Preserve queue throughput by separating intake and worker scheduling
**Source:** [thegent/src/thegent/queue/storage.go:210]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10473]

**Title:** Preserve hook behavior by separating pre and post processing branches
**Source:** [thegent/src/thegent/hooks/dispatcher.go:310]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10474]

**Title:** Preserve provider integrity by separating registry and transport setup
**Source:** [thegent/src/thegent/providers/registry.go:188]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10475]

**Title:** Preserve session state by separating claim transitions and persistence
**Source:** [thegent/src/thegent/session/state.go:305]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10476]

**Title:** Preserve sync reliability by separating source discovery and reconciliation
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:145]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10477]

**Title:** Preserve CLI behavior by separating parse and routing branches
**Source:** [thegent/src/thegent/runner/runner.go:460]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10478]

**Title:** Preserve observability by separating collection and emission phases
**Source:** [thegent/src/thegent/observability/prometheus.go:88]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10479]

**Title:** Preserve command flow by separating validation and execution
**Source:** [thegent/src/thegent/commands/dispatch.go:290]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
