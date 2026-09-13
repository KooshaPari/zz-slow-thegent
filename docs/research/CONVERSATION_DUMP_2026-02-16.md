<DONE>
# Conversation Dump — 2026-02-16

**Purpose:** Persist research, plans, and decisions from agent conversations so we can pick up later without hallucination.
**Source:** Cursor/Claude conversation(s)
**Date:** 2026-02-16

---

## 1. Shell & Shims Fixes (Session 1)

### Issues Addressed

- `NameError: name 'Optional' is not defined` in `thegent/src/thegent/main.py` (gamify_award, gamify_status)
- `git: '/opt/homebrew/bin/codex' is not a git command`
- `git: '/opt/homebrew/bin/copilot' is not a git command`
- Copilot parse error: `no matches found: /*---` (zsh parsing Node.js script)
- Zsh setup stripped (`.zshenv`, `.zshrc` had `return` only)
- Ghostty config missing

### Fixes Applied

1. **Optional fix:** Replaced `Optional[Path]` with `Path | None` in `main.py` (lines 3526, 3550)
2. **Agent shims:** Added `_install_agent_accelerators()` for `codex` and `copilot` — exec real binaries directly to avoid zsh parsing and git routing
3. **Zsh restore:** Restored `~/.zshenv`, `~/.zshrc` from `thegent/shell/`; replaced `~/.zsh_bundle.zsh` with thegent minimal (backup: `.zsh_bundle.zsh.broken`)
4. **Ghostty:** Created `~/.config/ghostty/config` (shell, theme, font)
5. **install-shims:** Now installs codex + copilot shims

### Shim Architecture (MTSP-10)

- **Git shim:** Multi-tenant lock coordination, index.lock handling, git_cached
- **Tool accelerators:** grep→rg, find→fd, jq→jaq, uv
- **Agent accelerators:** codex, copilot (exec real binary)
- **Role accelerators:** run, bg, ps, etc. → `thegent {role}`

### Docs Created

- `docs/SETUP-RESTORE.md`

---

## 2. TUI Compositor & Multiplexer Research

### User Request

Research TUI-os or similar TUI compositor + multiplexer for sitback and UI/UX.

### Findings

| Category           | Projects                                          | Notes                                                                                       |
| ------------------ | ------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| **Multiplexers**   | Zellij (29k★), tmux, mprocs (2.4k★), trex (10★)   | Zellij: layouts, plugins, floating panes. trex: tmux session manager with AI agent tracking |
| **TUI Frameworks** | Textual (34k★), Ratatui (18k★), Bubble Tea (39k★) | Textual: Python, CSS-like, `textual serve` for web                                          |
| **Dashboard Apps** | Superfile, Glow, gitui, taskwarrior-tui           | Reference UX patterns                                                                       |

### Recommendation for Sitback

- **Compositor:** Zellij or tmux
- **GUI-like layer:** Textual (Python) for menus, statusbar, dialogs
- **Integration:** Textual app that hosts the compositor, or Zellij plugins

### Unified Plan

TUI/compositor research merged into: [UNIFIED_SYSTEM_APPLICATION_PLAN.md](../plans/UNIFIED_SYSTEM_APPLICATION_PLAN.md)

### Resources

