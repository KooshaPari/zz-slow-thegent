"""Stub module."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BinaryDiscovery:
    """Discovery for binary tools."""

    def __init__(self) -> None:
        self.binaries: dict[str, str] = {}

    def discover(self, name: str) -> str | None:
        """Discover binary location."""
        return self.binaries.get(name)


__all__ = ["BinaryDiscovery", "is_thegent_shim"]


def is_thegent_shim(binary_path: str) -> bool:
    """Check if a binary is the thegent shim.

    Args:
        binary_path: Path to check.

    Returns:
        True if the path is a thegent shim, False otherwise.
    """
    path = Path(binary_path)

    # Check if path contains thegent shim marker
    if "thegent-shims-" in str(path):
        return True

    # Check if it's a symlink pointing to a shim
    try:
        if path.is_symlink():
            target = path.readlink()
            if "thegent" in str(target).lower():
                return True
    except PermissionError as e:
        # Log permission error and return False
        logger.warning(f"shim_resolution_failed: PermissionError accessing {binary_path}: {e}")
        return False
    except (OSError, Exception) as e:
        logger.warning(f"shim_resolution_failed: Error accessing {binary_path}: {e}")
        return False

    return False
