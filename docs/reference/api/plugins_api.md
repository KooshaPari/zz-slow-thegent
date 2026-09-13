# plugins API Reference

> **Source**: `src/thegent/tui/plugins.py`

Plugin system for TUI compositor.

Provides dynamic loading of external widgets and extensions.

---

## BuiltinPlugins

Registry of built-in plugins.

### Methods

#### BuiltinPlugins.create_dialog_plugin

```python
create_dialog_plugin(info: PluginInfo)
```

Create the dialog plugin.

---

#### BuiltinPlugins.create_status_plugin

```python
create_status_plugin(info: PluginInfo)
```

Create the status bar plugin.

---

#### BuiltinPlugins.create_terminal_plugin

```python
create_terminal_plugin(info: PluginInfo)
```

Create the terminal plugin.

---

#### BuiltinPlugins.get_plugin

```python
get_plugin(cls: Any, name: str, info: Any)
```

Get a built-in plugin by name.

---

---

## DialogPlugin

**Inherits from**: `WidgetPlugin`

**Method Resolution Order**: `DialogPlugin -> WidgetPlugin -> Plugin`

### Methods

#### DialogPlugin.**init**

```python
__init__(self: Any, info: PluginInfo)
```

---

---

## ExtensionPlugin

Plugin that extends compositor functionality.

**Inherits from**: `Plugin`

**Method Resolution Order**: `ExtensionPlugin -> Plugin`

### Methods

#### ExtensionPlugin.**init**

```python
__init__(self: Any, info: PluginInfo)
```

---

#### ExtensionPlugin.call_hooks

```python
call_hooks(self: Any, hook_name: str)
```

Call all hooks for an event.

---

#### ExtensionPlugin.register_hook

```python
register_hook(self: Any, hook_name: str, callback: Callable)
```

Register a hook callback.

---

---

## Plugin

Base class for TUI plugins.

### Methods

#### Plugin.**init**

```python
__init__(self: Any, info: PluginInfo)
```

---

#### Plugin.enabled

```python
enabled(self: Any, value: bool)
```

---

#### Plugin.get_compose

```python
get_compose(self: Any)
```

Get widgets to compose into the app.

---

#### Plugin.get_widgets

```python
get_widgets(self: Any)
```

Get widgets provided by this plugin.

---

#### Plugin.load

```python
load(self: Any)
```

Load the plugin.

---

#### Plugin.loaded

```python
loaded(self: Any)
```

---

#### Plugin.on_mount

```python
on_mount(self: Any)
```

Called when plugin is mounted.

---

#### Plugin.on_unmount

```python
on_unmount(self: Any)
```

Called when plugin is unmounted.

---

#### Plugin.unload

```python
unload(self: Any)
```

Unload the plugin.

---

---

## PluginInfo

Metadata about a plugin.

### Methods

#### PluginInfo.to_dict

```python
to_dict(self: Any)
```

---

---

## PluginLoader

Loads and manages plugins.

### Methods

#### PluginLoader.**init**

```python
__init__(self: Any, plugin_dir: Any)
```

---

#### PluginLoader.discover_plugins

```python
discover_plugins(self: Any)
```

Discover available plugins.

---

#### PluginLoader.get_plugin

```python
get_plugin(self: Any, name: str)
```

Get a loaded plugin.

---

#### PluginLoader.get_plugin_info

```python
get_plugin_info(self: Any, name: str)
```

Get info about a plugin.

---

#### PluginLoader.list_plugins

```python
list_plugins(self: Any)
```

List loaded plugin names.

---

#### PluginLoader.load_plugin

```python
load_plugin(self: Any, name: str)
```

Load a plugin by name.

---

#### PluginLoader.on_plugin_load

```python
on_plugin_load(self: Any, callback: Callable[(Any, None)])
```

Register a callback for plugin loading.

---

#### PluginLoader.reload_all

```python
reload_all(self: Any)
```

Reload all plugins.

---

#### PluginLoader.unload_plugin

```python
unload_plugin(self: Any, name: str)
```

Unload a plugin.

---

---

## StatusPlugin

**Inherits from**: `WidgetPlugin`

**Method Resolution Order**: `StatusPlugin -> WidgetPlugin -> Plugin`

### Methods

#### StatusPlugin.**init**

```python
__init__(self: Any, info: PluginInfo)
```

---

---

## TerminalPlugin

**Inherits from**: `WidgetPlugin`

**Method Resolution Order**: `TerminalPlugin -> WidgetPlugin -> Plugin`

### Methods

#### TerminalPlugin.**init**

```python
__init__(self: Any, info: PluginInfo)
```

---

---

## WidgetPlugin

Plugin that provides custom widgets.

**Inherits from**: `Plugin`

**Method Resolution Order**: `WidgetPlugin -> Plugin`

### Methods

#### WidgetPlugin.**init**

```python
__init__(self: Any, info: PluginInfo)
```

---

#### WidgetPlugin.get_widgets

```python
get_widgets(self: Any)
```

---

#### WidgetPlugin.register_widget

```python
register_widget(self: Any, widget_class: type[Widget])
```

Register a widget class.

---

---

## call_hooks

```python
call_hooks(self: Any, hook_name: str)
```

Call all hooks for an event.

---

## create_dialog_plugin

```python
create_dialog_plugin(info: PluginInfo)
```

Create the dialog plugin.

---

## create_status_plugin

```python
create_status_plugin(info: PluginInfo)
```

Create the status bar plugin.

---

## create_terminal_plugin

```python
create_terminal_plugin(info: PluginInfo)
```

Create the terminal plugin.

---

## discover_plugins

```python
discover_plugins(self: Any)
```

Discover available plugins.

---

## enabled

```python
enabled(self: Any, value: bool) -> None
```

---

## get_compose

```python
get_compose(self: Any)
```

Get widgets to compose into the app.

---

## get_plugin

```python
get_plugin(cls: Any, name: str, info: Any)
```

Get a built-in plugin by name.

---

## get_plugin_info

```python
get_plugin_info(self: Any, name: str)
```

Get info about a plugin.

---

## get_widgets

```python
get_widgets(self: Any) -> list[type[Widget]]
```

---

## list_plugins

```python
list_plugins(self: Any)
```

List loaded plugin names.

---

## load

```python
load(self: Any)
```

Load the plugin.

---

## load_plugin

```python
load_plugin(self: Any, name: str)
```

Load a plugin by name.

---

## loaded

```python
loaded(self: Any) -> bool
```

---

## on_mount

```python
on_mount(self: Any)
```

Called when plugin is mounted.

---

## on_plugin_load

```python
on_plugin_load(self: Any, callback: Callable[(Any, None)])
```

Register a callback for plugin loading.

---

## on_unmount

```python
on_unmount(self: Any)
```

Called when plugin is unmounted.

---

## register_hook

```python
register_hook(self: Any, hook_name: str, callback: Callable)
```

Register a hook callback.

---

## register_widget

```python
register_widget(self: Any, widget_class: type[Widget])
```

Register a widget class.

---

## reload_all

```python
reload_all(self: Any)
```

Reload all plugins.

---

## to_dict

```python
to_dict(self: Any) -> dict[(str, Any)]
```

---

## unload

```python
unload(self: Any)
```

Unload the plugin.

---

## unload_plugin

```python
unload_plugin(self: Any, name: str)
```

Unload a plugin.

---
