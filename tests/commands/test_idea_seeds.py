"""Tests for thegent.commands.idea_seeds — IdeaSeed scanner.

Covers IdeaSeedScanner.scan_file, scan_directory, filter_by_type,
to_work_stream_items, and export_markdown.

Traces to: FR-SEEDS-001 through FR-SEEDS-025
"""

from __future__ import annotations

from pathlib import Path

from thegent.commands.idea_seeds import (
    DEFAULT_EXTENSIONS,
    SEED_PATTERNS,
    IdeaSeed,
    IdeaSeedScanner,
    _make_slug,
    _priority_for_type,
    _try_relative,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write(tmp_path: Path, filename: str, content: str) -> Path:
    """Write content to a file and return its path."""
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# IdeaSeed dataclass
# ---------------------------------------------------------------------------


class TestIdeaSeedDataclass:
    """FR-SEEDS-001: IdeaSeed serialises correctly."""

    def test_to_dict_contains_all_keys(self, tmp_path: Path) -> None:
        seed = IdeaSeed(
            file=tmp_path / "foo.py",
            line=42,
            pattern_type="TODO",
            content="add caching here",
            context="line A\nline B",
        )
        d = seed.to_dict()
        assert set(d.keys()) == {"file", "line", "pattern_type", "content", "context"}

    def test_to_dict_file_is_string(self, tmp_path: Path) -> None:
        seed = IdeaSeed(file=tmp_path / "x.py", line=1, pattern_type="IDEA", content="x")
        d = seed.to_dict()
        assert isinstance(d["file"], str)

    def test_context_defaults_to_empty_string(self, tmp_path: Path) -> None:
        seed = IdeaSeed(file=tmp_path / "x.py", line=1, pattern_type="IDEA", content="y")
        assert seed.context == ""


# ---------------------------------------------------------------------------
# scan_file
# ---------------------------------------------------------------------------


class TestScanFile:
    """FR-SEEDS-002 through FR-SEEDS-010: Single-file scanning."""

    def test_finds_idea_pattern(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-002
        p = _write(tmp_path, "a.py", "x = 1\n# IDEA: add streaming support\ny = 2\n")
        seeds = IdeaSeedScanner().scan_file(p)
        assert len(seeds) == 1
        assert seeds[0].pattern_type == "IDEA"
        assert "streaming" in seeds[0].content

    def test_finds_todo_pattern(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-003
        p = _write(tmp_path, "b.py", "# TODO: refactor this\n")
        seeds = IdeaSeedScanner().scan_file(p)
        assert len(seeds) == 1
        assert seeds[0].pattern_type == "TODO"

    def test_finds_fixme_pattern(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-004
        p = _write(tmp_path, "c.py", "# FIXME: broken edge case\n")
        seeds = IdeaSeedScanner().scan_file(p)
        assert len(seeds) == 1
        assert seeds[0].pattern_type == "FIXME"

    def test_finds_refactor_pattern(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-005
        p = _write(tmp_path, "d.py", "# REFACTOR: split into helper\n")
        seeds = IdeaSeedScanner().scan_file(p)
        assert seeds[0].pattern_type == "REFACTOR"

    def test_finds_hack_pattern(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-006
        p = _write(tmp_path, "e.py", "# HACK: workaround for upstream bug\n")
        seeds = IdeaSeedScanner().scan_file(p)
        assert seeds[0].pattern_type == "HACK"

    def test_finds_seed_pattern(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-007
        p = _write(tmp_path, "f.py", "# SEED: explore event sourcing\n")
        seeds = IdeaSeedScanner().scan_file(p)
        assert seeds[0].pattern_type == "SEED"

    def test_finds_improve_pattern(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-008
        p = _write(tmp_path, "g.py", "# IMPROVE: use binary search\n")
        seeds = IdeaSeedScanner().scan_file(p)
        assert seeds[0].pattern_type == "IMPROVE"

    def test_js_slash_todo(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-009
        p = _write(tmp_path, "h.ts", "// TODO: add rate limiting\n")
        seeds = IdeaSeedScanner().scan_file(p)
        assert len(seeds) == 1
        assert seeds[0].pattern_type == "TODO"

    def test_js_slash_idea(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-010
        p = _write(tmp_path, "i.ts", "// IDEA: lazy evaluation\n")
        seeds = IdeaSeedScanner().scan_file(p)
        assert seeds[0].pattern_type == "IDEA"

    def test_line_number_is_correct(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-011
        p = _write(tmp_path, "j.py", "a = 1\nb = 2\n# TODO: fix this\nc = 3\n")
        seeds = IdeaSeedScanner().scan_file(p)
        assert seeds[0].line == 3

    def test_context_captured(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-012
        p = _write(tmp_path, "k.py", "line1\nline2\n# TODO: do it\nline4\nline5\n")
        seeds = IdeaSeedScanner().scan_file(p)
        assert "line1" in seeds[0].context or "line2" in seeds[0].context
        assert "line4" in seeds[0].context

    def test_multiple_seeds_in_one_file(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-013
        p = _write(tmp_path, "l.py", "# TODO: first\n# IDEA: second\n# FIXME: third\n")
        seeds = IdeaSeedScanner().scan_file(p)
        assert len(seeds) == 3

    def test_no_seeds_returns_empty(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "m.py", "x = 1\ny = 2\n")
        seeds = IdeaSeedScanner().scan_file(p)
        assert seeds == []

    def test_file_path_is_absolute(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "n.py", "# IDEA: something\n")
        seeds = IdeaSeedScanner().scan_file(p)
        assert seeds[0].file.is_absolute()

    def test_content_stripped(self, tmp_path: Path) -> None:
        p = _write(tmp_path, "o.py", "#   TODO:   lots of spaces   \n")
        seeds = IdeaSeedScanner().scan_file(p)
        assert seeds[0].content == "lots of spaces"

    def test_nonexistent_file_returns_empty(self, tmp_path: Path) -> None:
        scanner = IdeaSeedScanner()
        result = scanner.scan_file(tmp_path / "does_not_exist.py")
        assert result == []


# ---------------------------------------------------------------------------
# scan_directory
# ---------------------------------------------------------------------------


class TestScanDirectory:
    """FR-SEEDS-014 through FR-SEEDS-016: Recursive directory scanning."""

    def test_scan_directory_recursive(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-014
        sub = tmp_path / "sub"
        sub.mkdir()
        _write(sub, "deep.py", "# IDEA: deep\n")
        seeds = IdeaSeedScanner().scan_directory(tmp_path)
        assert any("deep" in s.content for s in seeds)

    def test_scan_directory_extension_filter(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-015
        _write(tmp_path, "a.py", "# TODO: python seed\n")
        _write(tmp_path, "b.js", "// TODO: js seed\n")
        seeds = IdeaSeedScanner().scan_directory(tmp_path, extensions=[".py"])
        assert all(s.file.suffix == ".py" for s in seeds)

    def test_scan_directory_skips_hidden(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-016
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        _write(hidden, "secret.py", "# TODO: should not appear\n")
        _write(tmp_path, "visible.py", "# TODO: should appear\n")
        seeds = IdeaSeedScanner().scan_directory(tmp_path)
        assert all(".hidden" not in str(s.file) for s in seeds)

    def test_non_directory_returns_empty(self, tmp_path: Path) -> None:
        not_a_dir = tmp_path / "not_a_dir.txt"
        not_a_dir.write_text("hello")
        seeds = IdeaSeedScanner().scan_directory(not_a_dir)
        assert seeds == []

    def test_default_extensions_used_when_none(self, tmp_path: Path) -> None:
        _write(tmp_path, "x.py", "# IDEA: python\n")
        _write(tmp_path, "y.xyz", "# IDEA: unknown ext\n")
        seeds = IdeaSeedScanner().scan_directory(tmp_path, extensions=None)
        assert any(s.file.name == "x.py" for s in seeds)
        assert all(s.file.name != "y.xyz" for s in seeds)


# ---------------------------------------------------------------------------
# filter_by_type
# ---------------------------------------------------------------------------


class TestFilterByType:
    """FR-SEEDS-017: filter_by_type preserves only matching seeds."""

    def _make_seeds(self, tmp_path: Path) -> list[IdeaSeed]:
        return [
            IdeaSeed(file=tmp_path / "a.py", line=1, pattern_type="TODO", content="x"),
            IdeaSeed(file=tmp_path / "b.py", line=2, pattern_type="IDEA", content="y"),
            IdeaSeed(file=tmp_path / "c.py", line=3, pattern_type="FIXME", content="z"),
        ]

    def test_filter_single_type(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-017
        scanner = IdeaSeedScanner()
        seeds = self._make_seeds(tmp_path)
        result = scanner.filter_by_type(seeds, ["TODO"])
        assert all(s.pattern_type == "TODO" for s in result)
        assert len(result) == 1

    def test_filter_multiple_types(self, tmp_path: Path) -> None:
        scanner = IdeaSeedScanner()
        seeds = self._make_seeds(tmp_path)
        result = scanner.filter_by_type(seeds, ["TODO", "IDEA"])
        assert {s.pattern_type for s in result} == {"TODO", "IDEA"}

    def test_filter_case_insensitive(self, tmp_path: Path) -> None:
        scanner = IdeaSeedScanner()
        seeds = self._make_seeds(tmp_path)
        result = scanner.filter_by_type(seeds, ["todo"])
        assert len(result) == 1

    def test_filter_empty_types_returns_nothing(self, tmp_path: Path) -> None:
        scanner = IdeaSeedScanner()
        seeds = self._make_seeds(tmp_path)
        result = scanner.filter_by_type(seeds, [])
        assert result == []

    def test_filter_unknown_type_returns_nothing(self, tmp_path: Path) -> None:
        scanner = IdeaSeedScanner()
        seeds = self._make_seeds(tmp_path)
        result = scanner.filter_by_type(seeds, ["BOGUS"])
        assert result == []


# ---------------------------------------------------------------------------
# to_work_stream_items
# ---------------------------------------------------------------------------


class TestToWorkStreamItems:
    """FR-SEEDS-018: to_work_stream_items returns valid WBS-format rows."""

    def _make_seed(self, tmp_path: Path, ptype: str = "TODO", content: str = "do it") -> IdeaSeed:
        return IdeaSeed(file=(tmp_path / "a.py").resolve(), line=1, pattern_type=ptype, content=content)

    def test_returns_list_of_dicts(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-018
        scanner = IdeaSeedScanner()
        rows = scanner.to_work_stream_items([self._make_seed(tmp_path)])
        assert isinstance(rows, list)
        assert all(isinstance(r, dict) for r in rows)

    def test_row_has_required_keys(self, tmp_path: Path) -> None:
        scanner = IdeaSeedScanner()
        rows = scanner.to_work_stream_items([self._make_seed(tmp_path)])
        assert set(rows[0].keys()) >= {"id", "title", "source", "priority", "depends"}

    def test_id_contains_pattern_type(self, tmp_path: Path) -> None:
        scanner = IdeaSeedScanner()
        rows = scanner.to_work_stream_items([self._make_seed(tmp_path, ptype="FIXME")])
        assert "fixme" in rows[0]["id"]

    def test_priority_for_fixme_is_p1(self, tmp_path: Path) -> None:
        scanner = IdeaSeedScanner()
        rows = scanner.to_work_stream_items([self._make_seed(tmp_path, ptype="FIXME")])
        assert rows[0]["priority"] == "P1"

    def test_priority_for_idea_is_p3(self, tmp_path: Path) -> None:
        scanner = IdeaSeedScanner()
        rows = scanner.to_work_stream_items([self._make_seed(tmp_path, ptype="IDEA")])
        assert rows[0]["priority"] == "P3"

    def test_empty_seeds_returns_empty_list(self, tmp_path: Path) -> None:
        scanner = IdeaSeedScanner()
        assert scanner.to_work_stream_items([]) == []


# ---------------------------------------------------------------------------
# export_markdown
# ---------------------------------------------------------------------------


class TestExportMarkdown:
    """FR-SEEDS-019: export_markdown writes valid markdown."""

    def test_creates_file(self, tmp_path: Path) -> None:
        # @trace FR-SEEDS-019
        scanner = IdeaSeedScanner()
        seed = IdeaSeed(file=tmp_path / "a.py", line=1, pattern_type="TODO", content="do it")
        out = tmp_path / "out" / "seeds.md"
        scanner.export_markdown([seed], out)
        assert out.exists()

    def test_markdown_contains_pattern_type_heading(self, tmp_path: Path) -> None:
        scanner = IdeaSeedScanner()
        seed = IdeaSeed(file=tmp_path / "a.py", line=5, pattern_type="IDEA", content="streaming")
        out = tmp_path / "seeds.md"
        scanner.export_markdown([seed], out)
        content = out.read_text()
        assert "## IDEA" in content

    def test_markdown_contains_seed_content(self, tmp_path: Path) -> None:
        scanner = IdeaSeedScanner()
        seed = IdeaSeed(file=tmp_path / "a.py", line=5, pattern_type="IDEA", content="unique-xyz-content")
        out = tmp_path / "seeds.md"
        scanner.export_markdown([seed], out)
        assert "unique-xyz-content" in out.read_text()

    def test_markdown_groups_by_type(self, tmp_path: Path) -> None:
        scanner = IdeaSeedScanner()
        seeds = [
            IdeaSeed(file=tmp_path / "a.py", line=1, pattern_type="TODO", content="aaa"),
            IdeaSeed(file=tmp_path / "a.py", line=2, pattern_type="IDEA", content="bbb"),
        ]
        out = tmp_path / "seeds.md"
        scanner.export_markdown(seeds, out)
        text = out.read_text()
        assert "## TODO" in text
        assert "## IDEA" in text

    def test_export_empty_seeds_writes_header_only(self, tmp_path: Path) -> None:
        scanner = IdeaSeedScanner()
        out = tmp_path / "seeds.md"
        scanner.export_markdown([], out)
        content = out.read_text()
        assert "# Idea Seeds" in content

    def test_export_creates_parent_dirs(self, tmp_path: Path) -> None:
        scanner = IdeaSeedScanner()
        seed = IdeaSeed(file=tmp_path / "a.py", line=1, pattern_type="TODO", content="x")
        out = tmp_path / "deep" / "nested" / "seeds.md"
        scanner.export_markdown([seed], out)
        assert out.exists()


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


class TestHelpers:
    """FR-SEEDS-020: Helper function correctness."""

    def test_make_slug_basic(self) -> None:
        assert _make_slug("add caching here") == "add-caching-here"

    def test_make_slug_truncates(self) -> None:
        long = "a" * 100
        assert len(_make_slug(long)) <= 40

    def test_priority_fixme(self) -> None:
        assert _priority_for_type("FIXME") == "P1"

    def test_priority_hack(self) -> None:
        assert _priority_for_type("HACK") == "P1"

    def test_priority_todo(self) -> None:
        assert _priority_for_type("TODO") == "P2"

    def test_priority_idea(self) -> None:
        assert _priority_for_type("IDEA") == "P3"

    def test_priority_unknown_defaults_to_p3(self) -> None:
        assert _priority_for_type("BOGUS") == "P3"

    def test_try_relative_returns_relative_when_possible(self, tmp_path: Path) -> None:
        import os

        old_cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            p = tmp_path / "sub" / "file.py"
            result = _try_relative(p)
            assert not result.is_absolute()
        finally:
            os.chdir(old_cwd)

    def test_try_relative_returns_absolute_on_failure(self, tmp_path: Path) -> None:
        p = Path("/some/completely/other/path/file.py")
        result = _try_relative(p)
        # Should not raise; returns a Path (may be absolute)
        assert isinstance(result, Path)

    def test_seed_patterns_list_non_empty(self) -> None:
        assert len(SEED_PATTERNS) > 0

    def test_default_extensions_contains_python(self) -> None:
        assert ".py" in DEFAULT_EXTENSIONS

    def test_default_extensions_contains_typescript(self) -> None:
        assert ".ts" in DEFAULT_EXTENSIONS
