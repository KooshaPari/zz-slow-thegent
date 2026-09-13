"""Tests for 'Edit on GitHub' link generator."""

import pytest

from thegent.docgen.edit_links import EditLinkGenerator


@pytest.fixture
def repo_root(tmp_path):
    """Create a mock repository root."""
    root = tmp_path / "myrepo"
    root.mkdir()
    docs = root / "docs"
    docs.mkdir()
    page = docs / "index.md"
    page.write_text("# Welcome")
    return root


def test_generate_edit_url(repo_root):
    """Test basic edit URL generation."""
    generator = EditLinkGenerator(
        repo_url="https://github.com/user/repo", base_dir=repo_root
    )

    file_path = repo_root / "docs" / "index.md"
    url = generator.get_edit_url(file_path)

    assert url == "https://github.com/user/repo/edit/main/docs/index.md"


def test_generate_edit_url_with_line(repo_root):
    """Test edit URL with line number."""
    generator = EditLinkGenerator(
        repo_url="https://github.com/user/repo", base_dir=repo_root
    )

    file_path = repo_root / "docs" / "index.md"
    url = generator.get_edit_url(file_path, line_number=42)

    assert url == "https://github.com/user/repo/edit/main/docs/index.md#L42"


def test_generate_edit_url_custom_branch(repo_root):
    """Test edit URL with custom branch."""
    generator = EditLinkGenerator(
        repo_url="https://github.com/user/repo", base_dir=repo_root, branch="develop"
    )

    file_path = repo_root / "docs" / "index.md"
    url = generator.get_edit_url(file_path)

    assert url == "https://github.com/user/repo/edit/develop/docs/index.md"


def test_inject_edit_link(repo_root):
    """Test injecting edit link into file."""
    generator = EditLinkGenerator(
        repo_url="https://github.com/user/repo", base_dir=repo_root
    )

    file_path = repo_root / "docs" / "index.md"
    generator.inject_edit_link(file_path)

    content = file_path.read_text()
    assert "[Edit this page on GitHub]" in content
    assert "https://github.com/user/repo/edit/main/docs/index.md" in content


def test_get_view_url(repo_root):
    """Test basic view URL generation."""
    generator = EditLinkGenerator(
        repo_url="https://github.com/user/repo", base_dir=repo_root
    )

    file_path = repo_root / "docs" / "index.md"
    url = generator.get_view_url(file_path)

    assert url == "https://github.com/user/repo/blob/main/docs/index.md"
