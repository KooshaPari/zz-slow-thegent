"""Stub parser module for CLI argument parsing."""

from __future__ import annotations

import sys
from typing import Any


def parse_args(argv: list[str] | None = None) -> dict[str, Any]:
    """Parse CLI arguments (stub)."""
    if argv is None:
        argv = sys.argv[1:]
    return {"argv": argv, "parsed": True}
