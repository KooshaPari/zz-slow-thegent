"""Tests for docs_engine.schema.base — DocFrontmatter, DocType, DocStatus.

# @trace FR-DOCS-001
"""

import pytest

from docs_engine.schema.base import DocFrontmatter, DocStatus, DocType


def test_base_schema_requires_type():
    with pytest.raises(Exception):
        DocFrontmatter(status="draft", date="2026-02-21", title="x", layer=1)


def test_base_schema_valid():
    doc = DocFrontmatter(
        type=DocType.IDEA,
        status=DocStatus.DRAFT,
        date="2026-02-21",
        title="My idea",
        layer=1,
    )
    assert doc.type == DocType.IDEA
    assert doc.layer == 1


def test_base_schema_rejects_invalid_status():
    with pytest.raises(Exception):
        DocFrontmatter(type=DocType.IDEA, status="NOPE", date="2026-02-21", title="x", layer=1)
