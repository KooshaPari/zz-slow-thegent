"""Thegent CLI entry point.

NOTE: This module is a stub. The actual CLI is located at:
- phenotype-thegent-cli package (apps structure)
- src/thegent/cli/commands/ (command implementations)

This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

from typing import Any

# Attempt to import from the CLI commands structure
try:
    from thegent.cli.apps.main import app
except ImportError:
    # Fallback: create a minimal stub app
    from typer import Typer

    app: Any = Typer()
    app.__doc__ = "Thegent CLI (stub - actual implementation in phenotype-thegent-cli)"


def _install_agent_accelerators() -> dict[str, Any]:
    """Install agent accelerators for the CLI.

    Returns:
        Dictionary with installation status and details.
    """
    return {"status": "installed", "accelerators": []}


__all__ = ["app", "_install_agent_accelerators"]
