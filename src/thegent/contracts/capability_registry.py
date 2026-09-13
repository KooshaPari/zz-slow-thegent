"""Capability registry — lightweight skill/capability lookup for agents.

Provides :class:`Capability` (data descriptor) and
:class:`CapabilityRegistry` (in-memory store with O(1) lookup).

# @trace WL-082
"""

from __future__ import annotations


class Capability:
    """A single agent capability entry."""

    __slots__ = ("id", "trust_level", "version")

    def __init__(self, id: str, version: str = "1.0", trust_level: int = 1) -> None:
        if not isinstance(id, str) or not id:
            raise ValueError("id must be a non-empty string")
        self.id = id
        self.version = version
        self.trust_level = trust_level

    def __repr__(self) -> str:
        return f"Capability(id={self.id!r}, version={self.version!r}, trust_level={self.trust_level!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Capability):
            return NotImplemented
        return self.id == other.id and self.version == other.version and self.trust_level == other.trust_level

    def __hash__(self) -> int:
        return hash((self.id, self.version, self.trust_level))


class CapabilityRegistry:
    """In-memory registry of :class:`Capability` instances.

    Lookup by ``id`` is O(1) via an internal dict.  Thread-safety is
    *not* guaranteed — callers should synchronise externally when needed.
    """

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        """Register *capability* (overwrites any existing entry with the same id)."""
        self._capabilities[capability.id] = capability

    def get_capability(self, capability_id: str) -> Capability | None:
        """Return the :class:`Capability` for *capability_id*, or ``None``."""
        return self._capabilities.get(capability_id)

    def list_capabilities(self) -> list[Capability]:
        """Return all registered capabilities."""
        return list(self._capabilities.values())

    def __len__(self) -> int:
        return len(self._capabilities)

    def __contains__(self, capability_id: str) -> bool:
        return capability_id in self._capabilities


__all__ = ["Capability", "CapabilityRegistry"]
