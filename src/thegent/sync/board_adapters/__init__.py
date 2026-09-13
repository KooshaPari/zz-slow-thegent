"""Stub module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GitHubBoardAdapter:
    """Adapter for GitHub board integration."""

    owner: str = ""
    repo: str = ""


__all__ = ["GitHubBoardAdapter", "LinearBoardAdapter"]


class LinearBoardAdapter:
    """Adapter for Linear board integration."""

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key
        self.issues: list[dict[str, Any]] = []

    def get_issues(self) -> list[dict[str, Any]]:
        """Get issues from Linear board."""
        return self.issues

    def create_issue(self, title: str, description: str = "") -> dict[str, Any]:
        """Create an issue on Linear board."""
        issue = {"title": title, "description": description, "id": len(self.issues)}
        self.issues.append(issue)
        return issue
