# cli_compositor API Reference

> **Source**: `src/thegent/ui/cli_compositor.py`

CLI Compositor: composites progress bars, status panels, and output.

Integrates with the Compositor panel system (thegent.ui.compositor.compositor)
to provide rich.progress-backed progress bars and dynamic status lines for
long-running CLI commands.

Main exports:

- ProgressPanel: A compositor panel backed by a rich Progress task.
- StatusPanel: A compositor panel backed by a dynamic callable.
- CliCompositor: Manages multiple progress bars and info panels in CLI output.

---

## CliCompositor

Manages multiple progress bars and info panels in CLI output.

Uses rich.progress.Progress for progress tracking and rich.live.Live for
live rendering of the combined panel output. Integrates with the
Compositor panel system for lifecycle management.

All progress panels share a single Progress instance so that they render
in a unified live display. Status panels render beneath progress bars in
a rich Table layout.

Usage::

    with CliCompositor() as comp:
        panel = comp.add_progress("download", total=100, description="Downloading…")
        comp.add_status_line("status", lambda: "Running…")
        for i in range(100):
            comp.update_progress("download", advance=1)
        comp.complete_progress("download")

### Methods

#### CliCompositor.**init**

```python
__init__(self: Any, console: Any)
```

Initialise a CliCompositor.

**Parameters**:

- `console`: Rich Console to use for output. Creates a new one if None.
- `refresh_per_second`: How many times per second to refresh the live display.
- `transient`: If True, the live display disappears on exit (useful for
  non-interactive pipelines).

---

#### CliCompositor.add_progress

```python
add_progress(self: Any, name: str, total: int, description: str)
```

Add a named progress bar panel.

If a panel with the same name already exists it is replaced.

**Parameters**:

- `name`: Unique name for this progress panel.
- `total`: Total number of steps for the progress bar.
- `description`: Initial description shown beside the bar.

**Returns**: The created ProgressPanel.

---

#### CliCompositor.add_status_line

```python
add_status_line(self: Any, name: str, content_fn: Callable[(Any, str)])
```

Add a named dynamic status line.

Status lines are rendered beneath all progress bars. If a status
panel with the same name already exists it is replaced.

**Parameters**:

- `name`: Unique name for this status panel.
- `content_fn`: Callable returning the status string. Called each render.

---

#### CliCompositor.complete_progress

```python
complete_progress(self: Any, name: str)
```

Mark a named progress panel as fully completed.

**Parameters**:

- `name`: The progress panel name.

---

#### CliCompositor.progress_panel_names

```python
progress_panel_names(self: Any)
```

Return ordered list of current progress panel names.

---

#### CliCompositor.remove_progress

```python
remove_progress(self: Any, name: str)
```

Remove a named progress panel entirely.

**Parameters**:

- `name`: The progress panel name.

**Returns**: True if found and removed, False if not found.

---

#### CliCompositor.remove_status_line

```python
remove_status_line(self: Any, name: str)
```

Remove a named status panel.

**Parameters**:

- `name`: The status panel name.

**Returns**: True if found and removed, False if not found.

---

#### CliCompositor.render

```python
render(self: Any)
```

Build and return a rich Table containing all panels.

Progress bars are rendered first via the Progress instance, then
status panels appear as rows in the table.

**Returns**: A rich Table renderable containing the combined display.

---

#### CliCompositor.status_panel_names

```python
status_panel_names(self: Any)
```

Return ordered list of current status panel names.

---

#### CliCompositor.update_progress

```python
update_progress(self: Any, name: str, advance: int, description: Any)
```

Update a named progress panel.

**Parameters**:

- `name`: The progress panel name.
- `advance`: Number of steps to advance.
- `description`: Optional new description.

---

---

## ProgressPanel

A compositor panel backed by a rich Progress bar task.

### Methods

#### ProgressPanel.advance

```python
advance(self: Any, amount: int, description: Any)
```

Advance the underlying progress task.

**Parameters**:

- `amount`: Number of steps to advance.
- `description`: Optional new description to display.

---

#### ProgressPanel.complete

```python
complete(self: Any)
```

Mark the progress task as fully completed.

---

#### ProgressPanel.render

```python
render(self: Any)
```

Return a text representation of current progress state.

---

---

## StatusPanel

A compositor panel backed by a dynamic callable that returns a status string.

### Methods

#### StatusPanel.render

```python
render(self: Any)
```

Render the current status string from content_fn.

---

---

## add_progress

```python
add_progress(self: Any, name: str, total: int, description: str)
```

Add a named progress bar panel.

If a panel with the same name already exists it is replaced.

**Parameters**:

- `name`: Unique name for this progress panel.
- `total`: Total number of steps for the progress bar.
- `description`: Initial description shown beside the bar.

**Returns**: The created ProgressPanel.

---

## add_status_line

```python
add_status_line(self: Any, name: str, content_fn: Callable[(Any, str)])
```

Add a named dynamic status line.

Status lines are rendered beneath all progress bars. If a status
panel with the same name already exists it is replaced.

**Parameters**:

- `name`: Unique name for this status panel.
- `content_fn`: Callable returning the status string. Called each render.

---

## advance

```python
advance(self: Any, amount: int, description: Any)
```

Advance the underlying progress task.

**Parameters**:

- `amount`: Number of steps to advance.
- `description`: Optional new description to display.

---

## complete

```python
complete(self: Any)
```

Mark the progress task as fully completed.

---

## complete_progress

```python
complete_progress(self: Any, name: str)
```

Mark a named progress panel as fully completed.

**Parameters**:

- `name`: The progress panel name.

**Raises**:

- `KeyError`: If no progress panel with `name` exists.

---

## make_cli_compositor

Factory helper to build a CliCompositor with common defaults.

**Parameters**:

- `console`: Optional Rich Console; creates a fresh one if None.
- `refresh_per_second`: Live refresh rate.
- `transient`: Whether the display disappears on exit (default: True for CI).

**Returns**: A configured CliCompositor (not yet entered as context manager).

---

## progress_panel_names

```python
progress_panel_names(self: Any)
```

Return ordered list of current progress panel names.

---

## remove_progress

```python
remove_progress(self: Any, name: str)
```

Remove a named progress panel entirely.

**Parameters**:

- `name`: The progress panel name.

**Returns**: True if found and removed, False if not found.

---

## remove_status_line

```python
remove_status_line(self: Any, name: str)
```

Remove a named status panel.

**Parameters**:

- `name`: The status panel name.

**Returns**: True if found and removed, False if not found.

---

## render

```python
render(self: Any)
```

Build and return a rich Table containing all panels.

Progress bars are rendered first via the Progress instance, then
status panels appear as rows in the table.

**Returns**: A rich Table renderable containing the combined display.

---

## status_panel_names

```python
status_panel_names(self: Any)
```

Return ordered list of current status panel names.

---

## update_progress

```python
update_progress(self: Any, name: str, advance: int, description: Any)
```

Update a named progress panel.

**Parameters**:

- `name`: The progress panel name.
- `advance`: Number of steps to advance.
- `description`: Optional new description.

**Raises**:

- `KeyError`: If no progress panel with `name` exists.

---
