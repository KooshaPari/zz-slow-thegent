# Cross-Platform Domain Technical Specification

## Overview

Platform abstraction for desktop automation across OSes.

## Platforms Supported

| Platform | Status | Automation               |
| -------- | ------ | ------------------------ |
| macOS    | ✅     | osascript, Accessibility |
| Windows  | ✅     | Win32, PowerShell        |
| Linux    | ✅     | X11, Wayland             |
| WSL      | ✅     | Interop                  |

### Desktop Automation

| Component       | Platform | Files                                |
| --------------- | -------- | ------------------------------------ |
| macOS desktop   | macOS    | `automation/macos_desktop.py`        |
| Windows desktop | Windows  | `automation/virtual_desktop.py`      |
| Linux desktop   | Linux    | `providers/linux_virtual_desktop.py` |

### Shell Strategy

| Shell      | Platform |
| ---------- | -------- |
| Zsh        | macOS    |
| PowerShell | Windows  |
| Bash       | Linux    |

## Cross-Platform Utilities

| Utility            | Purpose           |
| ------------------ | ----------------- |
| Desktop automation | UI control        |
| Coordination       | Multi-OS          |
| Security           | Platform-specific |
| Performance        | Metrics           |

## Performance

| Metric     | Target |
| ---------- | ------ |
| Launch     | <500ms |
| Input      | <10ms  |
| Screenshot | <100ms |
