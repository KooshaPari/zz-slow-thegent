# Cross-Platform Desktop Automation: Quick Start Guide

**Purpose:** Get started with desktop automation in 5 minutes.

**Date:** 2026-02-16
**Status:** Quick Start Guide
**Related:** CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md

---

## 5-Minute Quick Start

### Step 1: Install Dependencies (1 min)

```bash
# macOS
pip install py-applescript

# Windows
pip install pywinauto

# Linux
pip install pyatspi
```

### Step 2: Grant Permissions (2 min)

**macOS:**

1. System Preferences > Security & Privacy > Accessibility
2. Add Terminal (or your Python interpreter)
3. System Preferences > Security & Privacy > Screen Recording (for screenshots)
4. Add Terminal

**Windows:**

- Run as Administrator, OR
- Configure Group Policy (see Quick Reference)

**Linux:**

- Usually granted by default

### Step 3: Write Your First Automation (2 min)

```python
from thegent.infra.desktop_automation import get_provider

# Get provider (auto-detects platform)
provider = get_provider()

# Find element
element = provider.find_element("button[name='Save']")

# Click element
if element:
    result = provider.click(element)
    print(f"Success: {result.success}, Duration: {result.duration_ms}ms")
```

### Step 4: Run It!

```bash
python your_script.py
```

---

## Common Use Cases

### Use Case 1: Click a Button

```python
from thegent.infra.desktop_automation import get_provider

provider = get_provider()
element = provider.find_element("button[name='Save']")
if element:
    provider.click(element)
```

### Use Case 2: Fill a Form

```python
provider = get_provider()

# Fill username
username_field = provider.find_element("text_field[name='username']")
if username_field:
    provider.type_text(username_field, "myusername")

# Fill password
password_field = provider.find_element("text_field[name='password']")
if password_field:
    provider.type_text(password_field, "mypassword")

# Click submit
submit_button = provider.find_element("button[type='submit']")
if submit_button:
    provider.click(submit_button)
```

### Use Case 3: Take Screenshot

```python
provider = get_provider()

# Full screen
screenshot = provider.screenshot()

# Save to file
with open("screenshot.png", "wb") as f:
    f.write(screenshot)

# Region only
region = {"x": 100, "y": 200, "width": 800, "height": 600}
screenshot = provider.screenshot(region=region)
```

---

## Next Steps

1. **Read Quick Reference:** `docs/reference/CROSS_PLATFORM_MULTI_TENANT_QUICK_REFERENCE.md`
2. **Try Cookbook Recipes:** `docs/guides/CROSS_PLATFORM_DEVELOPER_COOKBOOK.md`
3. **Check API Reference:** `docs/reference/CROSS_PLATFORM_API_REFERENCE.md`
4. **Read Full Research:** `docs/research/CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md`

---

**Status:** Quick start guide complete. Ready for immediate use.

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

---

## 6. Platform-Specific Tips

### 6.1 macOS

```python
# Use AppleScript for native interactions
from infra.desktop_automation import macos_provider

# Click menu item
macos_provider.click_menu("File", "Save As...")

# Get active window title
title = macos_provider.get_active_window_title()

# Take screenshot
macos_provider.screenshot("screenshot.png")
```

### 6.2 Windows

```python
# Use pywinauto for Windows interactions
from infra.desktop_automation import windows_provider

# Find by control type
dialog = windows_provider.find_window(class_name="#32770")

# Click button
dialog.button("Save").click()

# Type text
dialog.edit("FileName:").type_keys("test.txt")
```

### 6.3 Linux

```python
# Use AT-SPI for Linux accessibility
from infra.desktop_automation import linux_provider

# Find by accessible name
button = linux_provider.find_element(name="Save")

# Get element attributes
attrs = linux_provider.get_attributes(button)

# Focus element
linux_provider.focus_element(button)
```

---

## 7. Common Automation Patterns

### 7.1 Waiting for Elements

```python
from infra.desktop_automation import get_provider

provider = get_provider()

# Wait for element to appear (timeout=10s)
element = provider.wait_for_element("button[name='Submit']", timeout=10)

# Wait for element to disappear
provider.wait_for_element_not_present("dialog[title='Loading']", timeout=30)
```

### 7.2 Handling Dialogs

```python
# Auto-handle common dialogs
provider.handle_dialog("save", path="/tmp/file.txt")
provider.handle_dialog("open", pattern="*.txt")
provider.handle_dialog("confirm", action="Yes")
provider.handle_dialog("error", action="Dismiss")
```

### 7.3 Taking Screenshots

```python
# Screenshot entire screen
provider.screenshot("screen.png")

# Screenshot specific region
provider.screenshot_region("region.png", x=100, y=100, width=500, height=300)

# Screenshot element
element = provider.find_element("window[name='Main']")
provider.screenshot_element(element, "window.png")
```

---

## 8. Testing Desktop Automation

```python
import pytest


@pytest.fixture
def automation_provider():
    """Provider fixture with cleanup."""
    provider = get_provider()
    yield provider
    provider.cleanup()


def test_save_dialog(automation_provider):
    """Test save dialog interaction."""
    # Open save dialog
    automation_provider.click_menu("File", "Save As...")

    # Verify dialog appeared
    dialog = automation_provider.find_window(title_contains="Save")
    assert dialog is not None

    # Enter filename
    dialog.edit(class_name="Edit").type_keys("test.txt")

    # Click save
    dialog.button("Save").click()
```

---

## 9. Extension Summary

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added Section 6:** Platform-Specific Tips
   - macOS automation patterns
   - Windows automation patterns
   - Linux automation patterns

2. **Added Section 7:** Common Automation Patterns
   - Waiting for elements
   - Handling dialogs
   - Taking screenshots

3. **Added Section 8:** Testing Desktop Automation
   - Pytest fixtures for automation
   - Example test cases

### Cross-References Added

- CROSS_PLATFORM_DEVELOPER_COOKBOOK.md
- CROSS_PLATFORM_MULTI_TENANT_DESKTOP_AUTOMATION_RESEARCH.md

### Practical Additions

- Platform-specific code examples
- Common automation patterns
- Testing patterns for automation
