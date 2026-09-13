# statusbar API Reference

> **Source**: `src/thegent/tui/widgets/statusbar.py`

Statusbar widget for TUI compositor.

---

## StatusItem

Represents a status indicator.

### Methods

#### StatusItem.**init**

```python
__init__(self: Any, label: str, value: str, active: bool, color: str)
```

---

---

## StatusbarWidget

Status bar showing session and agent status.

**Inherits from**: `Widget`

### Methods

#### StatusbarWidget.**init**

```python
__init__(self: Any)
```

---

#### StatusbarWidget.add_item

```python
add_item(self: Any, item: StatusItem)
```

Add a custom status item.

---

#### StatusbarWidget.clear_items

```python
clear_items(self: Any)
```

Clear all custom status items.

---

#### StatusbarWidget.compose

```python
compose(self: Any)
```

Create statusbar layout.

---

#### StatusbarWidget.on_mount

```python
on_mount(self: Any)
```

Initialize statusbar after mounting.

---

#### StatusbarWidget.remove_item

```python
remove_item(self: Any, label: str)
```

Remove a custom status item.

---

#### StatusbarWidget.set_status

```python
set_status(self: Any, status: str, message: str)
```

Set overall status with optional message.

---

#### StatusbarWidget.watch_agent_name

```python
watch_agent_name(self: Any, value: Any)
```

Update agent name display.

---

#### StatusbarWidget.watch_agent_status

```python
watch_agent_status(self: Any, value: str)
```

Update agent status display.

---

#### StatusbarWidget.watch_cwd

```python
watch_cwd(self: Any, value: str)
```

Update CWD display.

---

#### StatusbarWidget.watch_session_id

```python
watch_session_id(self: Any, value: Any)
```

Update session ID display.

---

---

## add_item

```python
add_item(self: Any, item: StatusItem)
```

Add a custom status item.

---

## clear_items

```python
clear_items(self: Any)
```

Clear all custom status items.

---

## compose

```python
compose(self: Any)
```

Create statusbar layout.

---

## on_mount

```python
on_mount(self: Any)
```

Initialize statusbar after mounting.

---

## remove_item

```python
remove_item(self: Any, label: str)
```

Remove a custom status item.

---

## set_status

```python
set_status(self: Any, status: str, message: str)
```

Set overall status with optional message.

---

## watch_agent_name

```python
watch_agent_name(self: Any, value: Any)
```

Update agent name display.

---

## watch_agent_status

```python
watch_agent_status(self: Any, value: str)
```

Update agent status display.

---

## watch_cwd

```python
watch_cwd(self: Any, value: str)
```

Update CWD display.

---

## watch_session_id

```python
watch_session_id(self: Any, value: Any)
```

Update session ID display.

---
