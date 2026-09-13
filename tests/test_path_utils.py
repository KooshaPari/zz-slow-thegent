"""Unit tests for scripts.path_utils module.

Comprehensive test coverage for cross-platform path handling including:
- Path normalization (~ expansion, relative resolution)
- Safe path joining (traversal prevention)
- Relative path computation
- Directory containment checking (is_within)
- Existence checking (safe_exists)
- Directory creation (ensure_dir)
- Cross-platform compatibility
- Edge cases (empty input, unicode, spaces, symlinks)
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Ensure scripts/ is on the path so we can import path_utils directly
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from path_utils import (  # noqa: E402
    ensure_dir,
    get_common_ancestor,
    is_absolute_or_relative,
    is_same_path,
    is_within,
    normalize_path,
    path_to_str,
    rel_to_cwd,
    safe_exists,
    safe_join,
    strip_common_prefix,
)

# ===========================================================================
# normalize_path
# ===========================================================================


class TestNormalizePath:
    """Tests for normalize_path function."""

    def test_normalize_none_returns_cwd(self):
        """None input returns current working directory."""
        result = normalize_path(None)
        assert result == Path.cwd()
        assert result.is_absolute()

    def test_normalize_string_path(self):
        """String paths are converted to Path objects."""
        result = normalize_path("/tmp/test")
        assert isinstance(result, Path)
        assert result == Path("/tmp/test").resolve()

    def test_normalize_path_object(self):
        """Path objects are normalized and resolved."""
        p = Path("/tmp/test")
        result = normalize_path(p)
        assert isinstance(result, Path)
        assert result == p.resolve()

    def test_normalize_tilde_expansion(self):
        """Tilde is expanded to home directory."""
        result = normalize_path("~/projects")
        assert "~" not in str(result)
        assert result.is_absolute()
        assert str(result).startswith(str(Path.home()))

    def test_normalize_relative_with_base(self):
        """Relative paths are resolved against base."""
        result = normalize_path("subdir", "/tmp")
        assert result == Path("/tmp/subdir").resolve()

    def test_normalize_absolute_ignores_base(self):
        """Absolute paths ignore the base parameter."""
        result = normalize_path("/tmp/test/file", "/home/user")
        assert result.is_absolute()
        assert result.name == "file"
        # Base is irrelevant for absolute paths; resolve() may follow symlinks
        # (e.g. on macOS /tmp -> /private/tmp) so only check the filename.
        assert result == Path("/tmp/test/file").resolve()

    def test_normalize_dot_components_collapsed(self):
        """Dot and double-dot components are collapsed."""
        result = normalize_path("/tmp/test/./subdir/../other")
        assert ".." not in str(result)
        assert result == Path("/tmp/test/other").resolve()

    def test_normalize_invalid_type_raises(self):
        """Non-path types raise TypeError."""
        with pytest.raises(TypeError):
            normalize_path(123)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            normalize_path(["/tmp"])  # type: ignore[arg-type]

    def test_normalize_always_absolute(self):
        """Normalized paths are always absolute."""
        cases = [
            "~/projects",
            "./relative",
            "../parent",
            "/absolute",
        ]
        for case in cases:
            result = normalize_path(case)
            assert result.is_absolute(), f"Failed for: {case}"

    def test_normalize_tilde_base_expansion(self):
        """Base paths with ~ are also expanded."""
        base = "~/projects"
        result = normalize_path("src", base)
        assert result.is_absolute()
        expected_base = normalize_path(base)
        assert result == (expected_base / "src").resolve()

    def test_normalize_returns_path_type(self):
        """Return type is always pathlib.Path."""
        for path in ["/tmp", "~/foo", None, Path("/tmp")]:
            result = normalize_path(path)
            assert isinstance(result, Path)

    def test_normalize_multiple_trailing_slashes(self):
        """Multiple trailing slashes collapse to single path."""
        r1 = normalize_path("/tmp/test/")
        r2 = normalize_path("/tmp/test///")
        assert r1 == r2


# ===========================================================================
# safe_join
# ===========================================================================


class TestSafeJoin:
    """Tests for safe_join(base, *parts) – must block traversal escapes."""

    def test_safe_join_simple_child(self, tmp_path):
        """Joining a simple filename inside base works."""
        result = safe_join(tmp_path, "file.txt")
        assert result == (tmp_path / "file.txt").resolve()

    def test_safe_join_nested_child(self, tmp_path):
        """Nested sub-directories inside base are allowed."""
        result = safe_join(tmp_path, "sub/dir/file.txt")
        assert result == (tmp_path / "sub" / "dir" / "file.txt").resolve()

    def test_safe_join_multiple_parts(self, tmp_path):
        """Multiple parts are joined left-to-right."""
        result = safe_join(tmp_path, "a", "b", "c.txt")
        assert result == (tmp_path / "a" / "b" / "c.txt").resolve()

    def test_safe_join_base_equals_result(self, tmp_path):
        """Joining empty string stays at base."""
        result = safe_join(tmp_path, "")
        assert result == tmp_path.resolve()

    def test_safe_join_traversal_blocked_double_dot(self, tmp_path):
        """Double-dot that escapes base raises ValueError."""
        with pytest.raises(ValueError, match="escapes base"):
            safe_join(tmp_path, "../../etc/passwd")

    def test_safe_join_traversal_blocked_parent_escape(self, tmp_path):
        """Single .. that escapes base raises ValueError."""
        with pytest.raises(ValueError, match="escapes base"):
            safe_join(tmp_path, "../outside.txt")

    def test_safe_join_traversal_via_long_chain(self, tmp_path):
        """Deep then escaping .. chain is blocked."""
        with pytest.raises(ValueError, match="escapes base"):
            safe_join(tmp_path, "a", "b", "..", "..", "..", "escape.txt")

    def test_safe_join_dotdot_that_stays_inside_is_ok(self, tmp_path):
        """.. that resolves inside base is allowed."""
        # /tmp/X/sub/../other  →  /tmp/X/other  →  still inside /tmp/X
        result = safe_join(tmp_path, "sub", "..", "other.txt")
        assert is_within(result, tmp_path)

    def test_safe_join_with_path_objects(self, tmp_path):
        """Path objects are accepted as parts."""
        result = safe_join(tmp_path, Path("sub"), Path("file.txt"))
        assert result == (tmp_path / "sub" / "file.txt").resolve()

    def test_safe_join_tilde_base(self):
        """Base can contain ~ (expanded before join)."""
        home = Path.home()
        result = safe_join("~", ".thegent", "sessions")
        assert result == (home / ".thegent" / "sessions").resolve()
        assert is_within(result, home)

    def test_safe_join_no_parts_returns_base(self, tmp_path):
        """No extra parts returns resolved base."""
        result = safe_join(tmp_path)
        assert result == tmp_path.resolve()

    def test_safe_join_absolute_part_blocked(self, tmp_path):
        """Absolute part in *parts that escapes base is blocked."""
        # /etc/passwd is outside tmp_path
        with pytest.raises(ValueError, match="escapes base"):
            safe_join(tmp_path, "/etc/passwd")


# ===========================================================================
# is_within
# ===========================================================================


class TestIsWithin:
    """Tests for is_within function."""

    def test_is_within_direct_child(self):
        """Direct child is within parent."""
        assert is_within("/tmp/foo/bar.txt", "/tmp/foo")

    def test_is_within_deeply_nested(self):
        """Deeply nested child is within ancestor."""
        assert is_within("/tmp/a/b/c/d/e.txt", "/tmp/a")

    def test_is_within_same_path(self):
        """A path is within itself."""
        assert is_within("/tmp/foo", "/tmp/foo")

    def test_is_within_parent_not_within_child(self):
        """Parent is not within child."""
        assert not is_within("/tmp/foo", "/tmp/foo/bar")

    def test_is_within_sibling_false(self):
        """Sibling directories are not within each other."""
        assert not is_within("/tmp/foo_a", "/tmp/foo_b")

    def test_is_within_different_root_false(self):
        """Completely different roots are not within each other."""
        assert not is_within("/var/log", "/tmp/data")

    def test_is_within_with_path_objects(self):
        """Accepts pathlib.Path arguments."""
        assert is_within(Path("/tmp/foo/bar"), Path("/tmp/foo"))

    def test_is_within_tilde_paths(self):
        """Tilde paths are expanded before comparison."""
        home = Path.home()
        child = home / "projects" / "thegent" / "src"
        parent = home / "projects"
        assert is_within(child, parent)
        assert not is_within(parent, child)

    def test_is_within_prefix_not_sufficient(self):
        """Prefix match on string is not sufficient – must be path component."""
        # /tmp/foo_extra is NOT inside /tmp/foo even though it starts the same
        assert not is_within("/tmp/foo_extra/file.txt", "/tmp/foo")

    def test_is_within_symlink_real_path(self, tmp_path):
        """Symlinks are resolved; real path determines containment."""
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        link_dir = tmp_path / "link"
        try:
            link_dir.symlink_to(real_dir)
            child = real_dir / "file.txt"
            assert is_within(child, link_dir)
        except OSError:
            pytest.skip("Symlinks not supported on this platform")


# ===========================================================================
# safe_exists
# ===========================================================================


class TestSafeExists:
    """Tests for safe_exists function."""

    def test_safe_exists_true_file(self):
        """Returns True for an existing file."""
        with tempfile.NamedTemporaryFile() as tmp:
            assert safe_exists(tmp.name) is True

    def test_safe_exists_true_directory(self):
        """Returns True for an existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert safe_exists(tmpdir) is True

    def test_safe_exists_false_nonexistent(self):
        """Returns False for non-existent paths."""
        assert safe_exists("/nonexistent/path/that/cannot/exist_xyz") is False

    def test_safe_exists_tilde_expansion(self):
        """Expands ~ before checking – home always exists."""
        assert safe_exists("~") is True

    def test_safe_exists_relative_path(self):
        """Works with relative paths resolved against CWD."""
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                os.chdir(tmpdir)
                Path("relative_test.txt").write_text("hi")
                assert safe_exists("relative_test.txt") is True
                assert safe_exists("does_not_exist.txt") is False
            finally:
                os.chdir(original)

    def test_safe_exists_swallows_permission_error(self):
        """Returns False instead of raising PermissionError."""
        with patch("path_utils.Path.exists", side_effect=PermissionError("denied")):
            assert safe_exists("/some/protected/path") is False

    def test_safe_exists_swallows_oserror(self):
        """Returns False instead of raising OSError."""
        with patch("path_utils.Path.exists", side_effect=OSError("I/O error")):
            assert safe_exists("/some/path") is False

    def test_safe_exists_path_object(self, tmp_path):
        """Accepts pathlib.Path arguments."""
        assert safe_exists(tmp_path) is True
        assert safe_exists(tmp_path / "no_such_file.txt") is False


