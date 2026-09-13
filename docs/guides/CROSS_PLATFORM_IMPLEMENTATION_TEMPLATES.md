# Cross-Platform Desktop Automation: Implementation Templates

**Purpose:** Code templates and scaffolding guides for implementing desktop automation providers and coordinators.

**Date:** 2026-02-16
**Status:** Implementation Guide
**Related:** CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md

---

## Template 1: Base Provider Implementation

### File: `src/thegent/infra/desktop_automation/base.py`

```python
"""Base classes for desktop automation providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import time
import logging

_log = logging.getLogger(__name__)


@dataclass
class UIElement:
    """Represents a UI element."""

    selector: str
    name: str
    role: str  # button, text_field, window, etc.
    bounds: dict[str, int]  # x, y, width, height
    attributes: dict[str, str]
    platform_specific: dict[str, any] = None

    def is_valid(self) -> bool:
        """Check if element is still valid."""
        # Platform-specific validation
        raise NotImplementedError


@dataclass
class AutomationAction:
    """Represents an automation action."""

    type: str  # click, type_text, find_element, screenshot, wait_for_idle
    selector: str | None = None
    text: str | None = None
    region: dict[str, int] | None = None
    timeout_ms: float = 5000.0
    wait_for_idle_seconds: float = 5.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "selector": self.selector,
            "text": self.text,
            "region": self.region,
            "timeout_ms": self.timeout_ms,
            "wait_for_idle_seconds": self.wait_for_idle_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AutomationAction":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class AutomationResult:
    """Result of an automation action."""

    success: bool
    element: UIElement | None = None
    screenshot: bytes | None = None
    error: str | None = None
    duration_ms: float = 0.0
    metadata: dict[str, any] = None
    skipped: bool = False  # True if action was skipped (e.g., already done)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "element": self.element.to_dict() if self.element else None,
            "screenshot": self.screenshot.hex() if self.screenshot else None,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "skipped": self.skipped,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AutomationResult":
        """Create from dictionary."""
        return cls(
            success=data["success"],
            element=UIElement.from_dict(data["element"]) if data.get("element") else None,
            screenshot=bytes.fromhex(data["screenshot"]) if data.get("screenshot") else None,
            error=data.get("error"),
            duration_ms=data.get("duration_ms", 0.0),
            metadata=data.get("metadata"),
            skipped=data.get("skipped", False),
        )


class DesktopAutomationProvider(ABC):
    """Abstract base for desktop automation providers."""

    def __init__(self, platform: str):
        self.platform = platform
        self._element_cache: dict[str, tuple[UIElement, float]] = {}
        self._cache_ttl = 30.0  # 30 seconds

    @abstractmethod
    def click(self, element: UIElement, timeout_ms: float = 5000.0) -> AutomationResult:
        """Click a UI element.

        Args:
            element: UI element to click
            timeout_ms: Timeout in milliseconds

        Returns:
            AutomationResult with success status and details
        """
        pass

    @abstractmethod
    def type_text(self, element: UIElement, text: str, timeout_ms: float = 5000.0) -> AutomationResult:
        """Type text into an element.

        Args:
            element: UI element to type into
            text: Text to type
            timeout_ms: Timeout in milliseconds

        Returns:
            AutomationResult with success status
        """
        pass

    @abstractmethod
    def find_element(self, selector: str, timeout_ms: float = 5000.0) -> Optional[UIElement]:
        """Find UI element by selector.

        Args:
            selector: Element selector (XPath, accessibility name, etc.)
            timeout_ms: Timeout in milliseconds

        Returns:
            UIElement if found, None otherwise
        """
        pass

    @abstractmethod
    def screenshot(self, region: Optional[dict[str, int]] = None) -> bytes:
        """Take screenshot of desktop or region.

        Args:
            region: Optional region {x, y, width, height}

        Returns:
            Screenshot as PNG bytes
        """
        pass

    @abstractmethod
    def wait_for_user_idle(self, idle_seconds: float = 5.0, timeout_ms: float = 30000.0) -> bool:
        """Wait until user is idle.

        Args:
            idle_seconds: Required idle duration in seconds
            timeout_ms: Maximum wait time in milliseconds

        Returns:
            True if user became idle, False on timeout
        """
        pass

    @abstractmethod
    def get_active_window(self) -> Optional[UIElement]:
        """Get currently active window.

        Returns:
            UIElement representing active window, None if not found
        """
        pass

    @abstractmethod
    def list_windows(self, app_name: Optional[str] = None) -> list[UIElement]:
        """List all windows (optionally filtered by app).

        Args:
            app_name: Optional app name filter

        Returns:
            List of UIElement representing windows
        """
        pass

    def find_element_cached(self, selector: str, timeout_ms: float = 5000.0) -> Optional[UIElement]:
        """Find element with caching.

        Args:
            selector: Element selector
            timeout_ms: Timeout in milliseconds

        Returns:
            UIElement if found (from cache or fresh lookup)
        """
        now = time.time()

        # Check cache
        if selector in self._element_cache:
            element, cached_at = self._element_cache[selector]
            if now - cached_at < self._cache_ttl:
                # Validate element still exists
                if element.is_valid():
                    return element
                else:
                    del self._element_cache[selector]

        # Cache miss: find element
        element = self.find_element(selector, timeout_ms)
        if element:
            self._element_cache[selector] = (element, now)

        return element

    def clear_cache(self):
        """Clear element cache."""
        self._element_cache.clear()
```

