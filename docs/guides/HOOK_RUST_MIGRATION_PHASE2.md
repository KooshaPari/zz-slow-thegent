# Hook Rust Migration: Phase 2 Opt-in Dispatch

**Status**: Implemented
**Traces to**: FR-HOOKS-001, FR-HOOKS-002, FR-HOOKS-003, FR-HOOKS-004
**Related**: `hooks/lib/rust_dispatch.sh`, `hooks/debounce.sh`, `hooks/incremental-check.sh`, `hooks/circuit-breaker.sh`

---

## Overview

Phase 2 introduces a per-hook opt-in dispatch mechanism: individual hook scripts can delegate their logic to the `thegent-hooks` Rust binary at runtime, with automatic fallback to the shell implementation when the binary is absent or disabled.

This is distinct from Phase 3 (common-rust.sh), which replaces entire hook library internals. Phase 2 sits at the hook-script level — each hook individually decides whether to hand off to Rust.

### Why Phase 2?

| Phase | Scope                                       | Mechanism                | Status              |
| ----- | ------------------------------------------- | ------------------------ | ------------------- |
| 1     | Rust binary built and available             | `crates/thegent-hooks/`  | Done                |
| **2** | **Per-hook opt-in via env/config**          | **`rust_dispatch.sh`**   | **Done (this doc)** |
| 3     | Full runtime replacement via common-rust.sh | Sources `common-rust.sh` | Separate            |

Phase 2 allows gradual adoption: hooks can be migrated one at a time while the rest of the hook system continues operating in shell mode.

---

## Enabling Rust Dispatch

### Environment Variable (Highest Priority)

```bash
export THGENT_HOOKS_RUST=1   # enable
export THGENT_HOOKS_RUST=0   # disable (explicit)
```

Accepted truthy values: `1`, `true`, `yes`, `on` (case-insensitive).
Accepted falsy values: `0`, `false`, `no`, `off`.

### hook-config.yaml (Config File)

```yaml
# hooks/hook-config.yaml
use_rust_runtime: true
```

The dispatch library reads this file directly (grep-based, no YAML parser dependency) when `THGENT_HOOKS_RUST` is not set. This is the production default.

### Resolution Order

```
THGENT_HOOKS_RUST env var  (highest priority)
        ↓
hook_config_true "use_rust_runtime"  (if common.sh is loaded)
        ↓
grep hook-config.yaml for use_rust_runtime: true
        ↓
Disabled by default
```

---

## Binary Resolution

The dispatch library locates `thegent-hooks` via the following cascade, caching the result in `THGENT_HOOKS_BIN`:

```
THGENT_HOOKS_BIN (already resolved this session)
        ↓
THGENT_HOOKS_RUST_BIN (explicit path override)
        ↓
crates/target/release/thegent-hooks
        ↓
crates/target/debug/thegent-hooks
        ↓
target/release/thegent-hooks
        ↓
target/debug/thegent-hooks
        ↓
hooks/../bin/thegent-hooks
        ↓
PATH lookup (command -v thegent-hooks)
        ↓
Not found → fall back to shell
```

### Overriding the Binary Path

```bash
export THGENT_HOOKS_RUST_BIN=/path/to/custom/thegent-hooks
```

---

## The Dispatch Library: `hooks/lib/rust_dispatch.sh`

Source this library at the top of any hook that wants opt-in Rust dispatch.

```bash
source "${_SCRIPT_DIR}/lib/rust_dispatch.sh"
```

### `hook_rust_dispatch <subcommand> [args...]`

Attempts to invoke `thegent-hooks <subcommand> [args...]`.

Return values:

| Return                | Meaning                                                       |
| --------------------- | ------------------------------------------------------------- |
| Exit code from binary | Binary executed; caller propagates its exit code              |
| Shell return `1`      | Rust disabled or binary not found; caller falls back to shell |

The binary's exit codes are forwarded as-is, except exit code `127` (command not found at exec time), which is treated as a fallback trigger.

**Usage pattern**:

