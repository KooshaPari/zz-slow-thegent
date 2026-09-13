# pane_manager API Reference

> **Source**: `src/thegent/ui/compositor/pane_manager.py`

PaneManager - Pane tree management for split/merge operations.

---

## PaneManager

Manages pane tree structure and operations.

### Methods

#### PaneManager.**init**

```python
__init__(self: Any)
```

Initialize PaneManager.

---

#### PaneManager.close_pane

```python
close_pane(self: Any)
```

Close the current pane.

**Returns**: True if successful, False otherwise

---

#### PaneManager.create_root_pane

```python
create_root_pane(self: Any, pane_id: str)
```

Create the root pane.

**Parameters**:

- `pane_id`: ID for the root pane

**Returns**: The root pane node

---

#### PaneManager.focus_next

```python
focus_next(self: Any)
```

Focus the next pane in rotation.

**Returns**: True if successful, False otherwise

---

#### PaneManager.restore_layout

```python
restore_layout(self: Any, layout_data: dict)
```

Restore pane tree from a dict.

**Parameters**:

- `layout_data`: Dictionary representation of tree

**Returns**: True if successful, False otherwise

---

#### PaneManager.save_layout

```python
save_layout(self: Any)
```

Serialize the pane tree to a dict.

**Returns**: Dictionary representation of the tree

---

#### PaneManager.split_pane

```python
split_pane(self: Any, direction: str)
```

Split the current pane.

**Parameters**:

- `direction`: "horizontal" or "vertical"

**Returns**: The new pane node, or None if no current pane

---

---

## PaneNode

Represents a node in the pane tree.

---

## close_pane

```python
close_pane(self: Any)
```

Close the current pane.

**Returns**: True if successful, False otherwise

---

## create_root_pane

```python
create_root_pane(self: Any, pane_id: str)
```

Create the root pane.

**Parameters**:

- `pane_id`: ID for the root pane

**Returns**: The root pane node

---

## focus_next

```python
focus_next(self: Any)
```

Focus the next pane in rotation.

**Returns**: True if successful, False otherwise

---

## restore_layout

```python
restore_layout(self: Any, layout_data: dict)
```

Restore pane tree from a dict.

**Parameters**:

- `layout_data`: Dictionary representation of tree

**Returns**: True if successful, False otherwise

---

## save_layout

```python
save_layout(self: Any)
```

Serialize the pane tree to a dict.

**Returns**: Dictionary representation of the tree

---

## split_pane

```python
split_pane(self: Any, direction: str)
```

Split the current pane.

**Parameters**:

- `direction`: "horizontal" or "vertical"

**Returns**: The new pane node, or None if no current pane

---
