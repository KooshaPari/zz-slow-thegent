"""Generate edit-on-GitHub links for documentation."""

import logging
from pathlib import Path

from thegent.utils.helpers import normalize_path, safe_read_file, safe_write_file

logger = logging.getLogger(__name__)


class EditLinksGenerator:
    """Generate edit-on-GitHub links for markdown files."""

    def __init__(
        self,
        repo_url: str = "https://github.com/yourorg/thegent",
        branch: str = "main",
        base_dir: Path | None = None,
    ) -> None:
        """Initialize edit links generator.

        Args:
            repo_url: GitHub repository URL
            branch: Git branch name
            base_dir: Base directory for documentation
        """
        self.repo_url = repo_url.rstrip("/")
        self.branch = branch
        self.base_dir = base_dir or Path.cwd()

    def generate_edit_link(self, file_path: Path) -> str:
        """Generate edit link for a file.

        Args:
            file_path: Path to file

        Returns:
            GitHub edit URL
        """
        file_path = normalize_path(file_path)

        # Get relative path from base_dir
        try:
            rel_path = file_path.relative_to(self.base_dir)
        except ValueError:
            # File is outside base_dir, use absolute path
            rel_path = file_path

        # GitHub edit URL format
        edit_url = f"{self.repo_url}/edit/{self.branch}/{rel_path}"
        return edit_url

    def add_edit_link_to_file(self, file_path: Path, position: str = "top") -> bool:
        """Add edit link to a markdown file.

        Args:
            file_path: Path to markdown file
            position: Where to add link ("top" or "bottom")

        Returns:
            True if successful
        """
        content = safe_read_file(file_path)
        if not content:
            return False

        edit_url = self.generate_edit_link(file_path)
        edit_link = f"\n\n---\n\n[Edit this page]({edit_url})\n"

        if position == "top":
            # Add after frontmatter if present
            if content.startswith("---"):
                # Find end of frontmatter
                end_idx = content.find("---", 3)
                if end_idx != -1:
                    new_content = content[: end_idx + 3] + edit_link + content[end_idx + 3 :]
                else:
                    new_content = content + edit_link
            else:
                new_content = edit_link + content
        else:
            new_content = content + edit_link

        return safe_write_file(file_path, new_content)

    def add_edit_links_batch(self, files: list[Path], position: str = "bottom") -> dict[str, bool]:
        """Add edit links to multiple files.

        Args:
            files: List of file paths
            position: Where to add links

        Returns:
            Dictionary mapping file paths to success status
        """
        results = {}
        for file_path in files:
            results[str(file_path)] = self.add_edit_link_to_file(file_path, position)
        return results