```bash
source "${_SCRIPT_DIR}/lib/rust_dispatch.sh"

if hook_rust_dispatch "my-subcommand" "${HOOK_KEY}" "${EXTRA_ARGS[@]}"; then
  exit $?   # Rust handled it; exit with its code
fi

# Shell fallback implementation
# ...
```

### `hook_rust_dispatch_or_exit <subcommand> [args...]`

Like `hook_rust_dispatch` but exits the current process when dispatch succeeds. Use this when there is no shell fallback.

```bash
# If Rust binary executes, process exits with binary's exit code.
# If Rust disabled/absent, returns 1 and continues to shell fallback.
hook_rust_dispatch_or_exit "my-subcommand" "${HOOK_KEY}"
```

### `rust_dispatch_bin`

Returns the resolved path to the `thegent-hooks` binary, or exits non-zero if not found.

```bash
bin="$(rust_dispatch_bin)"
```

### Verbose Logging

```bash
export THGENT_HOOKS_RUST_VERBOSE=1
```

Emits dispatch decisions to stderr:

```
rust_dispatch: routing to /path/to/thegent-hooks debounce my-hook ...
rust_dispatch: disabled (THGENT_HOOKS_RUST not set / use_rust_runtime: false)
rust_dispatch: thegent-hooks binary not found; falling back to shell
```

---

## Opt-in Hooks

The following hooks were created with Phase 2 opt-in dispatch:

### `hooks/debounce.sh` (FR-HOOKS-001, FR-HOOKS-003)

**Purpose**: Batch rapid file edits so expensive downstream hooks are not triggered for every write.

**Rust subcommand**: `debounce`

```
thegent-hooks debounce <hook_name> --timeout <secs> [file]
```

**Shell fallback**: Reads/writes JSON state in `$HOOK_CACHE_DIR/debounce/<hook_name>.json` using `jq`.

**Environment variables**:

| Variable           | Default                        | Description             |
| ------------------ | ------------------------------ | ----------------------- |
| `HOOK_NAME`        | `debounce`                     | Debounce key (required) |
| `DEBOUNCE_TIMEOUT` | `2`                            | Window in seconds       |
| `FILE_PATH`        | (empty)                        | File being edited       |
| `HOOK_CACHE_DIR`   | `/tmp/claude-hook-cache-<uid>` | Cache directory         |

**Exit codes**:

| Code | Meaning                                                      |
| ---- | ------------------------------------------------------------ |
| `0`  | Window elapsed; proceed. Prints JSON array of pending files. |
| `1`  | Within window; skip.                                         |

### `hooks/incremental-check.sh` (FR-HOOKS-002, FR-HOOKS-003)

**Purpose**: Skip re-validation when files are unchanged since last hook run.

**Rust subcommands**: `incremental-check`, `incremental-record`

```
thegent-hooks incremental-check  <hook_name> [files...]
thegent-hooks incremental-record <hook_name> [files...]
```

**Shell fallback**: Computes SHA-256 hashes (b3sum → sha256sum → shasum fallback chain), writes manifest to `$HOOK_CACHE_DIR/manifests/<hook_name>.manifest`.

**Usage**:

```bash
# Check mode (default): exits 1 if changed, 0 if unchanged
hooks/incremental-check.sh my-hook src/foo.py src/bar.py

# Record mode: writes new manifest
hooks/incremental-check.sh --record my-hook src/foo.py src/bar.py
```

**Exit codes (check mode)**:

| Code | Meaning                                                  |
| ---- | -------------------------------------------------------- |
| `0`  | No changes; caller may skip validation                   |
| `1`  | Changes detected (or no prior manifest); caller must run |

**Exit codes (record mode)**:

| Code | Meaning                       |
| ---- | ----------------------------- |
| `0`  | Manifest written successfully |
| `1`  | Error writing manifest        |

### `hooks/circuit-breaker.sh` (FR-HOOKS-004, FR-HOOKS-003)

**Purpose**: Fast-fail when external tools are consistently broken, avoiding wasted invocations.