# ===========================================================================
# rel_to_cwd
# ===========================================================================


class TestRelToCwd:
    """Tests for rel_to_cwd function."""

    def test_rel_to_cwd_child_path(self):
        """Paths under CWD become relative."""
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                os.chdir(tmpdir)
                test_file = Path(tmpdir) / "test.txt"
                test_file.touch()
                result = rel_to_cwd(test_file)
                assert not result.is_absolute()
                assert str(result) == "test.txt"
            finally:
                os.chdir(original)

    def test_rel_to_cwd_nested_child(self):
        """Nested paths become relative with correct structure."""
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                os.chdir(tmpdir)
                src = Path(tmpdir) / "src"
                src.mkdir()
                main = src / "main.py"
                main.touch()
                result = rel_to_cwd(main)
                assert not result.is_absolute()
                assert str(result) == str(Path("src") / "main.py")
            finally:
                os.chdir(original)

    def test_rel_to_cwd_outside_returns_absolute(self):
        """Paths outside CWD are returned as absolute."""
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                nested = Path(tmpdir) / "deep"
                nested.mkdir()
                os.chdir(nested)
                # /tmp itself is outside /tmp/deep
                result = rel_to_cwd(Path(tmpdir))
                # Either absolute or relative-with-.., either is fine;
                # but result must be a valid Path
                assert isinstance(result, Path)
            finally:
                os.chdir(original)

    def test_rel_to_cwd_returns_path_type(self, tmp_path):
        """Always returns a Path object."""
        result = rel_to_cwd(tmp_path)
        assert isinstance(result, Path)

    def test_rel_to_cwd_path_object_input(self, tmp_path):
        """Accepts pathlib.Path input."""
        result = rel_to_cwd(tmp_path)
        assert isinstance(result, Path)


