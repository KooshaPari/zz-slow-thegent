# TUI Compositor — Technical Design

**Date**: 2026-02-18
**Status**: Design Document
**Version**: 1.0

---

## Architecture Overview

### Layered Design

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Application (Textual)                             │
│  - CompositApp (main Textual.App)                          │
│  - Menubar, Statusbar, Dialogs                             │
│  - Key bindings and event routing                          │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Compositor (Pane Management)                      │
│  - PaneManager (split, merge, focus, layout)               │
│  - LayoutSerializer (save/restore)                         │
│  - SessionState (persistent state machine)                 │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Terminal Backend (PTY)                            │
│  - TerminalPane (wraps Textual.TerminalWidget)             │
│  - PTYAllocator (PTY allocation)                            │
│  - ProcessManager (process execution and cleanup)          │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. CompositApp (Textual.App)

**Responsibility**: Main application container, event dispatch, UI orchestration

**File**: `thegent/src/thegent/ui/compositor/app.py`

```python
from textual.app import ComposeResult, App
from textual.widgets import Header, Footer, Container
from textual.containers import Container


class CompositApp(App):
    """Main compositor application"""

    TITLE = "Thegent Compositor"
    BINDINGS = [
        ("ctrl+n", "new_pane", "New Pane"),
        ("ctrl+v", "split_vertical", "Split Vert"),
        ("ctrl+h", "split_horizontal", "Split Horiz"),
        ("ctrl+x", "close_pane", "Close"),
        ("ctrl+l", "focus_next", "Next Pane"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.pane_manager = PaneManager(self)
        self.session_state = SessionState()

    def compose(self) -> ComposeResult:
        """Compose application widgets"""
        yield Header()
        yield Container(id="main-pane-container")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize on app mount"""
        # Load prior session or create new
        layout = self.session_state.load_session()
        if layout:
            self.pane_manager.restore_layout(layout)
        else:
            self.pane_manager.create_default_layout()

    def action_new_pane(self) -> None:
        """Create new terminal pane"""
        self.pane_manager.create_pane()

    def action_split_vertical(self) -> None:
        """Split current pane vertically"""
        self.pane_manager.split_pane("vertical")

    def action_split_horizontal(self) -> None:
        """Split current pane horizontally"""
        self.pane_manager.split_pane("horizontal")

    def action_close_pane(self) -> None:
        """Close current pane"""
        self.pane_manager.close_pane()

    def action_focus_next(self) -> None:
        """Focus next pane"""
        self.pane_manager.focus_next()
```

### 2. PaneManager

**Responsibility**: Pane lifecycle, splitting, merging, layout management, focus handling

**File**: `thegent/src/thegent/ui/compositor/pane_manager.py`

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import uuid


class SplitDirection(Enum):
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"


@dataclass
class PaneNode:
    """Represents a pane or split in the layout tree"""

    id: str
    pane: Optional["TerminalPane"] = None
    left: Optional["PaneNode"] = None
    right: Optional["PaneNode"] = None
    direction: Optional[SplitDirection] = None

    def is_leaf(self) -> bool:
        """Check if this is a leaf (terminal pane)"""
        return self.pane is not None


class PaneManager:
    """Manages pane layout and lifecycle"""

    def __init__(self, app: CompositApp):
        self.app = app
        self.root: Optional[PaneNode] = None
        self.focus_pane: Optional[TerminalPane] = None

    def create_pane(self, working_dir: str = ".") -> TerminalPane:
        """Create new terminal pane"""
        pane_id = str(uuid.uuid4())[:8]
        pane = TerminalPane(pane_id, working_dir)

        if self.root is None:
            self.root = PaneNode(id=pane_id, pane=pane)
        else:
            self.focus_pane.split(pane, SplitDirection.VERTICAL)

        self.focus_pane = pane
        return pane

    def split_pane(self, direction: str, working_dir: str = ".") -> TerminalPane:
        """Split current pane in given direction"""
        if self.focus_pane is None:
            return self.create_pane(working_dir)

        new_pane = TerminalPane(str(uuid.uuid4())[:8], working_dir)
        self.focus_pane.split(new_pane, SplitDirection(direction))
        self.focus_pane = new_pane
        return new_pane

    def close_pane(self) -> None:
        """Close current pane"""
        if self.focus_pane:
            self.focus_pane.close()
            # TODO: Rebalance layout, move focus

    def focus_next(self) -> None:
        """Focus next pane in rotation"""
        # Traverse tree in-order, find next after current
        panes = self._collect_panes(self.root)
        if not panes:
            return

        current_idx = panes.index(self.focus_pane)
        next_idx = (current_idx + 1) % len(panes)
        self.focus_pane = panes[next_idx]
        self.focus_pane.focus()

    def restore_layout(self, layout_data: dict) -> None:
        """Restore pane layout from serialized data"""
        self.root = self._deserialize_tree(layout_data)

    def save_layout(self) -> dict:
        """Serialize current layout to dict"""
        return self._serialize_tree(self.root)

    def _collect_panes(self, node: Optional[PaneNode]) -> list[TerminalPane]:
        """Collect all panes in in-order traversal"""
        if node is None:
            return []

        if node.is_leaf():
            return [node.pane]

        result = []
        result.extend(self._collect_panes(node.left))
        result.extend(self._collect_panes(node.right))
        return result

    def _serialize_tree(self, node: Optional[PaneNode]) -> dict:
        """Serialize pane tree to dict"""
        if node is None:
            return {}

        if node.is_leaf():
            return {
                "type": "pane",
                "id": node.id,
                "working_dir": node.pane.working_dir,
            }

        return {
            "type": "split",
            "direction": node.direction.value,
            "left": self._serialize_tree(node.left),
            "right": self._serialize_tree(node.right),
        }

    def _deserialize_tree(self, data: dict) -> Optional[PaneNode]:
        """Deserialize pane tree from dict"""
        if not data:
            return None

        if data["type"] == "pane":
            pane = TerminalPane(data["id"], data["working_dir"])
            return PaneNode(id=data["id"], pane=pane)

        # Recursively deserialize children
        left = self._deserialize_tree(data.get("left", {}))
        right = self._deserialize_tree(data.get("right", {}))

        return PaneNode(
            id=str(uuid.uuid4())[:8],
            left=left,
            right=right,
            direction=SplitDirection(data["direction"]),
        )
