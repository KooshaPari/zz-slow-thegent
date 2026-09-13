"""STUB MODULE - thegent.registry.cross_project

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import orjson


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse YAML frontmatter from markdown text.

    Args:
        text: Markdown text that may contain frontmatter.

    Returns:
        Dictionary of frontmatter key-value pairs, or empty dict if not found.
    """
    import re

    match = re.match(r"^\s*---\s*\n(.*?)\n\s*---", text, re.DOTALL)
    if not match:
        return {}

    import yaml

    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}


def _extract_name(frontmatter: dict[str, Any], fallback: str) -> str:
    """Extract agent name from frontmatter.

    Args:
        frontmatter: Parsed frontmatter dictionary.
        fallback: Fallback name if not in frontmatter.

    Returns:
        Agent name.
    """
    name = frontmatter.get("name", "").strip()
    return name if name else fallback


def _extract_capabilities(frontmatter: dict[str, Any]) -> list[str]:
    """Extract capabilities from frontmatter.

    Args:
        frontmatter: Parsed frontmatter dictionary.

    Returns:
        List of capability strings.
    """
    tools = frontmatter.get("tools", frontmatter.get("capabilities", []))
    if isinstance(tools, str):
        caps = [t.strip().lower() for t in tools.split(",")]
    elif isinstance(tools, list):
        caps = [t.strip().lower() for t in tools]
    else:
        caps = []

    # Remove duplicates while preserving order
    seen = set()
    result = []
    for cap in caps:
        if cap and cap not in seen:
            seen.add(cap)
            result.append(cap)
    return result


@dataclass
class PersonaRecord:
    """Record for a persona/agent discovered across projects."""

    name: str
    project_root: Path
    capabilities: list[str] = field(default_factory=list)
    persona_file: Path | None = None
    last_seen: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert record to dictionary."""
        return {
            "name": self.name,
            "project_root": str(self.project_root),
            "capabilities": self.capabilities,
            "persona_file": str(self.persona_file) if self.persona_file else "",
            "last_seen": self.last_seen.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PersonaRecord":
        """Create record from dictionary."""
        try:
            last_seen = datetime.fromisoformat(data["last_seen"])
        except (ValueError, KeyError):
            last_seen = datetime.now(UTC)

        return cls(
            name=data["name"],
            project_root=Path(data["project_root"]),
            capabilities=data.get("capabilities", []),
            persona_file=Path(data["persona_file"]) if data.get("persona_file") else None,
            last_seen=last_seen,
        )


@dataclass
class CrossProjectRegistry:
    """Registry for cross-project persona discovery and search."""

    def __init__(self, registry_file: Path | None = None) -> None:
        self.registry_file = registry_file
        self.records: list[PersonaRecord] = []

    def discover_personas(self, project_root: Path) -> list[PersonaRecord]:
        """Discover persona files in a project.

        Args:
            project_root: Root directory of the project to scan.

        Returns:
            List of PersonaRecord objects.
        """
        agents_dir = project_root / "agents"
        if not agents_dir.is_dir():
            return []

        records = []
        for md_file in agents_dir.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            fm = _parse_frontmatter(content)
            name = _extract_name(fm, md_file.stem)
            capabilities = _extract_capabilities(fm)

            records.append(
                PersonaRecord(
                    name=name,
                    project_root=project_root.resolve(),
                    capabilities=capabilities,
                    persona_file=md_file,
                    last_seen=datetime.now(UTC),
                )
            )

        return records

    def register_project(self, project_root: Path) -> list[PersonaRecord]:
        """Discover and register personas from a project.

        Args:
            project_root: Root directory of the project.

        Returns:
            List of discovered PersonaRecord objects.
        """
        records = self.discover_personas(project_root)
        self.records.extend(records)
        self.save()
        return records

    def search(self, capability: str) -> list[PersonaRecord]:
        """Search for personas by capability.

        Args:
            capability: Capability to search for (case-insensitive).

        Returns:
            List of matching PersonaRecord objects.
        """
        capability = capability.lower()
        return [r for r in self.records if any(capability in cap.lower() for cap in r.capabilities)]

    def get_all(self) -> list[PersonaRecord]:
        """Get all registered personas."""
        return self.records

    def save(self) -> None:
        """Save registry to disk."""
        if not self.registry_file:
            return

        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = self.registry_file.with_suffix(".tmp")
        tmp_file.write_text(
            orjson.dumps([r.to_dict() for r in self.records]).decode(),
            encoding="utf-8",
        )
        tmp_file.rename(self.registry_file)

    def load(self) -> None:
        """Load registry from disk."""
        if not self.registry_file or not self.registry_file.exists():
            self.records = []
            return

        try:
            data = orjson.loads(self.registry_file.read_text())
            if not isinstance(data, list):
                raise ValueError("Expected JSON list")
            self.records = [PersonaRecord.from_dict(d) for d in data]
        except (orjson.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Corrupt persona registry: {e}") from e


# Stub implementation - functionality not available
__all__ = [
    "CrossProjectRegistry",
    "PersonaRecord",
    "_extract_capabilities",
    "_extract_name",
    "_parse_frontmatter",
]
