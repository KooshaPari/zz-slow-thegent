### [WL-8450]

**Title:** Preserve health signal propagation by separating collector parse and transport buffer
**Source:** [thegent/src/thegent/health/signal.py:498]
**Acceptance checklist:**

- [ ] Separate health collector parse failures from transport buffer failures.
- [ ] Preserve signal emission during transport fallback.
- [ ] Add tests for collector and transport error branches.
      **Notes:** Improves diagnostic continuity under mixed telemetry conditions.

### [WL-8451]

**Title:** Preserve CLI startup diagnostics by separating config discovery and default projection
**Source:** [thegent/src/thegent/cli/startup.py:372]
**Acceptance checklist:**

- [ ] Separate startup config discovery failures from default projection failures.
- [ ] Preserve diagnostic output on discovery fallbacks.
- [ ] Add tests for discovery and projection branches.
      **Notes:** Supports faster triage for startup issues in partial setups.

### [WL-8452]

**Title:** Preserve workflow checkpoints by separating checkpoint parse and state apply
**Source:** [thegent/src/thegent/workflow/checkpoint.py:441]
**Acceptance checklist:**

- [ ] Separate checkpoint parse failures from state application failures.
- [ ] Preserve last-known good state on checkpoint parse errors.
- [ ] Add tests for both checkpoint branch behaviors.
      **Notes:** Improves workflow recovery precision.

### [WL-8453]

**Title:** Preserve search indexing by separating analyzer parse and index writer
**Source:** [thegent/src/thegent/search/indexer.py:612]
**Acceptance checklist:**

- [ ] Distinguish analyzer parse failures from index writer failures.
- [ ] Keep indexer running with fallback analyzer on parse errors.
- [ ] Add tests for parser and writer branch handling.
      **Notes:** Reduces indexing outages from analyzer syntax slips.

### [WL-8454]

**Title:** Preserve command completion by separating candidate source fetch and ranking
**Source:** [thegent/src/thegent/shell_cli/candidate.py:357]
**Acceptance checklist:**

- [ ] Separate candidate source fetch failures from ranking failures.
- [ ] Keep fallback candidates when ranking is unavailable.
- [ ] Add tests for source-fetch and ranking branches.
      **Notes:** Keeps completion useful during temporary ranking service regressions.

### [WL-8455]

**Title:** Preserve artifact retention reporting by separating retention policy parse and retention execution
**Source:** [thegent/src/thegent/artifacts/reporting.py:381]
**Acceptance checklist:**

- [ ] Split policy parse failures from execution failures.
- [ ] Preserve retention reporting in degraded policy states.
- [ ] Add tests for parsing and execution branches.
      **Notes:** Improves reporting stability with evolving retention formats.

### [WL-8456]

**Title:** Preserve sync plan generation by separating queue snapshot and strategy selection
**Source:** [thegent/src/thegent/sync/plan.py:524]
**Acceptance checklist:**

- [ ] Separate queue snapshot acquisition failures from strategy selection failures.
- [ ] Keep safe sync strategy on queue snapshot errors.
- [ ] Add tests for snapshot and strategy branches.
      **Notes:** Improves sync output reliability under queue instability.

### [WL-8457]

**Title:** Preserve credential loading by separating source retrieval and validation checks
**Source:** [thegent/src/thegent/secrets/loader.py:477]
**Acceptance checklist:**

- [ ] Separate credential source retrieval failures from validation failures.
- [ ] Preserve credential set usage with source-fallback.
- [ ] Add tests for source and validation branch failures.
      **Notes:** Supports secure operation when one credential source is temporarily unavailable.

### [WL-8458]

**Title:** Preserve file watcher lifecycle by separating watch registration and event filtering
**Source:** [thegent/src/thegent/watcher/lifecycle.py:333]
**Acceptance checklist:**

- [ ] Separate watch registration failures from event filtering failures.
- [ ] Keep event stream active with filter fallback.
- [ ] Add tests for registration and filtering branches.
      **Notes:** Prevents watcher deactivation from one branch-specific failure.

### [WL-8459]

**Title:** Preserve task telemetry by separating task span parsing and telemetry export
**Source:** [thegent/src/thegent/observability/task_traces.py:412]
**Acceptance checklist:**

- [ ] Split task span parse failures from telemetry export failures.
- [ ] Preserve task telemetry continuity with export buffering.
- [ ] Add tests for parse and export branch failures.
      **Notes:** Improves traceability for tasks under parser drift.
