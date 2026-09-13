# TUI Compositor Implementation Proposal

**Date**: 2026-02-18
**Source**: [CONVERSATION_DUMP_2026-02-16_EXPANDED.md](../../research/CONVERSATION_DUMP_2026-02-16_EXPANDED.md) § 2
**Status**: Proposed
**Priority**: P1

---

## Executive Summary

Implement a **TUI Compositor** (terminal user interface compositor and multiplexer) to serve as the primary dashboard and control plane for the **Sitback Agent** and broader **thegent** system. The compositor will provide GUI-like experience (menus, statusbars, dialogs) with terminal pane splitting, process management, and real-time monitoring.

**Key Goals**:

- Unified control plane for agent orchestration and monitoring
- GUI-like experience (menubar, statusbar, keyboard shortcuts) in terminal
- Real-time process and session tracking
- Session persistence and layout management

---

## Problem Statement

**Current State**:

- Multiple disconnected UIs: shell prompt, separate tmux sessions, log files
- Sitback and other agents lack a unified dashboard
- No centralized view of running agents, tasks, and system state
- Users must manually manage terminal panes and sessions

**Desired State**:

- Single unified TUI dashboard
- Menubar navigation (File, Edit, View, Tools, Help)
- Statusbar showing session/agent status in real-time
- Pane splitting and layout management
- Session persistence across restarts

---

## Requirements

### Functional Requirements

| FR-ID          | Description                                                     | Priority |
| -------------- | --------------------------------------------------------------- | -------- |
| **FR-TUI-001** | Menubar with File/Edit/View/Tools/Help menus                    | P0       |
| **FR-TUI-002** | Statusbar displaying current session, agent, status             | P0       |
| **FR-TUI-003** | Horizontal and vertical pane splitting                          | P0       |
| **FR-TUI-004** | Terminal pane widget supporting shell interaction               | P1       |
| **FR-TUI-005** | Floating window support (dialogs, alerts)                       | P1       |
| **FR-TUI-006** | Layout save/restore (via YAML or JSON)                          | P1       |
| **FR-TUI-007** | Session persistence across application restarts                 | P1       |
| **FR-TUI-008** | Keyboard shortcuts (Ctrl+C, Ctrl+N, Ctrl+V, etc.)               | P0       |
| **FR-TUI-009** | Real-time process monitoring (CPU, memory)                      | P2       |
| **FR-TUI-010** | Integration with thegent work stream (do-next, claim, complete) | P2       |
| **FR-TUI-011** | Web export via `textual serve` (optional)                       | P3       |
| **FR-TUI-012** | Theme customization (light/dark)                                | P2       |

### Non-Functional Requirements

| NFR-ID          | Requirement                  | Target      |
| --------------- | ---------------------------- | ----------- |
| **NFR-TUI-001** | App startup latency          | <500ms      |
| **NFR-TUI-002** | Pane creation latency        | <100ms      |
| **NFR-TUI-003** | Layout switch latency        | <50ms       |
| **NFR-TUI-004** | Memory footprint             | <100MB idle |
| **NFR-TUI-005** | CPU usage (idle)             | <2%         |
| **NFR-TUI-006** | Responsiveness to user input | <50ms       |

---

## Technology Selection

### Framework: **Textual** (Python)

**Rationale**:

- Written in Python (matches thegent stack)
- CSS-like styling for maintainable UI code
- Rich widget library (menus, buttons, inputs, trees, etc.)
- `textual serve` for web export (future enhancement)
- Strong documentation and active community
- Easy integration with Python async code

**Alternatives Considered**:

- **Ratatui (Rust)**: More performant but requires Rust integration
- **Bubble Tea (Go)**: Not Python; would require separate service
- **Zellij (Rust)**: Compositor, but less control over UI

### Compositor Strategy: **Embedded Terminal Panes**

**Approach**:

- Use Textual's `TerminalWidget` (or equivalent) to embed PTY-based terminal panes
- Build custom layout manager on top
- Implement session state machine

**Alternative**: Use Zellij as backend compositor + custom Textual plugin (more complex)

---

## High-Level Architecture

### Layered Model