---

## Template 2: macOS Provider Implementation

### File: `src/thegent/infra/desktop_automation/macos.py`

```python
"""macOS desktop automation provider using AppleScript and Apple Events."""

import subprocess
import time
import logging
from typing import Optional
from pathlib import Path

from thegent.infra.desktop_automation.base import (
    DesktopAutomationProvider,
    UIElement,
    AutomationResult,
)

_log = logging.getLogger(__name__)


class macOSAutomationProvider(DesktopAutomationProvider):
    """macOS automation provider using AppleScript/Apple Events."""

    def __init__(self):
        super().__init__(platform="darwin")
        self._check_permissions()

    def _check_permissions(self) -> bool:
        """Check if Accessibility permission is granted."""
        try:
            import Quartz

            app = Quartz.AXUIElementCreateApplication(os.getpid())
            return True
        except Exception:
            _log.warning("Accessibility permission not granted")
            return False

    def click(self, element: UIElement, timeout_ms: float = 5000.0) -> AutomationResult:
        """Click element using AppleScript."""
        start_time = time.time()

        try:
            # AppleScript to click element
            script = f'''
            tell application "System Events"
                tell process "{element.attributes.get("process_name", "")}"
                    click {element.selector}
                end tell
            end tell
            '''

            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=timeout_ms / 1000.0
            )

            duration_ms = (time.time() - start_time) * 1000

            if result.returncode == 0:
                return AutomationResult(success=True, duration_ms=duration_ms)
            else:
                return AutomationResult(success=False, error=result.stderr, duration_ms=duration_ms)

        except subprocess.TimeoutExpired:
            return AutomationResult(success=False, error="Timeout", duration_ms=timeout_ms)
        except Exception as e:
            return AutomationResult(success=False, error=str(e), duration_ms=(time.time() - start_time) * 1000)

    def type_text(self, element: UIElement, text: str, timeout_ms: float = 5000.0) -> AutomationResult:
        """Type text using AppleScript."""
        start_time = time.time()

        try:
            # AppleScript to type text
            script = f'''
            tell application "System Events"
                tell process "{element.attributes.get("process_name", "")}"
                    set value of {element.selector} to "{text}"
                end tell
            end tell
            '''

            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=timeout_ms / 1000.0
            )

            duration_ms = (time.time() - start_time) * 1000

            if result.returncode == 0:
                return AutomationResult(success=True, duration_ms=duration_ms)
            else:
                return AutomationResult(success=False, error=result.stderr, duration_ms=duration_ms)

        except Exception as e:
            return AutomationResult(success=False, error=str(e), duration_ms=(time.time() - start_time) * 1000)

    def find_element(self, selector: str, timeout_ms: float = 5000.0) -> Optional[UIElement]:
        """Find element using AppleScript."""
        try:
            # AppleScript to find element
            script = f"""
            tell application "System Events"
                -- Find element logic here
            end tell
            """

            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=timeout_ms / 1000.0
            )

            if result.returncode == 0:
                # Parse result and create UIElement
                return UIElement(
                    selector=selector,
                    name="",  # Parse from result
                    role="",  # Parse from result
                    bounds={},  # Parse from result
                    attributes={},
                )

            return None

        except Exception as e:
            _log.error(f"Error finding element: {e}")
            return None

    def screenshot(self, region: Optional[dict[str, int]] = None) -> bytes:
        """Take screenshot using screencapture."""
        try:
            if region:
                # Region screenshot
                cmd = [
                    "screencapture",
                    "-x",  # No sounds
                    "-R",
                    f"{region['x']},{region['y']},{region['width']},{region['height']}",
                    "-t",
                    "png",
                    "-",
                ]
            else:
                # Full screen
                cmd = ["screencapture", "-x", "-t", "png", "-"]

            result = subprocess.run(cmd, capture_output=True, check=True)

            return result.stdout

        except Exception as e:
            _log.error(f"Error taking screenshot: {e}")
            raise

    def wait_for_user_idle(self, idle_seconds: float = 5.0, timeout_ms: float = 30000.0) -> bool:
        """Wait for user idle using IOKit."""
        try:
            import Quartz

            deadline = time.time() + (timeout_ms / 1000.0)
            last_activity = time.time()

            while time.time() < deadline:
                # Check last user activity
                # (Implementation depends on IOKit)
                idle_time = time.time() - last_activity

                if idle_time >= idle_seconds:
                    return True

                time.sleep(0.5)

            return False

        except Exception as e:
            _log.error(f"Error waiting for idle: {e}")
            return False

    def get_active_window(self) -> Optional[UIElement]:
        """Get active window."""
        # Implementation using AppleScript or Accessibility API
        pass

    def list_windows(self, app_name: Optional[str] = None) -> list[UIElement]:
        """List windows."""
        # Implementation using AppleScript or Accessibility API
        pass
```

