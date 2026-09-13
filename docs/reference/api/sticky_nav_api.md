# sticky_nav API Reference

> **Source**: `src/thegent/docgen/sticky_nav.py`

Sticky sidebar and header for documentation.

---

## StickyNav

Sticky navigation component for documentation.

### Methods

#### StickyNav.**init**

```python
__init__(self: Any, sidebar: bool, header: bool)
```

Initialize sticky navigation.

**Parameters**:

- `sidebar`: Enable sticky sidebar
- `header`: Enable sticky header

---

#### StickyNav.render_css

```python
render_css(self: Any)
```

Render CSS for sticky navigation.

**Returns**: CSS string

---

#### StickyNav.render_html

```python
render_html(self: Any, sidebar_content: str, header_content: str)
```

Render HTML structure with sticky navigation.

**Parameters**:

- `sidebar_content`: Sidebar HTML content
- `header_content`: Header HTML content

**Returns**: HTML string

---

---

## render_css

```python
render_css(self: Any)
```

Render CSS for sticky navigation.

**Returns**: CSS string

---

## render_html

```python
render_html(self: Any, sidebar_content: str, header_content: str)
```

Render HTML structure with sticky navigation.

**Parameters**:

- `sidebar_content`: Sidebar HTML content
- `header_content`: Header HTML content

**Returns**: HTML string

---