```
┌──────────────────────────────────────────────────┐
│  GUI-like Menu Layer (Textual)                   │
│  - Menubar (File, Edit, View, Tools, Help)      │
│  - Statusbar (session info, agent status)       │
│  - Dialogs (confirmations, inputs)              │
│  - Keyboard shortcuts (Ctrl+C, Ctrl+V, etc.)    │
└──────────────────────────────────────────────────┘
                        │
┌──────────────────────────────────────────────────┐
│  TUI Compositor Layer                            │
│  - Pane management (split, merge, focus)        │
│  - Floating window support                       │
│  - Layout management (save/restore)             │
│  - Session persistence                           │
└──────────────────────────────────────────────────┘
                        │
┌──────────────────────────────────────────────────┐
│  Terminal Emulator / PTY Layer                   │
│  - PTY allocation                                │
│  - Process execution                             │
│  - Output rendering                              │
└──────────────────────────────────────────────────┘
```

### Component Breakdown

| Component        | Purpose                   | Technology             | Status       |
| ---------------- | ------------------------- | ---------------------- | ------------ |
| **App**          | Main Textual application  | Textual                | To design    |
| **Menubar**      | Top-level menu navigation | Textual Menu           | To design    |
| **Statusbar**    | Real-time status display  | Textual Footer         | To design    |
| **PaneManager**  | Split/merge/layout logic  | Custom Python          | To implement |
| **TerminalPane** | PTY-based terminal widget | Textual TerminalWidget | To implement |
| **Session**      | Persistent session state  | YAML/JSON              | To design    |
| **Keyboard**     | Shortcut handling         | Textual key bindings   | To implement |

---

## Design Decisions

### D1: Framework Choice

**Decision**: Use **Textual** for TUI framework
**Rationale**: Python stack alignment, CSS styling, rich widgets, active community
**Alternatives Rejected**: Ratatui (requires Rust), Bubble Tea (Go-only)
**Tradeoff**: Textual may be slightly slower than Rust alternatives, but alignment with thegent stack outweighs performance cost

### D2: Terminal Pane Implementation

**Decision**: Use **Textual TerminalWidget** for embedded terminals
**Rationale**: Native Textual support, PTY integration, no external process needed
**Alternatives Rejected**: Zellij as compositor (more complex), tmux subprocess (harder to integrate)
**Tradeoff**: Embedded approach requires more development, but offers better integration

### D3: Layout Persistence

**Decision**: Save layouts to **YAML files** in `~/.config/thegent/layouts/`
**Rationale**: Human-readable, version-control friendly, easy to template
**Alternatives Rejected**: JSON (more verbose), binary (not human-readable)
**Tradeoff**: YAML is slightly slower to parse, but benefits outweigh

### D4: Session Model

**Decision**: Use **hierarchical session tree** (workspace → pane group → pane)
**Rationale**: Matches tmux/Zellij concepts, supports complex layouts
**Alternatives Rejected**: Flat session list (less flexible)
**Tradeoff**: More complex state management, but more powerful

---

## Acceptance Criteria

- [ ] **AC-1**: App starts in <500ms
- [ ] **AC-2**: Menubar with File/Edit/View/Tools/Help menus fully functional
- [ ] **AC-3**: Statusbar displays session name, agent status, real-time clock
- [ ] **AC-4**: Can split panes horizontally and vertically; focus switching works
- [ ] **AC-5**: Terminal panes execute shell commands and display output
- [ ] **AC-6**: Keyboard shortcuts work (Ctrl+N=new pane, Ctrl+V=vsplit, Ctrl+X=close)
- [ ] **AC-7**: Layouts can be saved to and restored from YAML
- [ ] **AC-8**: Session state persists across app restart
- [ ] **AC-9**: All linters pass (ruff, type checking); no new lint suppressions
- [ ] **AC-10**: Test coverage ≥80% for compositor core logic

---

## Related Documents

- **Architecture**: [../design.md](./design.md)
- **Implementation Tasks**: [../tasks.md](./tasks.md)
- **Research**: [../../research/CONVERSATION_DUMP_2026-02-16_EXPANDED.md](../../research/CONVERSATION_DUMP_2026-02-16_EXPANDED.md) § 2
- **Related Work**: [../../plans/UNIFIED_SYSTEM_APPLICATION_PLAN.md](../../plans/UNIFIED_SYSTEM_APPLICATION_PLAN.md)
- **Tech Stacks**: [../../reference/TECHNOLOGY_STACK_AND_FRAMEWORKS.md](../../reference/TECHNOLOGY_STACK_AND_FRAMEWORKS.md)

---

## See Also

- Textual Documentation: https://textual.textualize.io/
- Zellij Compositor: https://zellij.dev/
- tmux Reference: https://man7.org/linux/man-pages/man1/tmux.1.html
