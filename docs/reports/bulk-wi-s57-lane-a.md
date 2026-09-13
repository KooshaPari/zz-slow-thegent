### [WL-8370]

**Title:** Preserve agent memory restoration by separating snapshot decode and semantic hydration
**Source:** [thegent/src/thegent/agent/memory.py:611]
**Acceptance checklist:**

- [ ] Separate snapshot decode failures from semantic hydration failures.
- [ ] Preserve baseline memory for successful semantic chunks.
- [ ] Add tests for decode and hydration branches.
      **Notes:** Improves memory recovery in mixed-version checkpoints.

### [WL-8371]

**Title:** Preserve workflow retries by separating transient-failure classification and delay calculator
**Source:** [thegent/src/thegent/retry/handler.py:418]
**Acceptance checklist:**

- [ ] Separate transient classification failures from delay generation failures.
- [ ] Keep retry execution active when delay calculator degrades.
- [ ] Add tests for classification and delay branch behavior.
      **Notes:** Prevents one transient miss from suppressing all retries.

### [WL-8372]

**Title:** Preserve metric aggregation by separating label parsing and bucket insertion
**Source:** [thegent/src/thegent/metrics/aggregate.py:355]
**Acceptance checklist:**

- [ ] Separate invalid label parsing from bucket insertion failures.
- [ ] Preserve aggregate updates with fallback labels when parse fails.
- [ ] Add tests for invalid labels and insertion faults.
      **Notes:** Keeps telemetry stable when label schema changes.

### [WL-8373]

**Title:** Preserve event bus backpressure by separating buffer accounting and drain scheduling
**Source:** [thegent/src/thegent/events/backpressure.py:442]
**Acceptance checklist:**

- [ ] Distinguish accounting update failures from drain scheduling failures.
- [ ] Preserve backpressure signals during non-critical drain failures.
- [ ] Add tests for accounting and drain branches.
      **Notes:** Helps avoid event backlog growth from scheduler glitches.

### [WL-8374]

**Title:** Preserve API auth challenge flow by separating challenge parse and provider callback
**Source:** [thegent/src/thegent/auth/challenge.py:498]
**Acceptance checklist:**

- [ ] Split challenge payload parsing from provider callback failures.
- [ ] Preserve fallback auth challenge when callback is temporarily degraded.
- [ ] Add tests for parse and callback branch failure modes.
      **Notes:** Improves auth robustness across provider behavior changes.

### [WL-8375]

**Title:** Preserve task cleanup by separating stale marker detection and cleanup execution
**Source:** [thegent/src/thegent/tasks/cleanup.py:367]
**Acceptance checklist:**

- [ ] Separate stale marker detection failures from cleanup execution failures.
- [ ] Keep execution attempts for non-stale paths when detection fails.
- [ ] Add tests for marker and execution branch behavior.
      **Notes:** Prevents cleanup starvation when marker parsing is noisy.

### [WL-8376]

**Title:** Preserve data export formatting by separating schema render and transport upload
**Source:** [thegent/src/thegent/export/formatter.py:286]
**Acceptance checklist:**

- [ ] Separate schema rendering failures from upload failures.
- [ ] Preserve raw export artifact on rendering failures.
- [ ] Add tests for both branches and error reporting.
      **Notes:** Maintains data export continuity under output-format regressions.

### [WL-8377]

**Title:** Preserve CLI argument binding by separating parsing and default injection
**Source:** [thegent/src/thegent/cli/parser.py:329]
**Acceptance checklist:**

- [ ] Separate argument parsing failures from default injection failures.
- [ ] Keep defaults consistent when explicit parse succeeds.
- [ ] Add tests for parse and default injection branches.
      **Notes:** Reduces false negatives in CLI execution paths.

### [WL-8378]

**Title:** Preserve graph export by separating coordinate transform and JSON encode
**Source:** [thegent/src/thegent/ui/graph_export.py:410]
**Acceptance checklist:**

- [ ] Separate coordinate transformation failures from JSON encoding failures.
- [ ] Keep export output available with raw coordinates on encode failures.
- [ ] Add tests for transform and encode failure branches.
      **Notes:** Supports UI troubleshooting even with mixed rendering support.

### [WL-8379]

**Title:** Preserve file watch notifications by separating path normalization and event publish
**Source:** [thegent/src/thegent/watcher/notify.py:279]
**Acceptance checklist:**

- [ ] Split path normalization failures from event publish failures.
- [ ] Preserve event publish for unnormalized path cases.
- [ ] Add tests for path normalization and publish branches.
      **Notes:** Reduces blind spots in eventing for partially invalid paths.