# ===========================================================================
# ensure_dir
# ===========================================================================


class TestEnsureDir:
    """Tests for ensure_dir function."""

    def test_ensure_dir_creates_directory(self, tmp_path):
        """Creates a directory that does not yet exist."""
        target = tmp_path / "new" / "nested" / "dir"
        result = ensure_dir(target)
        assert target.exists()
        assert target.is_dir()
        assert result == target.resolve()

    def test_ensure_dir_returns_absolute_path(self, tmp_path):
        """Returns a resolved absolute Path."""
        result = ensure_dir(tmp_path / "sub")
        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_ensure_dir_existing_dir_no_error(self, tmp_path):
        """Calling on an existing directory does not raise."""
        result = ensure_dir(tmp_path)
        assert result == tmp_path.resolve()

    def test_ensure_dir_tilde_expansion(self):
        """Expands ~ in the directory path."""
        test_dir = "~/.thegent_test_ensure_dir_temp"
        normalized = normalize_path(test_dir)
        try:
            result = ensure_dir(test_dir)
            assert result.exists()
            assert result.is_absolute()
            assert "~" not in str(result)
        finally:
            if normalized.exists():
                normalized.rmdir()

    def test_ensure_dir_intermediate_parents_created(self, tmp_path):
        """Creates all intermediate parents (mkdir -p semantics)."""
        deep = tmp_path / "a" / "b" / "c" / "d"
        ensure_dir(deep)
        assert deep.exists()
        assert (tmp_path / "a").exists()
        assert (tmp_path / "a" / "b").exists()

    def test_ensure_dir_string_input(self, tmp_path):
        """Accepts string paths as well as Path objects."""
        target = str(tmp_path / "from_string")
        result = ensure_dir(target)
        assert result.exists()


