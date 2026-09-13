# menubar API Reference

> **Source**: `src/thegent/tui/widgets/menubar.py`

Menubar widget for TUI compositor.

---

## MenuDropdown

Dropdown menu widget.

**Inherits from**: `Static`

### Methods

#### MenuDropdown.**init**

```python
__init__(self: Any, items: list[tuple[(str, Any)]])
```

---

#### MenuDropdown.compose

```python
compose(self: Any)
```

Create dropdown items.

---

---

## MenubarWidget

Simple menubar widget with keyboard shortcuts display.

**Inherits from**: `Widget`

### Methods

#### MenubarWidget.action_toggle_menu

```python
action_toggle_menu(self: Any, menu_name: str)
```

Toggle a menu dropdown.

---

#### MenubarWidget.compose

```python
compose(self: Any)
```

Create menubar layout.

---

#### MenubarWidget.on_click

```python
on_click(self: Any, event: Click)
```

Handle click on menu items.

---

#### MenubarWidget.on_mount

```python
on_mount(self: Any)
```

Initialize menubar after mounting.

---

---

## action_toggle_menu

```python
action_toggle_menu(self: Any, menu_name: str)
```

Toggle a menu dropdown.

---

## compose

```python
compose(self: Any)
```

Create dropdown items.

---

## on_click

```python
on_click(self: Any, event: Click)
```

Handle click on menu items.

---

## on_mount

```python
on_mount(self: Any)
```

Initialize menubar after mounting.

---
