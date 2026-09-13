# platform_paths API Reference

> **Source**: `src/thegent/platform_paths.py`

Platform-specific path resolution following OS conventions.

---

## get_config_dir

Get platform-specific configuration directory.

Follows OS conventions:

- macOS: ~/Library/Application Support/thegent
- Linux: ~/.config/thegent
- Windows: %APPDATA%/thegent

**Returns**: Path to configuration directory (created if needed)

---
