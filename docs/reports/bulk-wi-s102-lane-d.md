### [WL-10750]

**Title:** Preserve policy enforcement by separating rule discovery and action execution
**Source:** [thegent/src/thegent/observability/prometheus.go:730]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10751]

**Title:** Preserve sync reliability by separating source scan and mutation apply
**Source:** [thegent/src/thegent/automation/workflow.go:747]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10752]

**Title:** Preserve runtime error behavior by separating recoverable and terminal branches
**Source:** [thegent/src/thegent/mcp/server.go:764]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10753]

**Title:** Preserve hook delivery by separating trigger evaluation and call sites
**Source:** [thegent/src/thegent/providers/registry.go:781]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10754]

**Title:** Preserve session lifecycle by separating claim transitions and persistence
**Source:** [thegent/src/thegent/commands/dispatch.go:798]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10755]

**Title:** Preserve CLI behavior by separating schema parse and command handling
**Source:** [thegent/src/thegent/queue/storage.go:815]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10756]

**Title:** Preserve orchestration determinism by separating plan and execution boundaries
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:832]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10757]

**Title:** Preserve queue throughput by separating intake and worker fanout
**Source:** [thegent/src/thegent/runner/runner.go:849]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10758]

**Title:** Preserve telemetry by separating metric collection and emitter lifecycle
**Source:** [thegent/src/thegent/hooks/dispatcher.go:866]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10759]

**Title:** Preserve provider selection by separating fallback and normal selection paths
**Source:** [thegent/src/thegent/policy/engine.go:263]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
