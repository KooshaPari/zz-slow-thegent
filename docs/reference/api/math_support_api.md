# math_support API Reference

> **Source**: `src/thegent/docgen/math_support.py`

KaTeX math support for documentation.

---

## MathSupport

KaTeX math rendering support.

### Methods

#### MathSupport.**init**

```python
__init__(self: Any, auto_render: bool)
```

Initialize math support.

**Parameters**:

- `auto_render`: Auto-render math expressions

---

#### MathSupport.render_block

```python
render_block(self: Any, expression: str)
```

Render block math expression.

**Parameters**:

- `expression`: Math expression

**Returns**: HTML string

---

#### MathSupport.render_inline

```python
render_inline(self: Any, expression: str)
```

Render inline math expression.

**Parameters**:

- `expression`: Math expression

**Returns**: HTML string

---

#### MathSupport.render_script

```python
render_script(self: Any)
```

Render KaTeX script tags.

**Returns**: HTML script tags

---

---

## render_block

```python
render_block(self: Any, expression: str)
```

Render block math expression.

**Parameters**:

- `expression`: Math expression

**Returns**: HTML string

---

## render_inline

```python
render_inline(self: Any, expression: str)
```

Render inline math expression.

**Parameters**:

- `expression`: Math expression

**Returns**: HTML string

---

## render_script

```python
render_script(self: Any)
```

Render KaTeX script tags.

**Returns**: HTML script tags

---
