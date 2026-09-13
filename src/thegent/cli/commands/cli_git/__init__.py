"""CLI git commands module."""

from __future__ import annotations

__all__ = ["app"]

try:
    from typer import Typer

    app = Typer()
except ImportError:

    class StubApp:
        def __call__(self) -> None:
            pass

    app = StubApp()
