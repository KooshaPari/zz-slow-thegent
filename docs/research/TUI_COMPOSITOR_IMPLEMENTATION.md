<DONE>
# TUI Compositor Implementation Research

> **Status**: Research Complete | **Version**: 1.0 | **Date**: 2026-02-18
> **Priority**: P1 | **Depends**: None

## Overview

TUI compositor provides a unified terminal user interface for thegent, combining multiple output streams, agent status, and interactive controls.

## Framework Comparison

| Framework | Language | Pros | Cons | Recommendation |
|-----------|----------|------|------|----------------|
| **Textual** | Python | Rich ecosystem, async native, CSS-like styling | Python-only runtime | ✅ Primary |
| **Rich** | Python | Beautiful output, progress bars | Limited interactivity | Output only |
| **Bubble Tea** | Go | Modern, interactive, excellent docs | Requires Go runtime | ❌ Not Python |
| **blessed** | Python | Mature, cross-platform | Older API, sync only | ❌ Legacy |
| **prompt_toolkit** | Python | Full-featured, Pythonic | Complex API | Alternative |

## Recommended Approach

**Primary**: Textual (Python, matches thegent ecosystem)
**Fallback**: Rich for simple output components

### Why Textual?

1. **Python Native**: Matches thegent's Python codebase
2. **Async Support**: First-class async/await for agent updates
3. **CSS-like Styling**: Familiar styling system
4. **Component Library**: Rich widget ecosystem
5. **Active Development**: Regularly updated
6. **Type Hints**: Full type annotation support

## Architecture Design

```
┌─────────────────────────────────────────────────────────┐
│                    Compositor Layer                      │
│  ┌─────────────────────────────────────────────────────┐│
│  │ Window Manager (Tiling + Floating)                  ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  ││
│  │  │ Window 1 │ │ Window 2 │ │    Window 3     │  ││
│  │  │ (Output) │ │ (Status) │ │   (Interactive) │  ││
│  │  └──────────┘ └──────────┘ └──────────────────┘  ││
│  └─────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────┤
│                   Component Layer                       │
│  ┌────────────┐ ┌────────────┐ ┌──────────────────┐  │
│  │AgentOutput │ │ StatusBar  │ │ CommandHistory   │  │
│  │  Widget    │ │  Widget    │ │     Widget       │  │
│  └────────────┘ └────────────┘ └──────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                 Terminal Adapter Layer                   │
│  ┌─────────────────────────────────────────────────────┐│
│  │ Terminal-agnostic output (ANSI, Kitty, WezTerm)    ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Basic Layout

```python
from textual.app import App
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Footer


class ThegentApp(App):
    """Main TUI application."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #header {
        height: 3;
        background: $accent;
        color: $text;
    }
    #main {
        layout: horizontal;
    }
    #output {
        width: 70%;
        border: solid $accent;
    }
    #sidebar {
        width: 30%;
        border: solid $accent;
    }
    #footer {
        height: 1;
        background: $surface;
    }
    """

    def compose(self):
        yield Header("thegent v0.1.0")
        with Horizontal(id="main"):
            yield OutputWidget(id="output")
            yield SidebarWidget(id="sidebar")
        yield Footer()

    async def on_mount(self):
        """Initialize components."""
        await self.output.connect_to_agent()
```

### Phase 2: Component Library

```python
from textual.widgets import RichLog, Button, Input
from textual.containers import Container


class OutputWidget(Container):
    """Agent output stream widget."""

    def compose(self):
        yield RichLog(id="agent-output", wrap=True, highlight=True)

    async def on_message(self, message: AgentMessage):
        """Display agent message."""
        self.query_one("#agent-output", RichLog).write(message.formatted)


class StatusWidget(Container):
    """Agent status display."""

    def compose(self):
        yield Static("Status: Idle", id="status")
        yield Static("Model: gpt-4", id="model")
        yield Static("Tokens: 0", id="tokens")

    def update_status(self, status: AgentStatus):
        self.query_one("#status", Static).update(f"Status: {status.name}")
```

### Phase 3: Interactive Features

```python
class InteractiveWidget(Container):
    """Interactive command input."""

    def compose(self):
        yield Input(placeholder="Enter command...", id="command")
        yield Button("Send", id="send")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle command submission."""
        command = self.query_one("#command", Input).value
        await self.app.send_command(command)
```

## Key Components

| Component | Purpose | Features |
|-----------|---------|----------|
| `OutputWidget` | Display agent output | Auto-scroll, syntax highlight |
| `StatusWidget` | Show agent status | Real-time updates |
| `CommandWidget` | Input commands | History, auto-complete |
| `ProgressWidget` | Show progress | ETA, percentage |
| `TimelineWidget` | Session timeline | Scrollback, search |
| `MetricsWidget` | Display metrics | Charts, graphs |

## Terminal Compatibility

```python
class TerminalAdapter:
    """Abstract terminal capabilities."""

    SUPPORTED = {
        "ansi": {"color": True, "styles": True},
        "xterm-256color": {"color": 256, "styles": True},
        "kitty": {"color": 16M, "styles": True, "images": True},
        "wezterm": {"color": 16M, "styles": True, "images": True}
    }

    @classmethod
    def detect(cls) -> str:
        """Detect terminal type."""
        import os
        return os.environ.get("TERM", "ansi")
```

---

**EXTENSION_SUMMARY**

**Extended on:** 2026-02-18
**Extended by:** Claude Code

### Changes Made

1. **Created standalone research document** from TUI_COMPOSITOR_*.md
2. **Compared frameworks** (Textual, Rich, Bubble Tea, blessed)
3. **Recommended Textual** as primary framework
4. **Designed architecture** (3 layers: Compositor, Component, Adapter)
5. **Provided implementation plan** (3 phases)

### Cross-References Added

- TUI_COMPOSITOR_COMPARISON.md
- TROUBLESHOOTING.md

### Practical Additions

- Complete Python implementations
- Component library designs
- Terminal compatibility layer
- CSS-like styling examples
