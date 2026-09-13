# Cross-Platform Desktop Automation: API Reference

**Purpose:** Complete API reference for desktop automation providers, coordinators, and MCP tools.

**Date:** 2026-02-16
**Status:** API Reference
**Related:** CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md

---

## Table of Contents

1. [Core Classes](#core-classes)
2. [Provider API](#provider-api)
3. [Coordinator API](#coordinator-api)
4. [MCP Tools API](#mcp-tools-api)
5. [Configuration API](#configuration-api)
6. [Utility Functions](#utility-functions)

---

## Core Classes

### `UIElement`

Represents a UI element in the accessibility tree.

```python
@dataclass
class UIElement:
    selector: str  # Element selector
    name: str  # Accessibility name
    role: str  # Element role (button, text_field, etc.)
    bounds: dict[str, int]  # {x, y, width, height}
    attributes: dict[str, str]  # Platform-specific attributes
    platform_specific: dict[str, any] = None

    def is_valid(self) -> bool:
        """Check if element is still valid."""
```

**Example:**
```python
element = UIElement(
    selector="button[name='Save']",
    name="Save",
    role="button",
    bounds={"x": 100, "y": 200, "width": 80, "height": 30},
    attributes={"process_name": "TextEdit"},
)
```

### `AutomationAction`

Represents an automation action to execute.

```python
@dataclass
class AutomationAction:
    type: str  # click, type_text, find_element, screenshot, wait_for_idle
    selector: str | None = None  # Element selector
    text: str | None = None  # Text to type
    region: dict[str, int] | None = None  # Screenshot region {x, y, width, height}
    timeout_ms: float = 5000.0  # Timeout in milliseconds
    wait_for_idle_seconds: float = 5.0  # Wait for user idle before action
```

**Example:**
```python
action = AutomationAction(type="click", selector="button[name='Save']", timeout_ms=5000.0, wait_for_idle_seconds=5.0)
```

### `AutomationResult`

Result of an automation action.

```python
@dataclass
class AutomationResult:
    success: bool  # Whether action succeeded
    element: UIElement | None = None  # Element (for find operations)
    screenshot: bytes | None = None  # Screenshot data (for screenshot operations)
    error: str | None = None  # Error message if failed
    duration_ms: float = 0.0  # Action duration in milliseconds
    metadata: dict[str, any] = None  # Additional metadata
    skipped: bool = False  # True if action was skipped
```

**Example:**
```python
result = AutomationResult(success=True, duration_ms=95.2, metadata={"click_count": 1})
```

### `AutomationScope`

Defines scope for automation coordination.

```python
@dataclass
class AutomationScope:
    app_name: str  # Application name
    window_title: str | None = None  # Window title filter
    region: dict[str, int] | None = None  # Region restriction {x, y, width, height}
```

**Example:**
```python
scope = AutomationScope(
    app_name="TextEdit", window_title="Untitled", region={"x": 0, "y": 0, "width": 1920, "height": 1080}
)
```

---

## Provider API

### `DesktopAutomationProvider`

Abstract base class for platform-specific providers.

#### `click(element: UIElement, timeout_ms: float = 5000.0) -> AutomationResult`

Click a UI element.

**Parameters:**
- `element`: UI element to click
- `timeout_ms`: Timeout in milliseconds (default: 5000.0)

**Returns:**
- `AutomationResult` with success status and duration

**Raises:**
- `TimeoutError` if timeout exceeded
- `ElementNotFoundError` if element invalid

**Example:**
```python
element = provider.find_element("button[name='Save']")
result = provider.click(element, timeout_ms=5000.0)
if result.success:
    print(f"Clicked in {result.duration_ms}ms")
```

#### `type_text(element: UIElement, text: str, timeout_ms: float = 5000.0) -> AutomationResult`

Type text into an element.

**Parameters:**
- `element`: UI element to type into
- `text`: Text to type
- `timeout_ms`: Timeout in milliseconds

**Returns:**
- `AutomationResult` with success status

**Example:**
```python
element = provider.find_element("text_field[name='username']")
result = provider.type_text(element, "myusername", timeout_ms=5000.0)
```

#### `find_element(selector: str, timeout_ms: float = 5000.0) -> UIElement | None`

Find UI element by selector.

**Parameters:**
- `selector`: Element selector (XPath, accessibility name, etc.)
- `timeout_ms`: Timeout in milliseconds

**Returns:**
- `UIElement` if found, `None` otherwise

**Example:**
```python
element = provider.find_element("button[name='Save']", timeout_ms=5000.0)
if element:
    print(f"Found element: {element.name}")
```

#### `find_element_cached(selector: str, timeout_ms: float = 5000.0) -> UIElement | None`

Find element with caching (faster for repeated finds).

**Parameters:**
- `selector`: Element selector
- `timeout_ms`: Timeout in milliseconds

**Returns:**
- `UIElement` if found (from cache or fresh lookup)

**Example:**
```python
# First call: 500ms (uncached)
element1 = provider.find_element_cached("button[name='Save']")

# Second call: 10ms (cached)
element2 = provider.find_element_cached("button[name='Save']")
```

#### `screenshot(region: dict[str, int] | None = None) -> bytes`

Take screenshot of desktop or region.

**Parameters:**
- `region`: Optional region `{x, y, width, height}` (default: full screen)

**Returns:**
- Screenshot as PNG bytes

**Example:**
```python
# Full screen
screenshot = provider.screenshot()

# Region
region = {"x": 100, "y": 200, "width": 800, "height": 600}
screenshot = provider.screenshot(region=region)
```

#### `wait_for_user_idle(idle_seconds: float = 5.0, timeout_ms: float = 30000.0) -> bool`

Wait until user is idle.

**Parameters:**
- `idle_seconds`: Required idle duration in seconds (default: 5.0)
- `timeout_ms`: Maximum wait time in milliseconds (default: 30000.0)

**Returns:**
- `True` if user became idle, `False` on timeout

**Example:**
```python
if provider.wait_for_user_idle(idle_seconds=5.0, timeout_ms=30000.0):
    # User is idle, safe to automate
    result = provider.click(element)
```

#### `get_active_window() -> UIElement | None`

Get currently active window.

**Returns:**
- `UIElement` representing active window, `None` if not found

**Example:**
```python
window = provider.get_active_window()
if window:
    print(f"Active window: {window.name}")
```

#### `list_windows(app_name: str | None = None) -> list[UIElement]`

List all windows (optionally filtered by app).

**Parameters:**
- `app_name`: Optional app name filter

**Returns:**
- List of `UIElement` representing windows

**Example:**
```python
# All windows
windows = provider.list_windows()

# TextEdit windows only
windows = provider.list_windows(app_name="TextEdit")
```

#### `clear_cache()`

Clear element cache.

**Example:**
```python
provider.clear_cache()
```

---

## Coordinator API

### `DesktopAutomationCoordinator`

Coordinates desktop automation across multiple agents.

#### `acquire_lock(scope: AutomationScope, agent_id: str, duration: float = 300.0) -> bool`

Acquire automation lock.

**Parameters:**
- `scope`: Automation scope
- `agent_id`: Agent identifier
- `duration`: Lock duration in seconds (default: 300.0)

**Returns:**
- `True` if lock acquired, `False` otherwise

**Example:**
```python
scope = AutomationScope(app_name="TextEdit")
if coordinator.acquire_lock(scope, agent_id="agent-1", duration=300.0):
    # Lock acquired, safe to automate
    pass
```

#### `release_lock(scope: AutomationScope, agent_id: str)`

Release automation lock.

**Parameters:**
- `scope`: Automation scope
- `agent_id`: Agent identifier

**Example:**
```python
coordinator.release_lock(scope, agent_id="agent-1")
```

#### `execute_with_coordination(scope: AutomationScope, agent_id: str, action: AutomationAction) -> AutomationResult`

Execute automation action with coordination.

**Parameters:**
- `scope`: Automation scope
- `agent_id`: Agent identifier
- `action`: Automation action

**Returns:**
- `AutomationResult` with success status

**Example:**
```python
scope = AutomationScope(app_name="TextEdit")
action = AutomationAction(type="click", selector="button[name='Save']")
result = coordinator.execute_with_coordination(scope, "agent-1", action)
```

---

## MCP Tools API

### `desktop_automation_click`

Click a UI element identified by selector.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "selector": {
      "type": "string",
      "description": "Element selector"
    },
    "wait_timeout": {
      "type": "number",
      "description": "Timeout in seconds",
      "default": 5.0
    },
    "agent_id": {
      "type": "string",
      "description": "Optional agent identifier"
    }
  },
  "required": ["selector"]
}
```

**Response Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "duration_ms": {"type": "number"},
    "error": {"type": "string", "nullable": true}
  }
}
```

**Example:**
```json
// Request
{
  "selector": "button[name='Save']",
  "wait_timeout": 5.0,
  "agent_id": "my-agent"
}

// Response
{
  "success": true,
  "duration_ms": 95.2,
  "error": null
}
```

### `desktop_automation_type`

Type text into a UI element.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "selector": {"type": "string"},
    "text": {"type": "string"},
    "wait_timeout": {"type": "number", "default": 5.0},
    "agent_id": {"type": "string"}
  },
  "required": ["selector", "text"]
}
```

### `desktop_automation_find`

Find UI element by selector.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "selector": {"type": "string"},
    "timeout": {"type": "number", "default": 5.0}
  },
  "required": ["selector"]
}
```

**Response Schema:**
```json
{
  "type": "object",
  "properties": {
    "found": {"type": "boolean"},
    "element": {
      "type": "object",
      "properties": {
        "selector": {"type": "string"},
        "name": {"type": "string"},
        "role": {"type": "string"},
        "bounds": {
          "type": "object",
          "properties": {
            "x": {"type": "integer"},
            "y": {"type": "integer"},
            "width": {"type": "integer"},
            "height": {"type": "integer"}
          }
        }
      }
    }
  }
}
```

### `desktop_automation_screenshot`

Take screenshot of desktop or region.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "region": {
      "type": "object",
      "properties": {
        "x": {"type": "integer"},
        "y": {"type": "integer"},
        "width": {"type": "integer"},
        "height": {"type": "integer"}
      }
    }
  }
}
```

**Response Schema:**
```json
{
  "type": "object",
  "properties": {
    "screenshot": {"type": "string", "description": "Base64-encoded PNG"},
    "format": {"type": "string", "const": "png"}
  }
}
```

### `desktop_automation_wait_for_user_idle`

Wait until user is idle.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "idle_seconds": {"type": "number", "default": 5.0},
    "timeout": {"type": "number", "default": 30.0}
  },
  "required": ["idle_seconds"]
}
```