**Rust subcommands**: `breaker-check`, `breaker-record`, `breaker-reset`, `breaker-success`

```
thegent-hooks breaker-check   <hook_name> [threshold] [cooldown_secs]
thegent-hooks breaker-record  <hook_name>
thegent-hooks breaker-reset   <hook_name>
thegent-hooks breaker-success <hook_name>
```

**Shell fallback**: Reads/writes JSON state in `$HOOK_CACHE_DIR/breakers/<hook_name>.json` using `jq`.

**Subcommands**:

| Subcommand | Rust subcommand   | Description                                         |
| ---------- | ----------------- | --------------------------------------------------- |
| `check`    | `breaker-check`   | Print circuit state; exit 0 if safe, exit 1 if open |
| `record`   | `breaker-record`  | Record a failure                                    |
| `reset`    | `breaker-reset`   | Clear circuit state                                 |
| `success`  | `breaker-success` | Decrement failure count                             |

**Circuit states**:

| State       | stdout      | Exit | Meaning                       |
| ----------- | ----------- | ---- | ----------------------------- |
| `closed`    | `closed`    | `0`  | Normal operation              |
| `open`      | `open`      | `1`  | Too many failures; skip tool  |
| `half-open` | `half-open` | `0`  | Cooldown elapsed; allow probe |

**Environment variables**:

| Variable            | Default                        | Description             |
| ------------------- | ------------------------------ | ----------------------- |
| `BREAKER_THRESHOLD` | `3`                            | Failures before opening |
| `BREAKER_COOLDOWN`  | `300`                          | Cooldown in seconds     |
| `HOOK_CACHE_DIR`    | `/tmp/claude-hook-cache-<uid>` | Cache directory         |

**Usage example**:

```bash
# In a hook that calls an external tool:
state="$(hooks/circuit-breaker.sh check my-tool)"
if [[ "$state" == "open" ]]; then
  echo "Circuit open; skipping my-tool" >&2
  exit 0
fi

if my-tool ...; then
  hooks/circuit-breaker.sh success my-tool
else
  hooks/circuit-breaker.sh record my-tool
fi
```

---

## Subcommand Mapping Reference

| Hook                          | Shell function / usage                           | Rust subcommand      |
| ----------------------------- | ------------------------------------------------ | -------------------- |
| debounce.sh                   | (standalone, env-driven)                         | `debounce`           |
| incremental-check.sh (check)  | `incremental-check.sh <key> [files...]`          | `incremental-check`  |
| incremental-check.sh (record) | `incremental-check.sh --record <key> [files...]` | `incremental-record` |
| circuit-breaker.sh check      | `circuit-breaker.sh check <key>`                 | `breaker-check`      |
| circuit-breaker.sh record     | `circuit-breaker.sh record <key>`                | `breaker-record`     |
| circuit-breaker.sh reset      | `circuit-breaker.sh reset <key>`                 | `breaker-reset`      |
| circuit-breaker.sh success    | `circuit-breaker.sh success <key>`               | `breaker-success`    |

---

## Adding Opt-in Dispatch to a New Hook

Follow this pattern to add Phase 2 Rust dispatch to any hook script:

```bash
#!/usr/bin/env zsh
# my-hook.sh — Description of what this hook does.
# @trace FR-HOOKS-003
set -euo pipefail

# --- Portable script path resolution ---
if [ -n "${ZSH_VERSION:-}" ]; then
  _SCRIPT_PATH="${(%):-%x}"
elif [ -n "${BASH_VERSION:-}" ]; then
  _SCRIPT_PATH="${BASH_SOURCE[0]}"
else
  _SCRIPT_PATH="$0"
fi
_SCRIPT_DIR="${_SCRIPT_PATH%/*}"

# --- Source the dispatch library ---
source "${_SCRIPT_DIR}/lib/rust_dispatch.sh"

# --- Parse arguments ---
HOOK_KEY="${1:-}"
[[ -z "${HOOK_KEY}" ]] && { echo "usage: $0 <hook_key> [args...]" >&2; exit 1; }
shift
EXTRA_ARGS=("$@")

# --- Attempt Rust dispatch ---
if hook_rust_dispatch "my-rust-subcommand" "${HOOK_KEY}" "${EXTRA_ARGS[@]}"; then
  exit $?
fi

# --- Shell fallback implementation ---
# ... your shell implementation here ...
```

