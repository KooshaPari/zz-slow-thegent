<DONE>
# Agent Access and Optimization — Audit and Plan

> **Purpose**: Audit file reads, web search/scrape, other accesses; research kilo, roo, OpenCode, batch edits; propose optimizations and enhanced baseline strategy.
> **Status**: Research + Plan | **Date**: 2026-02-16

---

## 1. Executive Summary

| Domain          | Current State                          | Gap                                                     | Recommendation                             |
| --------------- | -------------------------------------- | ------------------------------------------------------- | ------------------------------------------ |
| **File reads**  | IDE read_file, list_dir; shell ls/grep | No unified MCP tool; agents use ls in root (5m+ delays) | fd + rg canonical; add `thegent_files` MCP |
| **Web search**  | thegent_ddg_search (DDG)               | No URL fetch; no Firecrawl/FetchSERP                    | Add mcp_web_fetch; optional Firecrawl      |
| **Web scrape**  | Model scrapers (internal)              | No agent-facing scrape                                  | server-fetch for URL content               |
| **Batch edits** | thegent_apply_transaction              | Exists; underused                                       | Document; add search_replace batch         |
| **kilo / roo**  | AI providers (proxy)                   | N/A                                                     | Clarify in docs                            |
| **OpenCode**    | Session parsing support                | Cross-provider parity                                   | Document IDE parity                        |

---

## 2. File and Other Reads — Audit

### 2.1 Current Access Patterns

| Source    | Tool / Method                        | Platform            | Exclusions                       |
| --------- | ------------------------------------ | ------------------- | -------------------------------- |
| **IDE**   | read_file, list_dir, codebase_search | Cursor, Claude Code | IDE-specific                     |
| **Shell** | ls, find, grep, fd, rg               | All                 | fd/rg respect .gitignore         |
| **MCP**   | —                                    | —                   | **No file list/search MCP tool** |
| **Hooks** | fd-wrapper, grep-wrapper (→ rg)      | thegent hooks only  | common.sh                        |

### 2.2 Gaps

1. **No `thegent_files` MCP tool** — Agents using MCP cannot list/search files without shell.
2. **ls in project root** — 5m+ when node_modules/.venv present; agents do this by default.
3. **Inconsistent exclusions** — IDE vs shell vs (future) MCP may differ.

### 2.3 Recommendations

| Priority | Action                                                 | Effort           |
| -------- | ------------------------------------------------------ | ---------------- |
| P1       | Document fd + rg as canonical pair (skills, CLAUDE.md) | Done             |
| P1       | Add `thegent_files` MCP tool (list + search modes)     | 15–25 tool calls |
| P2       | .agentignore for project-level exclusions              | 4–6 tool calls   |
| P2       | Ensure fd, rg in Brewfile/setup for agent shells       | 1–2 edits        |

**Cross-ref**: [AGENT_FILE_SEARCH_UNIFIED_TOOL_RESEARCH.md](./AGENT_FILE_SEARCH_UNIFIED_TOOL_RESEARCH.md)

---

## 3. Web Search and Scrape — Audit

### 3.1 Current State

| Tool                   | Location                           | Purpose                                                |
| ---------------------- | ---------------------------------- | ------------------------------------------------------ |
| **thegent_ddg_search** | mcp_server.py                      | DuckDuckGo text search; returns titles, snippets, URLs |
| **ddg_search**         | tools/research.py                  | Backend for thegent_ddg_search                         |
| **mcp_web_fetch**      | Cursor built-in                    | Fetch URL content (read-only)                          |
| **server-fetch**       | @modelcontextprotocol/server-fetch | Official MCP for web content                           |

### 3.2 Gaps

1. **No URL content fetch in thegent** — Agents get DDG snippets but not full page content.
2. **No Firecrawl/FetchSERP** — SETUP_PROPOSED_ITEMS lists Firecrawl, FetchSERP as community MCPs.
3. **DDG rate limits** — No retry/backoff; no caching.

### 3.3 Recommendations

| Priority | Action                                                                       | Effort          |
| -------- | ---------------------------------------------------------------------------- | --------------- |
| P1       | Document: use thegent_ddg_search for research; mcp_web_fetch for URL content | Doc only        |
| P2       | Add thegent_fetch_url (or wire server-fetch) for full page content           | 8–12 tool calls |
| P3       | Optional: Firecrawl MCP for heavy scrape (JS-rendered pages)                 | External MCP    |
| P3       | DDG: add retry with backoff; optional cache TTL                              | 4–6 tool calls  |

---

## 4. Other Accesses — Audit

### 4.1 API and Scraping (Internal)

| Component              | Purpose                                                        |
| ---------------------- | -------------------------------------------------------------- |
| **models/scrapers.py** | Provider model discovery (cursor, gemini, claude, proxy, etc.) |
| **cliproxy_manager**   | Health check, model fetch, provider metrics                    |
| **ddg_search**         | Web search (agent-facing)                                      |

