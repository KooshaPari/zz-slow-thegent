"""STUB MODULE - thegent.commands.idea_seeds

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass


def _make_slug(text: str) -> str:
    """Create a URL-safe slug from text.

    Args:
        text: Text to slugify.

    Returns:
        Slugified text.
    """
    # Convert to lowercase
    slug = text.lower()
    # Replace spaces and underscores with hyphens
    slug = re.sub(r"[_\s]+", "-", slug)
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    return slug


def _priority_for_type(seed_type: str) -> int:
    """Get priority for a seed type.

    Args:
        seed_type: The type of seed (e.g., 'bugfix', 'feature', 'refactor').

    Returns:
        Priority value (lower is higher priority).
    """
    priority_map = {
        "bugfix": 1,
        "security": 1,
        "feature": 2,
        "enhancement": 3,
        "refactor": 4,
        "docs": 5,
        "test": 5,
        "chore": 6,
    }
    return priority_map.get(seed_type.lower(), 10)


def _try_relative(path: str, base: str) -> str:
    """Try to make a path relative to base.

    Args:
        path: The path to make relative.
        base: The base path to make it relative to.

    Returns:
        The relative path if possible, otherwise the original path.
    """
    try:
        return os.path.relpath(path, base)
    except ValueError:
        return path


@dataclass
class IdeaSeed:
    """An idea seed for idea generation."""

    id: str
    title: str
    description: str = ""
    category: str = "general"


# Default file extensions for idea seeds
DEFAULT_EXTENSIONS = [".py", ".js", ".ts", ".md", ".txt"]

# Seed patterns for idea generation
SEED_PATTERNS = [
    "feature_*",
    "bugfix_*",
    "refactor_*",
]


class IdeaSeedScanner:
    """Scanner for idea seeds."""

    def __init__(self, patterns: list[str] | None = None) -> None:
        self.patterns = patterns or SEED_PATTERNS

    def scan(self, directory: str) -> list[IdeaSeed]:
        """Scan directory for idea seeds."""
        return []


__all__ = [
    "DEFAULT_EXTENSIONS",
    "SEED_PATTERNS",
    "IdeaSeed",
    "IdeaSeedScanner",
    "_make_slug",
    "_priority_for_type",
    "_try_relative",
]
