# Indexing and Optimization Systems — Reference

> **Purpose**: Central reference for codebase indexing, search, and performance optimizations.
> **Status**: Reference | **Date**: 2026-02-16

---

## 1. What Exists Today

| System                     | What It Does                                    | Command / Config                                        | Status     |
| -------------------------- | ----------------------------------------------- | ------------------------------------------------------- | ---------- |
| **Spotlight (macOS)**      | Excludes heavy dirs from mds_stores indexing    | `thegent mcp spotlight-exclude`                         | ✓ In setup |
| **Starship**               | Reduces prompt scan timeout in large repos      | `.starship.toml` (scan_timeout=2000)                    | ✓ In setup |
| **Catalog prewarm**        | Warms model catalog at MCP startup              | `prewarm_catalog()` in lifespan                         | ✓          |
| **Git index prewarm**      | Warms git index for common commands             | `prewarm_git_index()` in lifespan                       | ✓          |
| **Quality index**          | Cached quality scores (TB2, SWE-Bench, AIME)    | `quality_index_cache_ttl_sec`, `quality_index_weight_*` | ✓ Config   |
| **Auto-prune**             | Kills orphan Node/LSP processes on Stop         | `THGENT_AUTO_PRUNE=1`                                   | Opt-in     |
| **Uni-mount MCP**          | Single thegent URL, fewer duplicate MCPs        | `thegent mcp migrate-unimount all`                      | One-time   |
| **Spotlight SessionStart** | Auto spotlight-exclude on first session (macOS) | `session-start-spotlight-exclude.sh`                    | Opt-in     |

---

## 2. Spotlight Exclusions (macOS)

`thegent mcp spotlight-exclude` excludes these from mds_stores:

- `~/.thegent`, `~/.claude`, `~/.cursor`
- `node_modules`, `.venv`, `venv`, `dist`, `build`
- `.claude`, `.thegent` (project)

**When**: Runs in `task setup` (macOS). Opt-in: `THGENT_SPOTLIGHT_EXCLUDE_ON_SESSION_START=1` for first SessionStart.

---

## 3. Cursor Codebase Indexing

Cursor indexes the workspace for semantic search and @-mentions. Heavy dirs (node_modules, .git, build) slow indexing and increase memory.

**Recommended**: Add `.cursorignore` in project root to exclude heavy dirs from Cursor's index. Cursor respects `.cursorignore` (or `.cursorindexingignore` in some versions) similar to `.gitignore`.

**Example `.cursorignore`** (add to project root):

```
node_modules/
.venv/
venv/
dist/
build/
docs-dist/
.git/
__pycache__/
*.pyc
.thegent/
.claude/
.process-compose/
.coverage
.pytest_cache/
```

---

## 4. LSP and Code Intelligence

| Item                          | Status   | Notes                                                    |
| ----------------------------- | -------- | -------------------------------------------------------- |
| **MTSP-04: LSP multiplexing** | Pending  | Single Serena daemon instead of per-session LSP          |
| **Per-session LSP**           | Current  | Each agent tab spawns clangd, gopls, rust-analyzer, etc. |
| **Type checker sharing**      | Research | Single tsserver/pyright for workspace; IDE-dependent     |

---

## 5. Prewarm and Caching

| Component           | Location                                     | Purpose                                    |
| ------------------- | -------------------------------------------- | ------------------------------------------ |
| `prewarm_catalog`   | `mcp_server.py` lifespan                     | Load model catalog before first request    |
| `prewarm_git_index` | `tools/terminal.py`                          | Warm git index for common commands         |
| `quality_index`     | `config.py`                                  | Cache TTL 300s; weights for TB2, SWE, AIME |
| `speed_index`       | `SPEED_QUALITY_INDEX_IMPLEMENTATION_PLAN.md` | Planned; from proxy metrics                |

---

## 6. Quick Setup Checklist

| Step | Command / Config                   | When                                                      |
| ---- | ---------------------------------- | --------------------------------------------------------- |
| 1    | `task setup`                       | One-time (creates .starship.toml, runs spotlight-exclude) |
| 2    | `direnv allow`                     | One-time (loads .envrc with STARSHIP_CONFIG)              |
| 3    | `export THGENT_AUTO_PRUNE=1`       | Add to .env or shell profile                              |
| 4    | `thegent mcp migrate-unimount all` | One-time                                                  |
| 5    | Add `.cursorignore`                | One-time (see §3)                                         |

---

## 7. Agent Directory Listing (ls -l Avoidance)

**Problem:** Agents run `ls -l` in the current shell on their own instructions. In project root (with node_modules, .venv, etc.), this can take minutes.

**Long-term strategies:**

