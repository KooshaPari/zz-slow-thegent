"""Tests for commit hook WorklogEntry writer.

# @trace FR-DOCS-005
"""

from docs_engine.capture.commit_hook import write_worklog_entry
from docs_engine.db.queries import DocQueries


def test_worklog_created(tmp_path):
    path = write_worklog_entry(
        docs_root=tmp_path / "docs",
        db_path=tmp_path / "test.db",
        commit_sha="abc1234",
        commit_msg="feat: add thing",
        files_changed=["src/foo.py"],
    )
    assert path.exists()
    text = path.read_text()
    assert "abc1234" in text
    assert "feat: add thing" in text


def test_worklog_sequential_numbering(tmp_path):
    docs_root = tmp_path / "docs"
    db = tmp_path / "test.db"
    p1 = write_worklog_entry(
        docs_root=docs_root,
        db_path=db,
        commit_sha="a",
        commit_msg="first",
        files_changed=[],
    )
    p2 = write_worklog_entry(
        docs_root=docs_root,
        db_path=db,
        commit_sha="b",
        commit_msg="second",
        files_changed=[],
    )
    assert p1.name == "WL-0001.md"
    assert p2.name == "WL-0002.md"


def test_worklog_indexed_as_published(tmp_path):
    write_worklog_entry(
        docs_root=tmp_path / "docs",
        db_path=tmp_path / "test.db",
        commit_sha="abc",
        commit_msg="feat: thing",
        files_changed=[],
    )
    results = DocQueries(tmp_path / "test.db").get_by_type("worklog")
    assert len(results) == 1
    assert results[0]["status"] == "published"
    assert results[0]["layer"] == 3
