### [WL-8710]

**Title:** Preserve command validation by separating schema parse and validation routing
**Source:** [thegent/src/thegent/commands/validation.py:501]
**Acceptance checklist:**

- [ ] Separate command schema parse failures from validation routing failures.
- [ ] Preserve validation routing with schema fallback.
- [ ] Add tests for schema and routing branch handling.
      **Notes:** Improves command reliability under schema transitions.

### [WL-8711]

**Title:** Preserve sync payload persistence by separating payload parse and persistence queueing
**Source:** [thegent/src/thegent/sync/persistence.py:412]
**Acceptance checklist:**

- [ ] Separate sync payload parse failures from persistence queueing failures.
- [ ] Preserve queueing with parse fallback.
- [ ] Add tests for parse and queueing branches.
      **Notes:** Helps avoid payload-loss cascades in sync flows.

### [WL-8712]

**Title:** Preserve artifact annotation by separating annotation parse and annotation persistence
**Source:** [thegent/src/thegent/artifacts/annotation.py:589]
**Acceptance checklist:**

- [ ] Separate annotation parse failures from persistence failures.
- [ ] Preserve annotations with fallback payloads.
- [ ] Add tests for parse and persistence branches.
      **Notes:** Keeps annotation workflows functional under format changes.

### [WL-8713]

**Title:** Preserve queue health alerts by separating alert threshold parse and alert dispatch
**Source:** [thegent/src/thegent/alerts/queue_alert.py:378]
**Acceptance checklist:**

- [ ] Separate alert threshold parse failures from alert dispatch failures.
- [ ] Preserve dispatch with fallback threshold values.
- [ ] Add tests for threshold and dispatch branches.
      **Notes:** Improves operational signal stability under config noise.

### [WL-8714]

**Title:** Preserve artifact sync reconciliation by separating reconciliation signature parse and reconciliation action
**Source:** [thegent/src/thegent/artifacts/reconcile.py:412]
**Acceptance checklist:**

- [ ] Separate reconciliation signature parse failures from reconciliation action failures.
- [ ] Preserve action execution with signature fallback.
- [ ] Add tests for parse and action branches.
      **Notes:** Reduces sync inconsistencies during signature payload variation.

### [WL-8715]

**Title:** Preserve command queue cleanup by separating cleanup config parse and cleanup scheduling
**Source:** [thegent/src/thegent/commands/cleanup_scheduler.py:461]
**Acceptance checklist:**

- [ ] Separate cleanup config parse failures from scheduling failures.
- [ ] Preserve cleanup scheduling with default cleanup config.
- [ ] Add tests for config parse and scheduling branches.
      **Notes:** Prevents command queue buildup under config parse faults.

### [WL-8716]

**Title:** Preserve webhook dispatch by separating dispatch config parse and transport retry
**Source:** [thegent/src/thegent/webhooks/dispatch.py:523]
**Acceptance checklist:**

- [ ] Separate dispatch config parse failures from transport retry failures.
- [ ] Preserve transport retries with config fallback.
- [ ] Add tests for config parse and retry branches.
      **Notes:** Improves webhook resilience during config format drift.

### [WL-8717]

**Title:** Preserve policy audit by separating audit rule parse and audit write
**Source:** [thegent/src/thegent/policies/audit.py:412]
**Acceptance checklist:**

- [ ] Separate audit rule parse failures from audit write failures.
- [ ] Preserve audit records with raw rule fallback.
- [ ] Add tests for rule parse and write branches.
      **Notes:** Keeps policy audit trail usable despite rule formatting changes.

### [WL-8718]

**Title:** Preserve queue eventing by separating event parse and event fanout
**Source:** [thegent/src/thegent/queue/event_fanout.py:589]
**Acceptance checklist:**

- [ ] Separate queue event parse failures from fanout execution failures.
- [ ] Preserve fanout with parse fallback.
- [ ] Add tests for parse and fanout execution branches.
      **Notes:** Helps prevent event blackouts during parser instability.

### [WL-8719]

**Title:** Preserve artifact compression by separating compression chunk parse and compression stream start
**Source:** [thegent/src/thegent/artifacts/compression_stream.py:333]
**Acceptance checklist:**

- [ ] Separate compression chunk parse failures from compression stream start failures.
- [ ] Preserve stream start with conservative chunk fallback.
- [ ] Add tests for parse and stream-start branches.
      **Notes:** Improves large payload handling under chunk format anomalies.
