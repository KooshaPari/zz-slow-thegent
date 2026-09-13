### [WL-8420]

**Title:** Preserve session registry operations by separating JSON parse and persistence updates
**Source:** [thegent/src/thegent/session/registry.py:332]
**Acceptance checklist:**

- [ ] Separate decode/parsing failures from persistence update failures.
- [ ] Preserve in-memory registry consistency on persistence errors.
- [ ] Add tests for parse and persistence branches.
      **Notes:** Improves registry resilience under mixed storage conditions.

### [WL-8421]

**Title:** Preserve connector sync handling by separating manifest diff and patch application
**Source:** [thegent/src/thegent/sync/connector.py:428]
**Acceptance checklist:**

- [ ] Distinguish connector manifest diff computation from patch application failures.
- [ ] Preserve already-applied sync states when patching fails.
- [ ] Add tests for diff and patch branch errors.
      **Notes:** Reduces partial-sync rollback risk under transient connector failures.

### [WL-8422]

**Title:** Preserve CLI auto-recovery by separating config reload and cache reset
**Source:** [thegent/src/thegent/cli/recovery.py:267]
**Acceptance checklist:**

- [ ] Separate config reload failures from command cache reset failures.
- [ ] Keep command cache stable on reload faults.
- [ ] Add tests for reload and reset branches.
      **Notes:** Makes recovery path robust to one-off config regressions.

### [WL-8423]

**Title:** Preserve artifact upload pipeline by separating stream split and multipart chunking
**Source:** [thegent/src/thegent/artifacts/upload.py:522]
**Acceptance checklist:**

- [ ] Separate stream split failures from chunk scheduler failures.
- [ ] Preserve upload fallback on chunking branch errors.
- [ ] Add tests for stream split and chunking branches.
      **Notes:** Helps avoid full upload aborts when one segmentation step fails.

### [WL-8424]

**Title:** Preserve event ingest by separating event schema parse and enrichment stages
**Source:** [thegent/src/thegent/events/ingest.py:364]
**Acceptance checklist:**

- [ ] Separate schema parse failures from metadata enrichment failures.
- [ ] Keep ingest queueing when enrichment is delayed.
- [ ] Add tests for parse-only and enrichment-only failures.
      **Notes:** Improves event throughput under partial enrichment outages.

### [WL-8425]

**Title:** Preserve command dispatch by separating dry-run validation and execution planning
**Source:** [thegent/src/thegent/commands/dispatch.py:389]
**Acceptance checklist:**

- [ ] Separate dry-run validation failures from execution plan generation failures.
- [ ] Keep execution planning available for non-blocking dry-runs.
- [ ] Add tests for validation and planning branches.
      **Notes:** Keeps operator workflows usable during validation false positives.

### [WL-8426]

**Title:** Preserve workstream snapshots by separating serialization and checksum generation
**Source:** [thegent/src/thegent/workstream/snapshot.py:451]
**Acceptance checklist:**

- [ ] Distinguish snapshot serialization failures from checksum mismatches.
- [ ] Preserve snapshot writes with checksum fallback.
- [ ] Add tests for both branch outcomes.
      **Notes:** Improves recoverability for snapshot persistence.

### [WL-8427]

**Title:** Preserve route matching by separating URL normalization and matcher compilation
**Source:** [thegent/src/thegent/routing/url_match.py:286]
**Acceptance checklist:**

- [ ] Separate URL normalization failures from matcher compile failures.
- [ ] Preserve route matching on compile fallback behavior.
- [ ] Add tests for normalization and compilation failures.
      **Notes:** Reduces routing regressions due to one malformed matcher.

### [WL-8428]

**Title:** Preserve queue metrics by separating measurement collection and report emission
**Source:** [thegent/src/thegent/queue/metrics.py:399]
**Acceptance checklist:**

- [ ] Split metrics collection failures from report emission failures.
- [ ] Keep queue metrics counters stable on emission faults.
- [ ] Add tests for collection and emission branches.
      **Notes:** Preserves observability when transport sinks are flaky.

### [WL-8429]

**Title:** Preserve health aggregation while separating rule eval and status export
**Source:** [thegent/src/thegent/health/aggregate.py:331]
**Acceptance checklist:**

- [ ] Separate health rule evaluation failures from status export failures.
- [ ] Preserve partial health snapshots when export fails.
- [ ] Add tests for rule-eval versus export error modes.
      **Notes:** Helps operations debug from partial telemetry rather than total absence.
