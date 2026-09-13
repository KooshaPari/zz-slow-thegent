# compositor_manager API Reference

> **Source**: `src/thegent/ui/compositor_manager.py`

CompositorManager: manage multiple Compositor instances with layout.

Provides:

- Layout: Enum of supported multi-compositor layouts (SINGLE, SPLIT_H,
  SPLIT_V, GRID_2X2).
- CompositorSlot: Dataclass binding a Compositor to a named slot with a
  relative size weight.
- CompositorManager: Manages a collection of CompositorSlots, computes per-
  slot column widths from weights and layout, renders each compositor into a
  box-drawn frame, and combines the frames into a single terminal string.

---

## CompositorManager

Manage multiple Compositor instances and provide layout management.

The manager stores slots in insertion order. A _focused_ slot is brought
visually to the foreground by rendering its border with a `[*]` marker.

### Methods

#### CompositorManager.**init**

```python
__init__(self: Any, layout: Layout)
```

Initialise an empty manager with the given layout.

---

#### CompositorManager.add_compositor

```python
add_compositor(self: Any, compositor: Compositor, slot_id: str, weight: float)
```

Add a compositor to the manager under _slot_id_.

If a slot with the same ID already exists it is replaced.

**Parameters**:

- `compositor`: The :class:`Compositor` to manage.
- `slot_id`: Unique identifier for the slot.
- `weight`: Relative size weight (must be &gt; 0).

---

#### CompositorManager.focus

```python
focus(self: Any, slot_id: str)
```

Bring the compositor at _slot_id_ to the foreground.

**Parameters**:

- `slot_id`: The slot to focus.

---

#### CompositorManager.get_compositor

```python
get_compositor(self: Any, slot_id: str)
```

Return the Compositor for _slot_id_, or None if not found.

**Parameters**:

- `slot_id`: Slot identifier.

**Returns**: The :class:`Compositor`, or _None_.

---

#### CompositorManager.get_focused

```python
get_focused(self: Any)
```

Return the currently focused :class:`CompositorSlot`, or None.

**Returns**: The focused slot, or _None_ if no slots are registered.

---

#### CompositorManager.layout

```python
layout(self: Any)
```

The current layout.

---

#### CompositorManager.remove_compositor

```python
remove_compositor(self: Any, slot_id: str)
```

Remove a slot by ID.

**Parameters**:

- `slot_id`: The slot to remove.

**Returns**: `True` if the slot existed and was removed, `False` otherwise.

---

#### CompositorManager.render_all

```python
render_all(self: Any, width: int)
```

Render all compositors and combine them with ANSI box drawing.

Each compositor's panels are rendered and wrapped in a single-line box
border. The focused slot's border title shows a `[*]` indicator.

Layout rules:

- `SINGLE`: The first slot fills the entire _width_.
- `SPLIT_H`: Slots are side-by-side; column widths are proportional
  to slot weights.
- `SPLIT_V`: Slots are stacked; each gets the full _width_.
- `GRID_2X2`: First four slots form a 2x2 grid; any extra slots
  fall through as a vertical stack below the grid.

**Parameters**:

- `width`: Total terminal character width (default 80).

**Returns**: A multi-line string suitable for writing to a terminal.

---

#### CompositorManager.slot_ids

```python
slot_ids(self: Any)
```

Ordered list of registered slot IDs.

---

#### CompositorManager.switch_layout

```python
switch_layout(self: Any, layout: Layout)
```

Change the current layout.

**Parameters**:

- `layout`: New :class:`Layout` value.

---

---

## CompositorSlot

A named slot that holds one Compositor with a relative size weight.

### Methods

---

## Layout

Supported multi-compositor screen layouts.

**Inherits from**: `Enum`

---

## add_compositor

```python
add_compositor(self: Any, compositor: Compositor, slot_id: str, weight: float)
```

Add a compositor to the manager under _slot_id_.

If a slot with the same ID already exists it is replaced.

**Parameters**:

- `compositor`: The :class:`Compositor` to manage.
- `slot_id`: Unique identifier for the slot.
- `weight`: Relative size weight (must be &gt; 0).

---

## focus

```python
focus(self: Any, slot_id: str)
```

Bring the compositor at _slot_id_ to the foreground.

**Parameters**:

- `slot_id`: The slot to focus.

**Raises**:

- `KeyError`: If no slot with the given ID exists.

---

## get_compositor

```python
get_compositor(self: Any, slot_id: str)
```

Return the Compositor for _slot_id_, or None if not found.

**Parameters**:

- `slot_id`: Slot identifier.

**Returns**: The :class:`Compositor`, or _None_.

---

## get_focused

```python
get_focused(self: Any)
```

Return the currently focused :class:`CompositorSlot`, or None.

**Returns**: The focused slot, or _None_ if no slots are registered.

---

## layout

```python
layout(self: Any)
```

The current layout.

---

## remove_compositor

```python
remove_compositor(self: Any, slot_id: str)
```

Remove a slot by ID.

**Parameters**:

- `slot_id`: The slot to remove.

**Returns**: `True` if the slot existed and was removed, `False` otherwise.

---

## render_all

```python
render_all(self: Any, width: int)
```

Render all compositors and combine them with ANSI box drawing.

Each compositor's panels are rendered and wrapped in a single-line box
border. The focused slot's border title shows a `[*]` indicator.

Layout rules:

- `SINGLE`: The first slot fills the entire _width_.
- `SPLIT_H`: Slots are side-by-side; column widths are proportional
  to slot weights.
- `SPLIT_V`: Slots are stacked; each gets the full _width_.
- `GRID_2X2`: First four slots form a 2x2 grid; any extra slots
  fall through as a vertical stack below the grid.

**Parameters**:

- `width`: Total terminal character width (default 80).

**Returns**: A multi-line string suitable for writing to a terminal.

---

## slot_ids

```python
slot_ids(self: Any)
```

Ordered list of registered slot IDs.

---

## switch_layout

```python
switch_layout(self: Any, layout: Layout)
```

Change the current layout.

**Parameters**:

- `layout`: New :class:`Layout` value.

---