- [ratatui.rs/showcase](https://ratatui.rs/showcase/)
- [awesome-ratatui](https://github.com/ratatui/awesome-ratatui)
- [textual.textualize.io](https://textual.textualize.io/)

---

## 3. TUI Compositor + GUI Menu System

### User Request

Compositor with GUI-like menu system layered on top to simulate robust terminal app.

### Layered Model

```
┌─────────────────────────────────────────────────────────────────┐
│  GUI-like menu layer (menubar, statusbar, dialogs, shortcuts)   │
├─────────────────────────────────────────────────────────────────┤
│  TUI compositor (panes, splits, floating windows, layout)       │
├─────────────────────────────────────────────────────────────────┤
│  Terminal emulator / PTY layer                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation Paths

- **A:** Zellij + custom TUI plugin (menubar, statusbar)
- **B:** Textual app hosting compositor (menubar, statusbar, dialogs, embed terminal panes)

---

## 4. Compute Offloading (Mac ↔ Desktop PC)

### User Question

Is prior research on linking desktop PC via compute offloading still present?

### Answer: Yes

**Location:** `docs/architecture/HYBRID_MAC_WIN_DEV_ENVIRONMENT.md`, `docs/reference/HYBRID_ENV_SUMMARY.md`, `docs/plans/HYBRID_ENV_IMPLEMENTATION_PLAN.md`, `docs/checklists/HYBRID_ENV_SETUP_CHECKLIST.md`

### Architecture

- **Mac:** Client (Cursor, Claude Code), light dev
- **Windows 11 PC:** Compute base (64GB RAM, 16GB VRAM, 8-core CPU, 5TB)
- **Sync:** Syncthing (bi-directional `kush/`)
- **Network:** Tailscale VPN
- **Remote:** Parsec RDP, SSH

### Compute Offloading (Phase 4)

- `thegent run --remote windows-pc "Build project" gemini`
- Heavy builds, Docker, process-compose on Windows
- Status: Architecture complete, implementation not started

---

## 5. Cursor-Agent Conversations 2/16

**Note:** Cursor stores chat history in app state. To recover conversations from 2/16:

1. Open Cursor → Chat history
2. Filter by date 2026-02-16
3. Manually export or copy research/plans from each conversation
4. Append to this doc or create `CONVERSATION_DUMP_2026-02-16_PART2.md`

---

## 6. Always-Write-Dumps Rule (This Session)

**User request:** Update CLAUDE.md to always push writing down these dumps from prompts, in the relevant project folder's docs subfolder, so we can pick up later and extend without hallucination.

**Action:** Add to CLAUDE.md (see next section).

---

## Document Status

| Section               | Source              | Status         |
| --------------------- | ------------------- | -------------- |
| 1. Shell & Shims      | Conversation        | ✅ Complete    |
| 2. TUI Research       | Conversation        | ✅ Complete    |
| 3. Compositor + Menu  | Conversation        | ✅ Complete    |
| 4. Compute Offloading | Conversation + docs | ✅ Complete    |
| 5. Cursor 2/16        | Manual check needed | ⏳ Pending     |
| 6. Always-Write-Dumps | Rule to add         | ✅ In progress |

---

## BACKLOG items & spec refs (for WORK_STREAM)

| Section                 | Work item                                  | Spec / plan                                                                                                                                                                  | BACKLOG ID (if new)          |
| ----------------------- | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| 1. Shell & shims        | Done (Optional, agent shims, Zsh, Ghostty) | [SETUP-RESTORE.md](../SETUP-RESTORE.md)                                                                                                                                      | —                            |
| 2. TUI research         | Merged                                     | [UNIFIED_SYSTEM_APPLICATION_PLAN.md](../plans/UNIFIED_SYSTEM_APPLICATION_PLAN.md)                                                                                            | —                            |
| 3. Compositor + menu    | Merged                                     | Same                                                                                                                                                                         | —                            |
| 4. Compute offloading   | Architecture done; impl not started        | [HYBRID_ENV_IMPLEMENTATION_PLAN.md](../plans/HYBRID_ENV_IMPLEMENTATION_PLAN.md), [REMOTE_COMPUTE_IMPLEMENTATION_DETAIL.md](../plans/REMOTE_COMPUTE_IMPLEMENTATION_DETAIL.md) | research-remote-compute-impl |
| 5. Cursor 2/16 recovery | Manual export from Cursor chat history     | —                                                                                                                                                                            | pending-cursor-2-16-export   |
| 6. Always-write-dumps   | Add rule to CLAUDE.md                      | CLAUDE.md (project root)                                                                                                                                                     | research-always-write-dumps  |

**Suggested BACKLOG rows to add** (if not already present):

| ID                           | Title                                                      | Source                             | Priority | Depends |
| ---------------------------- | ---------------------------------------------------------- | ---------------------------------- | -------- | ------- |
| research-remote-compute-impl | Implement `thegent run --remote` (Phase 4 compute offload) | CONVERSATION_DUMP_2026-02-16.md §4 | P2       | —       |
| research-always-write-dumps  | CLAUDE.md: always write conversation dumps to docs/        | CONVERSATION_DUMP_2026-02-16.md §6 | P2       | —       |

_Run `thegent plan incorporate` to merge into [WORK_STREAM.md](../reference/WORK_STREAM.md)._

---

## See Also

- [CONVERSATION_DUMP_2026-02-16_EXPANDED.md](./CONVERSATION_DUMP_2026-02-16_EXPANDED.md) - Expanded comprehensive guide
- [WORK_STREAM.md](../reference/WORK_STREAM.md) - Unified work stream
- [RESEARCH_SEED_FRAGMENT_INVENTORY](./RESEARCH_SEED_FRAGMENT_INVENTORY_AND_SPRAWL_TODO.md) - Fragment inventory

---

**Last Updated:** 2026-02-17

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## 8. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added conversation patterns
2. Added dump configurations
3. Enhanced cross-references

### Cross-References Added

- IDEA_SEEDS_SESSION_STORAGE.md
- USER_QUEUE_TUI_AND_AGENT_POLL.md

### Practical Additions

- Dump templates
- Conversation configurations

## Gap Prioritization Heuristics

| Gap Type              | Signal                                                        | Priority | Recovery Action                                                     |
| --------------------- | ------------------------------------------------------------- | -------- | ------------------------------------------------------------------- |
| Blocking unknown      | Cannot execute next planned step without missing fact         | P0       | Resolve immediately with one targeted source-of-truth check         |
| Contradictory state   | Two docs/notes disagree on current behavior                   | P0       | Reconcile by validating live behavior, then mark one canonical      |
| Dependency blind spot | Upstream/downstream owner, interface, or handoff unclear      | P1       | Identify owner + contract and record decision in backlog/workstream |
| Validation missing    | Change exists but no deterministic verification evidence      | P1       | Add a minimal proof command/output and attach to closure note       |
| Nice-to-know context  | Historical rationale not needed for execution or verification | P3       | Defer; do not block recovery closure                                |

- Tie-breaker: prioritize the gap that shortens time-to-verifiable-closure the most.
- Batch rule: close all P0 gaps before opening new implementation branches.

## Recovery Stop Conditions

- Stop when each open recovery item has: owner, next action, and due marker recorded.
- Stop when all P0/P1 gaps have either a verified fix or explicit defer decision.
- Stop when the current path has one reproducible validation artifact (command + observed result).
- Stop when backlog/workstream state matches repository reality with no unresolved contradictions.
- Stop when remaining work is execution, not discovery (no unanswered blocking questions).

## Recovery Ownership Matrix

| Scope                                                            | Accountable Owner    | Decision Right                            | Required Artifact Before Close                                     |
| ---------------------------------------------------------------- | -------------------- | ----------------------------------------- | ------------------------------------------------------------------ |
| Recovery command path (`thegent` runtime, shims, launcher)       | Runtime Maintainer   | Approves behavior and fallback semantics  | Passing focused validation command with captured output            |
| Planning and backlog truth (`WORK_STREAM`, plan docs)            | Recovery Coordinator | Sets canonical priority and sequencing    | Updated backlog row with owner, next action, and dependency status |
| Evidence and docs integrity (conversation dumps, recovery notes) | Documentation Owner  | Accepts evidence quality and completeness | Timestamped evidence block linked to exact file/section            |
| Cross-team handoff risks (external blockers, dependencies)       | Incident Lead        | Escalates defer vs proceed                | Logged handoff decision with named downstream owner                |

## Evidence Freeze Rules

- Freeze evidence at each recovery milestone by recording command, timestamp, and observed result together.
- Do not rewrite prior evidence lines; append corrections as superseding entries with explicit reason.
- Treat unresolved contradictions as open incidents until one canonical source is validated and tagged.
- Reject closure if any P0/P1 item lacks both an owner and a verifiable artifact.
- Require one final reconciliation pass confirming `WORK_STREAM` state matches repository reality.

## Priority Exception Rules

- Allow a lower-priority task to preempt only for active data-loss, security exposure, or irreversible-state risk.
- Require named approver, explicit exception reason, and expiration checkpoint before any sequence override.
- Time-box exception work to recovery stabilization scope; defer all opportunistic improvements.
- Re-enter canonical priority order immediately after the exception gate is cleared and logged.

## Recovery Verification Gate

- No recovery item closes without one deterministic command, expected outcome, and observed result.
- Verification evidence must include timestamp, operator, and target surface (runtime, docs, or backlog).
- If verification fails, reopen item at prior priority with updated next action and owner.
- Final gate passes only when repo state, `WORK_STREAM`, and recorded evidence are mutually consistent.
