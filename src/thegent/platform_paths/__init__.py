"""STUB MODULE - thegent.platform_paths

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

from pathlib import Path


def get_config_dir() -> Path:
    """Get the configuration directory."""
    return Path.home() / ".config" / "thegent"


# Stub implementation - functionality not available
__all__ = ["get_config_dir"]
