"""WP-10009: Backward-compatible API evolution controls.

Manages version negotiation and compatibility flags for API changes.
"""

from typing import Any


class APIEvolutionManager:
    """Manages compatibility between different API versions."""

    def __init__(self, current_version: str = "2.0") -> None:
        self.current_version = current_version
        self._compat_flags: dict[str, bool] = {
            "v1_legacy_parsing": True,
            "v2_strict_envelopes": False,
        }

    def negotiate_version(self, client_version: str) -> dict[str, Any]:
        """Negotiate the best API version for the client."""
        if client_version == self.current_version:
            return {"version": self.current_version, "compat_mode": "native"}

        if client_version.startswith("1."):
            return {
                "version": "1.0",
                "compat_mode": "legacy",
                "warning": "Using deprecated v1 API. Please migrate to v2.0.",
            }

        return {"version": self.current_version, "compat_mode": "fallback"}

    def is_feature_enabled(self, flag: str) -> bool:
        """Check if a specific compatibility flag is enabled."""
        return self._compat_flags.get(flag, False)