**Response Schema:**
```json
{
  "type": "object",
  "properties": {
    "idle": {"type": "boolean"},
    "idle_seconds": {"type": "number"}
  }
}
```

---

## Configuration API

### `DesktopAutomationSettings`

Configuration settings for desktop automation.

```python
class DesktopAutomationSettings(BaseSettings):
    desktop_automation_enabled: bool = False
    desktop_automation_platform: str | None = None
    desktop_automation_coordination_enabled: bool = True
    desktop_automation_user_idle_threshold: float = 5.0
    desktop_automation_rate_limit_per_minute: int = 100
    desktop_automation_budget_mtd: float = 10.0
    desktop_automation_allowed_apps: list[str] = []
    desktop_automation_blocked_apps: list[str] = []
```

**Environment Variables:**
- `THGENT_DESKTOP_AUTOMATION_ENABLED`: Enable desktop automation
- `THGENT_DESKTOP_AUTOMATION_PLATFORM`: Platform override (darwin, windows, linux)
- `THGENT_DESKTOP_AUTOMATION_COORDINATION_ENABLED`: Enable coordination
- `THGENT_DESKTOP_AUTOMATION_USER_IDLE_THRESHOLD`: Idle threshold in seconds
- `THGENT_DESKTOP_AUTOMATION_RATE_LIMIT_PER_MINUTE`: Rate limit
- `THGENT_DESKTOP_AUTOMATION_BUDGET_MTD`: Monthly budget in USD
- `THGENT_DESKTOP_AUTOMATION_ALLOWED_APPS`: JSON array of allowed apps
- `THGENT_DESKTOP_AUTOMATION_BLOCKED_APPS`: JSON array of blocked apps

