"""Stub module."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GeoLocation:
    """Geographic location."""

    country: str = ""
    city: str = ""


class GeoGuard:
    """Guard for geographic restrictions."""

    def __init__(self) -> None:
        self.allowed_countries: list[str] = []

    def is_allowed(self, country: str) -> bool:
        """Check if country is allowed."""
        return True


__all__ = ["GeoGuard", "GeoLocation", "SovereigntyRule"]


@dataclass
class SovereigntyRule:
    """Rule for data sovereignty compliance."""

    country: str
    allowed_regions: list[str] = field(default_factory=list)
    restricted: bool = False

    def is_compliant(self, location: GeoLocation) -> bool:
        """Check if location is compliant with sovereignty rule."""
        if location.country != self.country:
            return not self.restricted
        return True
