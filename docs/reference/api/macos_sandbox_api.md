# macos_sandbox API Reference

> **Source**: `src/thegent/security/macos_sandbox.py`

macOS sandbox profile management for secure agent execution.

Provides finer-grained security control over agent subprocesses using macOS
Seatbelt (sandbox-exec). Supports five security levels from no restrictions
to read-only filesystem access.

Integration: set `THGENT_SANDBOX_LEVEL` to one of:
none | readonly | restricted | networked | full

The `restricted` and `networked` levels require the project root to be
resolvable (falls back to cwd when not determinable).

---

## MacOSSandbox

macOS Seatbelt sandbox profile manager.

Wraps agent subcommands with `sandbox-exec -f &lt;profile&gt;` so that agents
run with the requested level of filesystem and network isolation.

Example usage::

    sandbox = MacOSSandbox()
    if sandbox.is_sandbox_available():
        cmd = sandbox.apply_to_command(["claude", "--dangerously-skip-permissions"], SandboxLevel.NETWORKED)
    subprocess.Popen(cmd, ...)

Profile files live in `security/profiles/`. The `restricted` and
`networked` templates contain a `PROJECT_ROOT_PLACEHOLDER` token that
is substituted with the real project root before writing to a temp file.

### Methods

#### MacOSSandbox.**init**

```python
__init__(self: Any, profile_dir: Any)
```

---

#### MacOSSandbox.apply_to_command

```python
apply_to_command(self: Any, cmd: list[str], level: SandboxLevel, project_root: Any)
```

Wrap _cmd_ with `sandbox-exec` for the given _level_.

For NONE and FULL, returns _cmd_ unchanged. For all other levels,
writes a profile to a temporary file and prepends
`sandbox-exec -f &lt;profile&gt;` to the command.

The temporary profile file is written with a unique name derived from
`tempfile.mkstemp` so that concurrent agents do not clobber each
other's profiles.

**Parameters**:

- `cmd`: The original subprocess command list.
- `level`: The sandbox security level to apply.
- `project_root`: Required for RESTRICTED and NETWORKED levels.
  Defaults to `Path.cwd()` when not supplied.

**Returns**: The wrapped command list.

---

#### MacOSSandbox.from_env

```python
from_env(cls: Any)
```

Construct a MacOSSandbox using defaults (profile_dir from package).

---

#### MacOSSandbox.generate_profile

```python
generate_profile(self: Any, level: SandboxLevel, project_root: Path)
```

Generate and return the sandbox profile text for _level_.

For RESTRICTED and NETWORKED, replaces `PROJECT_ROOT_PLACEHOLDER`
with _project_root_ so that file-write permissions are scoped to the
project directory.

**Parameters**:

- `level`: The desired sandbox security level.
- `project_root`: Absolute path to the agent's working project directory.

**Returns**: The complete seatbelt profile text ready to be written to a file.

---

#### MacOSSandbox.get_profile_path

```python
get_profile_path(self: Any, level: SandboxLevel)
```

Return the static template path for _level_, or None for NONE/FULL.

The file returned for RESTRICTED and NETWORKED still contains the
`PROJECT_ROOT_PLACEHOLDER` token; callers that need a ready-to-use
profile should call :meth:`generate_profile` instead.

---

#### MacOSSandbox.is_sandbox_available

```python
is_sandbox_available(self: Any)
```

Return True when `sandbox-exec` is present on this system.

`sandbox-exec` ships with macOS but is absent on Linux/Windows.

---

#### MacOSSandbox.level_from_env

```python
level_from_env(cls: Any)
```

Deprecated: Use level_from_settings() instead. Kept for backwards compatibility.

---

#### MacOSSandbox.level_from_settings

```python
level_from_settings(cls: Any)
```

Read sandbox level from ThegentSettings.

---

---

## SandboxLevel

Enumeration of macOS sandbox security levels.

Levels progress from most permissive (FULL/NONE) to most restrictive
(READONLY).

NONE — no sandbox applied; subprocess runs unrestricted.
FULL — no restrictions (alias for NONE; for trusted agents).
READONLY — read filesystem, no network, no writes.
RESTRICTED— read/write project dir only, no network.
NETWORKED — restricted + outbound HTTPS (port 443) allowed.

**Inherits from**: `Enum`

---

## apply_to_command

```python
apply_to_command(self: Any, cmd: list[str], level: SandboxLevel, project_root: Any)
```

Wrap _cmd_ with `sandbox-exec` for the given _level_.

For NONE and FULL, returns _cmd_ unchanged. For all other levels,
writes a profile to a temporary file and prepends
`sandbox-exec -f &lt;profile&gt;` to the command.

The temporary profile file is written with a unique name derived from
`tempfile.mkstemp` so that concurrent agents do not clobber each
other's profiles.

**Parameters**:

- `cmd`: The original subprocess command list.
- `level`: The sandbox security level to apply.
- `project_root`: Required for RESTRICTED and NETWORKED levels.
  Defaults to `Path.cwd()` when not supplied.

**Returns**: The wrapped command list.

**Raises**:

- `RuntimeError`: If sandbox-exec is not available on this platform.
- `FileNotFoundError`: If the profile template is missing.

---

## from_env

```python
from_env(cls: Any)
```

Construct a MacOSSandbox using defaults (profile_dir from package).

---

## generate_profile

```python
generate_profile(self: Any, level: SandboxLevel, project_root: Path)
```

Generate and return the sandbox profile text for _level_.

For RESTRICTED and NETWORKED, replaces `PROJECT_ROOT_PLACEHOLDER`
with _project_root_ so that file-write permissions are scoped to the
project directory.

**Parameters**:

- `level`: The desired sandbox security level.
- `project_root`: Absolute path to the agent's working project directory.

**Returns**: The complete seatbelt profile text ready to be written to a file.

**Raises**:

- `ValueError`: If _level_ is NONE or FULL (no profile needed).
- `FileNotFoundError`: If the profile template is missing.

---

## get_profile_path

```python
get_profile_path(self: Any, level: SandboxLevel)
```

Return the static template path for _level_, or None for NONE/FULL.

The file returned for RESTRICTED and NETWORKED still contains the
`PROJECT_ROOT_PLACEHOLDER` token; callers that need a ready-to-use
profile should call :meth:`generate_profile` instead.

---

## is_sandbox_available

```python
is_sandbox_available(self: Any)
```

Return True when `sandbox-exec` is present on this system.

`sandbox-exec` ships with macOS but is absent on Linux/Windows.

---

## level_from_env

```python
level_from_env(cls: Any)
```

Deprecated: Use level_from_settings() instead. Kept for backwards compatibility.

---

## level_from_settings

```python
level_from_settings(cls: Any)
```

Read sandbox level from ThegentSettings.

---