---

## Template 3: Coordinator Implementation

### File: `src/thegent/infra/desktop_automation/coordinator.py`

```python
"""Multi-tenant desktop automation coordinator."""

import time
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from thegent.orchestration.leasing import get_lease_manager, EditLease
from thegent.infra.desktop_automation.base import (
    DesktopAutomationProvider,
    AutomationScope,
    AutomationAction,
    AutomationResult,
)

_log = logging.getLogger(__name__)


@dataclass
class AutomationScope:
    """Defines scope for automation coordination."""

    app_name: str
    window_title: str | None = None
    region: dict[str, int] | None = None

    def to_lease_path(self) -> str:
        """Convert to lease path."""
        return f"automation:{self.app_name}:{self.window_title or '*'}:{self.region or '*'}"


class DesktopAutomationCoordinator:
    """Coordinates desktop automation across multiple agents."""

    def __init__(self, state_dir: Path, provider: DesktopAutomationProvider):
        self.state_dir = state_dir
        self.provider = provider
        self.lease_manager = get_lease_manager(state_dir)
        self.active_locks: dict[str, EditLease] = {}
        self.user_activity_detector = UserActivityDetector()

    def acquire_lock(self, scope: AutomationScope, agent_id: str, duration: float = 300.0) -> bool:
        """Acquire automation lock.

        Args:
            scope: Automation scope
            agent_id: Agent identifier
            duration: Lock duration in seconds

        Returns:
            True if lock acquired, False otherwise
        """
        lease_path = scope.to_lease_path()

        # Check user activity
        if self.user_activity_detector.is_user_active():
            _log.info("User is active, deferring automation")
            return False

        # Acquire lease
        acquired = self.lease_manager.acquire(path=lease_path, agent_id=agent_id, duration=duration, force=False)

        if acquired:
            self.active_locks[lease_path] = EditLease(
                path=lease_path, agent_id=agent_id, expires_at=time.time() + duration
            )

        return acquired

    def release_lock(self, scope: AutomationScope, agent_id: str):
        """Release automation lock."""
        lease_path = scope.to_lease_path()
        self.lease_manager.release(lease_path, agent_id)
        self.active_locks.pop(lease_path, None)

    def execute_with_coordination(
        self, scope: AutomationScope, agent_id: str, action: AutomationAction
    ) -> AutomationResult:
        """Execute automation action with coordination.

        Args:
            scope: Automation scope
            agent_id: Agent identifier
            action: Automation action

        Returns:
            AutomationResult
        """
        # Acquire lock
        if not self.acquire_lock(scope, agent_id):
            return AutomationResult(success=False, error="Could not acquire automation lock")

        try:
            # Wait for user idle if needed
            if action.wait_for_idle_seconds > 0:
                idle = self.provider.wait_for_user_idle(
                    idle_seconds=action.wait_for_idle_seconds, timeout_ms=action.timeout_ms
                )
                if not idle:
                    return AutomationResult(success=False, error="User did not become idle")

            # Execute action
            if action.type == "click":
                element = self.provider.find_element(action.selector, action.timeout_ms)
                if not element:
                    return AutomationResult(success=False, error=f"Element not found: {action.selector}")
                return self.provider.click(element, action.timeout_ms)

            elif action.type == "type_text":
                element = self.provider.find_element(action.selector, action.timeout_ms)
                if not element:
                    return AutomationResult(success=False, error=f"Element not found: {action.selector}")
                return self.provider.type_text(element, action.text, action.timeout_ms)

            elif action.type == "screenshot":
                screenshot = self.provider.screenshot(action.region)
                return AutomationResult(success=True, screenshot=screenshot)

            else:
                return AutomationResult(success=False, error=f"Unknown action type: {action.type}")

        finally:
            # Release lock
            self.release_lock(scope, agent_id)


class UserActivityDetector:
    """Detects user activity."""

    def __init__(self, threshold_seconds: float = 5.0):
        self.threshold = threshold_seconds
        self.last_activity_time: float = 0.0

    def is_user_active(self) -> bool:
        """Check if user is currently active."""
        # Platform-specific implementation
        # macOS: IOKit
        # Windows: GetLastInputInfo
        # Linux: X11/Wayland
        return (time.time() - self.last_activity_time) < self.threshold

    def record_activity(self):
        """Record user activity."""
        self.last_activity_time = time.time()
```

