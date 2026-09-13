### [WL-10740]

**Title:** Preserve hook delivery by separating trigger evaluation and call sites
**Source:** [thegent/src/thegent/commands/dispatch.go:560]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10741]

**Title:** Preserve session lifecycle by separating claim transitions and persistence
**Source:** [thegent/src/thegent/queue/storage.go:577]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10742]

**Title:** Preserve CLI behavior by separating schema parse and command handling
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:594]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10743]

**Title:** Preserve orchestration determinism by separating plan and execution boundaries
**Source:** [thegent/src/thegent/runner/runner.go:611]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10744]

**Title:** Preserve queue throughput by separating intake and worker fanout
**Source:** [thegent/src/thegent/hooks/dispatcher.go:628]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10745]

**Title:** Preserve telemetry by separating metric collection and emitter lifecycle
**Source:** [thegent/src/thegent/policy/engine.go:645]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10746]

**Title:** Preserve provider selection by separating fallback and normal selection paths
**Source:** [thegent/src/thegent/session/state.go:662]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10747]

**Title:** Preserve policy enforcement by separating rule discovery and action execution
**Source:** [thegent/src/thegent/observability/prometheus.go:679]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10748]

**Title:** Preserve sync reliability by separating source scan and mutation apply
**Source:** [thegent/src/thegent/automation/workflow.go:696]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10749]

**Title:** Preserve runtime error behavior by separating recoverable and terminal branches
**Source:** [thegent/src/thegent/mcp/server.go:713]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
