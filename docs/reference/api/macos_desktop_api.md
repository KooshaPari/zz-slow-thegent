# macos_desktop API Reference

> **Source**: `src/thegent/automation/macos_desktop.py`

macOS Desktop Automation provider wrapping AppleScript and JXA.

---

## AutomationError

Raised when a desktop automation operation fails unexpectedly.

**Inherits from**: `Exception`

---

## AutomationResult

Result from a desktop automation operation.

---

## MacOSDesktopAutomation

macOS desktop automation via AppleScript (osascript) and JXA.

Falls back gracefully on non-macOS platforms: every method returns an
`AutomationResult(success=False, ...)` rather than raising.

### Methods

#### MacOSDesktopAutomation.click_menu_item

```python
click_menu_item(self: Any, app: str, menu: str, item: str)
```

Click a menu item inside an application's menu bar.

**Parameters**:

- `app`: Application name, e.g. "Safari".
- `menu`: Top-level menu name, e.g. "File".
- `item`: Menu item name, e.g. "New Window".

**Returns**: AutomationResult indicating success or failure.

---

#### MacOSDesktopAutomation.get_frontmost_app

```python
get_frontmost_app(self: Any)
```

Return the name of the currently frontmost application.

**Returns**: Application name string, or None if the query fails.

---

#### MacOSDesktopAutomation.is_available

```python
is_available(self: Any)
```

Return True when running on macOS and _osascript_ is on PATH.

---

#### MacOSDesktopAutomation.open_application

```python
open_application(self: Any, name: str)
```

Activate (open/bring to front) an application by name.

**Parameters**:

- `name`: Application name as it appears in /Applications, e.g. "Safari".

**Returns**: AutomationResult indicating success or failure.

---

#### MacOSDesktopAutomation.run_applescript

```python
run_applescript(self: Any, script: str, timeout_s: float)
```

Execute an AppleScript snippet via _osascript_.

**Parameters**:

- `script`: AppleScript source code to execute.
- `timeout_s`: Maximum wall-clock seconds to allow (default 10).

**Returns**: AutomationResult with success flag, stdout, and optional error.

---

#### MacOSDesktopAutomation.run_jxa

```python
run_jxa(self: Any, script: str, timeout_s: float)
```

Execute a JavaScript for Automation (JXA) snippet via _osascript_.

**Parameters**:

- `script`: JXA source code to execute.
- `timeout_s`: Maximum wall-clock seconds to allow (default 10).

**Returns**: AutomationResult with success flag, stdout, and optional error.

---

---

## click_menu_item

```python
click_menu_item(self: Any, app: str, menu: str, item: str)
```

Click a menu item inside an application's menu bar.

**Parameters**:

- `app`: Application name, e.g. "Safari".
- `menu`: Top-level menu name, e.g. "File".
- `item`: Menu item name, e.g. "New Window".

**Returns**: AutomationResult indicating success or failure.

---

## get_frontmost_app

```python
get_frontmost_app(self: Any)
```

Return the name of the currently frontmost application.

**Returns**: Application name string, or None if the query fails.

---

## is_available

```python
is_available(self: Any)
```

Return True when running on macOS and _osascript_ is on PATH.

---

## open_application

```python
open_application(self: Any, name: str)
```

Activate (open/bring to front) an application by name.

**Parameters**:

- `name`: Application name as it appears in /Applications, e.g. "Safari".

**Returns**: AutomationResult indicating success or failure.

---

## run_applescript

```python
run_applescript(self: Any, script: str, timeout_s: float)
```

Execute an AppleScript snippet via _osascript_.

**Parameters**:

- `script`: AppleScript source code to execute.
- `timeout_s`: Maximum wall-clock seconds to allow (default 10).

**Returns**: AutomationResult with success flag, stdout, and optional error.

---

## run_jxa

```python
run_jxa(self: Any, script: str, timeout_s: float)
```

Execute a JavaScript for Automation (JXA) snippet via _osascript_.

**Parameters**:

- `script`: JXA source code to execute.
- `timeout_s`: Maximum wall-clock seconds to allow (default 10).

**Returns**: AutomationResult with success flag, stdout, and optional error.

---