---

## Template 4: MCP Tool Registration

### File: `src/thegent/mcp_server.py` (additions)

```python
"""MCP tool registration for desktop automation."""

from fastmcp import FastMCP
from thegent.infra.desktop_automation import get_provider, DesktopAutomationCoordinator
from thegent.infra.desktop_automation.base import AutomationAction, AutomationScope


# In mcp server initialization
def register_desktop_automation_tools(mcp: FastMCP, settings: ThegentSettings):
    """Register desktop automation MCP tools."""

    coordinator = DesktopAutomationCoordinator(state_dir=settings.session_dir, provider=get_provider())

    @mcp.tool()
    async def desktop_automation_click(
        selector: str, wait_timeout: float = 5.0, agent_id: str | None = None
    ) -> dict[str, any]:
        """Click a UI element identified by selector.

        Args:
            selector: Element selector (XPath, accessibility name, etc.)
            wait_timeout: Timeout in seconds (default: 5.0)
            agent_id: Optional agent identifier

        Returns:
            Result dictionary with success status
        """
        scope = AutomationScope(app_name="*")  # Global scope
        action = AutomationAction(type="click", selector=selector, timeout_ms=wait_timeout * 1000.0)

        result = coordinator.execute_with_coordination(scope=scope, agent_id=agent_id or "mcp-client", action=action)

        return result.to_dict()

    @mcp.tool()
    async def desktop_automation_type(
        selector: str, text: str, wait_timeout: float = 5.0, agent_id: str | None = None
    ) -> dict[str, any]:
        """Type text into a UI element.

        Args:
            selector: Element selector
            text: Text to type
            wait_timeout: Timeout in seconds
            agent_id: Optional agent identifier

        Returns:
            Result dictionary
        """
        scope = AutomationScope(app_name="*")
        action = AutomationAction(type="type_text", selector=selector, text=text, timeout_ms=wait_timeout * 1000.0)

        result = coordinator.execute_with_coordination(scope=scope, agent_id=agent_id or "mcp-client", action=action)

        return result.to_dict()

    @mcp.tool()
    async def desktop_automation_find(selector: str, timeout: float = 5.0) -> dict[str, any]:
        """Find UI element by selector.

        Args:
            selector: Element selector
            timeout: Timeout in seconds

        Returns:
            Element dictionary or None
        """
        provider = get_provider()
        element = provider.find_element(selector, timeout_ms=timeout * 1000.0)

        if element:
            return {
                "found": True,
                "element": {
                    "selector": element.selector,
                    "name": element.name,
                    "role": element.role,
                    "bounds": element.bounds,
                },
            }
        else:
            return {"found": False}

    @mcp.tool()
    async def desktop_automation_screenshot(region: dict[str, int] | None = None) -> dict[str, any]:
        """Take screenshot of desktop or region.

        Args:
            region: Optional region {x, y, width, height}

        Returns:
            Screenshot data (base64 encoded)
        """
        provider = get_provider()
        screenshot = provider.screenshot(region)

        import base64

        return {"screenshot": base64.b64encode(screenshot).decode("utf-8"), "format": "png"}

    @mcp.tool()
    async def desktop_automation_wait_for_user_idle(idle_seconds: float = 5.0, timeout: float = 30.0) -> dict[str, any]:
        """Wait until user is idle.

        Args:
            idle_seconds: Required idle duration in seconds
            timeout: Maximum wait time in seconds

        Returns:
            Result dictionary
        """
        provider = get_provider()
        idle = provider.wait_for_user_idle(idle_seconds=idle_seconds, timeout_ms=timeout * 1000.0)

        return {"idle": idle, "idle_seconds": idle_seconds}
```

