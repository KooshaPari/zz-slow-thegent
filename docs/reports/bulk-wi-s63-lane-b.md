### [WL-8680]

**Title:** Preserve notification batching by separating notification envelope parse and batch dispatch
**Source:** [thegent/src/thegent/notifications/batcher.py:412]
**Acceptance checklist:**

- [ ] Separate notification envelope parse failures from batch dispatch failures.
- [ ] Preserve dispatch behavior with envelope fallback.
- [ ] Add tests for parse and dispatch branches.
      **Notes:** Improves notification throughput under payload variations.

### [WL-8681]

**Title:** Preserve artifact hash validation by separating hash metadata parse and hash validation service
**Source:** [thegent/src/thegent/artifacts/hash_validator.py:523]
**Acceptance checklist:**

- [ ] Separate hash metadata parse failures from validation service failures.
- [ ] Preserve validation pipeline with safe hash fallback.
- [ ] Add tests for parse and service branches.
      **Notes:** Helps maintain integrity checks amid metadata schema changes.

### [WL-8682]

**Title:** Preserve command routing by separating route parse and route invocation
**Source:** [thegent/src/thegent/commands/route_invoke.py:333]
**Acceptance checklist:**

- [ ] Separate route parse failures from route invocation failures.
- [ ] Preserve fallback command invocation on route parse errors.
- [ ] Add tests for route parse and invocation branches.
      **Notes:** Keeps command routing functional under route schema churn.

### [WL-8683]

**Title:** Preserve plugin lifecycle by separating plugin lifecycle parse and lifecycle command apply
**Source:** [thegent/src/thegent/plugins/lifecycle.py:477]
**Acceptance checklist:**

- [ ] Separate plugin lifecycle parse failures from lifecycle apply failures.
- [ ] Preserve lifecycle state with parse fallback.
- [ ] Add tests for parse and apply branches.
      **Notes:** Prevents plugin disablement from lifecycle descriptor issues.

### [WL-8684]

**Title:** Preserve queue checkpoint recovery by separating checkpoint format parse and recovery resume
**Source:** [thegent/src/thegent/queue/checkpoint_recovery.py:401]
**Acceptance checklist:**

- [ ] Separate checkpoint format parse failures from recovery resume failures.
- [ ] Preserve resume path with conservative checkpoint fallback.
- [ ] Add tests for format parse and resume branches.
      **Notes:** Improves recovery reliability across checkpoint format evolution.

### [WL-8685]

**Title:** Preserve session policy checks by separating policy extraction and policy evaluation
**Source:** [thegent/src/thegent/session/policy_check.py:589]
**Acceptance checklist:**

- [ ] Separate policy extraction failures from policy evaluation failures.
- [ ] Preserve policy checks with extraction fallback.
- [ ] Add tests for extraction and evaluation branches.
      **Notes:** Keeps session controls active despite policy schema drift.

### [WL-8686]

**Title:** Preserve artifact retention policy by separating policy parse and retention execution
**Source:** [thegent/src/thegent/artifacts/retention_policy_runner.py:458]
**Acceptance checklist:**

- [ ] Separate retention policy parse failures from retention execution failures.
- [ ] Preserve execution with safer retention defaults.
- [ ] Add tests for parse and execution branch failures.
      **Notes:** Reduces accidental retention mismatches during config changes.

### [WL-8687]

**Title:** Preserve API telemetry transport by separating telemetry format parse and transport batch
**Source:** [thegent/src/thegent/api/telemetry_transport.py:522]
**Acceptance checklist:**

- [ ] Separate telemetry format parse failures from transport batching failures.
- [ ] Preserve transport batching with format fallback.
- [ ] Add tests for parse and batch branches.
      **Notes:** Maintains telemetry flow when payload format changes.

### [WL-8688]

**Title:** Preserve workflow scheduler by separating schedule window parse and scheduler registration
**Source:** [thegent/src/thegent/workflow/scheduler_registration.py:351]
**Acceptance checklist:**

- [ ] Separate schedule window parse failures from scheduler registration failures.
- [ ] Preserve scheduler registration with fallback windows.
- [ ] Add tests for parse and registration branches.
      **Notes:** Improves deterministic scheduling under window syntax issues.

### [WL-8689]

**Title:** Preserve artifact sync state by separating sync state parse and sync commit
**Source:** [thegent/src/thegent/artifacts/sync_state.py:501]
**Acceptance checklist:**

- [ ] Separate sync state parse failures from sync commit failures.
- [ ] Preserve commit attempts with fallback sync state.
- [ ] Add tests for parse and commit branches.
      **Notes:** Prevents sync stalling from state schema drift.
