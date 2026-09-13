"""STUB MODULE - thegent.sitback_plugins

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

from typing import Any


class SitbackPlugin:
    """Base class for sitback plugins."""

    def __init__(self, name: str) -> None:
        self.name = name

    def run(self) -> dict[str, Any]:
        """Run the plugin."""
        return {"status": "ok", "plugin": self.name}


def load_plugins() -> list[SitbackPlugin]:
    """Load available sitback plugins.

    Returns:
        List of SitbackPlugin instances.
    """
    return []


def _probe_harness_status() -> dict[str, Any]:
    """Get the status of the probe harness.

    Returns:
        Dictionary containing harness status information.
        - "ok": Harness is enabled and functional
        - "unavailable": Harness is disabled or missing dependencies
        - "error": Harness encountered a runtime error
    """
    # Check if harness is enabled in config
    try:
        from thegent.config import ThegentSettings

        settings = ThegentSettings()
        if not getattr(settings, "sitback_harness", False):
            return {
                "status": "unavailable",
                "active_probes": 0,
                "last_run": None,
                "reason": "disabled_by_config",
            }
    except Exception:
        pass

    # Check for missing dependencies
    # Check for missing dependencies - use getattr with default to avoid AttributeError
    try:
        terminal = __import__(
            "thegent.skills.terminal", fromlist=["heliosShield_status"]
        )
        helios_func = getattr(terminal, "heliosShield_status", None)
        if helios_func is None:
            return {
                "status": "unavailable",
                "active_probes": 0,
                "last_run": None,
                "reason": "dependency_missing",
            }
    except (ImportError, AttributeError):
        return {
            "status": "unavailable",
            "active_probes": 0,
            "last_run": None,
            "reason": "dependency_missing",
        }

    # Try to get harness status
    try:
        result = helios_func()
        return {
            "status": "ok",
            "active_probes": 1,
            "last_run": None,
            "details": result,
        }
    except RuntimeError:
        return {
            "status": "error",
            "active_probes": 0,
            "last_run": None,
            "reason": "runtime_failure",
        }
    except Exception:
        return {
            "status": "unavailable",
            "active_probes": 0,
            "last_run": None,
            "reason": "check_failed",
        }


__all__ = ["SitbackPlugin", "load_plugins", "_probe_harness_status"]