---

## Template 5: Test Fixtures

### File: `tests/fixtures/desktop_automation.py`

```python
"""Test fixtures for desktop automation."""

import pytest
from unittest.mock import Mock, MagicMock
from thegent.infra.desktop_automation.base import (
    DesktopAutomationProvider,
    UIElement,
    AutomationResult,
    AutomationAction,
)


@pytest.fixture
def mock_provider():
    """Mock automation provider."""
    provider = Mock(spec=DesktopAutomationProvider)

    # Mock click
    provider.click.return_value = AutomationResult(success=True)

    # Mock type_text
    provider.type_text.return_value = AutomationResult(success=True)

    # Mock find_element
    provider.find_element.return_value = UIElement(
        selector="button[name='Save']",
        name="Save",
        role="button",
        bounds={"x": 100, "y": 200, "width": 80, "height": 30},
        attributes={},
    )

    # Mock screenshot
    provider.screenshot.return_value = b"fake_png_data"

    # Mock wait_for_user_idle
    provider.wait_for_user_idle.return_value = True

    return provider


@pytest.fixture
def mock_element():
    """Mock UI element."""
    return UIElement(
        selector="button[name='Save']",
        name="Save",
        role="button",
        bounds={"x": 100, "y": 200, "width": 80, "height": 30},
        attributes={"process_name": "TextEdit"},
    )


@pytest.fixture
def mock_coordinator(tmp_path, mock_provider):
    """Mock coordinator."""
    from thegent.infra.desktop_automation.coordinator import DesktopAutomationCoordinator

    coordinator = DesktopAutomationCoordinator(state_dir=tmp_path, provider=mock_provider)

    return coordinator
```

---

## Template 6: Configuration Schema

### File: `src/thegent/config.py` (additions)

```python
"""Configuration schema for desktop automation."""

from pydantic import Field
from typing import Optional


class DesktopAutomationSettings(BaseSettings):
    """Settings for desktop automation."""

    desktop_automation_enabled: bool = Field(
        default=False, description="Enable desktop automation (THGENT_DESKTOP_AUTOMATION_ENABLED)"
    )

    desktop_automation_platform: Optional[str] = Field(
        default=None, description="Platform override (darwin, windows, linux) (THGENT_DESKTOP_AUTOMATION_PLATFORM)"
    )

    desktop_automation_coordination_enabled: bool = Field(
        default=True, description="Enable multi-tenant coordination (THGENT_DESKTOP_AUTOMATION_COORDINATION_ENABLED)"
    )

    desktop_automation_user_idle_threshold: float = Field(
        default=5.0, description="User idle threshold in seconds (THGENT_DESKTOP_AUTOMATION_USER_IDLE_THRESHOLD)"
    )

    desktop_automation_rate_limit_per_minute: int = Field(
        default=100, description="Global rate limit per minute (THGENT_DESKTOP_AUTOMATION_RATE_LIMIT_PER_MINUTE)"
    )

    desktop_automation_budget_mtd: float = Field(
        default=10.0, description="Monthly budget for automation in USD (THGENT_DESKTOP_AUTOMATION_BUDGET_MTD)"
    )

    desktop_automation_allowed_apps: list[str] = Field(
        default_factory=list, description="Allowed apps for automation (THGENT_DESKTOP_AUTOMATION_ALLOWED_APPS JSON)"
    )

    desktop_automation_blocked_apps: list[str] = Field(
        default_factory=list, description="Blocked apps for automation (THGENT_DESKTOP_AUTOMATION_BLOCKED_APPS JSON)"
    )
```

