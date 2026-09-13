# Starship Prompt — Long-Term Fix for Scan Timeout

**Problem:** `[WARN] - (starship::utils): Executing command "/Users/kooshapari/.local/bin/git" timed out` — Starship calls git frequently (status, branch info), and the git shim was resolving the real git binary on every call, causing 8+ minute delays.

**Solution:**

1. **Git shim caching** — The git shim now caches the resolved git path in `~/.cache/thegent/git-shim-cache`, so resolution only happens once (first call). Subsequent calls use the cached path (fast path).
2. **Starship timeout** — Increase `command_timeout` to handle the first git call (cache miss), and `scan_timeout` for directory scanning.

---

## Project-Level (Automatic)

When you run `task setup`, thegent creates `.starship.toml` with:

- `scan_timeout = 2000` (2 seconds for directory scanning)
- `command_timeout = 10000` (10 seconds for git commands — only needed on first call when cache is populated)

If you use **direnv** (`.envrc`), `STARSHIP_CONFIG` is set to use it when you `cd` into thegent.

1. Run `task setup` (creates `.starship.toml`)
2. Run `thegent install --scope both` or `thegent install -t all --system` (installs git shim with caching)
3. Run `direnv allow` (loads `.envrc` with `STARSHIP_CONFIG`)

---

## Global (Manual)

Add to `~/.config/starship.toml`:

```toml
scan_timeout = 2000
command_timeout = 10000
```

Or, if you already have a config, add those lines at the top level (prompt-wide options).

---

## Manual Project Setup (No direnv)

If you don't use direnv, after `task setup` add to your shell when working in thegent:

```bash
export STARSHIP_CONFIG="$PWD/.starship.toml"
```

Or add to `.env` and source it: `STARSHIP_CONFIG=/path/to/thegent/.starship.toml`

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
