<DONE>
# Doctor Shim Check Feature - Implementation Status

> **WORK_STREAM ID:** scratch-doctor-shim-check
> **Priority:** P2
> **Status:** ✅ Complete

## Summary

This work item implements shim version and binary availability checking in `thegent doctor`.

## Implementation Status

### ✅ Implementation Complete

The shim check feature is implemented in `src/thegent/doctor.py`:

1. **Shim Binary Check** (`_check_shim_binaries()`, line 557):
   - Checks `thegent-hooks` binary availability and version
   - Checks `thegent-shims` binary availability and version
   - Reports binary paths and versions

2. **Shim Details Check** (`_check_environment()`, lines 503-540):
   - Checks individual shim versions (git, grep, find, etc.)
   - Verifies target binary availability
   - Reports shim → target mappings

### Implementation Details

#### Shim Binary Check

```python
# src/thegent/doctor.py
def _check_shim_binaries() -> list[CheckResult]:
    """Check thegent-hooks and thegent-shims (Rust) binary version and availability."""
    results = []

    for name in ["thegent-hooks", "thegent-shims"]:
        r = CheckResult(name, "Shim Binaries")
        binary_path = shutil.which(name)

        if binary_path:
            # Check version
            try:
                result = run_subprocess_optimized([name, "--version"], capture_output=True, timeout=5)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    r.status = "ok"
                    r.message = f"{name} {version} at {binary_path}"
            except Exception:
                r.status = "warn"
                r.message = f"{name} found but version check failed"
        else:
            r.status = "warn"
            r.message = f"{name} not found in PATH"
            r.fix_hint = f"Build {name} binary or install via package manager"

        results.append(r)

    return results
```

#### Individual Shim Details Check

```python
# Enhanced: Check shim versions and binary availability
for shim_name in ["git", "grep", "find", "codex", "copilot"]:
    shim_path = shutil.which(shim_name)
    if shim_path and shim_path.startswith(str(shim_dir)):
        r_shim = CheckResult(f"{shim_name} Shim Details", "Environment")

        # Check if it's a shell script shim
        if Path(shim_path).suffix == ".sh" or Path(shim_path).is_file():
            # Read shim to find target binary
            try:
                with open(shim_path) as f:
                    content = f.read()
                    # Extract target binary from shim content
                    # ...
            except Exception:
                pass

        # Check target binary availability
        target = _resolve_shim_target(shim_name)
        if target:
            version_info = _get_binary_version(target)
            r_shim.status = "ok"
            r_shim.message = f"{shim_name} -> {target} ({version_info})"
        else:
            r_shim.status = "warn"
            r_shim.message = f"{shim_name} shim target not found"

        results.append(r_shim)
```

### Check Categories

1. **Rust Binary Shims**:
   - `thegent-hooks` - Hook execution binary
   - `thegent-shims` - Tool shim binary (in development)

2. **Shell Script Shims**:
   - `git` - Git wrapper with lock coordination
   - `grep` - Ripgrep wrapper
   - `find` - fd-find wrapper
   - `codex`, `copilot` - Agent binary wrappers

### Usage

```bash
# Run doctor to check shim status
thegent doctor

# Output includes:
# - Shim Binaries: thegent-hooks, thegent-shims
# - Environment: Individual shim details (git, grep, find, etc.)
```

### Output Example

```
Shim Binaries
├─ thegent-hooks: ✓ v0.1.0 at /usr/local/bin/thegent-hooks
└─ thegent-shims: ⚠ not found in PATH

Environment
├─ git Shim Details: ✓ git -> /usr/bin/git (2.42.0)
├─ grep Shim Details: ✓ grep -> /usr/local/bin/rg (14.0.0)
└─ find Shim Details: ✓ find -> /usr/local/bin/fd (9.0.0)
```

## Acceptance Criteria

- [x] Shim binary version checking implemented
- [x] Individual shim details checking implemented
- [x] Target binary availability verification
- [x] Version reporting
- [x] Fix hints for missing shims
- [x] Integration with `thegent doctor` command

## References

- [doctor.py](../../src/thegent/doctor.py) - Implementation
- [scratchpad/session_review.md](../scratchpad/session_review.md) - Original requirement
- [WORK_STREAM.md](../reference/WORK_STREAM.md)
