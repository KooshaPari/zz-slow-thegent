"""Tests for FileIndex — fd-style file indexing with TTL cache.

Traces to: FR-PERF-001 (file indexing), FR-CACHE-001 (TTL caching)
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from thegent.indexing import FileIndex
from thegent.indexing.file_index import _DEFAULT_EXCLUDE_DIRS, _DEFAULT_TTL

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """Create a small but representative directory tree for testing.

    Structure::

        root/
          src/
            main.py
            utils.py
            sub/
              helper.py
          tests/
            test_main.py
          README.md
          config.toml
          .git/              <- excluded dir
            HEAD
          __pycache__/       <- excluded dir
            cache.pyc
          node_modules/      <- excluded dir
            pkg/
              index.js
    """
    (tmp_path / "src" / "sub").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / ".git").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "node_modules" / "pkg").mkdir(parents=True)

    (tmp_path / "src" / "main.py").write_text("# main")
    (tmp_path / "src" / "utils.py").write_text("# utils")
    (tmp_path / "src" / "sub" / "helper.py").write_text("# helper")
    (tmp_path / "tests" / "test_main.py").write_text("# tests")
    (tmp_path / "README.md").write_text("# readme")
    (tmp_path / "config.toml").write_text("[tool]")
    # Files inside excluded dirs (should NOT appear in index)
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main")
    (tmp_path / "__pycache__" / "cache.pyc").write_bytes(b"")
    (tmp_path / "node_modules" / "pkg" / "index.js").write_text("module.exports={}")

    return tmp_path


# ---------------------------------------------------------------------------
# Build tests
# ---------------------------------------------------------------------------

# Number of Python files in the fixture tree
FIXTURE_PY_COUNT = 4
# Number of files in the fixture that live in two sibling dirs
SIBLING_FILE_COUNT = 2


class TestBuild:
    """Traces to: FR-PERF-001"""

    def test_build_returns_list_of_paths(self, tree: Path) -> None:
        idx = FileIndex()
        result = idx.build(tree)
        assert isinstance(result, list)
        assert all(isinstance(p, Path) for p in result)

    def test_build_finds_all_non_excluded_files(self, tree: Path) -> None:
        idx = FileIndex()
        result = idx.build(tree)
        names = {p.name for p in result}
        assert "main.py" in names
        assert "utils.py" in names
        assert "helper.py" in names
        assert "test_main.py" in names
        assert "README.md" in names
        assert "config.toml" in names

    def test_build_excludes_default_dirs(self, tree: Path) -> None:
        idx = FileIndex()
        result = idx.build(tree)
        paths_str = [str(p) for p in result]
        # No file from .git, __pycache__, or node_modules should appear
        assert not any(".git" + os.sep in s for s in paths_str)
        assert not any("__pycache__" + os.sep in s for s in paths_str)
        assert not any("node_modules" + os.sep in s for s in paths_str)

    def test_build_custom_exclude_dirs(self, tree: Path) -> None:
        """Custom exclusion set should override defaults."""
        idx = FileIndex()
        # Only exclude .git; allow __pycache__ and node_modules
        result = idx.build(tree, exclude_dirs={".git"})
        names = {p.name for p in result}
        assert "cache.pyc" in names  # __pycache__ now included
        assert "index.js" in names  # node_modules now included
        assert "HEAD" not in names  # .git still excluded

    def test_build_result_is_cached(self, tree: Path) -> None:
        idx = FileIndex()
        first = idx.build(tree)
        second = idx.build(tree)
        assert first is second  # same list object from cache

    def test_build_force_rebuilds(self, tree: Path) -> None:
        idx = FileIndex()
        first = idx.build(tree)
        second = idx.build(tree, force=True)
        # Content equal but not the same object (rebuilt)
        assert set(first) == set(second)
        assert first is not second


# ---------------------------------------------------------------------------
# find (glob pattern) tests
# ---------------------------------------------------------------------------


class TestFind:
    """Traces to: FR-PERF-001"""

    def test_find_glob_extension(self, tree: Path) -> None:
        idx = FileIndex()
        idx.build(tree)
        py_files = idx.find("*.py", root=tree)
        names = {p.name for p in py_files}
        assert "main.py" in names
        assert "utils.py" in names
        assert "helper.py" in names
        assert "test_main.py" in names
        assert "README.md" not in names

    def test_find_no_matches(self, tree: Path) -> None:
        idx = FileIndex()
        idx.build(tree)
        result = idx.find("*.rs", root=tree)
        assert result == []

    def test_find_builds_on_demand(self, tree: Path) -> None:
        """find() should build the index automatically if not yet built."""
        idx = FileIndex()
        # Do NOT call build() first
        result = idx.find("*.toml", root=tree)
        assert any(p.name == "config.toml" for p in result)


# ---------------------------------------------------------------------------
# find_by_name tests
# ---------------------------------------------------------------------------


class TestFindByName:
    """Traces to: FR-PERF-001"""

    def test_find_by_name_exact_match(self, tree: Path) -> None:
        idx = FileIndex()
        idx.build(tree)
        result = idx.find_by_name("main.py", root=tree)
        assert len(result) == 1
        assert result[0].name == "main.py"

    def test_find_by_name_no_match(self, tree: Path) -> None:
        idx = FileIndex()
        idx.build(tree)
        result = idx.find_by_name("nonexistent.py", root=tree)
        assert result == []

    def test_find_by_name_multiple_matches(self, tmp_path: Path) -> None:
        """Multiple files with the same name in different dirs should all match."""
        for subdir in ("a", "b"):
            (tmp_path / subdir).mkdir()
            (tmp_path / subdir / "common.txt").write_text("x")
        idx = FileIndex()
        result = idx.find_by_name("common.txt", root=tmp_path)
        assert len(result) == SIBLING_FILE_COUNT


# ---------------------------------------------------------------------------
# find_by_ext tests
# ---------------------------------------------------------------------------


class TestFindByExt:
    """Traces to: FR-PERF-001"""

    def test_find_by_ext_with_dot(self, tree: Path) -> None:
        idx = FileIndex()
        idx.build(tree)
        result = idx.find_by_ext(".py", root=tree)
        assert all(p.suffix == ".py" for p in result)
        assert len(result) == FIXTURE_PY_COUNT

    def test_find_by_ext_without_dot(self, tree: Path) -> None:
        """Extension without leading dot should produce identical results."""
        idx = FileIndex()
        idx.build(tree)
        with_dot = idx.find_by_ext(".md", root=tree)
        without_dot = idx.find_by_ext("md", root=tree)
        assert set(with_dot) == set(without_dot)

    def test_find_by_ext_toml(self, tree: Path) -> None:
        idx = FileIndex()
        idx.build(tree)
        result = idx.find_by_ext(".toml", root=tree)
        assert len(result) == 1
        assert result[0].name == "config.toml"

    def test_find_by_ext_no_match(self, tree: Path) -> None:
        idx = FileIndex()
        idx.build(tree)
        result = idx.find_by_ext(".xyz", root=tree)
        assert result == []


# ---------------------------------------------------------------------------
# TTL / cache invalidation tests
# ---------------------------------------------------------------------------


class TestTTL:
    """Traces to: FR-CACHE-001"""

    def test_is_cached_after_build(self, tree: Path) -> None:
        idx = FileIndex()
        assert not idx.is_cached(tree)
        idx.build(tree)
        assert idx.is_cached(tree)

    def test_invalidate_specific_root(self, tree: Path) -> None:
        idx = FileIndex()
        idx.build(tree)
        idx.invalidate(tree)
        assert not idx.is_cached(tree)

    def test_invalidate_all(self, tmp_path: Path) -> None:
        root_a = tmp_path / "a"
        root_b = tmp_path / "b"
        root_a.mkdir()
        root_b.mkdir()
        (root_a / "f.txt").write_text("a")
        (root_b / "f.txt").write_text("b")

        idx = FileIndex()
        idx.build(root_a)
        idx.build(root_b)
        assert idx.is_cached(root_a)
        assert idx.is_cached(root_b)

        idx.invalidate()  # clear all
        assert not idx.is_cached(root_a)
        assert not idx.is_cached(root_b)

    def test_ttl_expiry(self, tree: Path) -> None:
        """Index should expire after TTL seconds."""
        idx = FileIndex(ttl=1)  # 1-second TTL
        idx.build(tree)
        assert idx.is_cached(tree)

        time.sleep(1.1)  # Wait for TTL to expire
        assert not idx.is_cached(tree)

    def test_env_ttl_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """THGENT_FILE_INDEX_TTL env var should set the TTL."""
        monkeypatch.setenv("THGENT_FILE_INDEX_TTL", "1")
        from thegent.indexing.file_index import _get_ttl

        assert _get_ttl() == 1

    def test_env_ttl_invalid_falls_back_to_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("THGENT_FILE_INDEX_TTL", "not_a_number")
        from thegent.indexing.file_index import _get_ttl

        assert _get_ttl() == _DEFAULT_TTL


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Traces to: FR-PERF-001"""

    def test_empty_directory(self, tmp_path: Path) -> None:
        idx = FileIndex()
        result = idx.build(tmp_path)
        assert result == []

    def test_only_excluded_dirs(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "HEAD").write_text("ref")
        idx = FileIndex()
        result = idx.build(tmp_path)
        assert result == []

    def test_deeply_nested_files(self, tmp_path: Path) -> None:
        deep = tmp_path / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)
        (deep / "deep.py").write_text("x")
        idx = FileIndex()
        result = idx.build(tmp_path)
        assert any(p.name == "deep.py" for p in result)

    def test_default_exclude_dirs_contains_expected(self) -> None:
        """Sanity check the default exclusion set."""
        assert ".git" in _DEFAULT_EXCLUDE_DIRS
        assert "__pycache__" in _DEFAULT_EXCLUDE_DIRS
        assert ".venv" in _DEFAULT_EXCLUDE_DIRS
        assert "node_modules" in _DEFAULT_EXCLUDE_DIRS
