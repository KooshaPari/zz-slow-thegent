# utils API Reference

> **Source**: `src/thegent/utils/__init__.py`

Utility functions and helpers.

---

## get_resource_path

```python
get_resource_path(relative_path: str)
```

Get absolute path to a resource file.

In dev mode, looks in the project root.
When installed, uses importlib.resources.

---

## is_dev_mode

Check if thegent is running in development mode.

Dev mode is active if:

1. THGENT_DEV=1 is set (via ThegentSettings.dev)
2. We are running from a git repository and src/thegent exists

---

## strip_ansi

```python
strip_ansi(text: str)
```

Remove ANSI escape sequences from text. Uses rich Text.from_ansi().plain.

---
