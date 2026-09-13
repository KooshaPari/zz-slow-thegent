### [WL-6700]

**Title:** Make `shell reload` report failure when `source ~/.zshrc` exits non-zero.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:136]
**Acceptance Checklist:**

- [x] Capture the `subprocess.run` return code in `shell_reload` and gate success output on `returncode == 0`.
- [x] Surface stderr/stdout snippets when sourcing fails so users can diagnose bad shell config.
- [x] Add CLI test coverage for successful reload and non-zero exit paths.
      **Notes:** Current behavior always prints success when the subprocess call returns, even if zsh sourcing fails.

### [WL-6701]

**Title:** Convert swallowed alias-probe exceptions in `shell doctor` into explicit health findings.
**Source Path+Line:** [thegent/src/thegent/shell_cli.py:177]
**Acceptance Checklist:**

- [x] Replace the bare `except` in alias detection with typed exception handling.
- [x] Append a doctor issue entry when alias inspection fails due to timeout or subprocess error.
- [x] Add tests asserting failure diagnostics appear in doctor output instead of being silently ignored.
      **Notes:** Silent failure in the diagnostic probe can produce false healthy reports.

### [WL-6702]

**Title:** Emit fallback diagnostics when control-plane provider import fails.
**Source Path+Line:** [thegent/src/thegent/config_provider.py:93]
**Acceptance Checklist:**

- [x] Replace the `except ImportError: pass` branch with a logged warning that includes module context.
- [x] Preserve fallback to `EnvConfigProvider` so runtime behavior remains compatible.
- [x] Add tests validating warning emission and fallback selection when control-plane client is unavailable.
      **Notes:** Suppressing import failures hides why control-plane mode was not activated.

### [WL-6703]

**Title:** Safely quote remote working-directory changes in SSH command assembly.
**Source Path+Line:** [thegent/src/thegent/research/remote_compute.py:37]
**Acceptance Checklist:**

- [x] Replace direct string interpolation in `full_command` with shell-safe quoting for `cwd` and command segments.
- [x] Add tests covering spaces/shell metacharacters in remote paths to avoid command breakage or injection.
- [x] Preserve existing response payload shape (`stdout`, `stderr`, `exit_code`, `status`).
      **Notes:** Building `cd {cwd} && {command}` via raw interpolation is brittle for paths containing shell-sensitive characters.

### [WL-6704]

**Title:** Make Ghostty auto-configuration append logic idempotent with explicit managed markers.
**Source Path+Line:** [thegent/src/thegent/ide/auto_setup.py:193]
**Acceptance Checklist:**

- [x] Replace free-form block append with begin/end managed markers to prevent duplicate inserts.
- [x] Add update logic that rewrites an existing managed block instead of appending another copy.
- [x] Add tests for first-run insert and repeated-run no-op behavior.
      **Notes:** Current append-based configuration can drift and produce repeated shell integration snippets.

### [WL-6705]

**Title:** Track skipped files and parse failures during docs index rebuild.
**Source Path+Line:** [thegent/src/docs_engine/cli/commands.py:83]
**Acceptance Checklist:**

- [x] Replace blanket suppression in `index_cmd` with typed parse/read exception handling.
- [x] Count and report skipped files plus failure reasons in command output.
- [x] Add tests for malformed frontmatter and unreadable markdown files.
      **Notes:** Fully silent skip behavior makes index coverage and parsing reliability difficult to audit.

### [WL-6706]

**Title:** Add parse-error diagnostics when loading JSON conversation companions.
**Source Path+Line:** [thegent/src/thegent/research/always_write_dumps.py:218]
**Acceptance Checklist:**

- [x] Catch JSON decode errors explicitly in `load_dump_json` and log the failing file path.
- [x] Keep fail-open return semantics (`None`) for compatibility with existing callers.
- [x] Add tests for valid JSON, malformed JSON, and missing companion files.
      **Notes:** Returning `None` without diagnostics obscures whether the companion is missing or corrupted.