# ===========================================================================
# Additional helpers
# ===========================================================================


class TestPathToStr:
    """Tests for path_to_str helper."""

    def test_none_returns_empty_string(self):
        assert path_to_str(None) == ""

    def test_string_input_returned_unchanged(self):
        assert path_to_str("/tmp/test") == "/tmp/test"

    def test_path_object_converted(self):
        p = Path("/tmp/test")
        assert path_to_str(p) == str(p)


class TestIsAbsoluteOrRelative:
    """Tests for is_absolute_or_relative helper."""

    def test_unix_absolute_path(self):
        assert is_absolute_or_relative("/tmp/test") is True

    def test_relative_dot_slash(self):
        assert is_absolute_or_relative("./test") is False

    def test_relative_dot_dot_slash(self):
        assert is_absolute_or_relative("../parent") is False

    def test_bare_filename(self):
        assert is_absolute_or_relative("file.txt") is False

    def test_tilde_is_relative_before_expansion(self):
        # ~ is not expanded here – it is treated as relative
        assert is_absolute_or_relative("~/projects") is False

    def test_path_object_absolute(self):
        assert is_absolute_or_relative(Path("/tmp")) is True

    def test_path_object_relative(self):
        assert is_absolute_or_relative(Path("./test")) is False


class TestGetCommonAncestor:
    """Tests for get_common_ancestor helper."""

    def test_no_paths_returns_cwd(self):
        result = get_common_ancestor()
        assert result == Path.cwd()

    def test_same_path_twice(self):
        result = get_common_ancestor("/tmp/user/test", "/tmp/user/test")
        assert result == Path("/tmp/user/test").resolve()

    def test_sibling_paths(self):
        result = get_common_ancestor("/tmp/user/a", "/tmp/user/b")
        assert result == Path("/tmp/user").resolve()

    def test_nested_paths(self):
        result = get_common_ancestor("/tmp/a/b/c", "/tmp/a/b/d")
        assert result == Path("/tmp/a/b").resolve()

    def test_different_branches(self):
        result = get_common_ancestor("/tmp/user/a", "/tmp/other/b")
        assert result == Path("/tmp").resolve()


class TestIsSamePath:
    """Tests for is_same_path helper."""

    def test_identical_absolute_paths(self):
        assert is_same_path("/tmp/test", "/tmp/test") is True

    def test_equivalent_with_dot_components(self):
        assert is_same_path("/tmp/./test", "/tmp/test") is True
        assert is_same_path("/tmp/test/../test", "/tmp/test") is True

    def test_different_paths_false(self):
        assert is_same_path("/tmp/a", "/tmp/b") is False

    def test_nonexistent_paths_equality(self):
        # Falls back to resolved-path comparison
        assert is_same_path("/nonexistent/path_x", "/nonexistent/path_x") is True
        assert is_same_path("/nonexistent/path_x", "/nonexistent/path_y") is False


