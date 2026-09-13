# app API Reference

> **Source**: `src/thegent/ui/compositor/app.py`

CompositApp - Main Textual application for the TUI compositor.

---

## CompositApp

Main TUI Compositor application.

Features:

- Menubar with file/edit/view/tools/help menus
- Statusbar with session info and pane count
- Container for terminal panes
- Key bindings for pane management
- Lifecycle hooks for pane initialization/cleanup
- Error boundaries for crash recovery

**Inherits from**: `App`

### Methods

#### CompositApp.**init**

```python
__init__(self: Any, session_state: SessionState | None)
```

Initialize CompositApp.

**Parameters**:

- `session_state`: Optional session state for persistence

---

#### CompositApp.action_close_pane

```python
action_close_pane(self: Any)
```

Close the current pane.

Wrapped with error boundaries.
Decrements pane count (if > 1) and updates statusbar.

---

#### CompositApp.action_focus_next

```python
action_focus_next(self: Any)
```

Focus the next pane.

Wrapped with error boundaries.
Cycles focus through available panes.

---

#### CompositApp.action_new_pane

```python
action_new_pane(self: Any)
```

Create a new terminal pane.

Wrapped with error boundaries to catch pane creation failures.
Increments pane count and updates statusbar.

---

#### CompositApp.action_quit

```python
action_quit(self: Any)
```

Quit the application.

Cleans up resources and exits.

---

#### CompositApp.action_retry_pane

```python
action_retry_pane(self: Any)
```

Retry rendering the current pane.

Clears error state and attempts to re-render.

---

#### CompositApp.action_split_horizontal

```python
action_split_horizontal(self: Any)
```

Split the current pane horizontally.

Wrapped with error boundaries.
Increments pane count and updates statusbar.

---

#### CompositApp.action_split_vertical

```python
action_split_vertical(self: Any)
```

Split the current pane vertically.

Wrapped with error boundaries.
Increments pane count and updates statusbar.

---

#### CompositApp.compose

```python
compose(self: Any)
```

Compose the app layout.

**Returns**: Header widget
Main pane container
Statusbar widget
Footer widget

---

#### CompositApp.on_mount

```python
on_mount(self: Any)
```

Called when the app is mounted.

Lifecycle hook that:

- Sets window title and subtitle
- Initializes pane count
- Spawns shell processes for panes
- Sets up IPC/message passing
- Initializes state tracking

---

#### CompositApp.on_panel_mounted

```python
on_panel_mounted(self: Any, message: PanelMounted)
```

Handle PanelMounted message from terminal panes.

---

#### CompositApp.on_panel_unmounted

```python
on_panel_unmounted(self: Any, message: PanelUnmounted)
```

Handle PanelUnmounted message from terminal panes.

---

#### CompositApp.on_unmount

```python
on_unmount(self: Any)
```

Called when the app is about to unmount.

Lifecycle hook that:

- Gracefully terminates all child processes
- Cleans up IPC channels
- Saves session state

---

---

## ErrorBoundary

Error boundary widget for displaying pane render errors.

**Inherits from**: `Static`

### Methods

#### ErrorBoundary.**init**

```python
__init__(self: Any, error_message: str, error_type: str, stack_trace: str, pane_id: str)
```

Initialize error boundary.

**Parameters**:

- `error_message`: Human-readable error message
- `error_type`: Type of error (e.g., "Render Error", "Process Error")
- `stack_trace`: Full stack trace for debugging
- `pane_id`: ID of the pane that failed

---

#### ErrorBoundary.render

```python
render(self: Any)
```

Render error panel.

---

---

## Statusbar

Custom status bar showing session and pane information.

**Inherits from**: `Static`

### Methods

#### Statusbar.render

```python
render(self: Any)
```

Render status bar content.

---

---

## action_close_pane

```python
action_close_pane(self: Any)
```

Close the current pane.

Wrapped with error boundaries.
Decrements pane count (if > 1) and updates statusbar.

---

## action_focus_next

```python
action_focus_next(self: Any)
```

Focus the next pane.

Wrapped with error boundaries.
Cycles focus through available panes.

---

## action_new_pane

```python
action_new_pane(self: Any)
```

Create a new terminal pane.

Wrapped with error boundaries to catch pane creation failures.
Increments pane count and updates statusbar.

---

## action_quit

```python
action_quit(self: Any)
```

Quit the application.

Cleans up resources and exits.

---

## action_retry_pane

```python
action_retry_pane(self: Any)
```

Retry rendering the current pane.

Clears error state and attempts to re-render.

---

## action_split_horizontal

```python
action_split_horizontal(self: Any)
```

Split the current pane horizontally.

Wrapped with error boundaries.
Increments pane count and updates statusbar.

---

## action_split_vertical

```python
action_split_vertical(self: Any)
```

Split the current pane vertically.

Wrapped with error boundaries.
Increments pane count and updates statusbar.

---

## compose

```python
compose(self: Any)
```

Compose the app layout.

**Returns**: Header widget
Main pane container
Statusbar widget
Footer widget

---

## on_mount

```python
on_mount(self: Any)
```

Called when the app is mounted.

Lifecycle hook that:

- Sets window title and subtitle
- Initializes pane count
- Spawns shell processes for panes
- Sets up IPC/message passing
- Initializes state tracking

---

## on_panel_mounted

```python
on_panel_mounted(self: Any, message: PanelMounted)
```

Handle PanelMounted message from terminal panes.

---

## on_panel_unmounted

```python
on_panel_unmounted(self: Any, message: PanelUnmounted)
```

Handle PanelUnmounted message from terminal panes.

---

## on_unmount

```python
on_unmount(self: Any)
```

Called when the app is about to unmount.

Lifecycle hook that:

- Gracefully terminates all child processes
- Cleans up IPC channels
- Saves session state

---

## render

```python
render(self: Any)
```

Render status bar content.

---
