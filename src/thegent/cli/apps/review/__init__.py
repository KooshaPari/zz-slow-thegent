"""Review CLI module."""

from __future__ import annotations

from typing import Any

__all__ = ["app"]

# Create a minimal Typer app stub
try:
    from typer import Typer

    app = Typer()
except ImportError:

    class StubApp:
        def __call__(self) -> None:
            pass

    app = StubApp()
