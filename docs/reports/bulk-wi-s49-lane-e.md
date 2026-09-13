### [WL-8010]

**Title:** Add `--explain` mode for command resolution to show alias/plugin/path decision chain
**Source:** [thegent/src/thegent/cli/resolver.py:112]
**Acceptance checklist:**

- [ ] Add an `--explain` flag that prints the deterministic command resolution chain before execution.
- [ ] Ensure explain output is emitted only when the flag is provided and does not alter execution behavior.
- [ ] Add tests for alias resolution explanation, plugin resolution explanation, and no-output behavior without the flag.
      **Notes:** Faster command routing visibility reduces repeated debugging when commands resolve unexpectedly.

### [WL-8011]

**Title:** Add bounded retry for local config file read races during startup
**Source:** [thegent/src/thegent/config/loader.py:74]
**Acceptance checklist:**

- [ ] Retry transient read errors caused by short-lived file locks with bounded attempts and small backoff.
- [ ] Preserve immediate fail-fast behavior for non-transient parse and permission errors.
- [ ] Add tests for immediate success, transient lock recovery, and terminal failure with clear error context.
      **Notes:** Local startup flakiness often comes from brief editor or sync-process file lock windows.

### [WL-8012]

**Title:** Surface a focused “next action” hint when required env vars are missing
**Source:** [thegent/src/thegent/runtime/env_validation.py:39]
**Acceptance checklist:**

- [ ] Print a concise missing-env summary with one recommended command/action to remediate.
- [ ] Keep non-zero exit behavior unchanged when required variables are absent.
- [ ] Add tests for single-var messaging, multi-var messaging order, and no-hint output when validation passes.
      **Notes:** Developers lose time scanning long traces instead of seeing the first corrective action.

### [WL-8013]

**Title:** Add checksum-based skip for unchanged generated artifacts in local workflows
**Source:** [thegent/src/thegent/artifacts/writer.py:128]
**Acceptance checklist:**

- [ ] Compute stable content checksums and skip writes when target output is unchanged.
- [ ] Emit an explicit “unchanged, skipped” status line in verbose mode.
- [ ] Add tests for changed-write behavior, unchanged-skip behavior, and checksum stability across repeated runs.
      **Notes:** Avoiding needless rewrites speeds local loops and reduces noisy file watcher churn.

### [WL-8014]

**Title:** Add per-command timeout override with clear timeout diagnostics
**Source:** [thegent/src/thegent/commands/runner.py:91]
**Acceptance checklist:**

- [ ] Support command-level timeout override via CLI flag and environment variable with deterministic precedence.
- [ ] Report timed-out command name, effective timeout, and elapsed duration in a concise error.
- [ ] Add tests for default timeout behavior, override precedence, and timeout error formatting.
      **Notes:** One-size timeout values create false failures in slower local or CI-adjacent environments.

### [WL-8015]

**Title:** Add startup warning when config file contains unknown keys
**Source:** [thegent/src/thegent/config/schema.py:56]
**Acceptance checklist:**

- [ ] Detect unknown top-level and nested config keys and emit a sorted warning list.
- [ ] Keep valid-key parsing and runtime behavior unchanged when warnings are present.
- [ ] Add tests for no-warning valid config, unknown-key warning output, and deterministic key ordering.
      **Notes:** Silent typos in config keys lead to confusing no-op behavior and misconfigured environments.

### [WL-8016]

**Title:** Improve interrupt handling by writing partial progress checkpoint metadata on cancellation
**Source:** [thegent/src/thegent/runtime/checkpoint.py:67]
**Acceptance checklist:**

- [ ] Persist minimal checkpoint metadata on user cancellation for commands that support resume.
- [ ] Ensure checkpoint write is atomic and does not leave corrupt partial files.
- [ ] Add tests for cancellation checkpoint creation, atomic-write guarantees, and non-resumable command no-op behavior.
      **Notes:** Cancellation without resumable state forces full reruns and slows iterative troubleshooting.

### [WL-8017]

**Title:** Add human-readable diff summary to `thegent doctor --json` changes output
**Source:** [thegent/src/thegent/commands/doctor_diff.py:25]
**Acceptance checklist:**

- [ ] Include a compact summary section listing added/removed/changed checks alongside existing JSON payload.
- [ ] Keep machine-readable JSON structure stable for existing automated consumers.
- [ ] Add tests for summary rendering correctness, zero-change output behavior, and stable field order.
      **Notes:** Operators want quick glanceability without manually diffing full JSON blobs.

### [WL-8018]

**Title:** Add preflight check for unwritable cache directory with explicit remediation path
**Source:** [thegent/src/thegent/cache/fs.py:33]
**Acceptance checklist:**

- [ ] Validate cache directory writability during preflight before expensive command execution begins.
- [ ] Fail with a direct remediation hint including effective cache path and permission fix guidance.
- [ ] Add tests for writable-path success, unwritable-path failure, and stable error messaging.
      **Notes:** Late cache permission failures waste runtime and produce avoidable reruns.

### [WL-8019]

**Title:** Add optional compact output mode to reduce log noise during repetitive local runs
**Source:** [thegent/src/thegent/output/compact.py:14]
**Acceptance checklist:**

- [ ] Implement opt-in compact mode that suppresses repetitive informational lines while preserving warnings/errors.
- [ ] Keep default output unchanged when compact mode is not enabled.
- [ ] Add tests for compact suppression behavior, warning/error preservation, and default-mode parity.
      **Notes:** High-volume repeated logs make local debugging slower and obscure actionable lines.