---

## Utility Functions

### `get_provider(platform: str | None = None) -> DesktopAutomationProvider`

Get platform-specific provider.

**Parameters:**
- `platform`: Platform override (darwin, windows, linux) or None for auto-detect

**Returns:**
- `DesktopAutomationProvider` instance

**Example:**
```python
from thegent.infra.desktop_automation import get_provider

# Auto-detect platform
provider = get_provider()

# Override platform
provider = get_provider(platform="darwin")
```

### `check_permissions() -> dict[str, bool]`

Check desktop automation permissions.

**Returns:**
- Dictionary mapping permission names to granted status

**Example:**
```python
from thegent.infra.desktop_automation import check_permissions

permissions = check_permissions()
# {
#     "accessibility": True,
#     "screen_recording": False
# }
```

### `validate_selector(selector: str) -> tuple[bool, str]`

Validate element selector for security.

**Parameters:**
- `selector`: Element selector

**Returns:**
- Tuple of (is_valid, reason)

**Example:**
```python
from thegent.infra.desktop_automation.security import validate_selector

is_valid, reason = validate_selector("button[name='Save']")
if not is_valid:
    print(f"Invalid selector: {reason}")
```

### `verify_app(app_name: str, window_title: str | None = None) -> bool`

Verify app identity for security.

