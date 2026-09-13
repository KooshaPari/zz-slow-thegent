# registry_tui API Reference

> **Source**: `src/thegent/tui/registry_tui.py`

Agent Registry TUI using Textual (WP-9000).

---

## RegistryTUI

Unified Agent Registry TUI.

**Inherits from**: `App`

### Methods

#### RegistryTUI.**init**

```python
__init__(self: Any)
```

---

#### RegistryTUI.action_refresh

```python
action_refresh(self: Any)
```

---

#### RegistryTUI.action_toggle_all

```python
action_toggle_all(self: Any)
```

---

#### RegistryTUI.compose

```python
compose(self: Any)
```

---

#### RegistryTUI.on_mount

```python
on_mount(self: Any)
```

---

#### RegistryTUI.on_session_selected

```python
on_session_selected(self: Any, event: DataTable.RowSelected)
```

---

---

## SessionDetails

Details panel for a selected session.

**Inherits from**: `Static`

### Methods

#### SessionDetails.update_details

```python
update_details(self: Any, session: dict[(str, Any)])
```

---

---

## action_refresh

```python
action_refresh(self: Any) -> None
```

---

## action_toggle_all

```python
action_toggle_all(self: Any) -> None
```

---

## compose

```python
compose(self: Any) -> ComposeResult
```

---

## on_mount

```python
on_mount(self: Any) -> None
```

---

## on_session_selected

```python
on_session_selected(self: Any, event: DataTable.RowSelected) -> None
```

---

## update_details

```python
update_details(self: Any, session: dict[(str, Any)]) -> None
```

---