```

### 3. TerminalPane

**Responsibility**: PTY allocation, terminal widget, process execution

**File**: `thegent/src/thegent/ui/compositor/terminal_pane.py`

```python
from textual.widgets import Static
import pty
import os
import subprocess
from dataclasses import dataclass


class TerminalPane(Static):
    """Terminal pane widget wrapping PTY"""

    def __init__(self, pane_id: str, working_dir: str = "."):
        super().__init__()
        self.pane_id = pane_id
        self.working_dir = working_dir
        self.pty_fd: Optional[int] = None
        self.process_pid: Optional[int] = None

    def render(self) -> str:
        """Render terminal pane content"""
        # TODO: Read from PTY, render output
        return f"[Pane {self.pane_id}]\n{self.working_dir}"

    def spawn_shell(self, shell: str = "/bin/bash") -> None:
        """Spawn shell in PTY"""
        pid, self.pty_fd = pty.openpty()

        fork_pid = os.fork()
        if fork_pid == 0:
            # Child process
            os.close(pid)
            os.setsid()
            os.dup2(self.pty_fd, 0)  # stdin
            os.dup2(self.pty_fd, 1)  # stdout
            os.dup2(self.pty_fd, 2)  # stderr
            os.chdir(self.working_dir)
            os.execvp(shell, [shell])
        else:
            # Parent process
            os.close(self.pty_fd)
            self.process_pid = fork_pid

    def write_input(self, data: bytes) -> None:
        """Write input to PTY"""
        if self.pty_fd:
            os.write(self.pty_fd, data)

    def close(self) -> None:
        """Close terminal pane and cleanup"""
        if self.process_pid:
            os.kill(self.process_pid, 15)  # SIGTERM
            os.waitpid(self.process_pid, 0)
        if self.pty_fd:
            os.close(self.pty_fd)
```

### 4. SessionState

**Responsibility**: Session lifecycle, persistence, restoration

**File**: `thegent/src/thegent/ui/compositor/session_state.py`

```python
import yaml
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class SessionMetadata:
    """Session metadata"""

    id: str
    name: str
    created_at: str
    updated_at: str
    working_dir: str


class SessionState:
    """Manages session state and persistence"""

    SESSION_DIR = Path.home() / ".config" / "thegent" / "sessions"
    LAYOUTS_DIR = Path.home() / ".config" / "thegent" / "layouts"

    def __init__(self):
        self.SESSION_DIR.mkdir(parents=True, exist_ok=True)
        self.LAYOUTS_DIR.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[SessionMetadata] = None

    def load_session(self, session_id: Optional[str] = None) -> Optional[dict]:
        """Load session state from disk"""
        if session_id is None:
            session_id = self._get_last_session_id()

        if not session_id:
            return None

        session_file = self.SESSION_DIR / f"{session_id}.yaml"
        if not session_file.exists():
            return None

        with open(session_file) as f:
            return yaml.safe_load(f)

    def save_session(self, session_id: str, layout: dict) -> None:
        """Save session state to disk"""
        session_data = {
            "id": session_id,
            "layout": layout,
            "updated_at": datetime.now().isoformat(),
        }

        session_file = self.SESSION_DIR / f"{session_id}.yaml"
        with open(session_file, "w") as f:
            yaml.dump(session_data, f)

    def save_layout(self, layout_name: str, layout: dict) -> None:
        """Save layout template"""
        layout_file = self.LAYOUTS_DIR / f"{layout_name}.yaml"
        with open(layout_file, "w") as f:
            yaml.dump(layout, f)

    def list_layouts(self) -> list[str]:
        """List available layout templates"""
        return [f.stem for f in self.LAYOUTS_DIR.glob("*.yaml")]

    def _get_last_session_id(self) -> Optional[str]:
        """Get ID of most recent session"""
        sessions = sorted(self.SESSION_DIR.glob("*.yaml"))
        if not sessions:
            return None
        return sessions[-1].stem