| Strategy         | Where                            | What                                                                                                                 |
| ---------------- | -------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Prefer fd**    | Skills, CLAUDE.md, .cursor/rules | Use `fd -t f -d 1` or `fd -t d -d 1` instead of `ls -l`; fd excludes .git by default, add `-E node_modules -E .venv` |
| **List subdirs** | Agent instructions               | Run `ls -l src/` or `ls -l docs/` instead of project root                                                            |
| **Use ls -1**    | Agent instructions               | When only names needed, `ls -1` is faster than `ls -l` (no stat)                                                     |
| **.agentignore** | Project root                     | File listing dirs to exclude; agents read before ls (or inject into prompt)                                          |
| **Session env**  | thegent run/bg                   | Set `THGENT_LS_EXCLUDE`; agent shell sources it                                                                      |

**Recommended agent instruction (add to skills, CLAUDE.md, rules sync):**

> When listing directory contents: prefer `fd -t f -d 1` or `fd -t d -d 1` (excludes .git; add `-E node_modules -E .venv -E dist` for heavy dirs). If using ls: run in subdirs (`ls -l src/`, `ls -l docs/`) not project root; or use `ls -1` when only names needed. Avoid `ls -l` in project root when node_modules/.venv exist.

---

## 8. Unified File Search (fd + rg)

**Canonical pair for agents (Claude Code, Cursor, Codex):**

| Task            | Use                              | Replaces   |
| --------------- | -------------------------------- | ---------- |
| List files/dirs | `fd -t f -d 1` or `fd -t d -d 1` | ls, find   |
| Find by name    | `fd pattern -e ext`              | find -name |
| Search content  | `rg pattern`                     | grep       |

Both respect `.gitignore`. Add `-E node_modules -E .venv -E dist` for heavy dirs. When IDE provides @codebase or read_file, use those first.

**Grep timeout**: Hooks use `RG_TIMEOUT_SEC` (default 30) to cap rg; avoids 4m+ runs. For manual runs: `timeout 30 rg "pattern" path` or `RG_TIMEOUT_SEC=30`.

**Full research:** [AGENT_FILE_SEARCH_UNIFIED_TOOL_RESEARCH.md](../research/AGENT_FILE_SEARCH_UNIFIED_TOOL_RESEARCH.md) — includes `thegent_files` MCP tool proposal.

### 8.1 Layered Access Model (Enhanced Baseline)

| Layer        | File                           | Web                | Batch Edit                |
| ------------ | ------------------------------ | ------------------ | ------------------------- |
| **1. IDE**   | read_file, list_dir, @codebase | —                  | N× edit                   |
| **2. MCP**   | thegent_files (proposed)       | thegent_ddg_search | thegent_apply_transaction |
| **3. Shell** | fd, rg                         | —                  | sed (risky)               |

**Rule:** Prefer Layer 1 when available; Layer 2 when MCP connected; Layer 3 for terminal fallback.

**Full audit:** [AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN.md](../research/AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN.md) — file reads, web search/scrape, batch edits, kilo/roo/OpenCode, optimizations.

---

## 9. Gaps and Roadmap

| Gap                          | Effort                    | Impact                                                  |
| ---------------------------- | ------------------------- | ------------------------------------------------------- |
| **.cursorignore**            | 1–2 min                   | High — reduces Cursor index size and memory             |
| **Agent ls instructions**    | Add to skills, rules sync | High — prevents 5m+ ls in heavy dirs                    |
| **.agentignore**             | New file + agent read     | Medium — project-level exclusions                       |
| **thegent_files MCP tool**   | 15–25 tool calls          | High — unified fd+rg via MCP across platforms           |
| **MTSP-04 LSP multiplexing** | 15–25 tool calls          | High — eliminates N× LSP processes                      |
| **Cursor indexing docs**     | Doc only                  | Medium — clarify .cursorignore vs .cursorindexingignore |
| **Type checker sharing**     | Research                  | High — IDE-specific                                     |

---

_Cross-ref: [AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN.md](../research/AGENT_ACCESS_AND_OPTIMIZATION_AUDIT_PLAN.md) · [AGENT_FILE_SEARCH_UNIFIED_TOOL_RESEARCH.md](../research/AGENT_FILE_SEARCH_UNIFIED_TOOL_RESEARCH.md) · [SWARM_PROCESS_OPTIMIZATIONS.md](./SWARM_PROCESS_OPTIMIZATIONS.md) · [STARSHIP_SETUP.md](./STARSHIP_SETUP.md) · [PROCESS_OPTIMIZATION_PLAN.md](../plans/PROCESS_OPTIMIZATION_PLAN.md) · [MEMORY_OPTIMIZATION_LONG_TERM_PLAN.md](../research/MEMORY_OPTIMIZATION_LONG_TERM_PLAN.md)_

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
