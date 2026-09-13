# base API Reference

> **Source**: `src/thegent/tui/layouts/base.py`

Base layout classes for TUI compositor.

---

## BaseLayout

Base class for layout managers.

### Methods

#### BaseLayout.**init**

```python
__init__(self: Any, config: Any)
```

---

#### BaseLayout.apply_config

```python
apply_config(self: Any, config: LayoutConfig)
```

Apply a layout configuration.

---

#### BaseLayout.get_config

```python
get_config(self: Any)
```

Get current layout configuration.

---

#### BaseLayout.get_styles

```python
get_styles(self: Any)
```

Get CSS styles for the current layout.

---

#### BaseLayout.reset

```python
reset(self: Any)
```

Reset to default layout.

---

#### BaseLayout.restore_state

```python
restore_state(self: Any, name: str)
```

Restore a saved layout state.

---

#### BaseLayout.save_state

```python
save_state(self: Any, name: str)
```

Save current layout state.

---

#### BaseLayout.toggle_maximize

```python
toggle_maximize(self: Any)
```

Toggle output maximization.

---

#### BaseLayout.toggle_sidebar

```python
toggle_sidebar(self: Any)
```

Toggle sidebar visibility.

---

---

## FullOutputLayout

**Inherits from**: `BaseLayout`

**Method Resolution Order**: `FullOutputLayout -> BaseLayout`

### Methods

#### FullOutputLayout.apply_config

```python
apply_config(self: Any, config: LayoutConfig)
```

---

#### FullOutputLayout.get_config

```python
get_config(self: Any)
```

---

---

## LayoutConfig

Configuration for a layout.

---

## LayoutManager

Manages multiple layouts and transitions.

### Methods

#### LayoutManager.**init**

```python
__init__(self: Any)
```

---

#### LayoutManager.add_layout

```python
add_layout(self: Any, name: str, layout: BaseLayout)
```

Add a named layout.

---

#### LayoutManager.get_current_layout

```python
get_current_layout(self: Any)
```

Get the current layout.

---

#### LayoutManager.list_layouts

```python
list_layouts(self: Any)
```

List available layout names.

---

#### LayoutManager.switch_layout

```python
switch_layout(self: Any, name: str)
```

Switch to a named layout.

---

---

## SidebarLeftLayout

**Inherits from**: `BaseLayout`

**Method Resolution Order**: `SidebarLeftLayout -> BaseLayout`

### Methods

#### SidebarLeftLayout.apply_config

```python
apply_config(self: Any, config: LayoutConfig)
```

---

#### SidebarLeftLayout.get_config

```python
get_config(self: Any)
```

---

---

## add_layout

```python
add_layout(self: Any, name: str, layout: BaseLayout)
```

Add a named layout.

---

## apply_config

```python
apply_config(self: Any, config: LayoutConfig) -> None
```

---

## get_config

```python
get_config(self: Any) -> LayoutConfig
```

---

## get_current_layout

```python
get_current_layout(self: Any)
```

Get the current layout.

---

## get_styles

```python
get_styles(self: Any)
```

Get CSS styles for the current layout.

---

## list_layouts

```python
list_layouts(self: Any)
```

List available layout names.

---

## reset

```python
reset(self: Any)
```

Reset to default layout.

---

## restore_state

```python
restore_state(self: Any, name: str)
```

Restore a saved layout state.

---

## save_state

```python
save_state(self: Any, name: str)
```

Save current layout state.

---

## switch_layout

```python
switch_layout(self: Any, name: str)
```

Switch to a named layout.

---

## toggle_maximize

```python
toggle_maximize(self: Any)
```

Toggle output maximization.

---

## toggle_sidebar

```python
toggle_sidebar(self: Any)
```

Toggle sidebar visibility.

---
