# ghostty API Reference

> **Source**: `src/thegent/integrations/ghostty.py`

Ghostty terminal emulator integration for thegent.

Provides detection, configuration management, and feature access for the
Ghostty terminal emulator (https://ghostty.org).

FR traceability: FR-IDE-002 (Ghostty terminal integration)

---

## GhosttyConfig

Configuration record for a Ghostty terminal installation.

---

## GhosttyError

Raised when a Ghostty operation fails in an unrecoverable way.

**Inherits from**: `Exception`

---

## GhosttyIntegration

Detect Ghostty and provide access to its terminal features.

Usage::

    integration = GhosttyIntegration()
    if integration.is_available():
        cfg = integration.get_config()
        integration.set_theme("light")
        integration.send_notification("thegent", "Task complete")

### Methods

#### GhosttyIntegration.**init**

```python
__init__(self: Any, config_path: Any)
```

Initialise the integration.

**Parameters**:

- `config_path`: Override the default Ghostty config path
  (~/.config/ghostty/config). Useful for tests.

---

#### GhosttyIntegration.get_config

```python
get_config(self: Any)
```

Read the Ghostty configuration file and return a GhosttyConfig.

If the config file does not exist or cannot be parsed the returned
GhosttyConfig contains default values.

**Returns**: GhosttyConfig populated from `~/.config/ghostty/config`
(or the custom path provided at construction time).

---

#### GhosttyIntegration.get_env_info

```python
get_env_info(self: Any)
```

Return a dict of terminal-related environment variables.

The following variables are included (value is empty string when not
set in the current environment):

- `TERM_PROGRAM`
- `TERM`
- `COLORTERM`
- `TERM_PROGRAM_VERSION`
- `GHOSTTY_RESOURCES_DIR`
- `GHOSTTY_BIN_DIR`

**Returns**: Mapping of env-var name to its current value (or empty string).

---

#### GhosttyIntegration.is_available

```python
is_available(self: Any)
```

Return True when the current process is running inside Ghostty.

Detection is based on the `TERM_PROGRAM` environment variable being
set to `"ghostty"`.

**Returns**: True if `TERM_PROGRAM == "ghostty"`; False otherwise.

---

#### GhosttyIntegration.open_tab

```python
open_tab(self: Any, command: Any)
```

Open a new tab in the current Ghostty window.

Uses the `ghostty +open-tab` CLI command. The Ghostty binary must
be on `PATH`.

**Parameters**:

- `command`: Optional shell command to run in the new tab.
  If None, the default shell is used.

**Returns**: True if the command exited successfully; False otherwise.

---

#### GhosttyIntegration.send_notification

```python
send_notification(self: Any, title: str, body: str)
```

Send a macOS desktop notification via osascript.

Uses `osascript` (AppleScript) which is available on macOS.
Returns False on non-macOS platforms or when osascript is unavailable.

**Parameters**:

- `title`: Notification title.
- `body`: Notification body text.

**Returns**: True if the notification was delivered; False otherwise.

---

#### GhosttyIntegration.set_theme

```python
set_theme(self: Any, theme: str)
```

Write the theme setting to the Ghostty config file.

**Parameters**:

- `theme`: Theme name to set (e.g. `"dark"`, `"light"`,
  `"Dracula"`).

**Returns**: True on success; False if the write failed.

---

---

## get_config

```python
get_config(self: Any)
```

Read the Ghostty configuration file and return a GhosttyConfig.

If the config file does not exist or cannot be parsed the returned
GhosttyConfig contains default values.

**Returns**: GhosttyConfig populated from `~/.config/ghostty/config`
(or the custom path provided at construction time).

---

## get_env_info

```python
get_env_info(self: Any)
```

Return a dict of terminal-related environment variables.

The following variables are included (value is empty string when not
set in the current environment):

- `TERM_PROGRAM`
- `TERM`
- `COLORTERM`
- `TERM_PROGRAM_VERSION`
- `GHOSTTY_RESOURCES_DIR`
- `GHOSTTY_BIN_DIR`

**Returns**: Mapping of env-var name to its current value (or empty string).

---

## is_available

```python
is_available(self: Any)
```

Return True when the current process is running inside Ghostty.

Detection is based on the `TERM_PROGRAM` environment variable being
set to `"ghostty"`.

**Returns**: True if `TERM_PROGRAM == "ghostty"`; False otherwise.

---

## open_tab

```python
open_tab(self: Any, command: Any)
```

Open a new tab in the current Ghostty window.

Uses the `ghostty +open-tab` CLI command. The Ghostty binary must
be on `PATH`.

**Parameters**:

- `command`: Optional shell command to run in the new tab.
  If None, the default shell is used.

**Returns**: True if the command exited successfully; False otherwise.

---

## send_notification

```python
send_notification(self: Any, title: str, body: str)
```

Send a macOS desktop notification via osascript.

Uses `osascript` (AppleScript) which is available on macOS.
Returns False on non-macOS platforms or when osascript is unavailable.

**Parameters**:

- `title`: Notification title.
- `body`: Notification body text.

**Returns**: True if the notification was delivered; False otherwise.

---

## set_theme

```python
set_theme(self: Any, theme: str)
```

Write the theme setting to the Ghostty config file.

**Parameters**:

- `theme`: Theme name to set (e.g. `"dark"`, `"light"`,
  `"Dracula"`).

**Returns**: True on success; False if the write failed.

---
