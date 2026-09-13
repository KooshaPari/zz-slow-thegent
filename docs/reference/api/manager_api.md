# manager API Reference

> **Source**: `src/thegent/tui/layouts/manager.py`

Layout manager for TUI compositor.

Provides multi-pane layout management with save/restore functionality.

---

## LayoutManager

Manages layout persistence and switching.

### Methods

#### LayoutManager.**init**

```python
__init__(self: Any, storage_dir: Any)
```

---

#### LayoutManager.create_layout

```python
create_layout(self: Any, name: str, root: Any)
```

Create a new layout.

---

#### LayoutManager.delete_layout

```python
delete_layout(self: Any, name: str)
```

Delete a layout.

---

#### LayoutManager.duplicate_layout

```python
duplicate_layout(self: Any, source_name: str, new_name: str)
```

Duplicate an existing layout.

---

#### LayoutManager.get_current

```python
get_current(self: Any)
```

Get the current active layout.

---

#### LayoutManager.get_layout

```python
get_layout(self: Any, name: str)
```

Get a layout by name.

---

#### LayoutManager.list_layouts

```python
list_layouts(self: Any)
```

List all saved layouts.

---

#### LayoutManager.rename_layout

```python
rename_layout(self: Any, old_name: str, new_name: str)
```

Rename a layout.

---

#### LayoutManager.switch_layout

```python
switch_layout(self: Any, name: str)
```

Switch to a layout (returns the state for application).

---

---

## LayoutState

Complete layout state.

---

## PaneConfig

Configuration for a single pane.

---

## SplitConfig

Configuration for a split pane.

---

## create_default_layout

Create the default layout.

---

## create_full_output_layout

Create a full-screen output layout.

---

## create_horizontal_split

```python
create_horizontal_split(left_pane: PaneConfig, right_pane: PaneConfig, left_weight: int, right_weight: int)
```

Create a horizontal split layout.

---

## create_layout

```python
create_layout(self: Any, name: str, root: Any)
```

Create a new layout.

---

## create_main_sidebar

```python
create_main_sidebar(main_pane: PaneConfig, sidebar_pane: PaneConfig, sidebar_width: int)
```

Create a main content + sidebar layout.

---

## create_terminal_layout

Create a layout optimized for terminal use.

---

## create_three_column

```python
create_three_column(left: PaneConfig, center: PaneConfig, right: PaneConfig, weights: Any)
```

Create a three-column layout.

---

## create_vertical_split

```python
create_vertical_split(top_pane: PaneConfig, bottom_pane: PaneConfig, top_weight: int, bottom_weight: int)
```

Create a vertical split layout.

---

## delete_layout

```python
delete_layout(self: Any, name: str)
```

Delete a layout.

---

## duplicate_layout

```python
duplicate_layout(self: Any, source_name: str, new_name: str)
```

Duplicate an existing layout.

---

## get_current

```python
get_current(self: Any)
```

Get the current active layout.

---

## get_layout

```python
get_layout(self: Any, name: str)
```

Get a layout by name.

---

## list_layouts

```python
list_layouts(self: Any)
```

List all saved layouts.

---

## rename_layout

```python
rename_layout(self: Any, old_name: str, new_name: str)
```

Rename a layout.

---

## switch_layout

```python
switch_layout(self: Any, name: str)
```

Switch to a layout (returns the state for application).

---
