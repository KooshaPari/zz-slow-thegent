"""Tests for the docs typer CLI.

# @trace FR-DOCS-006
"""

from pathlib import Path

from typer.testing import CliRunner

from docs_engine.cli.commands import app

runner = CliRunner()


def test_new_idea_creates_file(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCS_ROOT", str(tmp_path / "docs"))
    monkeypatch.setenv("DOCS_ENGINE_DB", str(tmp_path / "test.db"))
    result = runner.invoke(app, ["new", "idea", "My test idea"])
    assert result.exit_code == 0
    assert "Created" in result.output


def test_search_returns_results(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCS_ROOT", str(tmp_path / "docs"))
    monkeypatch.setenv("DOCS_ENGINE_DB", str(tmp_path / "test.db"))
    runner.invoke(app, ["new", "idea", "Searchable idea"])
    result = runner.invoke(app, ["search", "Searchable"])
    assert result.exit_code == 0
    assert "Searchable" in result.output


def test_index_rebuild(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCS_ROOT", str(tmp_path / "docs"))
    monkeypatch.setenv("DOCS_ENGINE_DB", str(tmp_path / "test.db"))
    # Create a markdown file with frontmatter that can be indexed
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "test.md").write_text(
        "---\ntype: idea\nstatus: draft\ntitle: Rebuild test\nlayer: 1\ndate: 2026-02-21\n---\n\n# Rebuild test\n"
    )
    result = runner.invoke(app, ["index", "rebuild"])
    assert result.exit_code == 0
    assert "Indexed" in result.output


def test_new_unknown_type_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCS_ROOT", str(tmp_path / "docs"))
    monkeypatch.setenv("DOCS_ENGINE_DB", str(tmp_path / "test.db"))
    result = runner.invoke(app, ["new", "not-a-type", "Some title"])
    assert result.exit_code != 0


def test_index_rebuild_reports_malformed_frontmatter(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCS_ROOT", str(tmp_path / "docs"))
    monkeypatch.setenv("DOCS_ENGINE_DB", str(tmp_path / "test.db"))
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "bad.md").write_text("---\ntype: [oops\n---\n# Broken\n", encoding="utf-8")

    result = runner.invoke(app, ["index", "rebuild"])

    assert result.exit_code == 0
    assert "Indexed 0 documents." in result.output
    assert "Skipped 1 files." in result.output
    assert "frontmatter parse error" in result.output
    assert "bad.md" in result.output


def test_index_rebuild_reports_unreadable_markdown(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCS_ROOT", str(tmp_path / "docs"))
    monkeypatch.setenv("DOCS_ENGINE_DB", str(tmp_path / "test.db"))
    docs = tmp_path / "docs"
    docs.mkdir()
    bad_file = docs / "unreadable.md"
    bad_file.write_text("---\ntype: idea\n---\n# x\n", encoding="utf-8")

    original_read_text = Path.read_text

    def fake_read_text(self: Path, *args, **kwargs):
        if self == bad_file:
            raise OSError("permission denied")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fake_read_text)

    result = runner.invoke(app, ["index", "rebuild"])

    assert result.exit_code == 0
    assert "Skipped 1 files." in result.output
    assert "read error" in result.output
    assert "unreadable.md" in result.output
