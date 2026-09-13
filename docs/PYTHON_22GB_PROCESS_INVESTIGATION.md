# 22GB Python Process Investigation

**Symptom:** Single Python process using ~22GB RAM, 1 thread. Suspected: linter or language server.

---

## Likely Culprits

| Process                       | Language   | Single-threaded | Memory-heavy | Notes                               |
| ----------------------------- | ---------- | --------------- | ------------ | ----------------------------------- |
| **pylsp** (python-lsp-server) | Python     | Yes (Jedi)      | Yes          | Default LSP when Pylance disabled   |
| **jedi-language-server**      | Python     | Yes             | Yes          | Jedi-based completion               |
| **Jedi** (in pylsp)           | Python     | Yes             | Yes          | Builds full symbol table            |
| **mypy** (dmypy daemon)       | Python     | Yes             | Yes          | Full type-check indexing            |
| **Pylance/Pyright**           | TypeScript | Yes             | Yes          | **Not Python** – would show as Node |

**Conclusion:** A 22GB **Python** process is almost certainly **pylsp** or **jedi-language-server** (or mypy daemon). Pylance uses Pyright (TypeScript/Node), so it would appear as a Node process, not Python.

---

## Root Cause: Workspace Scope

The workspace root (`kush`) contains:

- **115+ directories** at root
- **46+ pyproject.toml** files across subprojects
- **Multiple .venv** (root, thegent, crun, usage, etc.)
- **Subprojects:** thegent, trace, agentapi, 4sgm, sharecli, etc.

When the IDE opens the full workspace, the Python language server indexes **everything** unless explicitly excluded:

| Config                         | Excludes                      | Gap                                      |
| ------------------------------ | ----------------------------- | ---------------------------------------- |
| **thegent/pyrightconfig.json** | `node_modules`, `__pycache__` | No `.venv`, `.worktrees`, other projects |
| **trace/pyrightconfig.json**   | Better (venv, etc.)           | Only applies when analyzing trace        |
| **agentapi/atomsAgent**        | Good excludes                 | Only applies in that subdir              |

**Missing excludes** that cause bloat:

- `**/.venv/**` (site-packages with huge libs)
- `**/.worktrees/**`
- `**/node_modules/**`
- Other project roots (4sgm, agentapi, sharecli, etc.)
- `**/site-packages/**`
- `**/.git/**`
- `**/__pycache__/**` (already in some configs)

---

## Why 22GB + 1 Thread?

1. **Single-threaded:** Jedi (pylsp’s engine) and mypy are largely single-threaded for analysis.
2. **Memory:** Full symbol table for the whole workspace, including venv site-packages if not excluded.
3. **Inefficiency:** Indexing pandas, numpy, etc. in `.venv` is unnecessary and very expensive.

---

## Mitigations

### 1. Add Aggressive Excludes (Immediate)

Create or update **root-level** `pyrightconfig.json`:

```json
{
  "exclude": [
    "**/node_modules",
    "**/__pycache__",
    "**/.venv",
    "**/venv",
    "**/.worktrees",
    "**/site-packages",
    "**/.git",
    "**/.pytest_cache",
    "**/.mypy_cache",
    "**/.ruff_cache",
    "**/dist",
    "**/build",
    "**/htmlcov"
  ]
}
```

### 2. Restrict Analysis Scope

**Option A – Use `include` in subproject configs:**

```json
{
  "include": ["src", "tests"],
  "exclude": ["**/.venv", "**/node_modules", "..."]
}
```

**Option B – Open only the project you care about:**

- Open `kush/thegent` as workspace instead of `kush`
- Or use a multi-root workspace and limit Python analysis to specific folders

### 3. Switch to Pylance (If Using pylsp)

Pylance (Pyright) is:

- Written in TypeScript (runs as Node)
- Generally more memory-efficient
- Better at excluding venv by default

**Check:** Cursor/VS Code → Settings → `python.languageServer` → should be `Pylance` (default).

If it’s `Jedi` or `None` (fallback to pylsp), switch to Pylance:

```json
"python.languageServer": "Pylance"
```

### 4. Limit Extra Indexing

Pylance settings:

```json
"python.analysis.extraPaths": [],
"python.analysis.autoSearchPaths": false,
"python.analysis.extraPaths": ["thegent/src"]
```

### 5. Disable Python Analysis for Non-Python Folders

In `.vscode/settings.json` or Cursor settings:

```json
"python.analysis.extraPaths": [],
"files.watcherExclude": {
  "**/.venv/**": true,
  "**/node_modules/**": true,
  "**/.worktrees/**": true
}
```

---

## Verification

1. **Identify the process:**

   ```bash
   ps aux | grep -E "python|python3" | grep -v grep
   # or
   top -o mem
   ```

2. **Check which Python LSP is active:**
   - Cursor: Settings → search "python language server"
   - Or: Command Palette → "Python: Select Language Server"

3. **After applying excludes:**
   - Restart IDE
   - Expect memory to drop to roughly 1–4GB for typical usage

---

## Quick Fix Summary

| Action                                                 | Effect                                     |
| ------------------------------------------------------ | ------------------------------------------ |
| Add root `pyrightconfig.json` with aggressive excludes | Stops indexing venv and other project dirs |
| Set `python.languageServer` to `Pylance`               | Uses more efficient Node-based LSP         |
| Open `thegent` only instead of full `kush`             | Limits analysis scope                      |
| Add `**/.venv` to all pyrightconfigs                   | Avoids indexing site-packages              |

---

## Files to Update

| File                                       | Change                              |
| ------------------------------------------ | ----------------------------------- |
| `kush/pyrightconfig.json` (create)         | Root-level excludes                 |
| `thegent/pyrightconfig.json`               | Add `**/.venv`, `**/.worktrees`     |
| `trace/pyrightconfig.json`                 | Already has venv; ensure consistent |
| `.vscode/settings.json` or Cursor settings | `python.languageServer: Pylance`    |
