<DONE>
# Smart Pruning Strategy: Intelligent Agent Resource Reclamation

## Overview

This document outlines the strategy for "Smart Pruning" of AI agent resources (Cursor, Claude Code, thegent). The goal is to reclaim system memory by killing redundant background processes (LSPs, MCP servers) associated with agents that are finished or idle, while ensuring documentation is written before session closure.

## 1. Audit and Discovery

The system will discover active agent sessions using a two-pronged approach:

- **Managed Sessions**: Queried from `RunRegistry` (thegent background runs).
- **IDE Sessions**: Discovered via process scanning (`ps`) for Cursor (`cursor-agent`), Claude Code (`claude-code`), and Codex.
- **Terminal Mapping**: Sessions are mapped to `tmux` panes by matching PIDs and command names.

## 2. Decision Logic (The "Smart" Criteria)

A session is marked for pruning only when **ALL** of the following conditions are met:

### A. Idle Detection (>60s)

- **Mechanism**: The system captures the terminal output (last 100 lines) of the associated tmux pane every 30 seconds.
- **Signal**: If the output remains unchanged for two consecutive checks (60s), the session is marked as `idle`.
- **Fallback**: For non-tmux sessions, the system checks the `mtime` of the session's `stdout.log` or the `atime` of the agent's process.

### B. Completion Signaling

- **Mechanism**: Regex-based pattern matching on the last 500 characters of terminal output.
- **Markers**:
  - **Claude Code**: `Summary:`, `... completed`, return of prompt `>`.
  - **Cursor**: `Done`, `Apply`, `Accept`, or long periods of silence after a complex task.
  - **Generic**: `Task finished`, `Exit code: 0`, `Terminating...`.

### C. Documentation Verification

- **Mechanism**: The system scans the `docs/` directory (specifically `docs/research/`, `docs/reports/`, and `docs/dumps/`).
- **Signal**: A session is "doc-verified" if at least one markdown file has been created or modified within the time window of the session (start_time to now).
- **Required Pattern**: Search for `CONVERSATION_DUMP_YYYY-MM-DD.md` or similar manifests.

## 3. Reprompting Loop (The "Last Ditch" Guard)

If a session is **Idle** and **Complete** but **Doc-Verification Fails**:

- **Action**: DO NOT PRUNE.
- **Reprompt**: The system sends a command to the agent via `tmux send-keys`:
  > "Automated Guard: You appear to have finished your task but haven't written a conversation dump to docs/research/. Please write one now before I prune this session to save memory."
- **Backoff**: Wait another 60s before re-checking.

## 4. Pruning Action

Once a session meets all criteria:

- **LSP/MCP Cleanup**: Kill all orphan-by-ppid processes matching redundant patterns (`pyright`, `tsserver`, etc.).
- **Agent Termination (Optional)**: If memory pressure is critical (>90%), kill the agent process itself.
- **Confirmation**: Log the reclamation (e.g., "Pruned ide-cursor-1234: reclaimed 1.2GB RAM").

## 5. Implementation Roadmap

1. **Module**: Create `src/thegent/orchestration/smart_prune.py`.
2. **CLI**: Add `thegent mcp smart-prune [--force] [--reprompt]`.
3. **Loop**: Add `smart_prune` step to `NeverIdleLoop` gardening rotation.
4. **State**: Store snapshots in `~/.thegent/smart_prune_state.json`.

---

_Status: Research & Audit Complete. Planning phase complete._