### 4.2 MCP Ecosystem (External)

| MCP                   | Purpose                   |
| --------------------- | ------------------------- |
| **server-fetch**      | Web content fetching      |
| **server-filesystem** | Secure file ops           |
| **server-github**     | GitHub PRs, issues, repos |
| **Firecrawl**         | Web scrape (JS-rendered)  |
| **Octocode**          | GitHub/code search        |

### 4.3 Recommendations

- **Document** which MCPs complement thegent (server-fetch, filesystem, Firecrawl).
- **Avoid duplication** — Prefer official MCPs over reimplementing in thegent when feasible.

---

## 5. kilo, roo, OpenCode — Clarification (Updated)

### 5.1 kilo and roo

**kilo** and **roo** have **both** an **AI proxy** (model API) **and** **OSS harnesses** (agent execution frameworks like Claude Code, Codex).

| Platform | AI proxy           | OSS harness | CLI              |
| -------- | ------------------ | ----------- | ---------------- |
| **kilo** | api.kilo.ai/v1     | ✓           | `kilo auth`      |
| **roo**  | api.roocode.com/v1 | ✓           | `roo auth login` |

**Usage**: `thegent run kilo "..."`, `thegent cliproxy login kilo` — thegent uses them as providers via CLIProxyAPIPlus.

### 5.2 OpenCode

**OpenCode** (opencode.ai) is an **OSS AI coding agent** (terminal, IDE, desktop) — similar to Claude Code, Codex.

| Aspect     | Details                                                                            |
| ---------- | ---------------------------------------------------------------------------------- |
| **CLI**    | `opencode` — npm install -g opencode                                               |
| **Zen**    | Curated models for coding agents; pay-per-request; works with any agent            |
| **Config** | `.opencode/` — commands, instructions, plugins, prompts, tools                     |
| **ECC**    | everything-claude-code has `.opencode/` plugin (12 agents, 24 commands, 16 skills) |

**OpenCode Zen + CLIProxyAPI**: OpenCode can use CLIProxyAPIPlus as backend — see [AGENT_PLATFORMS_KILO_ROO_OPencode_CLIPROXY_RESEARCH.md](./AGENT_PLATFORMS_KILO_ROO_OPencode_CLIPROXY_RESEARCH.md).

### 5.3 Platform Parity

| Platform    | AI proxy        | OSS harness | CLIProxy          |
| ----------- | --------------- | ----------- | ----------------- |
| Claude Code | Anthropic       | ✓           | ✓                 |
| Cursor      | cursor-api      | Partial     | —                 |
| Codex       | OpenAI          | ✓           | ✓ (adapter)       |
| OpenCode    | Zen, multi      | ✓           | Proposed (config) |
| kilo        | api.kilo.ai     | ✓           | ✓ (as provider)   |
| roo         | api.roocode.com | ✓           | ✓ (as provider)   |

---

## 6. Batch File Edits — Audit

### 6.1 Current State

| Tool                             | Location                      | Purpose                    |
| -------------------------------- | ----------------------------- | -------------------------- |
| **thegent_apply_transaction**    | mcp_server.py                 | Atomic multi-file apply    |
| **apply_multi_file_transaction** | orchestration/transactions.py | Temp files → atomic rename |

### 6.2 Capabilities

- **Input**: `[{"path": str, "content": str}, ...]`
- **Behavior**: Write each to temp, then rename all atomically. On failure, rollback.
- **Optional**: `git_commit=True` stages and commits after apply.

### 6.3 Gaps

1. **Underused** — Agents often use N× edit_file instead of one thegent_apply_transaction.
2. **No search_replace batch** — No "replace X with Y in files matching pattern" MCP tool.
3. **No dry-run** — Cannot preview changes before apply.

### 6.4 Recommendations

| Priority | Action                                                             | Effort           |
| -------- | ------------------------------------------------------------------ | ---------------- |
| P1       | Document thegent_apply_transaction in skills, CLAUDE.md            | 2–3 edits        |
| P2       | Add thegent_batch_search_replace (pattern, replacement, path_glob) | 12–18 tool calls |
| P3       | Add dry_run param to thegent_apply_transaction                     | 2–4 tool calls   |

---

## 7. Optimizations — Catalog

### 7.1 File Access

| Opt                  | Status      | Impact                       |
| -------------------- | ----------- | ---------------------------- |
| fd + rg over ls/grep | Documented  | 10–35x faster; avoids 5m+ ls |
| thegent_files MCP    | Proposed    | Unified across platforms     |
| .cursorignore        | Recommended | Reduces Cursor index size    |
| .agentignore         | Proposed    | Project-level exclusions     |

### 7.2 Web Search

