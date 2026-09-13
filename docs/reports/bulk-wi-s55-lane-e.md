### [WL-8310]

**Title:** Preserve CLI route parser while separating unknown command and execution failures
**Source:** [thegent/src/thegent/shell_cli.py:922]
**Acceptance checklist:**

- [ ] Separate unknown-command errors from command execution exceptions.
- [ ] Preserve help text and exit behavior for unknown commands.
- [ ] Add tests for unknown command and execution exceptions.
      **Notes:** Improves user feedback and debugging.

### [WL-8311]

**Title:** Preserve conversation dumper metadata handling by separating extraction and formatting failures
**Source:** [thegent/src/thegent/session/conversation_dumper.py:480]
**Acceptance checklist:**

- [ ] Split metadata extraction errors from export formatting errors.
- [ ] Keep partial exports available on formatting failures.
- [ ] Add tests for both extraction and formatting failures.
      **Notes:** Better handling of evolving metadata schemas.

### [WL-8312]

**Title:** Preserve artifact retention cleanup by separating dry-run calculation and execution
**Source:** [thegent/src/thegent/artifacts/retention.py:468]
**Acceptance checklist:**

- [ ] Separate dry-run candidate calculation from cleanup execution errors.
- [ ] Preserve dry-run reporting even if execution fails.
- [ ] Add tests for dry-run and execution branches.
      **Notes:** Prevents accidental destructive behavior from bad dry-run math.

### [WL-8313]

**Title:** Preserve queue state polling by separating state read and backoff scheduling
**Source:** [thegent/src/thegent/queue/state.py:282]
**Acceptance checklist:**

- [ ] Split read failures from backoff scheduling failures.
- [ ] Preserve polling cadence for read failures.
- [ ] Add tests for both branches.
      **Notes:** Keeps queue visibility under unstable poll loops.

### [WL-8314]

**Title:** Preserve config migration by separating migration list parse and execution failures
**Source:** [thegent/src/thegent/config/settings.py:512]
**Acceptance checklist:**

- [ ] Separate migration list parse failures from migration execution failures.
- [ ] Keep previous settings available if execution fails.
- [ ] Add tests for parsing and execution branch failures.
      **Notes:** Improves startup reliability across updates.

### [WL-8315]

**Title:** Preserve health response contract while separating metrics decode and formatting
**Source:** [thegent/src/thegent/health/endpoint.py:432]
**Acceptance checklist:**

- [ ] Separate metrics payload decode errors from formatting exceptions.
- [ ] Preserve status payload with fallback content.
- [ ] Add tests for decode and formatting failures.
      **Notes:** Avoids empty health responses under schema drift.

### [WL-8316]

**Title:** Preserve borrow telemetry by separating event capture and transport errors
**Source:** [thegent/src/thegent/tools/borrow.py:860]
**Acceptance checklist:**

- [ ] Split telemetry event capture errors from transport send failures.
- [ ] Preserve borrow call success contract when telemetry fails.
- [ ] Add tests for telemetry and transport error classes.
      **Notes:** Keeps primary function working when telemetry degrades.

### [WL-8317]

**Title:** Preserve scheduler metrics collection while separating sample and sink failures
**Source:** [thegent/src/thegent/orchestration/scheduler.py:702]
**Acceptance checklist:**

- [ ] Separate metrics sample collection failures from sink submission failures.
- [ ] Keep scheduler operation independent of sink failures.
- [ ] Add tests for both collection and sink branches.
      **Notes:** Improves resilience when reporting stack is degraded.

### [WL-8318]

**Title:** Preserve prompt rendering by separating template preprocessing and render execution
**Source:** [thegent/src/thegent/prompts.py:421]
**Acceptance checklist:**

- [ ] Split template preprocessing errors from render execution errors.
- [ ] Preserve fallback rendering on preprocessing failures.
- [ ] Add tests for preprocessing and render exceptions.
      **Notes:** Enables targeted fixes in prompt authoring pipelines.

### [WL-8319]

**Title:** Preserve artifact upload retries by separating checksum and send timeout failures
**Source:** [thegent/src/thegent/artifacts/uploader.py:522]
**Acceptance checklist:**

- [ ] Distinguish checksum generation failures from send timeout failures.
- [ ] Preserve retry policy with timeout failures.
- [ ] Add tests for checksum and timeout branches.
      **Notes:** Reduces repeated retries from deterministic checksum errors.
