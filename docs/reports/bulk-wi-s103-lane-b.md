### [WL-10780]

**Title:** Preserve orchestration determinism by separating plan and execution boundaries
**Source:** [thegent/src/thegent/observability/prometheus.go:620]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10781]

**Title:** Preserve queue throughput by separating intake and worker fanout
**Source:** [thegent/src/thegent/automation/workflow.go:637]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10782]

**Title:** Preserve telemetry by separating metric collection and emitter lifecycle
**Source:** [thegent/src/thegent/mcp/server.go:654]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10783]

**Title:** Preserve provider selection by separating fallback and normal selection paths
**Source:** [thegent/src/thegent/providers/registry.go:671]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10784]

**Title:** Preserve policy enforcement by separating rule discovery and action execution
**Source:** [thegent/src/thegent/commands/dispatch.go:688]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10785]

**Title:** Preserve sync reliability by separating source scan and mutation apply
**Source:** [thegent/src/thegent/queue/storage.go:705]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10786]

**Title:** Preserve runtime error behavior by separating recoverable and terminal branches
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:722]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10787]

**Title:** Preserve hook delivery by separating trigger evaluation and call sites
**Source:** [thegent/src/thegent/runner/runner.go:739]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10788]

**Title:** Preserve session lifecycle by separating claim transitions and persistence
**Source:** [thegent/src/thegent/hooks/dispatcher.go:756]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10789]

**Title:** Preserve CLI behavior by separating schema parse and command handling
**Source:** [thegent/src/thegent/policy/engine.go:773]
\*\*Acceptance checklist:

- [x] Separate parse and execution paths.
- [x] Preserve current behavior on both happy and failure paths.
- [x] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
