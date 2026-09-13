# Shell Configuration Guide

This document describes thegent's Zsh shell configuration architecture,
the audit tooling, and how to consolidate or extend the shell setup.

---

## File Layout

All shell configuration lives under `shell/`:

```
shell/
  .zshrc                  # Main user shell profile (install to ~/.zshrc)
  .zsh_bundle.zsh         # Core utilities, aliases, safe path helpers
  .zsh_optimization.zsh   # Eval caching, lazy loading, startup profiling
  .zsh_advanced.zsh       # Multi-level cache, async loading, circuit breakers
  .zsh_safeguards.zsh     # Resource limits, command safeguards, fork guard
  .zsh_slim.zsh           # Minimal agent-only profile (<10 ms startup)
  thegent.zshrc.agent     # Agent shell profile with preexec/precmd hooks
  zshrc.local.template    # Template for user customizations (never overwritten)
```

### Sourcing Chain

```
~/.zshrc  (= shell/.zshrc)
  └── ~/.zshenv         (system environment)
  └── .zsh_bundle.zsh
        └── .zsh_optimization.zsh
        └── .zsh_safeguards.zsh
        └── .zsh_advanced.zsh
  └── ~/.zshrc.local    (user customizations, not overwritten)
```

### Agent vs Interactive Shells

| Profile               | Purpose                             | Startup target |
| --------------------- | ----------------------------------- | -------------- |
| `.zshrc`              | Human interactive shell             | < 100 ms       |
| `.zsh_slim.zsh`       | AI agent sub-shells                 | < 10 ms        |
| `thegent.zshrc.agent` | Agent shell with structured logging | < 50 ms        |

---

## Audit Tool

The Python auditor (`src/thegent/tools/shell_config.py`) provides:

| Class / Method                                       | Purpose                                                      |
| ---------------------------------------------------- | ------------------------------------------------------------ |
| `ShellConfigFile.parse(path)`                        | Parse a single file for functions, aliases, and source calls |
| `ShellConfigAuditor.audit(dirs)`                     | Walk directories and return all config files                 |
| `ShellConfigAuditor.find_duplicates(configs)`        | Find function names defined in more than one file            |
| `ShellConfigAuditor.find_duplicate_aliases(configs)` | Find alias names defined in more than one file               |
| `ShellConfigAuditor.generate_consolidated(configs)`  | Merge all files into one script with origin comments         |
| `ShellConfigAuditor.check_sourcing_order(configs)`   | Detect missing sources, circular chains, empty files         |
| `ShellConfigAuditor.sourcing_graph(configs)`         | Build a name -> sourced-files mapping                        |

### Running the Audit

```bash
# Quick human-readable report
scripts/shell-audit.sh

# Audit specific directories
scripts/shell-audit.sh --dir shell --dir scripts/lib

# JSON output (for CI or further processing)
scripts/shell-audit.sh --json

# Write consolidated output
scripts/shell-audit.sh --output-consolidated /tmp/thegent-consolidated.zsh
```

Exit codes: `0` = clean, `1` = issues found, `2` = usage error.

### Python API

```python
from pathlib import Path
from thegent.tools.shell_config import ShellConfigAuditor

auditor = ShellConfigAuditor()
configs = auditor.audit([Path("shell"), Path("scripts")])

# Find duplicate function definitions
dupes = auditor.find_duplicates(configs)
for func_name, paths in dupes.items():
    print(f"{func_name} defined in {len(paths)} files")

# Check sourcing relationships
issues = auditor.check_sourcing_order(configs)
for issue in issues:
    print(f"[WARN] {issue}")

# Generate merged output
merged = auditor.generate_consolidated(configs)
Path("/tmp/merged.zsh").write_text(merged)
```

---

## Findings from Initial Audit

The initial audit of `shell/` identified the following:

### Functions defined in multiple files

| Function               | Files                                        |
| ---------------------- | -------------------------------------------- |
| `_thegent_timeout_cmd` | `.zsh_safeguards.zsh`, `.zsh_advanced.zsh`   |
| `zshexit`              | `.zsh_optimization.zsh`, `.zsh_advanced.zsh` |

**Recommendation**: Keep `_thegent_timeout_cmd` only in `.zsh_advanced.zsh` (which is sourced
after safeguards) and have `.zsh_safeguards.zsh` delegate to it via a guard. For `zshexit`,
consolidate into `.zsh_advanced.zsh` since it runs last and registers the cleanup job.

### Sourcing Relationships

`.zsh_bundle.zsh` sources all three sub-files:

```
.zsh_bundle.zsh -> .zsh_optimization.zsh
.zsh_bundle.zsh -> .zsh_safeguards.zsh
.zsh_bundle.zsh -> .zsh_advanced.zsh
```

`.zshrc` redundantly sources `.zsh_safeguards.zsh` a second time (already loaded by bundle).

**Recommendation**: Remove the redundant `source` of `.zsh_safeguards.zsh` from `.zshrc`.

### `.zshrc.optimized` / Redundant Files

No `.zshrc.optimized` file was found in the repository. If one exists on disk after
installation, it can safely be removed—`shell/.zshrc` is the canonical source.

---

## Adding a New Shell Function

1. Determine which file owns the concern:
   - Performance / caching → `.zsh_optimization.zsh`
   - Safety / resource limits → `.zsh_safeguards.zsh`
   - Advanced async / circuit breaker → `.zsh_advanced.zsh`
   - Core utilities / path helpers → `.zsh_bundle.zsh`
   - Agent-only → `.zsh_slim.zsh` or `thegent.zshrc.agent`
2. Add the function to the appropriate file.
3. Run `scripts/shell-audit.sh` to verify no duplicates were introduced.
4. Ensure all new functions are prefixed with `_thegent_` (private) or are listed in
   the exports section at the bottom of the relevant file.

---

## Installation

```bash
# Install main user shell profile
cp shell/.zshrc ~/.zshrc

# Install sub-files (keep in sync)
cp shell/.zsh_bundle.zsh ~/.zsh_bundle.zsh
cp shell/.zsh_optimization.zsh ~/.zsh_optimization.zsh
cp shell/.zsh_advanced.zsh ~/.zsh_advanced.zsh
cp shell/.zsh_safeguards.zsh ~/.zsh_safeguards.zsh

# Copy local template (only if it doesn't already exist)
[[ -f ~/.zshrc.local ]] || cp shell/zshrc.local.template ~/.zshrc.local
```

The agent profile (`.zsh_slim.zsh`) is sourced automatically by the thegent agent
runner—it does not need to be installed into `~`.

---

## See Also

- `src/thegent/tools/shell_config.py` — Python auditor implementation
- `scripts/shell-audit.sh` — Shell audit runner
- `tests/tools/test_shell_config.py` — Test suite
- `docs/guides/anti-patterns.md` — Shell anti-patterns to avoid
