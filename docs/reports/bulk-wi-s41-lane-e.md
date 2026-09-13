### [WL-7610]

**Title:** Preserve conversation export failure taxonomy when markdown dump writes fail
**Source:** [thegent/src/thegent/session/conversation_dumper.py:163]
**Acceptance checklist:**

- [ ] Replace broad export exception handling with typed filesystem and serialization failure branches.
- [ ] Preserve current command contract while emitting actionable failure details for operator debugging.
- [ ] Add tests for permission-denied output paths and malformed conversation payloads.
      **Notes:** Line 163 currently catches broadly, which reduces reliability diagnostics during export failures.

### [WL-7611]

**Title:** Make HTML transcript render errors deterministic instead of returning opaque `None`
**Source:** [thegent/src/thegent/session/conversation_dumper.py:215]
**Acceptance checklist:**

- [ ] Replace blanket render exception handling with explicit template/render failure classes.
- [ ] Preserve non-crashing caller behavior while returning structured error context for devx.
- [ ] Add tests for template read failures, invalid transcript structures, and success path parity.
      **Notes:** Line 215 currently collapses render failure causes into a generic error path.

### [WL-7612]

**Title:** Surface prompt-load item parse faults without silently dropping prompt entries
**Source:** [thegent/src/thegent/prompts.py:116]
**Acceptance checklist:**

- [ ] Replace broad per-item suppression with typed parse-validation diagnostics that include item identity.
- [ ] Preserve successful loading of valid prompt items in mixed-validity datasets.
- [ ] Add tests for malformed prompt items alongside valid entries and fully valid catalogs.
      **Notes:** Line 115 currently suppresses item-level failures with `pass`, reducing operator visibility.

### [WL-7613]

**Title:** Preserve include-file expansion observability in prompt ingestion pipeline
**Source:** [thegent/src/thegent/prompts.py:204]
**Acceptance checklist:**

- [ ] Replace silent include-processing suppression with bounded warnings containing include source path context.
- [ ] Preserve current best-effort behavior so one bad include does not abort overall prompt load.
- [ ] Add tests for missing include files, unreadable includes, and mixed include success.
      **Notes:** Line 205 currently swallows include expansion exceptions via `pass`.

### [WL-7614]

**Title:** Expose prompt metadata decode failures so selection quality regressions are diagnosable
**Source:** [thegent/src/thegent/prompts.py:425]
**Acceptance checklist:**

- [ ] Replace blanket metadata parse suppression with typed JSON/YAML decode handling and concise diagnostics.
- [ ] Preserve current prompt discovery continuity when optional metadata is invalid.
- [ ] Add tests for corrupt metadata files, valid metadata, and metadata-absent prompts.
      **Notes:** Line 425 currently uses silent suppression that hides metadata integrity issues.

### [WL-7615]

**Title:** Harden task migration progress-state parsing to improve reliability during partial upgrades
**Source:** [thegent/src/thegent/task/migrate.py:64]
**Acceptance checklist:**

- [ ] Replace broad migration-state suppression with explicit parse/version mismatch handling.
- [ ] Preserve idempotent migration behavior when prior state is missing or stale.
- [ ] Add tests for malformed state files, unsupported schema versions, and successful resume flows.
      **Notes:** Line 64 currently ignores migration-state failures with `pass`, which impairs repairability.

### [WL-7616]

**Title:** Keep port lease cleanup failures visible while retaining non-fatal teardown semantics
**Source:** [thegent/src/thegent/testing/port_lease.py:89]
**Acceptance checklist:**

- [ ] Replace silent lease-file cleanup suppression with low-noise diagnostics carrying path and errno context.
- [ ] Preserve non-throwing teardown behavior to avoid flaky test shutdowns.
- [ ] Add tests for missing lease files, permission-denied cleanup, and successful cleanup.
      **Notes:** Line 89 currently suppresses cleanup errors via `pass`, weakening test reliability debugging.

### [WL-7617]

**Title:** Strengthen summary-rollup robustness by classifying record parse failures explicitly
**Source:** [thegent/src/thegent/summary.py:317]
**Acceptance checklist:**

- [ ] Replace generic summary aggregation suppression with typed per-record parse and coercion error handling.
- [ ] Preserve existing aggregate output schema for downstream tooling compatibility.
- [ ] Add tests for malformed summary records, mixed valid/invalid runs, and fully valid inputs.
      **Notes:** Line 318 currently swallows exceptions without failure-class attribution.

### [WL-7618]

**Title:** Improve doctor setup check operator UX by eliminating catch-all bootstrap error handling
**Source:** [thegent/src/thegent/doctor_setup_checks.py:72]
**Acceptance checklist:**

- [ ] Replace broad setup exception handling with explicit environment, transport, and config validation branches.
- [ ] Preserve doctor command completion semantics while adding actionable remediation hints.
- [ ] Add tests for missing binaries, unreachable services, and success-path diagnostics formatting.
      **Notes:** Line 72 currently catches broadly, reducing determinism of setup-failure reporting.

### [WL-7619]

**Title:** Make shell command execution error channels consistent for better CLI debugging ergonomics
**Source:** [thegent/src/thegent/shell_cli.py:263]
**Acceptance checklist:**

- [ ] Replace broad shell execution suppression with typed subprocess and IO failure pathways.
- [ ] Preserve current return contract while ensuring stderr/context propagation is deterministic.
- [ ] Add tests for command-not-found, non-zero exit, and timeout behavior.
      **Notes:** Line 262 currently uses generic exception handling that blurs failure modes.
