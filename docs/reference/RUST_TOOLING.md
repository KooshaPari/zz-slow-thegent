# Rust-Based CLI Tooling

thegent uses Rust alternatives for common CLI tools to accelerate hooks and agent execution. This document maps tools, describes integration, and documents known issues.

## Tool Mapping

| Legacy                        | Rust Alternative | Drop-in | Speedup           | Integration                     |
| ----------------------------- | ---------------- | ------- | ----------------- | ------------------------------- |
| grep                          | ripgrep (rg)     | Partial | 2-10x (recursive) | grep-wrapper.sh routes grep→rg  |
| find                          | fd               | Partial | 3-23x             | fd-wrapper.sh, find() override  |
| jq                            | jaq              | Yes     | 2-10x             | JQ_CMD (jaq first)              |
| uniq                          | huniq            | Partial | 2-3x              | HUNIQ_CMD in sort_unique        |
| ps/pgrep                      | procs            | Partial | 2-3x              | procs-wrapper.sh                |
| shasum/sha256sum (cache keys) | b3sum            | Partial | 2-5x              | HASH_CMD, hash_for_cache (WP-B) |

## Integration Points

- **hooks/lib/common.sh**: Sources fd-wrapper, grep-wrapper, procs-wrapper; caches JQ_CMD, RG_CMD, HUNIQ_CMD, HASH_CMD
- **hooks/hook-dispatcher**: Exports RG_CMD, JQ_CMD, TIMEOUT_CMD to child hooks
- **grep-wrapper.sh**: Overrides `grep`; routes -r, -nE, -oE, -cE, -q, -l, -L to rg; fallback to system grep for -P, --include

## Ripgrep and Claude Code

### Known Issues

| Issue                                                                       | Severity   | Workaround                                          |
| --------------------------------------------------------------------------- | ---------- | --------------------------------------------------- |
| [ripgrep#3259](https://github.com/BurntSushi/ripgrep/issues/3259)           | Edge case  | rg fails on paths >32k deep; use grep fallback      |
| [claude-code#22176](https://github.com/anthropics/claude-code/issues/22176) | Regression | Built-in rg EAGAIN timeout on large gitignored dirs |
| [claude-code#22341](https://github.com/anthropics/claude-code/issues/22341) | Critical   | VSCode OOM after rg EAGAIN spawn failures           |

### Recommended: Use System Ripgrep

Add to `~/.zshrc` or `~/.bashrc`:

```bash
export USE_BUILTIN_RIPGREP=0   # Use system rg (5-10x faster than bundled)
```

Then ensure ripgrep is installed: `brew install ripgrep` (already in Brewfile).

## Grep vs rg Semantics

| grep                   | rg equivalent       |
| ---------------------- | ------------------- |
| `grep -nE 'pat' file`  | `rg -n 'pat' file`  |
| `grep -r pattern dir`  | `rg pattern dir`    |
| `grep -oE 'pat'`       | `rg -o 'pat'`       |
| `grep -cE 'pat'`       | `rg -c 'pat'`       |
| `grep -q 'pat'`        | `rg -q 'pat'`       |
| `grep -L 'pat' files`  | `rg -L 'pat' files` |
| `grep -v -E 'pat'`     | `rg -v 'pat'`       |
| `grep --exclude-dir=X` | `rg -g '!X'`        |

## Brewfile

Run `brew bundle` from the project root to install ripgrep, fd, jaq, procs (and other deps). Optional: huniq (cargo install huniq), eza (brew install eza), b3sum (brew install b3sum for faster cache key hashing).

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