---

## Template 7: CLI Commands

### File: `src/thegent/cli.py` (additions)

```python
"""CLI commands for desktop automation."""

import typer
from rich.console import Console
from rich.table import Table

console = Console()

desktop_automation_app = typer.Typer(help="Desktop automation commands")


@desktop_automation_app.command("check-permissions")
def check_permissions():
    """Check desktop automation permissions."""
    from thegent.infra.desktop_automation import check_permissions

    permissions = check_permissions()

    table = Table(title="Desktop Automation Permissions")
    table.add_column("Permission", style="cyan")
    table.add_column("Status", style="green")

    for perm, granted in permissions.items():
        status = "✓ Granted" if granted else "✗ Not Granted"
        table.add_row(perm, status)

    console.print(table)


@desktop_automation_app.command("test-click")
def test_click(
    selector: str = typer.Argument(..., help="Element selector"),
    timeout: float = typer.Option(5.0, "--timeout", "-t", help="Timeout in seconds"),
):
    """Test clicking an element."""
    from thegent.infra.desktop_automation import get_provider

    provider = get_provider()
    element = provider.find_element(selector, timeout_ms=timeout * 1000.0)

    if not element:
        console.print(f"[red]Element not found: {selector}[/red]")
        raise typer.Exit(1)

    result = provider.click(element, timeout_ms=timeout * 1000.0)

    if result.success:
        console.print(f"[green]Click successful[/green]")
    else:
        console.print(f"[red]Click failed: {result.error}[/red]")
        raise typer.Exit(1)


@desktop_automation_app.command("locks")
def list_locks():
    """List active automation locks."""
    from thegent.infra.desktop_automation.coordinator import DesktopAutomationCoordinator
    from thegent.config import ThegentSettings

    settings = ThegentSettings()
    coordinator = DesktopAutomationCoordinator(state_dir=settings.session_dir, provider=get_provider())

    table = Table(title="Active Automation Locks")
    table.add_column("Scope", style="cyan")
    table.add_column("Agent", style="yellow")
    table.add_column("Expires At", style="green")

    for lease_path, lease in coordinator.active_locks.items():
        table.add_row(lease_path, lease.agent_id, str(lease.expires_at))

    console.print(table)
```

---

## Usage Examples

### Example 1: Basic Automation

```python
from thegent.infra.desktop_automation import get_provider

provider = get_provider()

# Find element
element = provider.find_element("button[name='Save']")

# Click element
if element:
    result = provider.click(element)
    print(f"Success: {result.success}")
```

### Example 2: Coordinated Automation

```python
from thegent.infra.desktop_automation import get_provider
from thegent.infra.desktop_automation.coordinator import DesktopAutomationCoordinator, AutomationScope
from thegent.infra.desktop_automation.base import AutomationAction

provider = get_provider()
coordinator = DesktopAutomationCoordinator(state_dir=Path(".thegent"), provider=provider)

scope = AutomationScope(app_name="TextEdit")
action = AutomationAction(type="click", selector="button[name='Save']")

result = coordinator.execute_with_coordination(scope=scope, agent_id="agent-1", action=action)
```

### Example 3: MCP Tool Usage

```python
# Via MCP client
result = await mcp_client.call_tool(
    "desktop_automation_click", {"selector": "button[name='Save']", "wait_timeout": 5.0, "agent_id": "my-agent"}
)
```

---

## Implementation Checklist

### Phase 1: Foundation

- [ ] Create base provider abstract class
- [ ] Implement macOS provider
- [ ] Implement Windows provider
- [ ] Implement Linux provider
- [ ] Add provider factory (`get_provider()`)

### Phase 2: Coordination

- [ ] Create coordinator class
- [ ] Integrate with EditLeaseManager
- [ ] Add user activity detection
- [ ] Add conflict resolution

### Phase 3: MCP Integration

- [ ] Register MCP tools
- [ ] Add tool handlers
- [ ] Add error handling
- [ ] Add observability

### Phase 4: Testing

- [ ] Create test fixtures
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Add platform-specific tests

### Phase 5: Documentation

- [ ] API documentation
- [ ] Usage examples
- [ ] Troubleshooting guide
- [ ] Migration guide

---

**Status:** Implementation templates complete. Ready for code generation and implementation.

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
