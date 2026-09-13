### [WL-7960]

**Title:** Add startup phase timing summary to CLI verbose mode for faster cold-start triage
**Source:** [thegent/src/thegent/cli/main.py:88]
**Acceptance checklist:**

- [ ] Print phase-level startup timings (config load, plugin init, command dispatch) when verbose mode is enabled.
- [ ] Preserve current default output verbosity when verbose flags are not provided.
- [ ] Add tests for timing summary presence in verbose mode, absence in default mode, and deterministic phase label ordering.
      **Notes:** Slow command startup is currently hard to localize without ad-hoc profiling.

### [WL-7961]

**Title:** Harden cache metadata reads with corruption fallback and auto-rebuild path
**Source:** [thegent/src/thegent/cache/metadata.py:47]
**Acceptance checklist:**

- [ ] Detect malformed cache metadata files and fall back to a safe empty-state load.
- [ ] Trigger cache metadata rebuild on corruption while logging a concise warning.
- [ ] Add tests for valid metadata load, corrupted metadata fallback, and rebuild success without process crash.
      **Notes:** A single bad cache file should not block routine developer commands.

### [WL-7962]

**Title:** Add `--dry-run` support for config mutation commands to preview exact on-disk changes
**Source:** [thegent/src/thegent/commands/config.py:133]
**Acceptance checklist:**

- [ ] Implement `--dry-run` for config write subcommands that prints a normalized before/after diff preview.
- [ ] Ensure dry-run mode performs no filesystem writes and exits successfully when preview generation succeeds.
- [ ] Add tests for dry-run no-write guarantees, preview accuracy, and unchanged behavior for normal write mode.
      **Notes:** Operators want safer config edits before mutating shared environments.

### [WL-7963]

**Title:** Improve interrupted command UX by printing resumable next-step hints on SIGINT
**Source:** [thegent/src/thegent/runtime/signals.py:29]
**Acceptance checklist:**

- [ ] Catch SIGINT during long-running commands and emit a short, actionable resume/retry hint.
- [ ] Preserve existing non-zero exit semantics and signal handling for non-interactive usage.
- [ ] Add tests for single-interrupt hint output, repeated-interrupt behavior, and no-hint output for fast commands.
      **Notes:** Users currently lose context after Ctrl+C and must rediscover safe restart commands.

### [WL-7964]

**Title:** Add guarded retry with jitter for transient local IPC connection failures
**Source:** [thegent/src/thegent/ipc/client.py:72]
**Acceptance checklist:**

- [ ] Retry transient IPC connect failures with bounded attempts and jittered backoff.
- [ ] Surface final failure with concise attempt count and last error message.
- [ ] Add tests for immediate success, transient failure then recovery, and terminal failure after max retries.
      **Notes:** Brief socket race windows create avoidable flakes during local orchestration.

### [WL-7965]

**Title:** Normalize file path rendering in logs to workspace-relative form where possible
**Source:** [thegent/src/thegent/logging/formatters.py:54]
**Acceptance checklist:**

- [ ] Render paths relative to workspace root when safely representable, falling back to absolute paths otherwise.
- [ ] Preserve existing JSON logging fields and avoid breaking machine-parsed log consumers.
- [ ] Add tests for relative-path rendering, absolute fallback behavior, and unchanged output outside workspace contexts.
      **Notes:** Mixed absolute paths make logs noisy and harder to scan across developer machines.

### [WL-7966]

**Title:** Add `thegent doctor --json` schema version field for compatibility-safe automation
**Source:** [thegent/src/thegent/commands/doctor_json.py:18]
**Acceptance checklist:**

- [ ] Include a top-level schema version in doctor JSON output.
- [ ] Maintain backward-compatible existing fields while documenting version bump policy.
- [ ] Add tests for schema version presence, stable version formatting, and backward field continuity.
      **Notes:** Automation consumers need explicit versioning to safely parse evolving health output.

### [WL-7967]

**Title:** Add stale lockfile detection with age threshold and recovery guidance
**Source:** [thegent/src/thegent/runtime/lockfile.py:101]
**Acceptance checklist:**

- [ ] Detect lockfiles older than a configurable threshold and warn with ownership/age details.
- [ ] Provide a clear recovery command snippet when stale lockfiles block startup.
- [ ] Add tests for fresh lock acceptance, stale lock warning path, and threshold override behavior.
      **Notes:** Abandoned lockfiles frequently block workflows after crashes or terminal disconnects.

### [WL-7968]

**Title:** Enforce command alias collision checks at startup with deterministic conflict reporting
**Source:** [thegent/src/thegent/cli/aliases.py:63]
**Acceptance checklist:**

- [ ] Validate alias uniqueness during startup and fail fast on collisions.
- [ ] Report conflicts in deterministic sorted order including alias and owning command names.
- [ ] Add tests for no-collision startup, single-collision failure output, and multi-collision deterministic ordering.
      **Notes:** Hidden alias conflicts cause surprising command routing and difficult debugging.

### [WL-7969]

**Title:** Add concise post-run summary footer with duration and key artifact pointers
**Source:** [thegent/src/thegent/output/summary_footer.py:22]
**Acceptance checklist:**

- [ ] Print an opt-in summary footer containing total duration, exit status, and key artifact paths.
- [ ] Preserve existing command output contracts when summary footer is disabled.
- [ ] Add tests for footer-enabled rendering, footer-disabled no-op behavior, and stable field formatting.
      **Notes:** Developers benefit from a consistent run-end summary instead of scanning mixed logs.
