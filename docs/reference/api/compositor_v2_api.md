# compositor_v2 API Reference

> **Source**: `src/thegent/tui/compositor_v2.py`

TUI Compositor - Main application with PaneManager integration.

A unified terminal user interface for thegent using Textual with support for:

- Multi-pane layouts with split/merge operations
- Session persistence
- Layout management

---

## CompositorApp

Main TUI application for thegent.

Integrates:

- PaneManager for multi-pane layout
- SessionState for persistence
- Textual widgets for UI

**Inherits from**: `App`

### Methods

#### CompositorApp.**init**

```python
__init__(self: Any, context: Any)
```

---

#### CompositorApp.action_close_pane

```python
action_close_pane(self: Any)
```

Close current pane.

---

#### CompositorApp.action_focus_next

```python
action_focus_next(self: Any)
```

Focus the next pane.

---

#### CompositorApp.action_focus_prev

```python
action_focus_prev(self: Any)
```

Focus the previous pane.

---

#### CompositorApp.action_new_pane

```python
action_new_pane(self: Any)
```

Create a new terminal pane.

---

#### CompositorApp.action_quit

```python
action_quit(self: Any)
```

Quit the application.

---

#### CompositorApp.action_restore_layout

```python
action_restore_layout(self: Any)
```

Restore a saved layout.

---

#### CompositorApp.action_save_layout

```python
action_save_layout(self: Any)
```

Save current layout.

---

#### CompositorApp.action_show_help

```python
action_show_help(self: Any)
```

Show help dialog.

---

#### CompositorApp.action_split_horizontal

```python
action_split_horizontal(self: Any)
```

Split current pane horizontally.

---

#### CompositorApp.action_split_vertical

```python
action_split_vertical(self: Any)
```

Split current pane vertically.

---

#### CompositorApp.action_toggle_maximize

```python
action_toggle_maximize(self: Any)
```

Toggle output pane maximization.

---

#### CompositorApp.action_toggle_sidebar

```python
action_toggle_sidebar(self: Any)
```

Toggle sidebar visibility.

---

#### CompositorApp.append_output

```python
append_output(self: Any, text: str)
```

Append text to output pane.

---

#### CompositorApp.compose

```python
compose(self: Any)
```

Create the UI layout.

---

#### CompositorApp.on_mount

```python
on_mount(self: Any)
```

Initialize the app after mounting.

---

#### CompositorApp.set_agent_status

```python
set_agent_status(self: Any, status: str, agent: str)
```

Update agent status display.

---

#### CompositorApp.update_status

```python
update_status(self: Any)
```

Update status display.

---

#### CompositorApp.update_title

```python
update_title(self: Any)
```

Update window title.

---

#### CompositorApp.write_output

```python
write_output(self: Any, text: str)
```

Write text to output pane.

---

---

## TUIContext

Context passed to all widgets/components.

### Methods

#### TUIContext.**init**

```python
__init__(self: Any, session_id: Any, agent_name: Any, cwd: Any)
```

---

---

## action_close_pane

```python
action_close_pane(self: Any)
```

Close current pane.

---

## action_focus_next

```python
action_focus_next(self: Any)
```

Focus the next pane.

---

## action_focus_prev

```python
action_focus_prev(self: Any)
```

Focus the previous pane.

---

## action_new_pane

```python
action_new_pane(self: Any)
```

Create a new terminal pane.

---

## action_quit

```python
action_quit(self: Any)
```

Quit the application.

---

## action_restore_layout

```python
action_restore_layout(self: Any)
```

Restore a saved layout.

---

## action_save_layout

```python
action_save_layout(self: Any)
```

Save current layout.

---

## action_show_help

```python
action_show_help(self: Any)
```

Show help dialog.

---

## action_split_horizontal

```python
action_split_horizontal(self: Any)
```

Split current pane horizontally.

---

## action_split_vertical

```python
action_split_vertical(self: Any)
```

Split current pane vertically.

---

## action_toggle_maximize

```python
action_toggle_maximize(self: Any)
```

Toggle output pane maximization.

---

## action_toggle_sidebar

```python
action_toggle_sidebar(self: Any)
```

Toggle sidebar visibility.

---

## append_output

```python
append_output(self: Any, text: str)
```

Append text to output pane.

---

## compose

```python
compose(self: Any)
```

Create the UI layout.

---

## on_mount

```python
on_mount(self: Any)
```

Initialize the app after mounting.

---

## set_agent_status

```python
set_agent_status(self: Any, status: str, agent: str)
```

Update agent status display.

---

## update_status

```python
update_status(self: Any)
```

Update status display.

---

## update_title

```python
update_title(self: Any)
```

Update window title.

---

## write_output

```python
write_output(self: Any, text: str)
```

Write text to output pane.

---
