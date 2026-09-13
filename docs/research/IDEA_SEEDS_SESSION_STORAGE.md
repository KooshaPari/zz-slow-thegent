<DONE>
# Idea Seeds & Session Storage

**Purpose:** Capture and persist `$idea`-flagged prompts as research seeds. Harvest from Claude Code and Codex session history before they expire. Also supports `$defer`/`$pending` for session handoff.

---

## $idea Flag

When you include `$idea` in a user prompt, the system:

1. **UserPromptSubmit hook** — Saves the exact prompt immediately to `docs/research/idea-seeds/seed_YYYYMMDDTHHMMSSZ.md`
2. **Harvest script** — Periodically scans Claude/Codex history for `$idea` entries and saves them

---

## $defer / $pending Flags

When you include `$defer` or `$pending` in a user prompt, the system:

1. **UserPromptSubmit hook** — Blocks the prompt (does not send to model), appends to `PROJECT_DIR/.claude/pending-queue.jsonl` (or `~/.claude/pending-queue.jsonl`), exits 1
2. **Stop hook** — `harvest-pending-queue.sh` flushes the queue to `docs/research/pending-handoff.md` (or `~/.claude/pending-handoff.md`)
3. **Harvest script** — Scans Claude/Codex/Cursor history for `$defer`/`$pending` and appends to `pending-handoff.md`
4. **thegent_do_next** — Surfaces deferred items as `next_items` for "find the next thing to do"

See [CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md](./CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md) for full design.

---

## Session Storage Locations

### Claude Code

| Path                         | Schema                                                                            | Retention                                    |
| ---------------------------- | --------------------------------------------------------------------------------- | -------------------------------------------- |
| `~/.claude/history.jsonl`    | `{"display":"<prompt>","project":"<path>","timestamp":<ms>,"sessionId":"<uuid>"}` | `cleanupPeriodDays` (default 30) in settings |
| `~/.claude/tasks/<session>/` | Per-session task JSON files                                                       | Same                                         |
| `~/.claude/projects/`        | Project metadata                                                                  | Same                                         |

**Parsing:** Each line is a JSON object. `display` = user prompt text; `project` = workspace path. Filter for `$idea` in `display`. Seeds are written to `$project/docs/research/idea-seeds/` (git root resolved when in repo).

### Codex

| Path                      | Schema                                                  | Retention                  |
| ------------------------- | ------------------------------------------------------- | -------------------------- |
| `~/.codex/history.jsonl`  | `{"session_id":"<uuid>","ts":<unix>,"text":"<prompt>"}` | Varies (check config.toml) |
| `~/.codex/sessions/`      | Session metadata JSONL                                  | Same                       |
| `~/.codex/state_5.sqlite` | `threads(id, cwd, ...)` — maps session_id → cwd         | Same                       |

**Parsing:** Each line is a JSON object. `text` = user prompt. Filter for `$idea` in `text`. Lookup `cwd` via `SELECT cwd FROM threads WHERE id=<session_id>`. Seeds are written to `$cwd/docs/research/idea-seeds/` (git root resolved when in repo).

### Cursor (agent CLI)

| Path                                                                | Schema                                                                      | Retention  |
| ------------------------------------------------------------------- | --------------------------------------------------------------------------- | ---------- |
| `~/.cursor/projects/<project-id>/agent-transcripts/<session>.jsonl` | `{"role":"user","message":{"content":[{"type":"text","text":"<prompt>"}]}}` | Per Cursor |
| `~/.cursor/projects/<project-id>/agent-tools/`                      | Tool output (contains workspace paths)                                      | Same       |

**Parsing:** Each line is a JSON object. Filter for `role=="user"` and `$idea` in `message.content[].text`. Project path is resolved from folder name (decode) or by grepping agent-tools for paths. Seeds are written to `$project/docs/research/idea-seeds/`.

**$defer / $pending:** Same harvest can filter for `$defer` or `$pending`; those are written to `pending-handoff.md` instead of idea-seeds. See [CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md](./CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md).

---

## Harvest Script

```bash
# Run manually (from project root)
./scripts/harvest-idea-seeds.sh

# Or with env overrides
OUTPUT_DIR=/path/to/docs/research/idea-seeds PROJECT_DIR=/path/to/repo ./scripts/harvest-idea-seeds.sh
```

**State:** Tracks last processed line offset in `~/.claude/.idea-harvest-claude-offset` and `~/.claude/.idea-harvest-codex-offset` to avoid duplicates.

**When to run:** Before sessions expire (~2 weeks if cleanup is aggressive; Claude default is 30 days). The harvest runs automatically on **Stop** (session end). Also:

- `task harvest-idea-seeds` — manual run
- Cron: daily or weekly for extra safety
- First run with large history (~7k+ lines) may take 30–60s; subsequent runs are fast (offset-based)

---

## Output Format

Each seed file:

```markdown
---
saved_at: 2026-02-16T12:00:00Z
source: UserPromptSubmit | claude_history | codex_history
project: /path/to/project # Claude only
session_id: uuid # when available
---

<exact prompt text>
```

---

## Configuration

| Env               | Default                   | Purpose                                              |
| ----------------- | ------------------------- | ---------------------------------------------------- |
| `CLAUDE_HISTORY`  | `~/.claude/history.jsonl` | Claude history path                                  |
| `CODEX_HISTORY`   | `~/.codex/history.jsonl`  | Codex history path                                   |
| `CODEX_STATE_DB`  | `~/.codex/state_5.sqlite` | Codex sqlite (threads.cwd lookup)                    |
| `CURSOR_PROJECTS` | `~/.cursor/projects`      | Cursor agent-transcripts root; set empty to skip     |
| `OUTPUT_DIR`      | (unset)                   | Override: send all seeds here instead of per-project |
| `PROJECT_DIR`     | (unset)                   | Not used for routing; per-entry project/cwd used     |
| `STATE_DIR`       | `~/.claude`               | Offset file location                                 |

**Note:** Cursor harvest scans all project agent-transcripts; with many projects it can take 1–2 min. Use `CURSOR_PROJECTS=` to skip.

---

## 6. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Enhanced Section 3:** Added Cursor agent-transcripts parsing
2. **Enhanced Section 4:** Added harvest script shell wrapper with env overrides
3. **Added Section 5:** Added configuration table for environment variables

### Cross-References Added

- [CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md](./CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md) - Queue design patterns

### Practical Additions

- Environment variable configuration for Claude/Codex/Cursor paths
- Harvest script with offset-based processing
- Seed file format with YAML frontmatter

---

## See Also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md](./CLAUDE_CODE_QUEUE_PENDING_BLOCKING.md) - Queue design
- [IDEA_SEED_EXPANSION_COMPLETE.md](./idea-seeds/IDEA_SEED_EXPANSION_COMPLETE.md) - Seed expansion
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory
