"""Tests for session-end conversation dump writer.

# @trace FR-DOCS-004
"""

from docs_engine.capture.session_hook import write_conversation_dump
from docs_engine.db.queries import DocQueries


def test_dump_creates_file(tmp_path):
    path = write_conversation_dump(
        docs_root=tmp_path / "docs",
        db_path=tmp_path / "test.db",
        session_id="test-sess-001",
        content="## Issues Addressed\n\nFixed the thing.\n",
    )
    assert path.exists()
    text = path.read_text()
    assert "test-sess-001" in text
    assert "Fixed the thing" in text


def test_dump_indexed_as_layer_zero(tmp_path):
    write_conversation_dump(
        docs_root=tmp_path / "docs",
        db_path=tmp_path / "test.db",
        session_id="sess-x",
        content="content",
    )
    results = DocQueries(tmp_path / "test.db").get_by_type("conversation-dump")
    assert len(results) == 1
    assert results[0]["layer"] == 0


def test_dump_appends_to_existing_same_day_file(tmp_path):
    docs_root = tmp_path / "docs"
    db = tmp_path / "test.db"
    write_conversation_dump(docs_root=docs_root, db_path=db, session_id="s1", content="First dump.")
    write_conversation_dump(docs_root=docs_root, db_path=db, session_id="s2", content="Second dump.")
    # Should have one file (same day), and it should contain both
    dumps = list((docs_root / "research").glob("CONVERSATION_DUMP_*.md"))
    assert len(dumps) == 1
    text = dumps[0].read_text()
    assert "First dump." in text
    assert "Second dump." in text
