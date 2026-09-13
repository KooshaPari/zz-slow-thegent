# layout_engine API Reference

> **Source**: `src/thegent/compositor/layout_engine.py`

Core layout engine for TUI Compositor.

Provides layout primitives for organizing widgets: vertical stacking, horizontal arrangement,
nested containers, and responsive sizing.

---

## Direction

Layout direction.

**Inherits from**: `StrEnum`

---

## LayoutConstraints

Layout constraints for a widget or container.

### Methods

---

## LayoutEngine

Core layout engine for compositing multiple widgets.

### Methods

#### LayoutEngine.**init**

```python
__init__(self: Any)
```

Initialize the layout engine.

---

#### LayoutEngine.calculate_layout

```python
calculate_layout(self: Any, width: int, height: int)
```

Calculate final layout dimensions.

**Parameters**:

- `width`: Container width in cells
- `height`: Container height in cells

**Returns**: Dictionary mapping widget IDs to (x, y, w, h) tuples

---

#### LayoutEngine.create_grid

```python
create_grid(self: Any, rows: int, cols: int, widget_ids: list[str])
```

Create a grid layout.

**Parameters**:

- `rows`: Number of rows
- `cols`: Number of columns
- `widget_ids`: List of widget IDs in row-major order

**Returns**: Root node of the grid

---

#### LayoutEngine.create_horizontal_stack

```python
create_horizontal_stack(self: Any, widget_ids: list[str], constraints: Any)
```

Create a horizontal stack of widgets.

**Parameters**:

- `widget_ids`: List of widget IDs
- `constraints`: Optional list of constraints per widget

**Returns**: Root node of the stack

---

#### LayoutEngine.create_vertical_stack

```python
create_vertical_stack(self: Any, widget_ids: list[str], constraints: Any)
```

Create a vertical stack of widgets.

**Parameters**:

- `widget_ids`: List of widget IDs
- `constraints`: Optional list of constraints per widget

**Returns**: Root node of the stack

---

#### LayoutEngine.generate_layout_css

```python
generate_layout_css(self: Any)
```

Generate CSS for the current layout.

**Returns**: Complete CSS rules

---

#### LayoutEngine.get_widget

```python
get_widget(self: Any, widget_id: str)
```

Get a registered widget.

**Parameters**:

- `widget_id`: Widget ID

**Returns**: Widget instance or None

---

#### LayoutEngine.register_widget

```python
register_widget(self: Any, widget_id: str, widget: object)
```

Register a widget instance.

**Parameters**:

- `widget_id`: Unique widget ID
- `widget`: Widget instance

---

---

## LayoutNode

Represents a layout node in the layout tree.

### Methods

#### LayoutNode.**init**

```python
__init__(self: Any, direction: Direction, constraints: Any)
```

Initialize a layout node.

**Parameters**:

- `direction`: Layout direction (vertical or horizontal)
- `constraints`: Layout constraints

---

#### LayoutNode.add_child

```python
add_child(self: Any, child: Any, constraints: Any)
```

Add a child to this node.

**Parameters**:

- `child`: Child node or widget ID
- `constraints`: Optional layout constraints

**Returns**: The child node

---

#### LayoutNode.generate_css

```python
generate_css(self: Any, indent: int)
```

Generate CSS for this layout node.

**Parameters**:

- `indent`: CSS indentation level

**Returns**: CSS rules

---

#### LayoutNode.get_css_for_child

```python
get_css_for_child(self: Any, index: int)
```

Get CSS for a child at the given index.

**Parameters**:

- `index`: Child index

**Returns**: CSS size specification

---

#### LayoutNode.to_dict

```python
to_dict(self: Any)
```

Serialize layout to dictionary.

**Returns**: Dictionary representation of layout tree

---

---

## Margin

Margin specification.

### Methods

#### Margin.to_textual_css

```python
to_textual_css(self: Any)
```

Convert to Textual CSS margin.

---

---

## Padding

Padding specification.

### Methods

#### Padding.to_textual_css

```python
to_textual_css(self: Any)
```

Convert to Textual CSS padding.

---

---

## Size

Represents a dimension (width or height).

### Methods

#### Size.**init**

```python
__init__(self: Any, value: float, unit: Any)
```

Initialize a size.

**Parameters**:

- `value`: Numeric value
- `unit`: Unit type (%, fr, cells, auto)

---

#### Size.to_textual_css

```python
to_textual_css(self: Any)
```

Convert to Textual CSS size specification.

**Returns**: CSS size string (e.g., "1fr", "70%", "30w")

---

---

## SizeUnit

Size specification unit.

**Inherits from**: `StrEnum`

---

## add_child

```python
add_child(self: Any, child: Any, constraints: Any)
```

Add a child to this node.

**Parameters**:

- `child`: Child node or widget ID
- `constraints`: Optional layout constraints

**Returns**: The child node

---

## calculate_layout

```python
calculate_layout(self: Any, width: int, height: int)
```

Calculate final layout dimensions.

**Parameters**:

- `width`: Container width in cells
- `height`: Container height in cells

**Returns**: Dictionary mapping widget IDs to (x, y, w, h) tuples

---

## create_grid

```python
create_grid(self: Any, rows: int, cols: int, widget_ids: list[str])
```

Create a grid layout.

**Parameters**:

- `rows`: Number of rows
- `cols`: Number of columns
- `widget_ids`: List of widget IDs in row-major order

**Returns**: Root node of the grid

---

## create_horizontal_stack

```python
create_horizontal_stack(self: Any, widget_ids: list[str], constraints: Any)
```

Create a horizontal stack of widgets.

**Parameters**:

- `widget_ids`: List of widget IDs
- `constraints`: Optional list of constraints per widget

**Returns**: Root node of the stack

---

## create_vertical_stack

```python
create_vertical_stack(self: Any, widget_ids: list[str], constraints: Any)
```

Create a vertical stack of widgets.

**Parameters**:

- `widget_ids`: List of widget IDs
- `constraints`: Optional list of constraints per widget

**Returns**: Root node of the stack

---

## generate_css

```python
generate_css(self: Any, indent: int)
```

Generate CSS for this layout node.

**Parameters**:

- `indent`: CSS indentation level

**Returns**: CSS rules

---

## generate_layout_css

```python
generate_layout_css(self: Any)
```

Generate CSS for the current layout.

**Returns**: Complete CSS rules

---

## get_css_for_child

```python
get_css_for_child(self: Any, index: int)
```

Get CSS for a child at the given index.

**Parameters**:

- `index`: Child index

**Returns**: CSS size specification

---

## get_widget

```python
get_widget(self: Any, widget_id: str)
```

Get a registered widget.

**Parameters**:

- `widget_id`: Widget ID

**Returns**: Widget instance or None

---

## register_widget

```python
register_widget(self: Any, widget_id: str, widget: object)
```

Register a widget instance.

**Parameters**:

- `widget_id`: Unique widget ID
- `widget`: Widget instance

---

## to_dict

```python
to_dict(self: Any)
```

Serialize layout to dictionary.

**Returns**: Dictionary representation of layout tree

---

## to_textual_css

```python
to_textual_css(self: Any)
```

Convert to Textual CSS margin.

---
