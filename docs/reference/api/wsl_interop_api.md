# wsl_interop API Reference

> **Source**: `src/thegent/infra/wsl_interop.py`

WSL2 interop and path translation utilities.

---

## WslInterop

Utilities for seamless interop between native Windows and WSL2.

Provides high-performance path translation and identity mapping.

### Methods

#### WslInterop.**init**

```python
__init__(self: Any)
```

---

#### WslInterop.get_windows_user_profile

```python
get_windows_user_profile(self: Any)
```

Get the Windows user profile path (C:\Users\Name).

---

#### WslInterop.map_sid_to_uid

```python
map_sid_to_uid(self: Any, sid: str)
```

Map a Windows SID to a WSL2 UID.

Implementation logic:

1. deterministic hash-based mapping (similar to sub-user system).
2. /etc/wsl.conf [user] default=&lt;uid&gt; if needed.

---

#### WslInterop.to_windows_path

```python
to_windows_path(self: Any, wsl_path: str)
```

Convert a WSL path to a Windows path.

Uses fast-path regex if possible, falls back to wslpath.

---

#### WslInterop.to_wsl_path

```python
to_wsl_path(self: Any, windows_path: str)
```

Convert a Windows path to a WSL path.

Uses fast-path regex if possible, falls back to wslpath.

---

---

## get_windows_user_profile

```python
get_windows_user_profile(self: Any)
```

Get the Windows user profile path (C:\Users\Name).

---

## map_sid_to_uid

```python
map_sid_to_uid(self: Any, sid: str)
```

Map a Windows SID to a WSL2 UID.

Implementation logic:

1. deterministic hash-based mapping (similar to sub-user system).
2. /etc/wsl.conf [user] default=&lt;uid&gt; if needed.

---

## to_windows_path

```python
to_windows_path(self: Any, wsl_path: str)
```

Convert a WSL path to a Windows path.

Uses fast-path regex if possible, falls back to wslpath.

---

## to_wsl_path

```python
to_wsl_path(self: Any, windows_path: str)
```

Convert a Windows path to a WSL path.

Uses fast-path regex if possible, falls back to wslpath.

---
