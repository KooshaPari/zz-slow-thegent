# desktop_automation API Reference

> **Source**: `src/thegent/cross_platform/desktop_automation.py`

Desktop automation providers (macOS/Windows/Linux).

---

## DesktopAutomationProvider

Cross-platform desktop automation.

### Methods

#### DesktopAutomationProvider.**init**

```python
__init__(self: Any)
```

Initialize desktop automation.

---

#### DesktopAutomationProvider.click

```python
click(self: Any, x: int, y: int)
```

Click at coordinates.

**Parameters**:

- `x`: X coordinate
- `y`: Y coordinate

**Returns**: True if successful

---

#### DesktopAutomationProvider.get_screen_size

```python
get_screen_size(self: Any)
```

Get screen size.

**Returns**: (width, height) tuple

---

#### DesktopAutomationProvider.type_text

```python
type_text(self: Any, text: str)
```

Type text.

**Parameters**:

- `text`: Text to type

**Returns**: True if successful

---

---

## click

```python
click(self: Any, x: int, y: int)
```

Click at coordinates.

**Parameters**:

- `x`: X coordinate
- `y`: Y coordinate

**Returns**: True if successful

---

## get_screen_size

```python
get_screen_size(self: Any)
```

Get screen size.

**Returns**: (width, height) tuple

---

## type_text

```python
type_text(self: Any, text: str)
```

Type text.

**Parameters**:

- `text`: Text to type

**Returns**: True if successful

---
