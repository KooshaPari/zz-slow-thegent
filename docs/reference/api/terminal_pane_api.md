# terminal_pane API Reference

> **Source**: `src/thegent/tui/widgets/terminal_pane.py`

Terminal pane widget for TUI compositor.

Provides a terminal emulator pane using Python's asyncio and pty modules.
Supports subprocess execution and output display.

---

## TerminalConfig

Configuration for terminal pane.

---

## TerminalManager

Manages multiple terminal panes.

### Methods

#### TerminalManager.**init**

```python
__init__(self: Any)
```

---

#### TerminalManager.add_pane

```python
add_pane(self: Any, pane_id: str, pane: TerminalPane)
```

Add a terminal pane.

---

#### TerminalManager.get_active

```python
get_active(self: Any)
```

Get the active pane.

---

#### TerminalManager.get_pane

```python
get_pane(self: Any, pane_id: str)
```

Get a terminal pane by ID.

---

#### TerminalManager.list_panes

```python
list_panes(self: Any)
```

List all pane IDs.

---

#### TerminalManager.set_active

```python
set_active(self: Any, pane_id: str)
```

Set the active pane.

---

---

## TerminalPane

Widget that displays terminal output and executes commands.

**Inherits from**: `Widget`

### Methods

#### TerminalPane.**init**

```python
__init__(self: Any)
```

---

#### TerminalPane.clear

```python
clear(self: Any)
```

Clear the terminal output.

---

#### TerminalPane.get_output

```python
get_output(self: Any)
```

Get all output as a string.

---

#### TerminalPane.on_resize

```python
on_resize(self: Any, event: Resize)
```

Handle terminal resize.

---

---

## TerminalSize

Terminal dimensions in rows/cols.

---

## add_pane

```python
add_pane(self: Any, pane_id: str, pane: TerminalPane)
```

Add a terminal pane.

---

## clear

```python
clear(self: Any)
```

Clear the terminal output.

---

## get_active

```python
get_active(self: Any)
```

Get the active pane.

---

## get_output

```python
get_output(self: Any)
```

Get all output as a string.

---

## get_pane

```python
get_pane(self: Any, pane_id: str)
```

Get a terminal pane by ID.

---

## list_panes

```python
list_panes(self: Any)
```

List all pane IDs.

---

## on_resize

```python
on_resize(self: Any, event: Resize)
```

Handle terminal resize.

---

## set_active

```python
set_active(self: Any, pane_id: str)
```

Set the active pane.

---
