# Prompts Tooling — Cursor / Codex / Claude Aggregate

**Purpose:** Easy interaction with prompts and AI responses from Cursor, Codex, and Claude. Session and project/directory management for recovery and extension without hallucination.

---

## Quick Reference

| Command                                | Purpose                                                                |
| -------------------------------------- | ---------------------------------------------------------------------- |
| `thegent prompts harvest`              | Harvest $idea and $defer/$pending from all sources into docs/research/ |
| `thegent prompts sessions`             | List sessions by source (claude, codex, cursor) and project            |
| `thegent prompts list`                 | List harvested idea seeds                                              |
| `thegent prompts dump <session_id>`    | Dump full Cursor conversation to docs/research/                        |
| `thegent prompts sync`                 | Harvest + list in one shot                                             |
| **Explore (no flag filter)**           |                                                                        |
| `thegent prompts explore sessions`     | Discover sessions across all sources                                   |
| `thegent prompts explore prompts`      | Discover all prompts (no $idea/$defer)                                 |
| `thegent prompts explore session <id>` | Session by prompt/response                                             |
| `thegent prompts explore chat <id>`    | Full chat dump (user + assistant)                                      |

---

## Explore (Generic, No Flag Filter)

Session and prompt discovery/exploration without $idea/$defer/$pending:

```bash
# Discover sessions
thegent prompts explore sessions
thegent prompts explore sessions --source cursor --project /path/to/proj

# Discover prompts (all, no flag filter)
thegent prompts explore prompts
thegent prompts explore prompts --session <id> --source cursor

# Session by prompt/response
thegent prompts explore session <session_id>

# Full chat dump
thegent prompts explore chat <session_id>
thegent prompts explore chat <session_id> -o docs/research/chat.md
```

---

## Session Management

### By Session

```bash
# All sessions (Claude, Codex, Cursor)
thegent prompts sessions

# Filter by source
thegent prompts sessions --source cursor
thegent prompts sessions --source claude
thegent prompts sessions --source codex

# Filter by project
thegent prompts sessions --project /path/to/project

# Limit output
thegent prompts sessions --limit 50
```

### By Project

Sessions are associated with project paths when available:

- **Claude:** `project` from history.jsonl
- **Codex:** `cwd` from state_5.sqlite threads
- **Cursor:** Resolved from project folder name or agent-tools paths

---

## Harvest Flow

1. **$idea** → Saved to `docs/research/idea-seeds/seed_*.md`
2. **$defer / $pending** → Appended to `docs/research/pending-handoff.md` (or `~/.claude/pending-handoff.md`)

### Sources

| Source | Path                                             | Schema                                         |
| ------ | ------------------------------------------------ | ---------------------------------------------- |
| Claude | `~/.claude/history.jsonl`                        | `display`, `project`, `timestamp`, `sessionId` |
| Codex  | `~/.codex/history.jsonl`                         | `text`, `session_id`, `ts`                     |
| Cursor | `~/.cursor/projects/*/agent-transcripts/*.jsonl` | `role`, `message.content[].text`               |

### Env Overrides

| Env               | Default                   | Purpose                            |
| ----------------- | ------------------------- | ---------------------------------- |
| `CLAUDE_HISTORY`  | `~/.claude/history.jsonl` | Claude history                     |
| `CODEX_HISTORY`   | `~/.codex/history.jsonl`  | Codex history                      |
| `CODEX_STATE_DB`  | `~/.codex/state_5.sqlite` | Codex cwd lookup                   |
| `CURSOR_PROJECTS` | `~/.cursor/projects`      | Cursor projects; set `=` to skip   |
| `OUTPUT_DIR`      | (unset)                   | Override output for harvest script |
| `STATE_DIR`       | `~/.claude`               | Offset files                       |

---

## Conversation Dumps

### Manual Dump (Cursor)

```bash
# Dump Cursor session to docs/research/
thegent prompts dump <session_id>

# Custom output path
thegent prompts dump <session_id> -o docs/research/CONVERSATION_DUMP_2026-02-16.md
```

### Conversation Dump Policy (CLAUDE.md)

Agents must write dumps to `docs/research/CONVERSATION_DUMP_YYYY-MM-DD.md` after research/plan conversations. See CLAUDE.md "Conversation Dump Policy" section.

---

## Integration with Hooks

- **UserPromptSubmit:** `prompt-submit-guard.sh` saves $idea to idea-seeds immediately (Claude Code only)
- **Stop:** `harvest-idea-seeds-stop.sh` runs harvest on session end
- **Taskfile:** `task harvest-idea-seeds` invokes `./scripts/harvest-idea-seeds.sh`

`thegent prompts harvest` wraps the same script for consistent behavior.

---

## Recovery After Crashes

1. Run `thegent prompts harvest` to capture any $idea/$defer from recent sessions
2. Run `thegent prompts sessions` to list available Cursor sessions
3. Run `thegent prompts dump <session_id>` for sessions you want to recover
4. Merge manually recovered content into `CONVERSATION_DUMP_YYYY-MM-DD.md` if needed

Cursor chat history is stored in app state; export manually when thegent cannot access it.

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
