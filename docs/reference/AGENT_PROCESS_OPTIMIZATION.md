# Agent Process Optimization

> **Purpose**: Introspect and optimize Python, node, droid, claude, codex processes. Do not assume leak—use proper parent-chain checks.

---

## Quick Commands

```bash
# Full introspection (orphan detection, memory breakdown)
thegent mcp introspect

# With optimization strategies
thegent mcp introspect --optimize

# JSON output for scripting
thegent mcp introspect --json

# Prune orphan node processes (LSP, MCP, cc-status)
thegent mcp prune --dry-run   # Preview
thegent mcp prune --force     # Kill orphans
```

---

## Process Types

| Type       | Typical Use                          | Orphan Check                        | Optimization                           |
| ---------- | ------------------------------------ | ----------------------------------- | -------------------------------------- |
| **Python** | thegent CLI, uv run                  | Parent chain to Cursor/Claude/Codex | Reduce concurrency; stop idle sessions |
| **node**   | LSP (pyright, tsserver), MCP servers | Same                                | `mcp prune`; disable unused MCPs       |
| **droid**  | Factory droid exec                   | Same                                | Stop sessions; restart droid if stuck  |
| **claude** | Claude Code IDE                      | N/A (usually parent)                | Close unused windows                   |
| **codex**  | Codex/dex CLI                        | Same                                | Stop background sessions               |

---

## Introspection Logic

1. **Orphan** = process has no Cursor/Claude/Codex in its parent chain (up to init).
2. **Not assumed leak** — high RSS can be:
   - Active inference (CPU time growing)
   - Cached context (normal for LLM backends)
   - True leak (RSS grows over time with no activity)
3. **Robust check**: `scripts/agent-process-introspect.py` walks parent chain; only marks orphan when no agent parent found.

---

## Optimization Strategies

### Python (16+ GB single process)

- Reduce `THGENT_MAX_CONCURRENCY` (default may spawn many sessions)
- Run `thegent ps --all` → `thegent stop <session_id>` for idle sessions
- Close Cursor tabs; each can hold agent state

### Node (LSP, MCP)

- `thegent mcp prune --force` — kills orphan node processes
- `thegent mcp spotlight-exclude` — reduces mds_stores overhead on macOS
- Disable unused MCP servers in Cursor settings
- `THGENT_AUTO_PRUNE=1` — auto-prune on session stop

### Droid (multiple 1–2 GB instances)

- Droid runs are per-request; parallel work = multiple droids
- Check elapsed time: `ps -p <pid> -o etime=`
- Stop idle sessions: `thegent stop <session_id>`
- Factory droid may cache context; restart droid CLI if memory grows unbounded

### Claude / Codex

- Close unused IDE windows
- `thegent stop <session_id>` for background sessions
- Long CPU time = active inference (not necessarily leak)

---

## Prune Scope (Conservative)

`mcp prune` targets **node only** (LSP, MCP servers, cc-status). **Droid is excluded**—pruning droid risks killing live thegent sessions.

Orphan detection recognizes: Cursor, Electron, Cursor Helper, Claude, Codex, Python (thegent/uv run).

To stop droid/Python orphans manually after introspect:

```bash
thegent stop <session_id>   # Preferred
kill -TERM <pid>            # If session unknown
```
