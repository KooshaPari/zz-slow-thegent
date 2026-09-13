"""Tests for SQLite doc indexer and queries.

# @trace FR-DOCS-002
"""

import pytest

from docs_engine.db.indexer import DocIndexer
from docs_engine.db.queries import DocQueries


@pytest.fixture
def tmp_db(tmp_path):
    db_path = tmp_path / "test.db"
    indexer = DocIndexer(db_path)
    indexer.init_schema()
    return indexer, DocQueries(db_path)


def test_index_doc(tmp_db):
    indexer, queries = tmp_db
    indexer.upsert_doc(
        path="docs/ideas/2026-02-21-test.md",
        frontmatter={
            "type": "idea",
            "status": "draft",
            "title": "Test idea",
            "layer": 1,
            "date": "2026-02-21",
        },
    )
    results = queries.get_by_type("idea")
    assert len(results) == 1
    assert results[0]["title"] == "Test idea"


def test_upsert_updates_existing(tmp_db):
    indexer, queries = tmp_db
    indexer.upsert_doc(
        path="docs/ideas/2026-02-21-test.md",
        frontmatter={"type": "idea", "status": "draft", "title": "Test", "layer": 1, "date": "2026-02-21"},
    )
    indexer.upsert_doc(
        path="docs/ideas/2026-02-21-test.md",
        frontmatter={"type": "idea", "status": "active", "title": "Test", "layer": 1, "date": "2026-02-21"},
    )
    results = queries.get_by_type("idea")
    assert len(results) == 1  # still one row
    assert results[0]["status"] == "active"  # updated


def test_search_by_title(tmp_db):
    indexer, queries = tmp_db
    indexer.upsert_doc(
        "a.md",
        {"type": "research", "status": "active", "title": "SQLite performance", "layer": 1, "date": "2026-02-21"},
    )
    indexer.upsert_doc(
        "b.md", {"type": "research", "status": "active", "title": "VitePress setup", "layer": 1, "date": "2026-02-21"}
    )
    results = queries.search("SQLite")
    assert len(results) == 1
    assert "SQLite" in results[0]["title"]


def test_get_by_status(tmp_db):
    indexer, queries = tmp_db
    indexer.upsert_doc(
        "a.md", {"type": "idea", "status": "draft", "title": "Draft doc", "layer": 1, "date": "2026-02-21"}
    )
    indexer.upsert_doc(
        "b.md", {"type": "idea", "status": "published", "title": "Published doc", "layer": 1, "date": "2026-02-21"}
    )
    drafts = queries.get_by_status("draft")
    assert len(drafts) == 1
    assert drafts[0]["title"] == "Draft doc"
