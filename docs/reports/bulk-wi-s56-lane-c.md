### [WL-8340]

**Title:** Preserve CLI session handoff by separating context deserialization and resume token creation
**Source:** [thegent/src/thegent/session/restore.py:492]
**Acceptance checklist:**

- [ ] Separate context parsing failures from resume token generation errors.
- [ ] Keep handoff flow resilient to bad context payloads.
- [ ] Add tests for context and token branch behavior.
      **Notes:** Improves reconnection quality after partial session corruption.

### [WL-8341]

**Title:** Preserve API throttling by separating policy evaluation and timer scheduling
**Source:** [thegent/src/thegent/api/throttle.py:358]
**Acceptance checklist:**

- [ ] Separate rate policy evaluation errors from timer scheduling failures.
- [ ] Keep immediate throttle behavior on scheduling failures.
- [ ] Add tests for policy and timer branch faults.
      **Notes:** Helps prevent accidental overload from scheduler regressions.

### [WL-8342]

**Title:** Preserve graph rendering by separating node layout and edge resolution
**Source:** [thegent/src/thegent/ui/graph.py:523]
**Acceptance checklist:**

- [ ] Split layout calculation errors from edge resolution issues.
- [ ] Keep partial graph render with fallback layout.
- [ ] Add tests for layout and edge-lookup branches.
      **Notes:** Improves UI stability with partially corrupted graph data.

### [WL-8343]

**Title:** Preserve command suggestion engine by separating model parse and ranking
**Source:** [thegent/src/thegent/suggestions/model.py:447]
**Acceptance checklist:**

- [ ] Distinguish parse failures from ranking failures.
- [ ] Preserve baseline suggestions when ranking branch is degraded.
- [ ] Add tests for both parse and ranking behaviors.
      **Notes:** Reduces suggestion regressions when ranking model is unavailable.

### [WL-8344]

**Title:** Preserve migration execution by separating manifest read and dependency graph planning
**Source:** [thegent/src/thegent/migrations/runner.py:612]
**Acceptance checklist:**

- [ ] Split manifest read failures from dependency graph planning failures.
- [ ] Preserve safe migration subset execution on planning failures.
- [ ] Add tests for manifest and planning errors.
      **Notes:** Helps keep migrations actionable under partial metadata damage.

### [WL-8345]

**Title:** Preserve metrics export while separating CSV generation and file delivery
**Source:** [thegent/src/thegent/metrics/exporter.py:311]
**Acceptance checklist:**

- [ ] Separate CSV serialization errors from transport delivery failures.
- [ ] Preserve in-memory export artifacts for retry behavior.
- [ ] Add tests for serialization and delivery branches.
      **Notes:** Keeps metrics export usable when downstream transfer is slow.

### [WL-8346]

**Title:** Preserve log forwarding by separating filter expression parse and sink dispatch
**Source:** [thegent/src/thegent/logging/forwarder.py:276]
**Acceptance checklist:**

- [ ] Split filter expression parsing from sink dispatch errors.
- [ ] Keep forwarder running with safe fallback filters.
- [ ] Add tests for parser and sink branch failures.
      **Notes:** Reduces log drops under invalid operator combinations.

### [WL-8347]

**Title:** Preserve cache invalidation by separating wildcard resolution and delete execution
**Source:** [thegent/src/thegent/cache/invalidator.py:359]
**Acceptance checklist:**

- [ ] Separate wildcard pattern resolution from deletion execution.
- [ ] Preserve non-wildcard deletion semantics during resolver errors.
- [ ] Add tests for pattern and delete error branches.
      **Notes:** Helps avoid broad cache purges from single-pattern failures.

### [WL-8348]

**Title:** Preserve event replay by separating sequence validation and checkpoint write
**Source:** [thegent/src/thegent/events/replay.py:501]
**Acceptance checklist:**

- [ ] Separate sequence validation failures from checkpoint persistence failures.
- [ ] Preserve replay continuity while warning on non-critical validation issues.
- [ ] Add tests for checkpoint and sequence validation paths.
      **Notes:** Improves recovery confidence for partial event corruption.

### [WL-8349]

**Title:** Preserve file lock handling by separating lock metadata parse and unlock cleanup
**Source:** [thegent/src/thegent/files/locks.py:419]
**Acceptance checklist:**

- [ ] Split metadata parse errors from unlock cleanup failures.
- [ ] Preserve lock state transitions even when cleanup fails.
- [ ] Add tests for both lock branch errors.
      **Notes:** Prevents deadlock risk growth from single-path failures.
