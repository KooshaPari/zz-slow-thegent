"""STUB MODULE - thegent.maif.models

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionType(Enum):
    """Action type enumeration."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"


@dataclass
class MAIFArtifact:
    """Artifact in the MAIF system."""

    id: str
    name: str
    artifact_type: str = "generic"
    content: str = ""


__all__ = ["ActionType", "MAIFArtifact"]