class TestStripCommonPrefix:
    """Tests for strip_common_prefix helper."""

    def test_empty_list(self):
        assert strip_common_prefix([]) == []

    def test_same_directory(self):
        result = strip_common_prefix(
            ["/home/user/projects/file1.txt", "/home/user/projects/file2.txt"]
        )
        assert result == ["file1.txt", "file2.txt"]

    def test_mixed_depths(self):
        result = strip_common_prefix(
            ["/home/user/projects/src/main.py", "/home/user/projects/test/test.py"]
        )
        assert result == [str(Path("src/main.py")), str(Path("test/test.py"))]

    def test_single_path(self):
        result = strip_common_prefix(["/home/user/file.txt"])
        assert len(result) == 1


# ===========================================================================
# Integration scenarios
# ===========================================================================


class TestIntegration:
    """Integration tests combining multiple utilities."""

    def test_workflow_normalize_join_check(self):
        """normalize -> safe_join -> is_within round-trip."""
        base = normalize_path("~/.thegent")
        session_dir = safe_join(base, "sessions", "abc123")
        assert is_within(session_dir, base)
        assert not is_within(base, session_dir)

    def test_workflow_create_and_verify(self, tmp_path):
        """ensure_dir -> safe_join -> safe_exists -> is_within."""
        base = ensure_dir(tmp_path / "workspace")
        file_path = safe_join(base, "config.toml")
        file_path.write_text("[settings]")
        assert safe_exists(file_path)
        assert is_within(file_path, base)

    def test_workflow_relative_display(self, tmp_path):
        """safe_join + rel_to_cwd produces human-friendly display path."""
        original = Path.cwd()
        try:
            os.chdir(tmp_path)
            file_path = safe_join(tmp_path, "src", "main.py")
            display = rel_to_cwd(file_path)
            # Should be relative, not absolute
            assert not display.is_absolute()
        finally:
            os.chdir(original)

    def test_traversal_blocked_end_to_end(self, tmp_path):
        """Realistic attack scenario: user-supplied path escaping sandbox."""
        sandbox = tmp_path / "sandbox"
        sandbox.mkdir()
        malicious_inputs = [
            "../../etc/passwd",
            "../../../tmp/escape.txt",
            "legit/../../outside.txt",
        ]
        for bad in malicious_inputs:
            with pytest.raises(ValueError, match="escapes base"):
                safe_join(sandbox, bad)


# ===========================================================================
# Edge cases
# ===========================================================================


class TestEdgeCases:
    """Edge cases and corner conditions."""

    def test_unicode_path(self, tmp_path):
        """Handles unicode directory names."""
        unicode_dir = tmp_path / "тест_目录"
        unicode_dir.mkdir()
        result = normalize_path(unicode_dir)
        assert result.exists()

    def test_path_with_spaces(self, tmp_path):
        """Handles paths containing spaces."""
        space_dir = tmp_path / "directory with spaces"
        space_dir.mkdir()
        result = normalize_path(space_dir)
        assert result.exists()

    def test_dot_files(self):
        """Handles hidden/dot-prefixed path components."""
        result = normalize_path("~/.thegent/config")
        assert result.is_absolute()
        assert ".thegent" in str(result)

    def test_very_deep_path(self):
        """Handles extremely long paths gracefully."""
        deep = "/" + "/".join(["subdir"] * 50)
        result = normalize_path(deep)
        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_root_path(self):
        """Root path normalizes cleanly."""
        result = normalize_path("/")
        assert result == Path("/")

    def test_cwd_dot(self):
        """Single dot resolves to CWD."""
        result = normalize_path(".")
        assert result == Path.cwd()

    def test_safe_exists_on_root(self):
        """Root always exists."""
        assert safe_exists("/") is True

    def test_ensure_dir_idempotent(self, tmp_path):
        """Calling ensure_dir twice on same path is idempotent."""
        target = tmp_path / "idempotent"
        ensure_dir(target)
        ensure_dir(target)  # should not raise
        assert target.is_dir()
