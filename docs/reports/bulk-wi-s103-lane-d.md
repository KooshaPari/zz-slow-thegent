### [WL-10800]

**Title:** Preserve policy enforcement by separating rule discovery and action execution
**Source:** [thegent/src/thegent/providers/registry.go:340]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10801]

**Title:** Preserve sync reliability by separating source scan and mutation apply
**Source:** [thegent/src/thegent/commands/dispatch.go:357]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10802]

**Title:** Preserve runtime error behavior by separating recoverable and terminal branches
**Source:** [thegent/src/thegent/queue/storage.go:374]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10803]

**Title:** Preserve hook delivery by separating trigger evaluation and call sites
**Source:** [thegent/src/thegent/integrations/gh_project_sync.py:391]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10804]

**Title:** Preserve session lifecycle by separating claim transitions and persistence
**Source:** [thegent/src/thegent/runner/runner.go:408]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10805]

**Title:** Preserve CLI behavior by separating schema parse and command handling
**Source:** [thegent/src/thegent/hooks/dispatcher.go:425]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10806]

**Title:** Preserve orchestration determinism by separating plan and execution boundaries
**Source:** [thegent/src/thegent/policy/engine.go:442]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10807]

**Title:** Preserve queue throughput by separating intake and worker fanout
**Source:** [thegent/src/thegent/session/state.go:459]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10808]

**Title:** Preserve telemetry by separating metric collection and emitter lifecycle
**Source:** [thegent/src/thegent/observability/prometheus.go:476]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.

### [WL-10809]

**Title:** Preserve provider selection by separating fallback and normal selection paths
**Source:** [thegent/src/thegent/automation/workflow.go:493]
\*\*Acceptance checklist:

- [ ] Separate parse and execution paths.
- [ ] Preserve current behavior on both happy and failure paths.
- [ ] Add regression tests around boundary conditions.
      **Notes:** Continuation artifact for high-volume work item stream.
