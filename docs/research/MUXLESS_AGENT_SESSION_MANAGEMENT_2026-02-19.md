<DONE>
# Muxless Agent Session Management — Research Synthesis

> **Status**: Research complete | **Date**: 2026-02-19
> **Purpose**: Tools and architecture for detecting, registering, introspecting, and controlling agent sessions (cursor-agent, droid, claude, codex, etc.) with minimal overhead and maximal control.

---

## Requirements (from user prompt)

- **Detect & register** all agent instances (thegent-wrapped, native subagent tools, user-driven)
- **Introspect** full session when possible; **last 50 lines by default** for conciseness
- **Non-blocking messaging** for agents
- **Resumption** for headless sessions: paste full session + resumption prompt to identical new session
- **Interactive TUI control**: attach, read, remessage using TUI as control tools
- **User must not lose TUI**; temporary input loss OK
- **User takeover** via thegent session mgmt TUIs for any interactive session
- **Minimal overhead, maximal control** for both agents and user

---

## Tools Landscape

### Session Management & Registration

| Tool                    | Role                                                                | Notes                                                                                  |
| ----------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **Agent-of-Empires**    | Tmux-based session manager for Claude Code, OpenCode, Codex, Gemini | TUI dashboard, status detection, git worktrees. Reference for metadata mapping.        |
| **thegent DiscoveryV2** | `psutil`-based process scanner                                      | `AgentScanner` patterns: claude, aider, cursor-agent, thegent. Heartbeats + manifests. |
| **zmx**                 | Lightweight session persistence (Zig, libghostty-vt)                | Attach/detach, restores terminal state. Muxless alternative to tmux.                   |
| **abduco** / **dtach**  | Minimal detach/reattach                                             | No state restore. Lightweight for floating TUIs.                                       |

### Programmatic TUI Control

| Tool         | Role                                       | Notes                                                                                                     |
| ------------ | ------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| **Termitty** | Selenium-like terminal automation (Python) | `wait_until`, `get_screen_text()`, `find_menu_items()`, `click_menu_item()`, session recording. AI-ready. |
| **reptyr**   | Reparent process to new TTY                | "Steal" running process for agent control.                                                                |
| **WezTerm**  | CLI for programmatic control               | `wezterm cli list-clients`, `send-text`, etc.                                                             |
| **Kitty**    | `kitten @` remote control                  | Send text, list windows.                                                                                  |
| **Ghostty**  | Emerging HTTP Remote Control API           | Shell integration, libghostty-vt.                                                                         |

### Resumption & Continuation

| Mechanism                    | Role                    | Notes                                                        |
| ---------------------------- | ----------------------- | ------------------------------------------------------------ |
| **thegent `--continuation`** | Buffer-paste resumption | `_build_continuation_prompt` loads prior stdout/stderr tail. |
| **takeover.json**            | Loop injection          | `thegent_loop_takeover`, `thegent orchestrate loop-send`.    |

### Cloud / Browser Terminals

| Tool                     | Role                                | Notes                                                           |
| ------------------------ | ----------------------------------- | --------------------------------------------------------------- |
| **Browser Terminal Use** | Local CLI → remote browser terminal | `browterm exec`, exit-code parity. For cloud GPU, bastion-only. |

---

## Proposed Stack for thegent

| Feature           | Approach                                                                                        |
| ----------------- | ----------------------------------------------------------------------------------------------- |
| **Registration**  | DiscoveryV2 + psutil + extend patterns (droid, codex). Optionally integrate AoE metadata.       |
| **Introspection** | Termitty `get_screen_text()` / `snapshot()` for last N lines; or tmux `capture-pane` (current). |
| **Messaging**     | ACP (Agent Client Protocol) as unified JSON-RPC bridge for session attach/inspect/send.         |
| **TUI control**   | abduco for session sharing; Termitty for TUI automation; reptyr for process takeover.           |
| **Takeover**      | `thegent takeover` (tmux attach) + `takeover.json` for loop injection.                          |
| **Resumption**    | `thegent --continuation` (existing).                                                            |

---

## ACP Use Cases

- **session/attach** — Attach to existing terminal session (read-only or control)
- **session/inspect** — Return last N lines (default 50)
- **session/send** — Non-blocking message injection
- **session/list** — List registered sessions with metadata

---

## Existing thegent Components

- `src/thegent/infra/discovery_v2.py` — AgentScanner, HeartbeatMonitor, AgentManifest
- `src/thegent/tools/terminal.py` — list_tmux_panes, capture_tmux_pane, send_to_tmux_pane
- `src/thegent/mcp_server.py` — thegent*terminal*\*, thegent_loop_takeover
- `src/thegent/cli_impl.py` — \_build_continuation_prompt, \_load_prior_session_output
- `src/thegent/acp/` — ACP server/client adapters
- `docs/research/UNIFIED_AGENT_REGISTRY_API.md` — Registry API design

---

## Next Steps

1. Extend AgentScanner with droid, codex, cursor-agent patterns; register to unified registry.
2. Add Termitty-based introspection path for "last 50 lines" when tmux unavailable.
3. Extend ACP with session/attach, session/inspect, session/send.
4. Document takeover flow: `thegent takeover` + `takeover.json` for human and agent.
