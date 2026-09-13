# config API Reference

> **Source**: `src/thegent/tui/config.py`

Configuration system for TUI compositor.

Provides YAML/JSON configuration file support with validation.

---

## ConfigManager

Manages TUI configuration.

### Methods

#### ConfigManager.**init**

```python
__init__(self: Any, config_dir: Any)
```

---

#### ConfigManager.disable_plugin

```python
disable_plugin(self: Any, plugin: str)
```

Disable a plugin.

---

#### ConfigManager.enable_plugin

```python
enable_plugin(self: Any, plugin: str)
```

Enable a plugin.

---

#### ConfigManager.export

```python
export(self: Any, path: Path)
```

Export configuration to a file.

---

#### ConfigManager.get

```python
get(self: Any)
```

Get current configuration.

---

#### ConfigManager.get_custom_css

```python
get_custom_css(self: Any)
```

Get custom CSS.

---

#### ConfigManager.get_keybindings

```python
get_keybindings(self: Any)
```

Get custom keybindings.

---

#### ConfigManager.get_layout

```python
get_layout(self: Any)
```

Get current layout.

---

#### ConfigManager.get_plugins

```python
get_plugins(self: Any)
```

Get list of enabled plugins.

---

#### ConfigManager.get_shell

```python
get_shell(self: Any)
```

Get shell command.

---

#### ConfigManager.get_theme

```python
get_theme(self: Any)
```

Get current theme.

---

#### ConfigManager.import_config

```python
import_config(cls: Any, path: Path, config_dir: Any)
```

Import configuration from a file.

---

#### ConfigManager.remove_keybinding

```python
remove_keybinding(self: Any, key: str)
```

Remove a keybinding.

---

#### ConfigManager.reset

```python
reset(self: Any)
```

Reset to default configuration.

---

#### ConfigManager.set

```python
set(self: Any, config: TUIConfig)
```

Set configuration.

---

#### ConfigManager.set_custom_css

```python
set_custom_css(self: Any, css: str)
```

Set custom CSS.

---

#### ConfigManager.set_keybinding

```python
set_keybinding(self: Any, key: str, action: str)
```

Set a keybinding.

---

#### ConfigManager.set_layout

```python
set_layout(self: Any, layout: str)
```

Set layout.

---

#### ConfigManager.set_shell

```python
set_shell(self: Any, shell: str)
```

Set shell command.

---

#### ConfigManager.set_theme

```python
set_theme(self: Any, theme: str)
```

Set theme.

---

#### ConfigManager.update

```python
update(self: Any)
```

Update specific configuration values.

---

---

## KeyBinding

Single key binding.

### Methods

#### KeyBinding.to_dict

```python
to_dict(self: Any)
```

---

---

## TUIConfig

Main TUI compositor configuration.

### Methods

#### TUIConfig.from_dict

```python
from_dict(cls: Any, data: dict[(str, Any)])
```

---

#### TUIConfig.to_dict

```python
to_dict(self: Any)
```

---

---

## disable_plugin

```python
disable_plugin(self: Any, plugin: str)
```

Disable a plugin.

---

## enable_plugin

```python
enable_plugin(self: Any, plugin: str)
```

Enable a plugin.

---

## export

```python
export(self: Any, path: Path)
```

Export configuration to a file.

---

## from_dict

```python
from_dict(cls: Any, data: dict[(str, Any)]) -> TUIConfig
```

---

## get

```python
get(self: Any)
```

Get current configuration.

---

## get_config

```python
get_config(config_dir: Any)
```

Get the configuration manager.

---

## get_custom_css

```python
get_custom_css(self: Any)
```

Get custom CSS.

---

## get_keybindings

```python
get_keybindings(self: Any)
```

Get custom keybindings.

---

## get_layout

```python
get_layout(self: Any)
```

Get current layout.

---

## get_plugins

```python
get_plugins(self: Any)
```

Get list of enabled plugins.

---

## get_shell

```python
get_shell(self: Any)
```

Get shell command.

---

## get_theme

```python
get_theme(self: Any)
```

Get current theme.

---

## import_config

```python
import_config(cls: Any, path: Path, config_dir: Any)
```

Import configuration from a file.

---

## remove_keybinding

```python
remove_keybinding(self: Any, key: str)
```

Remove a keybinding.

---

## reset

```python
reset(self: Any)
```

Reset to default configuration.

---

## set

```python
set(self: Any, config: TUIConfig)
```

Set configuration.

---

## set_custom_css

```python
set_custom_css(self: Any, css: str)
```

Set custom CSS.

---

## set_keybinding

```python
set_keybinding(self: Any, key: str, action: str)
```

Set a keybinding.

---

## set_layout

```python
set_layout(self: Any, layout: str)
```

Set layout.

---

## set_shell

```python
set_shell(self: Any, shell: str)
```

Set shell command.

---

## set_theme

```python
set_theme(self: Any, theme: str)
```

Set theme.

---

## to_dict

```python
to_dict(self: Any) -> dict[(str, str)]
```

---

## update

```python
update(self: Any)
```

Update specific configuration values.

---
