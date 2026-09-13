# themes API Reference

> **Source**: `src/thegent/tui/themes.py`

Theme system for TUI compositor.

Provides theme management with built-in themes and custom theme support.

---

## ThemeColors

Color palette for a theme.

### Methods

#### ThemeColors.from_dict

```python
from_dict(cls: Any, data: dict[(str, str)])
```

---

#### ThemeColors.to_dict

```python
to_dict(self: Any)
```

---

---

## ThemeDefinition

Complete theme definition.

### Methods

#### ThemeDefinition.from_dict

```python
from_dict(cls: Any, data: dict[(str, Any)])
```

---

#### ThemeDefinition.to_dict

```python
to_dict(self: Any)
```

---

#### ThemeDefinition.to_textual_theme

```python
to_textual_theme(self: Any)
```

Convert to Textual Theme.

---

---

## ThemeManager

Manages themes for the TUI compositor.

### Methods

#### ThemeManager.**init**

```python
__init__(self: Any, storage_dir: Any)
```

---

#### ThemeManager.add_theme

```python
add_theme(self: Any, theme: ThemeDefinition)
```

Add a custom theme.

---

#### ThemeManager.apply_to_app

```python
apply_to_app(self: Any, app: Any)
```

Apply current theme to a Textual app.

---

#### ThemeManager.create_theme

```python
create_theme(self: Any, name: str, colors: ThemeColors, dark: bool, author: str, description: str)
```

Create and save a new theme.

---

#### ThemeManager.delete_theme

```python
delete_theme(self: Any, name: str)
```

Delete a custom theme.

---

#### ThemeManager.duplicate_theme

```python
duplicate_theme(self: Any, source: str, new_name: str)
```

Duplicate an existing theme.

---

#### ThemeManager.export_theme

```python
export_theme(self: Any, name: str, path: Path)
```

Export a theme to a JSON file.

---

#### ThemeManager.get_current

```python
get_current(self: Any)
```

Get the current theme.

---

#### ThemeManager.get_styles

```python
get_styles(self: Any)
```

Get CSS styles for the current theme.

---

#### ThemeManager.get_theme

```python
get_theme(self: Any, name: str)
```

Get a theme by name.

---

#### ThemeManager.import_theme

```python
import_theme(self: Any, path: Path)
```

Import a theme from a JSON file.

---

#### ThemeManager.list_themes

```python
list_themes(self: Any)
```

List all available theme names.

---

#### ThemeManager.set_theme

```python
set_theme(self: Any, name: str)
```

Set the current theme.

---

---

## add_theme

```python
add_theme(self: Any, theme: ThemeDefinition)
```

Add a custom theme.

---

## apply_to_app

```python
apply_to_app(self: Any, app: Any)
```

Apply current theme to a Textual app.

---

## create_theme

```python
create_theme(self: Any, name: str, colors: ThemeColors, dark: bool, author: str, description: str)
```

Create and save a new theme.

---

## delete_theme

```python
delete_theme(self: Any, name: str)
```

Delete a custom theme.

---

## duplicate_theme

```python
duplicate_theme(self: Any, source: str, new_name: str)
```

Duplicate an existing theme.

---

## export_theme

```python
export_theme(self: Any, name: str, path: Path)
```

Export a theme to a JSON file.

---

## from_dict

```python
from_dict(cls: Any, data: dict[(str, Any)]) -> ThemeDefinition
```

---

## get_builtin_themes

Get list of built-in themes.

---

## get_current

```python
get_current(self: Any)
```

Get the current theme.

---

## get_styles

```python
get_styles(self: Any)
```

Get CSS styles for the current theme.

---

## get_theme

```python
get_theme(self: Any, name: str)
```

Get a theme by name.

---

## import_theme

```python
import_theme(self: Any, path: Path)
```

Import a theme from a JSON file.

---

## list_themes

```python
list_themes(self: Any)
```

List all available theme names.

---

## set_theme

```python
set_theme(self: Any, name: str)
```

Set the current theme.

---

## to_dict

```python
to_dict(self: Any) -> dict[(str, Any)]
```

---

## to_textual_theme

```python
to_textual_theme(self: Any)
```

Convert to Textual Theme.

---
