"""Automated link checking for documentation."""

import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from thegent.utils.helpers import normalize_path, safe_read_file

logger = logging.getLogger(__name__)


class LinkChecker:
    """Check links in markdown files."""

    def __init__(self, base_dir: Path | None = None) -> None:
        """Initialize link checker.

        Args:
            base_dir: Base directory for documentation
        """
        self.base_dir = base_dir or Path.cwd()

    def find_links(self, file_path: Path) -> list[dict[str, Any]]:
        """Find all links in a markdown file.

        Args:
            file_path: Path to markdown file

        Returns:
            List of link dictionaries with url, line, type
        """
        content = safe_read_file(file_path)
        if not content:
            return []

        links = []
        lines = content.splitlines()

        # Markdown link patterns: [text](url) and [text][ref]
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        ref_pattern = r"\[([^\]]+)\]\[([^\]]+)\]"

        for i, line in enumerate(lines, 1):
            # Find inline links
            for match in re.finditer(link_pattern, line):
                url = match.group(2)
                links.append(
                    {
                        "url": url,
                        "line": i,
                        "type": "inline",
                        "text": match.group(1),
                    }
                )

            # Find reference links
            for match in re.finditer(ref_pattern, line):
                ref = match.group(2)
                links.append(
                    {
                        "url": ref,
                        "line": i,
                        "type": "reference",
                        "text": match.group(1),
                    }
                )

        return links

    def check_link(self, url: str, base_path: Path) -> dict[str, Any]:
        """Check if a link is valid.

        Args:
            url: Link URL
            base_path: Base path for relative links

        Returns:
            Dictionary with status, error, etc.
        """
        parsed = urlparse(url)

        # External links (http/https)
        if parsed.scheme in ("http", "https"):
            return {
                "url": url,
                "status": "external",
                "valid": None,  # Would need HTTP request to verify
            }

        # Anchor links (#section)
        if url.startswith("#"):
            return {
                "url": url,
                "status": "anchor",
                "valid": None,  # Would need to check if anchor exists
            }

        # Relative file links
        if not parsed.scheme:
            target_path = normalize_path(base_path.parent / url)
            exists = target_path.exists()
            return {
                "url": url,
                "status": "file",
                "valid": exists,
                "path": str(target_path),
            }

        return {
            "url": url,
            "status": "unknown",
            "valid": False,
        }

    def check_file(self, file_path: Path) -> list[dict[str, Any]]:
        """Check all links in a file.

        Args:
            file_path: Path to markdown file

        Returns:
            List of check results
        """
        links = self.find_links(file_path)
        results = []

        for link in links:
            check_result = self.check_link(link["url"], file_path)
            check_result.update(
                {
                    "line": link["line"],
                    "type": link["type"],
                    "text": link["text"],
                }
            )
            results.append(check_result)

        return results

    def check_directory(self, dir_path: Path, pattern: str = "**/*.md") -> dict[str, Any]:
        """Check all markdown files in a directory.

        Args:
            dir_path: Directory to check
            pattern: File pattern to match

        Returns:
            Summary dictionary with results
        """
        dir_path = normalize_path(dir_path)
        md_files = list(dir_path.glob(pattern))

        all_results = []
        for md_file in md_files:
            file_results = self.check_file(md_file)
            all_results.extend(file_results)

        # Summary
        total = len(all_results)
        broken = sum(1 for r in all_results if r.get("valid") is False)
        external = sum(1 for r in all_results if r.get("status") == "external")

        return {
            "total_links": total,
            "broken_links": broken,
            "external_links": external,
            "results": all_results,
        }