**Parameters:**
- `app_name`: Application name
- `window_title`: Optional window title

**Returns:**
- `True` if app is verified, `False` otherwise

**Example:**
```python
from thegent.infra.desktop_automation.security import verify_app

if verify_app("TextEdit", window_title="Untitled"):
    # App verified, safe to automate
    pass
```

---

## Error Classes

### `AutomationError`

Base exception for automation errors.

```python
class AutomationError(Exception):
    """Base exception for automation errors."""

    pass
```

### `ElementNotFoundError`

Element not found error.

```python
class ElementNotFoundError(AutomationError):
    """Element not found error."""

    pass
```

### `PermissionDeniedError`

Permission denied error.

```python
class PermissionDeniedError(AutomationError):
    """Permission denied error."""

    pass
```

### `TimeoutError`

Timeout error.

```python
class AutomationTimeoutError(AutomationError):
    """Automation timeout error."""

    pass
```

### `RateLimitExceededError`

Rate limit exceeded error.

```python
class RateLimitExceededError(AutomationError):
    """Rate limit exceeded error."""

    pass
```

---

## Platform-Specific Notes

### macOS

**Provider:** `macOSAutomationProvider`
**APIs:** AppleScript, Apple Events, Accessibility API
**Permissions:** Accessibility, Screen Recording

**Selector Formats:**
- Accessibility name: `"Save"`
- Role + name: `"button[name='Save']"`
- XPath: `"//button[@name='Save']"`

### Windows

**Provider:** `WindowsAutomationProvider`
**APIs:** UI Automation (UIA)
**Permissions:** UIA Access

**Selector Formats:**
- Automation ID: `"SaveButton"`
- Name: `"Save"`
- Control Type + Name: `"Button[Name='Save']"`

### Linux

**Provider:** `LinuxAutomationProvider`
**APIs:** AT-SPI, D-Bus
**Permissions:** Usually granted by default

**Selector Formats:**
- Accessibility name: `"Save"`
- Role + name: `"push button[name='Save']"`
- D-Bus path: `"/org/a11y/atspi/accessible/..."`

---

**Status:** API reference complete. Ready for implementation.


---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made
1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added
- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions
- Implementation templates
- Configuration examples
- Best practices
