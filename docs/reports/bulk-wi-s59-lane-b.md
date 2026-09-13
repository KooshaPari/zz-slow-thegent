### [WL-8480]

**Title:** Preserve telemetry ingestion by separating packet decode and schema enrichment
**Source:** [thegent/src/thegent/telemetry/ingest.py:462]
**Acceptance checklist:**

- [ ] Separate telemetry packet decode failures from schema enrichment failures.
- [ ] Keep raw packet buffering on enrichment errors.
- [ ] Add tests for decode and enrichment branches.
      **Notes:** Improves telemetry resilience under schema churn.

### [WL-8481]

**Title:** Preserve authentication challenge handling by separating challenge body parse and signer service
**Source:** [thegent/src/thegent/auth/challenge_handler.py:523]
**Acceptance checklist:**

- [ ] Separate challenge body parsing failures from signer service failures.
- [ ] Preserve challenge state on signer outages.
- [ ] Add tests for body parse and signer branch failures.
      **Notes:** Keeps auth challenge flows resilient to service spikes.

### [WL-8482]

**Title:** Preserve queue state persistence by separating state serialization and fsync scheduling
**Source:** [thegent/src/thegent/queue/state.py:501]
**Acceptance checklist:**

- [ ] Separate state serialization failures from fsync scheduling failures.
- [ ] Preserve in-memory queue state during fsync issues.
- [ ] Add tests for serialization and fsync paths.
      **Notes:** Improves durability behavior under write contention.

### [WL-8483]

**Title:** Preserve user preference migration by separating JSON upgrade and profile merge
**Source:** [thegent/src/thegent/user/prefs_migrate.py:346]
**Acceptance checklist:**

- [ ] Separate preference JSON upgrade failures from profile merge failures.
- [ ] Preserve user profiles with fallback migration.
- [ ] Add tests for upgrade and merge branches.
      **Notes:** Prevents preference regressions during upgrade steps.

### [WL-8484]

**Title:** Preserve command completion cache by separating candidate source parse and cache invalidation
**Source:** [thegent/src/thegent/shell_cli/completion_cache.py:411]
**Acceptance checklist:**

- [ ] Separate candidate source parse failures from cache invalidation failures.
- [ ] Preserve candidate cache on invalidation errors.
- [ ] Add tests for source parse and invalidation failures.
      **Notes:** Keeps completion responsive across cache churn.

### [WL-8485]

**Title:** Preserve artifact signing audit by separating signature metadata and persistence
**Source:** [thegent/src/thegent/artifacts/sign_audit.py:378]
**Acceptance checklist:**

- [ ] Separate signature metadata parse failures from persistence failures.
- [ ] Keep signature audit trail with degraded persistence mode.
- [ ] Add tests for signature metadata and persistence branches.
      **Notes:** Strengthens chain-of-custody under partial signing failures.

### [WL-8486]

**Title:** Preserve workstream orchestration by separating worker registration and health reporting
**Source:** [thegent/src/thegent/workstream/orchestrator.py:447]
**Acceptance checklist:**

- [ ] Separate worker registration failures from health reporting failures.
- [ ] Keep registration fallback metrics under reporting failures.
- [ ] Add tests for registration and reporting branch failures.
      **Notes:** Helps detect worker issues without stopping orchestration.

### [WL-8487]

**Title:** Preserve import command robustness by separating file manifest parse and command execution
**Source:** [thegent/src/thegent/commands/importer.py:522]
**Acceptance checklist:**

- [ ] Separate file manifest parse errors from execution failures.
- [ ] Preserve import command safety with execution fallback.
- [ ] Add tests for parse and execution branches.
      **Notes:** Reduces command-level failures from malformed manifests.

### [WL-8488]

**Title:** Preserve metric emission by separating sampling and exporter transport
**Source:** [thegent/src/thegent/metrics/emitter.py:356]
**Acceptance checklist:**

- [ ] Separate sample collection failures from transport emission failures.
- [ ] Preserve metric counters on transport branch failures.
- [ ] Add tests for sampling and emission branches.
      **Notes:** Keeps observability stable under noisy transport.

### [WL-8489]

**Title:** Preserve graph snapshot by separating node export and edge export
**Source:** [thegent/src/thegent/graph/snapshot.py:592]
**Acceptance checklist:**

- [ ] Separate node export failures from edge export failures.
- [ ] Preserve partial snapshots when one branch fails.
- [ ] Add tests for node and edge export branches.
      **Notes:** Helps recover graph state after partial export failures.