### [WL-6707]

**Title:** Complete mesh discover flow by surfacing discovered agents to users and state.
**Source Path+Line:** [thegent/src/thegent/mesh/main.py:53]
**Acceptance Checklist:**

- [x] Replace no-op loop body with concrete registration and/or output behavior for each discovered agent.
- [x] Add CLI output summarizing discovered agent count and identifiers.
- [x] Add tests ensuring discover does observable work for both auto-detect and pattern-filter modes.
      **Notes:** The current loop executes `pass`, so discovery results are effectively dropped.

### [WL-6708]

**Title:** Prevent partial loader state after artifact parse failures in `load_all`.
**Source Path+Line:** [thegent/src/thegent/planning/board_artifact_loader.py:65]
**Acceptance Checklist:**

- [x] Isolate JSON/CSV load mutations so failed parse attempts do not leave partially-updated `items`, `slices`, or `metadata`.
- [x] Include file-specific context in `result["errors"]` entries for each load failure.
- [x] Add tests for malformed JSON and CSV inputs verifying deterministic post-failure state.
      **Notes:** Current exception handling records errors but can leave in-memory loader structures in mixed states.

### [WL-6709]

**Title:** Normalize empty metric stats output to a stable schema.
**Source Path+Line:** [thegent/src/thegent/metrics/collector.py:39]
**Acceptance Checklist:**

- [x] Change `get_stats` to return a consistent typed payload for empty metrics (for example `count=0` with nullable min/max/avg).
- [x] Update downstream callers/tests to rely on schema stability rather than truthy dict checks.
- [x] Add unit tests for empty, single-value, and multi-value metric series.
      **Notes:** Returning `{}` for empty series forces callers into shape-branching and weakens interface predictability.

## Evidence

- `WL-6700` / `WL-6701`: `src/thegent/shell_cli.py` updated for `reload` return-code gating/snippets and doctor alias-probe issue surfacing; covered by `tests/test_wl6700_shell_cli.py`.
- `WL-6702`: `src/thegent/config_provider.py` now logs explicit control-plane import fallback warning; covered by `tests/test_unit_config_provider.py`.
- `WL-6703`: `src/thegent/research/remote_compute.py` now builds `cd <quoted cwd> && sh -lc <quoted command>`; covered by `tests/test_wl6703_remote_compute.py`.
- `WL-6704`: `src/thegent/ide/auto_setup.py` now uses managed begin/end markers with idempotent upsert; covered by `tests/test_wl6704_auto_setup_ghostty.py`.
- `WL-6705`: `src/docs_engine/cli/commands.py` now reports skipped/read/parse failures with reasons; covered by `tests/docs_engine/test_cli.py`.
- `WL-6706`: `src/thegent/research/always_write_dumps.py` now logs JSON parse/read failures with companion path; covered by `tests/test_unit_always_write_dumps_batch6.py`.
- `WL-6707`: `src/thegent/mesh/main.py` discover now registers agents and prints count/ids for auto-detect and pattern modes; covered by `tests/mesh/test_main_discover.py`.
- `WL-6708`: `src/thegent/planning/board_artifact_loader.py` now parses JSON/CSV into local state before commit and emits file-context errors; covered by `tests/test_wl158_board_artifact_integration.py`.
- `WL-6709`: `src/thegent/metrics/collector.py` empty stats now return stable schema with nullable aggregates; covered by `tests/test_wl6709_metrics_collector.py`.
- Focused validation command: `.venv/bin/python -m pytest -q -p no:tach tests/test_wl6700_shell_cli.py tests/test_unit_config_provider.py tests/test_wl6703_remote_compute.py tests/test_wl6704_auto_setup_ghostty.py tests/docs_engine/test_cli.py tests/test_unit_always_write_dumps_batch6.py tests/mesh/test_main_discover.py tests/test_wl158_board_artifact_integration.py tests/test_wl6709_metrics_collector.py` -> `46 passed in 7.05s`.
