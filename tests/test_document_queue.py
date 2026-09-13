"""
Integration tests for document queue system.
"""

import logging
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import orjson as json
import pytest

from thegent.agents.document import (
    DocumentAnalyzer,
    DocumentCategory,
    DocumentProcessor,
    MarkdownScanner,
    ProcessingPipeline,
    QueueManager,
    ScanConfig,
)
from thegent.agents.document.processor import (
    compute_file_hash,
    count_lines,
    extract_frontmatter,
    extract_headings,
    extract_links,
    extract_metadata,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_md_file(temp_dir):
    """Create a sample markdown file."""
    md_file = temp_dir / "test.md"
    md_file.write_text("""# Test Document

This is a test document.

## Section 1

Some content here.

[Link](https://example.com)
""")
    return md_file


@pytest.fixture
def sample_queue_file(temp_dir):
    """Create a sample queue file."""
    queue_data = {
        "scan_date": datetime.now(UTC).isoformat(),
        "scan_params": {},
        "summary": {"2026-02": {"total": 1, "by_location": {"test": 1}}},
        "queue": [
            {
                "month": "2026-02",
                "total_files": 1,
                "locations": [{"location": "test", "file_count": 1, "files": ["test.md"]}],
            }
        ],
    }
    queue_file = temp_dir / "queue.json"
    with open(queue_file, "w") as f:
        json.dump(queue_data, f)
    return queue_file


def test_scanner_scan(temp_dir, sample_md_file):
    """Test markdown scanner."""
    config = ScanConfig(
        locations={
            "test": {
                "path": str(temp_dir),
                "recursive": False,
            }
        },
        output_dir=temp_dir,
    )
    scanner = MarkdownScanner(config)
    results = scanner.scan()

    assert len(results) > 0
    # Should find our test file
    found = False
    for month_data in results.values():
        for files in month_data.values():
            if str(sample_md_file) in files:
                found = True
                break
    assert found


def test_queue_manager_load(sample_queue_file):
    """Test queue manager loading."""
    queue_manager = QueueManager(sample_queue_file)
    months = queue_manager.list_months()
    assert len(months) == 1
    assert months[0]["month"] == "2026-02"


def test_queue_manager_next(sample_queue_file):
    """Test getting next month."""
    queue_manager = QueueManager(sample_queue_file)
    next_month = queue_manager.get_next_month()
    assert next_month is not None
    assert next_month["month"] == "2026-02"


def test_queue_manager_mark_processed(sample_queue_file):
    """Test marking files as processed."""
    queue_manager = QueueManager(sample_queue_file)
    queue_manager.mark_file_processed("test.md")

    summary = queue_manager.get_summary()
    assert summary["processed"] == 1


def test_document_processor(sample_md_file):
    """Test document processor."""
    pipeline = ProcessingPipeline()
    pipeline.add_stage(extract_metadata)
    pipeline.add_stage(compute_file_hash)
    pipeline.add_stage(count_lines)

    processor = DocumentProcessor(pipeline)
    result = processor.process_file(str(sample_md_file))

    assert result.status.value == "completed"
    assert "hash" in result.metadata
    assert "line_count" in result.metadata


def test_extract_frontmatter(tmp_path: Path) -> None:
    """Frontmatter extraction parses valid YAML metadata blocks."""

    file_with_frontmatter = tmp_path / "with_frontmatter.md"
    file_with_frontmatter.write_text(
        """---
title: Test Doc
tags:
  - test
---

# Body
""",
        encoding="utf-8",
    )

    assert extract_frontmatter(file_with_frontmatter) == {
        "frontmatter": {
            "title": "Test Doc",
            "tags": ["test"],
        }
    }


def test_extract_frontmatter_missing_block(tmp_path: Path) -> None:
    """Files without frontmatter return an empty metadata payload."""

    plain_file = tmp_path / "plain.md"
    plain_file.write_text("# Title\n\nNo frontmatter here", encoding="utf-8")

    assert extract_frontmatter(plain_file) == {}


def test_extract_frontmatter_invalid_yaml(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Malformed YAML frontmatter is handled and logged before returning an empty dict."""

    bad_file = tmp_path / "bad_frontmatter.md"
    bad_file.write_text(
        """---
: invalid: yaml:
---

body
""",
        encoding="utf-8",
    )

    with caplog.at_level(logging.DEBUG, logger="thegent.agents.document.processor"):
        result = extract_frontmatter(bad_file)

    assert result == {}
    assert any("Failed to parse YAML frontmatter" in record.message for record in caplog.records)


def test_document_analyzer(sample_md_file):
    """Test document analyzer."""
    analyzer = DocumentAnalyzer()
    analysis = analyzer.analyze(sample_md_file)

    assert analysis.category in [
        DocumentCategory.DOCUMENTATION,
        DocumentCategory.UNKNOWN,
    ]
    assert analysis.word_count > 0
    assert analysis.section_count >= 2  # At least # and ##
    assert analysis.has_links


def test_processing_stages(sample_md_file):
    """Test individual processing stages."""
    # Test extract_headings
    headings_data = extract_headings(sample_md_file)
    assert "heading_count" in headings_data
    assert headings_data["heading_count"] >= 2

    # Test extract_links
    links_data = extract_links(sample_md_file)
    assert "total_links" in links_data
    assert links_data["total_links"] >= 1


def test_queue_state_persistence(temp_dir, sample_queue_file):
    """Test queue state persistence."""
    state_file = temp_dir / ".queue_state.json"
    queue_manager = QueueManager(sample_queue_file, state_file=state_file)

    queue_manager.mark_file_processed("test.md")
    queue_manager.mark_month_complete("2026-02")

    # Create new manager and verify state persisted
    queue_manager2 = QueueManager(sample_queue_file, state_file=state_file)
    summary = queue_manager2.get_summary()
    assert summary["processed"] == 1
    assert summary["last_processed_month"] == "2026-02"


def test_scanner_exclude_patterns(temp_dir):
    """Test scanner exclusion patterns."""
    # Create file in excluded directory
    excluded_dir = temp_dir / "node_modules"
    excluded_dir.mkdir()
    excluded_file = excluded_dir / "test.md"
    excluded_file.write_text("# Excluded")

    config = ScanConfig(
        locations={
            "test": {
                "path": str(temp_dir),
                "recursive": True,
            }
        },
        exclude_patterns={"node_modules"},
    )
    scanner = MarkdownScanner(config)
    results = scanner.scan()

    # Should not find file in node_modules
    found_excluded = False
    for month_data in results.values():
        for files in month_data.values():
            if str(excluded_file) in files:
                found_excluded = True
                break
    assert not found_excluded


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
