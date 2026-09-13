### [WL-10730]

**Title:** Preserve orchestration determinism by separating plan and execution boundaries
**Source:** [thegent/src/thegent/hooks/dispatcher.go:390]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10731]

**Title:** Preserve queue throughput by separating intake and worker fanout
**Source:** [thegent/src/thegent/policy/engine.go:407]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10732]

**Title:** Preserve telemetry by separating metric collection and emitter lifecycle
**Source:** [thegent/src/thegent/session/state.go:424]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10733]

**Title:** Preserve provider selection by separating fallback and normal selection paths
**Source:** [thegent/src/thegent/observability/prometheus.go:441]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10734]

**Title:** Preserve policy enforcement by separating rule discovery and action execution
**Source:** [thegent/src/thegent/automation/workflow.go:458]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10735]

**Title:** Preserve sync reliability by separating source scan and mutation apply
**Source:** [thegent/src/thegent/mcp/server.go:475]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10736]

**Title:** Preserve runtime error behavior by separating recoverable and terminal branches
**Source:** [thegent/src/thegent/providers/registry.go:492]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10737]

**Title:** Preserve hook delivery by separating trigger evaluation and call sites
**Source:** [thegent/src/thegent/commands/dispatch.go:509]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10738]

**Title:** Preserve session lifecycle by separating claim transitions and persistence
**Source:** [thegent/src/thegent/queue/storage.go:526]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10739]

**Title:** Preserve CLI behavior by separating schema parse and command handling
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:543]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