---

## Testing

BATS tests for all Phase 2 components live in:

```
tests/test_rust_dispatch.bats
```

### Running the Tests

```bash
# Requires: bats-core
bats tests/test_rust_dispatch.bats

# Or via task (if configured):
task test:bats
```

### Test Coverage

The test file contains 20 tests across 4 groups:

| Group                  | Tests | Covers                                                                                                                         |
| ---------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------ |
| `rust_dispatch.sh`     | 5     | enable/disable logic, binary resolution, dispatch, exit code forwarding                                                        |
| `debounce.sh`          | 4     | Rust delegate, shell fallback, window active, window elapsed                                                                   |
| `incremental-check.sh` | 5     | Rust check/record delegates, no manifest, unchanged files, changed files                                                       |
| `circuit-breaker.sh`   | 6     | Rust check/record/reset delegates, initial closed, threshold opens, reset clears, success decrements, half-open after cooldown |

### Test Stub Pattern

Tests use a minimal stub binary that mimics the thegent-hooks interface:

```bash
_write_stub_binary() {
  local dest="$1"
  local fail_cmd="${2:-__none__}"
  cat > "${dest}" << 'STUBEOF'
#!/usr/bin/env bash
cmd="${1:-}"; shift || true
[[ "$cmd" == "${fail_cmd}" ]] && { echo "STUB_FAIL: $cmd" >&2; exit 5; }
case "$cmd" in
  debounce)          echo '["stub_file.py"]'; exit 0 ;;
  incremental-check) exit 0 ;;
  incremental-record) exit 0 ;;
  breaker-check)     echo "closed"; exit 0 ;;
  breaker-record)    exit 0 ;;
  breaker-reset)     exit 0 ;;
  breaker-success)   exit 0 ;;
  *) echo "STUB: unknown $cmd" >&2; exit 2 ;;
esac
STUBEOF
  chmod +x "${dest}"
}
```

---

## Relationship to Other Phases

```
hooks/lib/common.sh          ← Phase 2 infra: hook_rust_runtime_invoke()
hooks/lib/rust_dispatch.sh   ← Phase 2 (this): hook_rust_dispatch() per-hook dispatch
hooks/lib/common-rust.sh     ← Phase 3: replaces entire common.sh at runtime

Individual hooks (debounce.sh, incremental-check.sh, circuit-breaker.sh)
  → source rust_dispatch.sh
  → call hook_rust_dispatch()
  → if disabled/absent → shell fallback
  → if enabled → thegent-hooks <subcommand>
```

Phase 2 and Phase 3 coexist: a hook can use Phase 2 dispatch at the script entry point while `common.sh` internals may simultaneously be running under Phase 3's binary wrappers. The dispatch is additive, not mutually exclusive.

---

## Troubleshooting

### Binary not found

```
rust_dispatch: thegent-hooks binary not found; falling back to shell
```

Build the binary:

```bash
cd crates && cargo build --release
# Binary at: crates/target/release/thegent-hooks
```

Or set an explicit path:

```bash
export THGENT_HOOKS_RUST_BIN=/path/to/thegent-hooks
```

### Dispatch silently disabled

Enable verbose logging:

```bash
export THGENT_HOOKS_RUST_VERBOSE=1
```

### Hook exits with unexpected code

Check that `THGENT_HOOKS_RUST` is set correctly in the calling environment. The env var takes precedence over `hook-config.yaml`.

### Cache directory issues

The shell fallback writes state to `$HOOK_CACHE_DIR` (defaults to `/tmp/claude-hook-cache-$(id -u)`). Ensure the directory is writable or override:

```bash
export HOOK_CACHE_DIR=/your/writable/cache
```
