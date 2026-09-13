### [WL-8150]

**Title:** Separate process-compose refresh config errors from runtime command errors
**Source:** [thegent/src/thegent/process_compose/watcher.py:162]
**Acceptance checklist:**

- [ ] Distinguish missing compose config from command execution failures.
- [ ] Preserve best-effort refresh behavior on transient refresh failures.
- [ ] Add tests for both failure branches.
      **Notes:** Improves operational reliability during live refresh workflows.

### [WL-8151]

**Title:** Preserve control-plane startup with explicit config read vs bind failures
**Source:** [thegent/src/thegent/control_plane/server.py:84]
**Acceptance checklist:**

- [ ] Split config read/parse failures from socket bind/listen failures.
- [ ] Keep existing startup retries and fallback states.
- [ ] Add tests for malformed config and bind-in-use cases.
      **Notes:** Faster diagnosis of control plane bootstrap issues.

### [WL-8152]

**Title:** Separate artifact collector directory traversal from permission failures
**Source:** [thegent/src/thegent/artifacts/collector.py:161]
**Acceptance checklist:**

- [ ] Add path traversal validation branch before collection.
- [ ] Handle permission errors separately in collector loop.
- [ ] Add tests for traversal attempts and permission-denied paths.
      **Notes:** Prevents hidden false negatives during collection scans.

### [WL-8153]

**Title:** Preserve CLI error codes while separating parse errors from execution exceptions
**Source:** [thegent/src/thegent/shell_cli.py:172]
**Acceptance checklist:**

- [ ] Split command argument parse validation from runtime command execution exceptions.
- [ ] Preserve command execution return codes for runtime failures.
- [[] ] Add tests for bad args, parse exceptions, and runtime failures.
  **Notes:** Keeps user-visible error semantics but adds clearer root-cause output.

### [WL-8154]

**Title:** Separate borrow tool telemetry publish errors from borrow execution failures
**Source:** [thegent/src/thegent/tools/borrow.py:392]
**Acceptance checklist:**

- [ ] Handle telemetry emit failures separately from borrow action failures.
- [ ] Preserve existing borrow results even when telemetry publishing fails.
- [ ] Add tests for telemetry-only failures.
      **Notes:** Keeps tool reliability even under observability outages.

### [WL-8155]

**Title:** Preserve queue scaling behavior while separating fetch failures and parser errors
**Source:** [thegent/src/thegent/queue/scaler.py:97]
**Acceptance checklist:**

- [ ] Split queue state fetch errors from payload schema parse errors.
- [ ] Preserve scaling decision logic for fetch-only partial failures.
- [ ] Add tests for malformed queue state and fetch exception cases.
      **Notes:** Distinguishes infra instability from schema contract breaks.

### [WL-8156]

**Title:** Distinguish settings override parse errors from override resolution failures
**Source:** [thegent/src/thegent/config/settings.py:233]
**Acceptance checklist:**

- [ ] Handle malformed override values separately from unresolved references.
- [ ] Preserve defaults where resolution fails.
- [ ] Add tests for override parse and resolution failures.
      **Notes:** Improves config robustness during gradual rollout.

### [WL-8157]

**Title:** Preserve summary output while separating render parse and rendering engine exceptions
**Source:** [thegent/src/thegent/summary.py:345]
**Acceptance checklist:**

- [ ] Separate output payload parse errors from render engine runtime exceptions.
- [ ] Keep summary generation contract on non-critical parse issues.
- [ ] Add tests for malformed summary payload and renderer failures.
      **Notes:** Prevents one bad payload from blanking summaries.

### [WL-8158]

**Title:** Preserve startup logs while separating plugin manifest read from schema parse
**Source:** [thegent/src/thegent/ui/plugin_loader.py:214]
**Acceptance checklist:**

- [ ] Handle plugin manifest file read failures separately from parse failures.
- [ ] Keep existing startup logging path for both branches.
- [ ] Add tests for I/O failure and malformed manifest.
      **Notes:** Better startup clarity for UI plugin onboarding.

### [WL-8159]

**Title:** Separate shell completion cache stale-state from serialization exceptions
**Source:** [thegent/src/thegent/shell_cli.py:512]
**Acceptance checklist:**

- [ ] Add dedicated handling for stale cache reads and JSON serialization exceptions.
- [ ] Preserve completion behavior with cache rebuild fallback.
- [ ] Add tests for corrupted cache and serialization failures.
      **Notes:** Keeps shell completion responsive in corrupt-cache situations.
