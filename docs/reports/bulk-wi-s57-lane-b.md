### [WL-8380]

**Title:** Preserve plugin hot reload by separating file diff computation and process signal
**Source:** [thegent/src/thegent/ui/plugin_hot_reload.py:355]
**Acceptance checklist:**

- [ ] Separate plugin diff calculation failures from process signaling failures.
- [ ] Preserve hot reload for unchanged diffs when signaling fails.
- [ ] Add tests for diff and signal branches.
      **Notes:** Helps keep development loop responsive despite transient process issues.

### [WL-8381]

**Title:** Preserve command routing by separating route template parse and executor registration
**Source:** [thegent/src/thegent/routing/commands.py:448]
**Acceptance checklist:**

- [ ] Separate command route template parse failures from executor registration failures.
- [ ] Preserve default routes when registration fails.
- [ ] Add tests for template parse and registration errors.
      **Notes:** Keeps control-plane stable when one route pattern regresses.

### [WL-8382]

**Title:** Preserve artifact metadata by separating metadata extraction and index update
**Source:** [thegent/src/thegent/artifacts/metadata.py:401]
**Acceptance checklist:**

- [ ] Separate metadata extraction failures from index update failures.
- [ ] Keep artifacts addressable when index update is delayed.
- [ ] Add tests for extraction and update branches.
      **Notes:** Improves discoverability with partial metadata corruption.

### [WL-8383]

**Title:** Preserve migration logging by separating event capture and persistence flush
**Source:** [thegent/src/thegent/migrations/logging.py:278]
**Acceptance checklist:**

- [ ] Separate migration event capture failures from persistence flush failures.
- [ ] Preserve event capture queue on flush failures.
- [ ] Add tests for capture and flush branches.
      **Notes:** Improves auditability when one persistence path is under load.

### [WL-8384]

**Title:** Preserve queue balancing by separating worker load parse and rebalance scheduling
**Source:** [thegent/src/thegent/queue/balancer.py:391]
**Acceptance checklist:**

- [ ] Separate worker load parse failures from rebalance scheduler failures.
- [ ] Preserve current allocation for load parse errors.
- [ ] Add tests for parse and scheduling branches.
      **Notes:** Keeps load distribution sane during telemetry noise.

### [WL-8385]

**Title:** Preserve tokenization pipeline by separating input normalization and feature extraction
**Source:** [thegent/src/thegent/nlp/tokenizer.py:511]
**Acceptance checklist:**

- [ ] Separate token input normalization failures from feature extraction failures.
- [ ] Preserve token output with fallback normalization.
- [ ] Add tests for input normalization and extraction faults.
      **Notes:** Improves NLP pipeline availability under language drift.

### [WL-8386]

**Title:** Preserve session audit trails by separating event flattening and sink formatting
**Source:** [thegent/src/thegent/audit/trail.py:337]
**Acceptance checklist:**

- [ ] Separate event flattening failures from sink formatting failures.
- [ ] Preserve audit storage semantics on formatting fallbacks.
- [ ] Add tests for flattening and formatting branches.
      **Notes:** Keeps audit continuity across output-format changes.

### [WL-8387]

**Title:** Preserve deployment status by separating status collector parse and aggregation
**Source:** [thegent/src/thegent/deploy/status.py:445]
**Acceptance checklist:**

- [ ] Separate status payload parse failures from aggregation failures.
- [ ] Preserve status output when aggregation fails.
- [ ] Add tests for parse and aggregation failures.
      **Notes:** Helps operators stay informed during partial status degradations.

### [WL-8388]

**Title:** Preserve policy rule evaluation by separating expression parse and evaluator initialization
**Source:** [thegent/src/thegent/policies/eval_engine.py:592]
**Acceptance checklist:**

- [ ] Split expression parsing failures from evaluator initialization failures.
- [ ] Keep simple fallback policy when parser branch fails.
- [ ] Add tests for parse and initialization branches.
      **Notes:** Reduces authorization outages due to one malformed expression.

### [WL-8389]

**Title:** Preserve sync checkpointing by separating diff generation and checkpoint write batching
**Source:** [thegent/src/thegent/sync/checkpoint.py:529]
**Acceptance checklist:**

- [ ] Separate checkpoint diff generation from batch write operations.
- [ ] Keep incremental checkpoint writes available on diff failures.
- [ ] Add tests for diff and batching failures.
      **Notes:** Improves sync reliability with large mutable state.
