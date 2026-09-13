"""Tests for nightly semantic knowledge extractor.

# @trace FR-DOCS-011
"""

from pathlib import Path

from docs_engine.semantic.indexer import SemanticIndexer


def _write_dump(docs_root: Path, content: str) -> None:
    dump_dir = docs_root / "research"
    dump_dir.mkdir(parents=True, exist_ok=True)
    (dump_dir / "CONVERSATION_DUMP_2026-02-21.md").write_text(content)


def test_extracts_decisions(tmp_path):
    docs_root = tmp_path / "docs"
    _write_dump(docs_root, "## Decisions\n\n- Use SQLite for doc index\n- Prefer VitePress over MkDocs\n")
    indexer = SemanticIndexer(docs_root=docs_root, db_path=tmp_path / "test.db")
    items = indexer.extract()
    assert len(items) >= 2
    titles = [i["title"] for i in items]
    assert any("SQLite" in t for t in titles)


def test_extracts_findings(tmp_path):
    docs_root = tmp_path / "docs"
    _write_dump(docs_root, "## Findings\n\n- orjson is 3x faster than json\n")
    indexer = SemanticIndexer(docs_root=docs_root, db_path=tmp_path / "test.db")
    items = indexer.extract()
    assert any("orjson" in i["title"] for i in items)


def test_extracts_lessons(tmp_path):
    docs_root = tmp_path / "docs"
    _write_dump(docs_root, "## Lessons Learned\n\n- Always write tests first\n")
    indexer = SemanticIndexer(docs_root=docs_root, db_path=tmp_path / "test.db")
    items = indexer.extract()
    assert any("tests" in i["title"].lower() for i in items)


def test_run_creates_kb_extracts(tmp_path):
    docs_root = tmp_path / "docs"
    _write_dump(docs_root, "## Decisions\n\n- Use structlog for logging\n")
    indexer = SemanticIndexer(docs_root=docs_root, db_path=tmp_path / "test.db")
    count = indexer.run()
    assert count >= 1
    kb_dir = docs_root / "kb"
    assert kb_dir.exists()
    kb_files = list(kb_dir.glob("*.md"))
    assert len(kb_files) >= 1


def test_deduplicates_on_rerun(tmp_path):
    docs_root = tmp_path / "docs"
    _write_dump(docs_root, "## Decisions\n\n- Use structlog for logging\n")
    indexer = SemanticIndexer(docs_root=docs_root, db_path=tmp_path / "test.db")
    count1 = indexer.run()
    count2 = indexer.run()
    # Second run should create 0 new files (all already exist)
    assert count2 == 0
    assert count1 >= 1
