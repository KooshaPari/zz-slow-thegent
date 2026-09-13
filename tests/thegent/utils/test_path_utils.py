"""
Unit tests for thegent.utils.path_utils.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from thegent.utils.path_utils import (
    ensure_dir,
    get_common_ancestor,
    is_same_path,
    is_within,
    normalize_path,
    rel_to_cwd,
    safe_exists,
    safe_join,
    sanitize_path,
)


def test_normalize_path_none():
    """normalize_path(None) returns CWD."""
    assert normalize_path(None) == Path.cwd()


def test_normalize_path_string():
    """normalize_path with string input."""
    # We resolve symlinks in normalize_path, so /tmp/foo -> /private/tmp/foo on macOS
    # Path.cwd() is already resolved
    cwd = Path.cwd().resolve()
    assert normalize_path(".") == cwd


def test_normalize_path_tilde():
    """normalize_path with tilde expansion."""
    home = Path.home().resolve()
    assert normalize_path("~") == home


def test_normalize_path_with_base(tmp_path):
    """normalize_path with base directory."""
    base = tmp_path.resolve()
    assert normalize_path("subdir", base=base) == base / "subdir"


def test_safe_join_ok(tmp_path):
    """safe_join with valid paths."""
    base = tmp_path.resolve()
    result = safe_join(base, "subdir", "file.txt")
    assert result == base / "subdir" / "file.txt"


def test_safe_join_traversal(tmp_path):
    """safe_join blocks traversal escapes."""
    base = tmp_path.resolve()
    with pytest.raises(ValueError, match="escapes base"):
        safe_join(base, "..", "outside.txt")


def test_is_within(tmp_path):
    """is_within checks directory containment."""
    base = tmp_path.resolve()
    child = base / "a" / "b"
    assert is_within(child, base) is True
    assert is_within(base, child) is False


def test_safe_exists(tmp_path):
    """safe_exists checks path existence without raising."""
    assert safe_exists(tmp_path) is True
    assert safe_exists(tmp_path / "nonexistent") is False


def test_rel_to_cwd(tmp_path):
    """rel_to_cwd computes relative paths when possible."""
    # If tmp_path is NOT under CWD, it should return absolute
    res = rel_to_cwd(tmp_path)
    if is_within(tmp_path, Path.cwd()):
        assert not res.is_absolute()
    else:
        assert res.is_absolute()


def test_ensure_dir(tmp_path):
    """ensure_dir creates directories recursively."""
    target = tmp_path / "a" / "b" / "c"
    res = ensure_dir(target)
    assert res.exists()
    assert res.is_dir()
    assert res == target.resolve()


def test_get_common_ancestor():
    """get_common_ancestor finds the common directory."""
    assert get_common_ancestor("/a/b/c", "/a/b/d") == Path("/a/b")


def test_is_same_path(tmp_path):
    """is_same_path handles symlinks and normalization."""
    p1 = tmp_path / "file.txt"
    p1.touch()
    p2 = tmp_path / "subdir" / ".." / "file.txt"
    assert is_same_path(p1, p2) is True


def test_sanitize_path():
    """sanitize_path replaces illegal characters."""
    assert sanitize_path("file:with*illegal?chars.txt") == "file_with_illegal_chars.txt"
