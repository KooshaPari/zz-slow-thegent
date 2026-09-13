#!/usr/bin/env python3
"""
Cross-platform path handling utilities with security and consistency.

This module provides normalized path operations that work consistently
across Windows, macOS, and Linux. All functions return pathlib.Path objects
to avoid str/Path mixing and ensure type safety.

Key features:
- Automatic ~ expansion and .. resolution
- Cross-platform separator handling
- Directory traversal attack prevention (safe_join / is_within)
- Safe path existence checks (no PermissionError leakage)
- Relative path computation for logging/display

Usage:
    from scripts.path_utils import (
        normalize_path,
        safe_join,
        is_within,
        safe_exists,
        rel_to_cwd,
        ensure_dir,
    )

    path = normalize_path("~/projects/myfile.txt")
    file = safe_join(base_dir, user_input)
    if not is_within(file, allowed_dir):
        raise ValueError("Path escapes allowed directory")
"""

from __future__ import annotations

import contextlib
import re
import tempfile
from pathlib import Path


def normalize_path(path: str | Path | None, base: str | Path | None = None) -> Path:
    """Normalize a path with ~ expansion and absolute resolution.

    If *path* is relative and *base* is given, the path is resolved relative
    to *base*.  If *base* is omitted, relative paths are resolved against the
    current working directory.

    Args:
        path: Input path as string or Path object. ``None`` returns the CWD.
        base: Optional base directory for resolving relative paths.

    Returns:
        Normalized absolute :class:`~pathlib.Path`.

    Raises:
        TypeError: If *path* is not ``str``, :class:`~pathlib.Path`, or ``None``.

    Examples:
        >>> normalize_path("~/projects/thegent")
        PosixPath('/Users/username/projects/thegent')

        >>> normalize_path("./config", "/home/user/app")
        PosixPath('/home/user/app/config')

        >>> normalize_path(None)
        PosixPath('/current/working/directory')
    """
    if path is None:
        return Path.cwd()

    if isinstance(path, str):
        p = Path(path)
    elif isinstance(path, Path):
        p = path
    else:
        raise TypeError(f"Expected str, Path, or None; got {type(path).__name__}")

    # Expand ~ to home directory
    p = p.expanduser()

    if not p.is_absolute():
        if base is not None:
            base_path = _resolve(Path(base).expanduser())
            p = (base_path / p).resolve()
        else:
            p = p.resolve()
    else:
        p = _resolve(p)

    return p


def safe_join(base: str | Path, *parts: str | Path) -> Path:
    """Join *base* with *parts*, blocking any directory traversal escape.

    Resolves the joined path and verifies it remains inside *base*.  Raises
    :class:`ValueError` if any ``..`` component or absolute override would
    navigate the result outside *base*.

    Args:
        base: The trusted base directory.
        *parts: Path components to join (may be user-supplied / untrusted).

    Returns:
        Absolute :class:`~pathlib.Path` strictly inside (or equal to) *base*.

    Raises:
        ValueError: If the joined path escapes *base*.

    Examples:
        >>> safe_join("/tmp/sandbox", "subdir/file.txt")
        PosixPath('/tmp/sandbox/subdir/file.txt')

        >>> safe_join("/tmp/sandbox", "../../etc/passwd")
        ValueError: Path escapes base '/tmp/sandbox'
    """
    resolved_base = _resolve(Path(base).expanduser())

    candidate = resolved_base
    for part in parts:
        candidate = candidate / Path(part).expanduser()

    resolved_candidate = _resolve(candidate)

    if not is_within(resolved_candidate, resolved_base):
        raise ValueError(f"Path escapes base '{resolved_base}': resolved to '{resolved_candidate}'")

    return resolved_candidate


def is_within(child: str | Path, parent: str | Path) -> bool:
    """Return ``True`` if *child* is at or below *parent* in the filesystem tree.

    Both paths are resolved (symlinks expanded, ``..`` collapsed) before the
    containment check so they cannot fool the comparison.

    Args:
        child: Path to test.
        parent: Directory that *child* must be contained in.

    Returns:
        ``True`` if *child* equals *parent* or is a descendant of *parent*.

    Examples:
        >>> is_within("/tmp/foo/bar.txt", "/tmp/foo")
        True

        >>> is_within("/tmp/other/file.txt", "/tmp/foo")
        False

        >>> is_within("/tmp/foo", "/tmp/foo")   # same path → True
        True
    """
    try:
        resolved_child = _resolve(Path(child).expanduser())
        resolved_parent = _resolve(Path(parent).expanduser())
        resolved_child.relative_to(resolved_parent)
        return True
    except ValueError:
        return False


def safe_exists(path: str | Path) -> bool:
    """Check whether *path* exists without raising on permission or OS errors.

    Unlike :meth:`~pathlib.Path.exists`, this function catches
    :class:`PermissionError` and :class:`OSError` and returns ``False``
    instead of propagating them.

    Args:
        path: Path to check (``~`` expansion is applied).

    Returns:
        ``True`` if the path exists and is accessible; ``False`` otherwise.

    Examples:
        >>> safe_exists("/tmp")
        True

        >>> safe_exists("/nonexistent/path")
        False

        >>> safe_exists("/root/secret")   # PermissionError → False
        False
    """
    try:
        return Path(path).expanduser().exists()
    except (PermissionError, OSError, TypeError, ValueError):
        return False


