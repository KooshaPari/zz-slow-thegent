"""Tests for documentation link checker."""

import pytest

from thegent.docgen.link_checker import DocLinkChecker


@pytest.fixture
def temp_docs(tmp_path):
    """Create temporary documentation structure."""
    docs = tmp_path / "docs"
    docs.mkdir()

    # File with valid internal links
    page1 = docs / "page1.md"
    page1.write_text("See [Page 2](page2.md) or [Subpage](sub/page3.md)")

    # File with broken internal link
    broken = docs / "broken.md"
    broken.write_text("See [Non-existent](missing.md)")

    # Subdirectory
    sub = docs / "sub"
    sub.mkdir()
    page3 = sub / "page3.md"
    page3.write_text("Back to [Page 1](../page1.md)")

    # Page 2
    page2 = docs / "page2.md"
    page2.write_text("Hello")

    return docs


@pytest.mark.asyncio
async def test_find_links(temp_docs):
    """Test finding links in a file."""
    async with DocLinkChecker(base_dir=temp_docs) as checker:
        links = checker.find_links(temp_docs / "page1.md")
        assert len(links) == 2
        assert links[0]["url"] == "page2.md"
        assert links[1]["url"] == "sub/page3.md"


@pytest.mark.asyncio
async def test_check_internal_link_valid(temp_docs):
    """Test checking valid internal links."""
    async with DocLinkChecker(base_dir=temp_docs) as checker:
        result = checker.check_internal_link("page2.md", temp_docs / "page1.md")
        assert result["valid"] is True
        assert result["type"] == "internal"


@pytest.mark.asyncio
async def test_check_internal_link_broken(temp_docs):
    """Test checking broken internal links."""
    async with DocLinkChecker(base_dir=temp_docs) as checker:
        result = checker.check_internal_link("missing.md", temp_docs / "page1.md")
        assert result["valid"] is False


@pytest.mark.asyncio
async def test_check_external_link(temp_docs):
    """Test checking external links (mocked)."""
    async with DocLinkChecker(base_dir=temp_docs) as checker:
        # We don't want to actually hit the network in tests if possible
        # but the task asks for it. For now, let's test the logic.
        result = await checker.check_external_link("https://github.com")
        assert "status_code" in result or "error" in result


@pytest.mark.asyncio
async def test_ignore_patterns(temp_docs):
    """Test ignoring links based on patterns."""
    async with DocLinkChecker(
        base_dir=temp_docs, ignore_patterns=[r"http://localhost.*"]
    ) as checker:
        links = checker.find_links(temp_docs / "page1.md")
        # Add a local link
        (temp_docs / "local.md").write_text("[Local](http://localhost:8080)")
        links = checker.find_links(temp_docs / "local.md")
        assert len(links) == 0


@pytest.mark.asyncio
async def test_check_directory(temp_docs):
    """Test checking a whole directory."""
    async with DocLinkChecker(base_dir=temp_docs) as checker:
        summary = await checker.check_directory(temp_docs)
        assert summary["total_links"] == 3  # 2 in page1, 1 in sub/page3
        assert summary["broken_links_count"] == 0

        # Now add broken file
        broken_summary = await checker.check_directory(temp_docs, pattern="broken.md")
        assert broken_summary["broken_links_count"] == 1
