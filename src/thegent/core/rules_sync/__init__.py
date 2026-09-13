"""Stub module."""

from dataclasses import dataclass, field
from typing import Any

ALL_PLATFORMS = ["linux", "darwin", "windows"]


@dataclass
class Rule:
    """A rule for synchronization across platforms."""

    id: str = ""
    name: str = ""
    pattern: str = ""
    action: str = "sync"
    platforms: list[str] = field(default_factory=lambda: ALL_PLATFORMS.copy())
    metadata: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def matches(self, path: str) -> bool:
        """Check if a path matches this rule's pattern."""
        import re

        try:
            return bool(re.match(self.pattern, path))
        except re.error:
            return False

    def is_applicable(self, platform: str) -> bool:
        """Check if this rule applies to a given platform."""
        return platform in self.platforms


class RulesSyncManager:
    """Manager for synchronizing rules across platforms."""

    def __init__(self) -> None:
        self._rules: dict[str, Rule] = {}
        self._sync_status: dict[str, str] = {}

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the manager."""
        self._rules[rule.id] = rule

    def get_rule(self, rule_id: str) -> Rule | None:
        """Get a rule by ID."""
        return self._rules.get(rule_id)

    def sync_all(self) -> dict[str, bool]:
        """Sync all rules to their target platforms."""
        results = {}
        for rule_id in self._rules:
            results[rule_id] = True
            self._sync_status[rule_id] = "synced"
        return results


__all__ = [
    "ALL_PLATFORMS",
    "Rule",
    "RulesSyncManager",
    "RulesSyncResult",
    "SyncRecord",
    "_parse_frontmatter",
    "_replace_managed_section",
]


def _replace_managed_section(content: str, new_section: str) -> str:
    """Replace the managed section in content.

    Args:
        content: Original content.
        new_section: New section content.

    Returns:
        Content with replaced section.
    """
    # Simple implementation - replace everything between markers
    lines = content.split("\n")
    result = []
    in_section = False
    for line in lines:
        if "<!-- managed-section -->" in line:
            in_section = True
            result.append(line)
            result.append(new_section)
        elif in_section and "<!-- /managed-section -->" in line:
            in_section = False
            result.append(line)
        elif not in_section:
            result.append(line)
    return "\n".join(result)


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse frontmatter from content.

    Args:
        content: Content with frontmatter.

    Returns:
        Tuple of (frontmatter dict, body string).
    """
    import yaml

    lines = content.split("\n")
    if lines and lines[0].strip() == "---":
        end_idx = None
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                end_idx = i
                break
        if end_idx:
            fm_content = "\n".join(lines[1:end_idx])
            body = "\n".join(lines[end_idx + 1 :])
            try:
                fm = yaml.safe_load(fm_content) or {}
            except yaml.YAMLError:
                fm = {}
            return fm, body
    return {}, content


@dataclass
class SyncRecord:
    """Record of a sync operation."""

    rule_id: str = ""
    platform: str = ""
    timestamp: float = 0.0
    status: str = "pending"


@dataclass
class RulesSyncResult:
    """Result of a rules synchronization operation."""

    rule_id: str = ""
    success: bool = False
    synced_platforms: list[str] = field(default_factory=list)
    failed_platforms: list[str] = field(default_factory=list)
    error_message: str = ""

    def is_full_success(self) -> bool:
        """Check if sync was successful for all platforms."""
        return self.success and not self.failed_platforms
