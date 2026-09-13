### [WL-10760]

**Title:** Preserve queue throughput by separating intake and worker fanout
**Source:** [thegent/src/thegent/runner/runner.go:280]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10761]

**Title:** Preserve telemetry by separating metric collection and emitter lifecycle
**Source:** [thegent/src/thegent/hooks/dispatcher.go:297]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10762]

**Title:** Preserve provider selection by separating fallback and normal selection paths
**Source:** [thegent/src/thegent/policy/engine.go:314]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10763]

**Title:** Preserve policy enforcement by separating rule discovery and action execution
**Source:** [thegent/src/thegent/session/state.go:331]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10764]

**Title:** Preserve sync reliability by separating source scan and mutation apply
**Source:** [thegent/src/thegent/observability/prometheus.go:348]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10765]

**Title:** Preserve runtime error behavior by separating recoverable and terminal branches
**Source:** [thegent/src/thegent/automation/workflow.go:365]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10766]

**Title:** Preserve hook delivery by separating trigger evaluation and call sites
**Source:** [thegent/src/thegent/mcp/server.go:382]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10767]

**Title:** Preserve session lifecycle by separating claim transitions and persistence
**Source:** [thegent/src/thegent/providers/registry.go:399]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10768]

**Title:** Preserve CLI behavior by separating schema parse and command handling
**Source:** [thegent/src/thegent/commands/dispatch.go:416]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10769]

**Title:** Preserve orchestration determinism by separating plan and execution boundaries
**Source:** [thegent/src/thegent/queue/storage.go:433]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
