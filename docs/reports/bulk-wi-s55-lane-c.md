### [WL-8290]

**Title:** Preserve replay output while separating replay decode and execution failures
**Source:** [thegent/src/thegent/execution.py:638]
**Acceptance checklist:**

- [ ] Split replay record decode failures from execution call failures.
- [ ] Keep replay progress reporting for recoverable decode failures.
- [ ] Add tests for decode and execution branches.
      **Notes:** Makes replay diagnostics much more actionable.

### [WL-8291]

**Title:** Preserve queue scale evaluation by separating data fetch and evaluator failures
**Source:** [thegent/src/thegent/queue/scaler.py:302]
**Acceptance checklist:**

- [ ] Separate queue data fetch failures from evaluator logic failures.
- [ ] Preserve default scale behavior when fetch fails.
- [ ] Add tests for fetch and evaluation branches.
      **Notes:** Prevents mis-scaling during transient data provider faults.

### [WL-8292]

**Title:** Preserve artifact sync by separating checksum validation and upload send failures
**Source:** [thegent/src/thegent/artifacts/uploader.py:482]
**Acceptance checklist:**

- [ ] Distinguish checksum mismatch failures from upload send failures.
- [ ] Keep retry semantics for send failures.
- [ ] Add tests for checksum mismatch and send failures.
      **Notes:** Avoids unnecessary retries on deterministic checksum mismatches.

### [WL-8293]

**Title:** Preserve UI plugin loader fallback while separating schema and runtime validation
**Source:** [thegent/src/thegent/ui/plugin_loader.py:468]
**Acceptance checklist:**

- [ ] Separate plugin manifest schema validation from runtime plugin validation.
- [ ] Keep fallback plugin list path for schema failures.
- [ ] Add tests for schema and runtime validation failures.
      **Notes:** Prevents one bad plugin from affecting entire UI.

### [WL-8294]

**Title:** Preserve retry engine metrics by separating telemetry and strategy branches
**Source:** [thegent/src/thegent/retry/strategy.py:312]
**Acceptance checklist:**

- [ ] Separate telemetry emission failures from strategy calculation failures.
- [ ] Keep strategy decisions stable when telemetry fails.
- [ ] Add tests for telemetry and strategy branches.
      **Notes:** Keeps retry logic deterministic under observability issues.

### [WL-8295]

**Title:** Preserve bootstrap flow by separating dependency graph and runtime init failures
**Source:** [thegent/src/thegent/session/bootstrap.py:424]
**Acceptance checklist:**

- [ ] Distinguish dependency graph resolution failures from runtime initialization failures.
- [ ] Preserve existing startup contract when graph resolution fails non-fatally.
- [ ] Add tests for both failure categories.
      **Notes:** Improves reliability and root-cause visibility.

### [WL-8296]

**Title:** Preserve shell completion reliability with separate parser and resolver error paths
**Source:** [thegent/src/thegent/shell_cli.py:882]
**Acceptance checklist:**

- [ ] Separate completion grammar parse failures from completion resolver failures.
- [ ] Keep completion degraded output behavior unchanged.
- [ ] Add tests for parser and resolver failure cases.
      **Notes:** Reduces noise from one malformed completion interaction.

### [WL-8297]

**Title:** Preserve artifact retention dry-run safety by separating dry-run validation and execution
**Source:** [thegent/src/thegent/artifacts/retention.py:430]
**Acceptance checklist:**

- [ ] Split dry-run flag validation failures from actual execution errors.
- [ ] Preserve dry-run output with no side effects.
- [ ] Add tests for dry-run validation and execution exceptions.
      **Notes:** Prevents accidental destructive runs under incorrect flags.

### [WL-8298]

**Title:** Preserve mesh control stability by separating broadcast and ack failures
**Source:** [thegent/src/thegent/mesh/control.py:632]
**Acceptance checklist:**

- [ ] Separate broadcast send failures from acknowledgement handling failures.
- [ ] Preserve control-plane fallback on ack misses.
- [ ] Add tests for broadcast and ack branches.
      **Notes:** Clarifies mesh reliability in distributed conditions.

### [WL-8299]

**Title:** Preserve scheduler reconciliation metrics while separating calculation and persistence
**Source:** [thegent/src/thegent/orchestration/scheduler.py:624]
**Acceptance checklist:**

- [ ] Split reconciliation calculation failures from persistence write failures.
- [ ] Keep reconciliation state machine consistent on persistence errors.
- [ ] Add tests for calculation and persistence branches.
      **Notes:** Improves confidence in scheduler health metrics.