| Opt                      | Status   | Impact                   |
| ------------------------ | -------- | ------------------------ |
| DDG retry/backoff        | Proposed | Resilience               |
| DDG result cache         | Proposed | Reduce duplicate queries |
| server-fetch integration | Proposed | Full URL content         |

### 7.3 Batch Operations

| Opt                       | Status   | Impact                  |
| ------------------------- | -------- | ----------------------- |
| thegent_apply_transaction | Exists   | Atomic multi-file       |
| batch_search_replace      | Proposed | Single call for N files |
| dry_run                   | Proposed | Safer preview           |

### 7.4 Model Scraping (Internal)

| Opt                   | Status                         | Impact             |
| --------------------- | ------------------------------ | ------------------ |
| ThreadPoolExecutor(6) | Done                           | 3–5x faster scrape |
| Cache TTL             | Done                           | ~300s              |
| diskcache             | Proposed (LIBRARY_REPLACEMENT) | Cleaner cache      |

---

## 8. Enhanced Baseline Strategy

### 8.1 Layered Access Model

```
Layer 1 (IDE-native)     → read_file, list_dir, @codebase, codebase_search
Layer 2 (MCP)           → thegent_files, thegent_ddg_search, thegent_apply_transaction
Layer 3 (Shell fallback) → fd, rg
```

**Rule**: Prefer Layer 1 when available; Layer 2 when MCP connected; Layer 3 for terminal-only.

### 8.2 Tool Selection Matrix

| Task           | IDE             | MCP                       | Shell          |
| -------------- | --------------- | ------------------------- | -------------- |
| Read file      | read_file       | (thegent_files read)      | cat, head      |
| List dir       | list_dir        | thegent_files list        | fd -t f -d 1   |
| Search content | codebase_search | thegent_files search      | rg             |
| Web search     | —               | thegent_ddg_search        | —              |
| Fetch URL      | mcp_web_fetch   | (thegent_fetch_url)       | curl           |
| Batch edit     | N× edit         | thegent_apply_transaction | sed -i (risky) |

### 8.3 Agent Instructions (Baseline)

1. **File discovery**: fd (list/find) and rg (content). Never ls -l in project root.
2. **Web research**: thegent_ddg_search. For full page: mcp_web_fetch or server-fetch.
3. **Multi-file edits**: thegent_apply_transaction instead of N× edit.
4. **Providers**: kilo, roo = AI providers; use for model routing, not file ops.
5. **Platforms**: Claude Code, Cursor, Codex, OpenCode — same MCP toolset when connected.

---

## 9. Implementation Roadmap

| Phase              | Tasks                                                                       | Effort           |
| ------------------ | --------------------------------------------------------------------------- | ---------------- |
| **P1 (Immediate)** | Document baseline in skills, CLAUDE.md; add kilo/roo/OpenCode clarification | 4–6 edits        |
| **P2 (Short)**     | thegent_files MCP tool; thegent_apply_transaction docs                      | 15–25 tool calls |
| **P3 (Medium)**    | thegent_fetch_url or server-fetch wire; batch_search_replace                | 20–30 tool calls |
| **P4 (Long)**      | DDG retry/cache; .agentignore; dry_run for transactions                     | 10–15 tool calls |

---

## 10. Cross-References

| Doc                                                                                        | Purpose                                |
| ------------------------------------------------------------------------------------------ | -------------------------------------- |
| [AGENT_FILE_SEARCH_UNIFIED_TOOL_RESEARCH.md](./AGENT_FILE_SEARCH_UNIFIED_TOOL_RESEARCH.md) | fd + rg, thegent_files design          |
| [INDEXING_AND_OPTIMIZATION_SYSTEMS.md](../reference/INDEXING_AND_OPTIMIZATION_SYSTEMS.md)  | Indexing, Spotlight, ls avoidance      |
| [SETUP_PROPOSED_ITEMS.md](../plans/SETUP_PROPOSED_ITEMS.md)                                | MCP ecosystem, server-fetch, Firecrawl |
| [TOUCHPOINT_INTEGRATION_DEEP_DIVE.md](../reference/TOUCHPOINT_INTEGRATION_DEEP_DIVE.md)    | Research tools, skill references       |

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added access patterns
2. Added optimization examples
3. Enhanced cross-references

### Cross-References Added

- AGENT_PROCESS_ARCHITECTURE_RESEARCH.md
- AGENT_PLATFORMS_KILO_ROO_OPencode_CLIPROXY_RESEARCH.md

### Practical Additions

- Access templates
- Optimization configurations

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [AGENT_FILE_SEARCH_UNIFIED_TOOL_RESEARCH.md](./AGENT_FILE_SEARCH_UNIFIED_TOOL_RESEARCH.md) - File search research
- [AGENT_PLATFORMS_KILO_ROO_OPencode_CLIPROXY_RESEARCH.md](./AGENT_PLATFORMS_KILO_ROO_OPencode_CLIPROXY_RESEARCH.md) - Platform research
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