```

### 5. Menubar & Statusbar

**Responsibility**: User interface and status display

**File**: `thegent/src/thegent/ui/compositor/widgets.py`

```python
from textual.widgets import Header, Footer, Static
from textual.reactive import reactive


class CompositHeader(Header):
    """Header with menus"""

    def __init__(self):
        super().__init__()
        self.show_header_and_footer = True


class CompositFooter(Footer):
    """Footer with statusbar"""

    session_name = reactive("Untitled")
    agent_status = reactive("idle")
    pane_count = reactive(1)

    def render(self) -> str:
        """Render statusbar"""
        return f"Session: {self.session_name} | Agent: {self.agent_status} | Panes: {self.pane_count}"
```

---

## Keyboard Shortcut Map

| Shortcut | Action             | Description                     |
| -------- | ------------------ | ------------------------------- |
| `Ctrl+N` | `new_pane`         | Create new pane                 |
| `Ctrl+H` | `split_horizontal` | Split current pane horizontally |
| `Ctrl+V` | `split_vertical`   | Split current pane vertically   |
| `Ctrl+X` | `close_pane`       | Close current pane              |
| `Ctrl+L` | `focus_next`       | Focus next pane (rotate)        |
| `Ctrl+S` | `save_layout`      | Save current layout             |
| `Ctrl+R` | `restore_layout`   | Restore saved layout            |
| `Ctrl+Q` | `quit`             | Quit application                |

---

## Data Model: Session & Layout

### Session YAML Format

```yaml
id: "session-20260218-143022"
name: "Development"
created_at: "2026-02-18T14:30:22Z"
updated_at: "2026-02-18T14:35:45Z"
working_dir: "/Users/kush/projects/thegent"
layout:
  type: "split"
  direction: "vertical"
  left:
    type: "pane"
    id: "pane-1"
    working_dir: "/Users/kush/projects/thegent"
  right:
    type: "split"
    direction: "horizontal"
    left:
      type: "pane"
      id: "pane-2"
      working_dir: "/Users/kush/projects/thegent"
    right:
      type: "pane"
      id: "pane-3"
      working_dir: "/Users/kush/projects/thegent"
```

### Layout Template Format

```yaml
name: "Three-Pane Layout"
description: "Vertical split with two right panes"
template:
  type: "split"
  direction: "vertical"
  left:
    type: "pane"
    working_dir: "."
  right:
    type: "split"
    direction: "horizontal"
    # ... nested structure
```

---

## Concurrency & Async Model

### Event Loop Integration

```python
# Integrate with Textual's event loop
async def on_terminal_output(self, pane_id: str, data: bytes):
    """Handle terminal output from PTY"""
    pane = self.pane_manager.get_pane(pane_id)
    if pane:
        pane.append_output(data)
        self.refresh()


async def on_resize(self):
    """Handle terminal resize"""
    # Update all panes with new dimensions
    self.pane_manager.resize_all_panes()
```

---

## Testing Strategy

### Unit Tests

- **PaneManager**: Tree structure, split/merge operations
- **SessionState**: Serialization/deserialization
- **LayoutSerializer**: YAML round-trip

### Integration Tests

- **CompositApp**: Full app initialization
- **TerminalPane**: PTY allocation and cleanup
- **Layout persistence**: Save/restore cycle

### E2E Tests

- User workflows (split, focus, close, save)
- Session recovery after restart

---

## Performance Targets

| Operation     | Target | Strategy                             |
| ------------- | ------ | ------------------------------------ |
| App startup   | <500ms | Lazy load layouts, defer async tasks |
| Pane creation | <100ms | Pre-allocate PTY descriptors         |
| Layout switch | <50ms  | In-memory layout tree, no disk I/O   |
| Idle memory   | <100MB | Limit output buffer per pane         |
| Idle CPU      | <2%    | No active polling; event-driven      |

---

## References

- **Textual Docs**: https://textual.textualize.io/
- **PTY Programming**: https://man7.org/linux/man-pages/man7/pty.7.html
- **tmux Source**: https://github.com/tmux/tmux
- **Zellij Layout Docs**: https://zellij.dev/documentation/layouts
