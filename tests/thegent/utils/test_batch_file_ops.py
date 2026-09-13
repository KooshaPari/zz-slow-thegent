"""
Unit tests for thegent.utils.batch_file_ops.
"""

from __future__ import annotations

import pytest

from thegent.utils.batch_file_ops import BatchFileOperations


@pytest.fixture
def batch_ops():
    """Fixture for BatchFileOperations."""
    return BatchFileOperations(create_backups=True)


def test_batch_read(tmp_path, batch_ops):
    """Test batch reading multiple files."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("content1")
    file2.write_text("content2")

    results = batch_ops.batch_read([file1, file2])
    assert results[file1.resolve()] == "content1"
    assert results[file2.resolve()] == "content2"


def test_batch_write_success(tmp_path, batch_ops):
    """Test successful batch writing."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "subdir" / "file2.txt"

    res = batch_ops.batch_write([(file1, "content1"), (file2, "content2")])
    assert res.successful == 2
    assert res.failed == 0
    assert file1.read_text() == "content1"
    assert file2.read_text() == "content2"


def test_batch_write_atomic_rollback(tmp_path, batch_ops):
    """Test atomic write rolls back on error."""
    file1 = tmp_path / "file1.txt"
    file1.write_text("original")

    # A non-existent parent that we'll make a file so mkdir fails
    bad_path = tmp_path / "bad"
    bad_path.touch()
    target_in_bad = bad_path / "fail.txt"

    with pytest.raises(Exception):
        batch_ops.batch_write([(file1, "new_content"), (target_in_bad, "should fail")], atomic=True)

    # file1 should be rolled back to 'original'
    assert file1.read_text() == "original"


def test_progress_callback(tmp_path, batch_ops):
    """Test progress callback during batch write."""
    calls = []

    def callback(current, total):
        calls.append((current, total))

    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"

    batch_ops.batch_write([(file1, "c1"), (file2, "c2")], on_progress=callback)
    assert calls == [(1, 2), (2, 2)]
