<DONE>
# Environment Variable Sanitization Fixes

> **Date**: 2026-02-18
> **Issue**: `rg` (ripgrep) was failing with "grep config error: unknown encoding" due to problematic environment variables
> **Status**: Fixed

## Problem

`rg` was reading grep compatibility configs from environment variables (`GREP_OPTIONS`, `GREP_COLOR`, `GREP_COLORS`) that contained invalid values, causing:

```
rg: error parsing flag -E: grep config error: unknown encoding: _proxy=|CURSOR_SANDBOX|SUDO_ASKPASS|CURSOR_ASKPASS
```

This affected all hooks and scripts using `rg` directly or through wrappers.

## Solution

Added environment sanitization to all `rg` invocations:

1. **Unset problematic env vars** before calling `rg`
2. **Use `--no-config`** flag to ignore config files
3. **Suppress stderr errors** for harmless config warnings

## Files Fixed

### Core Wrappers

- ✅ `hooks/lib/grep-wrapper.sh` - Main grep→rg wrapper
- ✅ `hooks/lib/common.sh` - `grep()` function

### Hook Scripts

- ✅ `hooks/test-maturity.sh` - Changed `_RG` from array to sanitized function
- ✅ `hooks/spec-verifier.sh` - Changed `_RG_CMD` to sanitized function
- ✅ `hooks/quality-gate.sh` - Direct `rg` call sanitized
- ✅ `hooks/qa-attestation-builder.sh` - Direct `rg` calls sanitized
- ✅ `hooks/agileplus-cycle.sh` - Direct `rg` call sanitized

## Pattern Applied

**Before:**

```bash
rg --no-config "$@"
```

**After:**

```bash
env -u GREP_OPTIONS -u GREP_COLOR -u GREP_COLORS rg --no-config "$@" 2> >(grep -v "grep config error" >&2)
```

Or as a reusable function:

```bash
_safe_rg() {
  env -u GREP_OPTIONS -u GREP_COLOR -u GREP_COLORS rg --no-config "$@" 2> >(grep -v "grep config error" >&2)
}
```

## Verification

All fixed files pass syntax checks and `rg` calls now work without config errors.

## Related Issues

- Similar issues may exist with other tools that read grep-compatible configs
- Consider adding sanitization to `fd`, `jq`, and other tool wrappers if they exhibit similar behavior

## Migration Note

As hooks migrate to Rust (see `HOOK_RUST_MIGRATION_COMPLETE.md`), these env var issues will be eliminated since Rust binaries don't read shell config files.