def rel_to_cwd(path: str | Path) -> Path:
    """Return *path* relative to the current working directory when possible.

    If *path* is not under the CWD the resolved absolute path is returned
    unchanged.  Intended for human-readable display and logging — not for
    filesystem operations.

    Args:
        path: Path to make relative (``~`` expansion applied).

    Returns:
        Relative :class:`~pathlib.Path` when *path* is inside the CWD,
        otherwise the absolute :class:`~pathlib.Path`.

    Examples:
        >>> rel_to_cwd("/home/user/project/src/main.py")   # CWD=/home/user/project
        PosixPath('src/main.py')

        >>> rel_to_cwd("/etc/hosts")
        PosixPath('/etc/hosts')
    """
    resolved = _resolve(Path(path).expanduser())
    try:
        return resolved.relative_to(Path.cwd())
    except ValueError:
        return resolved


def ensure_dir(path: str | Path) -> Path:
    """Create *path* as a directory (including parents) if it does not exist.

    Equivalent to ``mkdir -p``.  Does nothing if the directory already exists.

    Args:
        path: Directory path to create (``~`` expansion applied).

    Returns:
        Resolved absolute :class:`~pathlib.Path` of the created/existing directory.

    Raises:
        NotADirectoryError: If *path* exists but is a file.
        PermissionError: If the directory cannot be created.

    Examples:
        >>> ensure_dir("/tmp/myapp/logs")
        PosixPath('/tmp/myapp/logs')
    """
    p = _resolve(Path(path).expanduser())
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# Retained helpers from prior implementation
# ---------------------------------------------------------------------------


def path_to_str(path: str | Path | None) -> str:
    """Convert a path to a string, handling ``None`` gracefully.

    Args:
        path: Path object, string, or ``None``.

    Returns:
        String representation of *path*, or ``''`` for ``None``.
    """
    if path is None:
        return ""
    return str(path)


def get_common_ancestor(*paths: str | Path) -> Path:
    """Find the common ancestor directory of multiple paths.

    Args:
        *paths: Paths to find the common ancestor for.

    Returns:
        Common ancestor as a :class:`~pathlib.Path`, or the filesystem root
        if no common ancestor exists above the root.

    Examples:
        >>> get_common_ancestor("/home/user/a", "/home/user/b")
        PosixPath('/home/user')
    """
    if not paths:
        return Path.cwd()

    normalized = [normalize_path(p) for p in paths]
    all_parts = [p.parts for p in normalized]
    common: list[str] = []

    for i, part in enumerate(all_parts[0]):
        if all(i < len(pp) and pp[i] == part for pp in all_parts):
            common.append(part)
        else:
            break

    if not common:
        return Path(normalized[0].anchor or "/")

    return Path(*common)


def is_same_path(path1: str | Path, path2: str | Path) -> bool:
    """Return ``True`` if two paths refer to the same filesystem object.

    Uses :meth:`~pathlib.Path.samefile` when both paths exist (handles
    symlinks correctly) and falls back to resolved-path comparison otherwise.

    Args:
        path1: First path.
        path2: Second path.

    Returns:
        ``True`` if paths refer to the same object.
    """
    try:
        return normalize_path(path1).samefile(normalize_path(path2))
    except (OSError, ValueError):
        return normalize_path(path1) == normalize_path(path2)


def is_absolute_or_relative(path: str | Path) -> bool:
    """Return ``True`` if *path* is absolute, ``False`` if relative.

    Note: ``~`` paths are treated as relative until expanded.

    Args:
        path: Path to inspect.

    Returns:
        ``True`` if the path is absolute.

    Examples:
        >>> is_absolute_or_relative("/home/user")
        True

        >>> is_absolute_or_relative("~/projects")
        False

        >>> is_absolute_or_relative("./src")
        False
    """
    p = Path(path) if isinstance(path, str) else path
    return p.is_absolute()


def sanitize_path(name: str) -> str:
    """Replace characters illegal in file system paths with underscores.

    Replaces the characters ``:<>"/\\|?*`` with ``_``.

    Args:
        name: Filename or path component to sanitize.

    Returns:
        Sanitized string safe for use as a path component.

    Examples:
        >>> sanitize_path('file:with*illegal?chars.txt')
        'file_with_illegal_chars.txt'
    """
    return re.sub(r'[:<>"/\\|?*]', "_", name)


def strip_common_prefix(paths: list[str | Path]) -> list[str]:
    """Strip the common directory prefix from a list of paths for display.

    Args:
        paths: Paths to strip common prefix from.

    Returns:
        List of paths with common prefix removed, as strings.

    Examples:
        >>> strip_common_prefix(["/a/b/file1.txt", "/a/b/file2.txt"])
        ['file1.txt', 'file2.txt']
    """
    if not paths:
        return []

    normalized = [normalize_path(p) for p in paths]
    common = get_common_ancestor(*normalized)
    result = []
    for p in normalized:
        if is_within(p, common):
            result.append(str(p.relative_to(common)))
        else:
            result.append(str(p))
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve(path: Path) -> Path:
    """Resolve a path, falling back gracefully when it does not exist.

    On Python 3.6+, ``Path.resolve()`` resolves symlinks and ``..``
    components but does NOT require the path to exist (``strict=False``
    is the default since 3.6).  We make that explicit here.
    """
    return path.resolve()


# ---------------------------------------------------------------------------
# CLI self-test / demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    cwd = Path.cwd()
    sandbox_base = Path(tempfile.gettempdir()) / "sandbox"

    with contextlib.suppress(ValueError):
        safe_join(sandbox_base, "../../etc/passwd")

    safe = safe_join(sandbox_base, "sub/file.txt")

    with tempfile.TemporaryDirectory() as td:
        created = ensure_dir(Path(td) / "a" / "b" / "c")

    sys.exit(0)
