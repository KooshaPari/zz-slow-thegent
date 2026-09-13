# TUI Compositor Phase 1 - Quick Start Guide

**Quick Reference for Using TUI Compositor Components**

---

## Installation & Import

```python
# All components are available from the main module
from thegent.compositor import (
    # Layout Engine
    LayoutEngine,
    LayoutNode,
    Direction,
    Size,
    # Components
    OutputWidget,
    StatusWidget,
    SidebarWidget,
    HeaderWidget,
    FooterStatusBar,
    MetricsPanel,
    ProgressIndicator,
    # Pane Management
    CompositApp,
    PaneManager,
)
```

---

## Basic Layout Examples

### Vertical Stack

```python
from thegent.compositor import LayoutEngine

engine = LayoutEngine()
vertical = engine.create_vertical_stack(["header", "content", "footer"])
```

### Horizontal Split

```python
horizontal = engine.create_horizontal_stack(["sidebar", "main", "info"])
```

### 2x2 Grid

```python
grid = engine.create_grid(2, 2, ["w1", "w2", "w3", "w4"])
```

---

## Component Usage

### OutputWidget - Agent Output Display

```python
from thegent.compositor import OutputWidget

# Create
output = OutputWidget(title="Agent Output")

# Write messages
output.write("Task started", style="cyan", timestamp=True)
output.write("✓ Done!", style="green")

# Clear
output.clear()

# Get info
lines = output.get_line_count()
```

### StatusWidget - Status Display

```python
from thegent.compositor import StatusWidget

# Create
status = StatusWidget()

# Update status
status.update_status("running", model="claude-opus", tokens=5000)

# Time tracking
status.start_timer()
# ... work ...
status.stop_timer()

# Individual updates
status.status = "idle"
status.model = "gpt-4"
status.tokens_used = 1000
```

### SidebarWidget - Agent Tracking

```python
from thegent.compositor import SidebarWidget

# Create
sidebar = SidebarWidget()

# Add agents
sidebar.add_agent("agent-1", "Worker 1", "running")
sidebar.add_agent("agent-2", "Worker 2", "idle")

# Update status
sidebar.update_agent_status("agent-1", "done")

# Session info
sidebar.update_session_info(session_id="sess_xyz", start_time="14:30:45", uptime="00:10:30")
```

### MetricsPanel - Metrics Display

```python
from thegent.compositor import MetricsPanel

# Create
metrics = MetricsPanel()

# Add metrics
metrics.update_metric("requests", "1234")
metrics.update_metrics({"cpu": "45%", "memory": "2.1GB", "latency": "123ms"})
```

### ProgressIndicator - Progress Tracking

```python
from thegent.compositor import ProgressIndicator

# Create
progress = ProgressIndicator()

# Update progress
progress.update_progress(50, 100, "Processing files...")
# Renders: "Processing files...\n[████████░░░░░░░░] 50% (50/100)"
```

---

## Size Specifications

### Percentage

```python
from thegent.compositor import Size

size = Size(70, "%")
# 70% of parent width/height
```

### Fractions (Flexible)

```python
size = Size(1, "fr")  # 1 fraction unit (1fr)
size = Size(2, "fr")  # 2 fraction units (2fr)
```

### Fixed Cells

```python
size = Size(30, "cells")  # Exactly 30 character cells
```

### Auto

```python
size = Size(1, "auto")  # Automatic sizing
```

---

## Layout Constraints

```python
from thegent.compositor import LayoutConstraints, Size, Padding

constraints = LayoutConstraints(
    width=Size(50, "%"),
    height=Size(20, "cells"),
    min_width=10,
    max_width=100,
    padding=Padding(top=1, left=2),
)
```

---

## Building a Simple UI

```python
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from thegent.compositor import OutputWidget, StatusWidget, SidebarWidget, HeaderWidget, FooterStatusBar


class SimpleAgent(App):
    def compose(self) -> ComposeResult:
        yield HeaderWidget(title="My Agent", version="1.0")
        with Horizontal():
            yield OutputWidget(id="output")
            yield StatusWidget(id="status")
        yield SidebarWidget(id="sidebar")
        yield FooterStatusBar(id="footer")

    def on_mount(self):
        output = self.query_one("#output", OutputWidget)
        status = self.query_one("#status", StatusWidget)

        output.write("Agent started", style="green")
        status.update_status("running", model="claude-opus")


if __name__ == "__main__":
    app = SimpleAgent()
    app.run()
```

---

## Common Patterns

### Live Status Updates

```python
def update_agent_status():
    status = self.query_one("#status", StatusWidget)
    status.status = "running"
    status.tokens_used = 2500

    # Timer runs automatically
    status.start_timer()
```

### Output Streaming

```python
def stream_output(output_widget, lines):
    for line in lines:
        output_widget.write(line, timestamp=True)
```

### Multi-Agent Dashboard

```python
def setup_agents(sidebar, agents):
    for agent in agents:
        sidebar.add_agent(agent_id=agent.id, name=agent.name, status=agent.status)


def update_agent(sidebar, agent_id, new_status):
    sidebar.update_agent_status(agent_id, new_status)
```

---

## Styling

Components use Textual's CSS system. Default styles are included.

```python
# Custom colors via Textual CSS
widget.DEFAULT_CSS = """
OutputWidget {
    background: $surface;
    border: solid $accent;
}
"""
```

---

## Performance Tips

1. **Batch Updates** - Update multiple metrics at once

   ```python
   metrics.update_metrics({...})  # Better than individual updates
   ```

2. **Reuse Components** - Create once, update many times

   ```python
   output = OutputWidget()  # Create once
   # ... use many times with write()
   ```

3. **Use Reactive** - Status widget has reactive properties
   ```python
   status.status = "done"  # Auto-updates display
   ```

---

## Debugging

### Check Component State

```python
# Output widget
print(output.line_count)  # Number of lines

# Status widget
print(status.status)  # Current status
print(status.tokens_used)  # Current tokens

# Sidebar widget
print(sidebar.agents)  # Dictionary of agents
```

### View Generated CSS

```python
engine = LayoutEngine()
css = engine.generate_layout_css()
print(css)
```

---

## Next Steps

- Read full documentation: `TUI_COMPOSITOR_PHASE1_IMPLEMENTATION.md`
- Check tests for more examples: `tests/compositor/`
- Phase 2 roadmap: Input widgets, tables, themes

---

## Quick Reference

| Component         | Purpose             | Key Method              |
| ----------------- | ------------------- | ----------------------- |
| LayoutEngine      | Layout calculations | create_vertical_stack() |
| OutputWidget      | Display output      | write()                 |
| StatusWidget      | Show status         | update_status()         |
| SidebarWidget     | Track agents        | add_agent()             |
| HeaderWidget      | App title           | render()                |
| MetricsPanel      | Show metrics        | update_metrics()        |
| ProgressIndicator | Show progress       | update_progress()       |

---

**For issues or questions, see:** `TUI_COMPOSITOR_PHASE1_IMPLEMENTATION.md`
